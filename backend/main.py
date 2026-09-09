import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure backend directory is in sys.path for internal service imports
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.rules_engine import RulesEngine
from services.calibrator import CabinCalibrator
from services.segmenter import CabinSegmenter

app = FastAPI(
    title="Elevai API",
    description="AI-driven elevator modernization, segmentation, calibration, and fit validation platform.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Service Singletons (Lazy initialized or pre-loaded)
# -----------------------------------------------------------------------------
BASE_DIR = backend_dir.parent
rules_engine = RulesEngine()

_calibrator: Optional[CabinCalibrator] = None
_segmenter: Optional[CabinSegmenter] = None

def get_calibrator() -> CabinCalibrator:
    global _calibrator
    if _calibrator is None:
        _calibrator = CabinCalibrator()
    return _calibrator

def get_segmenter() -> CabinSegmenter:
    global _segmenter
    if _segmenter is None:
        _segmenter = CabinSegmenter()
    return _segmenter


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class EvaluateRequest(BaseModel):
    selected_skus: List[str] = Field(..., example=["WALL-SS-HAIRLINE", "FLR-RUB-COIN", "COP-COL-TFT", "CEIL-LED-PERIM"])
    site_measurements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional full site measurement payload. If omitted, scene_01_passenger data is used."
    )

class SceneActionRequest(BaseModel):
    scene_id: str = Field(default="scene_01_passenger", description="Target scene folder name inside data/scenes/")


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "services": {
            "rules_engine": "online",
            "calibrator": "ready",
            "segmenter": "ready"
        }
    }


@app.get("/api/v1/catalog")
def get_catalog(category: Optional[str] = Query(None, description="Filter catalog items by category")):
    items = list(rules_engine.catalog.values())
    if category:
        items = [i for i in items if i.get("category") == category]
    return {
        "total_items": len(items),
        "catalog_items": items
    }


@app.post("/api/v1/rules/evaluate")
def evaluate_configuration(payload: EvaluateRequest):
    measurements = payload.site_measurements
    if measurements is None:
        default_measurements_path = BASE_DIR / "data" / "scenes" / "scene_01_passenger" / "site_measurements.json"
        if not default_measurements_path.exists():
            raise HTTPException(status_code=404, detail="Default site measurements file not found.")
        import json
        with open(default_measurements_path, "r", encoding="utf-8") as f:
            measurements = json.load(f)

    result = rules_engine.evaluate_configuration(
        site_measurements=measurements,
        selected_skus=payload.selected_skus
    )
    return result


@app.post("/api/v1/calibrate")
def run_calibration(payload: SceneActionRequest):
    scene_dir = os.path.join(BASE_DIR, "data", "scenes", payload.scene_id)
    if not os.path.exists(scene_dir):
        raise HTTPException(status_code=404, detail=f"Scene folder '{payload.scene_id}' not found.")

    calibrator = get_calibrator()
    try:
        calib_result = calibrator.calibrate_scene(scene_dir=scene_dir)
        return {
            "status": "success",
            "scene_id": payload.scene_id,
            "data": calib_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration failure: {str(e)}")


@app.post("/api/v1/segment")
def run_segmentation(payload: SceneActionRequest):
    scene_dir = os.path.join(BASE_DIR, "data", "scenes", payload.scene_id)
    if not os.path.exists(scene_dir):
        raise HTTPException(status_code=404, detail=f"Scene folder '{payload.scene_id}' not found.")

    segmenter = get_segmenter()
    try:
        seg_result = segmenter.segment_scene(scene_dir=scene_dir)
        return {
            "status": "success",
            "scene_id": payload.scene_id,
            "data": seg_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Segmentation failure: {str(e)}")