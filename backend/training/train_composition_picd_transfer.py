"""Transfer-learn the composition model from PICD, then select on local validation.

PICD supplies high-precision auxiliary labels for rule-of-thirds, centered,
diagonal, and leading-line geometry. The local fixed train/validation/test split
remains authoritative for the final eight-class checkpoint.
"""
import argparse
import io
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import TypedDict

import numpy as np
import torch
from PIL import Image, ImageOps
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from ml_models.composition_model import COMPOSITION_TYPES, CompositionCNN, encode_composition_image
from training.evaluation import classification_metrics, seed_everything, write_json
from training.train_model import audit_and_split


NORMALIZE = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])


class Row(TypedDict):
    path: Path
    label: int


class ImagePathDataset(Dataset):
    def __init__(self, rows, training=False):
        self.rows = rows
        operations = [transforms.Resize((224, 224))]
        if training:
            operations.extend([transforms.RandomHorizontalFlip(),
                               transforms.ColorJitter(brightness=0.12, contrast=0.12, saturation=0.12)])
        operations.extend([transforms.ToTensor(), NORMALIZE])
        self.transform = transforms.Compose(operations)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        with Image.open(row['path']) as source:
            image = ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((320, 320))
        return self.transform(image), row['label']


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    logits, truth = [], []
    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        output = (model(images) + model(images.flip(3))) / 2
        logits.append(output.cpu())
        truth.append(labels)
    logits, truth = torch.cat(logits), torch.cat(truth)
    probabilities = logits.softmax(1)
    result = classification_metrics(truth.numpy(), probabilities.argmax(1).numpy(), COMPOSITION_TYPES)
    result['loss'] = float(nn.functional.cross_entropy(logits, truth))
    result['top_2_accuracy'] = float((probabilities.topk(2, dim=1).indices == truth[:, None]).any(1).float().mean())
    return result


def loader_options(args, device):
    options = dict(batch_size=args.batch_size, num_workers=args.workers,
                   pin_memory=device.type == 'cuda', persistent_workers=args.workers > 0)
    if args.workers > 0:
        options['prefetch_factor'] = 2
    return options


def train_epoch(model, loader, criterion, optimizer, scaler, device):
    model.train()
    total_loss, seen = 0.0, 0
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
    return total_loss / seen


def local_rows(split) -> list[Row]:
    return [Row(path=Path(row['path']), label=int(row['label'])) for row in split]


def external_rows(manifest_path) -> list[Row]:
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    labels = {name: index for index, name in enumerate(COMPOSITION_TYPES)}
    return [Row(path=Path(row['path']), label=labels[row['label']]) for row in manifest['samples']]


def main(args):
    seed_everything(args.seed)
    random.seed(args.seed)
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.set_float32_matmul_precision('high')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    splits, audit = audit_and_split(args.data_dir, args.seed, args.split_manifest)
    external = external_rows(args.external_manifest)
    train_rows = local_rows(splits['train'])
    validation_rows = local_rows(splits['validation'])
    test_rows = local_rows(splits['test'])
    options = loader_options(args, device)
    external_loader = DataLoader(ImagePathDataset(external, training=True), shuffle=True, **options)
    train_loader = DataLoader(ImagePathDataset(train_rows, training=True), shuffle=True, **options)
    validation_loader = DataLoader(ImagePathDataset(validation_rows), shuffle=False, **options)
    test_loader = DataLoader(ImagePathDataset(test_rows), shuffle=False, **options)

    model = CompositionCNN(num_classes=8, pretrained=True, spatial_pool_size=2).to(device)
    scaler = torch.amp.GradScaler('cuda', enabled=device.type == 'cuda')
    history = []
    started = time.time()

    external_counts = Counter(row['label'] for row in external)
    external_weights = torch.ones(8, device=device)
    for label, count in external_counts.items():
        external_weights[label] = len(external) / (len(external_counts) * count)
    external_criterion = nn.CrossEntropyLoss(weight=external_weights, label_smoothing=0.03)
    external_optimizer = torch.optim.AdamW(model.parameters(), lr=args.external_learning_rate, weight_decay=1e-3)
    for epoch in range(args.external_epochs):
        loss = train_epoch(model, external_loader, external_criterion, external_optimizer, scaler, device)
        print(f'PICD epoch {epoch + 1}/{args.external_epochs}: loss {loss:.4f}', flush=True)
        history.append(dict(stage='picd', epoch=epoch + 1, loss=loss))

    local_counts = {int(label): count for label, count in Counter(row['label'] for row in train_rows).items()}
    local_weights = torch.tensor([len(train_rows) / (8 * local_counts.get(i, 1)) for i in range(8)], device=device)
    criterion = nn.CrossEntropyLoss(weight=local_weights, label_smoothing=0.05)
    optimizer = torch.optim.AdamW([
        {'params': model.backbone.parameters(), 'lr': args.learning_rate / 10},
        {'params': model.classifier.parameters(), 'lr': args.learning_rate},
    ], weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=4, factor=0.5)
    best_f1, best_epoch, wait = -1.0, 0, 0
    args.save_dir.mkdir(parents=True, exist_ok=True)
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
        loss = train_epoch(model, train_loader, criterion, optimizer, scaler, device)
        validation = evaluate(model, validation_loader, device)
        scheduler.step(validation['macro_f1'])
        history.append(dict(stage='local', epoch=epoch + 1, train_loss=loss, validation=validation))
        print(f'Local epoch {epoch + 1}/{args.epochs}: loss {loss:.4f}, '
              f'val accuracy {validation["accuracy"]:.1%}, macro-F1 {validation["macro_f1"]:.3f}', flush=True)
        if validation['macro_f1'] > best_f1 + 1e-4:
            best_f1, best_epoch, wait = validation['macro_f1'], epoch + 1, 0
            torch.save(model.state_dict(), args.save_dir / 'composition_model_best.pth')
        else:
            wait += 1
        if epoch >= 15 and wait >= args.patience:
            break

    model.load_state_dict(torch.load(args.save_dir / 'composition_model_best.pth', map_location=device, weights_only=True))
    validation = evaluate(model, validation_loader, device)
    test = evaluate(model, test_loader, device) if args.evaluate_test else None
    report = dict(classes=list(COMPOSITION_TYPES), device=str(device), seed=args.seed,
                  external_manifest=str(args.external_manifest), external_samples=len(external),
                  external_mapping='PICD high-precision geometry folders mapped to four local labels',
                  spatial_pool_size=2, inference_aggregation='mean_logits', horizontal_flip=True,
                  freeze_batchnorm=args.freeze_batchnorm, batch_size=args.batch_size,
                  workers=args.workers, picd_epochs=args.external_epochs,
                  local_epochs_completed=len([row for row in history if row['stage'] == 'local']),
                  best_epoch=best_epoch, validation=validation, test=test,
                  test_used_for_selection=False, fixed_split_audit=audit,
                  elapsed_seconds=time.time() - started, history=history)
    write_json(args.save_dir / 'composition_metadata.json', report)
    write_json(args.save_dir / 'composition_data_audit.json', audit)
    print(json.dumps(dict(validation=validation, test=test, checkpoint=str(args.save_dir / 'composition_model_best.pth')), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BACKEND / 'training_data')
    parser.add_argument('--split-manifest', type=Path, default=BACKEND / 'ml_models/trained/composition_data_audit.json')
    parser.add_argument('--external-manifest', type=Path, default=Path(r'C:\tmp\agent-tmp\picd_subset\manifest.json'))
    parser.add_argument('--save-dir', type=Path, default=BACKEND / 'ml_models/trained/runs/composition_picd_transfer')
    parser.add_argument('--external-epochs', type=int, default=8)
    parser.add_argument('--epochs', type=int, default=80)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--external-learning-rate', type=float, default=3e-4)
    parser.add_argument('--learning-rate', type=float, default=3e-4)
    parser.add_argument('--workers', type=int, default=0)
    parser.add_argument('--patience', type=int, default=20)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--freeze-batchnorm', action='store_true')
    parser.add_argument('--evaluate-test', action='store_true')
    main(parser.parse_args())
