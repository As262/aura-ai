"""
Clean corrupted images from training data
"""
import os
from PIL import Image
from pathlib import Path

def clean_corrupted_images():
    """Remove corrupted images from training data"""
    training_data_dir = Path('training_data')
    
    if not training_data_dir.exists():
        print("❌ Training data directory not found!")
        return
    
    composition_types = [
        'rule_of_thirds', 'centered', 'leading_lines', 'diagonal',
        'symmetrical', 'golden_ratio', 'fill_the_frame', 'frame_within_frame'
    ]
    
    total_removed = 0
    total_checked = 0
    
    print("🧹 Cleaning corrupted images...")
    print("="*50)
    
    for comp_type in composition_types:
        folder_path = training_data_dir / comp_type
        
        if not folder_path.exists():
            print(f"⚠️ Folder not found: {comp_type}")
            continue
        
        # Get all image files
        image_files = list(folder_path.glob('*.jpg')) + list(folder_path.glob('*.jpeg')) + \
                     list(folder_path.glob('*.png')) + list(folder_path.glob('*.JPG')) + \
                     list(folder_path.glob('*.JPEG')) + list(folder_path.glob('*.PNG'))
        
        removed_count = 0
        
        for img_path in image_files:
            total_checked += 1
            
            try:
                # Try to open and verify the image
                with Image.open(img_path) as img:
                    img.verify()  # Verify image integrity
                
                # Try to load it again (verify() makes image unusable)
                with Image.open(img_path) as img:
                    img.convert('RGB')  # Test conversion
                    
            except Exception as e:
                print(f"🗑️ Removing corrupted: {img_path.name} - {e}")
                try:
                    img_path.unlink()  # Delete file
                    removed_count += 1
                    total_removed += 1
                except Exception as del_error:
                    print(f"❌ Failed to delete {img_path.name}: {del_error}")
        
        remaining = len(list(folder_path.glob('*.jpg'))) + len(list(folder_path.glob('*.jpeg'))) + \
                   len(list(folder_path.glob('*.png'))) + len(list(folder_path.glob('*.JPG'))) + \
                   len(list(folder_path.glob('*.JPEG'))) + len(list(folder_path.glob('*.PNG')))
        
        if removed_count > 0:
            print(f"📁 {comp_type}: Removed {removed_count} corrupted images, {remaining} remaining")
        else:
            print(f"📁 {comp_type}: All {remaining} images are valid ✅")
    
    print("\n" + "="*50)
    print(f"📊 Summary:")
    print(f"   Total images checked: {total_checked}")
    print(f"   Corrupted images removed: {total_removed}")
    print(f"   Clean images remaining: {total_checked - total_removed}")
    
    if total_removed > 0:
        print(f"\n✅ Cleaned up {total_removed} corrupted images!")
        print("🚀 Training should now work without image loading errors.")
    else:
        print("\n✅ No corrupted images found!")

if __name__ == "__main__":
    clean_corrupted_images()