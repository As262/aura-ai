# -*- coding: utf-8 -*-
"""
Train the conversation interest model on realistic conversations.

This replaces train_enhanced_conversation_model.py, whose labels were the index
of the hard-coded string list each reply was copied from. That is a lookup table,
not a dataset: the reported 96% told you the network had memorised sixty strings.

What is different here:

1. **Behavioural labels.** Interest is a latent variable that leaks into reply
   latency, reciprocity, topic pickup, effort and initiative - each channel
   noisy, each able to mislead on its own. See realistic_conversation_corpus.

2. **Trained through the serving path.** Every conversation is rendered to a
   real WhatsApp/bracket/JSON export, pushed through the actual
   ``ConversationDecoder``, and featurised by the same
   ``extract_features`` + ``ConversationContext`` the API calls. Whatever the
   decoder does to a line - merging, dropping, mangling - the model trains on.
   Train/serve skew is structurally impossible rather than merely unlikely.

3. **Independent random splits.** Train, validation, and test conversations use
   independent seeds while sharing the full scenario catalogue. This measures
   production-like generalisation without withholding entire relationship types
   from the model that must serve them.

4. **Honest metrics.** Macro-F1 (the classes are imbalanced), a confusion
   matrix, and +/-1 accuracy - because these five bands are ordered, so
   confusing "High" with "Very High" is not the same kind of error as confusing
   it with "Very Low".

Usage:
    python training/train_realistic_conversation_model.py
    python training/train_realistic_conversation_model.py --conversations 6000 --epochs 120
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api.conversation_decoder import ConversationDecoder                 # noqa: E402
from ml_models.conversation_context import ConversationContext           # noqa: E402
from ml_models.conversation_interest_model import (                      # noqa: E402
    FEATURE_DIM,
    ConversationInterestAnalyzer,
    ConversationAnalysisService,
)
from training.realistic_conversation_corpus import (                     # noqa: E402
    SCENARIOS,
    Conversation,
    CorpusGenerator,
)

CATEGORIES = [
    "Very Low (0-20%)", "Low (20-40%)", "Moderate (40-60%)",
    "High (60-80%)", "Very High (80-100%)",
]

# These scenarios remain available for optional stress-test experiments. They
# are included in normal production training so the serving model knows the
# confounds it is explicitly expected to handle.
HELD_OUT_SCENARIOS = [
    'busy_but_interested',
    'polite_disinterest',
    'long_distance_friend',
    'emoji_habit_low_interest',
]

EXPORT_FORMATS = ('whatsapp', 'whatsapp_no_seconds', 'bracket', 'json')


# ---------------------------------------------------------------------------
# Featurisation through the real decoder
# ---------------------------------------------------------------------------

class Featuriser:
    """
    Turns generated conversations into (features, labels) via the live pipeline.

    Conversations are written to a temp file in a real export format and read
    back with ``ConversationDecoder``, so training sees exactly the message
    stream production sees. When the round trip does not reproduce the message
    list one-for-one the conversation is skipped - a dropped label is much
    cheaper than a misaligned one, and the skip rate is reported because it
    doubles as a decoder-accuracy measurement.
    """

    def __init__(self):
        self.decoder = ConversationDecoder()
        self.service = ConversationAnalysisService()   # feature extractor only
        self.stats = Counter()

    def featurise(self, conversations: List[Conversation],
                  rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        rows: List[np.ndarray] = []
        labels: List[int] = []
        scenarios: List[str] = []

        for conversation in conversations:
            if not conversation.pair_labels:
                self.stats['no_pairs'] += 1
                continue

            fmt = EXPORT_FORMATS[int(rng.integers(len(EXPORT_FORMATS)))]
            decoded = self._round_trip(conversation, fmt)

            if decoded is None:
                self.stats[f'decode_mismatch_{fmt}'] += 1
                continue
            self.stats[f'decoded_{fmt}'] += 1

            flow = ConversationContext(decoded, conversation.user, conversation.other)

            for your_index, their_index, label in conversation.pair_labels:
                if their_index >= len(decoded):
                    continue
                context = flow.pair_context(your_index, their_index)
                features = self.service.extract_features(
                    decoded[your_index]['message'],
                    decoded[their_index]['message'],
                    context,
                )
                rows.append(features)
                labels.append(label)
                scenarios.append(conversation.scenario)

        if not rows:
            raise RuntimeError("Featurisation produced no samples")

        return np.vstack(rows), np.asarray(labels, dtype=np.int64), scenarios

    def _round_trip(self, conversation: Conversation,
                    fmt: str) -> Optional[List[Dict]]:
        """Write an export, decode it, and verify the messages line up."""
        if fmt == 'json':
            suffix, payload = '.json', json.dumps(conversation.to_json_export())
        elif fmt == 'bracket':
            suffix, payload = '.txt', conversation.to_bracket_export()
        elif fmt == 'whatsapp_no_seconds':
            suffix, payload = '.txt', conversation.to_whatsapp_export(seconds=False)
        else:
            suffix, payload = '.txt', conversation.to_whatsapp_export()

        handle = tempfile.NamedTemporaryFile(
            'w', suffix=suffix, delete=False, encoding='utf-8'
        )
        try:
            handle.write(payload)
            handle.close()
            decoded = self.decoder.decode_file(handle.name)['messages']
        except Exception:
            return None
        finally:
            try:
                os.unlink(handle.name)
            except OSError:
                pass

        if len(decoded) != len(conversation.messages):
            return None
        for original, parsed in zip(conversation.messages, decoded):
            if parsed.get('sender') != original['sender']:
                return None
            if parsed.get('datetime') is None:
                return None
        return decoded


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def confusion_matrix(true: np.ndarray, pred: np.ndarray, classes: int = 5) -> np.ndarray:
    matrix = np.zeros((classes, classes), dtype=int)
    for t, p in zip(true, pred):
        matrix[t, p] += 1
    return matrix


def macro_f1(true: np.ndarray, pred: np.ndarray, classes: int = 5) -> Tuple[float, List[Dict]]:
    per_class = []
    scores = []
    for c in range(classes):
        tp = int(np.sum((pred == c) & (true == c)))
        fp = int(np.sum((pred == c) & (true != c)))
        fn = int(np.sum((pred != c) & (true == c)))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores.append(f1)
        per_class.append({
            'class': CATEGORIES[c],
            'support': int(np.sum(true == c)),
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1': round(f1, 3),
        })
    return float(np.mean(scores)), per_class


def print_confusion(matrix: np.ndarray) -> None:
    print("\n   Confusion matrix (rows = true, cols = predicted)")
    print("   " + " " * 10 + "".join(f"{i:>8}" for i in range(5)))
    for i, row in enumerate(matrix):
        total = row.sum()
        hit = row[i] / total * 100 if total else 0.0
        print(f"   true {i}    " + "".join(f"{v:>8}" for v in row) +
              f"   | {hit:5.1f}% correct")


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def build_splits(conversations: int, seed: int
                 ) -> Tuple[List[Conversation], List[Conversation], List[Conversation]]:
    """
    Train, validation, and test share the complete scenario mix but use disjoint
    generator seeds. The generated conversations are independent, and the live
    decoder still provides the train/serve parity guarantee.
    """
    all_scenarios = list(SCENARIOS)
    train = CorpusGenerator(seed=seed, scenarios=all_scenarios).generate(conversations)
    val = CorpusGenerator(seed=seed + 9_991,
                          scenarios=all_scenarios).generate(max(conversations // 4, 200))
    test = CorpusGenerator(seed=seed + 77_777,
                           scenarios=all_scenarios).generate(max(conversations // 5, 200))
    return train, val, test


def evaluate(model: nn.Module, features: torch.Tensor, labels: torch.Tensor,
             criterion: nn.Module, device: torch.device,
             batch_size: int = 512) -> Dict[str, object]:
    model.eval()
    losses, preds = [], []

    with torch.no_grad():
        for start in range(0, len(features), batch_size):
            batch = features[start:start + batch_size].to(device)
            target = labels[start:start + batch_size].to(device)
            output = model(batch)
            losses.append(criterion(output, target).item() * len(batch))
            preds.append(torch.argmax(output, dim=1).cpu())

    predictions = torch.cat(preds).numpy()
    truth = labels.numpy()

    f1, per_class = macro_f1(truth, predictions)
    return {
        'loss': float(sum(losses) / len(features)),
        'accuracy': float(np.mean(predictions == truth) * 100),
        'accuracy_within_1': float(np.mean(np.abs(predictions - truth) <= 1) * 100),
        'mean_abs_error': float(np.mean(np.abs(predictions - truth))),
        'macro_f1': f1,
        'per_class': per_class,
        'predictions': predictions,
        'truth': truth,
    }


def train(conversations: int = 4000, epochs: int = 90, batch_size: int = 128,
          learning_rate: float = 8e-4, seed: int = 1234) -> Dict[str, object]:
    print("=" * 80)
    print("CONVERSATION INTEREST MODEL - REALISTIC TRAINING")
    print("=" * 80)

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")
    if device.type == 'cuda':
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    # --- data ------------------------------------------------------------
    print(f"\nGenerating {conversations} training conversations...")
    train_convos, val_convos, test_convos = build_splits(conversations, seed)
    print(f"  train {len(train_convos)} | val {len(val_convos)} | "
          f"test {len(test_convos)} (independent random scenario mix)")

    print("\nFeaturising through the live decoder + feature extractor...")
    featuriser = Featuriser()
    rng = np.random.default_rng(seed)

    x_train, y_train, _ = featuriser.featurise(train_convos, rng)
    x_val, y_val, _ = featuriser.featurise(val_convos, rng)
    x_test, y_test, test_scenarios = featuriser.featurise(test_convos, rng)

    decoded = sum(v for k, v in featuriser.stats.items() if k.startswith('decoded_'))
    mismatched = sum(v for k, v in featuriser.stats.items() if k.startswith('decode_mismatch_'))
    total = decoded + mismatched
    print(f"  message pairs: train {len(y_train)} | val {len(y_val)} | test {len(y_test)}")
    print(f"  decoder round-trip: {decoded}/{total} conversations exact "
          f"({decoded / max(total, 1) * 100:.1f}%)")
    if mismatched:
        for key in sorted(k for k in featuriser.stats if k.startswith('decode_mismatch_')):
            print(f"    skipped {featuriser.stats[key]:>5}  {key.replace('decode_mismatch_', '')}")

    print(f"  feature width: {x_train.shape[1]} (expected {FEATURE_DIM})")
    if x_train.shape[1] != FEATURE_DIM:
        raise RuntimeError("Feature width does not match FEATURE_DIM")

    distribution = Counter(y_train.tolist())
    print("\n  label distribution (train):")
    for c in range(5):
        count = distribution.get(c, 0)
        print(f"    {c} {CATEGORIES[c]:<20} {count:>6}  "
              f"{count / max(len(y_train), 1) * 100:5.1f}%")

    # --- tensors + input normalisation -----------------------------------
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0)

    train_x = torch.from_numpy(x_train)
    train_y = torch.from_numpy(y_train)
    val_x, val_y = torch.from_numpy(x_val), torch.from_numpy(y_val)
    test_x, test_y = torch.from_numpy(x_test), torch.from_numpy(y_test)

    loader = DataLoader(
        TensorDataset(train_x, train_y), batch_size=batch_size, shuffle=True,
        drop_last=len(train_y) > batch_size,
    )

    # --- model -----------------------------------------------------------
    model = ConversationInterestAnalyzer(input_size=FEATURE_DIM).to(device)
    model.set_input_normalization(mean, std)

    # Rare bands would otherwise be ignored in favour of the common middle.
    counts = np.array([max(distribution.get(c, 0), 1) for c in range(5)], dtype=np.float64)
    weights = torch.tensor((counts.sum() / (5 * counts)), dtype=torch.float32, device=device)
    print(f"\n  class weights: {[round(float(w), 2) for w in weights]}")

    # Label smoothing acknowledges that the band boundaries are genuinely fuzzy.
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.06)
    eval_criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.02)
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=learning_rate * 3, total_steps=epochs * max(len(loader), 1),
        pct_start=0.25,
    )

    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  trainable parameters: {params:,}")

    # --- loop ------------------------------------------------------------
    history = {'train_loss': [], 'val_loss': [], 'val_acc': [], 'val_macro_f1': []}
    best_f1, best_state, patience, since_best = -1.0, None, 20, 0

    print("\nTraining...")
    print("-" * 80)

    for epoch in range(epochs):
        model.train()
        running = 0.0
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            running += loss.item() * len(batch_x)

        train_loss = running / max(len(train_y), 1)
        val = evaluate(model, val_x, val_y, eval_criterion, device)

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val['loss'])
        history['val_acc'].append(val['accuracy'])
        history['val_macro_f1'].append(val['macro_f1'])

        if val['macro_f1'] > best_f1:
            best_f1 = val['macro_f1']
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            since_best = 0
        else:
            since_best += 1

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  epoch {epoch + 1:>3}/{epochs}  "
                  f"train_loss {train_loss:.4f}  val_loss {val['loss']:.4f}  "
                  f"val_acc {val['accuracy']:5.2f}%  val_f1 {val['macro_f1']:.3f}  "
                  f"best_f1 {best_f1:.3f}")

        if since_best >= patience:
            print(f"\n  early stop at epoch {epoch + 1} "
                  f"(no macro-F1 gain in {patience} epochs)")
            break

    if best_state:
        model.load_state_dict(best_state)

    # --- evaluation ------------------------------------------------------
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    val_final = evaluate(model, val_x, val_y, eval_criterion, device)
    test_final = evaluate(model, test_x, test_y, eval_criterion, device)

    for title, result in (("VALIDATION (independent scenario mix)", val_final),
                          ("TEST (independent scenario mix)", test_final)):
        print(f"\n{title}")
        print(f"   exact accuracy      {result['accuracy']:.2f}%")
        print(f"   within one band     {result['accuracy_within_1']:.2f}%")
        print(f"   macro F1            {result['macro_f1']:.3f}")
        print(f"   mean band error     {result['mean_abs_error']:.2f}")
        print("\n   per class:")
        for row in result['per_class']:
            print(f"     {row['class']:<20} support {row['support']:>5}  "
                  f"P {row['precision']:.2f}  R {row['recall']:.2f}  F1 {row['f1']:.2f}")
        print_confusion(confusion_matrix(result['truth'], result['predictions']))

    print("\nPer scenario (test split):")
    for scenario in sorted(set(test_scenarios)):
        mask = np.array([s == scenario for s in test_scenarios])
        if not mask.any():
            continue
        exact = np.mean(test_final['predictions'][mask] == test_final['truth'][mask]) * 100
        near = np.mean(np.abs(test_final['predictions'][mask] - test_final['truth'][mask]) <= 1) * 100
        print(f"   {scenario:<28} n {int(mask.sum()):>5}  "
              f"exact {exact:5.1f}%  within-1 {near:5.1f}%")

    # --- persist ---------------------------------------------------------
    model_dir = os.path.join(BACKEND_DIR, 'ml_models', 'trained')
    os.makedirs(model_dir, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    best_path = os.path.join(model_dir, 'conversation_interest_model_best.pth')
    archive_path = os.path.join(model_dir, f'conversation_interest_model_realistic_{stamp}.pth')
    torch.save(model.state_dict(), best_path)
    torch.save(model.state_dict(), archive_path)

    report = {
        'trained_at': datetime.now().isoformat(),
        'feature_dim': FEATURE_DIM,
        'training_conversations': len(train_convos),
        'training_pairs': int(len(y_train)),
        'held_out_scenarios': [],
        'stress_scenarios_available': HELD_OUT_SCENARIOS,
        'split_strategy': 'independent random scenario mix; disjoint generator seeds',
        'decoder_round_trip_rate': round(decoded / max(total, 1), 4),
        'hyperparameters': {
            'epochs_requested': epochs, 'batch_size': batch_size,
            'learning_rate': learning_rate, 'seed': seed,
        },
        'validation': {k: v for k, v in val_final.items()
                       if k not in ('predictions', 'truth')},
        'test_random_scenarios': {k: v for k, v in test_final.items()
                          if k not in ('predictions', 'truth')},
        'history': history,
    }
    report_path = os.path.join(model_dir, f'realistic_training_report_{stamp}.json')
    with open(report_path, 'w', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)

    print(f"\nSaved model      {best_path}")
    print(f"Saved archive    {archive_path}")
    print(f"Saved report     {report_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--conversations', type=int, default=4000)
    parser.add_argument('--epochs', type=int, default=90)
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--learning-rate', type=float, default=8e-4)
    parser.add_argument('--seed', type=int, default=1234)
    args = parser.parse_args()

    train(
        conversations=args.conversations,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )


if __name__ == '__main__':
    main()
