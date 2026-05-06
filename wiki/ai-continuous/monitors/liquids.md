---
name: liquids monitor family
description: "Six related monitors for liquid analysis: volume, colour, precipitation, and phase separation in vessels."
type: monitor
graph_node: monitors:liquids
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/liquids/liquid_volume.py }
  - { repo: Lumi-AI-Continuous, path: monitors/liquids/liquid_description.py }
  - { repo: Lumi-AI-Continuous, path: monitors/liquids/liquid_volume_yolo.py }
  - { repo: Lumi-AI-Continuous, path: monitors/liquids/liquid_description_yolo.py }
  - { repo: Lumi-AI-Continuous, path: monitors/liquids/liquid_precipitation.py }
  - { repo: Lumi-AI-Continuous, path: monitors/liquids/phase_liquid_description.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/LiquidAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/Vessels/PhaseAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/Colours/ColourAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/Models/YOLO/YoloInference.py }
tags: [monitor, family]
---

# liquids monitors

The `liquids/` directory ships **six** distinct monitors that all answer questions about liquid inside a vessel. They share the same scaffolding (config, archive mode, `LiquidStreamReporter`, `polygons_to_mask`) and converge on the same V2 building blocks — but differ in *what* they publish and which subset of `LiquidAnalyser` / `PhaseAnalyser` / `ColourAnalyser` / YOLO they use.

| Variant | Entry .py | What it publishes | V2 modules |
|---------|-----------|-------------------|-----------|
| Volume | `liquid_volume.py` | `liquidPolygons`, `estimatedVolume` | YoloInference (`materials.pt`, segment task), `LiquidAnalyser` |
| Volume (YOLO-only) | `liquid_volume_yolo.py` | same as Volume | YoloInference, `LiquidAnalyser` (older path; bypasses some smoothing) |
| Description | `liquid_description.py` | Volume fields plus `liquidColourInfo` (dominant colours per polygon) | YoloInference, `LiquidAnalyser`, `ColourAnalyser` |
| Description (YOLO-only) | `liquid_description_yolo.py` | same as Description | YoloInference, `LiquidAnalyser`, `ColourAnalyser` |
| Precipitation | `liquid_precipitation.py` | `precipitate` (bool), `homogeneity`, `contrast`, `relativeOpacity` | `ColourAnalyser` only |
| Phase + description | `phase_liquid_description.py` | Description fields plus per-phase breakdown | YoloInference, `LiquidAnalyser`, `ColourAnalyser`, `PhaseAnalyser` |

The "yolo" suffix doesn't mean a different detector — both branches use YOLO segmentation on `materials.pt`. The `_yolo` variants are the older/simpler code paths kept around for compatibility; new work should go on the unsuffixed versions.

## Where the code lives

- All entries: `Lumi-AI-Continuous/monitors/liquids/*.py`
- Shared tests: `monitors/liquids/test_liquids.py`

## How they run

Identical CLI for every variant:

```bash
# Local
python monitors/liquids/<variant>.py --config path/to/config.json --is_local

# Production
python monitors/liquids/<variant>.py --config path/to/config.json
```

`liquid_description.py` and `phase_liquid_description.py` additionally accept `--video <path>` to open a debug GUI window.

## Inputs

Common config keys (`liquid_volume.py:131-145`):

- `args.ai.vessel_polygon` — pixel polygon delineating the vessel; rasterised once at startup via `polygons_to_mask`.
- `args.ai.vessel_volume` — total vessel capacity (float). Used to compute `pix2ml = vessel_volume / vessel_mask_pixel_count` and convert detected liquid pixels to millilitres.
- `args.ai.vessel_units` — units string (default `ml`).
- Standard `monitorId`, `pipeline`, `connection.resolution_*`, archive timestamps.

`liquid_precipitation.py` instead reads a polygon ROI and uses three thresholds — `HOMOGENEITY_THRESHOLD`, `CONTRAST_THRESHOLD`, `OPACITY_THRESHOLD` — currently hard-coded as module constants (`liquid_precipitation.py:217`).

## Outputs

Per frame, via `LiquidStreamReporter.data(...)`. Schemas vary by variant:

```json
// liquid_volume / liquid_volume_yolo
{ "streamOffline": false, "liquidPolygons": [...], "estimatedVolume": 12.3 }

// liquid_description / liquid_description_yolo
{ "streamOffline": false, "liquidPolygons": [...], "estimatedVolume": 12.3,
  "liquidColourInfo": [{"dominantColours": [[r,g,b], ...]}] }

// liquid_precipitation
{ "streamOffline": false, "precipitate": true,
  "homogeneity": 0.4, "contrast": 22.1, "relativeOpacity": 0.7 }

// phase_liquid_description
{ "streamOffline": false, "liquidPolygons": [...], "estimatedVolume": 12.3,
  "liquidColourInfo": [...], /* plus per-phase breakdown */ }
```

The full per-frame pipeline for the volume/description variants is: YOLO segment → `LiquidAnalyser.remove_liquid_outside_vessel` → `LiquidAnalyser.fill_liquid_within_vessel` → `mask_to_polygons(min_area=3000)` (`liquid_volume.py:207-234`). Volume comes from `pixel_count * pix2ml`; if no polygon survives the area filter, volume is forced to 0 to keep the two fields consistent (`liquid_volume.py:237`).

`phase_liquid_description.py` adds `V2.Vessels.PhaseAnalyser` to split the liquid mask into stratified phases and reports `liquidColourInfo` per phase.

## V2 modules used

- [V2.Vessels](../../ai-core/modules/Vessels.md) — `LiquidAnalyser`, `PhaseAnalyser`.
- [V2.Colours](../../ai-core/modules/Colours.md) — `ColourAnalyser`.
- [V2.ModelInference](../../ai-core/modules/ModelInference.md) — `YoloInference` with `materials.pt` weights.

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.LiquidStreamReporter` (used by all six variants; `force_transmit_interval=10`, `changed_data_interval=1` on the description variants).
- `Common.common.polygons_to_mask`, `Common.common.mask_to_polygons` (with `min_area=3000` for liquid).

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md) — all variants.

## Tests

- `Lumi-AI-Continuous/monitors/liquids/test_liquids.py`

## When it goes wrong

- **`Vessel mask is empty (zero area)`** — your `vessel_polygon` is outside the frame or has fewer than 3 points. Check pixel coords against `connection.resolution_*`.
- **Volume jumps to 0 or non-zero erratically** — YOLO confidence noise. The `min_area=3000` polygon filter and the consistency check at `liquid_volume.py:237` exist precisely to suppress this; tighten further by raising `min_area`.
- **Always reads `precipitate: false`** — three thresholds must all pass; reduce one in `liquid_precipitation.py:217` to characterise your specific reagent.
- **Description variants publish empty `liquidColourInfo`** — empty when no liquid polygon survives, which then short-circuits the colour pass (`liquid_description.py:325-337`).
- **Wrong choice of variant** — quick rule: just need volume → `liquid_volume`. Need colour too → `liquid_description`. Need to detect particles forming → `liquid_precipitation`. Have layered phases → `phase_liquid_description`.

## See also

- [V2.Vessels](../../ai-core/modules/Vessels.md)
- [V2.Colours](../../ai-core/modules/Colours.md)
- [V2.ModelInference](../../ai-core/modules/ModelInference.md)
- [homogeneity monitor](homogeneity.md) — `liquid_precipitation` is essentially homogeneity+contrast+opacity with a threshold.
- [Kafka topics](../../architecture/kafka-topics.md)
