from itertools import product
from typing import Any, Dict, List


PLANNED_CATEGORIES = (
    "wall_panel",
    "flooring",
    "car_operating_panel",
    "ceiling_lighting",
)


class RecommendationEngine:
    """Rank only catalog combinations that pass the current dimensional screen."""

    def __init__(self, rules_engine):
        self.rules_engine = rules_engine

    @staticmethod
    def _accessibility_evidence(item: Dict[str, Any]) -> tuple[int, List[str]]:
        text = " ".join([
            item.get("name", ""),
            item.get("visual_attributes", {}).get("material", ""),
            item.get("visual_attributes", {}).get("finish", ""),
            " ".join(item.get("visual_attributes", {}).get("prompt_keywords", [])),
        ]).casefold()
        category = item.get("category")
        score = 0
        reasons: List[str] = []

        if category == "car_operating_panel":
            reach = item.get("mounting_constraints", {}).get("interactive_reach_max_mm")
            if isinstance(reach, (int, float)) and reach > 0:
                score += max(0, 1200 - int(reach)) // 100
                reasons.append(f"Catalog interactive reach limit: {reach:g} mm")
            if "braille" in text:
                score += 3
                reasons.append("Catalog description mentions Braille controls")
            if "horizontal" in text or "low reach" in text:
                score += 2
                reasons.append("Catalog description identifies a horizontal or lower-reach control")

        if category == "flooring" and any(term in text for term in ("non-slip", "anti-slip", "slip-resistant")):
            score += 2
            reasons.append("Catalog description identifies a slip-resistant surface")

        if category == "ceiling_lighting" and any(term in text for term in ("diffused", "glare-free", "indirect")):
            score += 1
            reasons.append("Catalog description identifies diffused or indirect lighting")

        return score, reasons

    def recommend(self, site_measurements: Dict[str, Any]) -> Dict[str, Any]:
        options_by_category = [
            [item for item in self.rules_engine.catalog.values() if item.get("category") == category]
            for category in PLANNED_CATEGORIES
        ]
        if any(not items for items in options_by_category):
            return {
                "status": "unavailable",
                "recommendations": [],
                "missing_information": ["Catalog must contain at least one item in each planned category."],
            }

        evaluated = []
        for combination in product(*options_by_category):
            skus = [item.get("sku_id") for item in combination]
            evaluation = self.rules_engine.evaluate_configuration(site_measurements, skus)
            if evaluation.get("overall_status") != "GEOMETRY_CHECKS_PASSED":
                continue
            evidence = [self._accessibility_evidence(item) for item in combination]
            evaluated.append({
                "items": combination,
                "selected_skus": skus,
                "evaluation": evaluation,
                "accessibility_score": sum(entry[0] for entry in evidence),
                "accessibility_reasons": [reason for _, reasons in evidence for reason in reasons],
                "estimated_cost_inr": evaluation.get("total_estimated_cost_inr"),
            })

        if not evaluated:
            evaluation = self.rules_engine.evaluate_configuration(
                site_measurements,
                [items[0].get("sku_id") for items in options_by_category],
            )
            return {
                "status": "review_required",
                "recommendations": [],
                "missing_information": evaluation.get("missing_information", []),
                "note": "No package is recommended until site measurements are complete and at least one package passes the dimensional screen.",
            }

        budget_choice = min(evaluated, key=lambda entry: (entry["estimated_cost_inr"], entry["selected_skus"]))
        accessibility_choice = max(
            evaluated,
            key=lambda entry: (
                entry["accessibility_score"],
                -entry["estimated_cost_inr"],
                entry["selected_skus"],
            ),
        )

        selections = [
            {
                "profile": "budget",
                "label": "Lowest-cost checked package",
                "entry": budget_choice,
                "reasons": ["Lowest estimated cost among catalog combinations that passed the current dimensional screen."],
            }
        ]
        if accessibility_choice["selected_skus"] != budget_choice["selected_skus"]:
            selections.append({
                "profile": "accessibility_oriented",
                "label": "Accessibility-oriented candidate",
                "entry": accessibility_choice,
                "reasons": accessibility_choice["accessibility_reasons"] or [
                    "Selected using the available catalog attributes; no special accessibility attribute was identified."
                ],
            })

        recommendations = []
        for selection in selections:
            entry = selection["entry"]
            recommendations.append({
                "profile": selection["profile"],
                "label": selection["label"],
                "selected_skus": entry["selected_skus"],
                "estimated_cost_inr": entry["estimated_cost_inr"],
                "reasons": selection["reasons"],
                "fit_evaluation": entry["evaluation"],
                "review_required": True,
            })

        return {
            "status": "options_available",
            "recommendations": recommendations,
            "combinations_evaluated": len(list(product(*options_by_category))),
            "passing_combinations": len(evaluated),
            "selection_basis": "Deterministic catalog attributes, estimated cost, and prototype dimensional checks.",
            "limitation": "Accessibility-oriented is a catalog-based candidate profile, not a standards-compliance or accessibility certification.",
        }
