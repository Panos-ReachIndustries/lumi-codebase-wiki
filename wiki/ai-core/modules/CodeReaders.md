---
name: V2.CodeReaders
description: Unified barcode / QR / DataMatrix reader with one V2 wrapper that routes to pyzbar or pylibdmtx backends per code type.
type: module
graph_node: core:CodeReaders
sources:
  - { repo: Lumi-AI-Core, path: V2/CodeReaders/base_reader.py }
  - { repo: Lumi-AI-Core, path: V2/CodeReaders/BarcodeReader/BarcodeReader.py }
  - { repo: Lumi-AI-Core, path: V2/CodeReaders/QRCodeReader/QRCodeReader.py }
  - { repo: Lumi-AI-Core, path: V2/CodeReaders/DataMatrixReader/DataMatrixReader.py }
  - { repo: Lumi-AI-Core, path: V2/CodeReaders/README.md }
tags: [v2-module]
---

# V2.CodeReaders

`CodeReaders` is the V2 module for reading machine-readable codes off a frame. The everyday entry point is `CodeReaderWrapper` — give it a frame and a `codeTypes` list and it dispatches to one or more backend readers (`BarcodeReader`, `QRCodeReader`, `DataMatrixReader`). All three readers share a common `BaseCodeReader` interface and a single output schema.

## What it does

`CodeReaderWrapper.read({"frame", "codeTypes", "config"?})` runs the requested backends and concatenates results (`Lumi-AI-Core/V2/CodeReaders/base_reader.py`):

- `BarcodeReader` (linear codes, e.g. `CODE128`) — pyzbar, with denoise + CLAHE + sharpening preprocessing for low-contrast labels.
- `QRCodeReader` — pyzbar.
- `DataMatrixReader` — pylibdmtx (separate library because pyzbar can't read DataMatrix).

Lazy imports keep heavy deps out of the import path until you actually use them.

## Public API

```python
CodeReaderWrapper({"codeTypes": ["barcode", "qr"]})  # default; add "datamatrix" explicitly
  .read({"frame": ndarray, "codeTypes"?: list[str], "config"?: dict})
    -> {"codes": [{"data": str, "type": str, "bbox": [x, y, w, h]}, ...]}
```

Direct access is also exported:

```python
from V2.CodeReaders import BarcodeReader, QRCodeReader, DataMatrixReader
```

All return V2 error dicts on failure with `codes: []` always present.

## Input/output shape

Custom — not the detection schema. `bbox` is `[x, y, w, h]` in **pixel** space (not normalised), `type` is the pyzbar/pylibdmtx symbol name (`"CODE128"`, `"QRCODE"`, `"DATAMATRIX"`, ...).

## Dependencies on other V2 modules

None. Pure backend wrappers around pyzbar and pylibdmtx; both have system-library prereqs (`libzbar`, `libdmtx0`).

## Used by which monitors / V2 modules

No direct `V2.CodeReaders` importers found under `Lumi-AI-Continuous/monitors/` at time of writing — best-effort: search for `V2.CodeReaders` across `monitors/`. The natural consumer is any vessel-labelling monitor that needs to decode tube barcodes.

## Tests

- `Lumi-AI-Core/V2/CodeReaders/tests/test_code_readers.py`
- `Lumi-AI-Core/V2/CodeReaders/tests/test_exposed_functions_compliance.py` — keeps implementation in sync with `exposed_functions.json`.

## Gotchas

- **DataMatrix is opt-in for a reason.** Per the README's benchmarks, DataMatrix alone is ~390 ms/frame vs ~29 ms for barcode-only. Do **not** include `"datamatrix"` in `codeTypes` unless you actually need it — adding it bumps a 47 ms call to 400+ ms.
- `pyzbar` cannot decode DataMatrix; if you put a DataMatrix code in front of `BarcodeReader` it will silently miss it.
- `bbox` is pixel coordinates, unlike most V2 modules which use normalised `[0,1]` bboxes.
- Thread safety of a shared wrapper instance is not tested — use one per worker.

## See also

- [V2.TextReader](TextReader.md) — sibling for OCR (free-form text rather than codes)
- [V2.Detection](Detection.md) — for finding *where* labels are before reading them
- [agreedDataSchema](../data-schema.md)
- [V2.Vessels](Vessels.md) — the most likely upstream identifier of label regions
