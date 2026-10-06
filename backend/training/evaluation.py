"""Shared, reproducible evaluation helpers; never select checkpoints on test data."""
import json
import random
from pathlib import Path

import numpy as np
import torch


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(4)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def classification_metrics(truth, predictions, classes):
    truth, predictions = np.asarray(truth), np.asarray(predictions)
    matrix = np.zeros((len(classes), len(classes)), dtype=int)
    np.add.at(matrix, (truth, predictions), 1)
    rows = []
    for index, name in enumerate(classes):
        tp = int(matrix[index, index])
        support = int(matrix[index].sum())
        precision = tp / max(int(matrix[:, index].sum()), 1)
        recall = tp / max(support, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-12)
        rows.append(dict(label=name, support=support, precision=precision, recall=recall, f1=f1))
    return {
        'samples': len(truth), 'accuracy': float(np.mean(truth == predictions)),
        'macro_f1': float(np.mean([row['f1'] for row in rows])),
        'confusion_matrix': matrix.tolist(), 'per_class': rows,
    }
