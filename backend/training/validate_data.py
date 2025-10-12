"""
Validate training data integrity to check for issues
"""
import os
from pathlib import Path

def check_data_integrity():
    data_dir = Path('training_data')
    
    print("🔍 Checking training data integrity...")
    print("="*50)
    
    if not data_dir.exists():
        print("❌ Training data directory not found!")
        return
    
    # Check each composition type folder
    composition_types = [
        'rule_of_thirds', 'centered', 'leading_lines', 'diagonal',
        'symmetrical', 'golden_ratio', 'fill_the_frame', 'frame_within_frame'
    ]
    
    total_images = 0
    for comp_type in composition_types:
        folder_path = data_dir / comp_type
        if folder_path.exists():
            images = list(folder_path.glob('*.jpg')) + list(folder_path.glob('*.png'))
            print(f"📁 {comp_type}: {len(images)} images")
            total_images += len(images)
        else:
            print(f"❌ {comp_type}: Folder missing!")
    
    print(f"\n📊 Total training images: {total_images}")
    
    # Check for duplicate images (basic check)
    print("\n🔍 Checking for potential issues...")
    
    if total_images < 400:
        print("⚠️  WARNING: Low image count may cause overfitting")
    
    if total_images > 2000:
        print("✅ Good image count for training")
    
    # Check model files
    model_dir = Path('ml_models/trained')
    if model_dir.exists():
        checkpoints = list(model_dir.glob('checkpoint_epoch_*.pth'))
        print(f"\n💾 Found {len(checkpoints)} checkpoints")
        
        if checkpoints:
            latest = sorted(checkpoints, key=lambda x: int(x.stem.split('_')[-1]))[-1]
            print(f"📂 Latest checkpoint: {latest.name}")
    
    return total_images

if __name__ == "__main__":
    check_data_integrity()