---
name: V2.VisibleObjectList
description: A tracked-object registry with lifecycle — current visible counts, total ever-seen counts, and double-count prevention. Detection plus an internal IoU tracker plus a counter.
type: module
graph_node: core:VisibleObjectList
sources:
  - { repo: Lumi-AI-Core, path: V2/VisibleObjectList/VisibleObjectList.py }
tags: [v2-module]
---

# V2.VisibleObjectList

`VisibleObjectList` is the V2 module that answers "how many things are on the bench right now" *and* "how many have I seen total" without double-counting. It bundles a detector, an IoU-based internal tracker, and an item counter into one V2 entry point.

## What it does

A single class composes three pieces (`Lumi-AI-Core/V2/VisibleObjectList/VisibleObjectList.py`):

1. **Detection** — wraps a `GenericDetectorWrapper` from [V2.Detection](Detection.md) and runs it per frame. Filters out a hard-coded exclusion list (`"uncertain: uncertain"`, `"other_equipment: other_equipment"`, `"container: cylinder"`) and contained-bbox duplicates.
2. **Tracking** — an internal IoU `Tracker` matches detections frame-to-frame with configurable `tracker_iou_threshold` and `tracker_history_length`. Each track carries a *status score* (ratio of detections in the history window).
3. **Counting** — an `ItemCounter` filters tracks by status (`>= min_score_threshold`) for the current count, and tracks unique `track_id`s for the total count. The first time a `track_id` clears the threshold, it's added to totals; it never increments again.

This is the "smart count" pattern — flicker-tolerant, occlusion-tolerant, but still honest about uniqueness.

## Public API

V2 dict-in/dict-out:

- `VisibleObjectList({"frame_width", "frame_height", "task"?, "detector_config"?, "tracker_iou_threshold"?, "tracker_history_length"?, "min_score_threshold"?, "confidence_threshold"?})`
- `process_frame({"frame": np.ndarray, "config"?})` → `{"current_counts", "total_counts", "detections_count"}`
- `get_counts({})` — current + total without re-running detection.
- `get_all_tracked_objects({})` — every tracked object with `detection_id`, `class`, normalised `bbox`, `center`, `confidence` (track status), `is_visible`.
- `reset({})` — wipe tracker + counter for a new video.

Counts come back as `[{"name": "container: flask", "count": 5}, ...]`.

## Input / output

In: BGR frames, normalised bboxes from the detector. Out: count lists, tracked-object lists. Errors land as the standard `{"errorType", "errorDesc", "stackTrace"}` dict — see [agreedDataSchema.md](../data-schema.md).

## Dependencies on other V2 modules

- [V2.Detection](Detection.md) — `GenericDetectorWrapper` is the detector backbone.
- No external V2 tracker; the tracker and counter are internal to this module (deliberately simpler than [V2.Tracking](Tracking.md)'s NorfairSTM).

## Used by

Inventory-style monitors that report bench occupancy, plus any per-protocol "container present?" gating that doesn't need re-ID-grade tracking.

## Tests

- `Lumi-AI-Core/V2/VisibleObjectList/test_visible_object_list.py`

## Gotchas

- The exclusion list is hard-coded — if your domain needs `container: cylinder`, monkey-patch or fork.
- Objects that leave and re-enter the frame become *new* `track_id`s; total counts will tick upward. The README is explicit that this is "acceptable per requirements".
- `task="bboxes"` vs `"segmentation"` changes which detector runs; performance differs (3-6 FPS RCNN vs ~8 FPS YOLO seg on CPU).

## See also

- [V2.Detection](Detection.md)
- [V2.Tracking](Tracking.md) — the heavier-duty tracking option
- [agreedDataSchema.md](../data-schema.md)
