---
name: dial monitor
description: Reads analogue needle gauges/dials — locates the gauge, finds keypoints, computes the value.
type: monitor
graph_node: monitors:dial
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/dial/gauge_reader.py }
  - { repo: Lumi-AI-Core, path: V2/Machine/GaugeReader/GaugeReader.py }
tags: [monitor]
---

# dial monitor

The `dial` monitor reads analogue needle gauges from a video stream. Each frame: detect every gauge in view (YOLO), pick the one whose bbox contains the configured `centre` point, run keypoint regression to find the centre and needle tip, and compute a numeric reading from the configured `minValue` / `maxValue` / `units` calibration. It is the production replacement for the legacy `needle_gauge.py` monitor — the `dial` config still uses the same `ai.needle.centre` / `ai.meter.{minValue,maxValue,units,minValuePoint,maxValuePoint}` shape.

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/dial/gauge_reader.py`
- **Per-frame pipeline:** `gauge_reader.py:290` (`gauge_reader.find_gauges` → `_is_centre_within_bbox` → `gauge_reader.run_continuous_monitor`)
- **Tests:** `Lumi-AI-Continuous/monitors/dial/test_gauge_reader.py`

## How it runs

```bash
# Local
python monitors/dial/gauge_reader.py --config path/to/config.json --is_local

# Production
python monitors/dial/gauge_reader.py --config path/to/config.json
```

## Inputs

`args.ai.needle.centre`, `args.ai.meter.{minValuePoint, maxValuePoint, minValue, maxValue, units}` — read at `gauge_reader.py:235-240`. YOLO and keypoint weights come from `args.ai.yoloModelWeights` / `keypointModelWeights`, falling back to `GAUGE_YOLO_WEIGHTS` / `GAUGE_KEYPOINT_WEIGHTS` env vars and finally the bundled `/src/data/weights/yolo_gauge_detector_v2.pt` / `resnet_heatmap_v7.pth` (`gauge_reader.py:25, 167`).

## Outputs

Per frame, via `GaugeStreamReporter.data(...)`:

```json
{
  "streamOffline": false,
  "value": 12.5,
  "units": "psi",
  "needleDirection": [0.21, -0.98]
}
```

When no gauge is detected, when the configured centre point isn't inside any detected gauge bbox, or when `run_continuous_monitor` errors, the same shape is published with `value: null`, `needleDirection: null`, and an `error` string explaining why (`gauge_reader.py:301-357`). Values are clipped to the calibrated range via `_clip_gauge_value` (`gauge_reader.py:81`), which handles reversed scales where `minValue > maxValue`.

## V2 modules used

- [V2.Machine](../../ai-core/modules/Machine.md) — specifically `V2.Machine.GaugeReader.GaugeReader`.

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.GaugeStreamReporter` — the dial-specific StreamReporter subclass.

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md)

## Tests

- `Lumi-AI-Continuous/monitors/dial/test_gauge_reader.py`

## When it goes wrong

- **`"selected gauge is not detected in frame!"`** — multiple gauges were detected but none of their bboxes contains `ai.needle.centre`. Re-check the centre point coordinates relative to the camera view.
- **`"No gauge detected in frame!"`** — YOLO confidence too low or wrong weights. Try `GAUGE_YOLO_WEIGHTS=...`.
- **Value pinned at `minValue` or `maxValue`** — `_clip_gauge_value` is doing its job; the underlying keypoint regression returned an out-of-range value. Inspect needle visibility.
- **`needleDirection` always `[0,0]`** — `centre` and `needleTip` keypoints landed on the same pixel; check the keypoint weights file (`gauge_reader.py:46`).
- **Reversed-scale gauges read backwards** — supported, but you must set `minValue > maxValue` in config.

## See also

- [V2.Machine](../../ai-core/modules/Machine.md)
- [Kafka topics](../../architecture/kafka-topics.md)
- [monitor_relay](../monitor-relay.md)
- [text monitor](text.md) — companion for digital readouts.
