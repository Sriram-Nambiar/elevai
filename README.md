# elevai

> Smart Visual Planning Tool for Lift Modernization

`elevai` is an AI-assisted spatial planning and visual modernization engine for elevator cabs. It segments cabin components from site photos, verifies physical tolerances against a bounded hardware catalog using deterministic engineering rules, and generates structure-preserving before-and-after renders alongside client proposals.

**Key Architecture**
* **Frontend:** Next.js (TypeScript), Tailwind CSS, Canvas / Fabric.js, `@react-pdf/renderer`
* **AI & Geometry Engine:** FastAPI (Python), Grounded SAM 2, Depth Anything V2
* **Structure-Preserving Synthesis:** ControlNet (Depth + Lineart) + Inpainting Diffusion
* **Compliance & Validation:** Deterministic rule engine against EN 81-70 / ADA standards

**Directory Layout**
```text
elevai/
├── data/
│   ├── catalog/          # Bounded SKU definitions and JSON validation schema
│   └── scenes/           # Reference elevator datasets and gold annotations
├── scripts/              # Data validation and benchmarking tools
├── backend/              # FastAPI server (segmentation, depth calibration, inpainting)
└── frontend/             # Next.js UI, comparison slider, and PDF proposal generator
