---
name: web/api/protocols
description: Lab-side protocol authoring — create, version, publish. Sibling of notebookProtocols.
type: api-domain
graph_node: web:api:protocols
sources:
  - { repo: lumi-web-v2, path: src/api/protocols }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/protocols

Eight hooks under `lumi-web-v2/src/api/protocols/` for the lab-side protocol authoring flow. Protocols are the structured "step list" experiments and workspaces run against — once a version is published, the runtime arbiters can track progress through it. This domain handles protocol CRUD plus the version sub-lifecycle (create / get / update / publish). The notebook-flavoured authoring path lives in [notebookProtocols](notebookProtocols.md).

`useCreateProtocol` is notable for hitting the **v3** endpoint (`/v3/lab/protocol/create`) while everything else stays on v2 — that's the upload route, which accepts a `multipart/form-data` payload with an optional uploaded protocol file.

## The pattern, in a nutshell

```ts
// src/api/protocols/useCreateProtocol.tsx (paraphrased)
const useCreateProtocol = () =>
  useConfiguredMutation({
    getRequestConfig: (request) => {
      const data = new FormData();
      data.append("title", request.title);
      if (request.rawText) data.append("rawText", request.rawText);
      if (request.file) data.append("file", request.file);
      return {
        url: gatewayRoutes.protocol.createV3,
        method: "POST",
        data,
        onUploadProgress: (e) => request.onProgress?.(e)
      };
    },
    errorCodeMap,
    getKeysToInvalidate: () => [`queryCacheKeys.protocolsList`]
  });
```

Other mutations are JSON; only create accepts a file. `usePublishProtocolVersion` invalidates `[protocolVersion, versionId]` so the published flag flips immediately on the version page.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useCreateProtocol` | Multipart create with optional file/raw text. v3 endpoint. |
| `useGetProtocol`, `useGetProtocolsList`, `useUpdateProtocol` | Core CRUD. |
| `useCreateProtocolVersion`, `useGetProtocolVersion`, `useUpdateProtocolVersion` | Version lifecycle. |
| `usePublishProtocolVersion` | Mark a version published — gate for adoption by workspaces / experiments. |

## Backend mapping

Routes under `/v2/lab/protocol/*` (and `/v3/lab/protocol/create`). Once a version is published, the runtime side picks it up from the lab-API: [arbiter:v1](../../ai-continuous/arbiters/v1.md) tracks the legacy step format, while [arbiter:v2](../../ai-continuous/arbiters/v2.md) owns the structured-step format that the v3 create endpoint produces. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/protocols/` — eight fixtures (`create.ts`, `get.ts`, `list.ts`, `update.ts`, `createVersion.ts`, `getVersion.ts`, `updateVersion.ts`, `publishVersion.ts`).

## Tests

E2E coverage in the protocol-authoring specs.

## See also

- [notebookProtocols](notebookProtocols.md) — sibling notebook-side authoring path
- [experiments](experiments.md), [workspaces](workspaces.md) — consumers
- [arbiter:v1](../../ai-continuous/arbiters/v1.md), [arbiter:v2](../../ai-continuous/arbiters/v2.md) — runtime trackers
- [devices](devices.md) — pattern reference
