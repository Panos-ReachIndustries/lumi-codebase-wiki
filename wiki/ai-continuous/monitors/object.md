---
name: object monitor (anonymiser)
description: Detects people, screens, and documents in a frame and publishes their polygons — used for live anonymisation overlays.
type: monitor
graph_node: monitors:object
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/object/anonymiser.py }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/Models/Pose/Mediapipe/MediapipePoseInference.py }
  - { repo: Lumi-AI-Core, path: V2/Machine/Screens/ScreenFinder.py }
  - { repo: Lumi-AI-Core, path: V2/Machine/Text/PaddleTextDetector.py }
  - { repo: Lumi-AI-Core, path: V2/Tracking/PolygonTrackerReference.py }
tags: [monitor]
---

# object monitor (anonymiser)

The `object` monitor — also known as the **anonymiser** — finds three things in every frame and publishes their polygons: people (from MediaPipe pose landmarks, hull-then-dilate-by-25%), screens (YOLO `ScreenFinder`), and documents (PaddleOCR text-region detection). The downstream consumer (typically the web client) uses the polygons to mask faces / monitors / paperwork before displaying or recording the feed.

Architecturally this is the most complex non-`custom` monitor: detection runs in a `ThreadPoolExecutor` across the three V2 modules in parallel (`anonymiser.py:332`), and a separate worker thread handles `PolygonTracker`-based smoothing and Kafka publishing via a bounded `queue.Queue` (`anonymiser.py:920`).

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/object/anonymiser.py`
- **Per-frame parallel detection:** `_process_single_frame` at `anonymiser.py:305`
- **Tracker / publisher worker:** `_tracker_worker` at `anonymiser.py:374`
- **Tests:** `Lumi-AI-Continuous/monitors/object/test_anonymiser.py`

## How it runs

```bash
# Local with display window (press 'q' to quit)
python monitors/object/anonymiser.py --config monitors/object/configs/default.json \
  --is_local --video path/to/video.mp4

# Production
python monitors/object/anonymiser.py --config path/to/config.json
```

## Inputs

- Standard `monitorId`, `pipeline`, `connection.resolution_*`.
- `ai.pose.{minDetectionConfidence, minTrackingConfidence, staticImageMode, modelComplexity, frameScale}` (`anonymiser.py:764`).
- `ai.text.{lang, enableMkldnn, maxImageSize, modelWeightsPath}` — falls back to `PADDLEOCR_LANG`, `PADDLEOCR_MODEL_WEIGHTS_PATH` env vars (`anonymiser.py:794-797`).
- `ai.screen.{weightsPath, confThreshold, imgsz}` — falls back to `SCREEN_WEIGHTS_PATH`. Screen detection is **silently disabled** if no weights file exists (`anonymiser.py:830`).
- `ai.processing.globalFrameScale` (default `1.0`) and `enableParallelDetection` (default `true`) for performance tuning.

## Outputs

Per frame, via `AnonymiserStreamReporter.data(...)` (`anonymiser.py:527`):

```json
{
  "streamOffline": false,
  "peoplePolygons":   [[[x, y], ...]],
  "screenPolygons":   [[[x, y], ...]],
  "documentPolygons": [[[x, y], ...]]
}
```

Coordinates are absolute pixels in the original frame size. Polygons are passed through three independent `PolygonTracker` instances (one per class) to suppress flicker (`anonymiser.py:879`); raw detections are used as a fallback if a tracker fails to initialise. The reporter applies `force_transmit_interval=10` / `changed_data_interval=1`, so unchanged frames are coalesced.

## V2 modules used

- [V2.ModelInference](../../ai-core/modules/ModelInference.md) — `MediapipePoseInference`.
- [V2.Machine](../../ai-core/modules/Machine.md) — `ScreenFinder`, `PaddleTextDetector`.
- [V2.Tracking](../../ai-core/modules/Tracking.md) — `PolygonTrackerReference.PolygonTracker`.

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.AnonymiserStreamReporter`
- `Common.common.convert_numpy_types` (the output dict goes through this before publish, `anonymiser.py:524`).

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md)

## Tests

- `Lumi-AI-Continuous/monitors/object/test_anonymiser.py`

## When it goes wrong

- **`screenPolygons` always empty** — `SCREEN_WEIGHTS_PATH` doesn't exist on the runtime image; screen detection is disabled silently with a debug log only.
- **High latency / dropped frames** — the `tracker_queue` is `maxsize=1` and old items are discarded when full (`anonymiser.py:1051`); set `enableParallelDetection: true` and reduce `globalFrameScale` to `0.5`.
- **People polygons are huge / blocky** — the 25% dilation in `_calculate_person_polygon` is intentional for anonymisation buffer; reduce by editing the constant if you need tighter masks.
- **Text detection misses small print** — bump `ai.text.maxImageSize`; default 1280 down-scales 4K frames.
- **GUI window doesn't appear** — only `--video` mode opens a window; production / Kafka mode is headless.

## See also

- [V2.Tracking](../../ai-core/modules/Tracking.md)
- [V2.Machine](../../ai-core/modules/Machine.md)
- [object_list monitor](object_list.md) — counts class instances rather than masking them.
- [Kafka topics](../../architecture/kafka-topics.md)
