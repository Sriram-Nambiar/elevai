import os
import json
import hashlib
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

class CabinInpainter:
    """
    Procedural, perspective-aware elevator modernization inpainter.
    Applies cv2.warpPerspective to project synthetic architectural textures
    (wall panels, coin rubber / granite tile flooring, perimeter LED ceiling,
    and gloss architectural COP column with backlit TFT '07' display and dual buttons)
    onto elevator cabin surfaces while preserving ambient lighting and shadows via
    alpha-weighted blending (cv2.addWeighted).
    """

    def __init__(self, catalog_path: Optional[str] = None):
        if catalog_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            catalog_path = os.path.join(base_dir, "data", "catalog", "catalog.json")

        self.catalog = {}
        if os.path.exists(catalog_path):
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("catalog_items", []) if isinstance(data, dict) else data
            for item in items:
                sku = item.get("sku_id") or item.get("sku") or item.get("id")
                if sku:
                    self.catalog[sku] = item

    # -------------------------------------------------------------------------
    # Procedural Texture Synthesizers
    # -------------------------------------------------------------------------

    def create_brushed_metal_texture(
        self,
        width: int = 600,
        height: int = 800,
        base_color: Tuple[int, int, int] = (210, 215, 220),
        tint: Optional[Tuple[int, int, int]] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Generates fine vertical brushed stainless steel with directional sheen and panel seams."""
        rng = rng or np.random.default_rng()
        tex = np.full((height, width, 3), base_color, dtype=np.float32)

        # 1. Vertical hairline streaks (1D noise broadcast horizontally)
        streak_noise = rng.normal(0, 14.0, (height, 1, 1)).astype(np.float32)
        tex += streak_noise

        # 2. High-frequency 2D micro-scratch grain
        micro_grain = rng.normal(0, 5.0, (height, width, 1)).astype(np.float32)
        tex += micro_grain

        # 3. Directional metallic sheen (horizontal reflection bands)
        x = np.linspace(0, np.pi, width)
        sheen = (np.sin(x * 1.5) * 18.0).reshape(1, width, 1).astype(np.float32)
        tex += sheen

        # 4. Color tinting (e.g. bronze or titanium)
        if tint is not None:
            tint_arr = np.array(tint, dtype=np.float32).reshape(1, 1, 3)
            tex = tex * (tint_arr / 255.0)

        # 5. Vertical architectural panel reveals / seams
        seam_interval = max(120, width // 3)
        for sx in range(seam_interval, width - 10, seam_interval):
            cv2.line(tex, (sx, 0), (sx, height), (30, 30, 35), 2)
            cv2.line(tex, (sx + 2, 0), (sx + 2, height), (240, 245, 250), 1)

        return np.clip(tex, 0, 255).astype(np.uint8)

    def create_wood_texture(
        self,
        width: int = 600,
        height: int = 800,
        wood_type: str = "oak",
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Generates architectural natural oak or fluted walnut wood textures."""
        if wood_type == "walnut":
            base = np.array([45, 65, 95], dtype=np.float32)  # Dark walnut BGR
            rib_width = 30
            tex = np.full((height, width, 3), base, dtype=np.float32)
            # Add 3D fluted ribs
            for rx in range(0, width, rib_width):
                rib_x = np.linspace(0, np.pi, min(rib_width, width - rx))
                shading = (np.sin(rib_x) * 35.0 - 15.0).reshape(1, -1, 1)
                tex[:, rx:rx + len(rib_x)] += shading
                # Shadow groove
                cv2.line(tex, (rx, 0), (rx, height), (20, 30, 45), 2)
        else:
            base = np.array([105, 160, 215], dtype=np.float32)  # Rift oak BGR
            tex = np.full((height, width, 3), base, dtype=np.float32)
            # Gentle sinusoidal vertical grain
            y_indices = np.arange(height).reshape(-1, 1)
            x_indices = np.arange(width).reshape(1, -1)
            grain = np.sin(x_indices * 0.12 + np.sin(y_indices * 0.02) * 4.0) * 18.0
            tex += grain[:, :, np.newaxis]
            fine_noise = (rng or np.random.default_rng()).normal(0, 4.0, (height, width, 1))
            tex += fine_noise

        return np.clip(tex, 0, 255).astype(np.uint8)

    def create_coin_rubber_texture(
        self,
        width: int = 700,
        height: int = 700,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Generates durable charcoal rubber flooring with 3D raised coin-studs."""
        # Dark charcoal matte base
        tex = np.full((height, width, 3), (32, 34, 36), dtype=np.uint8)

        # Micro rubber grain
        grain = (rng or np.random.default_rng()).normal(0, 3.5, (height, width, 3)).astype(np.float32)
        tex = np.clip(tex.astype(np.float32) + grain, 0, 255).astype(np.uint8)

        # Grid of raised coin studs
        stud_spacing = 38
        stud_radius = 11

        for y in range(stud_spacing // 2, height, stud_spacing):
            for x in range(stud_spacing // 2, width, stud_spacing):
                # Dropshadow (bottom-right crescent)
                cv2.circle(tex, (x + 2, y + 2), stud_radius, (16, 17, 19), -1)
                # Stud base
                cv2.circle(tex, (x, y), stud_radius, (42, 45, 48), -1)
                # Bevel highlight ring (top-left crescent)
                cv2.ellipse(tex, (x, y), (stud_radius, stud_radius), 0, 180, 315, (75, 80, 85), 2)
                # Subtle flat center cap
                cv2.circle(tex, (x, y), stud_radius - 3, (48, 52, 56), -1)
                cv2.circle(tex, (x - 1, y - 1), 3, (78, 83, 88), -1)

        return tex

    def create_granite_tile_texture(
        self,
        width: int = 700,
        height: int = 700,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Generates honed black granite tile floor with fine stone flecks and brass transition joints."""
        tex = np.full((height, width, 3), (26, 28, 30), dtype=np.float32)

        # Multi-scale crystalline granite noise
        rng = rng or np.random.default_rng()
        speckles = rng.choice([0, 20, 45, 75], size=(height, width, 1), p=[0.72, 0.18, 0.08, 0.02])
        tex += speckles
        tex += rng.normal(0, 4.0, (height, width, 3))

        tex = np.clip(tex, 0, 255).astype(np.uint8)

        # Tile grid joints
        tile_size = 140
        for gx in range(0, width, tile_size):
            cv2.line(tex, (gx, 0), (gx, height), (14, 15, 17), 2)
            cv2.line(tex, (gx + 1, 0), (gx + 1, height), (60, 85, 110), 1)  # subtle brass accent
        for gy in range(0, height, tile_size):
            cv2.line(tex, (0, gy), (width, gy), (14, 15, 17), 2)
            cv2.line(tex, (0, gy + 1), (width, gy + 1), (60, 85, 110), 1)

        return tex

    def create_perimeter_ceiling_texture(
        self,
        width: int = 700,
        height: int = 500,
        style: str = "perimeter_led",
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Generates perimeter indirect LED cove canopy or diffused acrylic light ceiling."""
        if style == "acrylic":
            # Seamless bright diffused acrylic
            tex = np.full((height, width, 3), (242, 246, 250), dtype=np.uint8)
            # Thin border frame
            cv2.rectangle(tex, (0, 0), (width - 1, height - 1), (50, 55, 60), 6)
            # Soft radial glow center
            glow = np.zeros((height, width), dtype=np.float32)
            cv2.circle(glow, (width // 2, height // 2), max(width, height) // 2, 1.0, -1)
            glow = cv2.GaussianBlur(glow, (99, 99), 0)
            tex = cv2.addWeighted(tex, 0.85, (glow[:, :, np.newaxis] * 255).astype(np.uint8), 0.15, 0)
            return tex

        # Perimeter indirect LED cove canopy
        tex = np.full((height, width, 3), (35, 38, 42), dtype=np.uint8)

        # Outer cove trough - intense warm/neutral indirect LED glow
        led_glow = np.zeros((height, width, 3), dtype=np.float32)
        # Perimeter glow bands (BGR warm neutral white 4000K: [215, 235, 255])
        glow_color = (215.0, 235.0, 255.0)
        trough_margin = 40

        # Draw glowing perimeter band
        cv2.rectangle(
            led_glow,
            (trough_margin // 2, trough_margin // 2),
            (width - trough_margin // 2, height - trough_margin // 2),
            glow_color,
            trough_margin
        )
        led_glow = cv2.GaussianBlur(led_glow, (55, 55), 0)

        # Center suspended floating drop ceiling plate (brushed stainless)
        plate_w = width - (trough_margin * 2)
        plate_h = height - (trough_margin * 2)
        if plate_w > 10 and plate_h > 10:
            plate = self.create_brushed_metal_texture(plate_w, plate_h, base_color=(190, 195, 200), rng=rng)
            # Plate shadow reveal
            cv2.rectangle(
                led_glow,
                (trough_margin - 3, trough_margin - 3),
                (width - trough_margin + 3, height - trough_margin + 3),
                (10, 12, 15),
                4
            )
            tex[trough_margin:trough_margin + plate_h, trough_margin:trough_margin + plate_w] = plate

        tex = cv2.addWeighted(tex, 0.7, np.clip(led_glow, 0, 255).astype(np.uint8), 0.3, 0)
        return tex

    def create_cop_overlay(
        self,
        width: int = 140,
        height: int = 380,
        sku_id: str = "COP-COL-TFT",
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Synthesizes a modern architectural COP column featuring:
        - Sleek brushed titanium / stainless steel bevelled column
        - High-resolution backlit color TFT digital floor indicator displaying '07' & status arrow '^'
        - Dual illuminated micro-motion push buttons with vibrant LED halo rings and tactile braille
        """
        # Column body
        cop = np.full((height, width, 3), (205, 210, 215), dtype=np.float32)
        # Vertical column brush grain
        brush = (rng or np.random.default_rng()).normal(0, 8.0, (height, 1, 1)).astype(np.float32)
        cop += brush
        # Side bevels
        cop[:, 0:4] = [70, 75, 80]
        cop[:, 4:8] = [130, 135, 140]
        cop[:, -8:-4] = [130, 135, 140]
        cop[:, -4:] = [70, 75, 80]
        cop = np.clip(cop, 0, 255).astype(np.uint8)

        # ---------------------------------------------------------------------
        # 1. Backlit TFT Digital Floor Display ("07" + Direction Arrow)
        # ---------------------------------------------------------------------
        screen_top = 18
        screen_h = int(height * 0.24)
        screen_left = 12
        screen_right = width - 12

        # TFT Bezel
        cv2.rectangle(cop, (screen_left - 2, screen_top - 2), (screen_right + 2, screen_top + screen_h + 2), (25, 26, 28), -1)
        # Backlit Screen (Deep sapphire blue display background)
        cv2.rectangle(cop, (screen_left, screen_top), (screen_right, screen_top + screen_h), (55, 30, 12), -1)

        # TFT Screen Sub-glow
        tft_center_x = (screen_left + screen_right) // 2
        tft_center_y = screen_top + (screen_h // 2)

        # Up Direction Arrow "^" (Emerald / Cyan illuminated)
        cv2.putText(
            cop,
            "^",
            (tft_center_x - 7, screen_top + 20),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (240, 220, 70),
            2,
            cv2.LINE_AA
        )

        # Large Digital Floor Numeral "07"
        cv2.putText(
            cop,
            "07",
            (tft_center_x - 26, tft_center_y + 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.95,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        # Subtitle Status
        cv2.putText(
            cop,
            "ELEVAI",
            (tft_center_x - 18, screen_top + screen_h - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.28,
            (180, 210, 230),
            1,
            cv2.LINE_AA
        )

        # ---------------------------------------------------------------------
        # 2. Dual Illuminated Push Button Columns
        # ---------------------------------------------------------------------
        btn_start_y = screen_top + screen_h + 16
        col1_x = width // 3
        col2_x = (width * 2) // 3
        btn_radius = 9
        row_spacing = 26

        button_pairs = [
            ("7", "6"),
            ("5", "4"),
            ("3", "2"),
            ("1", "G"),
            ("B", "*"),
            ("<|>", ">|<")
        ]

        max_rows = min(len(button_pairs), (height - btn_start_y - 20) // row_spacing)

        for row_idx in range(max_rows):
            by = btn_start_y + (row_idx * row_spacing)
            lbl1, lbl2 = button_pairs[row_idx]

            for bx, lbl in [(col1_x, lbl1), (col2_x, lbl2)]:
                # Glowing LED Halo Ring
                halo_color = (255, 195, 70) if lbl == "7" else (240, 235, 220)
                cv2.circle(cop, (bx, by), btn_radius + 2, halo_color, 1, cv2.LINE_AA)
                # Outer metal button bezel
                cv2.circle(cop, (bx, by), btn_radius, (75, 80, 85), 1, cv2.LINE_AA)
                # Button face
                btn_face_color = (245, 175, 45) if lbl == "7" else (40, 44, 48)
                cv2.circle(cop, (bx, by), btn_radius - 1, btn_face_color, -1)

                # Numeral / Symbol
                font_scale = 0.28 if len(lbl) > 1 else 0.35
                text_color = (15, 15, 20) if lbl == "7" else (225, 230, 235)
                offset_x = -6 if len(lbl) > 1 else -4
                cv2.putText(
                    cop,
                    lbl,
                    (bx + offset_x, by + 4),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    text_color,
                    1,
                    cv2.LINE_AA
                )

                # Micro Braille tactile dots indicator next to button
                braille_x = bx + btn_radius + 3
                if braille_x + 3 < width:
                    cv2.circle(cop, (braille_x, by - 2), 1, (130, 135, 140), -1)
                    cv2.circle(cop, (braille_x, by + 2), 1, (130, 135, 140), -1)

        # Bottom Key Switch / Service reveal
        key_y = height - 16
        cv2.circle(cop, (width // 2, key_y), 4, (45, 48, 52), -1)
        cv2.circle(cop, (width // 2, key_y), 2, (180, 185, 190), -1)

        return cop

    # -------------------------------------------------------------------------
    # Spatial Geometry & Perspective Mapping
    # -------------------------------------------------------------------------

    def extract_cabin_polygons(
        self,
        scene_dir: str,
        img_w: int,
        img_h: int
    ) -> Tuple[Dict[str, np.ndarray], str]:
        """
        Locates cabin surfaces (back_wall, left_wall, right_wall, floor, ceiling, cop)
        using scene annotations, detector boxes, or clearly reported fallbacks.
        """
        gold_path = os.path.join(scene_dir, "gold_annotations.json")
        detections_path = os.path.join(scene_dir, "masks", "detected_components.json")

        back_wall_box = None
        cop_box = None
        ceiling_box = None
        floor_box = None
        geometry_source = "generic_fallback_estimate"

        if os.path.exists(gold_path):
            with open(gold_path, "r", encoding="utf-8") as f:
                gold_data = json.load(f)
            geometry_source = f"{gold_data.get('review_status', 'unverified')}_annotations"
            for ann in gold_data.get("annotations", []):
                lbl = ann.get("label") or ann.get("category_id")
                ymin, xmin, ymax, xmax = ann.get("bbox_normalized", [0, 0, 0, 0])
                box = [int(ymin * img_h), int(xmin * img_w), int(ymax * img_h), int(xmax * img_w)]
                if lbl in ["back_wall", "wall_panel"]:
                    back_wall_box = box
                elif lbl in ["car_operating_panel", "cop"]:
                    cop_box = box
                elif lbl in ["ceiling", "ceiling_lighting"]:
                    ceiling_box = box
                elif lbl in ["floor", "flooring"]:
                    floor_box = box

        # Fallback to detected components if missing
        if (back_wall_box is None or cop_box is None) and os.path.exists(detections_path):
            with open(detections_path, "r", encoding="utf-8") as f:
                det_data = json.load(f)
            for comp in det_data.get("components", []):
                cat = comp.get("category")
                box = comp.get("bbox_pixel")
                if cat == "wall_panel" and back_wall_box is None:
                    back_wall_box = box
                elif cat == "cop" and cop_box is None:
                    cop_box = box
            if back_wall_box is not None and cop_box is not None:
                geometry_source = "detector_bounding_boxes"

        # Sensible geometric fallbacks if boxes not detected
        if back_wall_box is None:
            back_wall_box = [int(img_h * 0.19), int(img_w * 0.28), int(img_h * 0.77), int(img_w * 0.72)]
        if cop_box is None:
            cop_box = [int(img_h * 0.41), int(img_w * 0.75), int(img_h * 0.64), int(img_w * 0.81)]

        bw_ymin, bw_xmin, bw_ymax, bw_xmax = back_wall_box
        cop_ymin, cop_xmin, cop_ymax, cop_xmax = cop_box

        # Define 4-point perspective quadrilaterals for each plane:
        polygons = {
            "back_wall": np.float32([
                [bw_xmin, bw_ymin],
                [bw_xmax, bw_ymin],
                [bw_xmax, bw_ymax],
                [bw_xmin, bw_ymax]
            ]),
            "left_wall": np.float32([
                [0, 0],
                [bw_xmin, bw_ymin],
                [bw_xmin, bw_ymax],
                [0, img_h - 1]
            ]),
            "right_wall": np.float32([
                [bw_xmax, bw_ymin],
                [img_w - 1, 0],
                [img_w - 1, img_h - 1],
                [bw_xmax, bw_ymax]
            ]),
            "ceiling": np.float32([
                [0, 0],
                [img_w - 1, 0],
                [bw_xmax, bw_ymin],
                [bw_xmin, bw_ymin]
            ]),
            "floor": np.float32([
                [bw_xmin, bw_ymax],
                [bw_xmax, bw_ymax],
                [img_w - 1, img_h - 1],
                [0, img_h - 1]
            ]),
            "cop": np.float32([
                [cop_xmin, cop_ymin],
                [cop_xmax, cop_ymin],
                [cop_xmax, cop_ymax],
                [cop_xmin, cop_ymax]
            ])
        }

        if back_wall_box is None or cop_box is None:
            geometry_source = "generic_fallback_estimate"
        return polygons, geometry_source

    # -------------------------------------------------------------------------
    # Core Rendering Engine
    # -------------------------------------------------------------------------

    def render(
        self,
        scene_dir: str,
        selected_skus: List[str],
        output_filename: str = "after_preview.jpg"
    ) -> Dict[str, Any]:
        """
        Executes perspective texture synthesis and compositing for the specified SKUs.
        Writes after_preview.jpg to scene_dir and returns execution metadata.
        """
        cabin_img_path = os.path.join(scene_dir, "cabin_view.jpg")
        if not os.path.exists(cabin_img_path):
            cabin_img_path = os.path.join(scene_dir, "raw.jpg")

        if not os.path.exists(cabin_img_path):
            raise FileNotFoundError(f"No cabin image found in {scene_dir}")

        base_img = cv2.imread(cabin_img_path)
        if base_img is None:
            raise ValueError(f"Could not read cabin image: {cabin_img_path}")
        img_h, img_w, _ = base_img.shape

        # Extract ambient lighting (luminance map) for photorealistic shading preservation
        lab = cv2.cvtColor(base_img, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0].astype(np.float32)
        ambient_mult = np.clip(l_channel / 128.0, 0.35, 1.45)[:, :, np.newaxis]

        # Extract perspective polygons
        polygons, geometry_source = self.extract_cabin_polygons(scene_dir, img_w, img_h)

        result_img = base_img.copy()

        # Categorize active SKUs
        selected_items = {}
        unknown_skus = []
        for sku in selected_skus:
            if sku in self.catalog:
                item = self.catalog[sku]
                cat = item.get("category", "unknown")
                if cat in selected_items:
                    raise ValueError(f"Only one SKU per category can be rendered; duplicate category '{cat}'.")
                selected_items[cat] = item
            else:
                unknown_skus.append(sku)
        if unknown_skus:
            raise ValueError(f"Unknown catalog SKU(s): {', '.join(unknown_skus)}")

        seed_material = f"{os.path.basename(scene_dir)}:{'|'.join(sorted(selected_skus))}"
        seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        change_mask = np.zeros((img_h, img_w), dtype=np.uint8)

        rendered_components = []

        # 1. Render Wall Panels (Back, Left, and Right walls)
        wall_item = selected_items.get("wall_panel")
        if wall_item:
            sku = wall_item.get("sku_id")
            mat = wall_item.get("visual_attributes", {}).get("material", "")

            if "wood" in mat or "timber" in mat or "laminate" in mat:
                wood_type = "walnut" if "walnut" in sku.lower() else "oak"
                wall_tex = self.create_wood_texture(600, 800, wood_type=wood_type, rng=rng)
            elif "bronze" in mat or "brz" in sku.lower():
                wall_tex = self.create_brushed_metal_texture(600, 800, base_color=(120, 150, 190), tint=(140, 170, 220), rng=rng)
            elif "black" in sku.lower() or "pvd" in mat:
                wall_tex = self.create_brushed_metal_texture(600, 800, base_color=(40, 42, 45), rng=rng)
            elif "glass" in mat:
                wall_tex = np.full((800, 600, 3), (242, 245, 248), dtype=np.uint8)
                for jx in [200, 400]:
                    cv2.line(wall_tex, (jx, 0), (jx, 800), (190, 195, 200), 2)
            else:
                wall_tex = self.create_brushed_metal_texture(600, 800, base_color=(205, 210, 215), rng=rng)

            tex_h, tex_w, _ = wall_tex.shape
            src_pts = np.float32([[0, 0], [tex_w, 0], [tex_w, tex_h], [0, tex_h]])

            for wall_name in ["back_wall", "left_wall", "right_wall"]:
                dst_pts = polygons[wall_name]
                M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped = cv2.warpPerspective(wall_tex, M, (img_w, img_h), flags=cv2.INTER_LINEAR)

                mask = np.zeros((img_h, img_w), dtype=np.uint8)
                cv2.fillPoly(mask, [dst_pts.astype(np.int32)], 255)

                shaded_warped = np.clip(warped.astype(np.float32) * ambient_mult, 0, 255).astype(np.uint8)

                alpha = 0.82
                blended = cv2.addWeighted(shaded_warped, alpha, result_img, 1.0 - alpha, 0)
                result_img[mask > 0] = blended[mask > 0]
                change_mask[mask > 0] = 255

            rendered_components.append("wall_panel")

        # 2. Render Flooring (Coin Rubber / Granite Tiles)
        floor_item = selected_items.get("flooring")
        if floor_item:
            sku = floor_item.get("sku_id")
            if "coin" in sku.lower() or "rub" in sku.lower():
                floor_tex = self.create_coin_rubber_texture(700, 700, rng=rng)
            else:
                floor_tex = self.create_granite_tile_texture(700, 700, rng=rng)

            tex_h, tex_w, _ = floor_tex.shape
            src_pts = np.float32([[0, 0], [tex_w, 0], [tex_w, tex_h], [0, tex_h]])
            dst_pts = polygons["floor"]

            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_floor = cv2.warpPerspective(floor_tex, M, (img_w, img_h), flags=cv2.INTER_LINEAR)

            floor_mask = np.zeros((img_h, img_w), dtype=np.uint8)
            cv2.fillPoly(floor_mask, [dst_pts.astype(np.int32)], 255)

            shaded_floor = np.clip(warped_floor.astype(np.float32) * ambient_mult, 0, 255).astype(np.uint8)

            alpha = 0.88
            blended_floor = cv2.addWeighted(shaded_floor, alpha, result_img, 1.0 - alpha, 0)
            result_img[floor_mask > 0] = blended_floor[floor_mask > 0]
            change_mask[floor_mask > 0] = 255

            rendered_components.append("flooring")

        # 3. Render Ceiling Lighting (Perimeter LED / Acrylic Diffuser)
        ceil_item = selected_items.get("ceiling_lighting")
        if ceil_item:
            sku = ceil_item.get("sku_id")
            style = "acrylic" if "acrylic" in sku.lower() else "perimeter_led"
            ceil_tex = self.create_perimeter_ceiling_texture(700, 500, style=style, rng=rng)

            tex_h, tex_w, _ = ceil_tex.shape
            src_pts = np.float32([[0, 0], [tex_w, 0], [tex_w, tex_h], [0, tex_h]])
            dst_pts = polygons["ceiling"]

            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_ceil = cv2.warpPerspective(ceil_tex, M, (img_w, img_h), flags=cv2.INTER_LINEAR)

            ceil_mask = np.zeros((img_h, img_w), dtype=np.uint8)
            cv2.fillPoly(ceil_mask, [dst_pts.astype(np.int32)], 255)

            alpha = 0.90
            blended_ceil = cv2.addWeighted(warped_ceil, alpha, result_img, 1.0 - alpha, 0)
            result_img[ceil_mask > 0] = blended_ceil[ceil_mask > 0]
            change_mask[ceil_mask > 0] = 255

            rendered_components.append("ceiling_lighting")

        # 4. Render Car Operating Panel (Gloss column + TFT "07" + Dual Buttons)
        cop_item = selected_items.get("car_operating_panel")
        if cop_item:
            sku = cop_item.get("sku_id")
            cop_tex = self.create_cop_overlay(140, 420, sku_id=sku, rng=rng)

            tex_h, tex_w, _ = cop_tex.shape
            src_pts = np.float32([[0, 0], [tex_w, 0], [tex_w, tex_h], [0, tex_h]])
            dst_pts = polygons["cop"]

            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_cop = cv2.warpPerspective(cop_tex, M, (img_w, img_h), flags=cv2.INTER_LINEAR)

            cop_mask = np.zeros((img_h, img_w), dtype=np.uint8)
            cv2.fillPoly(cop_mask, [dst_pts.astype(np.int32)], 255)

            shaded_cop = np.clip(warped_cop.astype(np.float32) * (0.8 + 0.25 * ambient_mult), 0, 255).astype(np.uint8)

            alpha = 0.92
            blended_cop = cv2.addWeighted(shaded_cop, alpha, result_img, 1.0 - alpha, 0)
            result_img[cop_mask > 0] = blended_cop[cop_mask > 0]
            change_mask[cop_mask > 0] = 255

            rendered_components.append("car_operating_panel")

        # Save output image
        output_path = os.path.join(scene_dir, output_filename)
        cv2.imwrite(output_path, result_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        mask_filename = os.path.splitext(output_filename)[0] + "_change_mask.png"
        change_mask_path = os.path.join(scene_dir, mask_filename)
        cv2.imwrite(change_mask_path, change_mask)
        not_rendered = sorted(set(selected_items) - {"wall_panel", "flooring", "ceiling_lighting", "car_operating_panel"})

        return {
            "status": "success",
            "scene_dir": scene_dir,
            "output_path": output_path,
            "output_filename": output_filename,
            "rendered_components": rendered_components,
            "selected_skus": selected_skus,
            "change_mask_filename": mask_filename,
            "changed_pixel_fraction": round(float(np.count_nonzero(change_mask)) / (img_h * img_w), 4),
            "geometry_source": geometry_source,
            "review_required": geometry_source != "verified_annotations" or bool(not_rendered),
            "not_rendered_categories": not_rendered,
            "visual_disclaimer": "Procedural material concept only. Surface masks may approximate geometry; verify all changes against site measurements and the actual product."
        }
