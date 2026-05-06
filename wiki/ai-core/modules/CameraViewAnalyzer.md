---
name: V2.CameraViewAnalyzer
description: Uses GPT-4o vision to pick the best camera for a given subject and detect rotation needs — the bootstrap step for multi-camera monitor setups.
type: module
graph_node: core:CameraViewAnalyzer
sources:
  - { repo: Lumi-AI-Core, path: V2/CameraViewAnalyzer/CameraViewAnalyzer.py }
  - { repo: Lumi-AI-Core, path: V2/CameraViewAnalyzer/README.md }
tags: [v2-module, llm]
---

# V2.CameraViewAnalyzer

`CameraViewAnalyzer` answers two pre-flight questions you have to solve before any vision monitor can run on a multi-camera rig: **which camera has the best view of X**, and **does any camera need rotating 90°/180°/270° before downstream models will work**. It does both with one or two GPT-4o vision calls — a deliberate choice over training a classifier per machine.

## What it does

Given a dict of `cameraId -> BGR ndarray` and a list of natural-language criteria, the analyzer:

1. Resizes every image to fit `maxImageDimension` (default 1024) and base64-encodes as JPEG (`Lumi-AI-Core/V2/CameraViewAnalyzer/CameraViewAnalyzer.py`).
2. Sends a single multi-image request to OpenAI with a structured-JSON system prompt.
3. Parses the response (handles bare JSON, fenced JSON, and JSON-in-prose via regex).

For view ranking you get a winning `cameraId` per criterion plus a `confidence` and free-text `reason`. For rotation you get a `needsRotation` bool, `rotationDegrees` in `{0, 90, 180, 270}`, and reason per camera.

## Public API

```python
CameraViewAnalyzer(input_data: dict)
  # openaiApiKey (else env OPENAI_API_KEY), openaiModel="gpt-4o", maxImageDimension=1024

.analyze_camera_views({"images": dict, "viewCriteria": list[str], "config"?})
.detect_rotation_needs({"images": dict, "rotationCriteria": list[str], "config"?})
.analyze_complete({"images", "viewCriteria", "rotationCriteria", "config"?})  # both in one call
```

`__init__` raises `ValueError` if OpenAI is unavailable or no API key. Method calls return error dicts (`errorType`/`errorDesc`/`stackTrace`) on failure.

## Input/output shape

Not `agreedDataSchema.md` — this is a setup-time call, not a detection. Outputs are bespoke nested dicts (`cameraRankings`, `rotationNeeds`) plus an `analysisTime` float. See README sections "Output (Success)" for exact field layouts.

## Dependencies on other V2 modules

None. Stand-alone wrapper around `openai`, `numpy`, `opencv-python`, `Pillow`.

## Used by which monitors / V2 modules

Imported by the protocol arbiter and conftest in `Lumi-AI-Continuous` (`protocol_arbiter/arbiter.py`, `conftest.py`). It's designed for the **Weighing** flow per its README — when `startMonitor` arrives for `WEIGHING`, the arbiter pulls frames from all cameras, runs `analyze_complete`, and uses the result to drive [V2.Weighing](Weighing.md). Search for `V2.CameraViewAnalyzer` across `monitors/` to confirm coverage.

## Tests

- `Lumi-AI-Core/V2/CameraViewAnalyzer/test_CameraViewAnalyzer.py`

## Gotchas

- Costs OpenAI tokens per call. It's meant to run once at monitor start, not per-frame.
- The model occasionally embeds JSON inside prose; the parser handles this but is regex-fragile if OpenAI changes formatting.
- `images` keys (camera IDs) become exact strings in the output — keep them stable across calls.

## See also

- [V2.Weighing](Weighing.md) — the canonical downstream consumer
- [V2.MultiCamera](MultiCamera.md) — manages frame collection from many cameras
- [V2.Machine](Machine.md) — provides per-machine camera roster context
- [agreedDataSchema](../data-schema.md)
