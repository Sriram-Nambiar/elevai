import json
import os
import sys
from jsonschema import validate, ValidationError

def run_validation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "data", "catalog", "schema.json")
    catalog_path = os.path.join(base_dir, "data", "catalog", "catalog.json")
    scenes_dir = os.path.join(base_dir, "data", "scenes")
    annotation_schema_path = os.path.join(scenes_dir, "annotation.schema.json")

    print("[*] Validating catalog schema...")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    try:
        validate(instance=catalog, schema=schema)
        print(f"[+] Catalog validated: {len(catalog['catalog_items'])} items found.")
    except ValidationError as e:
        print(f"[-] Catalog schema error: {e.message}")
        sys.exit(1)

    with open(annotation_schema_path, "r", encoding="utf-8") as f:
        annotation_schema = json.load(f)

    validated_scenes = 0
    for scene_name in sorted(os.listdir(scenes_dir)):
        scene_dir = os.path.join(scenes_dir, scene_name)
        if not os.path.isdir(scene_dir):
            continue

        gold_path = os.path.join(scene_dir, "gold_annotations.json")
        if not os.path.exists(gold_path):
            continue

        image_candidates = [
            os.path.join(scene_dir, "cabin_view.jpg"),
            os.path.join(scene_dir, "raw.jpg")
        ]
        assert any(os.path.isfile(path) for path in image_candidates), f"Missing cabin image in {scene_dir}"
        measurement_path = os.path.join(scene_dir, "site_measurements.json")
        assert os.path.isfile(measurement_path), f"Missing site_measurements.json in {scene_dir}"

        with open(gold_path, "r", encoding="utf-8") as f:
            annotations = json.load(f)
        validate(instance=annotations, schema=annotation_schema)

        for label in annotations["annotations"]:
            top, left, bottom, right = label["bbox_normalized"]
            assert top < bottom and left < right, f"Invalid box order in {scene_name}: {label}"

        print(
            f"[+] {scene_name}: {len(annotations['annotations'])} labels "
            f"({annotations['review_status']})."
        )
        validated_scenes += 1

    if validated_scenes == 0:
        raise AssertionError("No annotated scene datasets found.")

    print(f"\n[SUCCESS] Catalog and {validated_scenes} annotated scene dataset(s) passed structural checks.")

if __name__ == "__main__":
    run_validation()
