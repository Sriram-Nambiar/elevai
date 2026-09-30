import os
import json
import sys
import uuid
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError

# Ensure backend directory is in sys.path for internal service imports
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.rules_engine import RulesEngine
from services.recommender import RecommendationEngine
from services.calibrator import CabinCalibrator
from services.segmenter import CabinSegmenter
from services.inpainter import CabinInpainter
from services.pdf_generator import QuotePDFGenerator

app = FastAPI(
    title="Elevai API",
    description="Measured-site lift modernization planning, catalog fit screening, and procedural concept previews.",
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
recommendation_engine = RecommendationEngine(rules_engine)

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

class RecommendRequest(BaseModel):
    site_measurements: Dict[str, Any] = Field(..., description="Measured site envelope used for option screening")

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
        default=None,
        description="Maximum floor sill threshold clearance in mm"
    )
    site_measurements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Explicit site measurements; missing fields remain unknown in the draft."
    )
    scene_id: Optional[str] = Field(default=None, description="Scene used for reference images")


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

@app.post("/api/v1/recommendations")
def recommend_configurations(payload: RecommendRequest):
    return recommendation_engine.recommend(payload.site_measurements)

@app.post("/api/v1/scene/upload")
async def upload_cabin_scene(file: UploadFile = File(...)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG/PNG).")

    contents = await file.read(12 * 1024 * 1024 + 1)
    if len(contents) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 12 MB or smaller.")

    try:
        with Image.open(BytesIO(contents)) as uploaded_image:
            if uploaded_image.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(status_code=400, detail="Unsupported image encoding.")
            uploaded_image.verify()
        with Image.open(BytesIO(contents)) as uploaded_image:
            normalized_image = uploaded_image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable image.")

    scene_id = f"upload_{uuid.uuid4().hex[:12]}"
    upload_scene_dir = BASE_DIR / "data" / "scenes" / scene_id
    upload_scene_dir.mkdir(parents=True, exist_ok=True)

    image_path = upload_scene_dir / "cabin_view.jpg"
    normalized_image.save(image_path, format="JPEG", quality=95)

    # Measurements are intentionally collected separately from the photograph.
    measurements_file = upload_scene_dir / "site_measurements.json"
    measurements = {
        "scene_id": scene_id,
        "measurement_status": "missing",
        "unknowns": [
            "cabin_dimensions_mm",
            "max_allowable_flooring_thickness_mm",
            "existing_cop.mounting_height_from_floor_mm"
        ]
    }
    with open(measurements_file, "w", encoding="utf-8") as f:
        json.dump(measurements, f, indent=2)

    return {
        "status": "success",
        "scene_id": scene_id,
        "image_url": f"/static/scenes/{scene_id}/cabin_view.jpg",
        "filename": file.filename,
        "measurement_status": "missing",
        "unknowns": measurements["unknowns"]
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
            "change_mask_url": f"/static/scenes/{payload.scene_id}/{render_result['change_mask_filename']}",
            "rendered_components": render_result.get("rendered_components", []),
            "selected_skus": payload.selected_skus,
            "changed_pixel_fraction": render_result.get("changed_pixel_fraction"),
            "geometry_source": render_result.get("geometry_source"),
            "review_required": render_result.get("review_required", True),
            "not_rendered_categories": render_result.get("not_rendered_categories", []),
            "visual_disclaimer": render_result.get("visual_disclaimer"),
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview rendering failure: {str(e)}")

@app.post("/api/v1/quote/export")
def export_quotation_pdf(payload: ExportQuoteRequest):
    site_measurements = payload.site_measurements or {
        "cabin_dimensions_mm": payload.cabin_dimensions_mm,
        "max_allowable_flooring_thickness_mm": payload.max_allowable_flooring_thickness_mm,
        "existing_cop": {},
    }
    dims = site_measurements.get("cabin_dimensions_mm")
    dims = dims if isinstance(dims, dict) else {}
    max_floor_thk = site_measurements.get("max_allowable_flooring_thickness_mm")

    # Evaluate configuration using deterministic rules engine
    evaluation = rules_engine.evaluate_configuration(
        site_measurements=site_measurements,
        selected_skus=payload.selected_skus
    )

    pdf_gen = get_pdf_generator()
    reference_images = []
    if payload.scene_id and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", payload.scene_id):
        scene_dir = (BASE_DIR / "data" / "scenes" / payload.scene_id).resolve()
        scenes_root = (BASE_DIR / "data" / "scenes").resolve()
        if scene_dir.parent == scenes_root:
            source_image = next((path for path in (
                scene_dir / "cabin_view.jpg", scene_dir / "raw.jpg"
            ) if path.is_file()), None)
            preview_image = scene_dir / "after_preview.jpg"
            if source_image:
                reference_images.append(("Uploaded / reference scene", str(source_image)))
            if preview_image.is_file():
                reference_images.append(("Procedural concept preview", str(preview_image)))

    try:
        pdf_bytes = pdf_gen.generate_pdf(
            evaluation=evaluation,
            cabin_dimensions_mm=dims,
            max_allowable_flooring_thickness_mm=max_floor_thk,
            site_measurements=site_measurements,
            scene_id=payload.scene_id,
            reference_images=reference_images,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=elevai_draft_modernization_proposal.pdf"}
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
    scene_dir = BASE_DIR / "data" / "scenes" / payload.scene_id
    if not scene_dir.exists():
        raise HTTPException(status_code=404, detail=f"Scene folder '{payload.scene_id}' not found.")

    segmenter = get_segmenter()
    try:
        raw_result = segmenter.segment_scene(scene_dir=str(scene_dir))

        category_map = {
            "wall_panel": ("wall_panel", "#3b82f6", "Wall panel"),
            "cop": ("car_operating_panel", "#10b981", "Car operating panel"),
            "ceiling": ("ceiling_lighting", "#a855f7", "Ceiling / lighting"),
            "floor": ("flooring", "#f59e0b", "Flooring"),
            "doors": ("doors", "#06b6d4", "Doors"),
            "display_unit": ("display_unit", "#f97316", "Display unit")
        }
        segments = []
        for detection in raw_result:
            category_info = category_map.get(detection.get("category"))
            box = detection.get("bbox_normalized")
            if category_info is None or not isinstance(box, list) or len(box) != 4:
                continue
            top, left, bottom, right = [min(1.0, max(0.0, float(value))) for value in box]
            if bottom <= top or right <= left:
                continue
            category, color, label = category_info
            confidence = float(detection.get("confidence", 0.0))
            segments.append({
                "id": detection.get("component_id", f"{category}_{len(segments)}"),
                "label": label,
                "category": category,
                "color": color,
                "polygon": [[left, top], [right, top], [right, bottom], [left, bottom]],
                "confidence": round(confidence, 3),
                "review_required": confidence < 0.45,
                "geometry_source": "detector_bounding_box"
            })

        return {
            "status": "success",
            "scene_id": scene_dir.name,
            "segments": segments,
            "raw_detections": raw_result,
            "geometry_note": "Overlays show detector bounding boxes, not pixel-accurate segmentation masks. Verify them before using them for a proposal."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Segmentation failure: {str(e)}")
