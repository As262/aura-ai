"""Train NIMA on human AVA vote distributions, selecting by validation EMD.

python training/train_aesthetic_model.py --ava training_data/public/ava --epochs 30
Supports either the downloader's manifest or official AVA.txt + images/.
Reports EMD, score MAE/RMSE, Pearson/Spearman, and binary >5 accuracy separately.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy.stats import pearsonr, spearmanr
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from ml_models.aesthetic_model import NIMA, aesthetic_preprocess
from training.evaluation import seed_everything, write_json


def load_samples(root, seed):
    root = Path(root)
    if (root / 'manifest.json').exists():
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        if not manifest.get('complete'):
            raise ValueError('Public dataset download is incomplete')
        rows = manifest['samples']
        provenance = {k: v for k, v in manifest.items() if k not in ('samples', 'invalid')}
    else:
        rows, seen = [], set()
        for line in (root / 'AVA.txt').read_text().splitlines():
            fields = line.split()
            if len(fields) < 12:
                continue
            path = root / 'images' / f'{fields[1]}.jpg'
            counts = [int(value) for value in fields[2:12]]
            if not path.exists() or sum(counts) <= 0:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            bucket = int(hashlib.sha256(f'{seed}:{digest}'.encode()).hexdigest()[:8], 16) % 100
            split = 'test' if bucket < 10 else 'validation' if bucket < 20 else 'train'
            rows.append(dict(image_id=fields[1], image=f'images/{fields[1]}.jpg',
                             rating_counts=counts, sha256=digest, split=split))
        provenance = dict(dataset='official local AVA', seed=seed)
    splits = {name: [row for row in rows if row['split'] == name]
              for name in ('train', 'validation', 'test')}
    if any(len(rows) < 50 for rows in splits.values()):
        raise ValueError('Need at least 50 labeled images in every split')
    hashes = [{row['sha256'] for row in rows} for rows in splits.values()]
    if any(hashes[i] & hashes[j] for i in range(3) for j in range(i)):
        raise ValueError('Duplicate image leakage between splits')
    return splits, provenance


class AVADataset(Dataset):
    def __init__(self, root, samples, training=False, cache_images=False):
        self.root, self.samples = Path(root), samples
        ops = list(aesthetic_preprocess().transforms)
        if training:
            ops.insert(1, transforms.RandomHorizontalFlip())
        self.transform = transforms.Compose(ops)
        self.cached_images = None
        if cache_images:
            # About 3.1 GB for the training split, avoiding tens of thousands
            # of OneDrive file opens and JPEG decodes on every training epoch.
            self.cached_images = []
            for row in samples:
                with Image.open(self.root / row['image']) as image:
                    rgb = ImageOps.exif_transpose(image).convert('RGB')
                    self.cached_images.append(np.asarray(transforms.functional.resize(rgb, [224, 224])).copy())

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        row = self.samples[index]
        if self.cached_images is not None:
            tensor = self.transform(Image.fromarray(self.cached_images[index]))
        else:
            with Image.open(self.root / row['image']) as image:
                tensor = self.transform(ImageOps.exif_transpose(image).convert('RGB'))
        counts = np.asarray(row['rating_counts'], dtype=np.float32)
        return tensor, torch.from_numpy(counts / counts.sum())


def emd_loss(predicted, target):
    return ((predicted.cumsum(1) - target.cumsum(1)).square().mean(1) + 1e-8).sqrt().mean()


def distribution_metrics(prediction, truth):
    bins = torch.arange(1, 11, dtype=torch.float32)
    predicted_scores, true_scores = (prediction * bins).sum(1).numpy(), (truth * bins).sum(1).numpy()
    difference = predicted_scores - true_scores
    def correlation(function):
        if np.std(predicted_scores) < 1e-6 or np.std(true_scores) < 1e-6:
            return 0.0
        statistic = float(function(predicted_scores, true_scores).statistic)
        return statistic if np.isfinite(statistic) else 0.0
    return dict(samples=len(truth), emd=float(emd_loss(prediction, truth)),
                mae=float(np.abs(difference).mean()), rmse=float(np.sqrt(np.mean(difference ** 2))),
                pearson=correlation(pearsonr), spearman=correlation(spearmanr),
                binary_accuracy=float(np.mean((predicted_scores > 5) == (true_scores > 5))))


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    predicted, truth = [], []
    for images, targets in loader:
        predicted.append(model(images.to(device)).cpu())
        truth.append(targets)
    return distribution_metrics(torch.cat(predicted), torch.cat(truth))


def train(args):
    seed_everything(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    splits, provenance = load_samples(args.ava, args.seed)
    args.save_dir.mkdir(parents=True, exist_ok=True)
    loaders = {name: DataLoader(AVADataset(args.ava, rows, name == 'train', args.cache_images),
                               batch_size=args.batch, shuffle=name == 'train', num_workers=args.workers,
                               pin_memory=device.type == 'cuda', persistent_workers=args.workers > 0)
               for name, rows in splits.items()}
    print(f'Device: {device}; splits: ' + str({k: len(v) for k, v in splits.items()}), flush=True)
    model = NIMA(pretrained_backbone=True).to(device)
    if args.resume_from:
        model.load_state_dict(torch.load(args.resume_from, map_location=device, weights_only=True))
    # Transfer learning: train the head first, then the final four bottleneck blocks.
    for parameter in model.features.parameters():
        parameter.requires_grad_(False)
    optimizer = torch.optim.AdamW([
        dict(params=model.head.parameters(), lr=args.lr),
        dict(params=model.features[-args.unfreeze_blocks:].parameters(), lr=args.lr / 10),
    ], weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
    scaler = torch.amp.GradScaler('cuda', enabled=device.type == 'cuda')
    history, best, wait, best_epoch = [], float('inf'), 0, 0
    initial_validation = None
    if args.resume_from:
        # A fine-tune must outperform its starting checkpoint on validation;
        # otherwise retain that checkpoint instead of saving a regression.
        initial_validation = evaluate(model, loaders['validation'], device)
        best = initial_validation['emd']
        torch.save(model.state_dict(), args.save_dir / 'aesthetic_nima.pth')
    start = time.time()
    for epoch in range(args.epochs):
        model.train()
        model.features.eval()  # preserve pretrained BatchNorm statistics on a smaller domain
        if epoch >= (0 if args.resume_from else 2):
            for parameter in model.features[-args.unfreeze_blocks:].parameters():
                parameter.requires_grad_(True)
        running, samples = 0, 0
        for images, targets in loaders['train']:
            images, targets = images.to(device), targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device.type, enabled=device.type == 'cuda'):
                predictions = model(images)
                loss = emd_loss(predictions.float(), targets)
                if args.score_loss_weight:
                    bins = torch.arange(1, 11, device=device)
                    loss = loss + args.score_loss_weight * nn.functional.mse_loss(
                        (predictions.float() * bins).sum(1), (targets * bins).sum(1))
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 5)
            scaler.step(optimizer)
            scaler.update()
            running += float(loss.detach()) * len(images)
            samples += len(images)
        validation = evaluate(model, loaders['validation'], device)
        scheduler.step(validation['emd'])
        history.append(dict(epoch=epoch + 1, train_emd=running / samples, validation=validation))
        if validation['emd'] < best - 1e-5:
            best, wait, best_epoch = validation['emd'], 0, epoch + 1
            torch.save(model.state_dict(), args.save_dir / 'aesthetic_nima.pth')
        else:
            wait += 1
        write_json(args.save_dir / 'aesthetic_progress.json', dict(history=history, best_epoch=best_epoch))
        print(f"Epoch {epoch + 1}/{args.epochs}: EMD {running / samples:.4f}; val EMD {validation['emd']:.4f}; MAE {validation['mae']:.3f}; Spearman {validation['spearman']:.3f}", flush=True)
        if epoch >= 10 and wait >= args.patience:
            break
    model.load_state_dict(torch.load(args.save_dir / 'aesthetic_nima.pth', map_location=device, weights_only=True))
    validation = evaluate(model, loaders['validation'], device)
    test = None if args.defer_test else evaluate(model, loaders['test'], device)
    # A constant training-mean distribution gives the meaningful baseline for regression.
    train_distribution = np.mean([np.asarray(row['rating_counts']) / sum(row['rating_counts'])
                                  for row in splits['train']], axis=0)
    truth = torch.tensor(np.stack([np.asarray(row['rating_counts']) / sum(row['rating_counts'])
                                  for row in splits['test']]), dtype=torch.float32)
    baseline = distribution_metrics(torch.tensor(train_distribution, dtype=torch.float32).expand(len(truth), -1), truth)
    report = dict(model='NIMA MobileNetV2', provenance=provenance, seed=args.seed,
                  split_sizes={k: len(v) for k, v in splits.items()}, epochs_completed=len(history),
                  best_epoch=best_epoch, elapsed_seconds=time.time() - start, validation=validation,
                  test=test, constant_baseline=baseline, history=history, test_used_for_selection=False,
                  resume_from=str(args.resume_from) if args.resume_from else None,
                  initial_validation=initial_validation,
                  unfreeze_blocks=args.unfreeze_blocks, score_loss_weight=args.score_loss_weight,
                  preprocessing='EXIF transpose, RGB, PIL bilinear resize 224x224, ImageNet normalization')
    write_json(args.save_dir / 'aesthetic_training_report.json', report)
    print('Held-out test:', test, 'Baseline:', baseline, flush=True)


def evaluate_checkpoint(args):
    """Evaluate an existing best checkpoint without changing its weights."""
    seed_everything(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    splits, provenance = load_samples(args.ava, args.seed)
    loaders = {name: DataLoader(AVADataset(args.ava, rows, False),
                               batch_size=args.batch, shuffle=False, num_workers=args.workers,
                               pin_memory=device.type == 'cuda', persistent_workers=args.workers > 0)
               for name, rows in splits.items()}
    model = NIMA(pretrained_backbone=False).to(device)
    model.load_state_dict(torch.load(args.save_dir / 'aesthetic_nima.pth',
                                     map_location=device, weights_only=True))
    validation, test = evaluate(model, loaders['validation'], device), evaluate(model, loaders['test'], device)
    train_distribution = np.mean([np.asarray(row['rating_counts']) / sum(row['rating_counts'])
                                  for row in splits['train']], axis=0)
    truth = torch.tensor(np.stack([np.asarray(row['rating_counts']) / sum(row['rating_counts'])
                                  for row in splits['test']]), dtype=torch.float32)
    baseline = distribution_metrics(torch.tensor(train_distribution, dtype=torch.float32).expand(len(truth), -1), truth)
    progress_path = args.save_dir / 'aesthetic_progress.json'
    progress = json.loads(progress_path.read_text(encoding='utf-8')) if progress_path.exists() else {}
    report = dict(model='NIMA MobileNetV2', provenance=provenance, seed=args.seed,
                  split_sizes={k: len(v) for k, v in splits.items()},
                  epochs_completed=len(progress.get('history', [])),
                  best_epoch=progress.get('best_epoch'), validation=validation, test=test,
                  constant_baseline=baseline, history=progress.get('history', []),
                  test_used_for_selection=False)
    write_json(args.save_dir / 'aesthetic_training_report.json', report)
    print('Held-out test:', test, 'Baseline:', baseline, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ava', type=Path, required=True)
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--batch', type=int, default=32)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--patience', type=int, default=7)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--save-dir', type=Path, default=BACKEND / 'ml_models/trained')
    parser.add_argument('--evaluate-only', action='store_true',
                         help='Evaluate the existing aesthetic_nima.pth without training')
    parser.add_argument('--resume-from', type=Path)
    parser.add_argument('--unfreeze-blocks', type=int, choices=range(1, 20), default=5)
    parser.add_argument('--score-loss-weight', type=float, default=0.0)
    parser.add_argument('--cache-images', action='store_true')
    parser.add_argument('--defer-test', action='store_true', help='Select on validation before evaluating the test set')
    args = parser.parse_args()
    evaluate_checkpoint(args) if args.evaluate_only else train(args)
