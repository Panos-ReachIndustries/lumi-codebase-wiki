---
name: web/api/aiSingular
description: One-shot inference hooks — fire an image at a model, get a single answer back. No lifecycle, no Kafka.
type: api-domain
graph_node: web:api:aiSingular
sources:
  - { repo: lumi-web-v2, path: src/api/aiSingular }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/aiSingular

Four hooks under `lumi-web-v2/src/api/aiSingular/`. Each one does the same thing structurally — POST an image (or image reference) to `/v2/ai/singular/...` and receive a single typed answer. There is no lifecycle, no streaming, no Kafka; this is the "REST-style" face of Lumi's AI stack, used inline from the UI when the user wants a one-off answer about a single frame.

Compare with [aiAgents](aiAgents.md), which is the long-running, Kafka-streamed counterpart. Singular is for "what's in this picture, right now"; aiAgents is for "watch this camera for the next hour".

## The pattern, in a nutshell

```ts
// src/api/aiSingular/useGetVesselMask.tsx (paraphrased)
const useGetVesselMask = (params, { enabled }) =>
  useConfiguredQuery<GetVesselMaskResponse>({
    getRequestConfig: () => ({
      url: gatewayRoutes.aiSingular.getVesselMask,
      method: "POST",
      data: params
    }),
    queryOptions: { enabled }
  });
```

`useGetGaugeDataFromImage` adds `staleTime: apiConfig.queryStaleTimes.live` for tighter cache invalidation, but the shape is identical across all four. Notice they're all `useQuery` despite being POSTs — the call is idempotent for a given (image, model) pair, so caching makes sense.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useGenerateMomentTitle` | Auto-generates a moment title from a captured image. Used in the moment-creation form. |
| `useGetVesselMask` | Returns a vessel-segmentation mask for a captured frame. Drives the wellplate / vessel preview overlays. |
| `useGetGaugeDataFromImage` | Extracts dial / gauge readings from a frame. Used in the dial-monitor moment editor. |
| `useGetTextRegionsFromImage` | OCR/text-region detection for labels and handwriting. Used by the operator notes flow. |

## Backend mapping

`/v2/ai/singular/*` routes resolve through the lumi-API gateway to per-model inference handlers backed by the same V2 modules that power the continuous monitors — vessel mask uses [V2.Vessels](../../ai-core/modules/Vessels.md), gauge reading shares a backbone with [monitors:dial](../../ai-continuous/monitors/dial.md), and text regions reuse [V2.CodeReaders](../../ai-core/modules/CodeReaders.md). Backend: lumi-API gateway forwards to a stateless inference worker; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/aiSingular/` — one fixture per route: `generateMomentTitle.ts`, `getVesselMask.ts`, `getGaugeDataFromImage.ts`, `getTextRegionsFromImage.ts`.

## Tests

No hook-level tests. Visual outputs (overlays drawn from masks) are smoke-tested via Storybook stories on the consuming components.

## See also

- [aiAgents](aiAgents.md) — the streaming counterpart
- [imageMoments](imageMoments.md) — image-moment flow that calls these on the fly
- [monitors:dial](../../ai-continuous/monitors/dial.md) — long-running gauge analogue
- [V2.Vessels](../../ai-core/modules/Vessels.md), [V2.CodeReaders](../../ai-core/modules/CodeReaders.md)
- [kubb-pipeline](../kubb-pipeline.md)
