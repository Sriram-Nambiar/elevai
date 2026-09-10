import os
import sys
import json
from fastapi.testclient import TestClient

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.append(backend_dir)
from main import app

def run_tests():
    client = TestClient(app)

    # 1. Health check
    r = client.get("/api/v1/health")
    assert r.status_code == 200, f"Health failed: {r.text}"
    print(f"[+] Health check passed: {r.json()}")

    # 2. Catalog check
    r = client.get("/api/v1/catalog")
    assert r.status_code == 200, f"Catalog failed: {r.text}"
    items_count = r.json()["total_items"]
    assert items_count >= 17, f"Catalog items count {items_count} < 17"
    print(f"[+] Catalog passed: {items_count} items found")

    # 3. Rules engine evaluation
    payload = {
        "selected_skus": ["WALL-BRZ-BRUSHED", "FLR-GRAN-NERO", "COP-COL-TFT", "CEIL-LED-PERIM"]
    }
    r = client.post("/api/v1/rules/evaluate", json=payload)
    assert r.status_code == 200, f"Evaluate failed: {r.text}"
    eval_data = r.json()
    print(f"[+] Evaluate passed: Status={eval_data['overall_status']}, Cost=INR {eval_data['total_estimated_cost_inr']:,.2f}")

    # 4. Inpainter Preview render
    render_payload = {
        "scene_id": "scene_01_passenger",
        "selected_skus": ["WALL-BRZ-BRUSHED", "FLR-GRAN-NERO", "COP-COL-TFT", "CEIL-LED-PERIM"]
    }
    r = client.post("/api/v1/preview/render", json=render_payload)
    assert r.status_code == 200, f"Render failed: {r.text}"
    render_data = r.json()
    print(f"[+] Inpainter render passed: {render_data['preview_url']}")
    print(f"    Rendered components: {render_data['rendered_components']}")

    # 5. Static file serving check (after_preview.jpg)
    r = client.get("/static/scenes/scene_01_passenger/after_preview.jpg")
    assert r.status_code == 200, f"Static fetch failed: {r.status_code}"
    assert len(r.content) > 10000, "Rendered image too small"
    print(f"[+] Static file after_preview.jpg verified: {len(r.content)} bytes")

    # 6. Static file serving check (cabin_view.jpg)
    r = client.get("/static/scenes/scene_01_passenger/cabin_view.jpg")
    assert r.status_code == 200, f"cabin_view.jpg fetch failed: {r.status_code}"
    print(f"[+] Static file cabin_view.jpg verified: {len(r.content)} bytes")

    # 7. PDF Quotation export check
    export_payload = {
        "selected_skus": ["WALL-BRZ-BRUSHED", "FLR-GRAN-NERO", "COP-COL-TFT", "CEIL-LED-PERIM"],
        "cabin_dimensions_mm": {"width": 1200, "depth": 1400, "height": 2350},
        "max_allowable_flooring_thickness_mm": 12
    }
    r = client.post("/api/v1/quote/export", json=export_payload)
    assert r.status_code == 200, f"PDF export failed: {r.status_code}, {r.text}"
    assert r.headers["content-type"] == "application/pdf", f"Invalid content-type: {r.headers.get('content-type')}"
    assert r.content.startswith(b"%PDF-"), "Invalid PDF binary stream"
    print(f"[+] PDF Quotation export verified: {len(r.content)} bytes")

    print("\n[SUCCESS] All API, Rules Engine, Inpainting, and PDF Export tests PASSED!")

if __name__ == "__main__":
    run_tests()
