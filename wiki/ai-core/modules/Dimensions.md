---
name: V2.Dimensions
description: 3D spatial analysis — lifts 2D bounding boxes into 3D using a depth map, plus real-world distance and area calculations from a known reference. Powers the 3DCalc monitor.
type: module
graph_node: core:Dimensions
sources:
  - { repo: Lumi-AI-Core, path: V2/Dimensions/Dimensions.py }
  - { repo: Lumi-AI-Core, path: V2/Dimensions/_bounding_box_3d.py }
  - { repo: Lumi-AI-Core, path: V2/Dimensions/README.md }
tags: [v2-module]
---

# V2.Dimensions

`Dimensions` turns a 2D detection plus a depth map into 3D camera-space geometry. It is depth-model-agnostic — any caller can feed it a `depthMap` array — but ships a convenience `infer_midas` that delegates to the V2 MiDaS wrapper. The two metric helpers (`infer_distance`, `infer_area`) let you bootstrap real-world units from a single known reference distance.

## What it does

Three independent capabilities (`Lumi-AI-Core/V2/Dimensions/Dimensions.py`):

1. **Depth estimation (optional convenience)** — `infer_midas({"frame"})` calls `V2.ModelInference.Midas.MidasInference.estimate_depth` and returns a normalised depth map in `[0, 1]`.
2. **3D bounding boxes** — `get_3d_bboxes({"frame", "depthMap", "boundingBoxes"})` projects every bbox into camera space via a pinhole model. Output per detection: `depthStats {min, max, avg}` and `bbox3d {center: {x,y,z}, dimensions: {width,height,depth}}`. The internal helper is `_BoundingBox3D` in `_bounding_box_3d.py`.
3. **Metric inference** — `infer_distance` / `infer_area` use a user-provided pair of reference points and a known real-world distance to produce a per-frame metric scale, then apply it to target points / polygons.

Camera defaults: `fx = fy = 1000`, `cx, cy = (W/2, H/2)`, depth scaled by 5.0 for "real-world units". Coordinate convention: **X right, Y down, Z forward**.

## Public API

```python
Dimensions({})  # no required params

.infer_midas({"frame"}) -> {"depthMap": ndarray}
.get_3d_bboxes({"frame", "depthMap", "boundingBoxes": [...], "fx"?, "fy"?, "cx"?, "cy"?})
  -> {"detections": [{bbox, confidence, classId, className, depthStats, bbox3d}, ...]}
.infer_distance({"depthMap", "referencePoint1", "referencePoint2", "referenceDistance",
                 "targetPoint1", "targetPoint2"}) -> {"distance": float}
.infer_area({"depthMap", "referencePoint1", "referencePoint2", "referenceDistance",
             "polygon": [[x,y], ...]}) -> {"area": float}
```

## Input/output shape

`boundingBoxes` is the V2 detection shape (`bbox`, `confidence`, `classId`, `className`) — see `agreedDataSchema.md`. The output keeps every input field and adds `depthStats` + `bbox3d`. Reference / target points are **pixel** coordinates, not normalised.

## Dependencies on other V2 modules

- `V2.ModelInference.Midas.MidasInference` — only when you call the `infer_midas` convenience method. The rest of the module needs no models.

## Used by which monitors / V2 modules

- `Lumi-AI-Continuous/monitors/3DCalc/3DCalc.py` — the principal consumer (also smoke-tested via `scripts/monitor_smoke_all.py` and `monitors/3DCalc/test_3DCalc.py`).

## Tests

- `Lumi-AI-Core/V2/Dimensions/test_dimensions.py`
- `Lumi-AI-Core/V2/Dimensions/example_usage.py` — runs the full pipeline over a video file (mode 2 = "full 3D spatial analysis").

## Gotchas

- The fixed `fx = fy = 1000` is a guess. For accurate metrics, calibrate the camera and pass real intrinsics, otherwise distances are arbitrary scale.
- `referenceDistance` is unitless from the module's perspective — outputs come back in **the same units** you pass in. Be consistent (cm, mm) across calls.
- Transparent / reflective objects (vials!) will give noisy MiDaS depth — consider running on uncluttered references where possible.
- `_build_bbox3d` is exposed only as a private helper; use `get_3d_bboxes` for batches.

## See also

- [V2.Detection](Detection.md) — produces the `boundingBoxes` you feed in
- [V2.ModelInference](ModelInference.md) — hosts the MiDaS depth model
- [3DCalc monitor](../../ai-continuous/monitors/3DCalc.md) — the production consumer
- [agreedDataSchema](../data-schema.md)
