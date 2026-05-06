---
name: V2.Weighing
description: End-to-end balance-scale pipeline — finds the screen and pan, reads the digits, detects tare, and tracks weight values across frames.
type: module
graph_node: core:Weighing
sources:
  - { repo: Lumi-AI-Core, path: V2/Weighing/weighingPipeline.py }
  - { repo: Lumi-AI-Core, path: V2/Weighing/weighingTextReader.py }
tags: [v2-module]
---

# V2.Weighing

`Weighing` is the V2 module that watches a balance scale and tells you what the readout says, when the scientist tared it, and whether their hand or an object is on the pan. It composes screen/pan detection, OCR (low-detail MMOCR + high-detail OpenAI), tare detection, and per-cycle weight tracking into a single per-frame call.

## What it does

`WeighingPipeline.process_frame` (`Lumi-AI-Core/V2/Weighing/weighingPipeline.py`) runs through, for each input frame:

1. **Screen detection** — locate the LCD readout via either template matching or YOLO (`objectDetection.screenDetectionType`).
2. **Balance-pan detection** — locate the pan the same way (`balancePanDetectionType`).
3. **Text find** — `WeightTextReader.find_text` (`weighingTextReader.py`) crops to the screen and runs YOLO text-detection with RANSAC-driven region extension.
4. **Text recognition** — two backends: low-detail `MMOCRTextRecogniser` for fast batched reads, high-detail `OpenAITextRecogniser` for ambiguous/decimal-heavy displays.
5. **Tare detection** — `TareDetector` watches for the readout going to zero across `tareDetectionFrameCount` frames, and starts a new `WeighingCycle`.
6. **Weight tracking** — the active `WeighingCycle` records value-vs-time; `objectOnBalance` and `gloves` flags come from concurrent object/pose detection.

The module reuses the same conceptual pipeline as [V2.TextReader](TextReader.md), but specialised for scale displays — including its own OCR backend choice and a tare-aware state machine.

## Public API

V2 dict pattern:

- `WeighingPipeline({"yoloModelWeights", "yoloConfThreshold"?, "ransacConfig"?, "mmocrModelName"?, "mmocrModelWeights"?, "openaiApiKey"?, "openaiModel"?, "objectDetection"?, "templateMatchingDetection"?, "poseDetection"?, "taring"?, ...})`
- `pipeline.process_frame({"frame": np.ndarray})` → `{screenLocation, balancePanLocation, textRegions, highDetailReadings, lowDetailReadings, balanceTared, trackedWeightRegion, currentWeight, gloves, objectOnBalance, processingSuccessful}`.
- `WeightTextReader` standalone for text-only use; `WeighingCycle` and `TareDetector` are exposed for integration.

## Input / output

In: BGR frame `np.ndarray`. Out: structured detections + a string `currentWeight`. Failures return the standard `{"errorType", "errorDesc", "stackTrace"}`. Per-cycle history accumulates inside the pipeline instance.

## Dependencies on other V2 modules

- [V2.ModelInference](ModelInference.md) — `YoloInference`, `TemplateMatchingDetector`, `YoloPoseInference`.
- `V2.Machine.Text` — `YOLOTextDetector`, `MMOCRTextRecogniser`, `OpenAITextRecogniser`.
- Honours env vars `PREFERRED_SCREEN_CAMERA` (lock to a single camera ID) and `CAMERA_ROTATIONS` (per-camera rotation JSON).

## Used by

Lab monitors that include a weighing step in their protocol. Composed via the custom agent rather than imported by other V2 modules.

## Tests

- `Lumi-AI-Core/V2/Weighing/test_weighing.py`

## Gotchas

- The OpenAI backend needs a valid `openaiApiKey` and is rate-limited; the MMOCR backend is fast and offline. Both can run, low-detail first.
- Tare detection waits for `tareDetectionFrameCount` consecutive zero reads — too low triggers spurious cycles, too high misses real tares.
- `PREFERRED_SCREEN_CAMERA` makes the pipeline silently ignore frames from other camera IDs; if outputs are mysteriously empty, check the env.

## See also

- [V2.TextReader](TextReader.md) — sibling module with the same YOLO+LLM pattern
- [V2.ModelInference](ModelInference.md)
- [agreedDataSchema.md](../data-schema.md)
