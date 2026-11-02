"""Benchmark frozen ImageNet composition classifiers on the fixed split.

This is designed for the current low-data setting. It extracts deterministic
ResNet embeddings once, tries validation-only classifier choices, and evaluates
the held-out test split only for the selected candidate.
"""
import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, LinearSVC
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from api.ai_services_optimized import OptimizedImageAnalysisService
from ml_models.composition_model import COMPOSITION_TYPES
from training.evaluation import seed_everything, write_json
from training.train_model import audit_and_split


NORMALIZE = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
TRANSFORM = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), NORMALIZE])


class CachedImageDataset(Dataset):
    def __init__(self, records):
        self.records = records

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        row = self.records[index]
        with Image.open(__import__('io').BytesIO(row['image'])) as image:
            return TRANSFORM(image.convert('RGB')), row['label']


def metrics(truth, prediction):
    return {
        'accuracy': float(accuracy_score(truth, prediction)),
        'macro_f1': float(f1_score(truth, prediction, average='macro', zero_division=0)),
    }


def extract_features(rows, backbone, device, batch_size, include_geometry):
    loader = DataLoader(CachedImageDataset(rows), batch_size=batch_size, shuffle=False, num_workers=0)
    features, labels = [], []
    service = OptimizedImageAnalysisService.__new__(OptimizedImageAnalysisService)
    with torch.no_grad():
        for images, target in loader:
            images = images.to(device)
            original = backbone(images)
            mirrored = backbone(images.flip(3))
            features.append(((original + mirrored) / 2).cpu().numpy())
            labels.extend(target.tolist())
    vectors = np.concatenate(features).astype(np.float32)
    if include_geometry:
        geometry = []
        for row in rows:
            with Image.open(__import__('io').BytesIO(row['image'])) as image:
                rgb = np.asarray(image.convert('RGB'))
            gray = __import__('cv2').cvtColor(rgb, __import__('cv2').COLOR_RGB2GRAY)
            geometry.append([
                service._check_rule_of_thirds(gray), service._check_centered(gray),
                service._check_leading_lines(gray), service._check_diagonal(gray),
                service._check_symmetry(gray), service._check_golden_ratio(gray),
                service._check_fill_frame(gray), service._check_frame_in_frame(gray),
            ])
        vectors = np.concatenate([vectors, np.asarray(geometry, dtype=np.float32)], axis=1)
    return vectors, np.asarray(labels, dtype=np.int64)


def candidates():
    for c in (0.01, 0.1, 1, 10, 100):
        yield f'logistic_c{c}', make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=3000, class_weight='balanced'))
        yield f'linear_svc_c{c}', make_pipeline(StandardScaler(), LinearSVC(C=c, class_weight='balanced', max_iter=10000))
        yield f'rbf_svc_c{c}', make_pipeline(StandardScaler(), SVC(C=c, kernel='rbf', gamma='scale', class_weight='balanced', probability=True))


def build_backbone(name):
    if name == 'resnet50':
        model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        model.fc = torch.nn.Identity()
    elif name == 'convnext_tiny':
        model = models.convnext_tiny(weights=models.ConvNeXt_Tiny_Weights.DEFAULT)
        model.classifier[2] = torch.nn.Identity()
    elif name == 'swin_t':
        model = models.swin_t(weights=models.Swin_T_Weights.DEFAULT)
        model.head = torch.nn.Identity()
    elif name == 'vit_b_16':
        model = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
        model.heads = torch.nn.Identity()
    else:
        raise ValueError(f'Unsupported backbone: {name}')
    return model


def main(args):
    seed_everything(args.seed)
    split_manifest = BACKEND / 'ml_models/trained/composition_data_audit.json'
    splits, _ = audit_and_split(args.data_dir, args.seed, split_manifest)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = build_backbone(args.backbone)
    model = model.to(device).eval()
    results = []
    cached = {}
    for include_geometry in (False, True):
        for split_name in ('train', 'validation', 'test'):
            cached[(include_geometry, split_name)] = extract_features(
                splits[split_name], model, device, args.batch_size, include_geometry)
        train_x, train_y = cached[(include_geometry, 'train')]
        val_x, val_y = cached[(include_geometry, 'validation')]
        for name, classifier in candidates():
            classifier.fit(train_x, train_y)
            validation = metrics(val_y, classifier.predict(val_x))
            results.append(dict(candidate=name, include_geometry=include_geometry,
                                feature_dim=int(train_x.shape[1]), validation=validation,
                                classifier=classifier))
    selected = max(results, key=lambda item: (item['validation']['macro_f1'], item['validation']['accuracy']))
    # Test is used exactly once, after validation selection.
    test_x, test_y = cached[(selected['include_geometry'], 'test')]
    selected['test'] = metrics(test_y, selected['classifier'].predict(test_x))
    output = [{k: v for k, v in item.items() if k not in ('classifier',)} for item in results]
    report = dict(model=f'{args.backbone} frozen embedding + sklearn classifier', seed=args.seed,
                  split_strategy='fixed composition audit manifest; test used after validation selection',
                  selected={k: v for k, v in selected.items() if k not in ('classifier',)},
                  candidates=output)
    args.save_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected['classifier'], args.save_dir / 'composition_embedding_classifier.joblib')
    torch.save(model.state_dict(), args.save_dir / f'composition_embedding_backbone_{args.backbone}.pth')
    write_json(args.save_dir / 'composition_embedding_report.json', report)
    print(json.dumps(report['selected'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BACKEND / 'training_data')
    parser.add_argument('--save-dir', type=Path, default=BACKEND / 'ml_models/trained/embedding_benchmark')
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--backbone', choices=('resnet50', 'convnext_tiny', 'swin_t', 'vit_b_16'), default='resnet50')
    main(parser.parse_args())
