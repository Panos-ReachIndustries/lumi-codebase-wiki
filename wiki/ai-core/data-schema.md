---
name: V2 Data Schema
description: The canonical I/O contract between V2 modules. Lives in Lumi-AI-Core/agreedDataSchema.md.
type: concept
tags: [v2, schema]
sources:
  - { repo: Lumi-AI-Core, path: agreedDataSchema.md }
---

# V2 Data Schema

The canonical I/O contract between V2 modules. Source of truth: [`Lumi-AI-Core/agreedDataSchema.md`](../../../Lumi-AI-Core/agreedDataSchema.md).

This wiki page is intentionally a pointer — duplicating the schema would cause it to drift. Read the source.

## What it covers (1-paragraph summary)

The schema defines the JSON shapes that move between V2 modules: detections (normalised bbox + confidence + class_name + optional masks), hand keypoints (21-point COCO-WholeBody-Hand layout), batched image-to-image tensor I/O, polygon segmentation contours in normalised coords, and the standard error envelope (`errorType`, `errorDesc`, `stackTrace`).

## Why it matters

If you're adding a new detector, tracker, or module that produces frame-level results, **conform to this schema**. Downstream consumers (e.g. `V2.Tracking`, the custom agent pipeline) assume it.

## See also

- [V2.Detection](modules/Detection.md) — exemplar producer
- The source: [`agreedDataSchema.md`](../../../Lumi-AI-Core/agreedDataSchema.md)
