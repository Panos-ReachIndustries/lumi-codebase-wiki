---
name: V2.HistoricVideoAnalysis
description: Post-hoc analysis of recorded experiment video — currently houses ActivityDetection, a CV-only "is something happening?" detector that runs without models or APIs.
type: module
graph_node: core:HistoricVideoAnalysis
sources:
  - { repo: Lumi-AI-Core, path: V2/HistoricVideoAnalysis/README.md }
  - { repo: Lumi-AI-Core, path: V2/HistoricVideoAnalysis/ActivityDetection/ActivityDetector.py }
  - { repo: Lumi-AI-Core, path: V2/HistoricVideoAnalysis/ActivityDetection/README.md }
tags: [v2-module]
---

# V2.HistoricVideoAnalysis

`HistoricVideoAnalysis` is the V2 namespace for **non-real-time** analysis of pre-recorded video. While most of the V2 modules assume a live stream, this folder exists for retrospective protocol verification and experiment review. Today it contains exactly one sub-module: `ActivityDetection`.

## What it does

`ActivityDetection.ActivityDetector` (`Lumi-AI-Core/V2/HistoricVideoAnalysis/ActivityDetection/ActivityDetector.py`) answers "is something happening in this frame?" with no model weights and no API keys — pure OpenCV + NumPy. You configure it with one of four methods:

- `optical_flow` — Lucas-Kanade, Farneback (default), or dense flow.
- `frame_diff` — per-pixel difference vs the previous frame.
- `temporal_gradient` — derivative of the frame buffer.
- `combined` (default) — OR over all three.

Optional grid mode (`gridX`, `gridY`) splits the frame into segments and reports per-cell activity. The detector keeps a `frameBufferSize` ring of recent frames and an optional `smoothingWindow` to suppress single-frame noise. Downscaling and grayscale conversion are configurable for speed.

## Public API

```python
ActivityDetector({
  "method": "combined",                    # | "optical_flow" | "frame_diff" | "temporal_gradient"
  "opticalFlowType": "farneback",          # | "lucas_kanade" | "dense"
  "threshold": 0.1,
  "minMotionMagnitude": 1.0,
  "frameBufferSize": 2,
  "useGrayscale": True,
  "downscaleFactor": 1.0,
  "smoothingWindow": 1,
  "gridX": 1, "gridY": 1,
})

.check_for_activity({"frame": ndarray, "frameNumber"?: int})
  -> {"isActive": bool,
      "confidence": float,
      "activityGrid": list[list[bool]],
      "confidenceGrid": list[list[float]],
      "methodResults": {...} | "methodResultsGrid": list[list[dict]],
      "metrics": list[list[dict]]}
```

`__init__` raises `ValueError` for invalid config; `check_for_activity` returns V2 error dicts on failure. State persists across frames in the instance — `check_for_activity` is **stateful**.

## Input/output shape

Custom — not the detection schema. `activityGrid` is a 2D list of booleans `[gridY][gridX]`; `metrics` carries motion magnitude, changed-pixels percentage, and temporal-gradient values per segment.

## Dependencies on other V2 modules

None. Pure OpenCV + NumPy. The README explicitly notes "No external dependencies". This is by design — historic analysis should be cheap and self-contained.

## Used by which monitors / V2 modules

Best-effort: search for `V2.HistoricVideoAnalysis` or `ActivityDetector` across `monitors/`. No direct importer found in `Lumi-AI-Continuous/monitors/` at the time of writing — this module is intended for offline review tooling rather than live monitors.

## Tests

- `Lumi-AI-Core/V2/HistoricVideoAnalysis/ActivityDetection/test_ActivityDetector.py`

## Gotchas

- `combined` uses **OR** logic across methods — any one of them firing flags the frame as active. Tighten `threshold` if you're getting false positives.
- The detector is stateful; create a fresh instance per video stream you want to analyse independently.
- `gridX`/`gridY` >= 2 changes the output shape — `methodResults` becomes `methodResultsGrid`. Branch downstream code accordingly.
- Despite being "historic", nothing stops you from feeding it live frames — but `V2.Detection` + a real model is usually more useful in that case.

## See also

- [V2.Detection](Detection.md) — when you need *what* is happening, not just *if*
- [V2.CentrifugeAngleAnalyzer](CentrifugeAngleAnalyzer.md) — uses related signals (Laplacian, frame diff) for spin detection
- [V2.Tracking](Tracking.md) — also stateful per-frame
- [agreedDataSchema](../data-schema.md)
