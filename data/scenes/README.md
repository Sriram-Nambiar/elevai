# Scene data and annotations

Each scene is a separate directory containing `cabin_view.jpg` (or `raw.jpg`), `site_measurements.json`, and `gold_annotations.json`. Use `scene_template/` as a starting point. Keep one scene completely held out from any prompt or model tuning.

## Annotation convention

`bbox_normalized` uses `[top, left, bottom, right]`, each in the inclusive range 0–1. Labels use the challenge categories in `annotation.schema.json`. Record partially visible or occluded components rather than silently treating the visible fragment as a complete component. Mark annotations `verified` only after a human has checked every label and box against the image.

## Measurement convention

Record measured values in millimetres and identify their source in the scene notes. Leave unknown values `null`; do not copy a different cabin's dimensions into a new scene. A single image's estimated depth is not a substitute for a site measurement.

## Image source and privacy

Record image provenance and the license or permission that allows the image to be used and shared. Remove faces, addresses, building identifiers, and other private details before committing a site image. Never describe generated or unverified images as real measured sites.

The repository currently contains one prepared demonstration scene. The upload workspace is not a second verified dataset; additional benchmark scenes must be supplied, measured, and annotated before accuracy claims are made.
