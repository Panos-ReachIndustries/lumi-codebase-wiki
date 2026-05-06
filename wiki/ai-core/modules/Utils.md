---
name: V2.Utils
description: Shared image, geometry, and data-conversion helpers used across V2 modules. A leaf dependency — nothing inside V2 should import upward from here.
type: module
graph_node: core:Utils
sources:
  - { repo: Lumi-AI-Core, path: V2/Utils/DataConverters.py }
  - { repo: Lumi-AI-Core, path: V2/Utils/ImageUtils.py }
  - { repo: Lumi-AI-Core, path: V2/Utils/GeometryUtils.py }
  - { repo: Lumi-AI-Core, path: V2/Utils/DetectionToTrackingPipeline.py }
  - { repo: Lumi-AI-Core, path: V2/Utils/PipelineSteps.py }
tags: [v2-module]
---

# V2.Utils

`Utils` is the V2 module everyone imports from but nobody imports back into. Three static-method classes (`DataConverters`, `ImageUtils`, `GeometryUtils`) and two pipeline glue helpers, kept deliberately leaf-shaped so other V2 modules never have to worry about cycles.

## What it does

Three families of helpers:

- **`DataConverters`** (`Lumi-AI-Core/V2/Utils/DataConverters.py`) — bridges between detection shapes used by different consumers: `detections_to_text_regions`, `merge_text_to_detections`, `filter_detections_by_area`, `process_regions_with_detector` (run a detector on each region crop and reassemble with offset handling), `mediapipe_hands_to_gesture_keypoints`.
- **`ImageUtils`** (`ImageUtils.py`) — `apply_clahe`, `enhance_contrast_in_regions`, `sharpen_image`, `resize_image`, `rotate_image` (with a `CAMERA_ROTATIONS` env hook), `rotate_polygon_coordinates_inverse` for round-tripping coords through a rotated frame.
- **`GeometryUtils`** (`GeometryUtils.py`) — line/angle math used by the pipette volume reader (`angle_from_vertical_deg`, `extend_line_to_frame_edges`, `centreline`, `width_between_lines`) plus bbox/polygon helpers used by [V2.Pipetting](Pipetting.md) and [V2.ObjectInteractionsManager](ObjectInteractionsManager.md) (`bbox_overlaps`, `pipette_tip_from_polygon`, `check_intersection` via Shapely).

`PipelineSteps.py` and `DetectionToTrackingPipeline.py` provide ready-made composition steps (Detection → Tracking glue) that other modules and the custom agent can re-use.

## Public API

`DataConverters` and `ImageUtils` follow the V2 dict I/O pattern (`input_data` in, dict out, `errorType`/`errorDesc`/`stackTrace` on failure). `GeometryUtils` deliberately uses positional/keyword args and returns `None` on degenerate inputs — no error dicts, since it is called inside hot loops. Three `*_exposed_functions.json` files document the dict-style methods.

## Input / output

Per function — see the JSON specs alongside each file. The shared assumptions: image arrays are HxWx3 BGR uint8, polygons are lists of `[x, y]` pairs (sometimes normalised, sometimes pixel — check the function), bboxes are `[x1, y1, x2, y2]` with origin top-left.

## Dependencies on other V2 modules

**None — by design.** `numpy`, `opencv-python`, `shapely` (only for `check_intersection`).

## Used by

Almost every V2 module that does anything geometric: [V2.Pipetting](Pipetting.md), [V2.ObjectInteractionsManager](ObjectInteractionsManager.md), [V2.LabContainerTracking](LabContainerTracking.md), [V2.Detection](Detection.md), [V2.Vessels](Vessels.md), and downstream pipelines built by the custom agent.

## Tests

- `Lumi-AI-Core/V2/Utils/test_v2_utils.py` — `DataConverters` + `ImageUtils` + `GeometryUtils` line/angle helpers.
- `Lumi-AI-Core/V2/Utils/test_GeometryUtils.py` — bbox/polygon helpers.
- `Lumi-AI-Core/V2/Utils/test_DetectionToTrackingPipeline.py`, `test_pipeline_integration.py`.

## Gotchas

- `GeometryUtils` assumes image-style coords (y down) and *near-vertical* lines for centreline/width helpers.
- `ImageUtils.rotate_image` honours `CAMERA_ROTATIONS` JSON env when supplied — a frame can rotate without you asking.
- `DataConverters.process_regions_with_detector` requires `_detector_instance` injection; expects to be called from a runtime that supplies it.

## See also

- [V2.Detection](Detection.md)
- [V2.Tracking](Tracking.md)
- [agreedDataSchema.md](../data-schema.md)
