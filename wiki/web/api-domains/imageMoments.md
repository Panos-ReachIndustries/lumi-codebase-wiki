---
name: web/api/imageMoments
description: Hooks for image-moment uploads, results retrieval, and device association.
type: api-domain
graph_node: web:api:imageMoments
sources:
  - { repo: lumi-web-v2, path: src/api/imageMoments }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/imageMoments

Eight hooks under `lumi-web-v2/src/api/imageMoments/` that power the image-moment flow — uploading a still image (rather than capturing from a live device), running an AI analysis on it, and storing the result for sharing. Image moments are the static-input cousin of [moments](moments.md): same UI shell, different ingest path. They live behind the `(authenticated)/moment/image/[imageAiAgentType]/[imageMomentId]` route group.

## The pattern, in a nutshell

```ts
// src/api/imageMoments/useUploadImageMomentRequest.tsx (paraphrased)
const useUploadImageMomentRequest = () =>
  useConfiguredMutation({
    getRequestConfig: (request) => ({
      url: gatewayRoutes.imageMoments.uploadImageMomentRequest,
      method: "POST",
      data: request,
      onUploadProgress: (e) => request.onProgress?.(e)
    }),
    errorCodeMap,
    getKeysToInvalidate: () => [`queryCacheKeys.imageMomentsList`]
  });
```

The upload hook threads an `onUploadProgress` callback through the request config so the UI can render a progress bar — same FormData-with-progress trick used by [protocols](protocols.md) and [organisation](organisation.md). Update mutations invalidate `[queryCacheKeys.imageMoment, imageMomentId]` so the moment page repaints after edits.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useUploadImageMomentRequest` | Multipart upload of an image, kicks off processing. |
| `useCreateImageMoment` | Creates the moment record itself (post-upload). |
| `useGetImageMoment` | Fetch a single moment by ID. |
| `useGetImageMomentsList` | Paginated list view. |
| `useGetImageMomentResults` | Latest analysis results for a moment. |
| `useUpdateImageMoment` | Edit metadata / title / description. |
| `useUpdateImageMomentDevices` | Associate / disassociate devices (`updateDevices` route). Invalidates the single-moment cache. |
| `useRemoveImageMomentResults` | Wipe results so the moment can be re-run. |

## Backend mapping

Routes under `/v2/ai/image-moment/*`. The image is forwarded through the lumi-API gateway to the same family of inference handlers as [aiSingular](aiSingular.md) for one-shot runs, or queued for a background process for heavier analyses. Persistence is in the AI moments store shared with [moments](moments.md) — the user-facing distinction is just the ingest format. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/imageMoments/` — eight fixtures, one per route (`createImageMoment.ts`, `uploadImageMomentRequest.ts`, `getImageMomentResults.ts`, `updateImageMomentDevices.ts`, etc.).

## Tests

E2E coverage shares the moment-flow specs; no dedicated hook unit tests.

## See also

- [moments](moments.md) — live-camera counterpart
- [aiSingular](aiSingular.md) — the inference path image-moments rely on
- [devices](devices.md) — pattern exemplar
- [kubb-pipeline](../kubb-pipeline.md)
