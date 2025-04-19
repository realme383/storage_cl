import os
import json
import time
from pathlib import Path
from PIL import Image
from datetime import datetime, timezone
import google.generativeai as genai
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define directories
cache_dir = r"D:\storage\cache"
main_dir = r"D:\storage\main"
output_file = r"D:\storage\index.json"


# Get Gemini API Key from environment variables ( dont be a fool like me and hardcode it eehehheh)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Function to get files without extension
def get_file_without_extension(filename):
    return os.path.splitext(filename)[0]

# Function to identify image content and categorize it
def identify_image(image_path):
    try:
        # Define predefined categories
        categories = [
            "#nature",
            "#anime",
            "#art",
            "#abstract",
            "#cars",
            "#architecture",
            "#minimal",
            "#tech"
        ]
        
        # Read the image file
        with Image.open(image_path) as img:
            # Resize image if too large to save bandwidth and processing time
            max_size = 800
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()
        
        # Set up the Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create the prompt
        prompt = f"""
        Analyze this image and categorize it into exactly one of these categories:
        {', '.join(categories)}
        
        Just respond with the category name only, including the # symbol. No explanation.
        """
        
        # Call the Gemini API
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
        
        # Clean up response to get just the category
        category = response.text.strip()
        
        # Validate the category is one of our predefined options
        if category not in categories:
            # If not a perfect match, try to match the closest one
            for valid_category in categories:
                if valid_category.lower() in category.lower():
                    category = valid_category
                    break
            else:
                # Default to #art if no match found
                print(f"Warning: Unrecognized category '{category}' for {image_path}. Defaulting to #art.")
                category = "#art"
                
        return category

    except Exception as e:
        print(f"Error identifying image {image_path}: {str(e)}")
        return "#art"  # Default category on error

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

# Function to get file timestamp in ISO format
def get_file_timestamp(file_path):
    try:
        mod_time = os.path.getmtime(file_path)
        # Convert Unix timestamp to ISO format string
        dt_object = datetime.fromtimestamp(mod_time, tz=timezone.utc)
        iso_timestamp = dt_object.isoformat()
        return iso_timestamp
    except Exception as e:
        print(f"Error getting timestamp for {file_path}: {str(e)}")
        return ""

# Function to compare two ISO format timestamps
def is_newer_timestamp(timestamp1, timestamp2):
    if not timestamp1:
        return False
    if not timestamp2:
        return True
    try:
        dt1 = datetime.fromisoformat(timestamp1)
        dt2 = datetime.fromisoformat(timestamp2)
        return dt1 > dt2
    except Exception as e:
        print(f"Error comparing timestamps: {str(e)}")
        return False

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
batch_size = 15
images_processed = 0
entries_to_process = []

# First, collect all entries that need processing
for base_name in set(cache_files.keys()).union(set(main_files.keys())):
    cache_file = cache_files.get(base_name, "")
    main_file = main_files.get(base_name, "")
    
    if cache_file or main_file:  # Only include if at least one exists
        # Check if this file already exists in the index
        if base_name in existing_entries:
            # Use existing entry but update if cache or main file has changed
            entry = existing_entries[base_name]
            changed = False
            needs_category_update = False
            main_path = None
            
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
                            "orientation": resolution_info["orientation"],
                            "timestamp": get_file_timestamp(main_path)
                        })
                        needs_category_update = True
                changed = True
            elif not "timestamp" in entry and main_file:  # Add timestamp if missing
                main_path = os.path.join(main_dir, main_file)
                if os.path.isfile(main_path):
                    entry["timestamp"] = get_file_timestamp(main_path)
                    changed = True
            elif main_file:  # Update timestamp if file was modified
                main_path = os.path.join(main_dir, main_file)
                current_timestamp = get_file_timestamp(main_path)
                if is_newer_timestamp(current_timestamp, entry.get("timestamp", "")):
                    entry["timestamp"] = current_timestamp
                    needs_category_update = True
                    changed = True
            
            # Add category if missing or needs update
            if main_file and (not "category" in entry or needs_category_update):
                main_path = os.path.join(main_dir, main_file)
                if os.path.isfile(main_path):
                    entries_to_process.append((entry, main_path, base_name, "update"))
            
            if changed and not needs_category_update:
                updated_entries += 1
                print(f"Updated metadata for: {base_name}")
            
            if not needs_category_update:
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
                if os.path.isfile(main_path):
                    resolution_info = get_resolution_info(main_path)
                    entry.update({
                        "width": resolution_info["width"],
                        "height": resolution_info["height"],
                        "resolution": resolution_info["resolution"],
                        "orientation": resolution_info["orientation"],
                        "timestamp": get_file_timestamp(main_path)
                    })
                    entries_to_process.append((entry, main_path, base_name, "new"))
                else:
                    result.append(entry)
                    new_entries += 1
            elif cache_file:  # If no main file but cache file exists, get timestamp from cache
                cache_path = os.path.join(cache_dir, cache_file)
                if os.path.isfile(cache_path):
                    entry["timestamp"] = get_file_timestamp(cache_path)
                    entries_to_process.append((entry, cache_path, base_name, "new"))
                else:
                    result.append(entry)
                    new_entries += 1
            else:
                result.append(entry)
                new_entries += 1

# Process images in batches with pauses
print(f"Collected {len(entries_to_process)} entries that need image analysis")
batch_count = 0

for i, (entry, image_path, base_name, entry_type) in enumerate(entries_to_process):
    # Check if we need to pause after processing a batch
    if i > 0 and i % batch_size == 0:
        batch_count += 1
        print(f"\nCompleted batch {batch_count}. Processed {i}/{len(entries_to_process)} images.")
        print(f"Pausing for 60 seconds before the next batch...\n")
        time.sleep(60)  # Pause for 1 minute
    
    # Identify image category
    category = identify_image(image_path)
    entry["category"] = category
    
    # Add to result and update counters
    result.append(entry)
    if entry_type == "new":
        new_entries += 1
        print(f"New ({i+1}/{len(entries_to_process)}): {base_name} - {category}")
    else:
        updated_entries += 1
        print(f"Updated ({i+1}/{len(entries_to_process)}): {base_name} - {category}")

# Write to JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4)

print(f"\nIndex created successfully: {len(result)} total entries ({new_entries} new, {updated_entries} updated)")
