import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
from services.calibrator import CabinCalibrator

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scene_dir = os.path.join(base_dir, "data", "scenes", "scene_01_passenger")

    calibrator = CabinCalibrator()
    calibrator.calibrate_scene(scene_dir=scene_dir)

if __name__ == "__main__":
    main()