"""
Deep Learning Model for Composition Detection
Uses CNN to classify composition types from images
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
import numpy as np
from PIL import Image
import os


class CompositionCNN(nn.Module):
    """
    Convolutional Neural Network for composition type classification.
    Based on ResNet18 with custom classification head.
    """
    
    def __init__(self, num_classes=8, pretrained=True):
        super(CompositionCNN, self).__init__()
        
        # Use pretrained ResNet18 as backbone
        self.backbone = models.resnet18(pretrained=pretrained)
        
        # Replace final fully connected layer
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()  # Remove original FC
        
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
        self.composition_types = [
            'rule_of_thirds',
            'centered',
            'leading_lines',
            'diagonal',
            'symmetrical',
            'golden_ratio',
            'fill_the_frame',
            'frame_within_frame'
        ]
    
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
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        image = Image.open(image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = self(image_tensor)
            probabilities = F.softmax(outputs, dim=1)[0]
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
    Uses ML model as primary, falls back to rules if confidence is low
    """
    
    def __init__(self, model_path=None, confidence_threshold=0.6):
        self.confidence_threshold = confidence_threshold
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load trained model
        self.model = CompositionCNN(num_classes=8, pretrained=False)
        
        if model_path and os.path.exists(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
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
        Hybrid detection: Try ML model first, fallback to rules
        
        Args:
            image_path: Path to image
            rule_based_scores: Dict of rule-based scores (from existing code)
        
        Returns:
            Detected composition with confidence
        """
        # Try ML model first
        if self.model_loaded:
            try:
                ml_result = self.model.predict_composition(image_path, self.device)
                
                # If confidence is high, use ML prediction
                if ml_result['confidence'] >= self.confidence_threshold:
                    return {
                        'method': 'ml',
                        'detected_type': ml_result['detected_type'],
                        'confidence': ml_result['confidence'],
                        'all_scores': ml_result['all_probabilities'],
                        'reliable': True
                    }
                
                # Medium confidence: combine ML + rules
                elif ml_result['confidence'] >= 0.4 and rule_based_scores:
                    combined_scores = self._combine_ml_and_rules(
                        ml_result['all_probabilities'],
                        rule_based_scores
                    )
                    best_type = max(combined_scores, key=combined_scores.get)
                    
                    return {
                        'method': 'hybrid',
                        'detected_type': best_type,
                        'confidence': combined_scores[best_type],
                        'all_scores': combined_scores,
                        'reliable': True,
                        'ml_contribution': ml_result['confidence'],
                        'rule_contribution': 1 - ml_result['confidence']
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
    
    def _combine_ml_and_rules(self, ml_probs, rule_scores):
        """
        Combine ML probabilities and rule-based scores
        ML weight: 70%, Rules weight: 30%
        """
        combined = {}
        
        for comp_type in ml_probs.keys():
            ml_score = ml_probs.get(comp_type, 0)
            rule_score = rule_scores.get(comp_type, 0) / 10.0  # Normalize to 0-1
            
            # Weighted combination
            combined[comp_type] = (ml_score * 0.7) + (rule_score * 0.3)
        
        return combined
