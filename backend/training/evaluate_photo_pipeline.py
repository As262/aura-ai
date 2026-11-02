"""Evaluate fixed held-out photo files through the actual serving decision path.

python training/evaluate_photo_pipeline.py --data-dir training_data
Uses original full-resolution files rather than the training JPEG cache.
"""
import argparse
from collections import Counter
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from api.ai_services_optimized import OptimizedImageAnalysisService
from ml_models.composition_model import COMPOSITION_TYPES
from training.evaluation import classification_metrics, seed_everything, write_json
from training.train_model import audit_and_split


def main(args):
    seed_everything(42)
    model_dir = args.model_dir
    splits, _ = audit_and_split(args.data_dir, split_manifest=model_dir / 'composition_data_audit.json')
    service = OptimizedImageAnalysisService(composition_model_path=model_dir / 'composition_model_best.pth')
    if not service.hybrid_detector or not service.hybrid_detector.model_loaded:
        raise RuntimeError('Serving composition checkpoint did not load')
    truth, predicted, rows = [], [], []
    for row in splits['test']:
        with Image.open(row['path']) as source:
            pixels = np.asarray(ImageOps.exif_transpose(source).convert('RGB'))
        original_pixels = pixels
        # Match the request's smart resize before composition inference.
        bgr = service._smart_resize(cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR))
        pixels = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        with contextlib.redirect_stdout(io.StringIO()):
            result = service._detect_composition_type(pixels, model_image_rgb=original_pixels)
        label = result.get('type_key')
        index = COMPOSITION_TYPES.index(label) if label in COMPOSITION_TYPES else len(COMPOSITION_TYPES)
        truth.append(row['label'])
        predicted.append(index)
        rows.append(dict(path=row['path'], truth=COMPOSITION_TYPES[row['label']],
                         predicted=label, method=result.get('method'),
                         confidence=result.get('ml_confidence'), reliable=result.get('ml_reliable')))

    classes = list(COMPOSITION_TYPES) + ['unclear']
    metrics = classification_metrics(truth, predicted, classes)
    metrics['macro_f1'] = float(np.mean([row['f1'] for row in metrics['per_class'][:len(COMPOSITION_TYPES)]]))
    metadata = json.loads((model_dir / 'composition_metadata.json').read_text(encoding='utf-8'))
    report = dict(
        evaluation='fixed held-out original files through serving preprocessing and classifier',
        samples=len(rows), split_membership_changed=False, held_out_labels_changed=False,
        checkpoint_sha256=hashlib.sha256((model_dir / 'composition_model_best.pth').read_bytes()).hexdigest(),
        spatial_pool_size=metadata['spatial_pool_size'], temperature=metadata['temperature'],
        confidence_threshold=service.hybrid_detector.confidence_threshold,
        serving_metrics=metrics, methods=dict(Counter(row['method'] for row in rows)),
        predictions=rows,
    )
    # Exercise complete image scoring on a real held-out photograph and a flat
    # input. The distribution's expected value must remain the reported score.
    smoke_rows = []
    smoke_paths = [Path(splits['test'][0]['path']), BACKEND / 'test_image.jpg']
    for path in smoke_paths:
        if not path.exists():
            continue
        with contextlib.redirect_stdout(io.StringIO()):
            result = service.analyze_image_comprehensive(path)
        aesthetic = result['aesthetic_score']
        expected = sum((index + 1) * probability for index, probability in enumerate(aesthetic['distribution']))
        assert abs(aesthetic['score'] - expected) <= 0.06, 'Serving altered the learned aesthetic score'
        assert result['overall_rating']['score'] == aesthetic['score'], 'Overall rating ignored learned appeal'
        smoke_rows.append(dict(path=str(path), overall_score=result['overall_rating']['score'],
                               aesthetic_score=aesthetic['score'], distribution_mean=round(expected, 4),
                               composition=result['composition_analysis']['detected_type'],
                               method=result['composition_analysis']['method'],
                               aesthetic_mode=aesthetic['mode'], pose_available=result['pose_analysis'].get('available')))
    report['integration_smoke'] = smoke_rows
    write_json(args.report, report)
    print(json.dumps(dict(serving_accuracy=metrics['accuracy'], macro_f1=metrics['macro_f1'],
                          methods=report['methods'], integration_smoke=smoke_rows,
                          report=str(args.report)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BACKEND / 'training_data')
    parser.add_argument('--model-dir', type=Path, default=BACKEND / 'ml_models/trained')
    parser.add_argument('--report', type=Path, default=BACKEND / 'ml_models/trained/photo_pipeline_evaluation.json')
    main(parser.parse_args())
