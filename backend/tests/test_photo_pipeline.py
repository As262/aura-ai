"""Regression tests for photo train/serve parity, scoring, and uncertainty.

Run: .venv-training/Scripts/python.exe -m pytest tests/test_photo_pipeline.py -q
"""
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
import torch
from PIL import Image, ImageOps
from torch.utils.data import DataLoader

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from api.ai_services_optimized import OptimizedImageAnalysisService
from ml_models.aesthetic_model import aesthetic_preprocess
from ml_models.composition_model import COMPOSITION_TYPES, CompositionCNN, HybridCompositionDetector, encode_composition_image
from training.train_aesthetic_model import AVADataset
from training.train_model import CompositionDataset, audit_and_split, evaluate


def image_pixels():
    rng = np.random.default_rng(21)
    return rng.integers(0, 256, (83, 137, 3), dtype=np.uint8)


def service_without_models():
    # Exercise the real scoring/decision functions without downloading models
    # or starting pose detection for a unit test.
    service = OptimizedImageAnalysisService.__new__(OptimizedImageAnalysisService)
    service.hybrid_detector = None
    return service


def diagnostics():
    return {
        'technical_quality': {'overall_score': 10, 'sharpness': {'score': 10},
                              'noise': {'score': 10}},
        'lighting_analysis': {'overall_score': 10},
        'color_analysis': {'overall_score': 10},
        'pose_analysis': {'detected': False},
        'composition_analysis': {'type_key': 'leading_lines', 'detected_type': 'Leading Lines',
                                 'method': 'ml', 'score': 10, 'ml_confidence': 99,
                                 'ml_reliable': True, 'all_scores': {}},
    }


def test_aesthetic_runtime_preprocessing_matches_training(tmp_path):
    pixels = image_pixels()
    path = tmp_path / 'photo.png'
    Image.fromarray(pixels).save(path)
    dataset = AVADataset(tmp_path, [{'image': path.name, 'rating_counts': [1] * 10}])
    training_tensor, _ = dataset[0]
    serving_tensor = aesthetic_preprocess()(Image.fromarray(pixels))
    assert torch.equal(training_tensor, serving_tensor)


def test_composition_evaluation_matches_serving_flip_aggregation():
    model = CompositionCNN(pretrained=False, spatial_pool_size=2)
    model.inference_aggregation = 'mean_logits'
    model.temperature = 1.15
    model.eval()
    pixels = image_pixels()
    encoded = encode_composition_image(Image.fromarray(pixels))
    loader = DataLoader(CompositionDataset([{'image': encoded, 'label': 0}]))
    _, logits, _ = evaluate(model, loader, 'cpu', model.temperature, horizontal_flip=True)
    expected = (logits[0] / model.temperature).softmax(0)
    prediction = model.predict_composition(pixels)
    actual = torch.tensor([prediction['all_probabilities'][key] for key in COMPOSITION_TYPES])
    torch.testing.assert_close(actual, expected)


def test_frozen_split_does_not_move_or_relabel_held_out_images(tmp_path):
    # A correction is allowed only for training. The deliberately wrong folder
    # labels in validation/test remain fixed for honest historical comparison.
    folder = tmp_path / 'rule_of_thirds'
    folder.mkdir()
    rows = []
    for index, name in enumerate(('Framing.jpg', 'Leading lines.jpg')):
        pixels = np.random.default_rng(index).integers(0, 256, (48, 64, 3), dtype=np.uint8)
        Image.fromarray(pixels).save(folder / name, format='PNG')
        rows.append({'path': f'rule_of_thirds/{name}', 'label': 'rule_of_thirds',
                     'sha256': hashlib.sha256(pixels.tobytes()).hexdigest()})
    manifest = tmp_path / 'split.json'
    manifest.write_text(json.dumps({'splits': {'train': [rows[0]], 'validation': [rows[1]], 'test': []}}))
    splits, report = audit_and_split(tmp_path, split_manifest=manifest)
    assert splits['train'][0]['label'] == COMPOSITION_TYPES.index('frame_within_frame')
    assert splits['validation'][0]['label'] == COMPOSITION_TYPES.index('rule_of_thirds')
    assert report['held_out_labels_changed'] is False
    assert splits['validation'][0]['sha256'] == rows[1]['sha256']


def test_low_confidence_style_is_not_replaced_by_geometry():
    detector = HybridCompositionDetector.__new__(HybridCompositionDetector)
    detector.model_loaded = True
    detector.device = 'cpu'
    detector.confidence_threshold = 0.73
    detector.model = SimpleNamespace(predict_composition=Mock(return_value={
        'detected_type': 'frame_within_frame', 'confidence': 0.42,
        'all_probabilities': {'frame_within_frame': 0.42, 'leading_lines': 0.39},
    }))
    result = detector.detect_composition(image_pixels(), {'leading_lines': 10, 'frame_within_frame': 0})
    assert result['detected_type'] == 'frame_within_frame'
    assert result['method'] == 'ml'
    assert result['reliable'] is False


def test_rotated_jpeg_and_oriented_pixels_have_identical_predictions(tmp_path):
    path = tmp_path / 'portrait.jpg'
    image = Image.fromarray(image_pixels())
    exif = image.getexif()
    exif[274] = 6
    image.save(path, exif=exif)
    with Image.open(path) as source:
        pixels = np.asarray(ImageOps.exif_transpose(source).convert('RGB'))
    model = CompositionCNN(pretrained=False)
    assert model.predict_composition(path) == model.predict_composition(pixels)


def test_constant_image_has_no_spurious_perfect_composition():
    result = service_without_models()._detect_composition_type(np.full((100, 100, 3), [255, 0, 0], dtype=np.uint8))
    assert result['method'] == 'insufficient-evidence'
    assert result['type_key'] is None
    assert result['score'] == 0
    assert max(result['all_scores'].values()) == 0


def test_empty_edge_map_is_not_perfect_symmetry():
    assert service_without_models()._check_symmetry(np.zeros((100, 100), dtype=np.uint8)) == 0


def test_confident_style_does_not_modify_learned_aesthetic_score(monkeypatch):
    import ml_models.aesthetic_model as module
    assessment = {'score': 3.8, 'mode': 'learned-nima', 'factors': {}}
    monkeypatch.setattr(module, 'get_assessor', lambda: SimpleNamespace(assess=lambda image: dict(assessment, factors={})))
    result = service_without_models()._assess_aesthetic(image_pixels(), diagnostics())
    assert result['score'] == 3.8


def test_overall_rating_uses_learned_quality_despite_perfect_heuristics():
    results = diagnostics()
    results['aesthetic_score'] = {'score': 3.8, 'mode': 'learned-nima'}
    result = service_without_models()._calculate_overall_rating(results)
    assert result['score'] == 3.8
    assert result['scoring_method'] == 'learned-nima'


def test_uncertain_style_does_not_generate_confident_composition_advice():
    results = diagnostics()
    composition = results['composition_analysis']
    composition.update(ml_reliable=False, score=1)
    assert service_without_models()._generate_dynamic_tips(results, composition) == []


def test_parallel_classification_keeps_each_uploads_pixels():
    service = service_without_models()
    received = []
    def detect(pixels, scores):
        received.append(int(pixels[0, 0, 0]))
        return {'method': 'ml', 'detected_type': 'centered', 'confidence': 0.4,
                'reliable': False, 'all_scores': {'centered': 0.4}}
    service.hybrid_detector = SimpleNamespace(model_loaded=True, detect_composition=detect)
    first, second = image_pixels(), image_pixels()
    first[0, 0, 0], second[0, 0, 0] = 12, 233
    with ThreadPoolExecutor(max_workers=2) as executor:
        outputs = list(executor.map(service._detect_composition_type, (first, second)))
    assert sorted(received) == [12, 233]
    assert all(output['method'] == 'ml' for output in outputs)
    assert not hasattr(service, 'current_image_path')


def test_active_spatial_checkpoint_and_metadata_are_compatible():
    detector = HybridCompositionDetector(str(BACKEND / 'ml_models/trained/composition_model_best.pth'))
    metadata = json.loads((BACKEND / 'ml_models/trained/composition_metadata.json').read_text())
    assert detector.model_loaded
    assert detector.model.backbone.avgpool.output_size == 2
    assert detector.model.inference_aggregation == 'mean_logits'
    assert detector.confidence_threshold == pytest.approx(metadata['confidence_threshold'])
