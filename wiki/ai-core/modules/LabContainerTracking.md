---
name: V2.LabContainerTracking
description: Tracks lab containers across frames and maintains an event-sourced substance inventory with provenance queries.
type: module
graph_node: core:LabContainerTracking
sources:
  - { repo: Lumi-AI-Core, path: V2/LabContainerTracking/LabContainerTrackingPipeline.py }
  - { repo: Lumi-AI-Core, path: V2/LabContainerTracking/_tracker.py }
  - { repo: Lumi-AI-Core, path: V2/LabContainerTracking/_substance_flow_tracker.py }
tags: [v2-module]
---

# V2.LabContainerTracking

`LabContainerTracking` is the V2 module that turns a stream of bbox detections into a *durable* model of "which container is which, what's in it, and how it got there". It is the bridge between per-frame vision and a stateful lab-inventory record; lab monitors lean on it whenever provenance matters.

## What it does

The pipeline ingests detections (or runs a `Detection` wrapper inline), assigns persistent `track_id`s with an IoU-based `InstanceTracker` (`Lumi-AI-Core/V2/LabContainerTracking/_tracker.py`), maps each track to a logical container in a `SceneRegistry`, and projects an append-only `EventStore` of transfers into a current inventory via `StateProjector`. A `SubstanceFlowTracker` diffs successive inventories and emits transfer events. A `QueryAPI` then answers provenance questions against that state.

## Public API

The single entry point is `LabContainerTrackingPipeline` (`Lumi-AI-Core/V2/LabContainerTracking/LabContainerTrackingPipeline.py:17`). Methods, all V2-style dict-in/dict-out:

- `process_frame(input_data)` — main per-frame call. Takes `{"detections": [...]}` (or `{"frame": np.ndarray}` when `use_external_detections=False`) and returns `tracked_instances`, `inventory`, `transfer_events`.
- `get_current_location({"substance_lot_id": ...})` — where a substance lot is right now.
- `get_container_contents({"container_id": ...})` — items currently in a container.
- `trace_substance({"substance_lot_id": ...})` — full provenance trail.
- `list_inventory({...})` — filtered inventory listing.
- `reset({})` — clear all state between videos.

## Input / output

Input detections conform to the bbox shape from [agreedDataSchema.md](../data-schema.md). Outputs are V2 dicts; failures land as `{"errorType": ..., "errorDesc": ..., "stackTrace": ...}` rather than exceptions.

## Dependencies

- [V2.Detection](Detection.md) — used inline when `use_external_detections=False` (`LabContainerTrackingPipeline.py:78`).
- numpy, opencv-python.
- Config at `V2/LabContainerTracking/config/lab_tracking_config.json` (container class mapping, IoU threshold, history length).

## Used by

Lab-bench monitors that need cross-frame container identity and substance provenance (alongside [V2.Pipetting](Pipetting.md)). The custom-agent pipeline composes it after `Detection`.

## Tests

- `Lumi-AI-Core/V2/LabContainerTracking/test_LabContainerTracking.py`
- Fixtures: `Lumi-AI-Core/V2/LabContainerTracking/test_fixtures.py` (`make_beaker_detections`, `make_moving_beaker_sequence`).
- Evaluation harness: `Lumi-AI-Core/V2/LabContainerTracking/run_evaluation.py`.

## Gotchas

- `class_name` strings must match `container_class_mapping` in the config — mismatches silently fall back to `default_container_type` (`unknown_container`).
- The pipeline buffers detections in a `deque`; if you feed sparse frames, recent history can dominate `tracked_instances`.
- Call `reset()` between unrelated videos — `EventStore` is append-only and persists otherwise.

## See also

- [V2.Detection](Detection.md)
- [V2.Tracking](Tracking.md)
- [agreedDataSchema.md](../data-schema.md)
- [V2.Pipetting](Pipetting.md)
