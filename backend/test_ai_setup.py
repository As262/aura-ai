#!/usr/bin/env python3
"""
Test script for AI dependencies and image analysis service
"""

import sys
import os
import traceback

def test_dependencies():
    """Test all AI dependencies are installed correctly"""
    print("🔍 Testing AI Dependencies...\n")
    
    dependencies = [
        ('cv2', 'opencv-python', 'Computer vision library'),
        ('mediapipe', 'mediapipe', 'Google MediaPipe for pose detection'),
        ('tensorflow', 'tensorflow', 'TensorFlow for deep learning'),
        ('numpy', 'numpy', 'Numerical computing'),
        ('PIL', 'Pillow', 'Image processing'),
        ('skimage', 'scikit-image', 'Image processing algorithms'),
        ('scipy', 'scipy', 'Scientific computing'),
        ('matplotlib', 'matplotlib', 'Plotting library'),
        ('torch', 'torch', 'PyTorch (optional)')
    ]
    
    results = []
    for module, package, description in dependencies:
        try:
            if module == 'torch':
                # PyTorch is optional
                try:
                    __import__(module)
                    results.append(f"✅ {package}: OK - {description}")
                except ImportError:
                    results.append(f"⚠️  {package}: OPTIONAL - {description}")
            else:
                __import__(module)
                results.append(f"✅ {package}: OK - {description}")
        except ImportError as e:
            results.append(f"❌ {package}: MISSING - {description}")
            print(f"   Error: {e}")
    
    for result in results:
        print(result)
    
    missing = [r for r in results if "MISSING" in r]
    if missing:
        print(f"\n⚠️  {len(missing)} critical dependencies missing.")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n🎉 All critical AI dependencies are available!")
        return True

def test_ai_service():
    """Test the AI service functionality"""
    print("\n🤖 Testing AI Service...\n")
    
    try:
        # Add the parent directory to Python path to import api modules
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from api.ai_services import ImageAnalysisService
        
        print("✅ ImageAnalysisService imported successfully")
        
        # Initialize the service
        ai_service = ImageAnalysisService()
        print("✅ AI service initialized successfully")
        
        # Test with a dummy image path (won't actually analyze without real image)
        print("✅ AI service is ready for image analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        print("\nFull error traceback:")
        traceback.print_exc()
        return False

def test_model_loading():
    """Test MediaPipe model loading"""
    print("\n📱 Testing MediaPipe Models...\n")
    
    try:
        import mediapipe as mp
        
        # Test pose detection model
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,  # Use lighter model for testing
            enable_segmentation=False,
            min_detection_confidence=0.5
        )
        print("✅ MediaPipe Pose model loaded successfully")
        
        # Test face mesh model
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=False,  # Disable for lighter model
            min_detection_confidence=0.5
        )
        print("✅ MediaPipe Face Mesh model loaded successfully")
        
        # Clean up
        pose.close()
        face_mesh.close()
        
        return True
        
    except Exception as e:
        print(f"❌ MediaPipe model loading failed: {e}")
        print("\nFull error traceback:")
        traceback.print_exc()
        return False

def test_opencv_functionality():
    """Test OpenCV basic functionality"""
    print("\n📸 Testing OpenCV Functionality...\n")
    
    try:
        import cv2
        import numpy as np
        
        # Create a test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:, :] = [255, 0, 0]  # Blue image
        
        # Test basic operations
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        print("✅ Color space conversion working")
        
        # Test image processing
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        print("✅ Image filtering working")
        
        # Test edge detection
        edges = cv2.Canny(gray, 50, 150)
        print("✅ Edge detection working")
        
        print(f"✅ OpenCV version: {cv2.__version__}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenCV functionality test failed: {e}")
        return False

def print_system_info():
    """Print system information"""
    print("💻 System Information:")
    print(f"   Python version: {sys.version}")
    print(f"   Platform: {sys.platform}")
    print(f"   Python executable: {sys.executable}")
    
    try:
        import tensorflow as tf
        print(f"   TensorFlow version: {tf.__version__}")
        
        # Check for GPU
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"   GPUs available: {len(gpus)}")
            for i, gpu in enumerate(gpus):
                print(f"     GPU {i}: {gpu.name}")
        else:
            print("   GPUs available: None (CPU-only)")
            
    except ImportError:
        print("   TensorFlow: Not installed")
    
    try:
        import torch
        print(f"   PyTorch version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        print("   PyTorch: Not installed")

def main():
    """Main test function"""
    print("🧪 AI Image Analysis - Dependency Test\n")
    print("=" * 50)
    
    # Print system info
    print_system_info()
    print("\n" + "=" * 50)
    
    # Run tests
    tests = [
        ("Dependencies", test_dependencies),
        ("OpenCV Functionality", test_opencv_functionality),
        ("MediaPipe Models", test_model_loading),
        ("AI Service", test_ai_service)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your AI setup is ready.")
        print("\n📝 Next steps:")
        print("   1. Start Django server: python manage.py runserver")
        print("   2. Test image upload in the frontend")
        print("   3. Check the detailed analysis results")
    else:
        print("\n⚠️  Some tests failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        print("\n💡 If issues persist:")
        print("   1. Check Python version (3.8+ recommended)")
        print("   2. Try installing dependencies individually")
        print("   3. Check system compatibility with MediaPipe/TensorFlow")

if __name__ == "__main__":
    main()