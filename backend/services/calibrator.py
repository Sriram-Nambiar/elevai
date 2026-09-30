import json
import os
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import pipeline


torch.set_num_threads(os.cpu_count() or 4)


class CabinCalibrator:
    """Create image-space and relative-depth diagnostics without inventing metric scale."""

    def __init__(self):
        self.depth_pipe = None

    def _depth_estimator(self):
        if self.depth_pipe is None:
            self.depth_pipe = pipeline(
                task="depth-estimation",
                model="depth-anything/Depth-Anything-V2-Small-hf",
                device=-1
            )
        return self.depth_pipe

    def generate_depth_map(self, image_path: str, output_path: str) -> np.ndarray:
        image = Image.open(image_path).convert("RGB")
        result = self._depth_estimator()(image)
        depth = np.asarray(result["depth"], dtype=np.float32)
        depth_range = float(depth.max() - depth.min())
        normalized = (depth - depth.min()) / (depth_range if depth_range > 1e-8 else 1.0)
        color_map = cv2.applyColorMap((normalized * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
        cv2.imwrite(output_path, color_map)
        return normalized

    @staticmethod
    def _find_image(scene_dir: Path) -> Path:
        for filename in ("cabin_view.jpg", "raw.jpg", "cabin_view.png", "raw.png"):
            candidate = scene_dir / filename
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(f"No cabin image found in {scene_dir}")

    def calibrate_scene(self, scene_dir: str) -> Dict[str, Any]:
        scene_path = Path(scene_dir)
        image_path = self._find_image(scene_path)
        measurements_path = scene_path / "site_measurements.json"
        detections_path = scene_path / "masks" / "detected_components.json"

        if not measurements_path.is_file():
            raise FileNotFoundError(f"Missing site measurements: {measurements_path}")
        if not detections_path.is_file():
            raise FileNotFoundError(f"Run component detection first: {detections_path}")

        with measurements_path.open("r", encoding="utf-8") as stream:
            measurements = json.load(stream)
        with detections_path.open("r", encoding="utf-8") as stream:
            detections = json.load(stream).get("components", [])

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read cabin image: {image_path}")
        image_height, image_width = image.shape[:2]

        depth = self.generate_depth_map(
            str(image_path), str(scene_path / "depth_map.png")
        )
        depth_height, depth_width = depth.shape[:2]
        components = []
        for detection in detections:
            box = detection.get("bbox_pixel")
            if not isinstance(box, list) or len(box) != 4:
                continue
            top, left, bottom, right = [int(value) for value in box]
            top = max(0, min(image_height, top))
            bottom = max(0, min(image_height, bottom))
            left = max(0, min(image_width, left))
            right = max(0, min(image_width, right))
            if bottom <= top or right <= left:
                continue

            # Depth is resized to its own output resolution before sampling.
            d_top = max(0, min(depth_height, round(top * depth_height / image_height)))
            d_bottom = max(d_top + 1, min(depth_height, round(bottom * depth_height / image_height)))
            d_left = max(0, min(depth_width, round(left * depth_width / image_width)))
            d_right = max(d_left + 1, min(depth_width, round(right * depth_width / image_width)))
            region = depth[d_top:d_bottom, d_left:d_right]

            components.append({
                "component_id": detection.get("component_id"),
                "category": detection.get("category"),
                "confidence": detection.get("confidence"),
                "bbox_pixel": [top, left, bottom, right],
                "bbox_normalized": [
                    round(top / image_height, 5),
                    round(left / image_width, 5),
                    round(bottom / image_height, 5),
                    round(right / image_width, 5),
                ],
                "dimensions_px": {"height": bottom - top, "width": right - left},
                "relative_depth": round(float(np.median(region)), 4) if region.size else None,
            })

        cabin_dimensions = measurements.get("cabin_dimensions_mm")
        known_site_dimensions = (
            isinstance(cabin_dimensions, dict)
            and all(isinstance(cabin_dimensions.get(axis), (int, float)) and cabin_dimensions[axis] > 0
                    for axis in ("width", "depth", "height"))
        )
        unknowns = [] if known_site_dimensions else ["Measured cabin width, depth, and height are required."]
        if not any(
            item.get("category") == "car_operating_panel"
            and item.get("dimensions_mm")
            for item in measurements.get("component_measurements", [])
        ):
            unknowns.append("A measured component dimension and camera reference are required for image-to-metric calibration.")

        result = {
            "scene_id": measurements.get("scene_id", scene_path.name),
            "image": {"file": image_path.name, "width_px": image_width, "height_px": image_height},
            "calibration_status": "RELATIVE_DEPTH_ONLY",
            "metric_scale_available": False,
            "relative_depth_model": "Depth Anything V2 Small",
            "components": components,
            "unknowns": unknowns,
            "limitations": [
                "Monocular depth is relative and does not provide millimetres or camera calibration.",
                "Pixel boxes and depth summaries are visual aids; do not use them alone for product fit decisions.",
                "Dimensional fit decisions use manually entered site measurements and catalog rules."
            ],
        }
        output_path = scene_path / "calibrated_scene.json"
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
