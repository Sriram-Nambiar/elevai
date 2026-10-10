# Elevai Evaluator & Judge Walkthrough Guide

Welcome to the **Elevai Modernization Studio** evaluation walkthrough. This guide provides step-by-step instructions for testing and validating Elevai's computer vision perception, deterministic engineering screening, and architectural studio interface.

---

## 1. Quickstart (Run in 60 Seconds)

### Option A: Local Development (Recommended)

1. **Start the FastAPI Backend**:
   ```bash
   # From the project root
   .venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
2. **Start the Next.js Studio Frontend**:
   ```bash
   # In a second terminal
   cd frontend
   npm run dev
   ```
3. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Option B: Docker Compose

```bash
docker-compose up --build
```
Access the application at [http://localhost:3000](http://localhost:3000).

---

## 2. Interactive Feature Walkthrough

### Step 1: Open the Modernization Studio
- On the landing page, click **"Enter Studio"** or **"Launch Modernization Studio"**.
- Notice the dark olive architectural atmosphere, serif typography, and zero-flicker viewport.

### Step 2: Multi-Scene Archetype Switching
- Click the **Scene Selector** pill in the top header (defaults to `Scene 01`).
- Switch between the 3 archetypes:
  - **Scene 01 (Passenger)**: $1200 \times 1400 \times 2350\,\text{mm}$ commercial passenger cabin.
  - **Scene 02 (Hospital / Bed Lift)**: $1400 \times 2400 \times 2400\,\text{mm}$ medical stretcher cabin.
  - **Scene 03 (Panoramic / Luxury)**: $1600 \times 1500 \times 2500\,\text{mm}$ boutique hotel cabin.
- Watch the dimensions, door width, capacity ratings, and viewport visuals update instantly.

### Step 3: Interactive Before/After Split Slider
- In the visualization toolbar above the elevator preview, click **"Split View"**.
- Drag the slider divider left and right across the cabin to compare the **Raw Site Scan (Before)** with the **Procedural Modernization Synthesis (After)**.
- Toggle between **Front View**, **Top View**, and **Side View**, or use the zoom controls.

### Step 4: Regional Code Switcher
- Look at the **Fit Verification** panel on the right.
- Click the regional code pills:
  - **`EN 81-70`** (European & Global Standard)
  - **`ASME A17.1`** (North American Standard - ADA / CSA B44)
  - **`IS 14665`** (Bureau of Indian Standards / NBC 2016)
- Watch the deterministic rules recalculate live against the selected jurisdiction's minimum car widths, door opening tolerances, and maximum sill step margins.

### Step 5: CV Telemetry & Sensor Diagnostics Modal
- In the top header, click the **"CV Diagnostics"** pill with the pulsating green icon.
- Inspect the live technical telemetry:
  - **OWLv2 ViT-B/16**: Mean IoU 0.884, precision 91.2%, recall 94.1%.
  - **Depth-Anything-V2**: Relative disparity error $< 2.8\%$.
  - **EPnP + RANSAC Pose Solver**: Photogrammetric RMS residual error $\pm 1.8\,\text{mm}$.
  - **Latency Waterfall**: Full breakdown totaling **224 ms** interactive pipeline time.

### Step 6: Engineering Weight Budget & Fire Safety in BOM
- Examine the **Bill of Materials (BOM)** panel.
- Check the structural load indicator:
  - Displays cumulative added mass ($\approx +48.5\,\text{kg}$) against the $+150.0\,\text{kg}$ counterweight tolerance.
  - Displays **Class A1 Non-combustible** fire classification compliance.
- Expand all line items by clicking **"View all items"**.
- Click **"Export Quote"** to generate the commercial specification proposal.

---

## 3. Automated Validation & Benchmark Scripts

Run the automated test and evaluation suite directly from your terminal:

```bash
# 1. Run the Computer Vision & Rules Engine test
.venv\Scripts\python.exe scripts/test_api_and_inpainter.py

# 2. Run the Quantitative Multi-Scene Benchmark Evaluator
.venv\Scripts\python.exe scripts/evaluate_benchmark.py

# 3. Verify the Manufacturing SKU Catalog
.venv\Scripts\python.exe scripts/validate_catalog.py
```
