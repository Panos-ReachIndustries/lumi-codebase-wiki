---
name: V2.Vortexing
description: Detects active use of a vortexer by tracking sustained glove–vortexer bbox overlap with grace periods and occlusion handling.
type: module
graph_node: core:Vortexing
sources:
  - { repo: Lumi-AI-Core, path: V2/Vortexing/Vortexer.py }
  - { repo: Lumi-AI-Core, path: V2/Vortexing/stand_alone_vortexer.py }
tags: [v2-module]
---

# V2.Vortexing

`Vortexing` is the V2 module that decides "is the scientist actively vortexing right now?". It is a small temporal state machine that watches glove/vortexer track overlap and fires `vortexing_started` / `vortexing_stopped` events.

## What it does

`Vortexer` (`Lumi-AI-Core/V2/Vortexing/Vortexer.py:16`) maintains a per-`track_id` state struct and runs the following logic each frame:

- IoU between any glove track and a vortexer track > `iou_threshold` (default 0.1) → start accumulating overlap.
- Continuous overlap ≥ `overlap_threshold_secs` (default 2.0) → fire `vortexing_started`, set `is_vortexing = True`.
- Gap in overlap ≤ `grace_period_secs` (default 0.5) → preserve the timer (absorbs detector flicker).
- Gap > `grace_period_secs` → fire `vortexing_stopped`, reset.

The interesting part is occlusion handling (`Vortexer.py:115`): when the vortexer track is *lost* but a glove still sits in its last-known box, the state is retained — the assumption being that the hand is occluding the vortexer. This carries on until either the glove leaves the region (then `grace_period_secs` evicts) or `max_occlusion_secs` (default 10.0) passes regardless.

Each vortexer track is monitored independently (multiple vortexers in scene work).

## Public API

- `Vortexer(init_args: dict)` — accepts `overlap_threshold_secs`, `iou_threshold`, `grace_period_secs`, `max_occlusion_secs`, `vortexer_class_name`, `glove_class_name`.
- `process({"tracks": [...]})` — agent entry point; splits flat track list by class and calls `infer_vortexing`.
- `infer_vortexing(vortexer_tracks, glove_tracks)` — direct entry point for tests.

Output: `{"events": [{"type", "track_id", "formatted_id", "reason"?}], "vortexer_status": [{"track_id", "is_vortexing", "overlap_duration"}]}`.

## Input / output

In: the flat `tracks` list from a `TrackingStep` — each track has `track_id`, `box` ([x1,y1,x2,y2] normalised), `class`, `formatted_id`, `score`. Out: events on state transitions and per-vortexer status. See [agreedDataSchema.md](../data-schema.md) for the upstream track shape.

## Dependencies on other V2 modules

- [V2.Tracking](Tracking.md) — `Vortexer` is designed to sit downstream of a `TrackingStep`.
- Indirectly [V2.Detection](Detection.md) (vortexer + glove detectors) — typically two YOLO models. `stand_alone_vortexer.py` shows the wiring.

No external Python deps beyond stdlib (`time`, `dataclasses`, typing).

## Used by

The custom agent's pipeline JSON, slotted in as a block named e.g. `"vortexer"` after `tracking`. Wired up by lab monitors that need vortex-equipment usage events.

## Tests

- `Lumi-AI-Core/V2/Vortexing/TestVortexer.py` (referenced in the README; the standalone runner is `stand_alone_vortexer.py`)

## Gotchas

- Class-name driven — if your tracker emits `"glove"` but you pass `glove_class_name="Glove"`, nothing matches.
- `max_occlusion_secs` exists specifically so a glove parked in the last-known vortexer region can't signal vortexing forever. Don't set it absurdly high.
- Uses `time.monotonic()` — playback at non-real-time speeds will misbehave; the standalone runner uses wall time.

## See also

- [V2.Tracking](Tracking.md) — required upstream
- [V2.Detection](Detection.md) — for the underlying glove + vortexer detectors
- [agreedDataSchema.md](../data-schema.md)
