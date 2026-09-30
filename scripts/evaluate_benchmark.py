"""Generate a transparent benchmark report from scenes marked as verified."""

import json
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from services.rules_engine import RulesEngine
from services.segmenter import CabinSegmenter


DETECTION_CATEGORY_MAP = {
    "wall_panel": "wall_panel",
    "cop": "car_operating_panel",
    "ceiling": "ceiling_lighting",
    "floor": "flooring",
    "doors": "doors",
    "display_unit": "display_unit",
}


def box_iou(first, second):
    top = max(first[0], second[0])
    left = max(first[1], second[1])
    bottom = min(first[2], second[2])
    right = min(first[3], second[3])
    intersection = max(0.0, bottom - top) * max(0.0, right - left)
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union else 0.0


def match_boxes(predictions, annotations, threshold=0.5):
    pairs = sorted(
        [
            (
            box_iou(prediction["bbox_normalized"], annotation["bbox_normalized"]),
            prediction_index,
            annotation_index,
            )
            for prediction_index, prediction in enumerate(predictions)
            for annotation_index, annotation in enumerate(annotations)
            if prediction["category"] == annotation["category"]
        ],
        reverse=True,
    )

    used_predictions = set()
    used_annotations = set()
    matched_ious = []
    for iou, prediction_index, annotation_index in pairs:
        if iou < threshold:
            continue
        if prediction_index in used_predictions or annotation_index in used_annotations:
            continue
        used_predictions.add(prediction_index)
        used_annotations.add(annotation_index)
        matched_ious.append(iou)

    return len(used_predictions), len(predictions) - len(used_predictions), len(annotations) - len(used_annotations), matched_ious


def main():
    scenes_root = os.path.join(BASE_DIR, "data", "scenes")
    segmenter = CabinSegmenter()
    rules_engine = RulesEngine()
    results = []
    totals = {"true_positive": 0, "false_positive": 0, "false_negative": 0}
    all_ious = []
    rule_violation_count = 0

    for scene_name in sorted(os.listdir(scenes_root)):
        scene_dir = os.path.join(scenes_root, scene_name)
        annotation_path = os.path.join(scene_dir, "gold_annotations.json")
        measurement_path = os.path.join(scene_dir, "site_measurements.json")
        if not os.path.isfile(annotation_path) or not os.path.isfile(measurement_path):
            continue

        with open(annotation_path, "r", encoding="utf-8") as stream:
            gold = json.load(stream)
        if gold.get("review_status") != "verified":
            continue

        with open(measurement_path, "r", encoding="utf-8") as stream:
            measurements = json.load(stream)

        detections = segmenter.segment_scene(scene_dir)
        predictions = []
        for detection in detections:
            category = DETECTION_CATEGORY_MAP.get(detection.get("category"))
            box = detection.get("bbox_normalized")
            if category and isinstance(box, list) and len(box) == 4:
                predictions.append({"category": category, "bbox_normalized": box})

        annotations = [
            {"category": ann["category_id"], "bbox_normalized": ann["bbox_normalized"]}
            for ann in gold.get("annotations", [])
        ]
        tp, fp, fn, ious = match_boxes(predictions, annotations)
        totals["true_positive"] += tp
        totals["false_positive"] += fp
        totals["false_negative"] += fn
        all_ious.extend(ious)

        default_skus = []
        for category in ("wall_panel", "flooring", "car_operating_panel", "ceiling_lighting"):
            candidate = next(
                (item for item in rules_engine.catalog.values() if item.get("category") == category),
                None,
            )
            if candidate:
                default_skus.append(candidate.get("sku_id"))
        fit_result = rules_engine.evaluate_configuration(measurements, default_skus)
        rule_violation_count += len(fit_result.get("violations", []))

        results.append({
            "scene_id": scene_name,
            "annotation_count": len(annotations),
            "prediction_count": len(predictions),
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "mean_matched_box_iou": round(sum(ious) / len(ious), 4) if ious else None,
            "fit_rule_status": fit_result.get("overall_status"),
            "fit_rule_violations": len(fit_result.get("violations", [])),
            "fit_rule_unknowns": fit_result.get("missing_information", []),
        })

    tp = totals["true_positive"]
    fp = totals["false_positive"]
    fn = totals["false_negative"]
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and precision + recall else None
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "thresholds": {"same_category_box_iou": 0.5},
        "verified_scenes_evaluated": len(results),
        "component_detection": {
            **totals,
            "precision": round(precision, 4) if precision is not None else None,
            "recall": round(recall, 4) if recall is not None else None,
            "f1": round(f1, 4) if f1 is not None else None,
            "mean_matched_box_iou": round(sum(all_ious) / len(all_ious), 4) if all_ious else None,
        },
        "fit_error_mm": None,
        "fit_error_note": "Requires independently measured component geometry and camera/plane calibration; relative monocular depth is not metric ground truth.",
        "fit_rule_violations": rule_violation_count,
        "human_study_required": {
            "render_perceptual_realism": "Not measured by this script; conduct a blinded human rating study.",
            "proposal_factual_error_rate": "Not measured by this script; compare every proposal claim with its source catalog/site record.",
            "time_saved_vs_manual_minutes": "Not measured by this script; time matched manual and tool-assisted tasks with the same participants.",
        },
        "scenes": results,
    }

    report_dir = os.path.join(BASE_DIR, "data", "evaluation")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(f"Wrote {report_path}")
    print(f"Verified scenes evaluated: {len(results)}")


if __name__ == "__main__":
    main()
