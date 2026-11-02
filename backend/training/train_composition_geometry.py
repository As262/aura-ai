"""Validation-only experiment combining CNN features with geometry scores."""
import argparse
import io
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from api.ai_services_optimized import OptimizedImageAnalysisService
from ml_models.composition_model import COMPOSITION_TYPES, CompositionCNN, composition_preprocess
from training.evaluation import classification_metrics, seed_everything, write_json
from training.train_model import audit_and_split


class GeometryDataset(Dataset):
    def __init__(self, rows, training=False):
        self.rows = rows
        operations = list(composition_preprocess().transforms)
        if training:
            operations[1:1] = [torchvision.transforms.RandomHorizontalFlip(),
                               torchvision.transforms.ColorJitter(brightness=0.12, contrast=0.12, saturation=0.12)]
        self.transform = torchvision.transforms.Compose(operations)
        self.service = OptimizedImageAnalysisService.__new__(OptimizedImageAnalysisService)

    def __len__(self):
        return len(self.rows)

    def geometry(self, image):
        rgb = np.asarray(image.convert('RGB'))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        return torch.tensor([
            self.service._check_rule_of_thirds(gray), self.service._check_centered(gray),
            self.service._check_leading_lines(gray), self.service._check_diagonal(gray),
            self.service._check_symmetry(gray), self.service._check_golden_ratio(gray),
            self.service._check_fill_frame(gray), self.service._check_frame_in_frame(gray),
        ], dtype=torch.float32) / 10.0

    def __getitem__(self, index):
        row = self.rows[index]
        with Image.open(io.BytesIO(row['image'])) as image:
            image = image.convert('RGB')
            return self.transform(image), self.geometry(image), row['label']


class CompositionGeometryModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = CompositionCNN(num_classes=8, pretrained=True, spatial_pool_size=2)
        self.base.classifier = nn.Identity()
        self.head = nn.Sequential(nn.Linear(2048 + 8, 512), nn.ReLU(), nn.Dropout(0.3),
                                  nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.3), nn.Linear(256, 8))

    def forward(self, images, geometry):
        return self.head(torch.cat([self.base.backbone(images), geometry], dim=1))


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    logits, truth = [], []
    for images, geometry, labels in loader:
        images, geometry = images.to(device), geometry.to(device)
        logits.append(((model(images, geometry) + model(images.flip(3), geometry)) / 2).cpu())
        truth.append(labels)
    logits, truth = torch.cat(logits), torch.cat(truth)
    return classification_metrics(truth.numpy(), logits.argmax(1).numpy(), COMPOSITION_TYPES)


def main(args):
    seed_everything(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    splits, audit = audit_and_split(args.data_dir, args.seed, args.split_manifest)
    datasets = {name: GeometryDataset(rows, name == 'train') for name, rows in splits.items()}
    loaders = {name: DataLoader(dataset, batch_size=args.batch_size, shuffle=name == 'train', num_workers=0)
               for name, dataset in datasets.items()}
    model = CompositionGeometryModel().to(device)
    counts = Counter(row['label'] for row in splits['train'])
    weights = torch.tensor([len(splits['train']) / (8 * counts[i]) for i in range(8)], device=device)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
    optimizer = torch.optim.AdamW([{'params': model.base.backbone.parameters(), 'lr': args.learning_rate / 10},
                                   {'params': model.head.parameters(), 'lr': args.learning_rate}], weight_decay=1e-3)
    best, wait, history = -1, 0, []
    for epoch in range(args.epochs):
        model.train()
        for parameter in model.base.backbone.parameters():
            parameter.requires_grad_(epoch >= 3)
        if epoch < 3 or args.freeze_batchnorm:
            model.base.backbone.eval()
            if epoch >= 3:
                for module in model.base.backbone.modules():
                    if isinstance(module, nn.BatchNorm2d):
                        module.eval()
        for images, geometry, labels in loaders['train']:
            images, geometry, labels = images.to(device), geometry.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(images, geometry), labels)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5)
            optimizer.step()
        validation = evaluate(model, loaders['validation'], device)
        history.append({'epoch': epoch + 1, 'validation': validation})
        print(f"Epoch {epoch + 1}/{args.epochs}: val accuracy {validation['accuracy']:.1%}, macro-F1 {validation['macro_f1']:.3f}", flush=True)
        if validation['macro_f1'] > best + 1e-4:
            best = validation['macro_f1']
            wait = 0
            torch.save(model.state_dict(), args.save_dir / 'composition_geometry_best.pth')
        else:
            wait += 1
        if epoch >= 15 and wait >= args.patience:
            break
    write_json(args.save_dir / 'composition_geometry_report.json', {
        'validation': max(history, key=lambda row: row['validation']['macro_f1'])['validation'],
        'epochs_completed': len(history), 'history': history,
        'split_manifest': str(args.split_manifest), 'test_used_for_selection': False,
        'audit': audit,
    })


if __name__ == '__main__':
    import torchvision
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BACKEND / 'training_data')
    parser.add_argument('--save-dir', type=Path, default=BACKEND / 'ml_models/trained/runs/composition_geometry')
    parser.add_argument('--split-manifest', type=Path, default=BACKEND / 'ml_models/trained/composition_data_audit.json')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--learning-rate', type=float, default=3e-4)
    parser.add_argument('--patience', type=int, default=20)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--freeze-batchnorm', action='store_true')
    args = parser.parse_args()
    args.save_dir.mkdir(parents=True, exist_ok=True)
    main(args)
