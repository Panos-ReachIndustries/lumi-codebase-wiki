---
name: V2.DocIngestingPDF
description: Uploads scientific-protocol PDFs to GPT-4o, then parses the response into a stages → steps → actions → subActions hierarchy used by the protocol builder.
type: module
graph_node: core:DocIngestingPDF
sources:
  - { repo: Lumi-AI-Core, path: V2/DocIngestingPDF/DocIngestingPDF.py }
  - { repo: Lumi-AI-Core, path: V2/DocIngestingPDF/parser_pdf.py }
  - { repo: Lumi-AI-Core, path: V2/DocIngestingPDF/prompt_pdf.py }
  - { repo: Lumi-AI-Core, path: V2/DocIngestingPDF/README.md }
tags: [v2-module, llm]
---

# V2.DocIngestingPDF

`DocIngestingPDF` is the first link in the "PDF protocol -> executable monitor plan" pipeline. It hands a PDF to OpenAI's file-upload API, runs GPT-4o with a fixed protocol-extraction prompt (`prompt_pdf.py`), and turns the raw text response into a strict four-level hierarchy: **stages -> steps -> actions -> subActions**. Each node carries an `id` and a `description`.

## What it does

Three methods on the `DocIngestingPDF` class (`Lumi-AI-Core/V2/DocIngestingPDF/DocIngestingPDF.py`):

1. `process_pdf({"pdfPath"})` — uploads the PDF, calls GPT-4o (max output 8000 tokens), returns `{"resultText": <raw model output>}`.
2. `parse_protocol_response({"resultText"})` — handed off to `parser_pdf.py`, which walks the text and emits `{"hierarchy": {...}}` with sequential IDs across stages, steps, actions, sub-actions.
3. `process_and_parse_pdf({"pdfPath"})` — convenience: runs both and returns both `resultText` and `hierarchy` in one call.

The prompt template is in `prompt_pdf.py`; tweak there if you want to bias extraction.

## Public API

```python
DocIngestingPDF({"openaiApiKey"?})       # else uses OPENAI_API_KEY env var

.process_pdf({"pdfPath": str})
  -> {"resultText": str} | error dict
.parse_protocol_response({"resultText": str})
  -> {"hierarchy": {...}} | error dict
.process_and_parse_pdf({"pdfPath": str})
  -> {"resultText": str, "hierarchy": {...}} | error dict
```

`__init__` raises if `openai` is not installed or no key is available; method calls return error dicts.

## Input/output shape

Not the canonical detection schema — this is structured-text I/O. The output `hierarchy` is the contract used by [V2.ProtocolBuilder](ProtocolBuilder.md) to compile a runnable plan. Each node has at minimum `id` (sequential int) and `description` (str); children live in nested lists keyed by level (`steps`, `actions`, `subActions`).

## Dependencies on other V2 modules

None directly. Pure OpenAI SDK wrapper. Conceptually paired with `V2.ProtocolBuilder` downstream.

## Used by which monitors / V2 modules

Best-effort: search for `V2.DocIngestingPDF` across the codebase. The natural consumer is the protocol-bootstrap pathway (web upload -> builder), not a live monitor. No direct importer found in `Lumi-AI-Continuous/monitors/` at the time of writing.

## Tests

- `Lumi-AI-Core/V2/DocIngestingPDF/test_doc_ingesting_pdf.py`

## Gotchas

- `OPENAI_API_KEY` is the canonical env var; passing `openaiApiKey` in `input_data` overrides it.
- Token limit is hard-coded at 8000 output tokens — long protocols may truncate. Watch for malformed JSON when parsing.
- Each `process_pdf` call uploads the PDF anew; cache `resultText` if you intend to re-parse without re-billing.
- The parser is deterministic regex / structure walking — if GPT-4o returns prose instead of the expected layout, parsing will return a `BAD_INPUT`-like error dict rather than guess.

## See also

- [V2.ProtocolBuilder](ProtocolBuilder.md) — the natural consumer of `hierarchy`
- [V2.CameraViewAnalyzer](CameraViewAnalyzer.md) — sibling LLM-vision wrapper, same OpenAI-SDK pattern
- [agreedDataSchema](../data-schema.md)
- `Lumi-AI-Core/V2/DocIngestingPDF/prompt_pdf.py` — the actual prompt
