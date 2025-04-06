import os
import json
from pathlib import Path

# Define directories
cache_dir = r"C:\Users\Ayan\Documents\GitHub\storage\cache"
main_dir = r"C:\Users\Ayan\Documents\GitHub\storage\main"
output_file = r"C:\Users\Ayan\Documents\GitHub\storage\index.json"

# Function to get files without extension
def get_file_without_extension(filename):
    return os.path.splitext(filename)[0]

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
        result.append({
            "file_name": base_name,
            "file_cache_name": cache_file,
            "file_main_name": main_file
        })

# Write to JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4)

print(f"Index created successfully with {len(result)} entries at {output_file}")
