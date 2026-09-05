import os
import json
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import pipeline

class CabinSegmenter:
    def __init__(self, device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[*] Initializing zero-shot detector on device: {self.device}")
        # Using Owl-ViT / OWLv2 for open-vocabulary cabin component detection
        self.detector = pipeline(
            model="google/owlv2-base-patch16-ensemble",
            task="zero-shot-object-detection",
            device=0 if self.device == "cuda" else -1
        )

    def segment_cabin(self, image_path: str, output_mask_dir: str):
        os.makedirs(output_mask_dir, exist_ok=True)
        image = Image.open(image_path).convert("RGB")
        img_w, img_h = image.size

        # Target prompts aligned with the catalog categories
        candidate_labels = [
            "elevator car operating panel push buttons",
            "elevator back wall panel",
            "elevator ceiling lighting",
            "elevator floor"
        ]

        print(f"[*] Running detection on: {image_path}")
        predictions = self.detector(
            image,
            candidate_labels=candidate_labels,
            threshold=0.12
        )

        label_map = {
            "elevator car operating panel push buttons": "cop",
            "elevator back wall panel": "wall_panel",
            "elevator ceiling lighting": "ceiling",
            "elevator floor": "floor"
        }

        detected_components = []
        overlay = cv2.imread(image_path)

        for idx, pred in enumerate(predictions):
            box = pred["box"]
            raw_label = pred["label"]
            score = pred["score"]
            standard_label = label_map.get(raw_label, "unknown")

            xmin, ymin, xmax, ymax = (
                int(box["xmin"]),
                int(box["ymin"]),
                int(box["xmax"]),
                int(box["ymax"])
            )

            # Generate individual binary mask
            mask = np.zeros((img_h, img_w), dtype=np.uint8)
            mask[ymin:ymax, xmin:xmax] = 255

            mask_filename = f"mask_{standard_label}_{idx}.png"
            mask_path = os.path.join(output_mask_dir, mask_filename)
            cv2.imwrite(mask_path, mask)

            # Draw visual feedback overlay
            cv2.rectangle(overlay, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            cv2.putText(
                overlay,
                f"{standard_label} ({score:.2f})",
                (xmin, max(20, ymin - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

            detected_components.append({
                "component_id": f"{standard_label}_{idx}",
                "category": standard_label,
                "confidence": round(score, 3),
                "bbox_pixel": [ymin, xmin, ymax, xmax],
                "bbox_normalized": [
                    round(ymin / img_h, 4),
                    round(xmin / img_w, 4),
                    round(ymax / img_h, 4),
                    round(xmax / img_w, 4)
                ],
                "mask_file": mask_filename
            })

        # Save annotated overlay and detection metadata
        overlay_path = os.path.join(output_mask_dir, "segmentation_preview.jpg")
        cv2.imwrite(overlay_path, overlay)

        metadata_path = os.path.join(output_mask_dir, "detected_components.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump({"components": detected_components}, f, indent=2)

        print(f"[+] Segmentation complete: {len(detected_components)} elements identified.")
        print(f"[+] Preview saved to: {overlay_path}")
        return detected_components
