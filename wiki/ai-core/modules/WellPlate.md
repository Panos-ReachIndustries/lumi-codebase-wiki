---
name: V2.WellPlate
description: A small dataclass + display-name mapper that represents a multi-well plate consistently across cameras (cam1 sees segmentation, cam3 sees a grid).
type: module
graph_node: core:WellPlate
sources:
  - { repo: Lumi-AI-Core, path: V2/WellPlate/WellPlate.py }
tags: [v2-module]
---

# V2.WellPlate

`WellPlate` is the V2 module that gives a multi-well plate one canonical representation regardless of which camera saw it and what shape that camera produced. It is unusually small for a V2 module — just a dataclass and a display-name mapper — but it nails down a contract that several monitors depend on.

## What it does

`WellPlate` is a `@dataclass` (`Lumi-AI-Core/V2/WellPlate/WellPlate.py:5`) with optional fields for `bounding_box`, `grid` (lines defining well coordinates), `segmentation` (polygon points), `source_class`, `instance_id`, and free-form `metadata`. The same plate may show up two ways:

- **cam1** typically loads `segmentation + bbox` (it has a clean overhead view for masks).
- **cam3** typically loads `grid + bbox` (the grid annotation gives well coordinates).

Both are valid representations of the same conceptual object. Two factory classmethods convert from raw annotation dicts:

- `WellPlate.from_grid_annotation(annotation, class_name)` — pulls `points`, `bbox_raw`, `seg_id`, `grid_lines` (`WellPlate.py:21`).
- `WellPlate.from_segmentation_annotation(annotation, class_name)` — pulls `points`, `bbox_raw`/`bbox_normalized`, `seg_id` (`WellPlate.py:39`).

`to_detection_dict()` projects either form into the standard detection dict shape (`class_name`, `bbox`, optional `polygon`, `grid`, `id`).

`WellPlateDisplayMapper` (`WellPlate.py:71`) collapses synonyms — `Grid`, `grid`, `wells_plate`, `well_plate`, `WellPlate` all display as `wells_plate`; `Pipette`, `pipette`, `PipetteTip`, `pipette_tip`, `Pipette_tip` display as `Pipette`. It also rewrites `formatted_id` prefixes (`Grid(id:1)` → `wells_plate(id:1)`).

## Public API

- `WellPlate(bounding_box=..., grid=..., segmentation=..., source_class=..., instance_id=..., metadata=...)`
- `WellPlate.from_grid_annotation(annotation, class_name="wells_plate")`
- `WellPlate.from_segmentation_annotation(annotation, class_name="wells_plate")`
- `wp.to_detection_dict()` → standard detection dict.
- `WellPlateDisplayMapper.get_display_class(source_class)`, `.get_display_formatted_id(formatted_id)`, `.is_well_plate_class(source_class)`.

## Input / output

In: annotation dicts (raw shapes from per-camera annotators) or direct constructor args. Out: a normalised dataclass plus a detection dict matching the shape in [agreedDataSchema.md](../data-schema.md).

## Dependencies on other V2 modules

None — pure stdlib (`dataclasses`, `typing`).

## Used by

Anywhere a multi-well plate appears in the unified scene model — pipetting workflows that target specific wells, monitors that aggregate across cam1/cam3 views. Imported as `from V2.WellPlate import WellPlate, WellPlateDisplayMapper`.

## Tests

No co-located tests — coverage comes through consumers (Pipetting and the custom agent).

## Gotchas

- `from_*_annotation` silently drops `segmentation` when fewer than 3 points are present — small/partial polygons disappear without an error.
- The display mapper is *prefix-based* on `formatted_id`. If your IDs use a different format (`vortexer(id:1)` rather than `Grid(id:1)`), the mapper just returns the input unchanged — that's intentional but easy to miss.

## See also

- [V2.Pipetting](Pipetting.md) — the most common consumer
- [V2.Detection](Detection.md) — the detection-dict shape `to_detection_dict` targets
- [agreedDataSchema.md](../data-schema.md)
