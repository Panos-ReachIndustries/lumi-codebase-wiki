---
name: text monitor
description: OCR for configured polygon regions — string and number readouts via MMOCR with a 4-stage legibility gate.
type: monitor
graph_node: monitors:text
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/text/text_recognition.py }
  - { repo: Lumi-AI-Core, path: V2/Machine/Text/TextRecogniser.py }
tags: [monitor]
---

# text monitor

The `text` monitor reads text from configured polygonal regions of the frame and publishes a base64-encoded string per region. The recogniser is `V2.Machine.Text.TextRecogniser.MMOCRTextRecogniser` running an `aster_resnet45_6e_st_mj` checkpoint (`text_recognition.py:317`). For digit-only regions (`type: "number"`) the monitor parses the OCR output, applies a configurable decimal location, and publishes a float (or `nan` on parse failure).

A notable detail: before each frame is sent to OCR, every region crop passes through a 4-stage cascade of cheap legibility tests — grayscale stddev → Laplacian variance → high-frequency FFT energy → 95th-percentile Sobel gradient (`text_recognition.py:69`). Crops that fail any gate are skipped, which dramatically reduces OCR load on blurry, motion-affected, or partially-occluded frames.

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/text/text_recognition.py`
- **Legibility gates:** `_estimate_text_legibility` at `text_recognition.py:69`
- **Per-frame OCR call:** `text_recognition.py:399` (`tr.extract_text_from_image(...)`)
- **Tests:** `test_text_recognition.py`, `test_mmocr_load.py`

## How it runs

```bash
# Local
python monitors/text/text_recognition.py --config path/to/config.json --is_local

# Production
python monitors/text/text_recognition.py --config path/to/config.json
```

## Inputs

- `args.ai.regions` — list of `{name, type, polygon, decimalLocFromRight?}` entries (`text_recognition.py:305`). `type` is `"string"` or `"number"`.
- `args.ai.textLegibilityGates` — optional dict overriding `gray_std_min` / `laplacian_var_min` / `hf_energy_ratio_min` / `gradient_p95_min` (`text_recognition.py:61`).
- `MMOCR_MODEL_WEIGHTS` env var — overrides the default weights path `/src/data/weights/aster_resnet45_6e_st_mj.pth` (`text_recognition.py:317`).
- Standard `monitorId`, `pipeline`, archive timestamps.

## Outputs

Per frame, via `TextStreamReporter.data(...)`:

```json
{
  "streamOffline": false,
  "regions": [
    {"regionName": "balance", "type": "number", "text": "MTIzLjQ1"},
    {"regionName": "label",   "type": "string", "text": "U2FtcGxlIEEx"}
  ]
}
```

The `text` field is base64-encoded UTF-8 (`text_recognition.py:181, 195`). For `type: "number"` it encodes the parsed float (or the literal string `"nan"`); for `type: "string"` it encodes the raw OCR text. **Empty-string regions of `type: "string"` are dropped before publish** (`_filter_empty_string_readings`, `text_recognition.py:139`) because the downstream Kafka consumer in `Lumi-AI-Core` rejects empty `text`. If every region drops, the frame is silently skipped (`text_recognition.py:422`).

## V2 modules used

- [V2.Machine](../../ai-core/modules/Machine.md) — `Text.TextRecogniser.MMOCRTextRecogniser`.

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.TextStreamReporter`

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md)

## Tests

- `Lumi-AI-Continuous/monitors/text/test_text_recognition.py`
- `Lumi-AI-Continuous/monitors/text/test_mmocr_load.py`

## When it goes wrong

- **Region always missing from output** — your text is `""`; for string regions that's silently dropped (see above). Switch the region to `type: "number"` if you actually want a value every frame.
- **All regions skipped via legibility gate** — debug log says e.g. `failed_gate: 'gray_std'`. Crops are too blurry/dark; loosen the gate via `ai.textLegibilityGates`.
- **Numbers come back as `nan`** — OCR returned non-numeric chars; the parser strips everything outside `0-9.-`. Check the raw OCR output via debug.
- **Decimal in wrong place** — set `decimalLocFromRight` per region; the parser inserts the decimal point N chars from the right (`text_recognition.py:185`).
- **OOM on first run** — MMOCR loads a ResNet checkpoint; ensure the weights path is on the runtime image and `MMOCR_MODEL_WEIGHTS` matches.

## See also

- [V2.Machine](../../ai-core/modules/Machine.md)
- [V2.TextReader](../../ai-core/modules/TextReader.md)
- [dial monitor](dial.md) — analogue-needle counterpart.
- [Kafka topics](../../architecture/kafka-topics.md)
