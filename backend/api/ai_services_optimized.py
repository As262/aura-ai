"""
Optimized AI Image Analysis Service
- Fast & Accurate Analysis
- Composition Type Detection
- Dynamic Tips Based on Analysis
- GPU Accelerated
"""

import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = hasattr(mp, 'solutions')
except ImportError:
    mp = None
    MEDIAPIPE_AVAILABLE = False

from PIL import Image, ImageEnhance, ImageStat
import torch
from skimage import measure, filters
import os
import sys
from pathlib import Path

# Import hybrid composition detector
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from ml_models.composition_model import HybridCompositionDetector
    HYBRID_MODEL_AVAILABLE = True
except ImportError:
    HYBRID_MODEL_AVAILABLE = False
    print("[WARN] Hybrid ML model not available. Using rule-based detection only.")


class OptimizedImageAnalysisService:
    """
    Ultra-fast, highly accurate image analysis with composition detection.
    Detects actual composition type and provides dynamic tips.
    """
    
    # Composition types with their characteristics
    COMPOSITION_TYPES = {
        'rule_of_thirds': {
            'name': 'Rule of Thirds',
            'description': 'Subject positioned at intersection points of thirds grid',
            'ideal_for': 'Landscapes, portraits, general photography'
        },
        'centered': {
            'name': 'Centered Composition',
            'description': 'Subject centered in the frame for symmetry and balance',
            'ideal_for': 'Symmetrical subjects, architecture, portraits'
        },
        'leading_lines': {
            'name': 'Leading Lines',
            'description': 'Lines guide the viewer\'s eye through the image',
            'ideal_for': 'Roads, rivers, architecture, depth creation'
        },
        'frame_within_frame': {
            'name': 'Frame within Frame',
            'description': 'Natural frames created by elements in the scene',
            'ideal_for': 'Windows, archways, adding depth and context'
        },
        'diagonal': {
            'name': 'Diagonal Composition',
            'description': 'Strong diagonal elements create dynamic energy',
            'ideal_for': 'Action shots, creating movement and energy'
        },
        'symmetrical': {
            'name': 'Symmetrical',
            'description': 'Perfect balance through mirroring or symmetry',
            'ideal_for': 'Architecture, reflections, formal compositions'
        },
        'golden_ratio': {
            'name': 'Golden Ratio',
            'description': 'Based on the Fibonacci sequence (1.618:1 ratio)',
            'ideal_for': 'Natural subjects, creating harmonious compositions'
        },
        'fill_the_frame': {
            'name': 'Fill the Frame',
            'description': 'Subject occupies most of the frame, minimal background',
            'ideal_for': 'Details, textures, macro photography'
        }
    }
    
    def __init__(self):
        # GPU detection
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.use_gpu = torch.cuda.is_available()
        
        # Initialize Hybrid ML Composition Detector
        if HYBRID_MODEL_AVAILABLE:
            model_path = Path(__file__).parent.parent / 'ml_models' / 'trained' / 'composition_model_best.pth'
            self.hybrid_detector = HybridCompositionDetector(
                model_path=str(model_path) if model_path.exists() else None,
                confidence_threshold=0.6
            )
        else:
            self.hybrid_detector = None
        
        # Initialize MediaPipe
        if MEDIAPIPE_AVAILABLE:
            self.pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.6
            )
            self.face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.6
            )
        else:
            self.pose = None
            self.face_detection = None
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Store current image path for hybrid detection
        self.current_image_path = None
    
    def analyze_image(self, image_path):
        """
        Main analysis function - Fast & Accurate
        Returns comprehensive analysis with composition type and dynamic tips
        """
        return self.analyze_image_comprehensive(image_path)
    
    def analyze_image_comprehensive(self, image_path):
        """
        Comprehensive analysis function (main entry point)
        Returns comprehensive analysis with composition type and dynamic tips
        """
        start_time = time.time()
        
        # Store image path for hybrid detection
        self.current_image_path = image_path
        
        # Load and optimize image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Failed to load image")
        
        # Smart resize for optimal speed/quality
        image = self._smart_resize(image, max_dimension=1920)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # Parallel analysis for speed
        futures = {
            'technical': self.executor.submit(self._analyze_technical, image, pil_image),
            'lighting': self.executor.submit(self._analyze_lighting, image),
            'colors': self.executor.submit(self._analyze_colors, pil_image, image_rgb),
        }
        
        # Composition detection (sequential for accuracy)
        composition_analysis = self._detect_composition_type(image_rgb)
        
        # Pose detection if available
        pose_result = self._analyze_pose(image_rgb) if MEDIAPIPE_AVAILABLE else {'detected': False}
        
        # Gather parallel results
        results = {
            'technical_quality': futures['technical'].result(),
            'lighting_analysis': futures['lighting'].result(),
            'color_analysis': futures['colors'].result(),
            'composition_analysis': composition_analysis,
            'pose_analysis': pose_result,
        }
        
        # Dedicated aesthetic score — new NIMA-style deep aesthetic model
        results['aesthetic_score'] = self._assess_aesthetic(image_rgb, results)

        # Calculate overall rating (uses aesthetic_score)
        results['overall_rating'] = self._calculate_overall_rating(results)

        # Generate dynamic tips based on actual analysis
        results['tips'] = self._generate_dynamic_tips(results, composition_analysis)
        
        # Processing time
        results['processing_time'] = round(time.time() - start_time, 2)
        
        return results
    
    def _smart_resize(self, image, max_dimension=1920):
        """Intelligently resize for optimal processing"""
        height, width = image.shape[:2]
        if max(height, width) <= max_dimension:
            return image
        
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    def _detect_composition_type(self, image_rgb):
        """
        Accurately detect the actual composition type being used.
        Returns detected type and improvement suggestions.
        """
        height, width = image_rgb.shape[:2]
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        
        # Calculate scores for each composition type
        composition_scores = {}
        
        # 1. Rule of Thirds Detection
        thirds_score = self._check_rule_of_thirds(gray)
        composition_scores['rule_of_thirds'] = thirds_score
        
        # 2. Centered Composition Detection
        centered_score = self._check_centered(gray)
        composition_scores['centered'] = centered_score
        
        # 3. Leading Lines Detection
        leading_lines_score = self._check_leading_lines(gray)
        composition_scores['leading_lines'] = leading_lines_score
        
        # 4. Diagonal Composition Detection
        diagonal_score = self._check_diagonal(gray)
        composition_scores['diagonal'] = diagonal_score
        
        # 5. Symmetry Detection
        symmetry_score = self._check_symmetry(gray)
        composition_scores['symmetrical'] = symmetry_score
        
        # 6. Golden Ratio Detection
        golden_ratio_score = self._check_golden_ratio(gray)
        composition_scores['golden_ratio'] = golden_ratio_score
        
        # 7. Fill the Frame Detection
        fill_frame_score = self._check_fill_frame(gray)
        composition_scores['fill_the_frame'] = fill_frame_score
        
        # 8. Frame within Frame Detection
        frame_in_frame_score = self._check_frame_in_frame(gray)
        composition_scores['frame_within_frame'] = frame_in_frame_score
        
        # ==== HYBRID ML + RULE-BASED DETECTION ====
        # Try ML model first if available
        if self.hybrid_detector and self.hybrid_detector.model_loaded and self.current_image_path:
            try:
                hybrid_result = self.hybrid_detector.detect_composition(
                    self.current_image_path,
                    composition_scores
                )
                
                # Use ML result if reliable AND corroborated by geometry
                if hybrid_result['reliable'] and hybrid_result['method'] in ['ml', 'hybrid']:
                    primary_type = hybrid_result['detected_type']
                    ml_conf = hybrid_result['confidence']

                    # Real rule-based geometric strengths (0-10). These stay intact
                    # and are what we display — NEVER the softmax class probabilities,
                    # which collapse every non-winning class to ~0 and made the UI
                    # show 0/10 across the board.
                    geom_scores = dict(composition_scores)
                    geom_for_type = geom_scores.get(primary_type, 0.0)
                    geom_winner = max(geom_scores, key=geom_scores.get)
                    geom_max = geom_scores[geom_winner]

                    # Corroboration guard: trust the CNN only if the geometry doesn't
                    # strongly contradict it. A confident-but-wrong CNN that asserts a
                    # type the geometry has no evidence for is overruled and we fall
                    # through to the rule-based winner instead.
                    accept_ml = (geom_for_type >= 4.0) or (ml_conf >= 0.85)
                    strong_disagreement = (geom_for_type < 3.0 and geom_max > 7.0)

                    if accept_ml and not strong_disagreement:
                        # Blend the headline score: mostly CNN confidence, partly the
                        # measured geometric strength of the detected type.
                        fused = (ml_conf * 10.0 * 0.6) + (geom_for_type * 0.4)
                        primary_score = min(fused, 10.0)

                        # Keep the softmax distribution separately (for % display only).
                        ml_probabilities = {k: round(v, 4)
                                            for k, v in hybrid_result.get('all_scores', {}).items()}

                        print(f"[AI] {hybrid_result['method'].upper()} Detection: {primary_type} "
                              f"(ml {ml_conf:.0%}, geom {geom_for_type:.1f}/10 -> {primary_score:.1f})")

                        return {
                            'detected_type': self.COMPOSITION_TYPES[primary_type]['name'],
                            'type_key': primary_type,
                            'description': self.COMPOSITION_TYPES[primary_type]['description'],
                            'ideal_for': self.COMPOSITION_TYPES[primary_type]['ideal_for'],
                            'score': round(primary_score, 1),
                            'quality': self._get_quality_rating(primary_score),
                            'secondary_type': None,
                            # Genuine geometric 0-10 strengths for every style
                            'all_scores': {k: round(min(v, 10.0), 1) for k, v in geom_scores.items()},
                            'analysis_details': {
                                'rule_of_thirds': round(geom_scores.get('rule_of_thirds', 0), 1),
                                'centered': round(geom_scores.get('centered', 0), 1),
                                'leading_lines': round(geom_scores.get('leading_lines', 0), 1),
                                'diagonal': round(geom_scores.get('diagonal', 0), 1),
                                'symmetry': round(geom_scores.get('symmetrical', 0), 1),
                                'golden_ratio': round(geom_scores.get('golden_ratio', 0), 1)
                            },
                            'ml_probabilities': ml_probabilities,
                            'method': hybrid_result['method'],
                            'ml_confidence': round(ml_conf * 100, 1)
                        }
                    else:
                        # CNN not supported by geometry -> use the rule-based winner.
                        print(f"[AI] CNN '{primary_type}' (conf {ml_conf:.0%}) overruled by "
                              f"geometry: winner '{geom_winner}' {geom_max:.1f}/10")
            except Exception as e:
                print(f"[WARN] Hybrid detection failed, using rule-based: {e}")
        
        # ==== RULE-BASED PRIORITY LOGIC (Fallback) ====
        # Smart priority logic - only suppress when there's true conflict
        # Priority 1: Strong leading lines (roads, paths) should NOT be suppressed
        if leading_lines_score >= 8.0:
            # Very strong leading lines - boost it, don't suppress
            composition_scores['leading_lines'] = min(leading_lines_score * 1.2, 10.0)
            # Only slightly reduce centered if leading lines are very strong
            if centered_score < leading_lines_score - 2:
                composition_scores['centered'] = centered_score * 0.8
        # Priority 2: Strong centered & symmetrical (but NOT when leading lines are dominant)
        elif centered_score >= 7.0 and symmetry_score >= 6.5:
            # Strongly boost centered/symmetrical, suppress leading lines/diagonal
            composition_scores['centered'] = min(centered_score * 1.7, 10.0)
            composition_scores['symmetrical'] = min(symmetry_score * 1.5, 10.0)
            composition_scores['leading_lines'] = leading_lines_score * 0.3
            composition_scores['diagonal'] = diagonal_score * 0.5
        elif centered_score >= 6.0 and symmetry_score >= 5.5:
            # Medium boost for moderately centered/symmetrical images
            composition_scores['centered'] = min(centered_score * 1.4, 10.0)
            composition_scores['symmetrical'] = min(symmetry_score * 1.3, 10.0)
            composition_scores['leading_lines'] = leading_lines_score * 0.5
            composition_scores['diagonal'] = diagonal_score * 0.7
        # If leading lines is moderate-high but centered/symmetrical are also moderate, prefer centered/symmetrical
        # BUT only if leading lines is NOT significantly higher
        elif leading_lines_score > 6 and leading_lines_score < 8 and (centered_score > 5.5 or symmetry_score > 5.5):
            if centered_score > leading_lines_score - 1.5:  # Only suppress if centered is close
                composition_scores['leading_lines'] = leading_lines_score * 0.6
        # If diagonal is high but centered/symmetrical are also moderate, prefer centered/symmetrical
        elif diagonal_score > 7 and (centered_score > 5.5 or symmetry_score > 5.5):
            composition_scores['diagonal'] = diagonal_score * 0.5
        
        # Determine primary composition type (highest score)
        primary_type = max(composition_scores, key=composition_scores.get)
        primary_score = min(composition_scores[primary_type], 10.0)  # Cap at 10
        
        # Secondary composition (second highest)
        sorted_compositions = sorted(composition_scores.items(), key=lambda x: x[1], reverse=True)
        secondary_type = sorted_compositions[1][0] if len(sorted_compositions) > 1 else None
        secondary_score = sorted_compositions[1][1] if len(sorted_compositions) > 1 else 0
        
        # Overall composition quality (capped at 10)
        overall_score = min(primary_score, 10.0)
        
        return {
            'detected_type': self.COMPOSITION_TYPES[primary_type]['name'],
            'type_key': primary_type,
            'description': self.COMPOSITION_TYPES[primary_type]['description'],
            'ideal_for': self.COMPOSITION_TYPES[primary_type]['ideal_for'],
            'score': round(min(overall_score, 10.0), 1),  # Ensure capped
            'quality': self._get_quality_rating(overall_score),
            'secondary_type': self.COMPOSITION_TYPES[secondary_type]['name'] if secondary_type else None,
            'all_scores': {k: round(min(v, 10.0), 1) for k, v in composition_scores.items()},  # Cap all scores
            'analysis_details': {
                'rule_of_thirds': round(thirds_score, 1),
                'centered': round(centered_score, 1),
                'leading_lines': round(leading_lines_score, 1),
                'diagonal': round(diagonal_score, 1),
                'symmetry': round(symmetry_score, 1),
                'golden_ratio': round(golden_ratio_score, 1)
            }
        }
    
    def _check_rule_of_thirds(self, gray):
        """Check if image follows rule of thirds"""
        h, w = gray.shape
        h_third, w_third = h // 3, w // 3
        
        # Check interest at intersection points
        points = [
            (h_third, w_third), (h_third, 2*w_third),
            (2*h_third, w_third), (2*h_third, 2*w_third)
        ]
        
        total_interest = 0
        for y, x in points:
            region = gray[max(0, y-30):min(h, y+30), max(0, x-30):min(w, x+30)]
            if region.size > 0:
                total_interest += np.std(region)
        
        avg_interest = total_interest / len(points)
        return min(10, (avg_interest / 8))
    
    def _check_centered(self, gray):
        """Check if subject is centered with improved accuracy"""
        h, w = gray.shape
        center_h, center_w = h // 2, w // 2
        
        # Check interest in center region (larger for better detection)
        center_size_h, center_size_w = h // 4, w // 4
        center_region = gray[center_h-center_size_h:center_h+center_size_h, 
                            center_w-center_size_w:center_w+center_size_w]
        
        # Define edge regions
        edge_size = min(h, w) // 8
        edge_regions = [
            gray[0:edge_size, :],  # Top
            gray[-edge_size:, :],  # Bottom
            gray[:, 0:edge_size],  # Left
            gray[:, -edge_size:]   # Right
        ]
        
        # Calculate interest (variance = detail/activity)
        center_interest = np.std(center_region) if center_region.size > 0 else 0
        edge_interest = np.mean([np.std(r) for r in edge_regions if r.size > 0])
        
        # Also check brightness concentration in center
        center_brightness = np.mean(center_region) if center_region.size > 0 else 0
        overall_brightness = np.mean(gray)
        brightness_ratio = center_brightness / (overall_brightness + 1)
        
        # Combined score: interest ratio + brightness concentration
        interest_ratio = center_interest / (edge_interest + 1)
        score = (interest_ratio * 4) + (brightness_ratio * 2)
        
        return min(10, score)
    
    def _check_leading_lines(self, gray):
        """Detect leading lines - roads, paths, converging lines"""
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=100, maxLineGap=15)
        
        if lines is None or len(lines) < 3:
            return 0
        
        h, w = gray.shape
        center_x, center_y = w // 2, h // 2
        
        # Analyze lines for leading characteristics
        parallel_pairs = []
        converging_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            
            if length < 80:  # Skip very short lines
                continue
            
            # Calculate angle (in degrees)
            angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi
            
            # Check if line points toward horizon/vanishing point (upper half of image)
            # Leading lines often converge toward top-center
            extends_to_horizon = (min(y1, y2) < h * 0.6)  # Reaches upper 60% of image
            
            # Calculate if line is approximately vertical (roads, paths)
            # or diagonal (stairs, converging lines)
            abs_angle = abs(angle)
            is_vertical_ish = (75 < abs_angle < 105)  # Near vertical (roads, lane markings)
            is_diagonal = (20 < abs_angle < 70 or 110 < abs_angle < 160)  # Diagonal lines
            
            if (is_vertical_ish or is_diagonal) and length > 100:
                span_ratio = length / h  # Use height for vertical lines
                if span_ratio > 0.25:  # Line spans >25% of image height
                    converging_lines.append((x1, y1, x2, y2, length, angle))
        
        # Check for parallel line pairs (characteristic of roads, paths)
        for i, line1 in enumerate(converging_lines):
            for line2 in converging_lines[i+1:]:
                angle_diff = abs(line1[5] - line2[5])
                # Parallel if angles are similar (within 15 degrees)
                if angle_diff < 15 or angle_diff > 165:
                    parallel_pairs.append((line1, line2))
        
        # Calculate score
        score = 0
        
        # Strong boost for parallel pairs (roads, paths)
        if len(parallel_pairs) >= 2:
            score += 8  # Strong indication of leading lines
        elif len(parallel_pairs) >= 1:
            score += 6
        
        # Boost for multiple converging lines
        if len(converging_lines) >= 4:
            score += 4
        elif len(converging_lines) >= 3:
            score += 2
        
        return min(10, score)
    
    def _check_diagonal(self, gray):
        """Detect diagonal composition"""
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=80, maxLineGap=10)
        
        if lines is None:
            return 0
        
        diagonal_lines = 0
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.arctan2(y2-y1, x2-x1) * 180 / np.pi)
            # Strong diagonals: 35-55 degrees or 125-145 degrees
            if (35 < angle < 55) or (125 < angle < 145):
                diagonal_lines += 1
        
        return min(10, diagonal_lines / 2)
    
    def _check_symmetry(self, gray):
        """Check for vertical and horizontal symmetry with edge detection"""
        h, w = gray.shape
        
        # Edge detection for better symmetry analysis
        edges = cv2.Canny(gray, 50, 150)
        
        # Vertical symmetry
        mid_v = w // 2
        left_half = edges[:, :mid_v]
        right_half = cv2.flip(edges[:, mid_v:], 1)
        
        # Ensure same dimensions
        min_width = min(left_half.shape[1], right_half.shape[1])
        left_half = left_half[:, :min_width]
        right_half = right_half[:, :min_width]
        
        v_difference = np.mean(np.abs(left_half.astype(float) - right_half.astype(float)))
        v_symmetry = max(0, 10 - (v_difference / 25.5))
        
        # Horizontal symmetry
        mid_h = h // 2
        top_half = edges[:mid_h, :]
        bottom_half = cv2.flip(edges[mid_h:, :], 0)
        
        min_height = min(top_half.shape[0], bottom_half.shape[0])
        top_half = top_half[:min_height, :]
        bottom_half = bottom_half[:min_height, :]
        
        h_difference = np.mean(np.abs(top_half.astype(float) - bottom_half.astype(float)))
        h_symmetry = max(0, 10 - (h_difference / 25.5))
        
        # Return the higher symmetry score (favor strongest axis)
        return max(v_symmetry, h_symmetry)
    
    def _check_golden_ratio(self, gray):
        """Check if composition follows golden ratio (1.618:1)"""
        h, w = gray.shape
        golden_ratio = 1.618
        
        # Golden ratio points
        golden_h = int(h / golden_ratio)
        golden_w = int(w / golden_ratio)
        
        # Check interest at golden ratio points
        points = [
            (golden_h, golden_w), (golden_h, w - golden_w),
            (h - golden_h, golden_w), (h - golden_h, w - golden_w)
        ]
        
        total_interest = 0
        for y, x in points:
            region = gray[max(0, y-25):min(h, y+25), max(0, x-25):min(w, x+25)]
            if region.size > 0:
                total_interest += np.std(region)
        
        avg_interest = total_interest / len(points)
        return min(10, (avg_interest / 9))
    
    def _check_fill_frame(self, gray):
        """Check if subject fills the frame"""
        # Use edge detection to find subject boundaries
        edges = cv2.Canny(gray, 100, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return 0
        
        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        total_area = gray.shape[0] * gray.shape[1]
        
        # Score based on how much of frame is filled
        fill_ratio = contour_area / total_area
        return min(10, fill_ratio * 12)
    
    def _check_frame_in_frame(self, gray):
        """Detect frame-within-frame composition.

        A real framing element is a large, convex, 4-sided contour that ENCLOSES
        the image centre (an archway, window, doorway), not just any 4-vertex blob.
        The previous version counted every quad — including the image border and
        tiny noise contours — so cluttered images trivially "won" frame-in-frame.
        """
        h, w = gray.shape
        total_area = float(h * w)
        cx, cy = w / 2.0, h / 2.0

        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        qualifying = 0
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue

            area = cv2.contourArea(approx)
            # Must be a substantial region, but not the full-frame border itself.
            if area < 0.08 * total_area or area > 0.95 * total_area:
                continue

            x, y, bw, bh = cv2.boundingRect(approx)
            # Reject the outer image border (spans almost the whole frame).
            if bw > 0.95 * w and bh > 0.95 * h:
                continue
            # The frame must actually enclose the image centre.
            if not (x < cx < x + bw and y < cy < y + bh):
                continue

            qualifying += 1

        # Each genuine enclosing frame is strong evidence.
        return min(10, qualifying * 5)
    
    def _generate_dynamic_tips(self, results, composition_analysis):
        """
        Generate dynamic, specific tips based on actual analysis.
        Tips are personalized to the detected composition and quality scores.
        """
        tips = []
        
        detected_type = composition_analysis['type_key']
        comp_score = composition_analysis['score']
        tech_score = results['technical_quality']['overall_score']
        lighting_score = results['lighting_analysis']['overall_score']
        color_score = results['color_analysis']['overall_score']
        
        # COMPOSITION TIPS (more personalized, only if truly needed)
        if comp_score < 6:
            tips.append({
                'category': 'Composition',
                'priority': 'High',
                'current': f"Using {composition_analysis['detected_type']} (Score: {comp_score}/10)",
                'tip': f"Your {composition_analysis['detected_type']} could be stronger. {self._get_composition_improvement_tip(detected_type, comp_score)}",
                'alternative': self._suggest_better_composition(composition_analysis)
            })
        elif comp_score < 7.5:
            # Only show if alternative composition is much better
            alt = self._suggest_better_composition(composition_analysis)
            if alt and alt['score'] - comp_score > 1.5:
                tips.append({
                    'category': 'Composition',
                    'priority': 'Low',
                    'current': f"Good {composition_analysis['detected_type']} (Score: {comp_score}/10)",
                    'tip': f"Solid {composition_analysis['detected_type']}. {self._get_composition_enhancement_tip(detected_type)}",
                    'alternative': alt
                })
        # If comp_score >= 7.5, don't show composition tips - it's already very good!
        
        # TECHNICAL QUALITY TIPS
        tech = results['technical_quality']
        if tech['sharpness']['score'] < 6:
            tips.append({
                'category': 'Technical',
                'priority': 'High',
                'current': f"Sharpness: {tech['sharpness']['score']}/10",
                'tip': "Increase sharpness: Use a tripod, faster shutter speed (1/250s+), or enable image stabilization. Ensure proper focus on your subject.",
                'alternative': "Try focus stacking for landscapes or macro shots."
            })
        
        if tech['noise']['score'] < 6:
            tips.append({
                'category': 'Technical',
                'priority': 'High',
                'current': f"Noise Level: {tech['noise']['level']:.1f}",
                'tip': f"Reduce noise: Lower ISO to 400 or below, use more light, or shoot in RAW format for better noise reduction in post.",
                'alternative': "Consider using a denoising filter in post-processing."
            })
        
        # LIGHTING TIPS
        lighting = results['lighting_analysis']
        if lighting['overall_score'] < 6:
            if lighting['shadows']['percentage'] > 35:
                tips.append({
                    'category': 'Lighting',
                    'priority': 'High',
                    'current': f"Shadow coverage: {lighting['shadows']['percentage']}%",
                    'tip': "Harsh shadows detected. Use a fill light, reflector, or shoot during golden hour (sunrise/sunset) for softer shadows.",
                    'alternative': "Try HDR photography to balance shadows and highlights."
                })
            
            if lighting['evenness'] < 5.5:
                tips.append({
                    'category': 'Lighting',
                    'priority': 'Medium',
                    'current': f"Lighting evenness: {lighting['evenness']}/10",
                    'tip': "Uneven lighting. Use diffused light sources or shoot in shade for more consistent illumination.",
                    'alternative': "Position subject to face the light source directly."
                })
        
        # COLOR TIPS
        colors = results['color_analysis']
        if color_score < 6:
            if colors['saturation']['score'] < 5.5:
                tips.append({
                    'category': 'Color',
                    'priority': 'Medium',
                    'current': f"Saturation: {colors['saturation']['rating']}",
                    'tip': "Colors appear flat. Shoot during golden/blue hour, or increase vibrance in post-processing (+10 to +20).",
                    'alternative': "Use a polarizing filter to enhance colors naturally."
                })
        
        # POSE TIPS (when pose detected)
        pose = results['pose_analysis']
        if pose.get('detected'):
            pose_score = pose.get('quality_score', 0)
            visibility = pose.get('visibility', 0)
            
            if pose_score < 6:
                tips.append({
                    'category': 'Pose',
                    'priority': 'High',
                    'current': f"Pose Quality: {pose_score}/10",
                    'tip': "Improve pose visibility: Ensure subject faces the camera more directly, avoid cluttered backgrounds, and use better lighting on the subject.",
                    'alternative': "Position subject in center frame with clear background separation."
                })
            
            if visibility < 0.6:
                tips.append({
                    'category': 'Pose',
                    'priority': 'Medium',
                    'current': f"Visibility: {visibility*100:.0f}%",
                    'tip': "Subject partially obscured. Clear obstacles between camera and subject, or reposition for better full-body visibility.",
                    'alternative': "Use wider angle or step back to capture complete pose."
                })
        
        # COMPOSITION-SPECIFIC TIPS
        tips.extend(self._get_composition_specific_tips(detected_type, composition_analysis))
        
        # Sort by priority
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        tips.sort(key=lambda x: priority_order[x['priority']])
        
        return tips[:8]  # Return top 8 tips
    
    def _get_composition_improvement_tip(self, comp_type, score):
        """Get specific tip for improving detected composition"""
        tips = {
            'rule_of_thirds': "Place your main subject at one of the four intersection points where the grid lines cross, not dead center.",
            'centered': "Ensure your subject is perfectly centered both horizontally and vertically. Use gridlines in your camera.",
            'leading_lines': "Strengthen your lines - make them more prominent and ensure they lead to your main subject, not away from it.",
            'diagonal': "Emphasize diagonal elements - tilt your camera slightly or find stronger diagonal subjects (stairs, roads).",
            'symmetrical': "Perfect the symmetry - align your camera precisely with the axis of symmetry. Even small tilts break symmetry.",
            'golden_ratio': "Position your subject at the golden ratio points (about 38% from edges), not at the center or thirds.",
            'fill_the_frame': "Get closer to your subject or zoom in more. The subject should occupy 70-80% of the frame.",
            'frame_within_frame': "Use natural frames (windows, archways, trees) more prominently. The frame should be clearly visible."
        }
        return tips.get(comp_type, "Review composition fundamentals for this technique.")
    
    def _get_composition_enhancement_tip(self, comp_type):
        """Get enhancement tip for well-executed composition"""
        tips = {
            'rule_of_thirds': "Consider adding a secondary subject at another intersection point for added interest.",
            'centered': "Try combining with symmetry for even more impact.",
            'leading_lines': "Experiment with multiple leading lines converging at your subject.",
            'diagonal': "Try incorporating more diagonal elements for even more dynamism.",
            'symmetrical': "Perfect! Maybe try breaking symmetry slightly with a small asymmetric element for intrigue.",
            'golden_ratio': "Excellent use of golden ratio! Consider the spiral for even more advanced composition.",
            'fill_the_frame': "Great frame filling! Ensure you haven't cut off important details.",
            'frame_within_frame': "Perfect framing! Try multiple layers of frames for added depth."
        }
        return tips.get(comp_type, "Well executed! Keep exploring this technique.")
    
    def _suggest_better_composition(self, composition_analysis):
        """Suggest alternative composition that might work better"""
        current_type = composition_analysis['type_key']
        all_scores = composition_analysis['all_scores']
        
        # Find best alternative (exclude current type)
        alternatives = {k: v for k, v in all_scores.items() if k != current_type}
        if not alternatives:
            return None
        
        best_alt = max(alternatives, key=alternatives.get)
        best_score = min(alternatives[best_alt], 10.0)  # Cap at 10
        
        # Always show alternative if it scores above 4.0 (useful alternative)
        if best_score >= 4.0:
            return {
                'type': self.COMPOSITION_TYPES[best_alt]['name'],
                'score': round(best_score, 1),
                'reason': f"Your image shows potential for {self.COMPOSITION_TYPES[best_alt]['name']} (Score: {best_score:.1f}). {self.COMPOSITION_TYPES[best_alt]['description']}",
                'how_to': self._get_composition_how_to(best_alt)
            }
        
        return None
    
    def _get_composition_how_to(self, comp_type):
        """Get specific instructions for achieving a composition type"""
        how_to = {
            'rule_of_thirds': "Enable grid overlay on your camera. Place subject at intersection points, not center.",
            'centered': "Position subject dead center. Use symmetry and negative space around subject.",
            'leading_lines': "Find lines (roads, rivers, fences) that lead toward your subject. Position camera to emphasize lines.",
            'diagonal': "Tilt camera slightly or find diagonal subjects (stairs, slopes). Shoot from corners.",
            'symmetrical': "Find symmetrical subjects or reflections. Align camera precisely with symmetry axis.",
            'golden_ratio': "Position subject 38% from frame edges (not 33% like rule of thirds). Use golden spiral overlay.",
            'fill_the_frame': "Get very close to subject or use telephoto lens. Subject should occupy 70%+ of frame.",
            'frame_within_frame': "Shoot through windows, doorways, arches. Frame should surround your main subject."
        }
        return how_to.get(comp_type, "Study examples of this composition technique.")
    
    def _get_composition_specific_tips(self, comp_type, comp_analysis):
        """Get tips specific to the detected composition type"""
        tips = []
        
        # Based on composition type, give specific advanced tips
        if comp_type == 'rule_of_thirds':
            tips.append({
                'category': 'Composition Pro Tip',
                'priority': 'Low',
                'current': 'Using Rule of Thirds',
                'tip': "Pro tip: Don't just place subject at intersection points - also align horizons on the thirds lines for more impact.",
                'alternative': None
            })
        
        elif comp_type == 'leading_lines':
            tips.append({
                'category': 'Composition Pro Tip',
                'priority': 'Low',
                'current': 'Using Leading Lines',
                'tip': "Pro tip: Leading lines work best when they start from bottom corners and lead to your main subject.",
                'alternative': None
            })
        
        elif comp_type == 'centered':
            tips.append({
                'category': 'Composition Pro Tip',
                'priority': 'Low',
                'current': 'Using Centered Composition',
                'tip': "Pro tip: Centered composition works best with symmetrical subjects and lots of negative space around them.",
                'alternative': None
            })
        
        elif comp_type == 'symmetrical':
            tips.append({
                'category': 'Composition Pro Tip',
                'priority': 'Low',
                'current': 'Using Symmetrical Composition',
                'tip': "Pro tip: Perfect symmetry is powerful, but slight breaks in symmetry can add intrigue and focal points.",
                'alternative': None
            })
        
        return tips
    
    def _analyze_technical(self, image, pil_image):
        """Fast technical quality analysis"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Sharpness
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # Noise
        noise_level = self._estimate_noise(gray)
        
        # Brightness and contrast
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Dynamic range
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        non_zero = np.where(hist > hist.max() * 0.001)[0]
        dynamic_range = (non_zero[-1] - non_zero[0]) if len(non_zero) > 0 else 0
        
        # Scoring
        sharpness_score = min(10, max(0, (sharpness / 100) * 10))
        noise_score = max(0, 10 - (noise_level / 3))
        # Full credit across a well-exposed band [90,170] (centre 130, +/-40),
        # then taper; clamped so extremes don't go negative.
        brightness_score = float(min(10.0, max(0.0, 10.0 - max(0.0, abs(brightness - 130) - 40) / 9.0)))
        # Full credit for std in [25,75]; std=100 is harsh, not "perfect".
        contrast_score = float(min(10.0, max(0.0, 10.0 - max(0.0, abs(contrast - 50.0) - 25.0) / 4.0)))
        range_score = (dynamic_range / 255) * 10
        
        overall = (sharpness_score * 0.30 + noise_score * 0.25 + 
                  brightness_score * 0.20 + contrast_score * 0.15 + range_score * 0.10)
        
        return {
            'overall_score': round(overall, 1),
            'sharpness': {'score': round(sharpness_score, 1), 'value': round(sharpness, 0), 'rating': self._get_rating(sharpness_score)},
            'noise': {'score': round(noise_score, 1), 'level': round(noise_level, 2), 'rating': self._get_rating(noise_score)},
            'brightness': {'score': round(brightness_score, 1), 'value': round(brightness, 1), 'optimal': 90 <= brightness <= 170},
            'contrast': {'score': round(contrast_score, 1), 'value': round(contrast, 1), 'optimal': 30 <= contrast <= 80},
            'dynamic_range': {'score': round(range_score, 1), 'range': int(dynamic_range), 'utilization': round((dynamic_range/255)*100, 1)}
        }
    
    def _estimate_noise(self, gray):
        """Fast noise estimation"""
        h, w = gray.shape
        center_h, center_w = h // 4, w // 4
        sample = gray[center_h:3*center_h, center_w:3*center_w]
        filtered = cv2.medianBlur(sample, 3)
        diff = sample.astype(float) - filtered.astype(float)
        return min(np.std(diff), 50)
    
    def _analyze_lighting(self, image):
        """Fast lighting analysis"""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        mean_light = np.mean(l_channel)
        std_light = np.std(l_channel)
        
        shadows = np.sum(l_channel < 50) / l_channel.size
        highlights = np.sum(l_channel > 200) / l_channel.size
        
        evenness = max(0, 10 - (std_light / 10))
        exposure_score = float(min(10.0, max(0.0, 10.0 - abs(mean_light - 127) / 12.7)))
        # Shadows: up to ~40% dark coverage is free (low-key photos are valid),
        # then a gentle penalty — instead of the old slope that zeroed at 33%.
        shadow_excess = max(0.0, float(shadows) - 0.40)
        shadow_score = float(min(max(10.0 - shadow_excess * 12.0, 0.0), 10.0))
        # Highlights: a little bright detail (~1-8%) is ideal; zero is neutral,
        # not perfect; lots of blown highlights is bad.
        if highlights <= 0.08:
            highlight_score = 7.0 + (float(highlights) / 0.08) * 3.0
        else:
            highlight_score = 10.0 - (float(highlights) - 0.08) * 30.0
        highlight_score = float(min(max(highlight_score, 0.0), 10.0))
        
        overall = evenness * 0.35 + exposure_score * 0.30 + shadow_score * 0.20 + highlight_score * 0.15
        
        quality = 'Professional' if overall >= 8.5 else 'Excellent' if overall >= 7.5 else 'Good' if overall >= 6.5 else 'Fair' if overall >= 5.0 else 'Needs Improvement'
        
        return {
            'overall_score': round(overall, 1),
            'quality': quality,
            'evenness': round(evenness, 1),
            'exposure': round(exposure_score, 1),
            'shadows': {'percentage': round(shadows * 100, 1), 'score': round(shadow_score, 1)},
            'highlights': {'percentage': round(highlights * 100, 1), 'score': round(highlight_score, 1)},
            'mean_brightness': round(mean_light, 1),
            'consistency': round(max(0, 10 - std_light / 10), 1)
        }
    
    def _get_color_name(self, rgb):
        """Map an (r, g, b) triple to a human-readable colour name."""
        r, g, b = [int(v) for v in rgb[:3]]
        mx, mn = max(r, g, b), min(r, g, b)
        # Greyscale family (low saturation)
        if mx - mn < 25:
            if mx < 60:
                return 'Black'
            if mx > 200:
                return 'White'
            return 'Gray'
        # Hue from HSV
        import colorsys
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        deg = h * 360
        if s < 0.18:
            return 'Gray'
        if deg < 15 or deg >= 345:
            name = 'Red'
        elif deg < 45:
            name = 'Orange'
        elif deg < 70:
            name = 'Yellow'
        elif deg < 160:
            name = 'Green'
        elif deg < 200:
            name = 'Cyan'
        elif deg < 255:
            name = 'Blue'
        elif deg < 290:
            name = 'Purple'
        else:
            name = 'Pink'
        if v < 0.4:
            return f'Dark {name}'
        if v > 0.85 and s < 0.5:
            return f'Light {name}'
        return name

    def _analyze_colors(self, pil_image, image_rgb):
        """Fast color analysis"""
        from sklearn.cluster import KMeans
        
        img_small = pil_image.resize((100, 100))
        pixels = np.array(img_small).reshape(-1, 3)
        
        kmeans = KMeans(n_clusters=3, max_iter=50, n_init=3, random_state=42)
        kmeans.fit(pixels)
        
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        unique, counts = np.unique(labels, return_counts=True)
        percentages = (counts / len(labels)) * 100
        
        dominant_colors = []
        for color, pct in zip(colors, percentages):
            dominant_colors.append({
                'rgb': color.tolist(),
                'hex': f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}',
                'percentage': round(pct, 1),
                'name': self._get_color_name(color.tolist())
            })

        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        saturation = np.mean(hsv[:, :, 1])

        # Gentler factor so moderate saturation doesn't instantly max out.
        saturation_score = min(10, (saturation / 255) * 11)
        # Diversity = how spread apart the dominant colours are (continuous 0-10),
        # not a coarse count of distinct centroids (which could only reach 6).
        cc = colors.astype(float)
        if len(cc) < 2:
            diversity_score = 0.0
        else:
            dists = [np.linalg.norm(cc[i] - cc[j])
                     for i in range(len(cc)) for j in range(i + 1, len(cc))]
            diversity_score = min(10.0, (float(np.mean(dists)) / 150.0) * 10.0)

        # ---- Colour harmony from dominant-hue relationships ----
        harmony = self._analyze_color_harmony(colors, percentages)

        # Blend harmony into the overall colour quality
        overall = saturation_score * 0.35 + diversity_score * 0.2 + harmony['score'] * 0.45

        return {
            'overall_score': round(overall, 1),
            'dominant_colors': dominant_colors[:3],
            'saturation': {'score': round(saturation_score, 1), 'level': round(saturation, 1), 'rating': self._get_rating(saturation_score)},
            'harmony': harmony,
            'diversity': round(diversity_score, 1),
            'rating': self._get_rating(overall)
        }

    def _analyze_color_harmony(self, colors, percentages):
        """
        Classify the colour scheme from dominant-hue spacing and score how
        harmonious it is (monochromatic / analogous / complementary / triadic).
        """
        # Convert dominant RGB centroids to hue degrees (0-360)
        hues = []
        for c in colors:
            r, g, b = [v / 255.0 for v in c[:3]]
            mx, mn = max(r, g, b), min(r, g, b)
            diff = mx - mn
            if diff == 0:
                h = 0.0
            elif mx == r:
                h = (60 * ((g - b) / diff) + 360) % 360
            elif mx == g:
                h = (60 * ((b - r) / diff) + 120) % 360
            else:
                h = (60 * ((r - g) / diff) + 240) % 360
            hues.append(h)

        if len(hues) < 2:
            return {'score': 6.5, 'type': 'Monochromatic', 'rating': 'Good'}

        # Largest circular gap between sorted hues characterises the scheme
        sorted_h = sorted(hues)
        spreads = [abs(a - b) for a, b in zip(sorted_h, sorted_h[1:])]
        spreads.append(360 - (sorted_h[-1] - sorted_h[0]))
        max_spread = max(spreads)

        if max_spread <= 40:
            scheme, score = 'Monochromatic', 8.0
        elif max_spread <= 90:
            scheme, score = 'Analogous', 9.0
        elif 150 <= max_spread <= 210:
            scheme, score = 'Complementary', 8.5
        elif 100 <= max_spread <= 140:
            scheme, score = 'Triadic', 7.5
        else:
            scheme, score = 'Eclectic', 6.0

        return {'score': round(score, 1), 'type': scheme, 'rating': self._get_rating(score)}
    
    def _analyze_pose(self, image_rgb):
        """Fast pose detection"""
        if not self.pose:
            return {'detected': False}
        
        try:
            results = self.pose.process(image_rgb)
            if not results.pose_landmarks:
                return {'detected': False}
            
            landmarks = results.pose_landmarks.landmark
            visibility_avg = np.mean([lm.visibility for lm in landmarks])
            pose_score = min(10, visibility_avg * 12)
            
            return {
                'detected': True,
                'quality_score': round(pose_score, 1),
                'visibility': round(visibility_avg, 2),
                'rating': self._get_rating(pose_score),
                'landmarks_count': len(landmarks)
            }
        except:
            return {'detected': False}
    
    def _calculate_overall_rating(self, results):
        """Calculate overall rating, trusting the trained CNN more when confident."""
        tech = results['technical_quality']['overall_score']
        lighting = results['lighting_analysis']['overall_score']
        comp = results['composition_analysis']['score']
        colors = results['color_analysis']['overall_score']

        # When the trained composition CNN is confident, give composition more weight
        comp_obj = results['composition_analysis']
        ml_conf = comp_obj.get('ml_confidence', 0) / 100.0 if comp_obj.get('method') in ('ml', 'hybrid') else 0.0
        comp_weight = 0.25 + 0.10 * ml_conf          # 0.25 → 0.35 as confidence rises
        colors_weight = 0.20
        tech_weight = 0.30 - 0.05 * ml_conf
        lighting_weight = 1.0 - (comp_weight + colors_weight + tech_weight)

        overall = (tech * tech_weight + lighting * lighting_weight +
                   comp * comp_weight + colors * colors_weight)

        if results['pose_analysis'].get('detected'):
            pose_score = results['pose_analysis'].get('quality_score', 0)
            overall = overall * 0.95 + pose_score * 0.05

        overall = min(max(overall, 0.0), 10.0)

        category = ('Outstanding' if overall >= 9.0 else 'Excellent' if overall >= 8.0
                    else 'Very Good' if overall >= 7.0 else 'Good' if overall >= 6.0
                    else 'Fair' if overall >= 5.0 else 'Needs Improvement')

        aesthetic = results.get('aesthetic_score', {}).get('score',
                                 min((comp * 0.6 + colors * 0.4), 10.0))

        return {
            'score': round(overall, 1),
            'category': category,
            'grade': self._score_to_grade(overall),
            'breakdown': {
                'technical': tech,
                'lighting': lighting,
                'composition': comp,
                'colors': colors,
                'aesthetic': round(aesthetic, 1)
            }
        }

    def _assess_aesthetic(self, image_rgb, results):
        """
        Primary aesthetic scorer: the new NIMA-style deep aesthetic model
        (MobileNetV2 backbone). Falls back to the rule-based aesthetic score
        if the model is unavailable. Blends in the trained composition CNN.
        """
        try:
            from ml_models.aesthetic_model import get_assessor
            assessment = get_assessor().assess(image_rgb)

            # Blend the deep aesthetic score with the trained composition CNN
            comp_obj = results['composition_analysis']
            ml_conf = comp_obj.get('ml_confidence', 0) / 100.0 if comp_obj.get('method') in ('ml', 'hybrid') else 0.0
            comp_score = comp_obj.get('score', assessment['score'])
            blended = assessment['score'] * (1 - 0.25 * ml_conf) + comp_score * (0.25 * ml_conf)
            assessment['score'] = round(float(min(max(blended, 1.0), 10.0)), 1)

            # Surface composition as an extra factor for the UI
            assessment.setdefault('factors', {})['composition'] = round(float(comp_score), 1)
            return assessment
        except Exception as e:
            print(f"[WARN] Deep aesthetic model unavailable, using rule-based: {e}")
            return self._calculate_aesthetic_score(results)

    def _calculate_aesthetic_score(self, results):
        """
        Fallback aesthetic score driven by the trained composition model,
        colour harmony and lighting balance, with a per-factor breakdown.
        """
        comp_obj = results['composition_analysis']
        color_obj = results['color_analysis']
        light_obj = results['lighting_analysis']

        composition = comp_obj.get('score', 0)
        harmony = color_obj.get('harmony', {}).get('score', color_obj.get('overall_score', 0))
        saturation = color_obj.get('saturation', {}).get('score', 0)
        lighting = light_obj.get('overall_score', 0)

        # Confidence of the trained CNN raises trust in the composition factor
        ml_conf = comp_obj.get('ml_confidence', 0) / 100.0 if comp_obj.get('method') in ('ml', 'hybrid') else 0.0

        factors = {
            'composition': round(float(composition), 1),
            'color_harmony': round(float(harmony), 1),
            'color_vibrancy': round(float(saturation), 1),
            'lighting': round(float(lighting), 1),
        }

        score = (composition * (0.40 + 0.10 * ml_conf) +
                 harmony * 0.25 +
                 lighting * 0.20 +
                 saturation * (0.15 - 0.10 * ml_conf))
        score = float(min(max(score, 0.0), 10.0))

        if score >= 8.5:
            interp = f"Striking aesthetic - a {comp_obj.get('detected_type', 'strong')} composition with {color_obj.get('harmony', {}).get('type', 'cohesive')} colour."
        elif score >= 7.0:
            interp = f"Strong aesthetic. The {color_obj.get('harmony', {}).get('type', 'colour')} palette and composition work well together."
        elif score >= 5.5:
            interp = "Solid aesthetic foundation. Tightening composition or colour balance would lift it further."
        else:
            interp = "Aesthetic needs work - focus on composition and a more deliberate colour palette."

        return {
            'score': round(score, 1),
            'interpretation': interp,
            'factors': factors,
            'model': 'trained-cnn' if ml_conf > 0 else 'rule-based',
            'confidence': round(float(ml_conf) * 100, 1),
        }
    
    def _get_rating(self, score):
        """Convert score to rating"""
        if score >= 9.0: return 'Outstanding'
        elif score >= 8.0: return 'Excellent'
        elif score >= 7.0: return 'Very Good'
        elif score >= 6.0: return 'Good'
        elif score >= 5.0: return 'Fair'
        else: return 'Needs Improvement'
    
    def _get_quality_rating(self, score):
        """Get quality rating for composition"""
        if score >= 8.5: return 'Excellent'
        elif score >= 7.0: return 'Good'
        elif score >= 5.5: return 'Fair'
        else: return 'Needs Improvement'
    
    def _score_to_grade(self, score):
        """Convert score to grade"""
        if score >= 9.5: return 'A+'
        elif score >= 9.0: return 'A'
        elif score >= 8.5: return 'A-'
        elif score >= 8.0: return 'B+'
        elif score >= 7.5: return 'B'
        elif score >= 7.0: return 'B-'
        elif score >= 6.5: return 'C+'
        elif score >= 6.0: return 'C'
        elif score >= 5.5: return 'C-'
        elif score >= 5.0: return 'D'
        else: return 'F'
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# ---------------------------------------------------------------------------
# Process-wide singleton so the heavy models (composition CNN + aesthetic
# MobileNetV2) load ONCE, not on every request. Keeps analysis fast.
# ---------------------------------------------------------------------------
import threading as _threading

_SERVICE_INSTANCE = None
_SERVICE_LOCK = _threading.Lock()


def get_image_service():
    global _SERVICE_INSTANCE
    if _SERVICE_INSTANCE is None:
        with _SERVICE_LOCK:
            if _SERVICE_INSTANCE is None:
                _SERVICE_INSTANCE = OptimizedImageAnalysisService()
    return _SERVICE_INSTANCE
