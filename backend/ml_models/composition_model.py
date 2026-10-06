"""
Deep Learning Model for Composition Detection
Uses CNN to classify composition types from images
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
import numpy as np
from PIL import Image, ImageOps
import os
import json
import io

COMPOSITION_TYPES = (
    'rule_of_thirds', 'centered', 'leading_lines', 'diagonal',
    'symmetrical', 'golden_ratio', 'fill_the_frame', 'frame_within_frame',
)


def composition_preprocess():
    return transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def encode_composition_image(image):
    """Match the full-frame image cache used to train the current checkpoint."""
    image = ImageOps.exif_transpose(image).convert('RGB')
    image.thumbnail((320, 320))
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=92)
    return buffer.getvalue()


class CompositionCNN(nn.Module):
    """
    Convolutional Neural Network for composition type classification.
    Based on ResNet18 with custom classification head.
    """
    
    def __init__(self, num_classes=8, pretrained=True, spatial_pool_size=1):
        super(CompositionCNN, self).__init__()
        
        # Use pretrained ResNet18 as backbone
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet18(weights=weights)
        
        # Replace final fully connected layer
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()  # Remove original FC
        self.backbone.avgpool = nn.AdaptiveAvgPool2d(spatial_pool_size)
        num_features *= spatial_pool_size ** 2
        
        # Custom classification head
        self.classifier = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
        
        # Composition types (must match training order)
        self.composition_types = list(COMPOSITION_TYPES)
        if num_classes != len(self.composition_types):
            raise ValueError('Composition output width must match the eight supported labels')

        # Softmax temperature for confidence calibration. Kept as a plain float
        # attribute (NOT a Parameter/buffer) so it stays out of state_dict and old
        # checkpoints still load under strict load_state_dict. T=1.0 is a no-op;
        # raise toward 1.5-3.0 to soften an over-confident model.
        self.temperature = 1.0
        self.inference_aggregation = 'mean_probabilities'
    
    def forward(self, x):
        features = self.backbone(x)
        output = self.classifier(features)
        return output
    
    def predict_composition(self, image_path, device='cpu'):
        """
        Predict composition type from image.
        Returns: detected type, confidence scores for all types
        """
        self.eval()
        
        # Preprocessing
        transform = composition_preprocess()
        
        if isinstance(image_path, np.ndarray):
            image = Image.fromarray(image_path).convert('RGB')
        elif isinstance(image_path, Image.Image):
            image = ImageOps.exif_transpose(image_path).convert('RGB')
        else:
            with Image.open(image_path) as source:
                image = ImageOps.exif_transpose(source).convert('RGB')
        with Image.open(io.BytesIO(encode_composition_image(image))) as cached:
            image_tensor = transform(cached.convert('RGB')).unsqueeze(0).to(device)

        # Test-time augmentation: average the original with its horizontal mirror.
        # Every composition label is closed under horizontal flip, so this is
        # label-safe and reduces single-crop prediction variance.
        batch = torch.cat([image_tensor, torch.flip(image_tensor, dims=[3])], dim=0)

        with torch.no_grad():
            outputs = self(batch)                                  # (2, num_classes)
            scaled = outputs / float(self.temperature)             # confidence calibration
            # Use the aggregation selected and calibrated during training.
            probabilities = (F.softmax(scaled.mean(dim=0), dim=0)
                             if self.inference_aggregation == 'mean_logits'
                             else F.softmax(scaled, dim=1).mean(dim=0))
            predicted_idx = torch.argmax(probabilities).item()
            confidence = probabilities[predicted_idx].item()
        
        return {
            'detected_type': self.composition_types[predicted_idx],
            'confidence': float(confidence),
            'all_probabilities': {
                comp_type: float(probabilities[i]) 
                for i, comp_type in enumerate(self.composition_types)
            }
        }


class HybridCompositionDetector:
    """
    Hybrid approach: ML model + rule-based fallback
    Uses the learned class decision and reports uncertainty separately.
    """
    
    def __init__(self, model_path=None, confidence_threshold=None):
        self.confidence_threshold = 0.6 if confidence_threshold is None else confidence_threshold
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load trained model
        self.model = CompositionCNN(num_classes=8, pretrained=False)
        
        if model_path and os.path.exists(model_path):
            try:
                metadata_path = os.path.join(os.path.dirname(model_path), 'composition_metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, encoding='utf-8') as handle:
                        metadata = json.load(handle)
                    pool_size = metadata.get('spatial_pool_size', 1)
                    if pool_size not in (1, 2):
                        raise ValueError('Unsupported composition spatial pool size')
                    if pool_size == 2:
                        self.model = CompositionCNN(num_classes=8, pretrained=False, spatial_pool_size=pool_size)
                    if metadata.get('classes') != self.model.composition_types:
                        raise ValueError('Checkpoint label order does not match runtime')
                    temperature = float(metadata.get('temperature', 1.0))
                    if not np.isfinite(temperature) or temperature <= 0:
                        raise ValueError('Invalid confidence calibration temperature')
                    self.model.temperature = temperature
                    self.model.inference_aggregation = metadata.get('inference_aggregation', 'mean_probabilities')
                    if self.model.inference_aggregation not in ('mean_logits', 'mean_probabilities'):
                        raise ValueError('Unsupported composition inference aggregation')
                    if confidence_threshold is None:
                        self.confidence_threshold = float(metadata.get('confidence_threshold', 0.6))
                    if not 0 <= self.confidence_threshold <= 1:
                        raise ValueError('Invalid composition confidence threshold')
                self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
                self.model.eval()
                self.model.to(self.device)
                self.model_loaded = True
                print(f"[OK] Loaded composition model from {model_path}")
            except Exception as e:
                self.model_loaded = False
                print(f"[WARN] Failed to load model: {e}")
        else:
            self.model_loaded = False
            print("[WARN] No trained model found. Using rule-based detection only.")
    
    def detect_composition(self, image_path, rule_based_scores=None):
        """
        Learned detection with a rule-based fallback.

        The geometric scores are useful supporting signals, but they are not a
        competing classifier: on natural photographs they frequently mistake
        texture, edges, and perspective for a composition pattern. A trained
        checkpoint therefore remains the primary source of the class decision.
        
        Args:
            image_path: Path to image
            rule_based_scores: Dict of rule-based scores (from existing code)
        
        Returns:
            Detected composition with confidence
        """
        # The learned model is the primary classifier whenever it is available.
        # Keep the confidence/reliable flag for callers that want to communicate
        # uncertainty, but do not replace a low-confidence learned prediction
        # with a substantially weaker hand-written geometry guess.
        if self.model_loaded:
            try:
                ml_result = self.model.predict_composition(image_path, self.device)
                return {
                    'method': 'ml',
                    'detected_type': ml_result['detected_type'],
                    'confidence': ml_result['confidence'],
                    'all_scores': ml_result['all_probabilities'],
                    'reliable': ml_result['confidence'] >= self.confidence_threshold,
                }
            except Exception as e:
                print(f"[WARN] ML prediction failed: {e}")
        
        # Fallback to rule-based
        if rule_based_scores:
            best_type = max(rule_based_scores, key=rule_based_scores.get)
            return {
                'method': 'rules',
                'detected_type': best_type,
                'confidence': rule_based_scores[best_type] / 10.0,  # Normalize to 0-1
                'all_scores': {k: v/10.0 for k, v in rule_based_scores.items()},
                'reliable': rule_based_scores[best_type] >= 7.0
            }
        
        return {
            'method': 'fallback',
            'detected_type': 'rule_of_thirds',  # Default
            'confidence': 0.5,
            'all_scores': {},
            'reliable': False
        }
    
