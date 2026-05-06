---
name: V2.BasicOps
description: Tiny utility module of generic OpenCV helpers shared across V2 modules. Currently just one function — convert a binary mask to a list of polygons.
type: module
graph_node: core:BasicOps
sources:
  - { repo: Lumi-AI-Core, path: V2/BasicOps/BasicOps.py }
  - { repo: Lumi-AI-Core, path: V2/BasicOps/README.md }
tags: [v2-module, utility]
---

# V2.BasicOps

`BasicOps` is the dumping ground for generic image-processing helpers that several V2 modules need but none of them owns. Today it has exactly one staticmethod: `mask_to_polygons`. Treat it as a place to add more shared primitives rather than copy-pasting OpenCV recipes between modules.

## What it does

`BasicOps.mask_to_polygons(input_data)` (`Lumi-AI-Core/V2/BasicOps/BasicOps.py:18`) takes a binary mask (uint8, 0/255) and returns approximated polygons. The pipeline:

1. Coerce input to uint8, drop extra channels (single channel kept; 3-channel BGR is converted to grayscale).
2. Threshold to a strict binary mask (`> 0`).
3. `cv2.findContours(..., RETR_EXTERNAL)` — outer contours only.
4. Filter contours by `cv2.contourArea < minArea` (default 3000).
5. Approximate each kept contour with `cv2.approxPolyDP` at `epsilon = 0.005 * arcLength`.

Output is a list of `[(x, y), ...]` integer-tuple polygons.

## Public API

```python
class BasicOps:
    @staticmethod
    def mask_to_polygons(input_data: Dict[str, Any]) -> Dict[str, Any]
```

Required: `mask: np.ndarray`. Optional: `minArea: int = 3000`. Returns `{"polygons": [...]}` or `{"errorType", "errorDesc", "stackTrace"}`.

There is no `__init__` to call — it's a static utility.

## Input/output shape

Polygon output (`list[list[tuple[int, int]]]`) is in **pixel** coordinates, not normalised. This is the one mismatch with the V2 detection schema (see `agreedDataSchema.md`) — if you're feeding polygons into a detection-shaped consumer, normalise yourself.

## Dependencies on other V2 modules

None. Pure OpenCV + NumPy. The module is intentionally trivial so anything can import it without dragging weights along.

## Used by which monitors / V2 modules

Best-effort: search for `V2.BasicOps` across `monitors/` and `V2/`. It's a candidate dependency anywhere a segmentation mask needs to become a polygon (e.g. visualisation, JSON export). The Detection segmenters return `segmentation` already as polygons, so most consumers never hit this directly.

## Tests

- `Lumi-AI-Core/V2/BasicOps/test_basic_ops.py`

## Gotchas

- `minArea` defaults to **3000 pixels**. Small contours from small images will silently disappear. If you're processing a 256×256 mask you almost certainly want to lower this.
- Polygon coords are pixel-space ints. Other V2 contracts use normalised floats — convert at the boundary.
- Douglas–Peucker `epsilon` is hard-coded; very curvy contours come back coarse.

## See also

- [V2.Detection](Detection.md) — segmenter output already in polygon form
- [V2.SegmentAnything](SegmentAnything.md) — produces masks you might want to polygonise
- [agreedDataSchema](../data-schema.md)
- [V2.Visualiser](Visualiser.md) — the most common downstream of polygons
