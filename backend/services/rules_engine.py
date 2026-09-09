import os
import json
import math
from typing import Dict, List, Any

class RulesEngine:
    def __init__(self, catalog_path: str = None):
        if catalog_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            catalog_path = os.path.join(base_dir, "data", "catalog", "catalog.json")

        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        items = catalog_data.get("catalog_items", []) if isinstance(catalog_data, dict) else catalog_data

        # Index catalog by sku_id (with fallbacks for sku / id)
        self.catalog = {
            (item.get("sku_id") or item.get("sku") or item.get("id")): item
            for item in items
            if (item.get("sku_id") or item.get("sku") or item.get("id")) is not None
        }

    def evaluate_configuration(
        self,
        site_measurements: Dict[str, Any],
        selected_skus: List[str]
    ) -> Dict[str, Any]:
        cabin_dims = site_measurements["cabin_dimensions_mm"]
        c_width = cabin_dims["width"]
        c_depth = cabin_dims["depth"]
        c_height = cabin_dims["height"]
        max_floor_thk = site_measurements.get("max_allowable_flooring_thickness_mm", 15)

        violations = []
        warnings = []
        bom_items = []
        total_cost = 0.0

        for sku in selected_skus:
            if sku not in self.catalog:
                violations.append(f"Unknown SKU '{sku}' not found in hardware catalog.")
                continue

            item = self.catalog[sku]
            category = item.get("category", "unknown")
            dims = item.get("dimensions_mm", {})
            unit_cost = item.get("unit_cost_inr", item.get("unit_price_usd", 0.0))
            item_name = item.get("name", sku)
            qty = 0
            item_violations = []

            # -----------------------------------------------------------------
            # 1. Wall Panels
            # -----------------------------------------------------------------
            if category == "wall_panel":
                panel_h = dims.get("height", 0)
                panel_w = dims.get("width", 1)

                if panel_h > c_height:
                    msg = f"Wall Panel [{sku}] height ({panel_h}mm) exceeds cabin height ({c_height}mm)."
                    violations.append(msg)
                    item_violations.append(msg)
                elif (c_height - panel_h) > 200:
                    warnings.append(
                        f"Wall Panel [{sku}] height leaves a gap of {c_height - panel_h}mm. Top frieze panel required."
                    )

                back_wall_panels = math.ceil(c_width / panel_w) if panel_w > 0 else 0
                side_wall_panels = math.ceil(c_depth / panel_w) * 2 if panel_w > 0 else 0
                qty = back_wall_panels + side_wall_panels

            # -----------------------------------------------------------------
            # 2. Flooring
            # -----------------------------------------------------------------
            elif category == "flooring":
                # Check explicit thickness keys first; fallback to lowest dimension value
                explicit_thk = dims.get("thickness_mm") or dims.get("thickness")
                if explicit_thk is not None:
                    thickness = explicit_thk
                else:
                    dim_values = [v for v in dims.values() if isinstance(v, (int, float)) and v > 0]
                    thickness = min(dim_values) if dim_values else 0

                if thickness > max_floor_thk:
                    msg = f"Flooring [{sku}] thickness ({thickness}mm) exceeds max sill clearance ({max_floor_thk}mm). Door sweep failure risk."
                    violations.append(msg)
                    item_violations.append(msg)

                floor_area_m2 = (c_width * c_depth) / 1_000_000.0
                pack_l = dims.get("length_mm") or dims.get("length") or dims.get("depth", c_depth)
                pack_w = dims.get("width_mm") or dims.get("width", c_width)
                pack_coverage_m2 = (pack_l * pack_w) / 1_000_000.0

                qty = math.ceil(floor_area_m2 / pack_coverage_m2) if pack_coverage_m2 > 0 else 1

            # -----------------------------------------------------------------
            # 3. Car Operating Panel (EN 81-70 / ADA)
            # -----------------------------------------------------------------
            elif category == "car_operating_panel":
                qty = 1
                cop_h = dims.get("height", 0)

                existing_cop = site_measurements.get("existing_cop", {})
                mount_h = existing_cop.get("mounting_height_from_floor_mm", 1000)

                interactive_max = item.get("mounting_constraints", {}).get("interactive_reach_max_mm", 1200)
                if mount_h > interactive_max:
                    msg = f"COP [{sku}] mount baseline ({mount_h}mm) violates EN 81-70 max reach limit ({interactive_max}mm)."
                    violations.append(msg)
                    item_violations.append(msg)

                if cop_h > c_height:
                    msg = f"COP [{sku}] height ({cop_h}mm) exceeds cabin vertical clearance ({c_height}mm)."
                    violations.append(msg)
                    item_violations.append(msg)

            # -----------------------------------------------------------------
            # 4. Ceiling Lighting (Field-Trimmable Canopies)
            # -----------------------------------------------------------------
            elif category == "ceiling_lighting":
                ceil_w = dims.get("width", 0)
                ceil_l = dims.get("length", dims.get("depth", 0))

                oversize_w = ceil_w - c_width
                oversize_l = ceil_l - c_depth

                if oversize_w > 200 or oversize_l > 200:
                    msg = f"Ceiling [{sku}] dimensions ({ceil_w}x{ceil_l}mm) exceed cabin frame ({c_width}x{c_depth}mm) by >200mm. Exceeds site trimming tolerance."
                    violations.append(msg)
                    item_violations.append(msg)
                elif oversize_w > 0 or oversize_l > 0:
                    warnings.append(
                        f"Ceiling [{sku}] ({ceil_w}x{ceil_l}mm) is oversized by {max(oversize_w, oversize_l)}mm. Field-trimming to {c_width}x{c_depth}mm required on site."
                    )
                qty = 1

            else:
                qty = 1

            item_cost = qty * unit_cost
            total_cost += item_cost

            bom_items.append({
                "sku_id": sku,
                "name": item_name,
                "category": category,
                "quantity": qty,
                "unit_cost_inr": unit_cost,
                "extended_cost_inr": round(item_cost, 2),
                "status": "PASS" if len(item_violations) == 0 else "FAIL"
            })

        is_compliant = len(violations) == 0

        return {
            "is_compliant": is_compliant,
            "overall_status": "APPROVED" if is_compliant else "REJECTED",
            "violations": violations,
            "warnings": warnings,
            "bill_of_materials": bom_items,
            "total_estimated_cost_inr": round(total_cost, 2)
        }