---
name: V2.GridTracker
description: Grid-based tracking for laboratory well plates and well racks — detects the grid, tracks individual wells / vials, and exposes per-cell state across frames.
type: module
graph_node: core:GridTracker
sources:
  - { repo: Lumi-AI-Core, path: V2/GridTracker/README.md }
  - { repo: Lumi-AI-Core, path: V2/GridTracker/WellPlate/GridTracker.py }
  - { repo: Lumi-AI-Core, path: V2/GridTracker/WellRack/GridTracker.py }
  - { repo: Lumi-AI-Core, path: V2/GridTracker/WellPlate/README.md }
  - { repo: Lumi-AI-Core, path: V2/GridTracker/WellRack/README.md }
tags: [v2-module, tracking]
---

# V2.GridTracker

`GridTracker` is the namespace under which the well-plate and well-rack grid trackers live. There is no top-level wrapper — instead, two sibling sub-modules each ship their own `GridTrackerWrapper`. They share the V2 dict-I/O contract, persistent per-frame state, and per-cell output, but the underlying detectors and what counts as a "cell" differ.

## What it does

Two independent grid trackers (`Lumi-AI-Core/V2/GridTracker/`):

- **WellPlate** (`WellPlate/GridTracker.py`) — standard well plates (e.g. 96-well). Backed by `V2.ModelInference.MultiUNet` for per-well detection plus an optional YOLO model for plate segmentation. `track_well_plate({"frame", "segmentationMask"?, "reset"?})` maintains tracker state across frames.
- **WellRack** (`WellRack/GridTracker.py`) — vial / tube racks. Two vial detectors selectable via `vialDetectorMethod`: `"hsl"` (HLS colour filtering + MiniBatchKMeans, no weights, CPU-only) or `"keypoint"` (`VialKeypointNet` ResNet18 heatmap, GPU-optional). Adds dominant/recessive grid-line fitting, a v6 lid-state classifier (~93.6% accuracy), occlusion handling, and v22 portrait-mode detection plus optional EfficientNet-B0 per-vial CNN classification.

Both wrappers maintain rolling-window display stability so jittery detections don't make the grid jump.

## Public API

```python
# WellPlate
from V2.GridTracker.WellPlate import GridTrackerWrapper
wrapper = GridTrackerWrapper({"wellPlateModelPath": "...", "wellPlateYoloModelPath"?: "..."})
wrapper.track_well_plate({"frame": ndarray, "segmentationMask"?, "reset"?})

# WellRack
from V2.GridTracker.WellRack import GridTrackerWrapper
wrapper = GridTrackerWrapper({"wellRackYoloModelPath"?, "vialDetectorMethod": "hsl"|"keypoint",
                              "enableCnnClassification": False})
wrapper.track_well_rack({"frame": ndarray})
```

Both return per-cell grid state plus error dicts on failure.

## Input/output shape

Custom — not the canonical detection schema. Each cell carries position, classification, and (for racks) lid state. WellRack v22 also returns inferred grid points and CNN bboxes for visualisation. See each sub-module's README for the exact field list.

## Dependencies on other V2 modules

- `V2.ModelInference.MultiUNet` (WellPlate well detection)
- `V2.ModelInference.YOLO` (both, optional)
- `V2.ModelInference.Models.RackKeypoint.RackKeypointInference` (WellRack `keypoint` mode)
- `V2.ModelInference.Models.VialLidsClassifier.VialLidsClassifierInference` (WellRack `enableCnnClassification=True`)

## Used by which monitors / V2 modules

`Lumi-AI-Continuous/monitors/custom/detection_handlers/wellplate_handler.py` consumes well-plate output (with `tests/test_capability_weights.py` and `test_wellplate_confidence.py` exercising it). For wider coverage, search for `V2.GridTracker` across `monitors/`.

## Tests

- `Lumi-AI-Core/V2/GridTracker/WellPlate/test_gridtracker.py` and `test_integration.py`
- `Lumi-AI-Core/V2/GridTracker/WellRack/{unit_tests.py, system_test.py, test_GridTracker.py}`

## Gotchas

- WellPlate and WellRack each export their own `GridTrackerWrapper` — they have the **same class name** but live in different sub-packages. Import from the right one.
- WellRack `keypoint` mode needs `best_model.pth` weights at the configured path; `hsl` mode is the only weights-free option.
- WellRack v6 lid classifier is **disabled in portrait mode** automatically — if you suspect missing classifications check the orientation HUD in the visualiser.
- Pass `reset=True` to clear state between independent runs of the same tracker instance.

## See also

- [V2.WellPlate](WellPlate.md) — the matching domain page (well-plate-specific concerns)
- [V2.LabContainerTracking](LabContainerTracking.md) — vessel-identity layer that may consume grid output
- [V2.ModelInference](ModelInference.md) — hosts the underlying detectors and classifiers
- [agreedDataSchema](../data-schema.md)
