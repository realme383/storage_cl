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

# Load existing index.json if it exists
existing_entries = {}
if os.path.exists(output_file):
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            # Create a dictionary with file_name as key for quick lookup
            for entry in existing_data:
                if 'file_name' in entry:
                    existing_entries[entry['file_name']] = entry
        print(f"Loaded {len(existing_entries)} existing entries from {output_file}")
    except Exception as e:
        print(f"Error loading existing index file: {str(e)}")
        existing_entries = {}

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
new_entries = 0
updated_entries = 0

for base_name in set(cache_files.keys()).union(set(main_files.keys())):
    cache_file = cache_files.get(base_name, "")
    main_file = main_files.get(base_name, "")
    
    if cache_file or main_file:  # Only include if at least one exists
        # Check if this file already exists in the index
        if base_name in existing_entries:
            # Use existing entry but update if cache or main file has changed
            entry = existing_entries[base_name]
            changed = False
            
            if entry.get('file_cache_name', '') != cache_file:
                entry['file_cache_name'] = cache_file
                changed = True
                
            if entry.get('file_main_name', '') != main_file:
                entry['file_main_name'] = main_file
                # Get resolution info if main file has changed
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
                changed = True
            
            if changed:
                updated_entries += 1
                print(f"Updated: {base_name}")
            
            result.append(entry)
        else:
            # Create a new entry
            entry = {
                "file_name": base_name,
                "file_cache_name": cache_file,
                "file_main_name": main_file
            }
            
            # Add resolution information if main file exists
            if main_file:
                main_path = os.path.join(main_dir, main_file)
                if os.path.isfile(main_path):  # Fixed: removed extra parenthesis
                    resolution_info = get_resolution_info(main_path)
                    entry.update({
                        "width": resolution_info["width"],
                        "height": resolution_info["height"],
                        "resolution": resolution_info["resolution"],
                        "orientation": resolution_info["orientation"]
                    })
            
            result.append(entry)
            new_entries += 1
            print(f"New: {base_name}")

# Write to JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4)

print(f"Index created successfully: {len(result)} total entries ({new_entries} new, {updated_entries} updated)")
