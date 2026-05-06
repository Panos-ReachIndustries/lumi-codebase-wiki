---
name: V2.BackgroundSubtraction
description: Counts and groups discrete objects (originally bacterial colonies) inside a circular ROI using adaptive thresholding plus auto-tuned parameters from a VGG16 + regressor.
type: module
graph_node: core:BackgroundSubtraction
sources:
  - { repo: Lumi-AI-Core, path: V2/BackgroundSubtraction/BackgroundSubtractionAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/BackgroundSubtraction/README.md }
tags: [v2-module]
---

# V2.BackgroundSubtraction

`BackgroundSubtraction` is the colony-counter / blob-counter. Given an image, a circular region of interest (`centreX`, `centreY`, `radius`), and either explicit thresholding parameters or learned ones, it returns the number of discrete objects, their contours, areas, and an OPTICS clustering of "groups" (e.g. distinct colony populations on a petri dish).

## What it does

The pipeline lives entirely inside `BackgroundSubtractionAnalyser` (`Lumi-AI-Core/V2/BackgroundSubtraction/BackgroundSubtractionAnalyser.py:28`):

1. Downscale to `maxWidth` (default 5120) if too large.
2. Mask everything outside the circular ROI to zero (`:298`).
3. (Optional) auto-tune adaptive-threshold params via VGG16 features + a joblib `MultiTargetRegressor` predicting `(invWin, invConst, inv)` (`:160-170`).
4. `cv2.adaptiveThreshold` + erode/dilate cycles to clean up noise.
5. `findContours`, filter by `area > 10`, run OPTICS clustering on `[cx, cy, area]` to bucket objects into groups.

## Public API

`BackgroundSubtractionAnalyser(input_data: dict)` — config: `weights`, `maxWidth=5120`, `enableBlur=False`, `clustMinSamples=0.15`, `clustXi=0.04`. Methods:

- `get_image_parameters({"image": ndarray})` returns `{invWin, invConst, inv}`.
- `get_thresholded_counts({"image", "centreX", "centreY", "radius", ...})` returns counts, contours, `colonyGroups`, etc.
- `annotate_image_with_counts({...})` returns `annotatedImage` (BGR) with coloured contours and labels.

All methods return V2 error dicts (`errorType`, `errorDesc`, `stackTrace`) on failure rather than raising.

## Input/output shape

This module does **not** speak the canonical `agreedDataSchema.md` detection schema — its outputs are colony-specific (`numObjects`, `numObjectPixels`, `colonyGroups`, `contours` as nested int lists for JSON-safe transport). See `BackgroundSubtractionAnalyser.py:360-393` for the full output dict.

## Dependencies on other V2 modules

None. Self-contained — uses Keras (VGG16), scikit-learn (OPTICS), OpenCV and Pillow for the `Poppins-Regular.ttf` font that ships next to the module.

## Used by which monitors

No direct importers in `Lumi-AI-Continuous/monitors/` at the time of writing — the module is exposed for use through the V2 façade and `exposed_functions.json`. Search for `V2.BackgroundSubtraction` across `monitors/` to confirm.

## Tests

- `Lumi-AI-Core/V2/BackgroundSubtraction/test_background_subtraction.py`

## Gotchas

- Without `weights`, `get_image_parameters` returns `BAD_INPUT` and you must pass `invWin`/`invConst`/`inv` manually to `get_thresholded_counts`.
- The font asset (`Poppins-Regular.ttf`) must sit next to the .py file or `__init__` raises. Don't move just one of the two files.
- `inv` is forced odd by the predictor (adaptive threshold requires odd window).

## See also

- [V2.Colours](Colours.md) — flexible region (box / mask / polygon) sampling primitive
- [V2.Detection](Detection.md) — when you want a learned detector instead of thresholding
- [agreedDataSchema](../data-schema.md)
- [V2.BasicOps](BasicOps.md) — `mask_to_polygons` for downstream contour handling
