---
name: V2.ReportGenerator
description: Generates LaTeX-rendered PDF reports combining protocol-execution analysis and per-monitor data visualisations.
type: module
graph_node: core:ReportGenerator
sources:
  - { repo: Lumi-AI-Core, path: V2/ReportGenerator/ReportGenerator.py }
  - { repo: Lumi-AI-Core, path: V2/ReportGenerator/Interpreters/ProtocolInterpreter.py }
  - { repo: Lumi-AI-Core, path: V2/ReportGenerator/Interpreters/AgentInterpreter.py }
tags: [v2-module]
---

# V2.ReportGenerator

`ReportGenerator` is the V2 module that produces post-run PDF deliverables from agent monitoring data and protocol-execution metadata. It's the artefact pipeline at the *end* of a run: protocol completeness analysis, per-monitor charts, and a LaTeX-rendered PDF. Everything else is upstream of it.

## What it does

Three classes, layered (`Lumi-AI-Core/V2/ReportGenerator/`):

- **`ProtocolInterpreter`** (`Interpreters/ProtocolInterpreter.py`) — analyses protocol-execution data, identifies incomplete stages/steps/actions, and draws a cascade timeline chart.
- **`AgentInterpreter`** (`Interpreters/AgentInterpreter.py`) — reads agent-monitoring JSON (or a dict) and produces visualisations per `monitorType`: COLOUR, TEXT, HOMOGENEITY, NEEDLE GAUGE, LIQUID DESCRIPTION, LIQUID VOLUME. Each type has its own visualiser under `Interpreters/AgentTypes/`.
- **`ReportGenerator`** (`ReportGenerator.py`) — composes the above into PDF reports via XeLaTeX or pdfLaTeX. Two report flavours: `generate_combined_report` (protocol + agent data) and `generate_basic_report` (with resources, ledger, screenshots from a remote endpoint).

Custom styling (logo, fonts, `reportStyle.sty`) lives under `Assets/`.

## Public API

- `ProtocolInterpreter({"openaiApiKey": ...})` -> `.incomplete_entites({"protocol": data})`, `.draw_cascade_chart({"protocol": data})`.
- `AgentInterpreter({"dataSource": dict_or_path, "openaiApiKey": ...})` -> `.create_visualization({})`.
- `ReportGenerator({"openaiApiKey": ..., "useCustomStyle": bool})` -> `.generate_combined_report({...})`, `.generate_basic_report({...})`.

All return V2 dicts; failures land as `{"errorType", "errorDesc", "stackTrace"}`.

## Input / output

Protocol data must include stages with timing info for cascade charts. Agent data must include a `monitorType` field for the visualiser to dispatch. Inputs/outputs use camelCase keys (per the README) — distinct from the snake_case used by detection modules. Outputs are PDF file paths plus interpreter results; not on the [agreedDataSchema.md](../data-schema.md) contract.

## Dependencies on other V2 modules

None directly. External deps: numpy, opencv-python, Pillow, matplotlib, requests, an OpenAI API key (advanced features), and a system LaTeX distribution (XeLaTeX or pdfLaTeX).

## Used by

The end-of-run report flow. Inputs typically come from monitor outputs (Lumi-AI-Continuous) and a protocol parsed by [V2.ProtocolBuilder](ProtocolBuilder.md). Not used by monitors themselves.

## Tests

- `Lumi-AI-Core/V2/ReportGenerator/test_report_generator.py`

## Gotchas

- LaTeX must be installed system-wide (`texlive-xetex` on Linux; MacTeX on macOS). Missing LaTeX -> `INTERNAL_ERROR` at PDF render time.
- `useCustomStyle=True` requires XeLaTeX (not pdfLaTeX) and the `Assets/reportStyle.sty` file on disk.
- `AgentInterpreter` dispatches on `monitorType` — agent data with an unknown or missing type yields a no-op (or error depending on the path). Validate upstream.
- `screenshotEndpoint` for `generate_basic_report` must be reachable; failures fetching screenshots degrade the report silently.

## See also

- [V2.ProtocolBuilder](ProtocolBuilder.md)
- [V2.PoCVIS](PoCVIS.md)
- [V2.Visualiser](Visualiser.md)
- [agreedDataSchema.md](../data-schema.md)
