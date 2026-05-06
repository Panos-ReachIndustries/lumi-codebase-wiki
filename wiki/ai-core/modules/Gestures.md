---
name: V2.Gestures
description: Rule-based hand-gesture classifier (okay, thumbs up/down, peace, middle finger) over 21-point hand keypoints from the glove detector.
type: module
graph_node: core:Gestures
sources:
  - { repo: Lumi-AI-Core, path: V2/Gestures/BaseGestureRecogniser.py }
  - { repo: Lumi-AI-Core, path: V2/Gestures/ClassicalGestureRecogniser.py }
  - { repo: Lumi-AI-Core, path: V2/Gestures/GestureProcessor.py }
  - { repo: Lumi-AI-Core, path: V2/Gestures/README.md }
tags: [v2-module]
---

# V2.Gestures

`Gestures` recognises a small fixed set of hand gestures from MediaPipe / glove-style 21-point keypoint arrays — no neural network, just geometric rules. The public surface is `ClassicalGestureRecogniser` for one hand at a time and `GestureProcessor` to batch over many hands per frame.

## What it does

The classifier (`Lumi-AI-Core/V2/Gestures/ClassicalGestureRecogniser.py`) computes one confidence score per gesture from finger-tip / joint geometry:

- `okay_confidence` — thumb tip and index tip near each other (circle).
- `thumbs_up_confidence` / `thumb_tip_direction` — thumb extended, other fingers curled; direction is up/down/side.
- `peace_confidence` — index and middle extended, ring and pinky curled.
- `middlefinger_confidence` — middle alone extended.

`recognise(input_data)` picks the highest-scoring gesture above the configured `threshold`, falling back to `"unknown"`. `GestureProcessor.process_hands` (`GestureProcessor.py`) wraps a single `ClassicalGestureRecogniser` and walks a list of hand-keypoint arrays.

## Public API

```python
ClassicalGestureRecogniser({"threshold": 50})  # default minimum confidence

.recognise(input_data)            -> {"gesture": str, "confidence": float}
.okay_confidence(input_data)      -> {"confidence": float}
.thumbs_up_confidence(input_data) -> {"confidence": float}
.peace_confidence(input_data)     -> {"confidence": float}
.middlefinger_confidence(input_data) -> {"confidence": float}
.thumb_tip_direction(input_data)  -> {"direction": "up"|"down"|"side"}

GestureProcessor({...})
.process_hands({"hands": [keypoints, ...]}) -> {"gestures": [...]}
```

`BaseGestureRecogniser` (`BaseGestureRecogniser.py`) is an abstract base; subclass and override `recognise` to add a model-based recogniser.

Recognised gestures: `okay`, `thumbs_up`, `thumbs_down`, `peace`, `middlefinger`, `unknown`.

## Input/output shape

Inputs are hand-keypoint arrays in the COCO-WholeBody-Hand layout (21 joints, pixel coordinates) — exactly what the glove pipeline of [V2.Detection](Detection.md) produces. See the `keypoints` field in `agreedDataSchema.md` (Glove / Hand Pose section). Outputs are bespoke gesture dicts.

## Dependencies on other V2 modules

None directly — but it consumes the `keypoints` output of the glove-mode `GenericDetectorWrapper` from [V2.Detection](Detection.md), so you'll always see them paired.

## Used by which monitors / V2 modules

Best-effort: search for `V2.Gestures` across `monitors/`. No direct importer found in `Lumi-AI-Continuous/monitors/` at the time of writing — likely consumer is a future hands-/gestures-aware monitor or a UI-debug widget on the web side.

## Tests

- `Lumi-AI-Core/V2/Gestures/test_gestures.py`

## Gotchas

- Threshold defaults to `50` (not 0.5) — the classifier returns scores in arbitrary units, so calibrate per-camera.
- "Unknown" is the explicit fallback; you cannot get back a gesture below the threshold.
- The classifier is rule-based, so it's deterministic and fast but **not robust to unusual hand poses** (gloved, partial occlusion, side view). It's designed for clear front-on shots.
- Keypoint coordinates are pixel-space — different to most V2 normalised conventions.

## See also

- [V2.Detection](Detection.md) — supplies the 21-point `keypoints` array (glove mode)
- [V2.Interactions](Interactions.md) — pairs gestures with object interactions
- [agreedDataSchema](../data-schema.md) — the canonical keypoint layout
- [V2.ObjectInteractionsManager](ObjectInteractionsManager.md)
