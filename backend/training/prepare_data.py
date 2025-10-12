"""
Helper script to prepare training data folders
"""

from pathlib import Path
import os


def setup_training_folders(base_dir='training_data'):
    """Create folder structure for training data"""
    
    base_path = Path(base_dir)
    composition_types = [
        'rule_of_thirds',
        'centered',
        'leading_lines',
        'diagonal',
        'symmetrical',
        'golden_ratio',
        'fill_the_frame',
        'frame_within_frame'
    ]
    
    print(f"📁 Creating training data structure at: {base_path.absolute()}\n")
    
    for comp_type in composition_types:
        folder = base_path / comp_type
        folder.mkdir(parents=True, exist_ok=True)
    
    print("✅ Created folders:")
    for comp_type in composition_types:
        folder = base_path / comp_type
        count = len(list(folder.glob('*.jpg'))) + len(list(folder.glob('*.png')))
        print(f"  ├─ {comp_type}/ ({count} images)")
    
    print("\n" + "="*70)
    print("📸 HOW TO ADD TRAINING DATA")
    print("="*70)
    
    print("\n1️⃣ MANUAL METHOD (Recommended):")
    print("   • Download images from Unsplash.com or Pexels.com")
    print("   • Organize by composition type")
    print("   • Add 50-200 images per folder")
    
    print("\n2️⃣ SEARCH TERMS:")
    print("   • rule_of_thirds: 'landscape rule of thirds'")
    print("   • centered: 'symmetrical portrait centered'")
    print("   • leading_lines: 'road perspective converging lines'")
    print("   • diagonal: 'diagonal composition stairs'")
    print("   • symmetrical: 'symmetrical architecture mirror'")
    print("   • golden_ratio: 'golden ratio spiral nature'")
    print("   • fill_the_frame: 'macro photography close up'")
    print("   • frame_within_frame: 'window archway photography'")
    
    print("\n3️⃣ FREE IMAGE SOURCES:")
    print("   • https://unsplash.com (highest quality)")
    print("   • https://pexels.com (good variety)")
    print("   • https://pixabay.com (large collection)")
    
    print("\n4️⃣ TIPS:")
    print("   • More images = better accuracy")
    print("   • Aim for balanced classes (similar count per type)")
    print("   • Use diverse images (different subjects, lighting)")
    print("   • Minimum: 50 images/type, Ideal: 100-200/type")
    
    print("\n5️⃣ AFTER ADDING IMAGES:")
    print("   • Run: python training/train_model.py")
    print("   • Training will take 30min-2hrs depending on GPU/CPU")
    
    print("\n" + "="*70)
    
    return base_path


def create_readme(base_dir='training_data'):
    """Create README in training_data folder"""
    
    readme_path = Path(base_dir) / 'README.md'
    
    content = """# Training Data for Composition Detection

## Folder Structure

Each folder represents a composition type. Add 50-200 images per folder.

### Composition Types:

1. **rule_of_thirds/** - Images following the rule of thirds
   - Subject at intersection points of 1/3 grid lines
   - Example: Landscape with horizon on lower third

2. **centered/** - Centered composition
   - Subject in center of frame
   - Example: Centered portraits, symmetrical objects

3. **leading_lines/** - Leading lines composition
   - Lines guiding eye through image
   - Example: Roads, rivers, railway tracks, hallways

4. **diagonal/** - Diagonal composition
   - Strong diagonal elements
   - Example: Stairs, sloped roads, dynamic angles

5. **symmetrical/** - Symmetrical composition
   - Perfect balance through mirroring
   - Example: Architecture, reflections in water

6. **golden_ratio/** - Golden ratio composition
   - Based on Fibonacci sequence (1.618:1)
   - Example: Natural spirals, harmonious placements

7. **fill_the_frame/** - Fill the frame
   - Subject occupies most of frame
   - Example: Macro photography, close-up portraits

8. **frame_within_frame/** - Frame within frame
   - Natural frames created by scene elements
   - Example: Windows, doorways, arches

## 📸 How to Collect Images

### Option 1: Download from Free Stock Sites

**Best Sites:**
- [Unsplash](https://unsplash.com) - Highest quality, commercial free
- [Pexels](https://pexels.com) - Good variety
- [Pixabay](https://pixabay.com) - Large collection

**Search Examples:**
```
"landscape rule of thirds"
"symmetrical architecture"
"road leading lines perspective"
"diagonal stairs composition"
"macro flower close up"
"window frame photography"
```

### Option 2: Use Your Own Photos

Organize your existing photos by composition type.

## ✅ Quality Guidelines

- **Resolution:** At least 800x600 pixels
- **Format:** JPG or PNG
- **Quantity:** Minimum 50 per type, ideal 100-200
- **Diversity:** Different subjects, lighting, angles
- **Accuracy:** Make sure images match the composition type

## 🚀 After Adding Images

1. Check image counts:
   ```bash
   python training/prepare_data.py
   ```

2. Train the model:
   ```bash
   python training/train_model.py
   ```

3. Model will be saved to `ml_models/trained/`

## 📊 Expected Results

- **50 images/type:** ~70-75% accuracy
- **100 images/type:** ~80-85% accuracy
- **200+ images/type:** ~85-90% accuracy

The more diverse and accurate your training data, the better the model!
"""
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created README.md in {base_dir}/")


if __name__ == "__main__":
    base_dir = 'training_data'
    setup_training_folders(base_dir)
    create_readme(base_dir)
    
    print(f"\n🎯 Next steps:")
    print(f"1. Add images to {Path(base_dir).absolute()}")
    print(f"2. Run: python training/train_model.py")
    print(f"3. Wait for training to complete")
    print(f"4. Restart your server to use the new model!\n")
