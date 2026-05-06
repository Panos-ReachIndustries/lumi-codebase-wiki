---
name: V2.Vessels
description: Container detection, segmentation, phase-line detection, height-to-volume conversion, and 3D rendering for lab vessels.
type: module
graph_node: core:Vessels
sources:
  - { repo: Lumi-AI-Core, path: V2/Vessels/VesselAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/VesselDetector.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/LiquidAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/PhaseAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/HeightEstimator.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/VolumeConverter.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/ContainerVisualizer.py }
tags: [v2-module]
---

# V2.Vessels

`Vessels` is the V2 module that turns "there's a beaker in the frame" into "the beaker is 60% full and contains 15 mL". It is a small constellation of analysers (vessel mask, liquid mask, phase boundaries, height, volume, 3D rendering) sharing the V2 dict-in/dict-out pattern.

## What it does

Six analysers, each instantiable on its own:

- **`VesselDetectorV2`** (`Lumi-AI-Core/V2/Vessels/VesselDetector.py:16`) — coarse vessel segmentation via the bundled `FCN_NetModel`, refined by SAM2 prompts.
- **`VesselAnalyser`** (`Lumi-AI-Core/V2/Vessels/VesselAnalyser.py:11`) — SAM2-driven mask generation from a points/box/mask prompt; the workhorse for getting clean per-vessel masks.
- **`LiquidAnalyser`** (`LiquidAnalyser.py`) — post-processes a liquid mask: gravity-aware row fill (`fill_liquid_within_vessel`), constrain to vessel (`remove_liquid_outside_vessel`), pixel-to-mL conversion (`calculate_volume_from_mask`).
- **`PhaseAnalyser`** (`PhaseAnalyser.py`) — finds up to two horizontal phase lines (oil/water boundaries) in an image or polygon ROI.
- **`HeightEstimator`** (`HeightEstimator.py`) — maps a 2D point on a vessel crop to a 0-1 height percentage given roll/pitch.
- **`VolumeConverter`** (`VolumeConverter.py`) — turns a height percentage into millilitres for `vial`/`cylinder` (linear), `ball`/`sphere` (non-linear), `volumetric_flask` (multi-section) containers.
- **`ContainerVisualizer`** (`ContainerVisualizer.py`) — `pyrender`-based 3D mock-ups using STL meshes in `Assets/`.

## Public API

V2 dict pattern across the board: `Cls(input_data)` to construct, then methods like `generate_vessel_mask`, `process_image`, `convert_volume`, `generate_visualization`. Errors return `{"errorType": "BAD_INPUT" | "INTERNAL_ERROR", "errorDesc", "stackTrace"}`. Full per-method tables live in `Lumi-AI-Core/V2/Vessels/README.md`.

## Input / output

In: BGR `np.ndarray` images, plus prompt dicts (points, box, polygon) or numeric inputs (height %, volume). Out: binary masks (`uint8` 0/255), polygons, volumes in mL, or rendered RGB images. Vessel masks plug into [V2.Detection](Detection.md)-shaped consumers when wrapped through the segmentation contract in [agreedDataSchema.md](../data-schema.md).

## Dependencies on other V2 modules

- [V2.SegmentAnything](SegmentAnything.md) — SAM2 is the backbone for mask generation.
- External: `torch`, `opencv-python`, `numpy`, `scipy`, `scikit-image`, `numba`, `shapely`, `trimesh`, `pyrender`. The bundled `FCN_NetModel.py` carries weights via the `fcn_weights` path.

## Used by

Lab monitors that need volumes or phase boundaries (the core "what's in the beaker" question). Composed via the custom agent rather than direct V2-to-V2 imports.

## Tests

- `Lumi-AI-Core/V2/Vessels/test_vessels.py`

## Gotchas

- SAM2 weights and variant must match — supply `samWeights` as a path or URL. The S3 URL pattern `https://reach-ml-weights.s3.eu-west-2.amazonaws.com/vessels/sam2.1_hiera_small.pt` is referenced in the README.
- `LiquidAnalyser.fill_liquid_within_vessel` is row-wise; tilt the camera and the gravity assumption breaks. Pre-rotate via [V2.Utils](Utils.md) `ImageUtils.rotate_image` if needed.
- `ContainerVisualizer` falls back to the vial STL if the volumetric-flask STL is missing; visuals will silently misrepresent the container.

## See also

- [V2.SegmentAnything](SegmentAnything.md)
- [V2.Detection](Detection.md)
- [agreedDataSchema.md](../data-schema.md)
