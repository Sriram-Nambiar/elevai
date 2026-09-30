import json
import math
import os
from typing import Any, Dict, List, Optional


# Demonstration fit allowance for field-trimmable ceiling products. This is a
# prototype rule, not a manufacturer-approved installation tolerance.
CEILING_FIELD_TRIM_TOLERANCE_MM = 200


class RulesEngine:
    def __init__(self, catalog_path: str = None):
        if catalog_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            catalog_path = os.path.join(base_dir, "data", "catalog", "catalog.json")

        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        items = catalog_data.get("catalog_items", []) if isinstance(catalog_data, dict) else catalog_data
        self.catalog = {
            item.get("sku_id") or item.get("sku") or item.get("id"): item
            for item in items
            if item.get("sku_id") or item.get("sku") or item.get("id")
        }

    @staticmethod
    def _positive_number(value: Any) -> Optional[float]:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if not math.isfinite(value) or value <= 0:
            return None
        return float(value)

    def evaluate_configuration(
        self,
        site_measurements: Dict[str, Any],
        selected_skus: List[str]
    ) -> Dict[str, Any]:
        site_measurements = site_measurements if isinstance(site_measurements, dict) else {}
        raw_cabin_dims = site_measurements.get("cabin_dimensions_mm")
        cabin_dims = raw_cabin_dims if isinstance(raw_cabin_dims, dict) else {}
        cabin = {
            key: self._positive_number(cabin_dims.get(key))
            for key in ("width", "depth", "height")
        }
        max_floor_thickness = self._positive_number(
            site_measurements.get("max_allowable_flooring_thickness_mm")
        )
        existing_cop = site_measurements.get("existing_cop")
        existing_cop = existing_cop if isinstance(existing_cop, dict) else {}
        cop_mount_height = self._positive_number(
            existing_cop.get("mounting_height_from_floor_mm")
        )

        violations: List[str] = []
        warnings: List[str] = []
        missing_information: List[str] = []
        bom_items: List[Dict[str, Any]] = []
        total_cost = 0.0
        total_cost_complete = True

        def require(value: Optional[float], name: str, item_missing: List[str]) -> bool:
            if value is None:
                item_missing.append(name)
                if name not in missing_information:
                    missing_information.append(name)
                return False
            return True

        for sku in selected_skus:
            if sku not in self.catalog:
                violations.append(f"Unknown SKU '{sku}' is not in the bounded catalog.")
                continue

            item = self.catalog[sku]
            category = item.get("category", "unknown")
            dims = item.get("dimensions_mm") or {}
            constraints = item.get("mounting_constraints") or {}
            name = item.get("name", sku)
            unit_cost = self._positive_number(item.get("unit_cost_inr"))
            item_violations: List[str] = []
            item_missing: List[str] = []
            quantity: Optional[int] = None

            if category == "wall_panel":
                panel_h = self._positive_number(dims.get("height"))
                panel_w = self._positive_number(dims.get("width"))
                valid = all([
                    require(cabin["height"], "cabin_dimensions_mm.height", item_missing),
                    require(cabin["width"], "cabin_dimensions_mm.width", item_missing),
                    require(cabin["depth"], "cabin_dimensions_mm.depth", item_missing),
                    require(panel_h, f"catalog.{sku}.dimensions_mm.height", item_missing),
                    require(panel_w, f"catalog.{sku}.dimensions_mm.width", item_missing),
                ])
                if valid:
                    if panel_h > cabin["height"]:
                        item_violations.append(
                            f"Panel height {panel_h:g} mm exceeds cabin height {cabin['height']:g} mm."
                        )
                    elif cabin["height"] - panel_h > 200:
                        warnings.append(
                            f"{sku}: panel leaves {cabin['height'] - panel_h:g} mm above; verify the finishing detail."
                        )
                    quantity = math.ceil(cabin["width"] / panel_w) + 2 * math.ceil(cabin["depth"] / panel_w)

            elif category == "flooring":
                thickness = self._positive_number(
                    dims.get("thickness_mm") or dims.get("thickness")
                )
                pack_width = self._positive_number(dims.get("width_mm") or dims.get("width"))
                pack_depth = self._positive_number(
                    dims.get("length_mm") or dims.get("length") or dims.get("depth")
                )
                valid = all([
                    require(cabin["width"], "cabin_dimensions_mm.width", item_missing),
                    require(cabin["depth"], "cabin_dimensions_mm.depth", item_missing),
                    require(max_floor_thickness, "max_allowable_flooring_thickness_mm", item_missing),
                    require(thickness, f"catalog.{sku}.dimensions_mm.thickness_mm", item_missing),
                    require(pack_width, f"catalog.{sku}.dimensions_mm.width", item_missing),
                    require(pack_depth, f"catalog.{sku}.dimensions_mm.depth", item_missing),
                ])
                if valid:
                    if thickness > max_floor_thickness:
                        item_violations.append(
                            f"Floor thickness {thickness:g} mm exceeds measured sill allowance {max_floor_thickness:g} mm."
                        )
                    cabin_area = cabin["width"] * cabin["depth"]
                    pack_area = pack_width * pack_depth
                    quantity = math.ceil(cabin_area / pack_area)

            elif category == "car_operating_panel":
                panel_h = self._positive_number(dims.get("height"))
                valid = all([
                    require(cabin["height"], "cabin_dimensions_mm.height", item_missing),
                    require(cop_mount_height, "existing_cop.mounting_height_from_floor_mm", item_missing),
                    require(panel_h, f"catalog.{sku}.dimensions_mm.height", item_missing),
                ])
                if valid:
                    reach_limit = self._positive_number(constraints.get("interactive_reach_max_mm"))
                    if reach_limit is None:
                        require(None, f"catalog.{sku}.mounting_constraints.interactive_reach_max_mm", item_missing)
                        valid = False
                    else:
                        if cop_mount_height > reach_limit:
                            item_violations.append(
                                f"Existing control mounting baseline {cop_mount_height:g} mm exceeds the catalog reach limit {reach_limit:g} mm."
                            )
                        if panel_h > cabin["height"]:
                            item_violations.append(
                                f"Panel height {panel_h:g} mm exceeds cabin height {cabin['height']:g} mm."
                        )
                if valid:
                    quantity = 1

            elif category == "ceiling_lighting":
                product_w = self._positive_number(dims.get("width"))
                product_d = self._positive_number(dims.get("depth") or dims.get("length"))
                valid = all([
                    require(cabin["width"], "cabin_dimensions_mm.width", item_missing),
                    require(cabin["depth"], "cabin_dimensions_mm.depth", item_missing),
                    require(product_w, f"catalog.{sku}.dimensions_mm.width", item_missing),
                    require(product_d, f"catalog.{sku}.dimensions_mm.depth", item_missing),
                ])
                if valid:
                    oversize_w = max(0.0, product_w - cabin["width"])
                    oversize_d = max(0.0, product_d - cabin["depth"])
                    if oversize_w > CEILING_FIELD_TRIM_TOLERANCE_MM or oversize_d > CEILING_FIELD_TRIM_TOLERANCE_MM:
                        item_violations.append(
                            f"Ceiling exceeds the demonstration field-trim allowance ({CEILING_FIELD_TRIM_TOLERANCE_MM} mm). Confirm final fit with the manufacturer."
                        )
                    elif oversize_w or oversize_d:
                        warnings.append(
                            f"{sku}: field trimming up to {max(oversize_w, oversize_d):g} mm per axis would be required; confirm with the manufacturer."
                        )
                    quantity = 1

            elif category == "doors":
                opening_width = self._positive_number(site_measurements.get("door_opening_width_mm"))
                door_h = self._positive_number(dims.get("height"))
                door_w = self._positive_number(dims.get("width"))
                valid = all([
                    require(opening_width, "door_opening_width_mm", item_missing),
                    require(cabin["height"], "cabin_dimensions_mm.height", item_missing),
                    require(door_h, f"catalog.{sku}.dimensions_mm.height", item_missing),
                    require(door_w, f"catalog.{sku}.dimensions_mm.width", item_missing),
                ])
                if valid:
                    if door_h > cabin["height"] or door_w * 2 < opening_width:
                        item_violations.append(
                            "Door-skin dimensions do not cover the measured opening; verify leaf geometry and clearances."
                        )
                    quantity = 1

            else:
                item_missing.append(f"No fit rule is defined for catalog category '{category}'.")
                if item_missing[-1] not in missing_information:
                    missing_information.append(item_missing[-1])

            if item_violations:
                violations.extend(f"{sku}: {message}" for message in item_violations)

            if quantity is None or unit_cost is None:
                extended_cost = None
                total_cost_complete = False
            else:
                extended_cost = round(quantity * unit_cost, 2)
                total_cost += extended_cost

            status = "FAIL" if item_violations else ("REVIEW" if item_missing else "PASS")
            bom_items.append({
                "sku_id": sku,
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit_cost_inr": unit_cost,
                "extended_cost_inr": extended_cost,
                "status": status,
                "fit_reasons": item_violations,
                "missing_information": item_missing,
            })

        if not selected_skus:
            missing_information.append("Select at least one catalog item.")

        if violations:
            overall_status = "REJECTED"
        elif missing_information:
            overall_status = "REVIEW_REQUIRED"
        else:
            overall_status = "GEOMETRY_CHECKS_PASSED"

        warnings.append(
            "Prototype dimensional screening only; this result is not a code certification or installation approval."
        )
        return {
            "is_compliant": overall_status == "GEOMETRY_CHECKS_PASSED",
            "overall_status": overall_status,
            "violations": violations,
            "warnings": warnings,
            "missing_information": missing_information,
            "bill_of_materials": bom_items,
            "total_estimated_cost_inr": round(total_cost, 2) if total_cost_complete else None,
            "fit_tolerance_mm": {
                "ceiling_field_trim_allowance": CEILING_FIELD_TRIM_TOLERANCE_MM
            },
            "review_required": True,
        }
