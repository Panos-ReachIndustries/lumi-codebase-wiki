---
name: colour monitor
description: Dominant colour analysis in regions of interest. The simplest monitor — a good template.
type: monitor
graph_node: monitors:colour
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/colour/colour.py }
  - { repo: Lumi-AI-Core, path: V2/Colours/ColourAnalyser.py }
tags: [monitor, exemplar]
---

# colour monitor

The `colour` monitor is the simplest production monitor in Lumi-AI-Continuous. If you read one monitor end-to-end, read this one — every other monitor follows the same pattern, just with different V2 modules.

## What it does

Given a video stream and a list of *regions of interest* (rectangles in normalised coordinates), it publishes the **dominant colour(s)** in each region per frame.

Used in protocols whenever a step depends on a vessel being a certain colour: blue → buffer added; pink → reaction underway; clear → reaction done.

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/colour/colour.py`
- **OpenAPI contract:** `Lumi-AI-Continuous/api/colour/openapi.yaml`
- **Algorithm:** `Lumi-AI-Core/V2/Colours/ColourAnalyser.py` (and `Colours.py`)
- **Config templates:** `Lumi-AI-Continuous/agent_definition_templates/colour.json`

## How it runs

```bash
# Local (Kafka bypassed)
python monitors/colour/colour.py \
  --config path/to/config.json \
  --is_local \
  --video path/to/video.mp4

# Production (Kafka)
python monitors/colour/colour.py --config path/to/config.json
```

The process reads frames from stdin or a video file, calls `ColourAnalyser.analyse(frame, regions)`, and prints structured results to stdout. In production, `monitor_relay` parses those `DATA: …` lines and publishes them to `MONITOR_DATA_TOPIC`.

## Inputs

- A *config* JSON: list of regions (each `{x, y, w, h, label}`), colour space settings, optional reference colour palettes.
- Video frames (BGR, OpenCV convention).

## Outputs

Per frame, per region:

```json
{
  "region": "vessel_a",
  "dominant_rgb": [180, 60, 70],
  "match": "pink",
  "confidence": 0.91
}
```

The full schema is in `api/colour/openapi.yaml`.

## Dependencies

- **V2 modules** imported: `V2.Colours.ColourAnalyser`. (Most other monitors also pull in `V2.Utils` for image / geometry helpers — `colour` does too, indirectly.)
- **Common** imported: `Common.common.StreamReporter` (subclass: `ColourStreamReporter`) and `Common.common.StreamCapture`.

## Why it's a good template

It's the smallest example of the full monitor pattern:

1. Parse args (config path, local mode, optional video).
2. Build a `StreamReporter` (Kafka in prod, stdout locally).
3. Build a `StreamCapture` (video file or WebRTC stdin).
4. Loop: pull frame → call V2 module → publish via reporter.
5. Trap signals so `monitor_relay` can shut it down cleanly.

Other monitors (e.g. `dial`, `text`, `liquids/*`) replace step 4 with their respective V2 modules.

## When it doesn't fire

- **Empty results** usually means the region rectangles don't intersect the frame. Check `--config` against the actual frame size.
- **Hangs on startup** is almost always a Kafka connection issue. Set `IS_LOCAL=true` to confirm.
- **Wrong colour palette** — `Colours.py` ships a default palette; pass a custom one via config.

## See also

- [V2 module: Colours](../../ai-core/modules/Colours.md)
- [Kafka topics](../../architecture/kafka-topics.md) — where `MONITOR_DATA_TOPIC` is documented
- [monitor_relay](../monitor-relay.md) — the supervisor that spawns this process
