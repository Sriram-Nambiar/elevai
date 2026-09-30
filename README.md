# Elevai

Elevai is a proof-of-concept workspace for planning lift-cabin modernization. It combines a bounded example catalog, site measurements, deterministic dimensional checks, image-assisted component detection, procedural surface previews, and a draft proposal.

## What the current prototype does

- Displays catalog items and lets a user select one item per supported cabin category.
- Runs dimensional checks against the entered cabin envelope and reports warnings and violations.
- Uploads a cabin image, runs open-vocabulary object detection, and creates a procedural preview from scene geometry.
- Exports a PDF summary of the selected configuration.

## Important prototype limits

- Only `scene_01_passenger` has a prepared image, measurements, and gold annotations. `custom_upload` is an upload workspace, not a labeled benchmark scene.
- The detector returns bounding boxes, not pixel-accurate segmentation masks. Any surface polygons used by the renderer are geometric approximations derived from annotations or detections.
- Single-image depth estimation is relative depth, not a metric site survey. The entered dimensions are the metric reference.
- The catalog, prices, compatibility checks, and standards references are demonstration data. They are not approved manufacturer specifications or a certification of EN 81-70 compliance.
- Procedural previews illustrate material choices and may not match the installed product or preserve every original pixel. A qualified lift professional must review the site and proposal before customer use.
- Uploaded images currently use a local development workflow. Do not upload confidential customer/site images to a public deployment.

## Run locally

Start the API from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.main:app --reload
```

In another terminal, start the web application:

```powershell
cd frontend
npm install
npm run dev
```

The web app expects the API at `http://127.0.0.1:8000` by default.

## Data layout

- `data/catalog/catalog.json`: bounded example SKU list and material descriptions.
- `data/catalog/schema.json`: structural catalog validation schema.
- `data/scenes/<scene-id>/`: source image, measurements, optional annotations, masks, and generated previews.
- `scripts/`: focused local utilities for catalog checks and pipeline experiments.

## Planned validation before a field pilot

Create three independently sourced and annotated scenes, keep at least one scene out of prompt/model tuning, report component-selection accuracy and geometric fit error, count rule violations and unknown inputs, and compare proposal preparation time with a documented manual baseline. Treat generated renders as visual aids until a qualified reviewer confirms the geometry and selected products.
