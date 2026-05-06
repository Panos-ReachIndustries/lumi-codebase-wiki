---
name: V2.Detection
description: The unified object detection / segmentation API. The most-imported V2 module — read this if you want to understand the V2 contract.
type: module
graph_node: core:Detection
sources:
  - { repo: Lumi-AI-Core, path: V2/Detection/GenericDetectorWrapper.py }
  - { repo: Lumi-AI-Core, path: V2/Detection/GenericDetector.py }
  - { repo: Lumi-AI-Core, path: V2/Detection/ObjectSegmenter.py }
  - { repo: Lumi-AI-Core, path: agreedDataSchema.md }
tags: [v2-module, exemplar]
---

# V2.Detection

`Detection` is the V2 module that everything visual eventually lands on. It hides the difference between a YOLO detector, an RCNN detector, and a SAM-style segmenter behind one schema.

## What it offers

A small set of public classes:

- **`GenericDetector`** — abstract base. Subclasses wrap concrete model backends (YOLO, RCNN, MMDetection variants).
- **`GenericDetectorWrapper`** — the everyday entry point. Takes a config (model name, weights, thresholds), produces an object that exposes `.detect(frame)`.
- **`ObjectSegmenter`** — like the wrapper, but the output includes per-instance masks.
- A glove-specific wrapper used by hand-related monitors.

## Output schema

This is the bit that matters across the whole codebase. Detections look like (see `Lumi-AI-Core/agreedDataSchema.md`):

```json
[
  {
    "bbox":      [x1, y1, x2, y2],   // normalised
    "confidence": 0.87,
    "class_name": "vessel",
    "class_id":   3,
    "mask":       [...]              // optional — only from segmenters
  },
  ...
]
```

Everything else in the codebase (Tracking, LabContainerTracking, the custom agent's pipeline) consumes this exact shape. If you're adding a new detector, **don't invent a new schema** — wrap your model so it emits this one.

## Why this module sits at the centre

Reading the import graph:

- Most monitors that need "find things in a frame" import `V2.Detection`.
- `V2.Tracking` consumes `V2.Detection` output frame-by-frame to maintain identity over time.
- `V2.LabContainerTracking` consumes `V2.Tracking` to maintain *vessel* identity, and reaches back into `V2.Detection` for first-frame initialisation.
- The custom-agent pipeline builder lets users compose a `Detection → Tracking → Vessels` chain via JSON.

In the graph view, `core:Detection` will have one of the highest in-degrees among V2 modules. Click it and you can see who uses it.

## Adding a new model backend

1. Subclass `GenericDetector`.
2. Implement `_detect(self, frame) -> list[Detection]` returning the schema above.
3. Register it in `GenericDetectorWrapper`'s factory or via `ModularDetector`'s `model_registry.py`.
4. Add weights under `Lumi-AI-Core/weights/` (gitkeep'd; weights ship out-of-band).
5. Add or update the module's `requirements.txt`.

## Tests

Co-located with the module:

- `V2/Detection/test_GenericDetectorWrapper.py`
- `V2/Detection/test_glove_detector_standalone.py`

Run them via:

```bash
docker compose -f docker-compose.pytest.yml run -e PYTEST_ARGS="V2/Detection" --rm test-runner
```

(from the `Lumi-AI-Core/` repo root, not from this wiki repo).

## When it goes wrong

- **Mask output empty** — you instantiated `GenericDetectorWrapper` instead of `ObjectSegmenter`. Check the wrapper class, not the model.
- **Classes don't match** — different model backends ship different class lists. If your downstream consumer expects `"vessel"`, make sure the backend you chose exposes that label.
- **Performance cliff** — most issues come from forgetting to call `.warmup()` on first frame, or running on CPU without realising. Check the config.

## See also

- [agreedDataSchema.md](../data-schema.md) — the canonical V2 I/O contract
- [V2.Tracking](Tracking.md) — the most common downstream consumer
- [V2.ModularDetector](ModularDetector.md) — the registry that picks a backend at runtime
- [custom monitor](../../ai-continuous/monitors/custom.md) — the largest user of this module
