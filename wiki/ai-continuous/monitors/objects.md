---
name: objects monitor
description: "Per-frame instance segmentation polygons via V2.Detection.ObjectSegmenter — currently scoped to the wellplate model."
type: monitor
graph_node: monitors:objects
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/objects/object_tracker.py }
  - { repo: Lumi-AI-Core, path: V2/Detection/ObjectSegmenter.py }
tags: [monitor]
---

# objects monitor

The `objects` monitor runs `V2.Detection.ObjectSegmenter` against every frame and publishes the resulting per-instance segmentation polygons. The entry file is named `object_tracker.py` for historical reasons, but no temporal tracking is performed — each frame is independent, identity is not preserved, and the V2 module returns segmentation masks projected to polygons (`object_tracker.py:198`, `ot.get_polygons(frame)`).

In production it is currently locked to a single model: `wellplate` (`object_tracker.py:128`). Any other `ai.model` value is rejected at startup. Treat this monitor as "fine-grained wellplate locator" rather than a general object segmenter — for that, use [V2.Detection](../../ai-core/modules/Detection.md) directly via the [custom monitor](custom.md).

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/objects/object_tracker.py`
- **V2 call:** `object_tracker.py:198`
- **Tests:** `Lumi-AI-Continuous/monitors/objects/test_object_tracker.py`

## How it runs

```bash
# Local
python monitors/objects/object_tracker.py --config path/to/config.json --is_local

# Production
python monitors/objects/object_tracker.py --config path/to/config.json
```

## Inputs

- Standard `monitorId`, `pipeline`, `connection.resolution_h/_w`.
- `ai.model` — must be `"wellplate"`; anything else exits with severity-3 error at startup (`object_tracker.py:128-132`).
- `ai.conf` (optional) — confidence threshold; default `0.36` for `wellplate`.
- Weights path is hard-coded as `/src/data/weights/{model_name}.pt` (`object_tracker.py:134`).
- Archive mode is supported.

## Outputs

Per frame, via `ObjectTrackerStreamReporter.data(...)` (`object_tracker.py:201`):

```json
{
  "streamOffline": false,
  "objects": [
    {
      "polygon": [[x1, y1], [x2, y2], ...],
      "confidence": 0.91,
      "class_name": "wellplate"
    }
  ]
}
```

The exact shape of each entry is whatever `ObjectSegmenter.get_polygons` returns; the monitor passes the list through unchanged. No polygon smoothing or temporal stitching.

## V2 modules used

- [V2.Detection](../../ai-core/modules/Detection.md) — specifically `ObjectSegmenter`.

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.ObjectTrackerStreamReporter`

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md)

## Tests

- `Lumi-AI-Continuous/monitors/objects/test_object_tracker.py`

## When it goes wrong

- **`Invalid model name` at startup** — only `wellplate` is allowed. Add the model to the `model_list` / `model_confs` arrays at `object_tracker.py:128-129` if you genuinely need another.
- **Empty `objects` list every frame** — confidence too high. Try `ai.conf: 0.2`.
- **Polygons jitter frame-to-frame** — expected; there is no temporal smoothing. Wrap with a `PolygonTracker` consumer if needed (see [object monitor](object.md)).
- **Weights file missing** — `/src/data/weights/wellplate.pt` must be present in the runtime image.
- **No `monitorStatus: COMPLETE` on archive end** — handled, but only after the `processToTimestamp` window elapses (`object_tracker.py:203-216`).

## See also

- [V2.Detection](../../ai-core/modules/Detection.md)
- [V2.WellPlate](../../ai-core/modules/WellPlate.md) — typical downstream consumer.
- [object monitor](object.md) — polygons for people / screens / docs with tracking.
- [Kafka topics](../../architecture/kafka-topics.md)
