import os
import json
from pathlib import Path
from PIL import Image

# Define directories
cache_dir = r"C:\Users\Ayan\Documents\GitHub\storage\cache"
main_dir = r"C:\Users\Ayan\Documents\GitHub\storage\main"
output_file = r"C:\Users\Ayan\Documents\GitHub\storage\index.json"

# Function to get files without extension
def get_file_without_extension(filename):
    return os.path.splitext(filename)[0]

# Function to determine resolution category and orientation
def get_resolution_info(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Determine orientation (Desktop vs Mobile)
            orientation = "Mobile" if height > width else "Desktop"
            
            # Determine resolution category
            if width >= 7680 or height >= 7680:
                resolution = "8K"
            elif width >= 3840 or height >= 3840:
                resolution = "4K"
            elif width >= 2560 or height >= 2560:
                resolution = "2K"
            elif width >= 1920 or height >= 1920:
                resolution = "1080p"
            elif width >= 1280 or height >= 1280:
                resolution = "720p"
            else:
                resolution = "SD"
                
            return {
                "width": width,
                "height": height,
                "resolution": resolution,
                "orientation": orientation
            }
    except Exception as e:
        print(f"Error reading image {image_path}: {str(e)}")
        return {
            "width": 0,
            "height": 0,
            "resolution": "Unknown",
            "orientation": "Unknown"
        }

# Get all files in cache directory
cache_files = {}
if os.path.exists(cache_dir):
    for file in os.listdir(cache_dir):
        if os.path.isfile(os.path.join(cache_dir, file)):
            base_name = get_file_without_extension(file)
            cache_files[base_name] = file

# Get all files in main directory
main_files = {}
if os.path.exists(main_dir):
    for file in os.listdir(main_dir):
        if os.path.isfile(os.path.join(main_dir, file)):
            base_name = get_file_without_extension(file)
            main_files[base_name] = file

# Create matching pairs
result = []
for base_name in set(cache_files.keys()).union(set(main_files.keys())):
    cache_file = cache_files.get(base_name, "")
    main_file = main_files.get(base_name, "")
    
    if cache_file or main_file:  # Only include if at least one exists
        entry = {
            "file_name": base_name,
            "file_cache_name": cache_file,
            "file_main_name": main_file
        }
        
        # Add resolution information if main file exists
        if main_file:
            main_path = os.path.join(main_dir, main_file)
            if os.path.isfile(main_path):
                resolution_info = get_resolution_info(main_path)
                entry.update({
                    "width": resolution_info["width"],
                    "height": resolution_info["height"],
                    "resolution": resolution_info["resolution"],
                    "orientation": resolution_info["orientation"]
                })
        
        result.append(entry)

# Write to JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4)

print(f"Index created successfully with {len(result)} entries at {output_file}")
