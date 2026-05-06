---
name: V2.PoCVIS
description: Visualisation toolkit for PoC video pipelines — info panels, logo overlays, mask overlays, summary frames, all in OpenCV/PIL.
type: module
graph_node: core:PoCVIS
sources:
  - { repo: Lumi-AI-Core, path: V2/PoCVIS/PoC_vis.py }
tags: [v2-module]
---

# V2.PoCVIS

`PoCVIS` is the V2 module that adds the consistent on-screen presentation layer used in PoC video deliverables: a logo, a side/top/bottom info panel with sectioned key-value or event-table displays, mask overlays with transparency, timestamps, and end-of-video summary frames. It does no AI of its own — it's the cosmetic layer that wraps whatever the pipeline produced.

## What it does

`PoCsVisualizer` (`Lumi-AI-Core/V2/PoCVIS/PoC_vis.py`) is a single class that holds panel structure, colours, fonts, and logo, and exposes drawing functions. Panels can be vertical (`side-left` / `side-right`) or horizontal (`top` / `bottom`), with custom column widths for event tables. Two ways to compose: in-place draw on the right side of the frame (`draw_info_panel`), or generate a standalone panel image and combine it (`create_panel_image` + `combine_frame_with_panel`). The latter is the right choice when you need to know output dimensions ahead of time (video writer setup).

## Public API

`PoCsVisualizer(panel_structure, panel_size, panel_position, colors, font_path, header_size, font_value_size, logo_path, logo_scale, logo_position)`:

- `overlay_logo(frame, logo=None, scale=None, position=None)` — alpha-blended logo placement.
- `draw_info_panel(frame, info_dict)` — in-place panel on the right.
- `create_panel_image(info_dict, height, width=None)` — standalone panel.
- `combine_frame_with_panel(frame, panel_image)` — concat in the right orientation.
- `get_output_dimensions(frame_w, frame_h)` — pre-flight size for video writers.
- `overlay_mask_alpha(frame, mask, color, alpha=0.4, label=None)` — static mask overlay with optional label.
- `draw_timestamp(frame, timestamp, position, color, scale)`.
- `create_summary_frame(frame, title, stats)`.

## Input / output

All inputs are BGR uint8 numpy arrays plus a Python dict for the panel structure (`[{"section": str, "fields": [str, ...], "column_widths": {field: int}}, ...]`). `info_dict` values are either `dict` (key-value section) or `list[dict]` (event-table section). Outputs are modified frames; this module is *not* on the [agreedDataSchema.md](../data-schema.md) detection contract.

## Dependencies on other V2 modules

None. Pure `opencv-python`, `Pillow`, `numpy`. Ships its own `font.ttf` and `Lumi Col 300dpi.png` logo.

## Used by

Any PoC pipeline that produces a video deliverable. Distinct from [V2.Visualiser](Visualiser.md) — the custom agent uses `Visualiser` for the live in-pipeline viz, while `PoCVIS` is the polished export layer.

## Tests

- `Lumi-AI-Core/V2/PoCVIS/test_PoC_vis.py`

## Gotchas

- `panel_size` is fixed at construction — no dynamic resize.
- If `font.ttf` fails to load, font *sizes* may be ignored (PIL default font doesn't honour the size param).
- Long strings in event tables are silently truncated to fit columns — pre-format if precision matters.
- Only the last N events display in the panel (panel-height-limited): vertical shows ~12, horizontal ~10.

## See also

- [V2.Visualiser](Visualiser.md)
- [V2.MultiCamera](MultiCamera.md)
- [V2.ReportGenerator](ReportGenerator.md)
- [agreedDataSchema.md](../data-schema.md)
