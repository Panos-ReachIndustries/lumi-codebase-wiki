---
name: V2.SegmentAnything
description: Thin re-export layer for SAM-based vessel segmentation plus a NumPy-to-JSON serialisation helper.
type: module
graph_node: core:SegmentAnything
sources:
  - { repo: Lumi-AI-Core, path: V2/SegmentAnything/__init__.py }
  - { repo: Lumi-AI-Core, path: V2/SegmentAnything/test_segment_anything.py }
tags: [v2-module]
---

# V2.SegmentAnything

`SegmentAnything` is the V2 module that exposes Segment Anything Model (SAM) capabilities through the same surface as the rest of V2. It is *intentionally tiny*: there is no `.py` implementation file beyond `__init__.py` and tests. All the real work happens in [V2.Vessels](Vessels.md) — this module exists so that callers wanting a "SAM-style" entry point can find one in the obvious place, and so that the JSON-serialisation utility lives next to it.

## What it does

Two exports, both via `Lumi-AI-Core/V2/SegmentAnything/__init__.py`:

- **`VesselDetectorV2`** — re-exported lazily from `V2.Vessels.VesselDetector`. Wraps SAM (variants `vit_b` / `vit_l` / `vit_h`) and an FCN model for vessel segmentation; provides utilities like `get_box_from_mask(mask)` to extract bounding boxes from binary masks.
- **`convert_numpy_types(obj)`** — recursively converts numpy scalars and arrays (`np.int*`, `np.uint*`, `np.float*`, `np.ndarray`) into JSON-serialisable Python types. Handles nested `dict`/`list`/`tuple`/`set` structures.

The lazy `__getattr__` means `from V2.SegmentAnything import convert_numpy_types` works without loading torch / SAM weights.

## Public API

```python
from V2.SegmentAnything import VesselDetectorV2, convert_numpy_types

detector = VesselDetectorV2({"fcn_weights": "...", "variant": "vit_h", "sam_weights": "..."})
box = detector.get_box_from_mask(binary_mask)   # [x1, y1, x2, y2]
serialisable = convert_numpy_types(box)
```

Refer to [V2.Vessels](Vessels.md) for the full `VesselDetectorV2` API surface.

## Input / output

Detection-shaped outputs (when used via `VesselDetectorV2`) follow [agreedDataSchema.md](../data-schema.md). `convert_numpy_types` accepts and returns arbitrary Python objects.

## Dependencies on other V2 modules

- [V2.Vessels](Vessels.md) — the real implementation, lazy-imported on first attribute access.
- Numpy is the only direct import in this module.

## Used by

Anywhere SAM-style segmentation is wanted under a name that says so on the tin. Also imported as a JSON-helper utility by modules that need to emit numpy types over HTTP or to disk (e.g. [V2.NuclioRequest](NuclioRequest.md)-adjacent code).

## Tests

- `Lumi-AI-Core/V2/SegmentAnything/test_segment_anything.py`

## Gotchas

- This module has *no main `.py`* — don't go looking for `SegmentAnything.py`. The implementation lives in [V2.Vessels](Vessels.md). Read that module's source to understand SAM behaviour.
- `convert_numpy_types` does not handle pandas, datetime, or custom objects — only numpy scalars/arrays plus standard collections.
- `VesselDetectorV2` requires both FCN and SAM weights on disk — see Vessels.

## See also

- [V2.Vessels](Vessels.md)
- [V2.NuclioRequest](NuclioRequest.md)
- [V2.Detection](Detection.md)
- [agreedDataSchema.md](../data-schema.md)
