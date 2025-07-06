import os
import random
import time
from icrawler.builtin import GoogleImageCrawler
from PIL import Image
from shutil import move
from pathlib import Path

# ----------- Configuration -----------
keyword = 'lion'
total_images = 2000
resize_to = (256, 256)
split_ratio = (0.7, 0.15, 0.15)
base_dir = f'dataset/{keyword}'
raw_dir = os.path.join(base_dir, 'raw')

# Create directory if it doesn't exist
Path(raw_dir).mkdir(parents=True, exist_ok=True)

# Check existing images
existing_images = len([f for f in os.listdir(raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
remaining_needed = total_images - existing_images

print(f"Existing images: {existing_images}")
print(f"Additional needed: {remaining_needed}")

if remaining_needed > 0:
    # Multiple search terms to avoid rate limiting
    search_terms = [
        'lion animal',
        'african lion',
        'male lion',
        'lioness female lion', 
        'lion pride',
        'lion wildlife',
        'lion savanna',
        'lion portrait'
    ]
    
    images_per_term = remaining_needed // len(search_terms) + 1
    
    for i, term in enumerate(search_terms):
        if remaining_needed <= 0:
            break
            
        print(f"\nCrawling with keyword '{term}'... ({i+1}/{len(search_terms)})")
        
        try:
            # Create crawler with conservative settings
            crawler = GoogleImageCrawler(
                storage={'root_dir': raw_dir},
                downloader_threads=1,  # Single thread to avoid being blocked
                parser_threads=1
            )
            
            crawler.crawl(
                keyword=term, 
                max_num=min(images_per_term, remaining_needed),
                offset=0
            )
            
            # Check progress
            current_count = len([f for f in os.listdir(raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
            remaining_needed = total_images - current_count
            print(f"Total collected so far: {current_count}")
            
            # Wait between searches to avoid being blocked
            if i < len(search_terms) - 1:
                print("Waiting...")
                time.sleep(15)
                
        except Exception as e:
            print(f"Failed for keyword '{term}': {e}")
            time.sleep(20)  # Longer wait on error
            continue

# Step 2: Resize and clean images
print("\nResizing and cleaning images...")
valid_images = []

for filename in os.listdir(raw_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        filepath = os.path.join(raw_dir, filename)
        try:
            with Image.open(filepath) as img:
                # Skip very small images
                if img.size[0] < 100 or img.size[1] < 100:
                    os.remove(filepath)
                    continue
                    
                img = img.convert('RGB')  # Ensure JPEG-compatible
                img = img.resize(resize_to, Image.Resampling.LANCZOS)
                
                # Save with consistent naming
                new_filename = f"lion_{len(valid_images):04d}.jpg"
                new_filepath = os.path.join(raw_dir, new_filename)
                img.save(new_filepath, 'JPEG', quality=95)
                
                # Remove old file if renamed
                if filepath != new_filepath:
                    os.remove(filepath)
                    
                valid_images.append(new_filename)
                
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)

print(f"Valid images: {len(valid_images)}")

# Step 3: Train/Val/Test split
if len(valid_images) > 0:
    random.shuffle(valid_images)
    
    train_count = int(len(valid_images) * split_ratio[0])
    val_count = int(len(valid_images) * split_ratio[1])
    
    splits = {
        'train': valid_images[:train_count],
        'val': valid_images[train_count:train_count+val_count],
        'test': valid_images[train_count+val_count:]
    }
    
    print(f"Data split: train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}")
    
    for split, files in splits.items():
        split_dir = os.path.join(base_dir, split, keyword)
        Path(split_dir).mkdir(parents=True, exist_ok=True)
        for f in files:
            move(os.path.join(raw_dir, f), os.path.join(split_dir, f))
    
    # Step 4: Cleanup raw directory
    try:
        os.rmdir(raw_dir)
    except:
        pass  # Directory might not be empty

    print("✅ Done! Images downloaded and split into train/val/test.")
    print(f"📁 Dataset location: {base_dir}")
else:
    print("❌ No valid images found.")