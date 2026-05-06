---
name: 3DCalc monitor
description: "Per-frame 3D object detection and depth estimation: YOLO + MiDaS + Dimensions."
type: monitor
graph_node: monitors:3DCalc
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/3DCalc/3DCalc.py }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/Models/YOLO/YoloInference.py }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/Models/Midas/MidasInference.py }
  - { repo: Lumi-AI-Core, path: V2/Dimensions/Dimensions.py }
tags: [monitor]
---

# 3DCalc monitor

The `3DCalc` monitor runs a three-stage V2 pipeline against every incoming video frame: a YOLO detector finds 2D bounding boxes, MiDaS produces a dense depth map, and `V2.Dimensions` lifts the boxes into 3D using that depth. The output is a list of detections enriched with min/max/avg depth and a 3D bounding box.

It is the monitor used whenever a step needs "where is this object in space, not just on screen?" — typical use is reasoning about object placement on a benchtop or inside a fume hood.

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/3DCalc/3DCalc.py`
- **V2 pipeline call:** `_detect_3d_objects` at `Lumi-AI-Continuous/monitors/3DCalc/3DCalc.py:50`
- **Tests:** `Lumi-AI-Continuous/monitors/3DCalc/test_3DCalc.py`

## How it runs

```bash
# Local
python monitors/3DCalc/3DCalc.py --config path/to/config.json --is_local

# Production (Kafka)
python monitors/3DCalc/3DCalc.py --config path/to/config.json
```

## Inputs

The config under `args` must supply `monitorId`, `pipeline`, and `connection.resolution_h/_w` — these are validated up front via `validate_config_structure` (`3DCalc.py:128`). Optional `ai.yolo_weights_path`, `ai.midas_weights_path`, and `ai.confidence` (default `0.5`) override the defaults `./weights/yolo_best_v11m.pt` and `./weights/midas_v21_small_256.pt` (`3DCalc.py:224`). Archive mode (`startTimestamp` / `processFromTimestamp` / `processToTimestamp`) is supported and seeks via `LocalStreamCapture`.

## Outputs

Per frame, via `reporter.data(...)` (`3DCalc.py:318`):

```json
{
  "streamOffline": false,
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.87,
      "class_id": 3,
      "class_name": "vessel",
      "min_depth": 0.42,
      "max_depth": 0.78,
      "avg_depth": 0.61,
      "bbox_3d": [...]
    }
  ]
}
```

Note the snake_case keys — they are deliberately mapped from the V2 camelCase response for backward compatibility (`3DCalc.py:88-101`).

## V2 modules used

- [V2.ModelInference](../../ai-core/modules/ModelInference.md) (YoloInference, MidasInference)
- [V2.Dimensions](../../ai-core/modules/Dimensions.md)

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture` (frame source)
- `Common.common.GenericStreamReporter` (no specialised subclass — uses generic with `enable_print=True`)
- `Common.common.validate_config_structure`

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md) — all `reporter.data(...)` payloads.

## Tests

- `Lumi-AI-Continuous/monitors/3DCalc/test_3DCalc.py`

## When it goes wrong

- **Empty `detections` always** — YOLO predicted nothing or returned `errorType`. Lower `ai.confidence` or check the weights path (`3DCalc.py:65`).
- **All depth fields are 0/None** — MiDaS returned `errorType`; commonly a wrong `midas_weights_path` (V2 expects a `.pt` file, not a model name like `MiDaS_small`).
- **Config rejected at startup** — `validate_config_structure` reports the missing keys via `produce_error` and exits.
- **Hangs on Kafka startup** — set `--is_local` to bypass; otherwise check `MSK_BROKERS`.
- **OOM on long archives** — explicit `del frame` in the hot loop (`3DCalc.py:321`) keeps memory steady; if you fork the loop, preserve it.

## See also

- [V2.Dimensions](../../ai-core/modules/Dimensions.md)
- [V2.ModelInference](../../ai-core/modules/ModelInference.md)
- [Kafka topics](../../architecture/kafka-topics.md)
- [monitor_relay](../monitor-relay.md)
