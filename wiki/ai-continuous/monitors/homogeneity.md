---
name: homogeneity monitor
description: Tracks homogeneity and contrast inside a polygon ROI — used to detect mixing / settling / precipitation.
type: monitor
graph_node: monitors:homogeneity
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/homogeneity/homogeneity.py }
  - { repo: Lumi-AI-Core, path: V2/Colours/ColourAnalyser.py }
tags: [monitor]
---

# homogeneity monitor

The `homogeneity` monitor publishes two scalars per frame — `homogeneity` and `contrast` — for a single polygon region of interest. Both come from `V2.Colours.ColourAnalyser.get_homogeneity_stats` (`homogeneity.py:192`). It's the cheapest "is this liquid mixed yet?" signal in the system: no detector, no tracker, just OpenCV-grade colour stats inside a fixed mask.

Protocols use it to gate steps like "vortex until homogeneous" or "wait for precipitate to form" (low homogeneity + high contrast).

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/homogeneity/homogeneity.py`
- **V2 call:** `homogeneity.py:192` (`ca.get_homogeneity_stats({"image": frame, "mask": region_mask})`)
- **Tests:** `Lumi-AI-Continuous/monitors/homogeneity/test_homogeneity.py`

## How it runs

```bash
# Local
python monitors/homogeneity/homogeneity.py --config path/to/config.json --is_local

# Production
python monitors/homogeneity/homogeneity.py --config path/to/config.json
```

## Inputs

- `args.ai.region_polygon` — list of `[x, y]` points defining the ROI in pixel coordinates (`homogeneity.py:129`).
- `args.connection.resolution_h/_w` — used to rasterise the polygon to a mask via `Common.common.polygons_to_mask` (`homogeneity.py:131`).
- Standard `monitorId`, `pipeline`, archive timestamps.

The ROI mask is built **once** at startup; if your camera moves, the readings will be wrong. Multi-region monitoring is not supported here — use multiple monitor instances instead.

## Outputs

Per frame, via `HomogeneityStreamReporter.data(...)` (`homogeneity.py:208`):

```json
{
  "streamOffline": false,
  "homogeneity": 0.83,
  "contrast": 12.4
}
```

Values come straight from `ColourAnalyser`. Higher homogeneity means more uniform colour inside the mask; higher contrast means more variation. On V2 errors the monitor reports via `produce_error` and continues (or exits with `monitorStatus: FAILED` in archive mode, `homogeneity.py:194-204`).

## V2 modules used

- [V2.Colours](../../ai-core/modules/Colours.md) — `ColourAnalyser.get_homogeneity_stats`.

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.HomogeneityStreamReporter`
- `Common.common.polygons_to_mask`

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md)

## Tests

- `Lumi-AI-Continuous/monitors/homogeneity/test_homogeneity.py`

## When it goes wrong

- **Empty region mask exit** — the polygon falls entirely outside the configured `resolution_h/_w`. Check the polygon coords are in pixels, not normalised.
- **Constant readings** — your polygon includes static background (vessel rim, table edge); shrink it.
- **`Vessel mask is empty` look-alike** — actually `polygons_to_mask` returning all zeros; same fix.
- **Camera drift over long runs** — there's no re-detection; the mask is hard-coded at startup. Use the [object monitor](object.md) or a vessel tracker upstream if drift is expected.
- **`Failed to initialise colour analyser (V2)`** — usually a dependency mismatch on `Lumi-AI-Core`.

## See also

- [V2.Colours](../../ai-core/modules/Colours.md)
- [colour monitor](colour.md) — sibling using the same V2 module.
- [liquids monitors](liquids.md) — `liquid_precipitation` combines homogeneity, contrast, and opacity.
- [Kafka topics](../../architecture/kafka-topics.md)
