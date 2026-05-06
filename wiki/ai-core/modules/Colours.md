---
name: V2.Colours
description: Colour analysis for an image region — dominant colours via K-means, opacity via Gaussian-blur iteration, and homogeneity / contrast via GLCM. Underpins the colour and liquids monitors.
type: module
graph_node: core:Colours
sources:
  - { repo: Lumi-AI-Core, path: V2/Colours/ColourAnalyser.py }
  - { repo: Lumi-AI-Core, path: V2/Colours/Colours.py }
  - { repo: Lumi-AI-Core, path: V2/Colours/README.md }
tags: [v2-module]
---

# V2.Colours

`Colours` is the perception primitive for "what colour is this region?". It exposes one class — `ColourAnalyser` — with three independent analyses (dominant colours, relative opacity, GLCM homogeneity/contrast) that all share the same flexible region API: pass `box`, `mask`, `polygon`, or none of the above to mean "the whole image".

## What it does

`ColourAnalyser` (`Lumi-AI-Core/V2/Colours/ColourAnalyser.py`) builds a K-means model over a curated colour vocabulary at init. Each analysis method extracts a region of pixels using whichever of `box | mask | polygon` you supply, then:

- `get_dominant_colours` — clusters region pixels and returns each cluster's `averageRgb`, the closest-named `matchedRgb`, `proportion`, and `colourName`. LAB colour space for perceptual distance.
- `get_relative_opacity` — iteratively Gaussian-blurs and measures how fast the region's variance collapses, returning `[0, 1]` opacity.
- `get_homogeneity_stats` — Gray-Level Co-occurrence Matrix (`scikit-image`) -> `homogeneity` and normalised `contrast`.

`Colours.get_colours_dict()` (`Colours.py`) is the static `{(r,g,b): "Name"}` lookup used to put English names on RGB clusters.

## Public API

```python
ColourAnalyser({})  # no required params

.get_dominant_colours({"image", "box"|"mask"|"polygon"?})
  -> {"dominantColours": [...], "averageRgb": [r,g,b], "homogeneity", "contrast"}
.get_relative_opacity({"image", "box"|"mask"|"polygon"?})
  -> {"relativeOpacity": float}
.get_homogeneity_stats({"image", "box"|"mask"|"polygon"?})
  -> {"homogeneity": float, "contrast": float}
```

`box` is normalised `[x1, y1, x2, y2]`; `polygon` is normalised `[[x, y], ...]`; `mask` is image-shape uint8. Provide at most **one** region spec per call. All methods return V2 error dicts on failure.

## Input/output shape

Region inputs use V2 normalised bbox / polygon / mask conventions (compatible with what [V2.Detection](Detection.md) emits — see `agreedDataSchema.md`). Outputs are bespoke colour dicts.

## Dependencies on other V2 modules

None. Pulls in scikit-learn (K-means), scikit-image (GLCM), OpenCV, NumPy, Pillow.

## Used by which monitors / V2 modules

Heavy usage from `Lumi-AI-Continuous`:

- `monitors/colour/colour.py` — primary consumer
- `monitors/homogeneity/homogeneity.py`
- `monitors/liquids/liquid_description.py`, `liquid_description_yolo.py`, `liquid_precipitation.py`, `phase_liquid_description.py`
- `Common/common.py`

## Tests

- `Lumi-AI-Core/V2/Colours/test_colour_analyser.py`

## Gotchas

- Provide **at most one** of `box`, `mask`, `polygon` per call — passing more than one is `BAD_INPUT`.
- `get_homogeneity_stats` needs a region of at least 2x2 pixels.
- Large regions are subsampled to ~25 pixels for K-means performance — don't expect pixel-perfect colour stats on huge crops.
- `dominantColours.proportion` sums to 1.0 across clusters; use it, not pixel counts, for downstream logic.

## See also

- [V2.Detection](Detection.md) — gives you the `box`/`polygon`/`mask` to pass in
- [agreedDataSchema](../data-schema.md)
- [colour monitor](../../ai-continuous/monitors/colour.md) — main downstream
- [V2.BasicOps](BasicOps.md) — converts masks to polygons if you need to re-shape input
