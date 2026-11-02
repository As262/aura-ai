"""Retrain the selected composition architecture on train+validation data.

Hyperparameters are inherited from the validation-selected spatial-pool-2
checkpoint. The untouched test set is evaluated only after this final fit.
"""
import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from train_model import CompositionDataset, audit_and_split
from ml_models.composition_model import COMPOSITION_TYPES, CompositionCNN
from training.evaluation import classification_metrics, seed_everything, write_json


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


@torch.no_grad()
def evaluate_test(model, loader, device):
    model.eval()
    logits, truth = [], []
    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        output = (model(images) + model(images.flip(3))) / 2
        logits.append(output.cpu())
        truth.append(labels)
    logits = torch.cat(logits)
    truth = torch.cat(truth)
    probability = logits.softmax(1)
    result = classification_metrics(truth.numpy(), probability.argmax(1).numpy(), COMPOSITION_TYPES)
    result['loss'] = float(nn.functional.cross_entropy(logits, truth))
    result['top_2_accuracy'] = float((probability.topk(2, dim=1).indices == truth[:, None]).any(1).float().mean())
    return result


def main(args):
    seed_everything(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if device.type == 'cuda':
        torch.backends.cudnn.benchmark = True
        torch.set_float32_matmul_precision('high')
    splits, audit = audit_and_split(args.data_dir, args.seed, args.split_manifest)
    train_rows = splits['train'] + splits['validation']
    loader_options = dict(batch_size=args.batch_size, num_workers=args.workers,
                          pin_memory=device.type == 'cuda', persistent_workers=args.workers > 0)
    if args.workers > 0:
        loader_options['prefetch_factor'] = 2
    loader = DataLoader(CompositionDataset(train_rows, training=True), shuffle=True, **loader_options)
    test_loader = DataLoader(CompositionDataset(splits['test']), shuffle=False, **loader_options)
    model = CompositionCNN(num_classes=8, pretrained=True, spatial_pool_size=2).to(device)
    counts = Counter(row['label'] for row in train_rows)
    weights = torch.tensor([len(train_rows) / (8 * counts[i]) for i in range(8)], device=device)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
    optimizer = torch.optim.AdamW([
        {'params': model.backbone.parameters(), 'lr': args.learning_rate / 10},
        {'params': model.classifier.parameters(), 'lr': args.learning_rate},
    ], weight_decay=1e-3)
    scaler = torch.amp.GradScaler('cuda', enabled=device.type == 'cuda')
    history = []
    started = time.time()
    for epoch in range(args.epochs):
        model.train()
        for parameter in model.backbone.parameters():
            parameter.requires_grad_(epoch >= 3)
        if epoch < 3 or args.freeze_batchnorm:
            model.backbone.eval()
            if epoch >= 3:
                for module in model.backbone.modules():
                    if isinstance(module, nn.BatchNorm2d):
                        module.eval()
        total_loss = 0.0
        seen = 0
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
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
        history.append({'epoch': epoch + 1, 'train_loss': total_loss / seen})
        print(f'Epoch {epoch + 1}/{args.epochs}: loss {total_loss / seen:.4f}', flush=True)

    args.save_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.save_dir / 'composition_model_best.pth'
    torch.save(model.state_dict(), checkpoint)
    test = evaluate_test(model, test_loader, device)
    metadata = {
        'classes': list(COMPOSITION_TYPES), 'spatial_pool_size': 2,
        'inference_aggregation': 'mean_logits', 'horizontal_flip': True,
        'temperature': 1.0, 'confidence_threshold': 1.0,
        'seed': args.seed, 'batch_size': args.batch_size,
        'learning_rate': args.learning_rate, 'epochs_completed': args.epochs,
        'dataset': 'fixed composition train+validation fit; untouched test evaluation',
        'train_samples': len(train_rows), 'test_samples': len(splits['test']),
        'frozen_split_manifest': str(args.split_manifest),
        'selection_source': 'spatial-pool-2 checkpoint selected by validation macro-F1',
        'test_used_for_selection': False, 'test': test,
        'history': history, 'elapsed_seconds': time.time() - started,
    }
    write_json(args.save_dir / 'composition_metadata.json', metadata)
    write_json(args.save_dir / 'composition_data_audit.json', audit)
    print('Held-out test:', test, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BACKEND / 'training_data')
    parser.add_argument('--save-dir', type=Path, default=BACKEND / 'ml_models/trained/runs/composition_trainval')
    parser.add_argument('--split-manifest', type=Path, default=BACKEND / 'ml_models/trained/composition_data_audit.json')
    parser.add_argument('--epochs', type=int, default=16)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--learning-rate', type=float, default=3e-4)
    parser.add_argument('--workers', type=int, default=0)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--freeze-batchnorm', action='store_true')
    main(parser.parse_args())
