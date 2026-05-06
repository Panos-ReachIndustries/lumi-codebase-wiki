---
name: V2.Interactions
description: Human-hand interaction primitives — track which hand touches which object over time, and simulate "wiping" coverage of a region.
type: module
graph_node: core:Interactions
sources:
  - { repo: Lumi-AI-Core, path: V2/Interactions/HumanHand/InteractionTracker.py }
  - { repo: Lumi-AI-Core, path: V2/Interactions/HumanHand/ObjectWiper.py }
  - { repo: Lumi-AI-Core, path: V2/Interactions/HumanHand/README.md }
  - { repo: Lumi-AI-Core, path: V2/Interactions/README.md }
tags: [v2-module, tracking]
---

# V2.Interactions

`Interactions` is the namespace for *who-touches-what* logic. Today it has one populated sub-package, `HumanHand`, exposing two utilities: `InteractionTracker` (temporal hand-object interactions) and `ObjectWiper` (region-coverage tracking, e.g. how much of a surface has been wiped). A `HumanFullBody` sibling exists as a placeholder (`tmp/` only) — there's no implementation yet.

## What it does

### InteractionTracker

`Lumi-AI-Core/V2/Interactions/HumanHand/InteractionTracker.py` watches a stream of detections (with `className` labelling hands vs everything else) and forms candidate interactions when a hand's inflated bbox overlaps an object. It maintains a temporal smoothing window (`windowSize`, default 11) and only emits an interaction when proximity confidence exceeds `proximityThreshold` (default 0.70). Each interaction carries `interactionId`, `state`, `handId`, `objectId`, both class names, `confidenceScore`, and `startTime`/`endTime`/`duration`. Stale interactions remain queryable via `get_tracked_interactions`.

### ObjectWiper

`ObjectWiper.py` holds a binary "dirty" mask and exposes circular (`wipe`) and elliptical (`wipe_oval`) erasure operations. `dirtType` is either `"timed"` (auto-resets every `resetTime` seconds) or `"contact"` (resets when `check_contact` overlaps an object mask). Use `get_wiped_proportion` for a `[0, 1]` coverage figure.

## Public API

```python
InteractionTracker({"windowSize": 11, "inflation": 1.05,
                    "proximityThreshold": 0.70, "handClassName": "hand"})
  .update_tracks({"detections": [{detectionId, bbox2d, className,
                                  depthRange?, landmarks?, polygons?}, ...],
                  "imageSize"?: [w, h]})
  .get_tracks({})                  -> {"tracks": [...]}
  .get_tracked_interactions({})    -> {"interactions": [...]}

ObjectWiper({"mask": ndarray, "dirtType": "timed"|"contact", "resetTime": 10})
  .wipe({"centre": [x,y], "radius": float})
  .wipe_oval({"centre": [x,y], "longAxis": [dx,dy], "shortAxis": [dx,dy]})
  .check_contact({"objectMasks": [ndarray, ...]}) -> {"contact": bool}
  .get_unwiped_mask({}) / .get_wiped_mask({}) / .get_wiped_proportion({}) / .reset_mask({})
```

All methods follow V2 dict-I/O — errors return `{errorType, errorDesc, stackTrace}`, no exceptions.

## Input/output shape

`InteractionTracker` accepts detection dicts with `bbox2d` in **pixel** coordinates (and optional `polygons`/`landmarks`), not the normalised V2 detection bbox. Convert at the boundary if you're piping in [V2.Detection](Detection.md) output. `ObjectWiper` works in raw image-shape masks (uint8). Outputs are bespoke interaction / coverage dicts — see `agreedDataSchema.md` for the upstream detection contract.

## Dependencies on other V2 modules

None directly. Pure NumPy + OpenCV. Conceptually depends on a hand-classifying detector upstream — typically [V2.Detection](Detection.md) in glove mode.

## Used by which monitors / V2 modules

Imported by `Lumi-AI-Continuous`:

- `protocol_arbiter_v2/ui_gateway.py` (and `Testing/test_ui_gateway.py`)
- `monitors/custom/step_evaluator.py` (and `test_step_evaluator.py`)

## Tests

- `Lumi-AI-Core/V2/Interactions/test_interactions.py`

## Gotchas

- `bbox2d` is **pixel-space** in this module — opposite of the normalised bboxes most of V2 uses.
- `imageSize` is inferred from max-bbox extents if you don't pass it. That's fine for steady-state but unreliable on the first frame; pass it explicitly when you can.
- `ObjectWiper`'s `dirtType="timed"` auto-resets on a wall-clock timer — make sure the resets are wanted before turning it on for long-running sessions.
- `HumanFullBody/` is unimplemented at time of writing — don't import from it.

## See also

- [V2.Detection](Detection.md) — produces the hand detections you feed in (especially glove mode)
- [V2.Gestures](Gestures.md) — pairs naturally with hand interactions
- [V2.ObjectInteractionsManager](ObjectInteractionsManager.md) — broader interaction state
- [agreedDataSchema](../data-schema.md)
