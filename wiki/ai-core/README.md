---
name: Lumi-AI-Core
description: V2-only AI/CV class libraries — detection, tracking, segmentation, vessels, pipetting, and friends. The repo every Lumi monitor leans on.
type: repo
graph_node: repo:core
sources:
  - { repo: Lumi-AI-Core, path: README.md }
  - { repo: Lumi-AI-Core, path: agreedDataSchema.md }
  - { repo: Lumi-AI-Core, path: V2/STANDARDS.md }
tags: [repo]
---

# Lumi-AI-Core

`Lumi-AI-Core` is the AI/CV library that every Lumi monitor and arbiter depends on for the *vision* parts of their job. The codebase is **V2-only** — there is no `V1/` to fall back to. Every module lives under `V2/` and follows a small set of conventions documented in `Lumi-AI-Core/V2/STANDARDS.md`.

## Layout

```
Lumi-AI-Core/
├── V2/                    # 35 modules (one folder each)
├── agreedDataSchema.md    # the canonical inter-module data contract
├── docker-compose.pytest.yml
├── pytest.ini
├── weights/               # placeholder; weights ship out-of-band
└── README.md
```

Each `V2/<Name>/` folder is self-contained: its own `README.md`, optional `requirements.txt`, an `exposed_functions.json` describing the dict-style public API, and co-located `test_*.py` files.

## How to think about the modules

Roughly three layers, top-down:

- **Infrastructure** — leaf utilities that everything else imports: [V2.Utils](modules/Utils.md) (geometry, image, data converters), [V2.BasicOps](modules/BasicOps.md), [V2.ModelInference](modules/ModelInference.md) (YOLO / template matching / pose model wrappers), [V2.NuclioRequest](modules/NuclioRequest.md).
- **Vision primitives** — generic CV building blocks: [V2.Detection](modules/Detection.md) (the unified detection contract), [V2.Tracking](modules/Tracking.md) (multi-object tracking), [V2.SegmentAnything](modules/SegmentAnything.md), [V2.ModularDetector](modules/ModularDetector.md), [V2.BackgroundSubtraction](modules/BackgroundSubtraction.md), [V2.GridTracker](modules/GridTracker.md), [V2.MultiCamera](modules/MultiCamera.md), [V2.HistoricVideoAnalysis](modules/HistoricVideoAnalysis.md), [V2.CameraViewAnalyzer](modules/CameraViewAnalyzer.md), [V2.Visualiser](modules/Visualiser.md).
- **Task-specific** — modules wired to a particular lab activity: [V2.Vessels](modules/Vessels.md), [V2.Pipetting](modules/Pipetting.md), [V2.LabContainerTracking](modules/LabContainerTracking.md), [V2.Vortexing](modules/Vortexing.md), [V2.Weighing](modules/Weighing.md), [V2.WellPlate](modules/WellPlate.md), [V2.TextReader](modules/TextReader.md), [V2.ThinLayerChromatography](modules/ThinLayerChromatography.md), [V2.CentrifugeAngleAnalyzer](modules/CentrifugeAngleAnalyzer.md), [V2.Dimensions](modules/Dimensions.md), [V2.Colours](modules/Colours.md), [V2.Gestures](modules/Gestures.md), [V2.CodeReaders](modules/CodeReaders.md), [V2.VisibleObjectList](modules/VisibleObjectList.md), [V2.ObjectInteractionsManager](modules/ObjectInteractionsManager.md), [V2.Interactions](modules/Interactions.md), [V2.Machine](modules/Machine.md), [V2.PoCVIS](modules/PoCVIS.md), [V2.DocIngestingPDF](modules/DocIngestingPDF.md), [V2.ProtocolBuilder](modules/ProtocolBuilder.md), [V2.ReportGenerator](modules/ReportGenerator.md).

The grouping is informal — there's nothing in the directory layout that enforces it.

## The data contract

`Lumi-AI-Core/agreedDataSchema.md` is the canonical contract: detection bbox shape, segmentation shape, glove/hand pose shape, image-to-image task shape. Every V2 module that produces or consumes detections speaks this dialect. New modules should *wrap* their backend to emit the schema — never invent a new one. See [agreedDataSchema.md](data-schema.md).

V2 modules also share an error convention: rather than raising, runtime methods return `{"errorType": "BAD_INPUT" | "INTERNAL_ERROR", "errorDesc": str, "stackTrace": str}`. `__init__` is the exception — it raises `ValueError` because there's nothing meaningful to do with a half-constructed object.

## Running tests

From the `Lumi-AI-Core/` repo root:

```bash
# Full suite (allow ~30 min for first build + run)
docker compose -f docker-compose.pytest.yml run --rm test-runner

# One module
docker compose -f docker-compose.pytest.yml run -e PYTEST_ARGS="V2/Detection" --rm test-runner

# Re-run last failures
docker compose -f docker-compose.pytest.yml run -e PYTEST_ARGS="--lf" --rm test-runner
```

The container is capped at 2 CPUs / 4 GB RAM so it fits inside GitHub Actions. Per-test timeout is 600s (`pytest.ini`).

## Where weights live

`Lumi-AI-Core/weights/` exists as a placeholder — actual model weights ship **out-of-band** (S3, Nuclio model registry, etc.). Each module's `__init__` accepts a `samWeights` / `yoloModelWeights` / `fcn_weights` path or URL. For SAM2 a typical path looks like `https://reach-ml-weights.s3.eu-west-2.amazonaws.com/vessels/sam2.1_hiera_small.pt`. Don't commit weights to the repo.

## See also

- [agreedDataSchema.md](data-schema.md) — the inter-module contract
- [V2.Detection](modules/Detection.md) — the exemplar V2 module
- [System overview](../architecture/system-overview.md)
