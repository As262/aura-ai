"""
Quick Setup Script - Downloads sample training data
Uses Unsplash API to get sample images for each composition type
"""

import requests
import os
from pathlib import Path
import time

# Unsplash API configuration
# Get your free API key at: https://unsplash.com/developers
UNSPLASH_ACCESS_KEY = "fk5vRu7DiIm28wqUVDkVMrCwjdJ1rFhpLyH713q3wlo"  # Replace with your key

# Search queries for each composition type
SEARCH_QUERIES = {
    'rule_of_thirds': [
        'landscape rule of thirds',
        'portrait rule of thirds',
        'nature rule of thirds photography'
    ],
    'centered': [
        'symmetrical portrait centered',
        'centered composition architecture',
        'minimalist centered subject'
    ],
    'leading_lines': [
        'road perspective leading lines',
        'railway tracks converging',
        'hallway perspective architecture'
    ],
    'diagonal': [
        'diagonal composition stairs',
        'diagonal lines architecture',
        'dynamic diagonal photography'
    ],
    'symmetrical': [
        'symmetrical architecture mirror',
        'reflection symmetry water',
        'perfect symmetry building'
    ],
    'golden_ratio': [
        'golden ratio spiral nature',
        'fibonacci composition photography',
        'golden ratio landscape'
    ],
    'fill_the_frame': [
        'macro photography close up',
        'fill frame portrait',
        'texture photography closeup'
    ],
    'frame_within_frame': [
        'window frame photography',
        'doorway architecture frame',
        'archway composition'
    ]
}

def download_sample_images(images_per_type=10):
    """
    Download sample images for training
    
    Args:
        images_per_type: Number of images to download per composition type
    """
    
    if UNSPLASH_ACCESS_KEY == "YOUR_API_KEY_HERE":
        print("❌ Please set your Unsplash API key first!")
        print("\n📝 How to get API key:")
        print("1. Go to: https://unsplash.com/developers")
        print("2. Create account (free)")
        print("3. Create new app")
        print("4. Copy Access Key")
        print("5. Paste it in this script (UNSPLASH_ACCESS_KEY)")
        print("\n💡 OR: Download images manually from Unsplash.com")
        return
    
    base_dir = Path('training_data')
    
    for comp_type, queries in SEARCH_QUERIES.items():
        print(f"\n📥 Downloading {comp_type} images...")
        comp_dir = base_dir / comp_type
        comp_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = 0
        for query in queries:
            if downloaded >= images_per_type:
                break
            
            # Search Unsplash
            url = f"https://api.unsplash.com/search/photos"
            params = {
                'query': query,
                'per_page': min(30, images_per_type - downloaded),
                'client_id': UNSPLASH_ACCESS_KEY
            }
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    results = response.json()['results']
                    
                    for img_data in results:
                        if downloaded >= images_per_type:
                            break
                        
                        # Download image
                        img_url = img_data['urls']['regular']
                        img_id = img_data['id']
                        img_path = comp_dir / f"{img_id}.jpg"
                        
                        if img_path.exists():
                            continue
                        
                        img_response = requests.get(img_url)
                        if img_response.status_code == 200:
                            with open(img_path, 'wb') as f:
                                f.write(img_response.content)
                            downloaded += 1
                            print(f"  ✓ Downloaded {downloaded}/{images_per_type}")
                        
                        time.sleep(0.5)  # Rate limiting
                else:
                    print(f"  ⚠️ API error: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
        
        print(f"✅ {comp_type}: {downloaded} images")
    
    print("\n🎉 Sample dataset ready!")
    print(f"📁 Location: {base_dir.absolute()}")
    print("\n🔄 Next steps:")
    print("1. Review and organize images (remove poor quality)")
    print("2. Add more images for better accuracy (aim for 100+/type)")
    print("3. Run: python training/train_model.py")


def manual_download_guide():
    """Print manual download instructions"""
    
    print("\n" + "="*70)
    print("📖 MANUAL DOWNLOAD GUIDE")
    print("="*70)
    
    print("\n1️⃣ Go to Unsplash.com")
    print("2️⃣ Search for each composition type:")
    
    for comp_type, queries in SEARCH_QUERIES.items():
        print(f"\n   {comp_type}:")
        for query in queries:
            print(f"      - \"{query}\"")
    
    print("\n3️⃣ Download 50-200 images per type")
    print("4️⃣ Save to training_data/<composition_type>/")
    print("5️⃣ Run: python training/train_model.py")
    
    print("\n💡 TIP: Use high-quality images (at least 800x600)")
    print("="*70)


if __name__ == "__main__":
    print("🎨 Aura AI - Training Data Collection")
    print("="*70)
    
    choice = input("\nChoose option:\n1. Auto-download (requires API key)\n2. Manual guide\n\nChoice (1/2): ")
    
    if choice == "1":
        download_sample_images(images_per_type=10)
    else:
        manual_download_guide()
