"""Train the eight-class composition CNN with duplicate-safe train/val/test splits.

python training/train_model.py --epochs 80 --batch-size 32 --workers 2
Only validation macro-F1 selects the checkpoint. Test data is evaluated once.
"""
import argparse
import hashlib
import io
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from ml_models.composition_model import COMPOSITION_TYPES, CompositionCNN, composition_preprocess, encode_composition_image
from training.evaluation import classification_metrics, seed_everything, write_json

# A small set of source-folder mistakes found during visual audit. These are
# metadata corrections only: the original images stay where the user put them,
# while the training manifest records the corrected semantic label. The
# corrections are intentionally explicit and auditable rather than inferred
# from the model's own predictions.
COMPOSITION_LABEL_CORRECTIONS = {
    ('rule_of_thirds', 'framing.jpg'): 'frame_within_frame',
    ('rule_of_thirds', 'leading lines.jpg'): 'leading_lines',
    ('rule_of_thirds', 'this is and example of leading lines because the….jpg'): 'leading_lines',
    ('rule_of_thirds', 'this photo using some framing and leading lines….jpg'): 'leading_lines',
    ('leading_lines', 'diagonal.jpg'): 'diagonal',
    ('symmetrical', '82b71a3b-c57b-4251-939a-71738d945b85.jpg'): 'leading_lines',
    ('fill_the_frame', 'frame within a frame, within a frame, within a frame.jpg'): 'frame_within_frame',
}


def corrected_label(path, original_label):
    key = (path.parent.name.casefold(), path.name.casefold())
    return COMPOSITION_LABEL_CORRECTIONS.get(key, original_label)


def audit_and_split(root, seed=42, split_manifest=None):
    """Group exact and near duplicates; quarantine conflicting labels, not users' files."""
    records, invalid = [], []
    for label, name in enumerate(COMPOSITION_TYPES):
        for path in sorted((Path(root) / name).glob('*')):
            if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}:
                continue
            try:
                with Image.open(path) as source:
                    image = ImageOps.exif_transpose(source).convert('RGB')
                    image.load()
                    if min(image.size) < 32:
                        raise ValueError('Image is smaller than 32 pixels')
                    small = np.asarray(image.resize((17, 16)).convert('L'), dtype=np.int16)
                    bits = small[:, 1:] > small[:, :-1]
                    phash = int.from_bytes(np.packbits(bits).tobytes(), 'big')
                    digest = hashlib.sha256(image.tobytes()).hexdigest()
                    # Cache only a resized JPEG, avoiding repeated large-file I/O each epoch.
                    encoded = encode_composition_image(image)
                records.append(dict(path=str(path), label=label, original_label=label,
                                    corrected_label=corrected_label(path, COMPOSITION_TYPES[label]),
                                    sha256=digest,
                                    phash=phash, image=encoded))
            except Exception as exc:
                invalid.append(dict(path=str(path), reason=str(exc)))
    label_by_name = {name: index for index, name in enumerate(COMPOSITION_TYPES)}
    if split_manifest is not None:
        # Re-labeling a training example must not shuffle previously held-out
        # photographs into training. Match the frozen split by decoded-pixel
        # hash, which also makes a Windows manifest portable across machines.
        frozen = json.loads(Path(split_manifest).read_text(encoding='utf-8'))
        by_hash = {record['sha256']: record for record in records}
        splits = {name: [] for name in ('train', 'validation', 'test')}
        seen = set()
        corrections = []
        for name, rows in frozen['splits'].items():
            for row in rows:
                digest = row['sha256']
                if digest in seen:
                    raise ValueError('Frozen composition split contains duplicate leakage')
                if digest not in by_hash:
                    raise ValueError(f'Frozen composition image is missing or changed: {row["path"]}')
                seen.add(digest)
                record = dict(by_hash[digest])
                label = record['corrected_label'] if name == 'train' else row['label']
                record['label'] = label_by_name[label]
                splits[name].append(record)
                original_label = COMPOSITION_TYPES[record['original_label']]
                if name == 'train' and label != original_label:
                    corrections.append(dict(path=record['path'], from_label=original_label, to_label=label))
        # Refuse a manifest that partitions a near-duplicate group.
        for i, first in enumerate(splits):
            for second in list(splits)[:i]:
                if any((a['phash'] ^ b['phash']).bit_count() <= 4
                       for a in splits[first] for b in splits[second]):
                    raise ValueError('Near-duplicate leakage in frozen composition split')
        report = dict(frozen, frozen_split_manifest=str(split_manifest),
                      label_corrections=corrections, held_out_labels_changed=False)
        report['splits'] = {name: [dict(path=r['path'], label=COMPOSITION_TYPES[r['label']],
                                      sha256=r['sha256']) for r in rows]
                            for name, rows in splits.items()}
        return splits, report
    for record in records:
        record['label'] = label_by_name[record['corrected_label']]
    corrections = [
        dict(path=record['path'], from_label=COMPOSITION_TYPES[record['original_label']],
             to_label=record['corrected_label'])
        for record in records
        if record['corrected_label'] != COMPOSITION_TYPES[record['original_label']]
    ]
    parents = list(range(len(records)))

    def root_of(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for i, first in enumerate(records):
        for j in range(i):
            second = records[j]
            if first['sha256'] == second['sha256'] or (first['phash'] ^ second['phash']).bit_count() <= 4:
                parents[root_of(i)] = root_of(j)
    groups = defaultdict(list)
    for i, record in enumerate(records):
        groups[root_of(i)].append(record)
    clean, conflicts = defaultdict(list), []
    for group in groups.values():
        if len({r['label'] for r in group}) > 1:
            conflicts.append([r['path'] for r in group])
        else:
            # Keep one representative; repeated exports are not independent examples.
            clean[group[0]['label']].append(group[0])
    rng = np.random.default_rng(seed)
    splits = {name: [] for name in ('train', 'validation', 'test')}
    for label, name in enumerate(COMPOSITION_TYPES):
        rows = clean[label]
        if len(rows) < 10:
            raise ValueError(f'{name}: only {len(rows)} unique, unambiguous images; need at least 10')
        rng.shuffle(rows)
        held = max(2, round(len(rows) * 0.15))
        splits['test'].extend(rows[:held])
        splits['validation'].extend(rows[held:2 * held])
        splits['train'].extend(rows[2 * held:])
    report = {
        'seed': seed, 'images_found': len(records), 'invalid': invalid,
        'conflicting_duplicate_groups': conflicts,
        'label_corrections': corrections,
        'duplicates_removed': len(records) - sum(len(v) for v in clean.values()) - sum(map(len, conflicts)),
        'splits': {name: [dict(path=r['path'], label=COMPOSITION_TYPES[r['label']],
                             sha256=r['sha256']) for r in rows] for name, rows in splits.items()},
    }
    return splits, report


class CompositionDataset(Dataset):
    def __init__(self, records, training=False):
        self.records = records
        # Geometry-preserving transforms: crops/rotation can change the composition label.
        operations = list(composition_preprocess().transforms)
        if training:
            operations[1:1] = [transforms.RandomHorizontalFlip(),
                               transforms.ColorJitter(brightness=0.12, contrast=0.12, saturation=0.12)]
        self.transform = transforms.Compose(operations)

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        row = self.records[index]
        with Image.open(io.BytesIO(row['image'])) as image:
            return self.transform(image.convert('RGB')), row['label']


@torch.no_grad()
def evaluate(model, loader, device, temperature=1.0, horizontal_flip=False):
    model.eval()
    logits, truth = [], []
    for images, labels in loader:
        images = images.to(device)
        output = model(images)
        if horizontal_flip:
            output = (output + model(images.flip(3))) / 2
        logits.append(output.cpu())
        truth.append(labels)
    logits, truth = torch.cat(logits), torch.cat(truth)
    probabilities = (logits / temperature).softmax(1)
    result = classification_metrics(truth.numpy(), probabilities.argmax(1).numpy(), COMPOSITION_TYPES)
    result['loss'] = float(nn.functional.cross_entropy(logits / temperature, truth))
    result['brier_score'] = float((probabilities - nn.functional.one_hot(truth, len(COMPOSITION_TYPES))).square().sum(1).mean())
    result['top_2_accuracy'] = float((probabilities.topk(2, dim=1).indices == truth[:, None]).any(1).float().mean())
    return result, logits, truth


def train_composition_model(data_dir=BACKEND / 'training_data', epochs=80, batch_size=32,
                            learning_rate=3e-4, save_dir=BACKEND / 'ml_models/trained',
                            workers=2, patience=15, seed=42, split_manifest=None,
                            spatial_pool_size=1, freeze_batchnorm=False, defer_test=False):
    seed_everything(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    splits, audit = audit_and_split(data_dir, seed, split_manifest)
    write_json(save_dir / 'composition_data_audit.json', audit)
    print(f'Device: {device}; unique images: ' + ', '.join(f'{k}={len(v)}' for k, v in splits.items()), flush=True)
    loaders = {name: DataLoader(CompositionDataset(rows, name == 'train'), batch_size=batch_size,
                               shuffle=name == 'train', num_workers=workers,
                               pin_memory=device.type == 'cuda', persistent_workers=workers > 0)
               for name, rows in splits.items()}
    model = CompositionCNN(num_classes=len(COMPOSITION_TYPES), pretrained=True,
                           spatial_pool_size=spatial_pool_size).to(device)
    counts = Counter(row['label'] for row in splits['train'])
    weights = torch.tensor([len(splits['train']) / (8 * counts[i]) for i in range(8)], device=device)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
    optimizer = torch.optim.AdamW([
        {'params': model.backbone.parameters(), 'lr': learning_rate / 10},
        {'params': model.classifier.parameters(), 'lr': learning_rate},
    ], weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=4, factor=0.5)
    scaler = torch.amp.GradScaler('cuda', enabled=device.type == 'cuda')
    history, best_f1, wait, best_epoch = [], -1, 0, 0
    start = time.time()
    for epoch in range(epochs):
        model.train()
        for parameter in model.backbone.parameters():
            parameter.requires_grad_(epoch >= 3)
        if epoch < 3:
            model.backbone.eval()
        elif freeze_batchnorm:
            # Small photo batches should not overwrite ImageNet normalization
            # statistics; the convolutional weights still receive gradients.
            for module in model.backbone.modules():
                if isinstance(module, nn.BatchNorm2d):
                    module.eval()
        total_loss, seen = 0, 0
        for images, labels in loaders['train']:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device.type, enabled=device.type == 'cuda'):
                loss = criterion(model(images), labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 5)
            scaler.step(optimizer)
            scaler.update()
            total_loss += float(loss.detach()) * len(labels)
            seen += len(labels)
        validation, _, _ = evaluate(model, loaders['validation'], device, horizontal_flip=True)
        scheduler.step(validation['macro_f1'])
        history.append(dict(epoch=epoch + 1, train_loss=total_loss / seen, validation=validation))
        if validation['macro_f1'] > best_f1 + 1e-4:
            best_f1, wait, best_epoch = validation['macro_f1'], 0, epoch + 1
            torch.save(model.state_dict(), save_dir / 'composition_model_best.pth')
        else:
            wait += 1
        write_json(save_dir / 'composition_progress.json', dict(history=history, best_epoch=best_epoch))
        print(f"Epoch {epoch + 1}/{epochs}: loss {total_loss / seen:.4f}, val accuracy {validation['accuracy']:.1%}, macro-F1 {validation['macro_f1']:.3f}", flush=True)
        if epoch >= 15 and wait >= patience:
            break
    model.load_state_dict(torch.load(save_dir / 'composition_model_best.pth', map_location=device, weights_only=True))
    validation, logits, truth = evaluate(model, loaders['validation'], device, horizontal_flip=True)
    # Fit confidence temperature solely on validation data.
    candidates = np.linspace(0.7, 5.0, 87)
    temperature = float(min(candidates, key=lambda t: float(nn.functional.cross_entropy(logits / t, truth))))
    validation, _, _ = evaluate(model, loaders['validation'], device, temperature, horizontal_flip=True)
    probabilities = (logits / temperature).softmax(1)
    confidence, predicted = probabilities.max(1)
    thresholds = np.linspace(0.6, 0.95, 36)
    def selective_metrics(threshold):
        selected = confidence >= threshold
        return dict(samples=int(selected.sum()), coverage=float(selected.float().mean()),
                    accuracy=float((predicted[selected] == truth[selected]).float().mean()) if selected.any() else None)
    confidence_threshold = next((float(value) for value in thresholds
                                 if selective_metrics(value)['samples'] >= 20
                                 and selective_metrics(value)['accuracy'] >= 0.80), 1.0)
    test = None if defer_test else evaluate(model, loaders['test'], device, temperature, horizontal_flip=True)[0]
    report = dict(classes=list(COMPOSITION_TYPES), temperature=temperature, seed=seed,
                  spatial_pool_size=spatial_pool_size, inference_aggregation='mean_logits',
                  horizontal_flip=True, frozen_split_manifest=str(split_manifest) if split_manifest else None,
                  confidence_threshold=confidence_threshold,
                  confidence_target_met=confidence_threshold < 1.0,
                  selective_validation=selective_metrics(confidence_threshold),
                  freeze_batchnorm=freeze_batchnorm, learning_rate=learning_rate, batch_size=batch_size,
                  preprocessing='EXIF transpose, RGB, thumbnail <=320, JPEG quality 92, PIL resize 224x224, ImageNet normalization',
                  epochs_completed=len(history), best_epoch=best_epoch, elapsed_seconds=time.time() - start,
                  dataset='local manually classified composition images', validation=validation, test=test,
                  history=history, test_used_for_selection=False)
    write_json(save_dir / 'composition_metadata.json', report)
    print('Test evaluation deferred' if defer_test else f'Held-out test: {test}', flush=True)
    return model, report


def evaluate_checkpoint(args):
    """Evaluate the selected checkpoint using its exact serving aggregation."""
    seed_everything(args.seed)
    metadata_path = args.save_dir / 'composition_metadata.json'
    report = json.loads(metadata_path.read_text(encoding='utf-8'))
    manifest = args.save_dir / 'composition_data_audit.json'
    splits, _ = audit_and_split(args.data_dir, args.seed, manifest)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = CompositionCNN(pretrained=False, spatial_pool_size=report.get('spatial_pool_size', 1)).to(device)
    model.load_state_dict(torch.load(args.save_dir / 'composition_model_best.pth', map_location=device, weights_only=True))
    for name in ('validation', 'test'):
        loader = DataLoader(CompositionDataset(splits[name]), batch_size=args.batch_size,
                            shuffle=False, num_workers=args.workers)
        report[name], _, _ = evaluate(model, loader, device, report['temperature'],
                                      horizontal_flip=report.get('horizontal_flip', False))
    report['checkpoint_sha256'] = hashlib.sha256((args.save_dir / 'composition_model_best.pth').read_bytes()).hexdigest()
    write_json(metadata_path, report)
    print('Held-out test:', report['test'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BACKEND / 'training_data')
    parser.add_argument('--save-dir', type=Path, default=BACKEND / 'ml_models/trained')
    parser.add_argument('--epochs', type=int, default=80)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--learning-rate', type=float, default=3e-4)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--patience', type=int, default=15)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--split-manifest', type=Path, help='Reuse an existing fixed split by pixel hash')
    parser.add_argument('--spatial-pool-size', type=int, choices=(1, 2), default=1)
    parser.add_argument('--freeze-batchnorm', action='store_true')
    parser.add_argument('--defer-test', action='store_true', help='Report validation only until model selection is complete')
    parser.add_argument('--evaluate-only', action='store_true', help='Evaluate an existing checkpoint with serving-time aggregation')
    args = parser.parse_args()
    if args.evaluate_only:
        evaluate_checkpoint(args)
    else:
        kwargs = vars(args).copy()
        kwargs.pop('evaluate_only')
        train_composition_model(**kwargs)
