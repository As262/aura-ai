# 🚀 Complete Setup Guide for AI Image Analysis

## Step-by-Step Installation

### Step 1: Install AI Dependencies

**Option A: Automated Setup (Recommended)**

**Windows:**
```powershell
# Navigate to your project directory
cd "c:\Users\avina\Desktop\Aura Ai\aura-ai"

# Run the setup script
.\setup_ai.bat
```

**Linux/Mac:**
```bash
# Navigate to your project directory
cd /path/to/aura-ai

# Make script executable and run
chmod +x setup_ai.sh
./setup_ai.sh
```

**Option B: Manual Installation**

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create and activate virtual environment:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. **Upgrade pip and install dependencies:**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Verify Installation

Run this test script to verify all dependencies are installed:

```python
# test_ai_dependencies.py
import sys

def test_dependencies():
    """Test all AI dependencies are installed correctly"""
    dependencies = [
        ('cv2', 'opencv-python'),
        ('mediapipe', 'mediapipe'),
        ('tensorflow', 'tensorflow'),
        ('numpy', 'numpy'),
        ('PIL', 'Pillow'),
        ('sklearn', 'scikit-learn'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib')
    ]
    
    results = []
    for module, package in dependencies:
        try:
            __import__(module)
            results.append(f"✅ {package}: OK")
        except ImportError:
            results.append(f"❌ {package}: MISSING")
    
    for result in results:
        print(result)
    
    missing = [r for r in results if "MISSING" in r]
    if missing:
        print(f"\n⚠️  {len(missing)} dependencies missing. Run: pip install -r requirements.txt")
        return False
    else:
        print("\n🎉 All AI dependencies installed successfully!")
        return True

if __name__ == "__main__":
    test_dependencies()
```

Run the test:
```bash
python test_ai_dependencies.py
```

### Step 3: Start the Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
python manage.py migrate  # Run database migrations
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install  # If not already done
npm start
```

### Step 4: Test the AI Analysis

1. Open http://localhost:3000 in your browser
2. Navigate to the Aesthetic Analyzer
3. Upload an image (JPEG, PNG, WebP)
4. Wait for the AI analysis to complete

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Import mediapipe could not be resolved"
**Solution:**
```bash
pip install mediapipe==0.10.0
# If that fails, try:
pip install --upgrade pip
pip install mediapipe --no-cache-dir
```

#### Issue 2: "TensorFlow not found"
**Solution:**
```bash
# For CPU-only version:
pip install tensorflow-cpu==2.13.0

# For GPU version (if you have CUDA setup):
pip install tensorflow==2.13.0
```

#### Issue 3: "OpenCV installation failed"
**Solution:**
```bash
# Try alternative installation:
pip install opencv-python-headless==4.8.0.76

# Or if you need GUI features:
pip install opencv-contrib-python==4.8.0.76
```

#### Issue 4: "Module 'skimage' not found"
**Solution:**
```bash
pip install scikit-image==0.20.0
```

#### Issue 5: "PyTorch installation issues"
**Solution:**
Visit https://pytorch.org/get-started/locally/ and select your system configuration, then run the suggested command.

For CPU-only:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### Issue 6: "Memory error during analysis"
**Solution:**
Reduce image size before analysis:
```python
# Add to ai_services.py
def resize_image_if_large(image_path, max_size=1920):
    """Resize image if it's too large"""
    image = cv2.imread(image_path)
    height, width = image.shape[:2]
    
    if max(height, width) > max_size:
        scale = max_size / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height))
        cv2.imwrite(image_path, image)
    
    return image_path
```

### Performance Optimization

#### GPU Acceleration (Optional)
If you have an NVIDIA GPU with CUDA:

1. **Install CUDA Toolkit:** https://developer.nvidia.com/cuda-downloads
2. **Install GPU-enabled TensorFlow:**
```bash
pip install tensorflow[and-cuda]==2.13.0
```
3. **Verify GPU detection:**
```python
import tensorflow as tf
print("GPUs Available: ", tf.config.list_physical_devices('GPU'))
```

#### Memory Management
Add these environment variables for better memory management:
```bash
# Windows (in Command Prompt):
set TF_FORCE_GPU_ALLOW_GROWTH=true
set TF_CPP_MIN_LOG_LEVEL=2

# Linux/Mac:
export TF_FORCE_GPU_ALLOW_GROWTH=true
export TF_CPP_MIN_LOG_LEVEL=2
```

## 🎯 Using Pre-trained Models vs Training Custom Models

### Pre-trained Models (Current Implementation) ✅

**Advantages:**
- ✅ Ready to use immediately
- ✅ No training data required
- ✅ Proven accuracy
- ✅ Fast setup
- ✅ Lower computational requirements

**Current Models Used:**
- **MediaPipe Pose**: Google's pose detection model
- **MediaPipe Face Mesh**: Facial landmark detection
- **Computer Vision Algorithms**: For technical quality assessment
- **Heuristic Models**: For aesthetic scoring

### Training Custom Models (Advanced Option)

**When to Consider:**
- You have specific industry requirements (e.g., fashion, real estate)
- You have access to large, labeled datasets
- You need domain-specific aesthetic preferences
- You have significant computational resources

**Requirements for Custom Training:**
```python
# Example dataset structure for aesthetic scoring
{
    "images": [
        {
            "path": "image1.jpg",
            "aesthetic_score": 8.5,
            "technical_score": 7.2,
            "pose_score": 9.1,
            "lighting_score": 8.0,
            "composition_score": 8.8
        }
        # ... thousands more examples
    ]
}
```

**Training Setup Example:**
```python
import tensorflow as tf
from tensorflow.keras import layers, models

def create_aesthetic_model():
    """Create a custom aesthetic scoring model"""
    base_model = tf.keras.applications.ResNet50(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(1, activation='sigmoid')  # Aesthetic score 0-1
    ])
    
    # Freeze base model layers initially
    base_model.trainable = False
    
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae']
    )
    
    return model

# Training would require:
# - 50,000+ labeled images
# - GPU with 8GB+ VRAM
# - Several days of training time
# - Validation dataset
# - Data augmentation pipeline
```

## 🔄 Model Updates and Maintenance

### Updating AI Models

1. **Check for MediaPipe updates:**
```bash
pip install --upgrade mediapipe
```

2. **Update TensorFlow:**
```bash
pip install --upgrade tensorflow
```

3. **Test after updates:**
```bash
python test_ai_dependencies.py
```

### Adding New Analysis Features

To add new analysis capabilities:

1. **Extend the ImageAnalysisService:**
```python
# In ai_services.py
def analyze_new_feature(self, image_rgb):
    """Add your new analysis feature here"""
    # Example: Emotion detection, object detection, etc.
    pass
```

2. **Update the API response:**
```python
# In views.py, update the analysis_result
analysis_result['new_feature'] = ai_service.analyze_new_feature(image_rgb)
```

3. **Update the frontend component:**
```javascript
// In DetailedAnalysisResults.js
{analysis.new_feature && (
  <div className="analysis-section new-feature">
    <h2>🆕 New Feature Analysis</h2>
    {/* Render new feature results */}
  </div>
)}
```

## 📊 Expected Results

After setup, you should see analysis results like:

### Overall Rating: 8.2/10 (Very Good)
- **Technical Quality**: 7.8/10
- **Aesthetic Appeal**: 8.5/10  
- **Composition**: 8.3/10

### Technical Analysis:
- **Sharpness**: High (8.5/10)
- **Noise**: Low (Good)
- **Brightness**: Good (145/255)
- **Contrast**: Good (65)

### Pose Analysis (if person detected):
- **Quality Score**: 7.5/10
- **Posture**: Good
- **Balance**: Balanced
- **Openness**: Open

### Lighting Analysis:
- **Overall Quality**: Good
- **Shadows**: 15.2% (Medium)
- **Color Temperature**: 5500K (Neutral)

### Composition Analysis:
- **Rule of Thirds**: 8.0/10
- **Visual Balance**: 7.5/10
- **Symmetry**: 6.0/10

### Priority Improvements:
1. **Medium Priority**: Consider using reflector to reduce shadows
2. **Low Priority**: Composition follows rule of thirds well

## 🚀 Next Steps

1. **Test with different image types** (portraits, landscapes, products)
2. **Customize scoring weights** based on your preferences
3. **Add custom analysis features** for your specific use case
4. **Integrate with your existing workflow**
5. **Consider training custom models** for specialized requirements

## 📞 Support

If you encounter issues:

1. **Check the console logs** in both frontend and backend
2. **Verify all dependencies** are installed correctly
3. **Test with smaller images** if memory issues occur
4. **Check Python version compatibility** (3.8+ recommended)
5. **Ensure sufficient disk space** for model downloads

Happy analyzing! 🎉📸