import os
import shutil
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure backend directory is in sys.path for internal service imports
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.rules_engine import RulesEngine
from services.calibrator import CabinCalibrator
from services.segmenter import CabinSegmenter
from services.inpainter import CabinInpainter
from services.pdf_generator import QuotePDFGenerator

app = FastAPI(
    title="Elevai API",
    description="AI-driven elevator modernization, spatial compliance auditing (EN 81-70), and procedural inpainting previews.",
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

BASE_DIR = backend_dir.parent

# Mount static scenes directory to serve raw scans and modernized renders
scenes_static_dir = BASE_DIR / "data" / "scenes"
scenes_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/scenes", StaticFiles(directory=str(scenes_static_dir)), name="static_scenes")

# -----------------------------------------------------------------------------
# Service Singletons (Lazy initialized or pre-loaded)
# -----------------------------------------------------------------------------
rules_engine = RulesEngine()

_calibrator: Optional[CabinCalibrator] = None
_segmenter: Optional[CabinSegmenter] = None
_inpainter: Optional[CabinInpainter] = None
_pdf_generator: Optional[QuotePDFGenerator] = None

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

def get_inpainter() -> CabinInpainter:
    global _inpainter
    if _inpainter is None:
        _inpainter = CabinInpainter()
    return _inpainter

def get_pdf_generator() -> QuotePDFGenerator:
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = QuotePDFGenerator()
    return _pdf_generator


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

class PreviewRenderRequest(BaseModel):
    scene_id: str = Field(default="scene_01_passenger", description="Target scene folder name inside data/scenes/")
    selected_skus: List[str] = Field(..., description="List of hardware SKU IDs to composite")

class ExportQuoteRequest(BaseModel):
    selected_skus: List[str] = Field(..., example=["WALL-SS-HAIRLINE", "FLR-RUB-COIN", "COP-COL-TFT", "CEIL-LED-PERIM"])
    cabin_dimensions_mm: Optional[Dict[str, int]] = Field(
        default=None,
        description="Clear cabin dimensions width, depth, height in mm"
    )
    max_allowable_flooring_thickness_mm: Optional[int] = Field(
        default=12,
        description="Maximum floor sill threshold clearance in mm"
    )


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "services": {
            "rules_engine": "online",
            "inpainter": "ready",
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
        with open(default_measurements_path, "r", encoding="utf-8") as f:
            measurements = json.load(f)

    result = rules_engine.evaluate_configuration(
        site_measurements=measurements,
        selected_skus=payload.selected_skus
    )
    return result

@app.post("/api/v1/scene/upload")
async def upload_cabin_scene(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG/PNG).")

    upload_scene_dir = BASE_DIR / "data" / "scenes" / "custom_upload"
    upload_scene_dir.mkdir(parents=True, exist_ok=True)

    image_path = upload_scene_dir / "cabin_view.jpg"
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Maintain raw.jpg as identical copy for compatibility
    raw_path = upload_scene_dir / "raw.jpg"
    shutil.copyfile(image_path, raw_path)

    # Initialize baseline calibration and measurements
    measurements_file = upload_scene_dir / "site_measurements.json"
    default_measurements = {
        "scene_id": "custom_upload",
        "lift_type": "passenger",
        "building_type": "commercial",
        "cabin_dimensions_mm": {
            "width": 1200,
            "depth": 1400,
            "height": 2350
        },
        "max_allowable_flooring_thickness_mm": 12,
        "existing_cop": {
            "mounting_height_from_floor_mm": 1000,
            "panel_width_mm": 180,
            "panel_height_mm": 800
        },
        "door_opening_width_mm": 800
    }
    with open(measurements_file, "w", encoding="utf-8") as f:
        json.dump(default_measurements, f, indent=2)

    return {
        "status": "success",
        "scene_id": "custom_upload",
        "image_url": "http://127.0.0.1:8000/static/scenes/custom_upload/cabin_view.jpg",
        "filename": file.filename,
        "cabin_dimensions_mm": default_measurements["cabin_dimensions_mm"],
        "max_allowable_flooring_thickness_mm": default_measurements["max_allowable_flooring_thickness_mm"],
        "existing_cop": default_measurements["existing_cop"]
    }

@app.post("/api/v1/preview/render")
def render_preview(payload: PreviewRenderRequest):
    scene_dir = BASE_DIR / "data" / "scenes" / payload.scene_id
    if not scene_dir.exists():
        raise HTTPException(status_code=404, detail=f"Scene folder '{payload.scene_id}' not found.")

    inpainter = get_inpainter()
    try:
        render_result = inpainter.render(
            scene_dir=str(scene_dir),
            selected_skus=payload.selected_skus,
            output_filename="after_preview.jpg"
        )
        preview_url = f"http://127.0.0.1:8000/static/scenes/{payload.scene_id}/after_preview.jpg"
        return {
            "status": "success",
            "scene_id": payload.scene_id,
            "preview_url": preview_url,
            "rendered_components": render_result.get("rendered_components", []),
            "selected_skus": payload.selected_skus
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview rendering failure: {str(e)}")

@app.post("/api/v1/quote/export")
def export_quotation_pdf(payload: ExportQuoteRequest):
    dims = payload.cabin_dimensions_mm or {"width": 1200, "depth": 1400, "height": 2350}
    max_floor_thk = payload.max_allowable_flooring_thickness_mm or 12

    site_measurements = {
        "cabin_dimensions_mm": dims,
        "max_allowable_flooring_thickness_mm": max_floor_thk,
        "existing_cop": {
            "mounting_height_from_floor_mm": 1000
        }
    }

    # Evaluate configuration using deterministic rules engine
    evaluation = rules_engine.evaluate_configuration(
        site_measurements=site_measurements,
        selected_skus=payload.selected_skus
    )

    pdf_gen = get_pdf_generator()
    try:
        pdf_bytes = pdf_gen.generate_pdf(
            evaluation=evaluation,
            cabin_dimensions_mm=dims,
            max_allowable_flooring_thickness_mm=max_floor_thk
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=elevai_modernization_quote.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failure: {str(e)}")

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