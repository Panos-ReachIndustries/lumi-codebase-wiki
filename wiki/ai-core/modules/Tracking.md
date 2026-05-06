---
name: V2.Tracking
description: Multi-object tracking — class-routed Norfair STM tracker with motion-aware Kalman, appearance re-ID, and a polygon variant. The default downstream of any V2 detector.
type: module
graph_node: core:Tracking
sources:
  - { repo: Lumi-AI-Core, path: V2/Tracking/TrackerManager.py }
  - { repo: Lumi-AI-Core, path: V2/Tracking/BaseTracker.py }
  - { repo: Lumi-AI-Core, path: V2/Tracking/BoxTrackerNorfairSTM.py }
  - { repo: Lumi-AI-Core, path: V2/Tracking/PolygonTrackerReference.py }
tags: [v2-module]
---

# V2.Tracking

`Tracking` is the V2 module that consumes per-frame [V2.Detection](Detection.md) output and threads identity through time. It is the second-most-imported piece of V2 vision infrastructure — almost every monitor that wants stable IDs runs detections through it.

## What it does

The production tracker is `NorfairSTMTracker` (a wrapper around the Norfair multi-object tracker, in `Lumi-AI-Core/V2/Tracking/BoxTrackerNorfairSTM.py`). It combines:

- **Motion-aware Kalman filtering** for next-frame box prediction;
- **Appearance re-ID** with RGB/HSV histograms over a Short-Term-Memory (STM) buffer, so tracks survive occlusions;
- **Active/inactive states** — lost tracks linger in memory for `Inactive_tracks_max_age` frames before being evicted;
- **Class-aware behaviour** — `class_type="hand"` caps tracks at 2 and prefixes IDs with `H_`; `class_type="object"` is unlimited.

A `PolygonTracker` variant lives in `PolygonTrackerReference.py` for shapes that aren't axis-aligned (silhouettes, screens). `BoxTrackerIoU` and `BoxTrackerPassthrough` are simpler/test fallbacks.

## Public API

All trackers subclass `BaseTracker` (`Lumi-AI-Core/V2/Tracking/BaseTracker.py:25`) and use V2 dict I/O:

- `NorfairSTMTracker({"frame_width", "frame_height", "class_type", ...})` → `.update_tracks({"detections", "frame"})` → `{"tracks": [...]}`.
- `PolygonTracker({"trackerType", ...})` → `.update_tracks({"detections": [{polygon, class, score}]})`.
- `TrackerManager({"routing": {class_name: tracker_id}})` (`TrackerManager.py:14`) — registers multiple tracker instances and routes detections by class. Output schema: `{"tracks": [...]}` with each track carrying `track_id`, `formatted_id`, `class`, `box`, `score`.

## Input / output

In: detections in the bbox shape from [agreedDataSchema.md](../data-schema.md), plus the raw `frame` (required for appearance matching). Out: tracked objects with persistent IDs in normalised coordinates. Failures return `{"errorType", "errorDesc", "stackTrace"}`.

## Dependencies on other V2 modules

- [V2.Detection](Detection.md) — upstream source of per-frame inputs.
- Internal: vendored `Norfair_STM/` directory bundling the Norfair fork.
- External: `numpy`, `opencv-contrib-python`, `scipy`, `filterpy`.

## Used by

- [V2.LabContainerTracking](LabContainerTracking.md) — wraps tracking with persistent container identity.
- [V2.ObjectInteractionsManager](ObjectInteractionsManager.md) — consumes track outputs for interaction logic.
- [V2.Vortexing](Vortexing.md) — operates on `tracks` from a `TrackingStep`.
- [V2.VisibleObjectList](VisibleObjectList.md) — uses an internal IoU tracker, but follows the same pattern.

## Tests

- `Lumi-AI-Core/V2/Tracking/test_tracking.py`
- `Lumi-AI-Core/V2/Tracking/test_TrackerManager.py`

## Gotchas

- Coordinates are normalised on the wire but the tracker needs `frame_width`/`frame_height` to convert internally — get those wrong and matching breaks silently.
- `class_type="hand"` quietly caps you at 2 tracks. If you need >2 hand tracks, use `class_type="object"`.
- Appearance matching needs the `frame` array on every `update_tracks` call, even if you're feeding pre-computed detections.

## See also

- [V2.Detection](Detection.md) — upstream contract
- [V2.LabContainerTracking](LabContainerTracking.md) — track-aware container identity
- [agreedDataSchema.md](../data-schema.md)
