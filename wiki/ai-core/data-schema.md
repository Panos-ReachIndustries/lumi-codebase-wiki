---
name: V2 Agreed Data Schema
description: Canonical inter-module data formats for Lumi-AI-Core V2 — detections, tracking, segmentations, and image pipelines.
type: architecture
tags: [v2-module, data-contract]
sources:
  - { repo: Lumi-AI-Core, path: agreedDataSchema.md }
---

# V2 Agreed Data Schema

`Lumi-AI-Core/agreedDataSchema.md` is the canonical living document that defines the Python dict shapes all V2 modules agree to pass between each other. It exists so every module can trust its inputs without ad-hoc coupling. If you're wiring two V2 modules together, check here first.

## Bounding-box detections

The most common pipeline. Used by every monitor that calls `V2.Detection`.

**Input:**
```python
{
  "task":        "bboxes",          # selects bbox pipeline
  "rgb_image":   np.ndarray,        # HxWx3 uint8/int16, NOT encoded bytes
  "depth_image": None,              # optional HxW or HxWx1, aligned to RGB
  "config":      { ... }            # model-specific thresholds, etc.
}
```

**Output:**
```python
{
  "detections": [
    {
      "bbox":       [x1, y1, x2, y2],  # float, normalised [0,1], top-left → bottom-right
      "confidence": 0.87,              # float [0,1]
      "class_name": "flask",           # string semantic label
    }
  ],
  "detection_inference_time": 0.032    # seconds end-to-end
}
```

## Segmentation detections

Extends bbox output with mask data. Same input shape but `"task": "segmentation"`.

**Output adds:**
```python
"segmentation": [...]  # OpenCV contour format (list of points/contours)
```

## Glove / hand-pose detections

`"task": "glove"` — the most complex detection type. Runs a two-stage pipeline: segmentation heatmap → MMPose 21-keypoint hand pose.

**Key output extras beyond bbox:**
```python
"keypoints":       [[x, y], ...],   # 21 joints, PIXEL coords (not normalised), COCO-WholeBody-Hand layout
"keypoint_scores": [0.0, ...],      # 21 per-joint confidences
"pose_confidence": 0.0,             # overall pose confidence (0 in rapid mode)
"segmentation_heatmap": np.ndarray, # float32 HxW [0,1], resized to input
"raw_heatmap":          np.ndarray, # float32 256×256 native model output
```

Three modes via `GenericDetectorWrapper.set_mode({"mode": "rapid"|"normal"|"precise"})`:
- **rapid** — no pose tracking, fastest, `keypoints` absent
- **normal** — pose tracking enabled
- **precise** — highest accuracy, slowest

Keypoint layout: 0 = wrist, 1–4 = thumb (CMC→tip), 5–8 = index, 9–12 = middle, 13–16 = ring, 17–20 = little.

> **Gotcha:** keypoints are in pixel space, not normalised. All other coordinates in the schema are normalised [0,1].

## Image-to-image pipeline

`"task": "image_to_image"` — for transformation models (super-resolution, denoising, etc).

```python
# In
{ "task": "image_to_image", "image": np.ndarray,  # [N, C, H, W] integer
  "config": { ... } }

# Out
{ "image": np.ndarray,        # same [N, C, H, W] shape
  "inference_time": 0.012 }
```

## Tracked objects

Downstream of Detection. See [V2.Tracking](modules/Tracking.md) for the full tracked-object schema — adds `track_id`, `formatted_id` to each detection dict.

## Error envelope

All V2 modules return this shape on failure instead of raising:
```python
{ "errorType": "...", "errorDesc": "...", "stackTrace": "..." }
```

Callers should always check for the presence of `"errorType"` before using output.

## Why it matters

If you're adding a new detector, tracker, or module that produces frame-level results, **conform to this schema**. Downstream consumers (`V2.Tracking`, custom agent pipeline, all monitors) assume it without defensive checks.

## See also

- [V2.Detection](modules/Detection.md) — the production implementation of the bbox pipeline
- [V2.Tracking](modules/Tracking.md) — wraps detection output with persistent IDs
- [V2.ModelInference](modules/ModelInference.md) — low-level inference runner
- Source: `Lumi-AI-Core/agreedDataSchema.md` (authoritative — check for additions before this page)
