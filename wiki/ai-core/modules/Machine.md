---
name: V2.Machine
description: Lazy-loading facade over text recognition, screen detection, and gauge-reading capabilities.
type: module
graph_node: core:Machine
sources:
  - { repo: Lumi-AI-Core, path: V2/Machine/__init__.py }
  - { repo: Lumi-AI-Core, path: V2/Machine/Text }
  - { repo: Lumi-AI-Core, path: V2/Machine/Screens/ScreenFinder.py }
  - { repo: Lumi-AI-Core, path: V2/Machine/GaugeReader/GaugeReader.py }
tags: [v2-module]
---

# V2.Machine

`Machine` is the V2 facade for "read what a piece of lab equipment is showing": text on labels, regions of monitors/screens, and analogue gauge dials. It exists primarily as a routing layer — the heavy lifting lives in three submodules — and lazy-loads each backend so importing the package is cheap.

## What it does

The top-level package re-exports a small, stable public surface and lazy-imports submodules on first attribute access. The underlying capabilities are:

- **`Text`** — text detection (YOLO-based) plus OCR with multiple recogniser backends (OpenAI vision, MMOCR, PaddleOCR).
- **`Screens`** — locate monitor/screen regions in benchtop imagery.
- **`GaugeReader`** — read analogue gauges and emit structured numeric readings.

## Public API

Exported via `V2.Machine.__all__` (`Lumi-AI-Core/V2/Machine/__init__.py`):

- `YOLOTextDetector` → `V2.Machine.Text.YOLOTextDetector`
- `OpenAITextRecogniser`, `MMOCRTextRecogniser`, `PaddleTextDetector` → `V2.Machine.Text.*`
- `ScreenFinder` → `V2.Machine.Screens.ScreenFinder`
- `GaugeReader` → `V2.Machine.GaugeReader.GaugeReader`

Each follows the V2 dict-in/dict-out contract; failures return `{"errorType": ..., "errorDesc": ..., "stackTrace": ...}`.

```python
from V2.Machine import YOLOTextDetector, GaugeReader, ScreenFinder

text_detector = YOLOTextDetector({...})
gauge = GaugeReader({...})
screens = ScreenFinder({...})
```

## Input / output

Submodules each define their own Dictified I/O — see the per-submodule READMEs (`V2/Machine/Text/README.md`, `V2/Machine/Screens/README.md`, `V2/Machine/GaugeReader/README.md`). Detection-style outputs follow [agreedDataSchema.md](../data-schema.md); gauge / OCR outputs are submodule-specific.

## Dependencies on other V2 modules

The package itself has no V2 dependencies — it's a pure facade. Submodules pull in their own backends (ultralytics for YOLO, openai/mmocr/paddleocr for OCR, custom keypoint models for `GaugeReader`).

## Used by

Monitors that read meters, balances, hot-plate displays, or labels reach for `Machine` — e.g. `monitors/needle-gauge` for analogue dials and `monitors/text` for label OCR. The custom agent can also wire it into its pipeline.

## Tests

- `Lumi-AI-Core/V2/Machine/test_machine.py` — facade-surface smoke test (asserts `__all__` is intact and `__getattr__` rejects unknown names). Deeper behavioural tests live in each submodule.

## Gotchas

- The lazy `__getattr__` masks attribute errors at *import* time but surfaces them on *first use* — heavy backend deps (mmocr, paddleocr, ultralytics) only fail when you instantiate the relevant class.
- `OpenAITextRecogniser` needs `OPENAI_API_KEY`; the others want local weight files.

## See also

- [V2.Detection](Detection.md)
- [V2.ModelInference](ModelInference.md)
- [agreedDataSchema.md](../data-schema.md)
- [V2.Visualiser](Visualiser.md)
