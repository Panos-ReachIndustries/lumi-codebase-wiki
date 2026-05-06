---
name: V2.ThinLayerChromatography
description: Analyses thin-layer chromatography plates from a still image — detects plates, lanes, and spots; returns Rf values and visualisations.
type: module
graph_node: core:ThinLayerChromatography
sources:
  - { repo: Lumi-AI-Core, path: V2/ThinLayerChromatography/ThinLayerChromatography.py }
  - { repo: Lumi-AI-Core, path: V2/ThinLayerChromatography/processor.py }
  - { repo: Lumi-AI-Core, path: V2/ThinLayerChromatography/plate_detector.py }
  - { repo: Lumi-AI-Core, path: V2/ThinLayerChromatography/analyzer.py }
  - { repo: Lumi-AI-Core, path: V2/ThinLayerChromatography/visualizer.py }
tags: [v2-module]
---

# V2.ThinLayerChromatography

`ThinLayerChromatography` (TLC) is a still-image analyser that looks at a chromatography plate photo and reports where each spot is, in which lane, and at what Rf (retardation factor). Unlike most V2 modules it does not consume a video stream — it operates on file paths.

## What it does

The class wraps a `TLCProcessor` (`Lumi-AI-Core/V2/ThinLayerChromatography/ThinLayerChromatography.py:18`). The pipeline:

1. **Plate detection** — `plate_detector.py` finds plates in the image. Two backends: rectangle/edge detection (`rectDetection`) or a YOLOX model (`yoloxDetection`). Multi-plate images are supported via `processAllPlates`.
2. **Lane analysis** — `analyzer.py` finds lanes either from baseline dashes drawn on the plate or via automatic detection.
3. **Spot detection** — profile-based (1D intensity profile peak finding) or contour-based, configurable via `analysis.spotDetection.method`.
4. **Rf calculation** — distance from origin to spot divided by distance from origin to solvent front.
5. **Visualisation** — `visualizer.py` writes annotated PNGs (lanes, spots, Rf labels, debug overlays).

## Public API

All V2-style dict-in / dict-out (`Lumi-AI-Core/V2/ThinLayerChromatography/ThinLayerChromatography.py:52`):

- `ThinLayerChromatography({"config": {...}})` — init with a config covering `detection`, `analysis`, `visualization`, `logging`.
- `process({"imagePath", "nLanes"?, "debugOptions"?})` — single plate; returns `{plateBgr, analysis: {laneResults, spots, originY, frontY, baselineDashes, …}}`.
- `processAllPlates({"imagePath", ...})` — multi-plate; returns `{plates: [...], originalImage}`.
- `saveVisualizations({"results", "outputDir", "plateIndex"?, "saveDebugImages"?})` — write PNGs to disk.

## Input / output

In: image path on disk plus a config dict. Out: an analysis dict; failures return `{"errorType": "BAD_INPUT" | "INTERNAL_ERROR", "errorDesc", "stackTrace"}` rather than raising (except `__init__`, which raises `ValueError`).

## Dependencies on other V2 modules

None — TLC is self-contained. Vendored helpers in `geometry_utils.py` and `logging_utils.py`. Hard deps: `opencv-python`, `numpy`, `matplotlib`, `scipy` (peak finding). Optional YOLOX assets live alongside the module under `TLC_AI/`.

## Used by

Lab-bench monitors that watch a TLC workflow and need Rf reporting. Currently consumed via the custom agent rather than direct imports from other V2 modules.

## Tests

- `Lumi-AI-Core/V2/ThinLayerChromatography/test_thin_layer_chromatography.py`

## Gotchas

- `imagePath` must point to a real file the process can read — there is no in-memory `np.ndarray` entry point.
- The config tree is deep; if you skip the `logging` or `visualization` sub-dicts you can hit surprising defaults. Use `tlc_config.json` as a starting template.
- `process` errors out (rather than auto-falling-back) when multiple plates are present; use `processAllPlates`.

## See also

- [V2.Detection](Detection.md) — for the unified detection contract (TLC predates it for plate detection)
- [agreedDataSchema.md](../data-schema.md)
