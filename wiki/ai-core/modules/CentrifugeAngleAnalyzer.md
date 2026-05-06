---
name: V2.CentrifugeAngleAnalyzer
description: Tracks the rotational angle of a centrifuge rotor through manual rotation and motor spin, and remembers vial positions so each tube can be re-identified after the cycle.
type: module
graph_node: core:CentrifugeAngleAnalyzer
sources:
  - { repo: Lumi-AI-Core, path: V2/CentrifugeAngleAnalyzer/centrifuge_analyzer.py }
  - { repo: Lumi-AI-Core, path: V2/CentrifugeAngleAnalyzer/angle_tracker.py }
  - { repo: Lumi-AI-Core, path: V2/CentrifugeAngleAnalyzer/spin_detector.py }
  - { repo: Lumi-AI-Core, path: V2/CentrifugeAngleAnalyzer/vial_registry.py }
  - { repo: Lumi-AI-Core, path: V2/CentrifugeAngleAnalyzer/README.md }
tags: [v2-module, tracking]
---

# V2.CentrifugeAngleAnalyzer

`CentrifugeAngleAnalyzer` is the centrifuge-specific tracker. It bolts together a YOLOv8n rotor detector, Lucas-Kanade optical flow, an auto-calibrating spin detector, and a polar-coordinate vial registry so that vials retain their identity across loading, manual rotation, and a full motor spin. It's the only V2 module that maintains rotor-local positions of objects.

## What it does

Per-frame pipeline (`Lumi-AI-Core/V2/CentrifugeAngleAnalyzer/centrifuge_analyzer.py`):

1. **Rotor detection** — `RotorDetectionInference` (YOLOv8n at 320px, mAP50=0.995) finds the bowl, EMA-smoothed.
2. **Spin detection** — three-signal state machine (keypoint count, Laplacian variance, frame difference) auto-calibrated from frame 1 (`spin_detector.py`). Returns `spinning | stationary | candidate | unknown`.
3. **Angle tracking** — Shi-Tomasi + LK optical flow, median angular displacement (`angle_tracker.py`). Falls back to polar phase correlation after a spin to recover modulo the rotor's auto-detected N-fold symmetry.
4. **Optional fiducials** — green or red HSV markers (`marker_detector.py`) give absolute angle and lid-close-as-spin detection.
5. **Vial registry** — `vial_registry.py` stores each registered vial in rotor-local `(theta, radius)`, updates as the rotor turns, and matches camera-space queries back to track IDs.

Hits 16-25 fps on CPU.

## Public API

```python
CentrifugeAngleAnalyzer({
  "rotorModelWeights": "...pt",   # required
  "confThreshold": 0.25, "rotorFraction": 0.78, "noiseGateDeg": 0.20,
  "lkMaxCorners": 250, "lkWinSize": 21, "lkMaxLevels": 5,
  "fps": 30.0,
  "markerColor": "green" | "red" | dict | None,
})

.analyze_frame({"frame": ndarray, "annotation": {bbox|polygon|mask}})
  -> {rotor, spinStatus, angle: {angleDeg, deltaAngleDeg, confidence, method}, frameIndex, processingTimeS}
.reset_angle()                    # re-zero
.get_status()                     # frame counter + nfold + registered vials
.register_vial({"track" | "position", "trackId"?})
.identify_vial({...})             # ranked candidate match
.remove_vial({"trackId"})
.get_vial_positions()
```

`method` is one of `lk | fiducial | polar_reacq | frozen | idle | init`.

## Input/output shape

Custom — not the canonical detection schema. Inputs accept a V2 `annotation` (bbox/polygon/mask); vial inputs accept either a V2 track dict (with `track_id` + `center`) or `{x, y}` normalised. See `agreedDataSchema.md` for the upstream `track` shape.

## Dependencies on other V2 modules

- `V2.ModelInference.Models.RotorDetection.RotorDetectionInference` — wraps the YOLOv8n weights as a V2 `InferenceModel`.

## Used by which monitors / V2 modules

Domain-specific; no direct importers found in `Lumi-AI-Continuous/monitors/` at time of writing. Best-effort: search for `V2.CentrifugeAngleAnalyzer`. Likely consumer is a future `centrifuge` monitor or [V2.LabContainerTracking](LabContainerTracking.md) for vial ID handoff.

## Tests

Substantial suite under `Lumi-AI-Core/V2/CentrifugeAngleAnalyzer/tests/` — `test_centrifuge_analyzer.py`, `test_angle_tracker.py`, `test_spin_detector.py`, `test_marker_detector.py`, `test_vial_registry.py`, plus `test_exposed_functions_compliance.py`.

## Gotchas

- Without fiducial markers, post-spin angle is correct **modulo the slot spacing** (e.g. ±30° for a 12-slot rotor). Add a coloured sticker if you need absolute orientation.
- Lid-closing centrifuges break signal-based spin detection (the lid is feature-rich, not blurry). Use `markerColor` to fall back to fiducial-based spin detection (marker disappearance = lid closed).
- Bottom-up cameras give poor LK accuracy because the rotor underside is texture-poor.
- Fast spins exceed the LK search radius and are underestimated; rely on the spin-detector state machine to skip during spin and re-acquire afterwards.

## See also

- [V2.Tracking](Tracking.md) — upstream source of the `track` dicts you register
- [V2.LabContainerTracking](LabContainerTracking.md) — handles vial identity outside the centrifuge
- [V2.ModelInference](ModelInference.md) — hosts the rotor detector
- [agreedDataSchema](../data-schema.md)
