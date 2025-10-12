"""
Test the current best model to verify its actual performance
"""
import torch
import torchvision.transforms as transforms
from PIL import Image
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from ml_models.composition_model import CompositionCNN

def test_model_performance():
    """Test if the model is actually performing as reported"""
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🎮 Testing on device: {device}")
    
    # Load the best model
    model_path = Path('ml_models/trained/composition_model_best.pth')
    
    if not model_path.exists():
        print("❌ No best model found!")
        return
    
    # Initialize model
    model = CompositionCNN(num_classes=8)
    
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        model = model.to(device)
        model.eval()
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Test with a few random images from training data
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    composition_types = [
        'rule_of_thirds', 'centered', 'leading_lines', 'diagonal',
        'symmetrical', 'golden_ratio', 'fill_the_frame', 'frame_within_frame'
    ]
    
    print("\n🧪 Testing model predictions...")
    print("="*50)
    
    correct_predictions = 0
    total_predictions = 0
    
    for i, comp_type in enumerate(composition_types):
        folder_path = Path(f'training_data/{comp_type}')
        
        if not folder_path.exists():
            continue
            
        # Test first 3 images from each category
        images = list(folder_path.glob('*.jpg'))[:3] + list(folder_path.glob('*.png'))[:3]
        
        for img_path in images[:3]:  # Test max 3 per category
            try:
                # Load and preprocess image
                image = Image.open(img_path).convert('RGB')
                input_tensor = transform(image).unsqueeze(0).to(device)
                
                # Get prediction
                with torch.no_grad():
                    outputs = model(input_tensor)
                    probabilities = torch.nn.functional.softmax(outputs, dim=1)
                    confidence, predicted = torch.max(probabilities, 1)
                    
                predicted_class = composition_types[predicted.item()]
                confidence_score = confidence.item() * 100
                
                # Check if prediction is correct
                is_correct = predicted_class == comp_type
                if is_correct:
                    correct_predictions += 1
                total_predictions += 1
                
                status = "✅" if is_correct else "❌"
                print(f"{status} {comp_type} → {predicted_class} ({confidence_score:.1f}%)")
                
            except Exception as e:
                print(f"❌ Error processing {img_path}: {e}")
    
    if total_predictions > 0:
        accuracy = (correct_predictions / total_predictions) * 100
        print(f"\n📊 Sample Test Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
        
        # Assess if the accuracy seems realistic
        if accuracy > 95:
            print("⚠️  WARNING: Accuracy seems too high - might indicate data leakage")
        elif accuracy > 85:
            print("✅ Good accuracy - model seems to be working correctly")
        elif accuracy > 70:
            print("✅ Reasonable accuracy for a trained model")
        else:
            print("❌ Low accuracy - model might have issues")
    else:
        print("❌ No images could be tested")

if __name__ == "__main__":
    test_model_performance()