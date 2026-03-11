# 🤖 AI Image Analysis Guide

## Overview

Aura AI now includes advanced AI-powered image analysis capabilities that can rate images and provide detailed suggestions for improving pose, lighting, composition, and overall aesthetic quality.

## 🚀 Quick Start

### Step 1: Install AI Dependencies

**Windows:**
```bash
setup_ai.bat
```

**Linux/Mac:**
```bash
chmod +x setup_ai.sh
./setup_ai.sh
```

**Manual Installation:**
```bash
cd backend
pip install opencv-python mediapipe tensorflow scikit-image scipy matplotlib torch torchvision
```

### Step 2: Start the Server
```bash
cd backend
python manage.py runserver
```

## 📊 Analysis Features

### 1. Overall Rating (1-10 Scale)
- **Technical Quality** (30%): Sharpness, noise, exposure, contrast
- **Aesthetic Appeal** (40%): Color harmony, visual interest, artistic merit  
- **Composition** (30%): Rule of thirds, balance, symmetry, leading lines

### 2. Technical Quality Analysis
- **Sharpness Detection**: Laplacian variance analysis
- **Noise Assessment**: Statistical noise estimation
- **Exposure Analysis**: Histogram-based clipping detection
- **Brightness & Contrast**: Optimal range evaluation

### 3. Pose Analysis (MediaPipe Integration)
- **Pose Detection**: Full body landmark detection
- **Posture Evaluation**: Balance, symmetry, openness assessment
- **Pose Quality Scoring**: Based on professional photography standards
- **Improvement Suggestions**: Specific pose recommendations

### 4. Lighting Analysis
- **Light Direction Detection**: Primary light source analysis
- **Shadow/Highlight Analysis**: Dynamic range assessment
- **Color Temperature**: Warm/cool tone evaluation
- **Quality Rating**: Professional lighting standards

### 5. Composition Analysis
- **Rule of Thirds**: Subject positioning evaluation
- **Leading Lines**: Visual flow analysis
- **Symmetry Detection**: Balance assessment
- **Visual Weight Distribution**: Compositional balance

### 6. Color Analysis
- **Dominant Color Extraction**: Palette identification
- **Color Harmony**: Complementary/analogous relationships
- **Saturation Analysis**: Vibrance and naturalness
- **Temperature Analysis**: Warmth/coolness evaluation

## 🔗 API Endpoints

### Basic Analysis
```http
POST /api/aesthetic-analysis/
Content-Type: multipart/form-data

{
  "image": [file]
}
```

### Detailed Analysis (Recommended)
```http
POST /api/detailed-image-analysis/
Content-Type: multipart/form-data

{
  "image": [file]
}
```

### Response Example
```json
{
  "success": true,
  "analysis": {
    "overall_rating": {
      "score": 8.2,
      "category": "Very Good",
      "breakdown": {
        "technical": 7.8,
        "aesthetic": 8.5,
        "composition": 8.3
      }
    },
    "technical_quality": {
      "sharpness": {
        "score": 8.5,
        "level": "High"
      },
      "noise": {
        "level": 12.3,
        "rating": "Low"
      },
      "brightness": {
        "value": 145,
        "rating": "Good"
      },
      "contrast": {
        "value": 65,
        "rating": "Good"
      },
      "exposure": {
        "shadows_clipped": false,
        "highlights_clipped": false,
        "overall": "Good"
      }
    },
    "pose_analysis": {
      "detected": true,
      "quality_score": 7.5,
      "analysis": {
        "posture": "Good",
        "balance": "Balanced",
        "symmetry": "Good",
        "openness": "Open"
      },
      "suggestions": [
        {
          "category": "Pose",
          "priority": "Medium",
          "suggestion": "Try angling your body slightly towards the camera",
          "technical_details": "Creates more dynamic poses"
        }
      ]
    },
    "lighting_analysis": {
      "overall_quality": "Good",
      "brightness": {
        "mean": 145,
        "distribution": "Even"
      },
      "shadows": {
        "percentage": 15.2,
        "level": "Medium"
      },
      "highlights": {
        "percentage": 3.1,
        "level": "Low"
      },
      "direction": {
        "primary": "Front-left",
        "confidence": 0.7,
        "softness": "Medium"
      },
      "color_temperature": {
        "kelvin": 5500,
        "description": "Neutral"
      },
      "suggestions": []
    },
    "composition_analysis": {
      "rule_of_thirds": {
        "score": 8.0,
        "compliance": "Good",
        "suggestions": "Subject well positioned"
      },
      "leading_lines": {
        "score": 6.5,
        "detected": true,
        "strength": "Medium"
      },
      "symmetry": {
        "score": 6.0,
        "type": "Asymmetric",
        "balance": "Good"
      },
      "balance": {
        "score": 7.5,
        "type": "Well balanced",
        "weight_distribution": "Even"
      },
      "overall_score": 7.0
    },
    "color_analysis": {
      "dominant_colors": [
        {
          "hex": "#3498db",
          "percentage": 35,
          "name": "Blue"
        }
      ],
      "harmony": {
        "type": "Complementary",
        "score": 8.0,
        "description": "Colors work well together"
      },
      "temperature": {
        "warmth": "Neutral",
        "score": 7.0,
        "kelvin": 5500
      },
      "saturation": {
        "level": "Well saturated",
        "score": 7.5,
        "vibrance": "Natural"
      }
    },
    "aesthetic_score": {
      "score": 8.2,
      "factors": {
        "color_harmony": 7.5,
        "composition": 7.0,
        "balance": 7.5,
        "interest": 6.5,
        "quality": 7.0
      },
      "interpretation": "Good aesthetic quality with room for minor improvements"
    },
    "improvement_suggestions": [
      {
        "category": "Lighting",
        "priority": "Medium",
        "suggestion": "Consider using a reflector to reduce shadows",
        "technical_details": "Current shadow coverage: 15.2%"
      },
      {
        "category": "Composition",
        "priority": "Low",
        "suggestion": "Composition follows rule of thirds well",
        "technical_details": "Good subject positioning"
      }
    ]
  }
}
```

## 💡 Pre-trained vs Custom Models

### Current Implementation (Recommended)
- ✅ **No training required**
- ✅ **Ready to use immediately**
- ✅ **Based on proven algorithms**
- ✅ **MediaPipe integration for pose detection**
- ✅ **Computer vision techniques for quality assessment**

### If You Want to Train Custom Models

For specialized use cases, you could train custom models:

#### 1. Aesthetic Scoring Model
```python
# Example training approach using AVA dataset
import tensorflow as tf
from tensorflow.keras import layers

def create_aesthetic_model():
    model = tf.keras.Sequential([
        layers.Conv2D(32, 3, activation='relu'),
        layers.MaxPooling2D(2),
        layers.Conv2D(64, 3, activation='relu'),
        layers.MaxPooling2D(2),
        layers.Conv2D(128, 3, activation='relu'),
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation='relu'),
        layers.Dense(1, activation='sigmoid')  # Aesthetic score 0-1
    ])
    return model

# Training would require:
# - AVA dataset (250k images with aesthetic ratings)
# - GPU training setup
# - Several days/weeks of training time
```

#### 2. Style-Specific Models
- **Portrait Photography**: Train on portrait datasets
- **Landscape Photography**: Train on landscape datasets  
- **Product Photography**: Train on e-commerce datasets

#### 3. Custom Pose Scoring
```python
# Custom pose evaluation model
def train_pose_model():
    # Would require:
    # - Dataset of rated poses
    # - Professional photography standards
    # - Pose landmark annotations
    pass
```

## 🔧 Customization Options

### 1. Adjust Scoring Weights
```python
# In ai_services.py
weights = {
    'color_harmony': 0.2,    # Adjust these based on your preferences
    'composition': 0.25,
    'balance': 0.2,
    'interest': 0.15,
    'quality': 0.2
}
```

### 2. Add Custom Analysis
```python
def custom_analysis(self, image_rgb):
    """Add your custom analysis logic here"""
    # Example: Brand-specific color detection
    # Example: Face expression analysis
    # Example: Product-specific quality checks
    pass
```

### 3. Integrate Additional Models
```python
# Add CLIP for semantic understanding
# Add YOLO for object detection
# Add custom trained models
```

## 🎯 Optimization Tips

### 1. Performance
- Images are automatically resized for analysis
- MediaPipe models are optimized for real-time use
- Consider caching analysis results

### 2. Accuracy
- Ensure good lighting for pose detection
- Use high-resolution images for better analysis
- Consider image preprocessing for edge cases

### 3. Customization
- Adjust thresholds based on your specific use case
- Add domain-specific rules (portraits vs landscapes)
- Implement feedback loops for continuous improvement

## 🚀 Future Enhancements

### Planned Features
1. **Deep Learning Integration**: NIMA model for aesthetic scoring
2. **Advanced Pose Analysis**: Professional photography pose database
3. **Style Classification**: Automatic style detection and suggestions
4. **Batch Processing**: Analyze multiple images simultaneously
5. **Real-time Analysis**: Live camera feed analysis
6. **Custom Model Training**: Easy interface for training specialized models

### Integration Options
- **Mobile App**: React Native integration
- **Batch Processing**: CLI tool for bulk analysis
- **API Extensions**: Additional endpoints for specific use cases
- **Third-party Integration**: Webhook support for external services

## 🤝 Contributing

Want to improve the AI analysis? Here are areas for contribution:

1. **New Analysis Algorithms**: Implement additional quality metrics
2. **Model Integration**: Add pre-trained models (CLIP, NIMA, etc.)
3. **Performance Optimization**: Improve analysis speed
4. **Accuracy Improvements**: Better heuristics and thresholds
5. **Documentation**: More examples and use cases

## 📞 Support

If you encounter issues:

1. **Dependencies**: Run `pip install -r requirements.txt`
2. **Model Loading**: Models download automatically on first use
3. **Performance**: Consider using GPU acceleration for large batches
4. **Accuracy**: Provide feedback on analysis results for improvements

---

**Happy Analyzing! 📸✨**