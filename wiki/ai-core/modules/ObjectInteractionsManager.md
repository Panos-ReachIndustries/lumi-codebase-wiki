---
name: V2.ObjectInteractionsManager
description: Routes tracked objects to per-class interaction handlers — the dispatcher that turns a list of tracks into pairwise interaction events.
type: module
graph_node: core:ObjectInteractionsManager
sources:
  - { repo: Lumi-AI-Core, path: V2/ObjectInteractionsManager/ObjectInteractionsManager.py }
  - { repo: Lumi-AI-Core, path: V2/ObjectInteractionsManager/PipettingInteractions.py }
  - { repo: Lumi-AI-Core, path: V2/ObjectInteractionsManager/OverlapInteractions.py }
tags: [v2-module]
---

# V2.ObjectInteractionsManager

`ObjectInteractionsManager` is the V2 dispatcher that takes a flat list of tracked objects (from [V2.Tracking](Tracking.md)) and routes them to interaction handlers grouped by the classes each handler cares about. A handler can declare it needs `["pipette", "well_plate"]` together, or `["hand", "beaker", "testTube"]` together — the manager passes the relevant subset on each frame.

## What it does

The manager keeps a registry of `BaseObjectInteractions` subclasses (`Lumi-AI-Core/V2/ObjectInteractionsManager/ObjectInteractionsManager.py:18`). On `process_tracked_objects(...)`, it splits incoming `tracks` by class, and for every registered handler calls `handler.process({"tracks": ..., "tracksByClass": {class: [...], ...}, "frame": ..., "context": ...})`. Two concrete handlers ship with the module:

- **`PipettingInteractions`** (`PipettingInteractions.py`) — pairwise interactions between pipettes and containers.
- **`OverlapInteractions`** (`OverlapInteractions.py`) — generic IoU-based overlap detection between any two tracked classes.

## Public API

- `ObjectInteractionsManager({"interactionClasses": [...]} or empty)` — construct, optionally pre-register handlers.
- `register_interaction_class(cls_or_instance)` — add a handler at runtime.
- `process_tracked_objects({"tracks": [...], "frame": ndarray, "context": {...}})` → `{"handlerResults": [{"supportedClasses": [...], "result": ...}, ...], "processedClasses": [...]}`.

`BaseObjectInteractions` is the abstract base; subclasses implement `get_supported_class_names() -> list[str]` and override `_process_impl(input_data) -> dict`.

## Input / output

Input tracks must include `track_id` and `class` (or `class_name`, normalised by `BaseTracker.track_to_tracked_object`). All other keys (`box`, `data`, `center`, `score`, `age`, `hits`) pass through unchanged. Failures land as V2 error dicts (`errorType`, `errorDesc`, `stackTrace`) on both the manager and individual handlers — neither raises.

## Dependencies on other V2 modules

- [V2.Tracking](Tracking.md) — imports `BaseTracker`, `TRACK_CLASS_KEY` from `V2.Tracking.BaseTracker` (`ObjectInteractionsManager.py:15`). Track-dict format must match.

## Used by

The custom agent and any monitor that wants pairwise interaction logic on top of raw tracks. [V2.Pipetting](Pipetting.md) consumes its own pipetting-interaction handler; [V2.MultiCamera](MultiCamera.md) consumes the events these handlers emit.

## Tests

- `Lumi-AI-Core/V2/ObjectInteractionsManager/test_ObjectInteractionsManager.py`
- Test runner: `Lumi-AI-Core/V2/ObjectInteractionsManager/run_tests.py`.

## Gotchas

- A handler whose `get_supported_class_names()` returns classes that are *not* present in the current frame's tracks gets called with empty `tracks` — handlers should treat that gracefully, not error.
- Duplicate registrations of the same class are silently overwritten.
- `tracksByClass` is keyed by *normalised* class name — handlers reading `tracks[i]["class"]` should use the same normalisation to be safe.

## See also

- [V2.Tracking](Tracking.md)
- [V2.Pipetting](Pipetting.md)
- [V2.MultiCamera](MultiCamera.md)
- [V2.Detection](Detection.md)
