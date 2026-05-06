---
name: V2.TextReader
description: Reads text from frames or stills using YOLO digit detection plus an LLM (OpenAI or local Llama) for OCR, with temporal smoothing.
type: module
graph_node: core:TextReader
sources:
  - { repo: Lumi-AI-Core, path: V2/TextReader/TextReader.py }
  - { repo: Lumi-AI-Core, path: V2/TextReader/YoloV11DigitDetector.py }
  - { repo: Lumi-AI-Core, path: V2/TextReader/base_processor.py }
  - { repo: Lumi-AI-Core, path: V2/TextReader/openai_processor.py }
  - { repo: Lumi-AI-Core, path: V2/TextReader/llama_processor.py }
  - { repo: Lumi-AI-Core, path: V2/TextReader/temporal_tracker.py }
tags: [v2-module]
---

# V2.TextReader

`TextReader` reads numeric values off lab instruments — digital scales, pH meters, hot plates, anything with a 7-segment-ish display. It is *not* a general OCR; it is a YOLO digit detector glued to an LLM that interprets the cropped reading.

## What it does

The pipeline (`Lumi-AI-Core/V2/TextReader/TextReader.py:69`):

1. **Detect** — `YOLO11Model` (`Lumi-AI-Core/V2/TextReader/YoloV11DigitDetector.py:33`) runs on each frame, emitting per-digit / per-glyph bboxes. The detector loads OpenVINO `.xml` weights when available, otherwise PyTorch.
2. **Group** — RANSAC line fitting (`skimage.measure.LineModelND`) groups co-linear digits into reading lines and computes their orientation.
3. **Warp + crop** — each line is rotated upright and cropped with configurable padding (`TEXTREADER_PADDING_FACTOR`, `TEXTREADER_LLM_BOX_SCALE`).
4. **Interpret** — the cropped reading goes to a `BaseProcessor` subclass that returns a JSON `{title, value, units, message}`. Two backends ship: `OpenAIProcessor` (GPT-4o-class) and `LlamaProcessor` (local server). The system prompt is intricate — it forces decimal-point preservation and gates against bad splits (`base_processor.py:10`).
5. **Smooth** — `TemporalTracker` accumulates per-region readings across frames and emits stable values.

## Public API

- `TextReader(cap, processor_type="openai"|"llama", api_key=..., yolo_model_path=..., yolo_confidence_threshold=..., max_image_dimension=512)` — the main class. `cap` is a frame source.
- `BaseProcessor` (abstract) → `OpenAIProcessor`, `LlamaProcessor` — swap LLM backends.
- `YoloV11Detector` / `YOLO11Model` wrapper — also usable standalone.
- `TemporalTracker` — exposed for tests.

## Input / output

In: `np.ndarray` BGR frames via `cap`. Out: a list of `{title, value, units, message, image_index}` dicts (see `base_processor.py:60` for the schema). Errors from the LLM bubble up; YOLO failures yield empty detections.

## Dependencies on other V2 modules

- [V2.ModelInference](ModelInference.md) — pulls `YOLO11Model` from `V2/ModelInference/Models/YOLO`.
- `scikit-image` for RANSAC, `ultralytics` for YOLO, optional `openvino` runtime.

## Used by

- [V2.Weighing](Weighing.md) reuses the same pattern (a separate `WeightTextReader`, but the YOLO + LLM idea is identical).
- Any monitor that needs a readout off a benchtop instrument — typically wired through the custom agent rather than imported directly.

## Tests

- `Lumi-AI-Core/V2/TextReader/test_text_reader.py`

## Gotchas

- Two LLM backends, two failure modes: `OpenAIProcessor` needs `api_key`; `LlamaProcessor` needs a reachable local server. Connection retries are gated by `TEXTREADER_MAX_CONNECTION_ATTEMPTS` / `TEXTREADER_CONNECTION_RETRY_SLEEP_SECONDS`.
- Decimal points are the failure mode the prompt obsesses over — if your readings are off by an order of magnitude, the LLM is missing the dot.
- Heavy env-var surface; defaults live at the top of `TextReader.py:38-57`.

## See also

- [V2.Weighing](Weighing.md) — sibling module for scale-specific reading
- [V2.ModelInference](ModelInference.md)
- [agreedDataSchema.md](../data-schema.md)
