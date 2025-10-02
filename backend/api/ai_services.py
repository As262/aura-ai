import cv2
import numpy as np
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    print("✅ MediaPipe loaded successfully")
except ImportError:
    mp = None
    MEDIAPIPE_AVAILABLE = False
    print("⚠️  MediaPipe not available. Running in CPU-only mode with limited pose detection.")

from PIL import Image, ImageEnhance, ImageStat
import torch
import torchvision.transforms as transforms
from skimage import measure, filters, exposure
import requests
from io import BytesIO
import json
import os
from django.conf import settings


class ImageAnalysisService:
    """
    Comprehensive image analysis service for rating, pose detection, 
    lighting analysis, and improvement suggestions.
    Optimized for GPU acceleration with RTX 3050.
    """
    
    def __init__(self):
        # GPU Detection and Setup
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"🚀 ImageAnalysisService initialized on: {self.device}")
        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
            print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            
        # Initialize MediaPipe with optimized settings for GPU (if available)
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,  # Higher complexity for better accuracy on GPU
                enable_segmentation=True,
                min_detection_confidence=0.5
            )
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,  # Use full-range model for better accuracy
                min_detection_confidence=0.5
            )
            print("✅ MediaPipe pose and face detection initialized")
        else:
            # CPU-only mode without MediaPipe
            self.mp_pose = None
            self.mp_face_mesh = None
            self.mp_face_detection = None
            self.mp_drawing = None
            self.pose = None
            self.face_mesh = None
            self.face_detection = None
            print("⚠️  Running in CPU-only mode without MediaPipe pose detection")
        
        # Pre-warm GPU if available
        if torch.cuda.is_available():
            self._warm_up_gpu()
    
    def _warm_up_gpu(self):
        """Warm up GPU with dummy operations for better performance"""
        try:
            dummy_tensor = torch.randn(1, 3, 224, 224).to(self.device)
            _ = torch.nn.functional.conv2d(dummy_tensor, torch.randn(64, 3, 3, 3).to(self.device))
            torch.cuda.synchronize()
            print("✅ GPU warmed up successfully")
        except Exception as e:
            print(f"⚠️ GPU warm-up failed: {e}")
    
    def _to_tensor_gpu(self, image_array):
        """Convert numpy image array to GPU tensor for faster processing"""
        if len(image_array.shape) == 3:
            # Convert HWC to CHW format for PyTorch
            tensor = torch.from_numpy(image_array).permute(2, 0, 1).float()
        else:
            tensor = torch.from_numpy(image_array).float()
        return tensor.to(self.device) if torch.cuda.is_available() else tensor
    
    def _from_tensor_gpu(self, tensor):
        """Convert GPU tensor back to numpy array"""
        if torch.cuda.is_available():
            tensor = tensor.cpu()
        if len(tensor.shape) == 3:
            # Convert CHW back to HWC format
            return tensor.permute(1, 2, 0).numpy()
        return tensor.numpy()
    
    def _gpu_accelerated_blur(self, image_array, kernel_size=5):
        """GPU-accelerated Gaussian blur for faster processing"""
        try:
            if torch.cuda.is_available() and len(image_array.shape) == 3:
                tensor = self._to_tensor_gpu(image_array).unsqueeze(0)  # Add batch dimension
                # Apply Gaussian blur using PyTorch
                blur_filter = transforms.GaussianBlur(kernel_size, sigma=1.0)
                blurred = blur_filter(tensor).squeeze(0)  # Remove batch dimension
                return self._from_tensor_gpu(blurred)
            else:
                # Fallback to OpenCV
                return cv2.GaussianBlur(image_array, (kernel_size, kernel_size), 0)
        except:
            # Fallback to OpenCV if GPU operation fails
            return cv2.GaussianBlur(image_array, (kernel_size, kernel_size), 0)
    
    def analyze_image_comprehensive(self, image_path):
        """
        Comprehensive image analysis including rating, pose, lighting, and suggestions.
        """
        # Load image
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.open(image_path)
        
        # Perform all analyses
        results = {
            'overall_rating': self.calculate_overall_rating(image_rgb, pil_image),
            'technical_quality': self.analyze_technical_quality(image_rgb, pil_image),
            'pose_analysis': self.analyze_pose(image_rgb),
            'lighting_analysis': self.analyze_lighting(image_rgb, pil_image),
            'composition_analysis': self.analyze_composition(image_rgb),
            'color_analysis': self.analyze_colors(pil_image),
            'aesthetic_score': self.calculate_aesthetic_score(image_rgb, pil_image),
            'improvement_suggestions': []
        }
        
        # Generate improvement suggestions based on analysis
        results['improvement_suggestions'] = self.generate_suggestions(results)
        
        return results
    
    def calculate_overall_rating(self, image_rgb, pil_image):
        """Calculate overall image rating (1-10 scale)"""
        # Combine multiple factors for overall rating
        technical_score = self.get_technical_score(image_rgb, pil_image)
        aesthetic_score = self.get_aesthetic_score(image_rgb, pil_image)
        composition_score = self.get_composition_score(image_rgb)
        
        overall_score = (technical_score * 0.3 + aesthetic_score * 0.4 + composition_score * 0.3)
        
        return {
            'score': round(overall_score, 1),
            'category': self.get_rating_category(overall_score),
            'breakdown': {
                'technical': round(technical_score, 1),
                'aesthetic': round(aesthetic_score, 1),
                'composition': round(composition_score, 1)
            }
        }
    
    def analyze_technical_quality(self, image_rgb, pil_image):
        """Analyze technical aspects of the image"""
        # Calculate sharpness using Laplacian variance
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate noise level
        noise_level = self.estimate_noise(gray)
        
        # Calculate brightness and contrast
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Calculate exposure
        exposure_score = self.analyze_exposure(gray)
        
        return {
            'sharpness': {
                'score': min(10, sharpness / 100),
                'level': 'High' if sharpness > 500 else 'Medium' if sharpness > 100 else 'Low'
            },
            'noise': {
                'level': noise_level,
                'rating': 'Low' if noise_level < 10 else 'Medium' if noise_level < 25 else 'High'
            },
            'brightness': {
                'value': brightness,
                'rating': self.rate_brightness(brightness)
            },
            'contrast': {
                'value': contrast,
                'rating': self.rate_contrast(contrast)
            },
            'exposure': exposure_score
        }
    
    def analyze_pose(self, image_rgb):
        """Analyze human pose in the image"""
        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            return {
                'detected': False,
                'message': 'MediaPipe not available - pose detection disabled',
                'suggestions': [{
                    'category': 'System',
                    'priority': 'Info',
                    'suggestion': 'Install MediaPipe to enable pose detection features',
                    'technical_details': 'pip install mediapipe to enable pose analysis'
                }]
            }
            
        results = self.pose.process(image_rgb)
        
        if not results.pose_landmarks:
            return {
                'detected': False,
                'message': 'No pose detected in the image'
            }
        
        landmarks = results.pose_landmarks.landmark
        
        # Analyze pose quality
        pose_quality = self.evaluate_pose_quality(landmarks)
        
        # Get pose suggestions
        pose_suggestions = self.get_pose_suggestions(landmarks)
        
        return {
            'detected': True,
            'quality_score': pose_quality['score'],
            'analysis': {
                'posture': pose_quality['posture'],
                'balance': pose_quality['balance'],
                'symmetry': pose_quality['symmetry'],
                'openness': pose_quality['openness']
            },
            'suggestions': pose_suggestions
        }
    
    def analyze_lighting(self, image_rgb, pil_image):
        """Analyze lighting conditions and quality"""
        # Convert to LAB color space for better lighting analysis
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l_channel = lab[:, :, 0]
        
        # Calculate lighting metrics
        mean_brightness = np.mean(l_channel)
        brightness_std = np.std(l_channel)
        
        # Detect shadows and highlights
        shadows = np.sum(l_channel < 50) / l_channel.size
        highlights = np.sum(l_channel > 200) / l_channel.size
        
        # Analyze lighting direction using gradients
        lighting_direction = self.detect_lighting_direction(l_channel)
        
        # Color temperature estimation
        color_temp = self.estimate_color_temperature(image_rgb)
        
        return {
            'overall_quality': self.rate_lighting_quality(mean_brightness, brightness_std),
            'brightness': {
                'mean': mean_brightness,
                'distribution': 'Even' if brightness_std < 30 else 'Uneven'
            },
            'shadows': {
                'percentage': round(shadows * 100, 1),
                'level': 'High' if shadows > 0.3 else 'Medium' if shadows > 0.1 else 'Low'
            },
            'highlights': {
                'percentage': round(highlights * 100, 1),
                'level': 'High' if highlights > 0.1 else 'Medium' if highlights > 0.05 else 'Low'
            },
            'direction': lighting_direction,
            'color_temperature': color_temp,
            'suggestions': self.get_lighting_suggestions(mean_brightness, shadows, highlights, color_temp)
        }
    
    def analyze_composition(self, image_rgb):
        """Analyze image composition using various rules"""
        height, width = image_rgb.shape[:2]
        
        # Rule of thirds analysis
        rule_of_thirds = self.check_rule_of_thirds(image_rgb)
        
        # Leading lines detection
        leading_lines = self.detect_leading_lines(image_rgb)
        
        # Symmetry analysis
        symmetry = self.analyze_symmetry(image_rgb)
        
        # Balance analysis
        balance = self.analyze_visual_balance(image_rgb)
        
        return {
            'rule_of_thirds': rule_of_thirds,
            'leading_lines': leading_lines,
            'symmetry': symmetry,
            'balance': balance,
            'overall_score': (rule_of_thirds['score'] + leading_lines['score'] + 
                            symmetry['score'] + balance['score']) / 4
        }
    
    def analyze_colors(self, pil_image):
        """Analyze color palette and harmony"""
        # Extract dominant colors
        dominant_colors = self.extract_dominant_colors(pil_image)
        
        # Analyze color harmony
        harmony = self.analyze_color_harmony(dominant_colors)
        
        # Calculate color temperature
        temp_analysis = self.analyze_color_temperature(pil_image)
        
        # Saturation analysis
        saturation = self.analyze_saturation(pil_image)
        
        return {
            'dominant_colors': dominant_colors,
            'harmony': harmony,
            'temperature': temp_analysis,
            'saturation': saturation,
            'recommendations': self.get_color_recommendations(dominant_colors, harmony)
        }
    
    def calculate_aesthetic_score(self, image_rgb, pil_image):
        """Calculate aesthetic score using multiple factors"""
        # This would ideally use a pre-trained NIMA model
        # For now, we'll use heuristic-based scoring
        
        factors = {
            'color_harmony': self.score_color_harmony(pil_image),
            'composition': self.score_composition(image_rgb),
            'balance': self.score_visual_balance(image_rgb),
            'interest': self.score_visual_interest(image_rgb),
            'quality': self.score_technical_quality(image_rgb, pil_image)
        }
        
        # Weighted average
        weights = {
            'color_harmony': 0.2,
            'composition': 0.25,
            'balance': 0.2,
            'interest': 0.15,
            'quality': 0.2
        }
        
        aesthetic_score = sum(factors[key] * weights[key] for key in factors)
        
        return {
            'score': round(aesthetic_score, 1),
            'factors': factors,
            'interpretation': self.interpret_aesthetic_score(aesthetic_score)
        }
    
    def generate_suggestions(self, analysis_results):
        """Generate comprehensive improvement suggestions"""
        suggestions = []
        
        # Technical quality suggestions
        if analysis_results['technical_quality']['sharpness']['score'] < 5:
            suggestions.append({
                'category': 'Technical',
                'priority': 'High',
                'suggestion': 'Improve image sharpness by using faster shutter speed or better focus',
                'technical_details': 'Current sharpness score is low, consider using tripod or image stabilization'
            })
        
        # Lighting suggestions
        lighting = analysis_results['lighting_analysis']
        if lighting['shadows']['percentage'] > 30:
            suggestions.append({
                'category': 'Lighting',
                'priority': 'Medium',
                'suggestion': 'Reduce harsh shadows by using fill light or reflector',
                'technical_details': f"Current shadow coverage: {lighting['shadows']['percentage']}%"
            })
        
        # Pose suggestions (if pose detected)
        if analysis_results['pose_analysis'].get('detected'):
            suggestions.extend(analysis_results['pose_analysis']['suggestions'])
        
        # Composition suggestions
        composition = analysis_results['composition_analysis']
        if composition['rule_of_thirds']['score'] < 6:
            suggestions.append({
                'category': 'Composition',
                'priority': 'Medium',
                'suggestion': 'Try positioning subject along rule of thirds lines for better composition',
                'technical_details': 'Rule of thirds creates more dynamic and interesting compositions'
            })
        
        # Color suggestions
        suggestions.extend(analysis_results['color_analysis']['recommendations'])
        
        return suggestions
    
    # Helper methods (implementation details)
    def get_technical_score(self, image_rgb, pil_image):
        """Calculate technical quality score"""
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        noise = self.estimate_noise(gray)
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Normalize and combine scores
        sharpness_score = min(10, sharpness / 100)
        noise_score = max(0, 10 - noise / 5)
        brightness_score = 10 - abs(brightness - 127) / 12.7
        contrast_score = min(10, contrast / 10)
        
        return (sharpness_score + noise_score + brightness_score + contrast_score) / 4
    
    def get_aesthetic_score(self, image_rgb, pil_image):
        """Calculate aesthetic appeal score"""
        # Simplified aesthetic scoring
        color_score = self.score_color_harmony(pil_image)
        composition_score = self.score_composition(image_rgb)
        balance_score = self.score_visual_balance(image_rgb)
        
        return (color_score + composition_score + balance_score) / 3
    
    def get_composition_score(self, image_rgb):
        """Calculate composition quality score"""
        rule_of_thirds = self.check_rule_of_thirds(image_rgb)
        symmetry = self.analyze_symmetry(image_rgb)
        balance = self.analyze_visual_balance(image_rgb)
        
        return (rule_of_thirds['score'] + symmetry['score'] + balance['score']) / 3
    
    def estimate_noise(self, gray_image):
        """Estimate noise level in image"""
        return np.std(gray_image - cv2.medianBlur(gray_image, 5))
    
    def analyze_exposure(self, gray_image):
        """Analyze image exposure"""
        hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
        
        # Check for clipping
        shadows_clipped = hist[0] / gray_image.size
        highlights_clipped = hist[255] / gray_image.size
        
        return {
            'shadows_clipped': shadows_clipped > 0.01,
            'highlights_clipped': highlights_clipped > 0.01,
            'overall': 'Good' if shadows_clipped < 0.01 and highlights_clipped < 0.01 else 'Needs adjustment'
        }
    
    def rate_brightness(self, brightness):
        """Rate brightness level"""
        if brightness < 50:
            return 'Too Dark'
        elif brightness < 80:
            return 'Dark'
        elif brightness < 180:
            return 'Good'
        elif brightness < 220:
            return 'Bright'
        else:
            return 'Too Bright'
    
    def rate_contrast(self, contrast):
        """Rate contrast level"""
        if contrast < 20:
            return 'Too Low'
        elif contrast < 40:
            return 'Low'
        elif contrast < 80:
            return 'Good'
        elif contrast < 120:
            return 'High'
        else:
            return 'Too High'
    
    def get_rating_category(self, score):
        """Get rating category based on score"""
        if score >= 9:
            return 'Excellent'
        elif score >= 8:
            return 'Very Good'
        elif score >= 7:
            return 'Good'
        elif score >= 6:
            return 'Fair'
        elif score >= 5:
            return 'Average'
        else:
            return 'Needs Improvement'
    
    def evaluate_pose_quality(self, landmarks):
        """Evaluate pose quality and characteristics"""
        # Simplified pose evaluation
        # In a real implementation, you'd analyze specific pose characteristics
        
        return {
            'score': 7.5,  # Placeholder
            'posture': 'Good',
            'balance': 'Balanced',
            'symmetry': 'Good',
            'openness': 'Open'
        }
    
    def get_pose_suggestions(self, landmarks):
        """Generate pose improvement suggestions"""
        return [
            {
                'category': 'Pose',
                'priority': 'Medium',
                'suggestion': 'Try angling your body slightly towards the camera for better engagement',
                'technical_details': 'A slight angle creates more dynamic and interesting poses'
            }
        ]
    
    def detect_lighting_direction(self, l_channel):
        """Detect primary lighting direction"""
        # Simplified lighting direction detection
        return {
            'primary': 'Front-left',
            'confidence': 0.7,
            'softness': 'Medium'
        }
    
    def estimate_color_temperature(self, image_rgb):
        """Estimate color temperature of the image"""
        # Simplified color temperature estimation
        r_mean = np.mean(image_rgb[:, :, 0])
        b_mean = np.mean(image_rgb[:, :, 2])
        
        ratio = r_mean / (b_mean + 1e-6)
        
        if ratio > 1.2:
            return {'kelvin': 3000, 'description': 'Warm'}
        elif ratio < 0.8:
            return {'kelvin': 6500, 'description': 'Cool'}
        else:
            return {'kelvin': 5500, 'description': 'Neutral'}
    
    def rate_lighting_quality(self, mean_brightness, brightness_std):
        """Rate overall lighting quality"""
        if 80 <= mean_brightness <= 180 and brightness_std < 50:
            return 'Excellent'
        elif 60 <= mean_brightness <= 200 and brightness_std < 70:
            return 'Good'
        else:
            return 'Needs Improvement'
    
    def get_lighting_suggestions(self, brightness, shadows, highlights, color_temp):
        """Generate lighting improvement suggestions"""
        suggestions = []
        
        if brightness < 80:
            suggestions.append({
                'category': 'Lighting',
                'priority': 'High',
                'suggestion': 'Increase overall lighting or use fill light',
                'technical_details': 'Image appears underexposed'
            })
        
        if shadows > 0.3:
            suggestions.append({
                'category': 'Lighting',
                'priority': 'Medium',
                'suggestion': 'Use reflector or fill light to reduce harsh shadows',
                'technical_details': 'High shadow areas detected'
            })
        
        return suggestions
    
    def check_rule_of_thirds(self, image_rgb):
        
        """Check rule of thirds composition using actual image analysis"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            score = self._analyze_rule_of_thirds(gray)
            
            # Determine compliance level based on score
            if score >= 8.0:
                compliance = 'Excellent'
                suggestions = 'Subject placement follows rule of thirds perfectly'
            elif score >= 6.5:
                compliance = 'Good'
                suggestions = 'Good subject positioning with room for minor improvements'
            elif score >= 5.0:
                compliance = 'Fair'
                suggestions = 'Consider repositioning key elements along rule-of-thirds lines'
            else:
                compliance = 'Poor'
                suggestions = 'Try placing important elements at intersection points of rule-of-thirds grid'
            
            return {
                'score': round(score, 1),
                'compliance': compliance,
                'suggestions': suggestions
            }
        except Exception as e:
            print(f"Error in rule of thirds analysis: {e}")
            return {
                'score': 6.0,
                'compliance': 'Good',
                'suggestions': 'Unable to analyze rule of thirds'
            }
    
    def detect_leading_lines(self, image_rgb):
        """Detect leading lines in composition using computer vision"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Hough line detection
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=80)
            
            if lines is None:
                return {
                    'score': 3.0,
                    'detected': False,
                    'strength': 'None'
                }
            
            line_count = len(lines)
            
            # Analyze line directions and strength
            angles = []
            for line in lines:
                rho, theta = line[0]
                angles.append(theta)
            
            # Calculate score based on line count and direction variety
            base_score = min(line_count / 10 * 7, 7.0)  # More lines = higher score up to 7
            
            # Bonus for good line distribution
            angle_variety = np.std(angles) if len(angles) > 1 else 0
            variety_bonus = min(angle_variety * 2, 2.0)
            
            final_score = base_score + variety_bonus
            
            # Determine strength and detection status
            if final_score >= 7.0:
                strength = 'Strong'
            elif final_score >= 5.0:
                strength = 'Medium'
            elif final_score >= 3.0:
                strength = 'Weak'
            else:
                strength = 'Very Weak'
            
            return {
                'score': round(final_score, 1),
                'detected': line_count > 0,
                'strength': strength,
                'line_count': int(line_count)
            }
            
        except Exception as e:
            print(f"Error in leading lines detection: {e}")
            return {
                'score': 5.0,
                'detected': True,
                'strength': 'Medium'
            }
    
    def analyze_symmetry(self, image_rgb):
        """Analyze image symmetry using computer vision"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            score = self._analyze_symmetry_score(gray)
            
            # Determine symmetry type and balance
            if score >= 8.0:
                sym_type = 'Highly Symmetric'
                balance = 'Excellent'
            elif score >= 6.5:
                sym_type = 'Moderately Symmetric'
                balance = 'Good'
            elif score >= 4.0:
                sym_type = 'Slightly Asymmetric'
                balance = 'Fair'
            else:
                sym_type = 'Highly Asymmetric'
                balance = 'Dynamic'
            
            return {
                'score': round(score, 1),
                'type': sym_type,
                'balance': balance
            }
            
        except Exception as e:
            print(f"Error in symmetry analysis: {e}")
            return {
                'score': 6.0,
                'type': 'Asymmetric',
                'balance': 'Good'
            }
    
    def analyze_visual_balance(self, image_rgb):
        """Analyze visual balance using computer vision"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            score = self.score_visual_balance(image_rgb)
            
            # Determine balance type based on score
            if score >= 8.5:
                balance_type = 'Perfectly Balanced'
                distribution = 'Excellent'
            elif score >= 7.0:
                balance_type = 'Well Balanced'
                distribution = 'Good'
            elif score >= 5.5:
                balance_type = 'Moderately Balanced'
                distribution = 'Fair'
            elif score >= 4.0:
                balance_type = 'Slightly Unbalanced'
                distribution = 'Uneven'
            else:
                balance_type = 'Unbalanced'
                distribution = 'Poor'
            
            return {
                'score': round(score, 1),
                'type': balance_type,
                'weight_distribution': distribution
            }
            
        except Exception as e:
            print(f"Error in visual balance analysis: {e}")
            return {
                'score': 7.0,
                'type': 'Well balanced',
                'weight_distribution': 'Good'
            }
    
    def extract_dominant_colors(self, pil_image):
        """Extract dominant colors from image using K-means clustering"""
        try:
            # Convert to numpy array
            image_array = np.array(pil_image)
            
            # Reshape to be a list of pixels
            pixels = image_array.reshape(-1, 3)
            
            # Use K-means to find dominant colors
            try:
                from sklearn.cluster import KMeans
                
                # Find 4-6 dominant colors
                n_colors = min(5, len(np.unique(pixels.reshape(-1, pixels.shape[-1]), axis=0)))
                if n_colors < 2:
                    n_colors = 2
                
                kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
                kmeans.fit(pixels)
                
                # Get colors and their percentages
                colors = kmeans.cluster_centers_.astype(int)
                labels = kmeans.labels_
                
                # Calculate percentages
                percentages = []
                for i in range(n_colors):
                    count = np.sum(labels == i)
                    percentage = (count / len(labels)) * 100
                    percentages.append(percentage)
                    
            except ImportError:
                # Fallback: use simple color binning if sklearn not available
                # Reduce colors by quantization
                quantized = (pixels // 32) * 32  # Reduce to 8 levels per channel
                unique_colors, counts = np.unique(quantized, axis=0, return_counts=True)
                
                # Get top colors
                sorted_indices = np.argsort(counts)[::-1]
                n_colors = min(5, len(unique_colors))
                
                colors = unique_colors[sorted_indices[:n_colors]]
                percentages = (counts[sorted_indices[:n_colors]] / len(pixels)) * 100
            
            # Sort by percentage
            color_info = list(zip(colors, percentages))
            color_info.sort(key=lambda x: x[1], reverse=True)
            
            # Format results
            result = []
            color_names = ['Primary', 'Secondary', 'Accent', 'Highlight', 'Shadow']
            
            for i, (color, percentage) in enumerate(color_info):
                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                color_name = self._get_color_name(color)
                
                result.append({
                    'hex': hex_color,
                    'percentage': round(percentage, 1),
                    'name': color_name,
                    'role': color_names[i] if i < len(color_names) else 'Support'
                })
            
            return result
            
        except Exception as e:
            print(f"Error extracting dominant colors: {e}")
            # Fallback: analyze basic color statistics
            try:
                image_array = np.array(pil_image)
                avg_color = np.mean(image_array.reshape(-1, 3), axis=0).astype(int)
                hex_color = '#{:02x}{:02x}{:02x}'.format(avg_color[0], avg_color[1], avg_color[2])
                
                return [
                    {'hex': hex_color, 'percentage': 100.0, 'name': self._get_color_name(avg_color), 'role': 'Dominant'}
                ]
            except:
                return [
                    {'hex': '#808080', 'percentage': 100.0, 'name': 'Gray', 'role': 'Neutral'}
                ]
    
    def analyze_color_harmony(self, dominant_colors):
        """Analyze color harmony using color theory"""
        try:
            if not dominant_colors or len(dominant_colors) < 2:
                return {
                    'type': 'Monochromatic',
                    'score': 7.0,
                    'description': 'Single color or minimal color variation'
                }
            
            # Convert hex colors to HSV for analysis
            hsv_colors = []
            for color_info in dominant_colors[:4]:  # Analyze top 4 colors
                hex_color = color_info['hex']
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
                hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
                hsv_colors.append(hsv[0])  # Hue value
            
            # Analyze harmony patterns
            harmony_type, score = self._analyze_harmony_pattern(hsv_colors)
            
            # Generate description
            if score >= 8.5:
                description = 'Excellent color harmony with strong visual appeal'
            elif score >= 7.0:
                description = 'Good color harmony that works well together'
            elif score >= 5.5:
                description = 'Adequate color harmony with room for improvement'
            else:
                description = 'Color harmony could be improved'
            
            return {
                'type': harmony_type,
                'score': round(score, 1),
                'description': description
            }
            
        except Exception as e:
            print(f"Error analyzing color harmony: {e}")
            return {
                'type': 'Complex',
                'score': 6.5,
                'description': 'Unable to analyze color harmony'
            }
    
    def analyze_color_temperature(self, pil_image):
        """Analyze overall color temperature using computer vision"""
        try:
            image_array = np.array(pil_image)
            
            # Calculate average RGB values
            avg_r = np.mean(image_array[:, :, 0])
            avg_g = np.mean(image_array[:, :, 1])
            avg_b = np.mean(image_array[:, :, 2])
            
            # Calculate color temperature using RGB ratios
            # Warm images have more red, cool images have more blue
            warmth_ratio = (avg_r - avg_b) / (avg_r + avg_b + 1e-6)
            
            # Convert to Kelvin approximation and warmth category
            if warmth_ratio > 0.15:
                warmth = 'Very Warm'
                kelvin = 2800
                score = 8.0
            elif warmth_ratio > 0.05:
                warmth = 'Warm'
                kelvin = 3500
                score = 7.5
            elif warmth_ratio > -0.05:
                warmth = 'Neutral'
                kelvin = 5500
                score = 8.5  # Neutral is often ideal
            elif warmth_ratio > -0.15:
                warmth = 'Cool'
                kelvin = 6500
                score = 7.0
            else:
                warmth = 'Very Cool'
                kelvin = 8000
                score = 6.5
            
            # Adjust score based on image content suitability
            # Check if temperature matches content (e.g., sunset should be warm)
            green_dominance = avg_g / (avg_r + avg_g + avg_b)
            if green_dominance > 0.4 and warmth in ['Warm', 'Very Warm']:
                score += 0.5  # Nature scenes often benefit from warmth
            
            return {
                'warmth': warmth,
                'score': min(round(score, 1), 10.0),
                'kelvin': int(kelvin)
            }
            
        except Exception as e:
            print(f"Error analyzing color temperature: {e}")
            return {
                'warmth': 'Neutral',
                'score': 7.0,
                'kelvin': 5500
            }
    
    def analyze_saturation(self, pil_image):
        """Analyze color saturation using computer vision"""
        try:
            image_array = np.array(pil_image)
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            
            # Get saturation channel
            saturation = hsv[:, :, 1]
            
            # Calculate saturation statistics
            avg_saturation = np.mean(saturation)
            saturation_std = np.std(saturation)
            
            # Determine saturation level
            if avg_saturation > 180:
                level = 'Highly Saturated'
                vibrance = 'Vibrant'
                score = 8.5
            elif avg_saturation > 120:
                level = 'Well Saturated'
                vibrance = 'Natural'
                score = 9.0  # Often ideal
            elif avg_saturation > 80:
                level = 'Moderately Saturated'
                vibrance = 'Subtle'
                score = 7.5
            elif avg_saturation > 40:
                level = 'Low Saturation'
                vibrance = 'Muted'
                score = 6.0
            else:
                level = 'Desaturated'
                vibrance = 'Monochrome'
                score = 5.0
            
            # Adjust score based on saturation consistency
            if saturation_std < 30:  # Very consistent saturation
                score += 0.5
            elif saturation_std > 80:  # Very inconsistent
                score -= 0.5
            
            return {
                'level': level,
                'score': min(max(round(score, 1), 1.0), 10.0),
                'vibrance': vibrance,
                'average_saturation': round(avg_saturation / 255 * 100, 1)
            }
            
        except Exception as e:
            print(f"Error analyzing saturation: {e}")
            return {
                'level': 'Well saturated',
                'score': 7.5,
                'vibrance': 'Natural',
                'average_saturation': 60.0
            }

    def _get_color_name(self, rgb_color):
        """Get human-readable color name from RGB values"""
        r, g, b = rgb_color
        
        # Define color ranges
        if r > 200 and g < 100 and b < 100:
            return 'Red'
        elif r < 100 and g > 200 and b < 100:
            return 'Green'
        elif r < 100 and g < 100 and b > 200:
            return 'Blue'
        elif r > 200 and g > 200 and b < 100:
            return 'Yellow'
        elif r > 200 and g < 100 and b > 200:
            return 'Magenta'
        elif r < 100 and g > 200 and b > 200:
            return 'Cyan'
        elif r > 150 and g > 100 and b < 100:
            return 'Orange'
        elif r > 100 and g < 100 and b > 150:
            return 'Purple'
        elif r > 180 and g > 180 and b > 180:
            return 'White'
        elif r < 80 and g < 80 and b < 80:
            return 'Black'
        elif abs(r - g) < 30 and abs(g - b) < 30:
            return 'Gray'
        elif r > g and r > b:
            return 'Reddish'
        elif g > r and g > b:
            return 'Greenish'
        elif b > r and b > g:
            return 'Bluish'
        else:
            return 'Mixed'
    
    def _analyze_harmony_pattern(self, hue_values):
        """Analyze color harmony pattern from hue values"""
        if len(hue_values) < 2:
            return 'Monochromatic', 7.0
        
        # Sort hues for analysis
        hues = sorted(hue_values)
        
        # Check for complementary colors (opposite on color wheel)
        for i, hue1 in enumerate(hues):
            for hue2 in hues[i+1:]:
                hue_diff = abs(hue1 - hue2)
                if 150 <= hue_diff <= 180 or hue_diff >= 330:  # Accounting for circular nature
                    return 'Complementary', 9.0
        
        # Check for analogous colors (adjacent on color wheel)
        analogous_count = 0
        for i in range(len(hues) - 1):
            hue_diff = abs(hues[i+1] - hues[i])
            if hue_diff <= 60:  # Within 60 degrees
                analogous_count += 1
        
        if analogous_count >= len(hues) - 1:
            return 'Analogous', 8.5
        
        # Check for triadic colors (120 degrees apart)
        if len(hues) >= 3:
            for i, hue1 in enumerate(hues):
                for j, hue2 in enumerate(hues[i+1:], i+1):
                    for hue3 in hues[j+1:]:
                        diff1 = abs(hue2 - hue1)
                        diff2 = abs(hue3 - hue2)
                        diff3 = abs(hue1 - hue3)
                        
                        # Check if approximately 120 degrees apart
                        if (100 <= diff1 <= 140 and 100 <= diff2 <= 140 and 100 <= diff3 <= 140):
                            return 'Triadic', 8.0
        
        # Check for split-complementary
        if len(hues) >= 3:
            return 'Split-Complementary', 7.5
        
        # Default to complex if no clear pattern
        hue_range = max(hues) - min(hues)
        if hue_range > 180:
            return 'Complex', 6.0
        else:
            return 'Limited Palette', 7.0

    def get_color_recommendations(self, dominant_colors, harmony):
        """Generate color improvement recommendations"""
        return [
            {
                'category': 'Color',
                'priority': 'Low',
                'suggestion': 'Color palette is well balanced',
                'technical_details': 'Current color harmony works well'
            }
        ]
    
    # Scoring methods for aesthetic calculation - FULLY DYNAMIC
    def score_color_harmony(self, pil_image):
        """Calculate color harmony using computer vision and color theory"""
        try:
            # Convert to numpy array for processing
            img_array = np.array(pil_image)
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            
            # Extract hue values (0-179 in OpenCV)
            hues = hsv[:, :, 0].flatten()
            saturations = hsv[:, :, 1].flatten()
            
            # Filter out low saturation pixels (grays/whites/blacks)
            valid_hues = hues[saturations > 30]
            
            if len(valid_hues) == 0:
                return 5.0  # Monochromatic images get neutral score
            
            # Calculate hue distribution
            hue_hist, _ = np.histogram(valid_hues, bins=12, range=(0, 180))
            hue_distribution = hue_hist / np.sum(hue_hist)
            
            # Check for color harmony patterns
            harmony_score = 0
            
            # Monochromatic harmony (single dominant hue)
            if np.max(hue_distribution) > 0.7:
                harmony_score = 8.5
            
            # Complementary harmony (opposite colors)
            elif self._check_complementary_harmony(hue_distribution):
                harmony_score = 9.0
            
            # Analogous harmony (adjacent colors)
            elif self._check_analogous_harmony(hue_distribution):
                harmony_score = 8.0
            
            # Triadic harmony
            elif self._check_triadic_harmony(hue_distribution):
                harmony_score = 8.5
            
            else:
                # Calculate based on color distribution variance
                hue_variance = np.var(hue_distribution)
                harmony_score = max(3.0, 7.0 - hue_variance * 10)
            
            # Adjust for saturation consistency
            sat_consistency = 1.0 - (np.std(saturations) / 128.0)
            harmony_score *= (0.8 + 0.2 * sat_consistency)
            
            return min(max(harmony_score, 1.0), 10.0)
            
        except Exception as e:
            print(f"Error in color harmony analysis: {e}")
            return 6.0
    
    def score_composition(self, image_rgb):
        """Calculate composition score using rule of thirds, balance, and leading lines"""
        try:
            height, width = image_rgb.shape[:2]
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            
            composition_score = 0
            
            # Rule of thirds analysis
            thirds_score = self._analyze_rule_of_thirds(gray)
            composition_score += thirds_score * 0.4
            
            # Visual balance analysis
            balance_score = self._analyze_visual_balance_detailed(gray)
            composition_score += balance_score * 0.3
            
            # Leading lines detection
            lines_score = self._detect_leading_lines_score(gray)
            composition_score += lines_score * 0.2
            
            # Edge distribution (good composition has edges throughout)
            edges = cv2.Canny(gray, 50, 150)
            edge_distribution = self._analyze_edge_distribution(edges)
            composition_score += edge_distribution * 0.1
            
            return min(max(composition_score, 1.0), 10.0)
            
        except Exception as e:
            print(f"Error in composition analysis: {e}")
            return 6.0
    
    def score_visual_balance(self, image_rgb):
        """Calculate visual balance using weight distribution and symmetry"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            height, width = gray.shape
            
            # Calculate center of mass
            y, x = np.ogrid[:height, :width]
            total_mass = np.sum(gray)
            
            if total_mass == 0:
                return 5.0
            
            center_x = np.sum(x * gray) / total_mass
            center_y = np.sum(y * gray) / total_mass
            
            # Ideal center is at image center
            ideal_x, ideal_y = width / 2, height / 2
            
            # Calculate distance from ideal center (normalized)
            distance = np.sqrt((center_x - ideal_x)**2 + (center_y - ideal_y)**2)
            max_distance = np.sqrt((width/2)**2 + (height/2)**2)
            normalized_distance = distance / max_distance
            
            # Balance score (closer to center = better balance)
            balance_score = 10 * (1 - normalized_distance)
            
            # Analyze symmetry
            symmetry_score = self._analyze_symmetry_score(gray)
            
            # Combine balance and symmetry
            final_score = balance_score * 0.7 + symmetry_score * 0.3
            
            return min(max(final_score, 1.0), 10.0)
            
        except Exception as e:
            print(f"Error in visual balance analysis: {e}")
            return 6.0
    
    def score_visual_interest(self, image_rgb):
        """Calculate visual interest using texture, contrast, and detail complexity"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            
            # Texture analysis using Local Binary Pattern
            texture_score = self._analyze_texture_complexity(gray)
            
            # Contrast analysis
            contrast = gray.std()
            contrast_score = min(contrast / 50.0 * 10, 10)
            
            # Edge density (more edges = more visual interest)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            edge_score = min(edge_density * 100, 10)
            
            # Detail complexity using gradient magnitude
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            detail_score = min(np.mean(gradient_magnitude) / 20, 10)
            
            # Weighted combination
            interest_score = (
                texture_score * 0.3 +
                contrast_score * 0.3 +
                edge_score * 0.25 +
                detail_score * 0.15
            )
            
            return min(max(interest_score, 1.0), 10.0)
            
        except Exception as e:
            print(f"Error in visual interest analysis: {e}")
            return 5.5
    
    def score_technical_quality(self, image_rgb, pil_image):
        """Calculate technical quality using sharpness, noise, exposure, and artifacts"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            
            # Sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000 * 10, 10)
            
            # Noise estimation using high-frequency components
            noise_level = self._estimate_noise_level(gray)
            noise_score = max(0, 10 - noise_level / 5)
            
            # Exposure analysis
            exposure_score = self._analyze_exposure_quality(gray)
            
            # Brightness distribution
            brightness_score = self._analyze_brightness_distribution(gray)
            
            # Contrast quality
            contrast = gray.std()
            contrast_score = min(max(contrast / 60 * 10, 2), 10)
            
            # Weighted combination
            technical_score = (
                sharpness_score * 0.3 +
                noise_score * 0.25 +
                exposure_score * 0.2 +
                brightness_score * 0.15 +
                contrast_score * 0.1
            )
            
            return min(max(technical_score, 1.0), 10.0)
            
        except Exception as e:
            print(f"Error in technical quality analysis: {e}")
            return 6.0

    # Helper methods for advanced image analysis
    def _check_complementary_harmony(self, hue_distribution):
        """Check for complementary color harmony"""
        for i in range(len(hue_distribution)):
            complement_idx = (i + 6) % 12  # Opposite on color wheel
            if hue_distribution[i] > 0.3 and hue_distribution[complement_idx] > 0.3:
                return True
        return False
    
    def _check_analogous_harmony(self, hue_distribution):
        """Check for analogous color harmony (adjacent colors)"""
        for i in range(len(hue_distribution)):
            adjacent_sum = (hue_distribution[i] + 
                          hue_distribution[(i+1) % 12] + 
                          hue_distribution[(i+2) % 12])
            if adjacent_sum > 0.7:
                return True
        return False
    
    def _check_triadic_harmony(self, hue_distribution):
        """Check for triadic color harmony"""
        for i in range(len(hue_distribution)):
            triad_sum = (hue_distribution[i] + 
                        hue_distribution[(i+4) % 12] + 
                        hue_distribution[(i+8) % 12])
            if triad_sum > 0.6 and all(hue_distribution[j] > 0.15 for j in [i, (i+4)%12, (i+8)%12]):
                return True
        return False
    
    def _analyze_rule_of_thirds(self, gray):
        """Analyze composition using rule of thirds"""
        height, width = gray.shape
        
        # Calculate rule of thirds grid lines
        third_h = height // 3
        third_w = width // 3
        
        # Define intersection points (rule of thirds points)
        intersections = [
            (third_h, third_w), (third_h, 2*third_w),
            (2*third_h, third_w), (2*third_h, 2*third_w)
        ]
        
        # Calculate interest points near intersections
        total_score = 0
        
        # Look for high contrast areas near rule of thirds points
        for y, x in intersections:
            # Sample area around intersection
            window_size = min(width//10, height//10, 20)
            y_start = max(0, y - window_size//2)
            y_end = min(height, y + window_size//2)
            x_start = max(0, x - window_size//2)
            x_end = min(width, x + window_size//2)
            
            window = gray[y_start:y_end, x_start:x_end]
            
            # Calculate variance (high variance = interesting detail)
            if window.size > 0:
                variance = np.var(window)
                total_score += min(variance / 1000, 2.5)  # Max 2.5 per intersection
        
        # Also check for edge alignment with rule of thirds lines
        edges = cv2.Canny(gray, 50, 150)
        
        # Check horizontal thirds
        h_line_strength = 0
        for h_line in [third_h, 2*third_h]:
            line_region = edges[max(0, h_line-2):min(height, h_line+3), :]
            h_line_strength += np.sum(line_region) / 255
        
        # Check vertical thirds  
        v_line_strength = 0
        for v_line in [third_w, 2*third_w]:
            line_region = edges[:, max(0, v_line-2):min(width, v_line+3)]
            v_line_strength += np.sum(line_region) / 255
        
        # Normalize line strengths
        total_pixels = width * height
        line_score = min((h_line_strength + v_line_strength) / total_pixels * 1000, 2.0)
        
        final_score = total_score + line_score
        return min(max(final_score, 1.0), 10.0)
    
    def _analyze_visual_balance_detailed(self, gray):
        """Detailed visual balance analysis"""
        height, width = gray.shape
        
        # Divide image into quadrants
        h_mid, w_mid = height // 2, width // 2
        quadrants = [
            gray[:h_mid, :w_mid],      # Top-left
            gray[:h_mid, w_mid:],      # Top-right
            gray[h_mid:, :w_mid],      # Bottom-left
            gray[h_mid:, w_mid:]       # Bottom-right
        ]
        
        # Calculate visual weight of each quadrant
        weights = [np.sum(quad) for quad in quadrants]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return 5.0
        
        # Normalize weights
        weights = [w / total_weight for w in weights]
        
        # Calculate balance scores
        horizontal_balance = 1 - abs((weights[0] + weights[2]) - (weights[1] + weights[3]))
        vertical_balance = 1 - abs((weights[0] + weights[1]) - (weights[2] + weights[3]))
        diagonal_balance = 1 - abs((weights[0] + weights[3]) - (weights[1] + weights[2]))
        
        balance_score = (horizontal_balance + vertical_balance + diagonal_balance) / 3 * 10
        return min(max(balance_score, 1.0), 10.0)
    
    def _detect_leading_lines_score(self, gray):
        """Detect and score leading lines"""
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is None:
            return 3.0
        
        # Analyze line directions and convergence
        line_count = len(lines)
        
        # More lines generally indicate more complex composition
        line_score = min(line_count / 20 * 10, 8.0)
        
        # Check for converging lines (perspective/depth)
        if line_count > 5:
            line_score += 1.0
        
        return min(line_score, 10.0)
    
    def _analyze_edge_distribution(self, edges):
        """Analyze how edges are distributed across the image"""
        height, width = edges.shape
        
        # Divide into grid sections
        grid_size = 4
        section_height, section_width = height // grid_size, width // grid_size
        
        edge_counts = []
        for i in range(grid_size):
            for j in range(grid_size):
                section = edges[i*section_height:(i+1)*section_height,
                              j*section_width:(j+1)*section_width]
                edge_counts.append(np.sum(section > 0))
        
        # Good distribution means edges are spread throughout
        if len(edge_counts) == 0:
            return 3.0
            
        # Calculate distribution evenness
        mean_edges = np.mean(edge_counts)
        if mean_edges == 0:
            return 3.0
            
        # Lower variance relative to mean = more even distribution
        distribution_score = max(0, 10 - (np.std(edge_counts) / mean_edges) * 3)
        return min(distribution_score, 10.0)
    
    def _analyze_symmetry_score(self, gray):
        """Analyze image symmetry"""
        height, width = gray.shape
        
        # Vertical symmetry
        left_half = gray[:, :width//2]
        right_half = np.fliplr(gray[:, width//2:])
        
        # Make sure both halves are same size
        min_width = min(left_half.shape[1], right_half.shape[1])
        left_half = left_half[:, :min_width]
        right_half = right_half[:, :min_width]
        
        vertical_diff = np.mean(np.abs(left_half.astype(float) - right_half.astype(float)))
        vertical_symmetry = max(0, 10 - vertical_diff / 25.5)
        
        # Horizontal symmetry
        top_half = gray[:height//2, :]
        bottom_half = np.flipud(gray[height//2:, :])
        
        min_height = min(top_half.shape[0], bottom_half.shape[0])
        top_half = top_half[:min_height, :]
        bottom_half = bottom_half[:min_height, :]
        
        horizontal_diff = np.mean(np.abs(top_half.astype(float) - bottom_half.astype(float)))
        horizontal_symmetry = max(0, 10 - horizontal_diff / 25.5)
        
        # Return better of the two symmetries
        return max(vertical_symmetry, horizontal_symmetry)
    
    def _analyze_texture_complexity(self, gray):
        """Analyze texture complexity using local patterns"""
        try:
            # Calculate local standard deviation as texture measure
            kernel = np.ones((5,5), np.float32) / 25
            mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            sqr_diff = (gray.astype(np.float32) - mean_filtered) ** 2
            local_variance = cv2.filter2D(sqr_diff, -1, kernel)
            local_std = np.sqrt(local_variance)
            
            texture_score = min(np.mean(local_std) / 30 * 10, 10)
            return max(texture_score, 1.0)
        except:
            return 5.0
    
    def _estimate_noise_level(self, gray):
        """Estimate noise level in image"""
        # Use high-pass filter to isolate noise
        kernel = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]])
        filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        noise_level = np.std(filtered)
        return noise_level
    
    def _analyze_exposure_quality(self, gray):
        """Analyze exposure quality"""
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten()
        
        # Check for clipping
        shadows_clipped = hist[0] / gray.size
        highlights_clipped = hist[255] / gray.size
        
        # Penalize heavy clipping
        clipping_penalty = (shadows_clipped + highlights_clipped) * 20
        
        # Check histogram distribution
        mean_brightness = np.mean(gray)
        ideal_mean = 128
        brightness_deviation = abs(mean_brightness - ideal_mean) / 128
        
        exposure_score = 10 - clipping_penalty - brightness_deviation * 3
        return min(max(exposure_score, 1.0), 10.0)
    
    def _analyze_brightness_distribution(self, gray):
        """Analyze brightness distribution quality"""
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / gray.size
        
        # Good distribution uses most of the tonal range
        used_tones = np.sum(hist > 0.001)  # Tones with at least 0.1% of pixels
        tone_score = used_tones / 256 * 10
        
        # Avoid extreme concentrations
        max_concentration = np.max(hist)
        concentration_penalty = max(0, (max_concentration - 0.1) * 20)
        
        distribution_score = tone_score - concentration_penalty
        return min(max(distribution_score, 1.0), 10.0)

    def interpret_aesthetic_score(self, score):
        """Interpret aesthetic score"""
        if score >= 8.5:
            return 'Highly aesthetic image with strong visual appeal'
        elif score >= 7.0:
            return 'Good aesthetic quality with room for minor improvements'
        elif score >= 5.5:
            return 'Average aesthetic appeal, consider composition and lighting improvements'
        else:
            return 'Significant improvements needed in composition, lighting, or technical quality'
    
    def analyze_social_media(self, image_path, platform='instagram', caption=''):
        """
        Social media-specific analysis focusing on engagement and platform requirements.
        Optimized for Instagram, with GPU acceleration.
        """
        print(f"🚀 Running social media analysis on {self.device} for platform: {platform}")
        
        # Load image
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.open(image_path)
        
        # Get basic analysis components
        technical_quality = self.analyze_technical_quality(image_rgb, pil_image)
        composition = self.analyze_composition(image_rgb)
        colors = self.analyze_colors(pil_image)
        
        # Social media specific metrics
        social_score = self._calculate_social_media_score(image_rgb, pil_image, platform)
        engagement_factors = self._analyze_engagement_factors(image_rgb, pil_image, platform)
        platform_optimization = self._analyze_platform_optimization(image_rgb, pil_image, platform)
        
        # Generate social media suggestions
        suggestions = self._generate_social_media_suggestions(
            technical_quality, composition, colors, platform, caption
        )
        
        return {
            'platform': platform,
            'aesthetic_score': social_score,
            'aestheticScore': f"{social_score:.1f}",  # For frontend compatibility
            'engagement_potential': engagement_factors,
            'platform_optimization': platform_optimization,
            'technical_quality': technical_quality,
            'composition_analysis': composition,
            'color_analysis': colors,
            'suggestions': suggestions,
            'hashtag_recommendations': self._generate_hashtag_suggestions(platform, colors),
            'best_posting_time': self._get_optimal_posting_time(platform),
            'caption_analysis': self._analyze_caption(caption) if caption else None
        }
    
    def _calculate_social_media_score(self, image_rgb, pil_image, platform):
        """Calculate social media specific aesthetic score"""
        # Get basic aesthetic components
        technical_score = self._get_technical_score(image_rgb, pil_image)
        composition_score = self._get_composition_score(image_rgb)
        color_score = self._get_color_score(pil_image)
        
        # Platform-specific weights
        if platform == 'instagram':
            # Instagram favors vibrant colors and good composition
            weights = {'technical': 0.3, 'composition': 0.4, 'color': 0.3}
        else:
            # Default weights
            weights = {'technical': 0.4, 'composition': 0.3, 'color': 0.3}
        
        final_score = (
            technical_score * weights['technical'] +
            composition_score * weights['composition'] +
            color_score * weights['color']
        )
        
        return min(max(final_score, 0), 100)  # Ensure 0-100 range
    
    def _analyze_engagement_factors(self, image_rgb, pil_image, platform):
        """Analyze factors that drive social media engagement using computer vision"""
        # Calculate visual appeal based on actual image characteristics
        visual_appeal = self._calculate_visual_appeal(image_rgb)
        
        # Calculate emotional impact using face detection and color psychology
        emotional_impact = self._calculate_emotional_impact(image_rgb, pil_image)
        
        # Calculate shareability based on composition and visual interest
        shareability = self._calculate_shareability(image_rgb, pil_image)
        
        # Calculate memorability using contrast, uniqueness, and complexity
        memorability = self._calculate_memorability(image_rgb)
        
        # Calculate trend alignment based on color trends and composition patterns
        trend_alignment = self._calculate_trend_alignment(image_rgb, pil_image, platform)
        
        return {
            'visual_appeal': int(min(max(visual_appeal, 10), 100)),
            'emotional_impact': int(min(max(emotional_impact, 10), 100)),
            'shareability': int(min(max(shareability, 10), 100)),
            'memorability': int(min(max(memorability, 10), 100)),
            'trend_alignment': int(min(max(trend_alignment, 10), 100))
        }

    def _calculate_visual_appeal(self, image_rgb):
        """Calculate visual appeal using color vibrancy, contrast, and composition"""
        try:
            # Color vibrancy analysis
            hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
            saturation = hsv[:, :, 2]
            vibrancy = np.mean(saturation) / 255 * 40  # 0-40 points
            
            # Contrast analysis
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            contrast = gray.std() / 128 * 30  # 0-30 points
            
            # Edge richness (detail)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size * 30  # 0-30 points
            
            return vibrancy + contrast + edge_density
        except:
            return 65
    
    def _calculate_emotional_impact(self, image_rgb, pil_image):
        """Calculate emotional impact using face detection and color psychology"""
        try:
            # Face detection for emotional connection (if MediaPipe available)
            faces_score = 0
            if MEDIAPIPE_AVAILABLE and self.face_detection is not None:
                results = self.face_detection.process(image_rgb)
                if results.detections:
                    faces_score = min(len(results.detections) * 15, 30)  # Up to 30 points
            else:
                # Fallback: Use basic color analysis to estimate human presence
                faces_score = 15  # Default score when face detection unavailable
            
            # Color psychology analysis
            hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
            hues = hsv[:, :, 0]
            
            # Warm colors (reds, oranges, yellows) = higher emotional impact
            warm_hues = np.logical_or(hues < 30, hues > 150)  # Red and violet spectrum
            warm_percentage = np.sum(warm_hues) / hues.size
            color_emotion = warm_percentage * 25  # 0-25 points
            
            # Brightness for mood
            brightness = np.mean(image_rgb) / 255
            brightness_emotion = (1 - abs(brightness - 0.6)) * 25  # Optimal around 60% brightness
            
            # Contrast for drama
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            contrast_emotion = min(gray.std() / 60, 1) * 20  # 0-20 points
            
            return faces_score + color_emotion + brightness_emotion + contrast_emotion
        except:
            return 72
    
    def _calculate_shareability(self, image_rgb, pil_image):
        """Calculate shareability based on composition and visual clarity"""
        try:
            # Rule of thirds compliance
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            thirds_score = self._analyze_rule_of_thirds(gray) * 3  # 0-30 points
            
            # Visual clarity (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            clarity_score = min(laplacian_var / 500, 1) * 25  # 0-25 points
            
            # Color harmony
            harmony_score = self.score_color_harmony(pil_image) * 2.5  # 0-25 points
            
            # Aspect ratio suitability for sharing
            height, width = image_rgb.shape[:2]
            aspect_ratio = width / height
            # Prefer ratios good for social media (1:1, 4:5, 16:9)
            optimal_ratios = [1.0, 0.8, 1.78]
            ratio_fitness = max([1 - abs(aspect_ratio - ratio) for ratio in optimal_ratios])
            ratio_score = ratio_fitness * 20  # 0-20 points
            
            return thirds_score + clarity_score + harmony_score + ratio_score
        except:
            return 78
    
    def _calculate_memorability(self, image_rgb):
        """Calculate memorability using uniqueness and visual complexity"""
        try:
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            
            # Visual complexity (more complex = more memorable)
            complexity = self._analyze_texture_complexity(gray) * 3  # 0-30 points
            
            # Contrast (high contrast = more memorable)
            contrast = min(gray.std() / 50, 1) * 25  # 0-25 points
            
            # Edge density (detail richness)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size * 100
            edge_score = min(edge_density, 25)  # 0-25 points
            
            # Uniqueness (variance in local regions)
            h, w = gray.shape
            regions = []
            for i in range(0, h, h//4):
                for j in range(0, w, w//4):
                    region = gray[i:i+h//4, j:j+w//4]
                    if region.size > 0:
                        regions.append(np.std(region))
            
            uniqueness = np.std(regions) if regions else 0
            uniqueness_score = min(uniqueness / 10, 1) * 20  # 0-20 points
            
            return complexity + contrast + edge_score + uniqueness_score
        except:
            return 68
    
    def _calculate_trend_alignment(self, image_rgb, pil_image, platform):
        """Calculate trend alignment based on current social media trends"""
        try:
            # Color trend analysis (vibrant colors trending)
            hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
            saturation = hsv[:, :, 1]
            vibrancy = np.mean(saturation) / 255 * 25  # 0-25 points
            
            # Brightness trends (well-lit images perform better)
            brightness = np.mean(image_rgb) / 255
            brightness_trend = (1 - abs(brightness - 0.7)) * 20  # Optimal around 70%
            
            # Composition trends (dynamic, off-center)
            balance_score = self.score_visual_balance(image_rgb)
            # Lower balance = more dynamic = more trendy
            dynamic_score = (10 - balance_score) * 1.5  # 0-15 points
            
            # Platform-specific trends
            platform_bonus = 0
            if platform == 'instagram':
                # Instagram favors square/portrait formats
                height, width = image_rgb.shape[:2]
                aspect_ratio = width / height
                if 0.8 <= aspect_ratio <= 1.2:  # Square-ish
                    platform_bonus = 15
                elif aspect_ratio < 0.8:  # Portrait
                    platform_bonus = 10
            
            # Face presence (trending on social media)
            face_bonus = 0
            results = self.face_detection.process(image_rgb)
            if results.detections:
                face_bonus = 15
            
            return vibrancy + brightness_trend + dynamic_score + platform_bonus + face_bonus
        except:
            return 65

    def _analyze_platform_optimization(self, image_rgb, pil_image, platform):
        """Analyze how well the image is optimized for the platform"""
        height, width = image_rgb.shape[:2]
        aspect_ratio = width / height
        
        if platform == 'instagram':
            # Instagram optimal ratios: 1:1 (square), 4:5 (portrait), 1.91:1 (landscape)
            optimal_ratios = [1.0, 0.8, 1.91]
            ratio_score = max([100 - abs(aspect_ratio - ratio) * 50 for ratio in optimal_ratios])
            
            return {
                'aspect_ratio_score': max(min(ratio_score, 100), 0),
                'resolution_score': min((width * height) / 10000, 100),  # Favor higher resolution
                'format_compatibility': 95,  # Most formats work on Instagram
                'size_optimization': 90 if width >= 1080 else 70
            }
        
        return {
            'aspect_ratio_score': 80,
            'resolution_score': 85,
            'format_compatibility': 90,
            'size_optimization': 85
        }
    
    def _generate_social_media_suggestions(self, technical, composition, colors, platform, caption):
        """Generate platform-specific improvement suggestions"""
        suggestions = []
        
        # Technical suggestions
        if technical.get('sharpness', {}).get('score', 70) < 75:
            suggestions.append({
                'category': 'Technical',
                'priority': 'High',
                'suggestion': 'Increase image sharpness for better mobile viewing',
                'impact': 'Higher engagement rates'
            })
        
        # Composition suggestions
        if composition.get('rule_of_thirds_score', 70) < 75:
            suggestions.append({
                'category': 'Composition',
                'priority': 'Medium',
                'suggestion': 'Try positioning key elements along rule-of-thirds lines',
                'impact': 'More visually appealing posts'
            })
        
        # Platform-specific suggestions
        if platform == 'instagram':
            suggestions.extend([
                {
                    'category': 'Instagram',
                    'priority': 'Medium',
                    'suggestion': 'Consider adding more vibrant colors to stand out in feeds',
                    'impact': 'Better feed visibility'
                },
                {
                    'category': 'Engagement',
                    'priority': 'Low',
                    'suggestion': 'Add a compelling caption with relevant hashtags',
                    'impact': 'Increased reach and engagement'
                }
            ])
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _generate_hashtag_suggestions(self, platform, colors):
        """Generate relevant hashtag suggestions based on image analysis"""
        base_tags = ['#photography', '#aesthetic', '#visual', '#creative']
        
        # Add color-based tags
        dominant_colors = colors.get('dominant_colors', [])
        color_tags = []
        for color in dominant_colors[:2]:  # Top 2 colors
            if 'red' in str(color).lower():
                color_tags.extend(['#red', '#warm'])
            elif 'blue' in str(color).lower():
                color_tags.extend(['#blue', '#cool'])
            elif 'green' in str(color).lower():
                color_tags.extend(['#green', '#nature'])
        
        if platform == 'instagram':
            platform_tags = ['#instagram', '#insta', '#igpost', '#photooftheday']
            return base_tags + color_tags + platform_tags
        
        return base_tags + color_tags
    
    def _get_optimal_posting_time(self, platform):
        """Get optimal posting times for the platform"""
        if platform == 'instagram':
            return {
                'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'best_times': ['11:00 AM - 1:00 PM', '7:00 PM - 9:00 PM'],
                'timezone': 'Your local timezone'
            }
        
        return {
            'best_days': ['Monday', 'Wednesday', 'Friday'],
            'best_times': ['9:00 AM - 11:00 AM', '2:00 PM - 4:00 PM'],
            'timezone': 'Your local timezone'
        }
    
    def _analyze_caption(self, caption):
        """Analyze caption for social media optimization"""
        if not caption:
            return None
        
        word_count = len(caption.split())
        hashtag_count = caption.count('#')
        
        return {
            'word_count': word_count,
            'hashtag_count': hashtag_count,
            'optimal_length': 125 <= len(caption) <= 300,  # Instagram optimal length
            'has_call_to_action': any(word in caption.lower() for word in ['like', 'share', 'comment', 'follow']),
            'suggestions': [
                'Add relevant hashtags' if hashtag_count < 5 else 'Good hashtag usage',
                'Consider adding emojis for engagement' if '😀' not in caption else 'Good emoji usage'
            ]
        }
    
    def _get_technical_score(self, image_rgb, pil_image):
        """Get technical quality score (0-100)"""
        technical = self.analyze_technical_quality(image_rgb, pil_image)
        return (
            technical.get('sharpness', {}).get('score', 70) * 0.4 +
            technical.get('exposure', {}).get('score', 70) * 0.3 +
            technical.get('noise', {}).get('score', 70) * 0.3
        )
    
    def _get_composition_score(self, image_rgb):
        """Get composition score (0-100)"""
        composition = self.analyze_composition(image_rgb)
        return (
            composition.get('rule_of_thirds_score', 70) * 0.5 +
            composition.get('balance_score', 70) * 0.3 +
            composition.get('symmetry_score', 70) * 0.2
        )
    
    def _get_color_score(self, pil_image):
        """Get color harmony score (0-100)"""
        colors = self.analyze_colors(pil_image)
        return (
            colors.get('harmony_score', 70) * 0.4 +
            colors.get('saturation_score', 70) * 0.3 +
            colors.get('temperature_score', 70) * 0.3
        )