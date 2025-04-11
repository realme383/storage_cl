import os
import shutil
from PIL import Image
from PIL import ImageFile
from concurrent.futures import ThreadPoolExecutor
import warnings
import math

# Suppress DecompressionBombWarning and increase image size limit
warnings.simplefilter('ignore', Image.DecompressionBombWarning)
Image.MAX_IMAGE_PIXELS = None

# Define source and destination directories
source_dir = r"C:\Users\Ayan\Pictures\up\upscayl_png_high-fidelity-4x_4x"
destination_dir = r"D:\storage\cache"
main_dir = r"D:\storage\main"

# Ensure destination directories exist
os.makedirs(destination_dir, exist_ok=True)
os.makedirs(main_dir, exist_ok=True)

def compress_image(filename):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):  # Check for image files
        source_path = os.path.join(source_dir, filename)
        destination_path = os.path.join(destination_dir, os.path.splitext(filename)[0] + ".webp")
        main_path = os.path.join(main_dir, filename)
        
        # Copy original file to main directory
        try:
            shutil.copy2(source_path, main_path)
            print(f"Copied original: {filename} to {main_dir}")
        except Exception as e:
            print(f"Error copying original file {filename}: {e}")
        
        # Get original file size in KB
        original_size = os.path.getsize(source_path) / 1024
        
        try:
            # Open the image
            with Image.open(source_path) as img:
                # Get original dimensions
                width, height = img.size
                
                # Resize if image is too large (max width or height of 1920px)
                max_dimension = 1920
                if width > max_dimension or height > max_dimension:
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        new_width = max_dimension
                        new_height = math.floor(height * (max_dimension / width))
                    else:
                        new_height = max_dimension
                        new_width = math.floor(width * (max_dimension / height))
                    
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Save with different settings based on file size
                if original_size > 1000:  # For large files (>1MB)
                    img.save(destination_path, "WEBP", quality=10, method=6)
                elif original_size > 500:  # For medium files (>500KB)
                    img.save(destination_path, "WEBP", quality=20, method=6)
                else:  # For smaller files
                    img.save(destination_path, "WEBP", quality=30, method=6)
                
                # Calculate compression ratio
                new_size = os.path.getsize(destination_path) / 1024
                compression_ratio = (1 - (new_size / original_size)) * 100
                
                print(f"{filename}: {original_size:.2f}KB → {new_size:.2f}KB ({compression_ratio:.2f}% reduction)")
        
        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("Starting image optimization...")

# Use ThreadPoolExecutor to process images with 8 threads
with ThreadPoolExecutor(max_workers=6) as executor:
    executor.map(compress_image, os.listdir(source_dir))

print("Image compression and conversion completed.")
