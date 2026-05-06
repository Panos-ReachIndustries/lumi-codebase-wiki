---
name: V2.NuclioRequest
description: HTTP client wrapper for Nuclio serverless function endpoints — handles base64 image encoding, mask decoding, and V2-style error responses.
type: module
graph_node: core:NuclioRequest
sources:
  - { repo: Lumi-AI-Core, path: V2/NuclioRequest/NuclioRequest.py }
tags: [v2-module]
---

# V2.NuclioRequest

`NuclioRequest` is the V2 module that sends HTTP requests to Nuclio-deployed inference functions. It is *only* an HTTP client — no model code lives here. It exists to give callers a stable Python API over remote Nuclio endpoints (currently the SAM segmenter), with automatic image base64 encoding/decoding and standard V2 error reporting.

## What it does

Wraps `requests` calls to one or more configured Nuclio URLs (`Lumi-AI-Core/V2/NuclioRequest/NuclioRequest.py:13`). On request, encodes a numpy `BGR` image to JPEG/base64; on response, decodes any returned mask back into a numpy array under the `mask_decoded` key. Tracks request times. Errors never raise from public methods — they come back as `{"errorType": ..., "errorDesc": ..., "stackTrace": ...}` dicts.

## Public API

`NuclioClient({"endpoints": {name: url, ...}, "default_endpoint": name})`:

- `segment_with_points({"image": np.ndarray, "points": [[x,y], ...], "labels": [1|0, ...], "endpoint": name})` → `{"jobId", "box", "polygons", "mask", "mask_decoded", "request_time"}`.
- `segment_with_box({"image": np.ndarray, "box": [x1,y1,x2,y2], "endpoint": name})` → same shape.
- `get_job({"jobId": str, "endpoint": name})` → previously computed result.
- `recompute_job({"jobId": str, "box": [...], "endpoint": name})` → re-run with a new prompt.

## Input / output

Inputs are V2 dicts; image arrays are BGR uint8 (numpy). Outputs are JSON-decoded responses extended with `mask_decoded` (numpy `H×W` mask) when masks are returned. The client raises `ValueError` from the *constructor* if `endpoints` is missing or malformed; runtime failures return error dicts.

## Dependencies on other V2 modules

None. Uses `requests`, `opencv-python`, `numpy` only (`Lumi-AI-Core/V2/NuclioRequest/requirements.txt`).

## Used by

The SAM-segmenter Nuclio endpoint is the primary consumer; any V2 module that needs SAM-style point/box-prompted segmentation but doesn't want to host SAM in-process can use this wrapper. [V2.Vessels](Vessels.md) and [V2.SegmentAnything](SegmentAnything.md) cover the in-process equivalent.

## Tests

- `Lumi-AI-Core/V2/NuclioRequest/test_nuclio_client.py`
- `Lumi-AI-Core/V2/NuclioRequest/test_function.py`

## Gotchas

- Endpoints must be HTTP/HTTPS URLs and the dict must be non-empty — both are validated at construction.
- `points` and `labels` must have the same length; mismatch → `BAD_INPUT`.
- The remote function must accept the JSON shape the client sends. Adding new function types means adding a new method *and* extending `exposed_functions.json` — there's no generic `call` method.
- This client expects synchronous Nuclio function responses; long-running jobs would need a different pattern.

## See also

- [V2.SegmentAnything](SegmentAnything.md)
- [V2.Vessels](Vessels.md)
- [V2.Detection](Detection.md)
- [agreedDataSchema.md](../data-schema.md)
