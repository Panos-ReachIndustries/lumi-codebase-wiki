---
name: V2.ModelInference
description: Standardised model-inference framework that wraps every backbone (YOLO, MiDaS, FCN, MediaPipe pose, etc.) behind a common dict-in/dict-out API.
type: module
graph_node: core:ModelInference
sources:
  - { repo: Lumi-AI-Core, path: V2/ModelInference/__init__.py }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/inference_schema.py }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/Base }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/Models }
tags: [v2-module]
---

# V2.ModelInference

`ModelInference` is the V2 module that wraps every model backbone the codebase uses — YOLO11, YOLOX, MiDaS, DepthAnything, MediaPipe pose, FCN vessel segmentation, MultiUNet, gauge-keypoint heads — behind a single, predictable dict-in/dict-out API. Higher-level modules (`Detection`, `ModularDetector`, `Vessels`, `Pipetting`) all delegate raw model calls here so that swapping backbones doesn't ripple through the codebase.

## What it does

Two layers, by design (`Lumi-AI-Core/V2/ModelInference/__init__.py`):

- **`Base/`** — abstract interfaces (e.g. `ObjectDetectionInference`) that every backend implements.
- **`Models/`** — concrete wrappers (`YOLO/`, `YOLOX/`, `Midas/`, `DepthAnything/`, `Pose/YOLO/`, `Pose/Mediapipe/`, `FCN/`, `MultiUNet/`, `GaugeKeypoint/`, `RectangleDetection/`, `ColorBasedDetection/`, `TemplateMatching/`, `ModularDetection/`).

Each wrapper accepts an `input_data` config dict (weights path, thresholds, device), exposes a method like `predict()` / `estimate_depth()` / `detect_human_pose()`, and returns either a result dict or `{"errorType", "errorDesc", "stackTrace"}` on failure. Weights are loaded from local files only — no auto-downloads.

## Public API

The package re-exports flat aliases for the common backbones:

- `YoloInference`, `YOLO11Model` (`Models/YOLO/`)
- `MidasInference` (`Models/Midas/`)
- `DepthAnythingInference` (`Models/DepthAnything/`)
- `YoloPoseInference` (`Models/Pose/YOLO/`)
- `MediapipePoseInference` (`Models/Pose/Mediapipe/`)
- `FCNInference` (`Models/FCN/`)

A shared `Detection` dataclass and validation helpers live in `Lumi-AI-Core/V2/ModelInference/inference_schema.py`.

```python
from V2.ModelInference import YoloInference

det = YoloInference({"modelWeights": "yolov11n.pt", "confThreshold": 0.5})
out = det.predict({"frame": img})
```

## Input / output

Detection-shaped outputs follow [agreedDataSchema.md](../data-schema.md). Depth and pose outputs are documented in each submodule's README and `exposed_functions.json`.

## Dependencies on other V2 modules

None — `ModelInference` sits *below* the rest of V2. Per-backbone deps (torch, ultralytics, mediapipe, onnxruntime, openvino) are pinned in each model's `requirements.txt`.

## Used by

[V2.Detection](Detection.md) and [V2.ModularDetector](ModularDetector.md) wrap these backends; [V2.Vessels](Vessels.md), [V2.Pipetting](Pipetting.md) (volume reader), [V2.Machine](Machine.md) (gauge keypoints, text), and the `ThreeDCalc` legacy module also delegate here.

## Tests

- `Lumi-AI-Core/V2/ModelInference/test_inference_schema.py`
- Per-backbone tests under `Lumi-AI-Core/V2/ModelInference/Models/<Name>/tests/`.

## Gotchas

- Local weights only — set `modelWeights` to an absolute path that exists. Missing weights raise at construction.
- The legacy `Models/YOLO/` (ultralytics) is being phased out in favour of `Models/ModularDetection/OnnxDetectionInference.py`. New code should prefer the ONNX path.
- Backbone-specific config keys (e.g. `confThreshold` vs `confidence_threshold`) are not normalised across submodules — read the relevant README before swapping.

## See also

- [V2.Detection](Detection.md)
- [V2.ModularDetector](ModularDetector.md)
- [V2.Vessels](Vessels.md)
- [agreedDataSchema.md](../data-schema.md)
