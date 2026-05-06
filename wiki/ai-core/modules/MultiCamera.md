---
name: V2.MultiCamera
description: Cross-camera instance matcher — links per-camera object IDs to a canonical identity by aligning interaction events across feeds.
type: module
graph_node: core:MultiCamera
sources:
  - { repo: Lumi-AI-Core, path: V2/MultiCamera/InstanceMatcher.py }
tags: [v2-module]
---

# V2.MultiCamera

`MultiCamera` is the V2 module that answers: "this pipette in cam1 — is it the same physical pipette as the one cam2 sees?" It does *not* match images. Instead, it matches **interaction events** (e.g. `dispense` from `Pipette(id:1)` into `wells_plate(id:2)`) that should be the same physical event observed from two angles, and uses the alignment to build a canonical-ID lookup table.

## What it does

Given per-camera event streams keyed by camera ID, `InstanceMatcher` (`Lumi-AI-Core/V2/MultiCamera/InstanceMatcher.py`) groups events by `verb` and frame number (or timestamp, if frame numbers are absent). Events that share a verb and fall within `maxFrameDelta` frames are treated as the same physical interaction; their per-camera actor and target IDs are unioned into the same canonical identity. Optionally enriches the input events in-place with `canonical_actor_id` / `canonical_target_id`.

## Public API

- `InstanceMatcher({"maxFrameDelta": 2, "maxTimestampDeltaSeconds": 0.1, "configPath": "..."})` — construct.
- `process({"eventsByCamera": {camera_id: [event, ...]}, "enrichEvents": bool})` → `{"instance_map": {"cam1|Pipette(id:1)": "Pipette#A", ...}, "enriched_events": [...]}`.
- `get_canonical_id(camera_id, formatted_id)` → canonical ID string or `None`.
- `get_per_camera_ids(canonical_id)` → list of `(camera_id, formatted_id)` pairs.
- `get_instance_map()` → full mapping dict.

Errors come back as `{"errorType": "BAD_INPUT" | "INTERNAL_ERROR", "errorDesc": ..., "stackTrace": ..., "instance_map": {}}`.

## Input / output

Events must include at minimum a `verb` (string) and either `metadata.frame_number` or `metadata.timestamp`. Actor/target ID format is `ClassName(id:N)` — the matcher parses these to derive class-aware groupings. Output `instance_map` keys use the `"camera_id|formatted_id"` convention.

## Dependencies on other V2 modules

None directly — pure stdlib (`json`, `re`, `os`, `logging`). Upstream, the events typically come from interaction handlers (e.g. [V2.ObjectInteractionsManager](ObjectInteractionsManager.md), [V2.Pipetting](Pipetting.md)).

## Used by

The custom agent uses `MultiCamera` (along with [V2.Visualiser](Visualiser.md)) to fuse multi-angle benchtop captures. Any monitor running >1 camera and emitting interaction events can plug it in.

## Tests

- `Lumi-AI-Core/V2/MultiCamera/test_MultiCamera.py`

## Gotchas

- The matcher relies on event verbs being *identical* across cameras for the same interaction. If one camera emits `dispense` and another emits `Dispense`, they will not match — normalise upstream.
- `maxFrameDelta` defaults to 2; raise it for cameras with non-trivial frame-rate skew, but expect false positives if you raise it too far.
- Output IDs are stable only within a single `process()` call — the matcher does not persist state across calls.

## See also

- [V2.ObjectInteractionsManager](ObjectInteractionsManager.md)
- [V2.Visualiser](Visualiser.md)
- [V2.Tracking](Tracking.md)
- [V2.Pipetting](Pipetting.md)
