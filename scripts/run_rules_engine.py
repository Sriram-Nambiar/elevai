import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
from services.rules_engine import RulesEngine

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    measurements_path = os.path.join(base_dir, "data", "scenes", "scene_01_passenger", "site_measurements.json")

    with open(measurements_path, "r", encoding="utf-8") as f:
        site_data = json.load(f)

    c_w = site_data["cabin_dimensions_mm"]["width"]
    c_d = site_data["cabin_dimensions_mm"]["depth"]

    engine = RulesEngine()

    # Index SKUs by category
    catalog_by_cat = {}
    for sku_id, item in engine.catalog.items():
        cat = item.get("category")
        catalog_by_cat.setdefault(cat, []).append(item)

    # Pick a ceiling fixture whose dimensions fit within the cabin frame
    fitting_ceiling = None
    for item in catalog_by_cat.get("ceiling_lighting", []):
        dims = item.get("dimensions_mm", {})
        w = dims.get("width", 0)
        l = dims.get("length", dims.get("depth", 0))
        if w <= c_w and l <= c_d:
            fitting_ceiling = item.get("sku_id")
            break

    # Fallback to the first ceiling SKU if no perfect dimensional match is flagged
    if not fitting_ceiling and catalog_by_cat.get("ceiling_lighting"):
        fitting_ceiling = catalog_by_cat["ceiling_lighting"][0].get("sku_id")

    compliant_package = [
        catalog_by_cat["wall_panel"][0]["sku_id"],
        catalog_by_cat["flooring"][0]["sku_id"],
        catalog_by_cat["car_operating_panel"][0]["sku_id"],
        fitting_ceiling
    ]
    compliant_package = [sku for sku in compliant_package if sku]

    print("=========================================================")
    print("  TEST 1: Evaluating Compliant Modernization Package     ")
    print("=========================================================")
    print(f"Selected SKUs: {compliant_package}\n")
    res1 = engine.evaluate_configuration(site_data, compliant_package)
    cost1 = res1.get("total_estimated_cost_inr", 0.0)

    print(f"Status: {res1['overall_status']}")
    print(f"Violations ({len(res1['violations'])}): {res1['violations']}")
    print(f"Warnings ({len(res1['warnings'])}): {res1['warnings']}")
    print(f"Total Cost: INR {cost1:,.2f}")
    print("\nItemized Bill of Materials (BOM):")
    for item in res1["bill_of_materials"]:
        unit_price = item.get("unit_cost_inr", 0.0)
        ext_cost = item.get("extended_cost_inr", 0.0)
        print(f" - [{item['sku_id']}] {item['name']}: {item['quantity']} units @ INR {unit_price:,.2f} = INR {ext_cost:,.2f} (Status: {item['status']})")

    print("\n=========================================================")
    print("  TEST 2: Evaluating Non-Compliant Package (Violations)   ")
    print("=========================================================")
    invalid_package = [compliant_package[0], "UNKNOWN-SKU-999"]
    site_strict = json.loads(json.dumps(site_data))
    site_strict["max_allowable_flooring_thickness_mm"] = 1

    if "flooring" in catalog_by_cat:
        invalid_package.append(catalog_by_cat["flooring"][0]["sku_id"])

    res2 = engine.evaluate_configuration(site_strict, invalid_package)
    cost2 = res2.get("total_estimated_cost_inr", 0.0)

    print(f"Status: {res2['overall_status']}")
    print(f"Violations ({len(res2['violations'])}):")
    for v in res2["violations"]:
        print(f"   [X] {v}")
    print(f"Total Cost: INR {cost2:,.2f}")

if __name__ == "__main__":
    main()