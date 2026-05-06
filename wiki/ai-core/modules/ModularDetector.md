---
name: V2.ModularDetector
description: Task-oriented ONNX bbox detector with built-in ByteTrack tracking — pick a task key, get tracked detections in original-frame pixel space.
type: module
graph_node: core:ModularDetector
sources:
  - { repo: Lumi-AI-Core, path: V2/ModularDetector/ModularDetector.py }
  - { repo: Lumi-AI-Core, path: V2/ModularDetector/model_registry.py }
  - { repo: Lumi-AI-Core, path: V2/ModularDetector/model_paths.json }
tags: [v2-module]
---

# V2.ModularDetector

`ModularDetector` is the V2 module for task-oriented bbox detection on top of pure `onnxruntime`. Callers pick a task key (e.g. `equipment.vortex`, `equipment.centrifuge`); the wrapper resolves weights, thresholds, class names, and a tracking preset from a registry — and emits normalised bbox detections plus persistent ByteTrack IDs. It's the modern replacement for the ultralytics-based `Models/YOLO/` path.

## What it does

A single call shape (`detect`) covers every registered task. Under the hood (`Lumi-AI-Core/V2/ModularDetector/ModularDetector.py`):

- Letterboxes the input frame to the model's `imgsz`, runs ONNX inference, applies NMS, then inverse-letterboxes — so detections always land in *original*-frame pixel coordinates regardless of aspect ratio (480p / 720p / 1080p, landscape or portrait).
- Routes per-detection through a `TrackingManager` that combines `supervision.ByteTrack` (persistent IDs) with a per-tid `TrackSmoother` (hysteresis, EMA, accept-radius gate, velocity cap, peak-conf activation gate).
- Never raises from public methods — failures come back as dicts with `errorType` / `errorDesc` / `stackTrace`.

## Public API

- `ModularDetector({"task": "equipment.vortex", "userConfig": {...}})` — construct.
- `detect({"rgb_image": np.ndarray})` → `{"detections": [...], "detection_inference_time": ...}` where each detection has `bbox` (normalised `[x1,y1,x2,y2]`), `confidence`, `className`, and an optional `track` sub-dict (`trackId`, `framesSeen`, `framesSinceUpdate`, `confirmed`).
- `list_tasks()` — discover registered tasks and their default thresholds / classes.
- `reset_tracking()` — clear ByteTrack IDs and smoother state between unrelated videos.

## Input / output

Conforms to the bbox shape from [agreedDataSchema.md](../data-schema.md), with `track` as an additive field. The `Detection.track` contract change is noted in the module's README — downstream consumers that ignore the field keep working.

## Dependencies on other V2 modules

- [V2.ModelInference](ModelInference.md) — the actual ONNX runtime lives in `V2/ModelInference/Models/ModularDetection/OnnxDetectionInference.py`.
- `supervision` (ByteTrack), `onnxruntime`. No torch, no ultralytics.

## Used by

Equipment-aware monitors (vortex, centrifuge) and the custom-agent pipeline. Sits next to [V2.Detection](Detection.md) — same I/O shape, different backend.

## Tests

- `Lumi-AI-Core/V2/ModularDetector/run_tests.py`
- Unit lane (no weights): `Lumi-AI-Core/V2/ModularDetector/tests/`, `Lumi-AI-Core/V2/ModelInference/Models/ModularDetection/tests/`, `tracking/tests/`.
- Integration lane (weights gated by `MODULAR_DETECTOR_TEST_WEIGHTS_DIR`).

## Gotchas

- Weights live in S3 (`s3://reach-ml-weights/modular_detector/...`); the deploy pipeline syncs them to `local_path` per `model_paths.json`. A missing local file surfaces as a constructor error citing the S3 URL.
- `detect()` takes only the frame — no per-call config override. Tune via `userConfig.tracking` at construction.
- Tracking is on by default. Disable with `userConfig.tracking = False`, or pass-through specific classes via `disabled_classes`.
- Activation has *three* gates (sustained EMA, duration, peak-conf). A persistent mid-confidence misclassification stays pending forever — by design.

## See also

- [V2.Detection](Detection.md)
- [V2.Tracking](Tracking.md)
- [V2.ModelInference](ModelInference.md)
- [agreedDataSchema.md](../data-schema.md)
