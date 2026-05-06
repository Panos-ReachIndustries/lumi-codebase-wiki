---
name: web/api/notebookProtocols
description: Notebook-side protocol authoring — create, update, version, parse, export. Sibling of the lab-side protocols domain.
type: api-domain
graph_node: web:api:notebookProtocols
sources:
  - { repo: lumi-web-v2, path: src/api/notebookProtocols }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/notebookProtocols

Eleven hooks under `lumi-web-v2/src/api/notebookProtocols/` covering the **notebook-flavoured** protocol authoring path. These are protocols a user writes inside the notebook UI (free-form sections, attachments, embedded data tables) rather than the more structured lab-side ones in [protocols](protocols.md). Both flows ultimately produce a published version that experiments and workspaces can reference, but the editing surface and storage shapes differ.

## The pattern, in a nutshell

```ts
// src/api/notebookProtocols/useParseNotebookProtocolVersion.tsx (paraphrased)
const useParseNotebookProtocolVersion = () =>
  useConfiguredMutation<ParseNotebookProtocolVersionRequest, SuccessResponse>({
    getRequestConfig: (request) => ({
      url: gatewayRoutes.notebookProtocol.parseVersion,
      method: "POST",
      data: request
    }),
    errorCodeMap,
    getKeysToInvalidate: (request) => [
      [queryCacheKeys.notebookProtocolVersion, request.versionId],
      [queryCacheKeys.notebookProtocol, request.protocolId]
    ]
  });
```

The double-invalidation is the flavour signature here — most mutations touch both the version-level cache and the parent-protocol cache so the editor refreshes consistently.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useCreateNotebookProtocol`, `useGetNotebookProtocol`, `useGetNotebookProtocolList`, `useUpdateNotebookProtocol` | Core CRUD. |
| `useCreateNotebookProtocolVersion`, `useGetNotebookProtocolVersion`, `useUpdateNotebookProtocolVersion` | Version lifecycle. |
| `usePublishNotebookProtocolVersion` | Marks a version published — the gate before workspaces / experiments can adopt it. |
| `useParseNotebookProtocolVersion` | Server-side parse / validate of free-form notebook content into structured steps. |
| `useExportNotebookProtocolVersion` | Export to PDF / structured format. |
| `useGetNotebookProtocolWorkspaces` | Lists workspaces currently using this protocol — used in the protocol overview. |

## Backend mapping

Routes under `/v2/notebook/protocol/*`, served by the lumi-API gateway. The notebook-protocol service stores a richer document model than the lab side and runs a parse step that breaks free-form content into the structured steps that the [arbiter:v2](../../ai-continuous/arbiters/v2.md) and [arbiter:v3](../../ai-continuous/arbiters/v3.md) can track during a live run. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/notebookProtocols/` — eleven fixtures (`create.ts`, `get.ts`, `list.ts`, `createVersion.ts`, `parseVersion.ts`, `publishVersion.ts`, `exportVersion.ts`, `workspacesList.ts`, …).

## Tests

E2E coverage in the protocol-authoring specs; no dedicated hook unit tests.

## See also

- [protocols](protocols.md) — sibling lab-side authoring path
- [workspaces](workspaces.md) and [experiments](experiments.md) — consumers of published versions
- [arbiter:v2](../../ai-continuous/arbiters/v2.md), [arbiter:v3](../../ai-continuous/arbiters/v3.md) — runtime trackers of parsed steps
- [devices](devices.md) — pattern reference
