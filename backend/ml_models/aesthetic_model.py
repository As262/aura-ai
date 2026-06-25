"""
Image Aesthetic Assessment Model
================================

A dedicated aesthetic-quality model, separate from the composition CNN.

Two modes:
  * LEARNED   — a NIMA-style network (MobileNetV2 backbone + 10-bin score
                distribution head). Used automatically when trained weights
                exist at ml_models/trained/aesthetic_nima.pth.
  * PERCEPTUAL — when no trained weights are present, the same MobileNetV2
                backbone (ImageNet-pretrained) is used as a deep feature
                extractor and fused with established aesthetic correlates
                (colorfulness, multi-scale sharpness, depth-of-field
                separation, exposure & contrast balance). Produces a
                genuinely image-dependent, calibrated 1-10 score.

Both modes run on CPU in well under a second per image.

Train a fully-learned model with backend/training/train_aesthetic_model.py
(on the AVA dataset) to drop a weights file in and switch to LEARNED mode.
"""

import os
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms


class NIMA(nn.Module):
    """Neural IMage Assessment — MobileNetV2 backbone + 10-bin score head."""

    def __init__(self, pretrained_backbone=True):
        super().__init__()
        try:
            weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained_backbone else None
            backbone = models.mobilenet_v2(weights=weights)
        except Exception:
            backbone = models.mobilenet_v2(pretrained=pretrained_backbone)

        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(
            nn.Dropout(0.25),
            nn.Linear(1280, 10),
        )

    def forward(self, x):
        f = self.features(x)
        f = self.pool(f).flatten(1)
        logits = self.head(f)
        return F.softmax(logits, dim=1)

    def features_only(self, x):
        f = self.features(x)
        return self.pool(f).flatten(1)


class AestheticAssessor:
    """High-level aesthetic scorer used by the analysis pipeline."""

    SCORE_BINS = torch.arange(1, 11, dtype=torch.float32)

    def __init__(self, weights_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = NIMA(pretrained_backbone=True).to(self.device).eval()

        self.learned = False
        if weights_path and os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location=self.device)
                self.model.load_state_dict(state)
                self.learned = True
                print(f"[OK] Loaded learned aesthetic model from {weights_path}")
            except Exception as e:
                print(f"[WARN] Could not load aesthetic weights ({e}); using perceptual mode.")

        self.preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224), antialias=True),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                  std=[0.229, 0.224, 0.225]),
        ])

    # ---------------------------------------------------------------- public

    @torch.no_grad()
    def assess(self, image_rgb: np.ndarray) -> dict:
        """
        Assess an RGB (H, W, 3) uint8 image.
        Returns score (1-10), distribution, confidence, factors, mode.
        """
        tensor = self.preprocess(image_rgb).unsqueeze(0).to(self.device)

        # Deep feature signal (learned representation richness) — used in both modes
        feats = self.model.features_only(tensor)[0].cpu().numpy()
        feat_richness = self._feature_richness(feats)

        # Perceptual correlates (computed directly on the image)
        perceptual = self._perceptual_factors(image_rgb)

        if self.learned:
            dist = self.model(tensor)[0].cpu()
            mean = float((dist * self.SCORE_BINS).sum())
            std = float(((self.SCORE_BINS - mean) ** 2 * dist).sum().sqrt())
            confidence = round(max(0.0, 1.0 - std / 3.5) * 100, 1)
            factors = perceptual['factors']
            factors['deep_quality'] = round(feat_richness, 1)
            return {
                'score': round(mean, 1),
                'distribution': [round(float(p), 4) for p in dist.tolist()],
                'confidence': confidence,
                'factors': factors,
                'mode': 'learned-nima',
                'interpretation': self._interpret(mean, perceptual),
            }

        # ---- Perceptual-calibrated fusion ----
        factors = perceptual['factors']
        factors['deep_quality'] = round(feat_richness, 1)

        score = (
            factors['colorfulness']  * 0.18 +
            factors['sharpness']     * 0.20 +
            factors['depth_of_field'] * 0.14 +
            factors['exposure']      * 0.18 +
            factors['contrast']      * 0.12 +
            factors['deep_quality']  * 0.18
        )
        score = float(min(max(score, 1.0), 10.0))

        # Pseudo-distribution peaked at the score (for UI parity with NIMA)
        dist = self._score_to_distribution(score)
        confidence = round(perceptual['stability'] * 100, 1)

        return {
            'score': round(score, 1),
            'distribution': [round(p, 4) for p in dist],
            'confidence': confidence,
            'factors': factors,
            'mode': 'deep-perceptual',
            'interpretation': self._interpret(score, perceptual),
        }

    # -------------------------------------------------------------- internals

    def _feature_richness(self, feats: np.ndarray) -> float:
        """
        Richness/structure of the MobileNetV2 deep features. Well-composed,
        content-rich images activate a broader, more confident set of
        channels; flat/empty frames activate fewer. Mapped to 0-10.
        """
        f = np.maximum(feats, 0.0)
        if f.max() <= 0:
            return 5.0
        p = f / (f.sum() + 1e-8)
        entropy = -np.sum(p * np.log(p + 1e-12))
        max_entropy = np.log(len(p))
        spread = entropy / max_entropy                  # 0..1 channel diversity
        energy = float(np.tanh(np.mean(f) * 2.0))       # 0..1 activation strength
        richness = (spread * 0.6 + energy * 0.4) * 10.0
        return float(min(max(richness, 1.0), 10.0))

    def _perceptual_factors(self, image_rgb: np.ndarray) -> dict:
        img = image_rgb.astype(np.float32)
        r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # 1) Colorfulness — Hasler & Süsstrunk (2003)
        rg = r - g
        yb = 0.5 * (r + g) - b
        colorfulness = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + \
            0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
        color_score = self._calib(colorfulness, 0, 110, soft=True)

        # 2) Sharpness — variance of Laplacian
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharp_score = self._calib(np.log1p(lap_var), 3.0, 8.5)

        # 3) Depth-of-field separation — centre sharpness vs REAL peripheral
        #    sharpness, measured on the four border strips. (Zeroing the centre
        #    of a copy injects two huge artificial step edges along the block
        #    boundary, which made this factor swing to 1.0 / 10.0 on artifacts.)
        cy0, cy1 = int(h * 0.30), int(h * 0.70)
        cx0, cx1 = int(w * 0.30), int(w * 0.70)
        center = gray[cy0:cy1, cx0:cx1]
        if center.size == 0:
            dof_score = 5.5
        else:
            center_sharp = cv2.Laplacian(center, cv2.CV_64F).var()
            strips = [gray[:cy0, :], gray[cy1:, :],
                      gray[cy0:cy1, :cx0], gray[cy0:cy1, cx1:]]
            edge_vars = [cv2.Laplacian(s, cv2.CV_64F).var() for s in strips if s.size]
            edge_sharp = float(np.mean(edge_vars)) if edge_vars else center_sharp
            if center_sharp < 1.0 and edge_sharp < 1.0:
                dof_score = 5.5            # near-flat frame: no DoF signal -> neutral
            else:
                dof_ratio = min(center_sharp / (edge_sharp + 1e-6), 50.0)
                dof_score = self._calib(np.log1p(dof_ratio), 0.0, 3.0)

        # 4) Exposure — flat well-exposed band [90,150], gentle falloff, and a
        #    MULTIPLICATIVE clipping penalty (the old additive subtraction double-
        #    counted darkness and pinned dark frames at the 1.0 floor).
        mean_l = gray.mean()
        if 90.0 <= mean_l <= 150.0:
            exposure_center = 1.0
        else:
            dist = (90.0 - mean_l) if mean_l < 90.0 else (mean_l - 150.0)
            exposure_center = max(0.0, 1.0 - dist / 90.0)
        clip_low = float((gray < 8).mean())
        clip_high = float((gray > 247).mean())
        clip_pen = min(0.7, 1.5 * (clip_low + clip_high))
        exposure = exposure_center * (1.0 - clip_pen)
        exposure_score = float(min(max(exposure * 10.0, 1.0), 10.0))

        # 5) Contrast — luminance spread (penalise flat & blown)
        contrast = gray.std()
        contrast_score = self._calib(contrast, 18, 75, soft=True)

        stability = float(min(max((sharp_score / 10 * 0.5 + exposure_score / 10 * 0.5), 0.3), 0.97))

        return {
            'factors': {
                'colorfulness': round(color_score, 1),
                'sharpness': round(sharp_score, 1),
                'depth_of_field': round(dof_score, 1),
                'exposure': round(exposure_score, 1),
                'contrast': round(contrast_score, 1),
            },
            'stability': stability,
            'mean_luminance': float(mean_l),
        }

    @staticmethod
    def _calib(value, lo, hi, soft=False):
        """Map a raw metric to a 1-10 score between lo..hi."""
        t = (value - lo) / (hi - lo + 1e-8)
        t = max(0.0, min(1.0, t))
        if soft:  # rise to a full-score plateau, shave only extreme over-saturation
            # (The old triangle peaked at t=0.8 and DROPPED to 7.75 at the max,
            #  so the most colourful/contrasty images scored below moderate ones.)
            base = min(t / 0.8, 1.0)                    # monotonic, plateaus at 1.0
            penalty = max(0.0, t - 0.95) / 0.05 * 0.10  # <=0.10, only past t>0.95
            t = max(0.0, min(1.0, base - penalty))
        return float(1.0 + t * 9.0)

    @staticmethod
    def _score_to_distribution(score):
        bins = np.arange(1, 11, dtype=np.float32)
        d = np.exp(-((bins - score) ** 2) / 2.0)
        d = d / d.sum()
        return d.tolist()

    @staticmethod
    def _interpret(score, perceptual):
        f = perceptual['factors']
        weakest = min(f, key=f.get).replace('_', ' ')
        if score >= 8.5:
            return "Exceptional aesthetic quality — strong on every visual dimension."
        if score >= 7.0:
            return f"Strong aesthetic. Biggest opportunity: {weakest}."
        if score >= 5.5:
            return f"Solid image with room to grow. Focus on {weakest}."
        return f"Aesthetic needs work — {weakest} is holding it back the most."


# Singleton accessor so the heavy backbone loads once per process
_ASSESSOR = None


def get_assessor():
    global _ASSESSOR
    if _ASSESSOR is None:
        weights = os.path.join(os.path.dirname(__file__), 'trained', 'aesthetic_nima.pth')
        _ASSESSOR = AestheticAssessor(weights if os.path.exists(weights) else None)
    return _ASSESSOR
