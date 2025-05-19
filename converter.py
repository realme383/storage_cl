import os
from PIL import Image, UnidentifiedImageError

# Set your folder path
folder_path = "C:/Users/Ayan/Pictures/up"  # Change this if your images are in a different folder

# Create output folder
output_folder = os.path.join(folder_path, "converted_pngs")
os.makedirs(output_folder, exist_ok=True)

# Supported input formats
supported_extensions = [".jfif", ".gif"]

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    ext = os.path.splitext(filename)[1].lower()
    if ext in supported_extensions:
        input_path = os.path.join(folder_path, filename)
        output_filename = os.path.splitext(filename)[0] + ".png"
        output_path = os.path.join(output_folder, output_filename)

        try:
            with Image.open(input_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                img.save(output_path, "PNG")
                print(f"Converted: {filename} -> {output_filename}")
        except UnidentifiedImageError:
            print(f"Cannot identify image file: {filename}")
        except Exception as e:
            print(f"Failed to convert {filename}: {e}")
