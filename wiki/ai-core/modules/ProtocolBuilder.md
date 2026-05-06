---
name: V2.ProtocolBuilder
description: LLM-backed parser that decomposes scientific protocols into structured stages/steps/actions and generates custom-agent configs. Wraps OpenAI GPT-4o and Google Gemini.
type: module
graph_node: core:ProtocolBuilder
sources:
  - { repo: Lumi-AI-Core, path: V2/ProtocolBuilder/ChatWrapper.py }
  - { repo: Lumi-AI-Core, path: V2/ProtocolBuilder/GeminiWrapper.py }
  - { repo: Lumi-AI-Core, path: V2/ProtocolBuilder/config_generator.py }
  - { repo: Lumi-AI-Core, path: V2/ProtocolBuilder/ProtocolAnalyser.py }
tags: [v2-module, llm]
---

# V2.ProtocolBuilder

`ProtocolBuilder` is the V2 module that uses LLMs to turn unstructured scientific protocol text (or a PDF) into structured laboratory-automation artefacts. It is the codebase's main *external-LLM-dependent* module — every public entry point ultimately calls OpenAI GPT-4o or Google Gemini.

## What it does

Two flavours, same shape:

- **`ChatWrapper`** wraps OpenAI GPT-4o; **`GeminiWrapper`** wraps Google `gemini-2.5-flash-lite`. Both expose `callChat({"text": ..., "maxSteps": ...})` for protocol-text decomposition and `callChatPDF({"pdfFilepath": ..., "maxSteps": ...})` for PDF analysis. The system prompt is supplied at construction; iterative analysis runs `maxSteps` rounds and returns the conversation messages.
- **`ConfigGenerator`** (`Lumi-AI-Core/V2/ProtocolBuilder/config_generator.py`) takes a parsed protocol JSON plus an optional `selectedModules` list and asks the LLM to pick which V2 module classes/functions to wire into a custom-agent config. Constructor and function arguments are intentionally left blank — the user fills them in.

Prompts and the parser live in `prompts.py` / `parser.py` (legacy) and `v2prompts.py` / `v2parser.py` (current). `ProtocolAnalyser.py` is the legacy higher-level driver.

## Public API

- `ChatWrapper({"systemPrompt": str, "apiKey"?: str})` → `.callChat(...)`, `.callChatPDF(...)`.
- `GeminiWrapper({"systemPrompt": str, "apiKey"?: str})` → `.callChat(...)`, `.callChatPDF(...)`.
- `ConfigGenerator({"modelWeight"?: str})` → `.generate_config({"protocolFilepath"?, "protocolData"?, "selectedModules"?})` returning `{"agent_definition": {"blocks": [...]}}`.

## Input / output

Inputs are V2 dicts; outputs are dicts with `messages: list[str]`, `totalSteps: int`, or `agent_definition`. Failures land as `{"errorType": "BAD_INPUT" | "INTERNAL_ERROR", "errorDesc": ..., "stackTrace": ...}`. Not on the [agreedDataSchema.md](../data-schema.md) detection contract — this is a text/document module.

## Dependencies on other V2 modules

- Reads every V2 module's `exposed_functions.json` (`config_generator._get_exposed_functions_paths`). When the surface of any V2 module changes, that JSON must be updated or `ConfigGenerator` will produce stale configs.

## Used by

The protocol-to-config flow that bootstraps custom agents from new protocol PDFs. Not used by lab monitors — they're configured manually.

## Tests

- `Lumi-AI-Core/V2/ProtocolBuilder/test_config_generator.py`
- Sample input: `Lumi-AI-Core/V2/ProtocolBuilder/test_protocol.json`.

## Gotchas

- Requires `OPENAI_API_KEY` (ChatWrapper, ConfigGenerator) or `GEMINI_API_KEY` (GeminiWrapper) — set as env var or pass via `apiKey`.
- `callChat` resets conversation history on each call — there's no multi-turn memory across calls.
- `ConfigGenerator` deliberately produces *partial* configs: class/function selections only. Constructor args and function args are user-supplied. Don't expect a runnable agent definition straight from the LLM.
- LLM output is non-deterministic — same protocol can yield different module choices across runs.

## See also

- [V2.ReportGenerator](ReportGenerator.md)
- [V2.DocIngestingPDF](DocIngestingPDF.md)
- [V2.Pipetting](Pipetting.md)
- [agreedDataSchema.md](../data-schema.md)
