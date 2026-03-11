from PIL import Image
import os

# Source image path
source_image = r"c:\Users\HP\AppData\Local\Microsoft\Windows\INetCache\IE\8IS8D3Y9\Gemini_Generated_Image_r0jvffr0jvffr0jv[1].png"

# Output directory
output_dir = r"c:\Users\HP\Desktop\aura ai\aura-ai\frontend\public"

# Check if source image exists
if not os.path.exists(source_image):
    print(f"Error: Source image not found at {source_image}")
    exit(1)

print(f"Loading image from: {source_image}")

# Open the source image
img = Image.open(source_image)

# Convert to RGBA if not already
if img.mode != 'RGBA':
    img = img.convert('RGBA')

print(f"Original image size: {img.size}")

# Create favicon.ico (16x16, 32x32, 48x48)
print("Creating favicon.ico...")
favicon_sizes = [(16, 16), (32, 32), (48, 48)]
favicon_images = []
for size in favicon_sizes:
    resized = img.resize(size, Image.Resampling.LANCZOS)
    favicon_images.append(resized)

favicon_path = os.path.join(output_dir, "favicon.ico")
favicon_images[0].save(favicon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
print(f"✓ Created: {favicon_path}")

# Create logo192.png
print("Creating logo192.png...")
logo192 = img.resize((192, 192), Image.Resampling.LANCZOS)
logo192_path = os.path.join(output_dir, "logo192.png")
logo192.save(logo192_path, 'PNG')
print(f"✓ Created: {logo192_path}")

# Create logo512.png
print("Creating logo512.png...")
logo512 = img.resize((512, 512), Image.Resampling.LANCZOS)
logo512_path = os.path.join(output_dir, "logo512.png")
logo512.save(logo512_path, 'PNG')
print(f"✓ Created: {logo512_path}")

print("\n✅ All favicon files created successfully!")
print("Files created:")
print(f"  - {favicon_path}")
print(f"  - {logo192_path}")
print(f"  - {logo512_path}")
print("\nPlease refresh your browser (Ctrl+Shift+R) to see the new favicon!")
