# Training Data for Composition Detection

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
