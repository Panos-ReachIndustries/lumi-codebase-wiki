---
name: V2.Pipetting
description: Detects Aspirate / Dispense pipetting actions from video using a temporal state machine over hand, tool, and container detections.
type: module
graph_node: core:Pipetting
sources:
  - { repo: Lumi-AI-Core, path: V2/Pipetting/PipettingPipeline.py }
  - { repo: Lumi-AI-Core, path: V2/Pipetting/_action_engine.py }
  - { repo: Lumi-AI-Core, path: V2/Pipetting/_action_detector.py }
  - { repo: Lumi-AI-Core, path: V2/Pipetting/pipetting_manager.py }
tags: [v2-module]
---

# V2.Pipetting

`Pipetting` is the V2 module that turns per-frame detections (hands, pipette/hand_tool, vials, plates) into discrete pipetting actions: `Aspirate`, `Dispense`, or `None`. It is a complete V2 rewrite — *not* the legacy `PipettingAction` package — and is one of the modules most heavily used by lab monitors.

## What it does

`PipettingPipeline` (`Lumi-AI-Core/V2/Pipetting/PipettingPipeline.py:17`) coordinates annotation loading, optional ML-based tip prediction, and the action engine. The core logic lives in `_action_engine.py` as a **state-machine** over per-frame geometry: hand–tool overlap detects "pipette held"; thumb-on-plunger detects "plunger pressed"; tool–container overlap with hysteresis selects an `activeContainerId`; an N-frame temporal smoother confirms an `Aspirate`/`Dispense` action keyed by container class (vial → Aspirate, plate → Dispense). `_action_detector.py` provides the geometry primitives (`bbox_overlap_ratio`, `bbox_min_distance`, `thumb_on_plunger`).

## Public API

- `PipettingPipeline({...})` — construct (annotation paths, class lists, thresholds, optional `tipPredictor`).
- `process_frame({"frameNumber", "frameWidth", "frameHeight", "tipCenter"?, "externalDetections"?, "frameImage"?, "tipPredictionMode"?})` → `{"frame", "pipetteHeld", "plungerPressed", "lowlevelAction", "highlevelAction", "activeContainerId", "activeContainerClass", "handToolOverlap", "toolContainerOverlap", "tipCenter"}`.
- `reset_state({})` — clear temporal buffers between videos.
- `get_statistics({})` — per-class detection counts and frame range.

Submodules (lazy): `PipetteTipPredictor` (MLP + CNN tip prediction from hand landmarks), `PipetteVolumeReader` (EfficientNet + digit recognition), `PipetteTipState` (TipAttached / TipDetached). `pipetting_manager.py` exposes a higher-level integration when `enableTipStateDetection=True`.

## Input / output

External detections follow the bbox shape from [agreedDataSchema.md](../data-schema.md). Errors land as `{"errorType": ..., "errorDesc": ..., "stackTrace": ...}` rather than raising.

## Dependencies on other V2 modules

- [V2.ModelInference](ModelInference.md) — `EfficientNet` for the volume reader's window-visibility classifier (optional).
- Hand keypoints assumed to be in MediaPipe 21-landmark format.

## Used by

Lab monitors that watch pipetting-heavy protocols (the per-task brief explicitly calls out `Pipetting` as a lab-monitor dependency). The custom agent can wire it in, often paired with [V2.LabContainerTracking](LabContainerTracking.md) for substance provenance.

## Tests

- `Lumi-AI-Core/V2/Pipetting/test_pipetting.py`
- `Lumi-AI-Core/V2/Pipetting/test_pipetting_pipeline.py`
- `Lumi-AI-Core/V2/Pipetting/test_pipetting_manager_integration.py`
- `Lumi-AI-Core/V2/Pipetting/test_PipetteTipState.py`

## Gotchas

- Stateful: frames must be processed in order; `reset_state({})` between videos.
- Action assignment is *container-class-driven* — if your detection class names don't match `containerClasses` (default `['Plate', 'Vial', 'Container']`), no action is ever emitted.
- `tipPredictor` requires hand landmarks with exactly 21 keypoints.
- `PipetteActionIdentifier` (legacy) is still re-exported for backward compatibility but is deprecated; prefer `PipettingPipeline`.

## See also

- [V2.LabContainerTracking](LabContainerTracking.md)
- [V2.ObjectInteractionsManager](ObjectInteractionsManager.md)
- [V2.Detection](Detection.md)
- [V2.Tracking](Tracking.md)
