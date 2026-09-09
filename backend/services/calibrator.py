import os
import json
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import pipeline

torch.set_num_threads(os.cpu_count() or 4)

class CabinCalibrator:
    def __init__(self):
        print("[*] Initializing Depth Anything V2 (Small) on CPU...")
        self.depth_pipe = pipeline(
            task="depth-estimation",
            model="depth-anything/Depth-Anything-V2-Small-hf",
            device=-1
        )

    def generate_depth_map(self, image_path: str, output_path: str) -> np.ndarray:
        raw_image = Image.open(image_path).convert("RGB")
        result = self.depth_pipe(raw_image)
        depth_pil = result["depth"]
        
        # Convert depth map to normalized float [0.0 (near) to 1.0 (far)]
        depth_np = np.array(depth_pil).astype(np.float32)
        depth_norm = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min() + 1e-8)
        
        # Save false-color depth visualization
        depth_colormap = cv2.applyColorMap((depth_norm * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
        cv2.imwrite(output_path, depth_colormap)
        return depth_norm

    def calibrate_scene(self, scene_dir: str):
        image_path = os.path.join(scene_dir, "raw.jpg")
        measurements_path = os.path.join(scene_dir, "site_measurements.json")
        detections_path = os.path.join(scene_dir, "masks", "detected_components.json")
        output_depth_path = os.path.join(scene_dir, "depth_map.png")
        output_calib_path = os.path.join(scene_dir, "calibrated_scene.json")

        assert os.path.exists(measurements_path), f"Missing {measurements_path}"
        assert os.path.exists(detections_path), f"Run Phase 2 segmentation first: missing {detections_path}"

        with open(measurements_path, "r", encoding="utf-8") as f:
            site_data = json.load(f)

        with open(detections_path, "r", encoding="utf-8") as f:
            detected_data = json.load(f)

        # 1. Generate dense depth map
        depth_norm = self.generate_depth_map(image_path, output_depth_path)
        img = cv2.imread(image_path)
        img_h, img_w, _ = img.shape

        known_cabin_height_mm = site_data["cabin_dimensions_mm"]["height"]

        # 2. Locate rear wall bounding box to establish reference metric plane
        back_wall = next(
            (c for c in detected_data["components"] if c["category"] == "wall_panel"),
            None
        )
        
        # Fallback to full vertical span if no back wall is segmented
        if back_wall:
            bw_ymin, _, bw_ymax, _ = back_wall["bbox_pixel"]
            reference_height_px = max(1, bw_ymax - bw_ymin)
            ref_depth = float(np.median(depth_norm[bw_ymin:bw_ymax, :]))
        else:
            reference_height_px = int(img_h * 0.75)
            ref_depth = 0.5

        # Millimeters per pixel at the reference depth plane
        base_mm_per_px = known_cabin_height_mm / reference_height_px

        calibrated_components = []
        for comp in detected_data["components"]:
            ymin, xmin, ymax, xmax = comp["bbox_pixel"]
            h_px = ymax - ymin
            w_px = xmax - xmin

            # Sample local depth for this component
            comp_depth = float(np.median(depth_norm[ymin:ymax, xmin:xmax]))

            # Adjust scale according to perspective depth delta
            # Higher depth values = further away (requires larger mm/px scaling)
            depth_scale_ratio = (comp_depth / ref_depth) if ref_depth > 0 else 1.0
            effective_mm_per_px = base_mm_per_px * (0.85 + 0.3 * depth_scale_ratio)

            est_height_mm = round(h_px * effective_mm_per_px, 1)
            est_width_mm = round(w_px * effective_mm_per_px, 1)

            calibrated_components.append({
                "component_id": comp["component_id"],
                "category": comp["category"],
                "confidence": comp["confidence"],
                "median_depth": round(comp_depth, 3),
                "dimensions_px": {"height": h_px, "width": w_px},
                "estimated_dimensions_mm": {
                    "height": est_height_mm,
                    "width": est_width_mm
                }
            })

        # 3. Calculate COP tolerance error against site measurements (Deliverable 2 benchmark)
        cop_comp = next((c for c in calibrated_components if c["category"] == "car_operating_panel"), None)
        fit_error_analysis = {}
        if cop_comp and "existing_cop" in site_data:
            ground_truth_h = site_data["existing_cop"]["panel_height_mm"]
            ground_truth_w = site_data["existing_cop"]["panel_width_mm"]
            est_h = cop_comp["estimated_dimensions_mm"]["height"]
            est_w = cop_comp["estimated_dimensions_mm"]["width"]

            err_h_pct = round(abs(est_h - ground_truth_h) / ground_truth_h * 100, 2)
            err_w_pct = round(abs(est_w - ground_truth_w) / ground_truth_w * 100, 2)

            fit_error_analysis = {
                "evaluated_component": "car_operating_panel",
                "ground_truth_mm": {"height": ground_truth_h, "width": ground_truth_w},
                "estimated_mm": {"height": est_h, "width": est_w},
                "error_percentage": {
                    "height_error_pct": err_h_pct,
                    "width_error_pct": err_w_pct,
                    "mean_error_pct": round((err_h_pct + err_w_pct) / 2, 2)
                },
                "tolerance_status": "PASS" if (err_h_pct + err_w_pct) / 2 <= 12.0 else "REVIEW"
            }

        calibrated_payload = {
            "scene_id": site_data["scene_id"],
            "camera_calibration": {
                "reference_depth": round(ref_depth, 3),
                "base_mm_per_pixel": round(base_mm_per_px, 4)
            },
            "calibrated_components": calibrated_components,
            "fit_error_analysis": fit_error_analysis
        }

        with open(output_calib_path, "w", encoding="utf-8") as f:
            json.dump(calibrated_payload, f, indent=2)

        print(f"[+] Calibration complete. Output saved to: {output_calib_path}")
        print(f"[+] Depth visualization saved to: {output_depth_path}")
        if fit_error_analysis:
            print(f"[+] Mean Fit Error: {fit_error_analysis['error_percentage']['mean_error_pct']}% -> Status: {fit_error_analysis['tolerance_status']}")

        return calibrated_payload