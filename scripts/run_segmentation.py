import os
import sys

# Ensure backend directory is in Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
from services.segmenter import CabinSegmenter

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(base_dir, "data", "scenes", "scene_01_passenger", "raw.jpg")
    output_dir = os.path.join(base_dir, "data", "scenes", "scene_01_passenger", "masks")

    if not os.path.exists(image_path):
        print(f"[-] Image not found: {image_path}")
        return

    segmenter = CabinSegmenter()
    segmenter.segment_cabin(image_path=image_path, output_mask_dir=output_dir)

if __name__ == "__main__":
    main()
