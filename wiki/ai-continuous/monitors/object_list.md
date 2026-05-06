---
name: object_list monitor
description: "Counts visible objects per class — current and cumulative — using V2.VisibleObjectList."
type: monitor
graph_node: monitors:object_list
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/object_list/visible_object_list.py }
  - { repo: Lumi-AI-Core, path: V2/VisibleObjectList/VisibleObjectList.py }
tags: [monitor]
---

# object_list monitor

The `object_list` monitor publishes two count vectors per frame: `currentItems` (what is visible right now) and `totalItems` (cumulative unique objects since the monitor started). Both come from a single call to `V2.VisibleObjectList.process_frame` (`visible_object_list.py:187`), which internally runs detection plus a lightweight tracker to deduplicate objects across frames.

This is the monitor for "how many tip racks are on the bench?" or "how many vials have appeared during this run?" questions — useful for inventory and step-completion checks where you don't need pose or geometry, just counts.

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/object_list/visible_object_list.py`
- **V2 call:** `visible_object_list.py:187`
- **Tests:** `Lumi-AI-Continuous/monitors/object_list/test_visible_object_list.py`

## How it runs

```bash
# Local with optional video override
python monitors/object_list/visible_object_list.py \
  --config /src/configs/visible_object_list.json --is_local --video path/to/video.mp4

# Production
python monitors/object_list/visible_object_list.py --config path/to/config.json
```

## Inputs

- Standard `monitorId`, `pipeline`, `connection.resolution_h/_w`.
- The V2 module is initialised with hard-coded thresholds at `visible_object_list.py:123` — `task: "bboxes"`, `tracker_iou_threshold: 0.2`, `tracker_history_length: 10`, `min_score_threshold: 0.7`, `confidence_threshold: 0.5`. None of these are exposed via the JSON config.
- Archive mode (`startTimestamp` / `processFromTimestamp` / `processToTimestamp`) is supported.

## Outputs

Per frame, via `GenericStreamReporter.data(...)` (`visible_object_list.py:215`):

```json
{
  "streamOffline": false,
  "currentItems": [
    {"className": "vial", "count": 3},
    {"className": "tip_rack", "count": 1}
  ],
  "totalItems": [
    {"className": "vial", "count": 5},
    {"className": "tip_rack", "count": 1}
  ]
}
```

Exact entry shape comes from `V2.VisibleObjectList`'s `current_counts` / `total_counts` — the monitor passes them through unchanged. On V2 errors (`errorType` in result) the frame is dropped with a `produce_error` and the loop continues (`visible_object_list.py:195-203`).

## V2 modules used

- [V2.VisibleObjectList](../../ai-core/modules/VisibleObjectList.md)

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.GenericStreamReporter` (no specialised subclass)

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md)

## Tests

- `Lumi-AI-Continuous/monitors/object_list/test_visible_object_list.py`

## When it goes wrong

- **`totalItems` keeps climbing during reruns** — counts are cumulative for the lifetime of the process; restart to reset.
- **Object disappears and reappears as a new id** — `tracker_history_length: 10` (frames) is the gap budget; longer occlusions create new entries in `totalItems`.
- **No detections** — the V2 module ships its own model; weights are loaded internally. Check the `Lumi-AI-Core` version pinned in your image.
- **Need different thresholds** — currently you must edit the constructor call in `visible_object_list.py:123`; there is no config knob.
- **Hangs on Kafka startup** — set `--is_local`; otherwise check `MSK_BROKERS`.

## See also

- [V2.VisibleObjectList](../../ai-core/modules/VisibleObjectList.md)
- [object monitor](object.md) — polygon-based, anonymisation-focused.
- [objects monitor](objects.md) — segmentation polygons for a single named model.
- [Kafka topics](../../architecture/kafka-topics.md)
