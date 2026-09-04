import json
import os
import sys
from jsonschema import validate, ValidationError

def run_validation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "data", "catalog", "schema.json")
    catalog_path = os.path.join(base_dir, "data", "catalog", "catalog.json")
    scene_dir = os.path.join(base_dir, "data", "scenes", "scene_01_passenger")

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

    print("[*] Validating scene_01_passenger dataset...")
    raw_img = os.path.join(scene_dir, "raw.jpg")
    measurements = os.path.join(scene_dir, "site_measurements.json")
    gold = os.path.join(scene_dir, "gold_annotations.json")

    assert os.path.exists(raw_img), f"Missing raw.jpg in {scene_dir}"
    assert os.path.exists(measurements), f"Missing site_measurements.json in {scene_dir}"
    assert os.path.exists(gold), f"Missing gold_annotations.json in {scene_dir}"

    with open(measurements, "r", encoding="utf-8") as f:
        m_data = json.load(f)
        assert "cabin_dimensions_mm" in m_data, "cabin_dimensions_mm missing in site_measurements.json"

    with open(gold, "r", encoding="utf-8") as f:
        g_data = json.load(f)
        assert "annotations" in g_data, "annotations missing in gold_annotations.json"

    print(f"[+] scene_01_passenger verified with {len(g_data['annotations'])} ground-truth labels.")
    print("\n[SUCCESS] Phase 1 setup complete and fully validated.")

if __name__ == "__main__":
    run_validation()
