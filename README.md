# Elevai

Elevai is a proof-of-concept workspace for planning lift-cabin modernization. It combines a bounded example catalog, site measurements, deterministic dimensional checks, image-assisted component detection, procedural surface previews, and a draft proposal.

## What the current prototype does

- Displays catalog items and lets a user edit the proposed SKU choices across wall, floor, controls, ceiling, and door categories.
- Collects site measurements separately from images. Missing dimensions keep package recommendations on hold.
- Compares a lowest-cost checked package with an accessibility-oriented catalog candidate, then screens both through the same deterministic fit rules.
- Shows detector bounding boxes and confidence, and creates repeatable procedural material previews with a change mask.
- Exports a draft proposal with site/reference images, selected SKU references, unknowns, assumptions, and an unsigned qualified-review section.

## Important prototype limits

- Only `scene_01_passenger` has a prepared image, measurements, and gold annotations. `custom_upload` is an upload workspace, not a labeled benchmark scene.
- The detector returns bounding boxes, not pixel-accurate segmentation masks. Any surface polygons used by the renderer are geometric approximations derived from annotations or detections.
- The renderer currently does not synthesize every catalog category (including door skins); the response and interface identify categories that were not rendered.
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
- `scripts/evaluate_benchmark.py`: benchmark reporting for scenes whose annotations have been independently marked verified.

## Evaluation

Use `data/scenes/scene_template/` to prepare new scenes and mark annotations `verified` only after independent human review. Then run `python scripts/evaluate_benchmark.py`. It reports detector precision/recall/F1 and box IoU on verified scenes, fit-rule violations, and leaves metric fit error and human-study outcomes unreported until they have valid independent measurements. The current demonstration annotations are provisional, so they are not included in benchmark accuracy.

## Planned validation before a field pilot

Create three independently sourced and annotated scenes, keep at least one scene out of prompt/model tuning, report component-selection accuracy and geometric fit error, count rule violations and unknown inputs, and compare proposal preparation time with a documented manual baseline. Treat generated renders as visual aids until a qualified reviewer confirms the geometry and selected products.
