import subprocess
import sys
import os

COMMITS = [
    # 1-5: Build & Configuration
    (
        ["frontend/package.json"],
        "build(deps): update frontend package dependencies"
    ),
    (
        ["frontend/package-lock.json"],
        "build(deps): update package-lock.json integrity hashes"
    ),
    (
        ["frontend/tsconfig.json"],
        "build(ts): exclude landing shaders from nextjs compilation"
    ),
    (
        ["frontend/next.config.ts"],
        "build(next): configure api and static reverse proxy rewrites"
    ),
    (
        ["backend/main.py"],
        "feat(backend): configure permissive cors headers for local origin proxy"
    ),

    # 6-7: Testing & Scenes
    (
        ["scripts/validate_catalog.py"],
        "test(catalog): harden catalog validation assertions and spec integrity"
    ),
    (
        ["data/scenes/scene_01_passenger/after_preview_change_mask.png"],
        "feat(scenes): add procedural change mask for scene 01 passenger cabin"
    ),
    (
        ["data/scenes/scene_01_passenger/after_preview.jpg"],
        "feat(scenes): update after preview synthesis render for passenger lift"
    ),

    # 8-12: WebGL Hero Runtime Assets
    (
        ["frontend/public/landing-pages/inner-green-assets/three.min.js"],
        "assets(webgl): import three.min.js runtime bundle"
    ),
    (
        ["frontend/public/landing-pages/inner-green-assets/lexend-latin.woff2"],
        "assets(fonts): add lexend latin woff2 font asset"
    ),
    (
        ["frontend/public/landing-pages/inner-green-assets/card-ethos.jpg"],
        "assets(landing): import card ethos background texture"
    ),
    (
        ["frontend/public/landing-pages/inner-green-assets/card-ecostove.jpg"],
        "assets(landing): import card ecostove tactile image"
    ),
    (
        ["frontend/public/landing-pages/inner-green-3d.html"],
        "feat(landing): integrate inner green 3d webgl scene template"
    ),

    # 13-23: Sketchbook Landing Assets
    (
        ["frontend/public/landing-pages/meng-to-sketchbook/bg-wash.jpg"],
        "assets(sketchbook): import botanical paper wash background"
    ),
    (
        [
            "frontend/public/landing-pages/meng-to-sketchbook/bloom.png",
            "frontend/public/landing-pages/meng-to-sketchbook/divider.png"
        ],
        "assets(sketchbook): import flora illustrations and bloom elements"
    ),
    (
        [
            "frontend/public/landing-pages/meng-to-sketchbook/botany-left.png",
            "frontend/public/landing-pages/meng-to-sketchbook/botany-right.png"
        ],
        "assets(sketchbook): import botanical foliage borders"
    ),
    (
        [
            "frontend/public/landing-pages/meng-to-sketchbook/botanic-gardens.png",
            "frontend/public/landing-pages/meng-to-sketchbook/buddha-tooth.png"
        ],
        "assets(sketchbook): import botanic gardens and buddha tooth sketches"
    ),
    (
        ["frontend/public/landing-pages/meng-to-sketchbook/gardens-by-the-bay.png"],
        "assets(sketchbook): import gardens by the bay illustration"
    ),
    (
        [
            "frontend/public/landing-pages/meng-to-sketchbook/joo-chiat.png",
            "frontend/public/landing-pages/meng-to-sketchbook/lau-pa-sat.png"
        ],
        "assets(sketchbook): import joo chiat and lau pa sat sketches"
    ),
    (
        [
            "frontend/public/landing-pages/meng-to-sketchbook/marina-bay-sands.png",
            "frontend/public/landing-pages/meng-to-sketchbook/marina-bay-skyline.png"
        ],
        "assets(sketchbook): import marina bay sands and skyline sketches"
    ),
    (
        [
            "frontend/public/landing-pages/meng-to-sketchbook/merlion.png",
            "frontend/public/landing-pages/meng-to-sketchbook/singapore-river.png"
        ],
        "assets(sketchbook): import merlion and singapore river sketches"
    ),
    (
        ["frontend/public/landing-pages/meng-to-sketchbook/instrument-serif.woff2"],
        "assets(fonts): import instrument serif regular woff2 font"
    ),
    (
        ["frontend/public/landing-pages/meng-to-sketchbook/instrument-serif-italic.woff2"],
        "assets(fonts): import instrument serif italic woff2 font"
    ),
    (
        ["frontend/public/landing-pages/meng-to-sketchbook/newsreader.woff2"],
        "assets(fonts): import newsreader editorial typography font"
    ),
    (
        ["frontend/public/landing-pages/meng-to-sketchbook.html"],
        "feat(sketchbook): import meng to sketchbook landing html page"
    ),

    # 26-30: ThreeUI Shaders & Controls
    (
        ["frontend/src/shaders/threeui.css"],
        "feat(shaders): implement threeui base styling definitions"
    ),
    (
        ["frontend/src/shaders/landing-pages/pageTypography.ts"],
        "feat(shaders): implement page typography definitions"
    ),
    (
        ["frontend/src/shaders/landing-pages/pageRecipes.ts"],
        "feat(shaders): implement page recipes and shader presets"
    ),
    (
        ["frontend/src/shaders/landing-pages/LandingPageFrame.tsx"],
        "feat(shaders): implement landing page frame wrapper component"
    ),
    (
        ["frontend/src/shaders/landing-pages/LandingPages.tsx"],
        "feat(shaders): implement landing pages registry component"
    ),

    # 31-36: Static Scenes Deployment
    (
        [
            "frontend/public/static/scenes/annotation.schema.json",
            "frontend/public/static/scenes/README.md"
        ],
        "feat(scenes): deploy annotation schema and readme docs"
    ),
    (
        [
            "frontend/public/static/scenes/custom_upload/cabin_view.jpg",
            "frontend/public/static/scenes/custom_upload/site_measurements.json"
        ],
        "feat(scenes): deploy custom upload scene template files"
    ),
    (
        [
            "frontend/public/static/scenes/scene_template/gold_annotations.json",
            "frontend/public/static/scenes/scene_template/site_measurements.json"
        ],
        "feat(scenes): deploy scene template gold annotations"
    ),
    (
        [
            "frontend/public/static/scenes/scene_01_passenger/cabin_view.jpg",
            "frontend/public/static/scenes/scene_01_passenger/raw.jpg"
        ],
        "feat(scenes): deploy passenger cabin scan images to public static"
    ),
    (
        [
            "frontend/public/static/scenes/scene_01_passenger/after_preview.jpg",
            "frontend/public/static/scenes/scene_01_passenger/after_preview_change_mask.png"
        ],
        "feat(scenes): deploy passenger scene after preview and change mask"
    ),
    (
        [
            "frontend/public/static/scenes/scene_01_passenger/calibrated_scene.json",
            "frontend/public/static/scenes/scene_01_passenger/depth_map.png",
            "frontend/public/static/scenes/scene_01_passenger/gold_annotations.json",
            "frontend/public/static/scenes/scene_01_passenger/site_measurements.json"
        ],
        "feat(scenes): deploy passenger depth map and photogrammetry config"
    ),
    (
        ["frontend/public/static/scenes/scene_01_passenger/masks/"],
        "feat(scenes): deploy passenger scene segmentation masks"
    ),

    # 38-39: Data Layer
    (
        ["frontend/src/data/fallbackCatalog.ts"],
        "feat(data): define fallback hardware catalog with all 17 lift skus and presets"
    ),

    # 40-44: Studio Assets
    (
        [
            "frontend/public/assets/studio/logo_mark.png",
            "frontend/public/assets/studio/elevai_logo.png"
        ],
        "assets(studio): add elevai logo marks and badges"
    ),
    (
        [
            "frontend/public/assets/studio/card_walls.jpg",
            "frontend/public/assets/studio/card_flooring.jpg"
        ],
        "assets(studio): add wall cladding and flooring finish card thumbnails"
    ),
    (
        [
            "frontend/public/assets/studio/card_ceiling.jpg",
            "frontend/public/assets/studio/card_cop.jpg"
        ],
        "assets(studio): add ceiling canopy and cop finish card thumbnails"
    ),
    (
        ["frontend/public/assets/studio/card_doors.jpg"],
        "assets(studio): add brushed stainless door cladding card thumbnail"
    ),
    (
        ["frontend/public/assets/studio/cabin_modernized.jpg"],
        "assets(studio): deploy clean modernized cabin preview viewport"
    ),
    (
        [
            "frontend/public/assets/studio/cabin_clean_resized.jpg",
            "frontend/public/assets/studio/cabin_clean_surface.jpg",
            "frontend/public/assets/studio/cabin_clean_test.jpg",
            "frontend/public/assets/studio/cabin_pure.jpg"
        ],
        "assets(studio): add clean reference surface and crops"
    ),
    (
        [
            "frontend/public/assets/studio/crop_im1.jpg",
            "frontend/public/assets/studio/crop_im2.jpg",
            "frontend/public/assets/studio/finishes_row.jpg",
            "frontend/public/assets/studio/thumb_ceiling.jpg",
            "frontend/public/assets/studio/thumb_cop.jpg",
            "frontend/public/assets/studio/thumb_doors.jpg",
            "frontend/public/assets/studio/thumb_flooring.jpg",
            "frontend/public/assets/studio/thumb_walls.jpg",
            "frontend/public/assets/studio/viewport_scene.jpg"
        ],
        "assets(studio): add architectural finish swatches and crops"
    ),

    # 46-50: Styles, Components & App Assembly
    (
        ["frontend/src/app/globals.css"],
        "style(theme): establish dark olive architectural palette and typography"
    ),
    (
        ["frontend/src/components/Scene.tsx"],
        "feat(ui): implement scene bridge component connecting 3d hero and app"
    ),
    (
        ["frontend/src/components/ElevaiStudio.tsx"],
        "feat(studio): implement elevai modernization studio component"
    ),
    (
        ["scripts/make_commits.py"],
        "chore(build): record multi-stage modernization commit choreography"
    ),
    (
        ["frontend/src/app/page.tsx"],
        "feat(app): configure app root page with interactive studio overlay"
    )
]

def main():
    print(f"Total structured commits planned: {len(COMMITS)}")
    assert len(COMMITS) == 50, f"Expected exactly 50 commits, got {len(COMMITS)}"

    success_count = 0
    for i, (files, msg) in enumerate(COMMITS, 1):
        print(f"[{i:02d}/50] Staging and committing: {msg}")
        
        # Add files
        add_cmd = ["git", "add"] + files
        res = subprocess.run(add_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  Warning on git add: {res.stderr.strip()}")

        # Check staged
        status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        staged = [l for l in status_res.stdout.splitlines() if l.startswith(('A ', 'M ', 'D ', 'R '))]
        if not staged:
            print(f"  Note: No diff staged for step {i}, continuing.")
            continue

        commit_cmd = ["git", "commit", "-m", msg]
        res = subprocess.run(commit_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  Error on git commit: {res.stderr.strip()}")
            continue

        success_count += 1

    print(f"\nCompleted {success_count} commits successfully!")
    
    # Final status
    status_final = subprocess.run(["git", "status", "-s"], capture_output=True, text=True)
    out = status_final.stdout.strip()
    if out:
        print("Remaining unstaged/untracked:\n" + out)
    else:
        print("Working directory completely clean!")

if __name__ == "__main__":
    main()
