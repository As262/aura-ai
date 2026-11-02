"""Compare validation-only ensembles of spatial composition checkpoints."""
import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from ml_models.composition_model import COMPOSITION_TYPES, CompositionCNN
from training.evaluation import classification_metrics, seed_everything
from training.train_model import CompositionDataset, audit_and_split


@torch.no_grad()
def logits_for(model, loader, device):
    model.eval()
    logits, truth = [], []
    for images, labels in loader:
        images = images.to(device)
        logits.append(((model(images) + model(images.flip(3))) / 2).cpu())
        truth.append(labels)
    return torch.cat(logits), torch.cat(truth)


def score(logits, truth):
    prediction = logits.argmax(1).numpy()
    return classification_metrics(truth.numpy(), prediction, COMPOSITION_TYPES)


def main(args):
    seed_everything(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    splits, _ = audit_and_split(args.data_dir, args.seed, args.split_manifest)
    loader = DataLoader(CompositionDataset(splits['validation']), batch_size=args.batch_size,
                        shuffle=False, num_workers=0)
    all_logits, truth = [], None
    rows = []
    for model_dir in args.model_dirs:
        metadata = json.loads((model_dir / 'composition_metadata.json').read_text(encoding='utf-8'))
        model = CompositionCNN(pretrained=False, spatial_pool_size=int(metadata.get('spatial_pool_size', 2))).to(device)
        model.load_state_dict(torch.load(model_dir / 'composition_model_best.pth', map_location=device, weights_only=True))
        logits, truth = logits_for(model, loader, device)
        all_logits.append(logits)
        rows.append({'models': [str(model_dir)], 'validation': score(logits, truth)})
    for count in range(2, len(all_logits) + 1):
        averaged = torch.stack(all_logits[:count]).mean(0)
        rows.append({'models': [str(path) for path in args.model_dirs[:count]],
                     'validation': score(averaged, truth)})
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BACKEND / 'training_data')
    parser.add_argument('--split-manifest', type=Path, default=BACKEND / 'ml_models/trained/composition_data_audit.json')
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('model_dirs', type=Path, nargs='+')
    main(parser.parse_args())
