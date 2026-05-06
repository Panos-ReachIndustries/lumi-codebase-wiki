---
name: web/api/workspaces
description: The largest API domain — workspaces are the live "lab session" primitive. CRUD, status, layout, protocol tracking, internal resources, files, data tables, well plates, plus aiAgent and comments subfolders.
type: api-domain
graph_node: web:api:workspaces
sources:
  - { repo: lumi-web-v2, path: src/api/workspaces }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter_v2 }
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter_v3 }
tags: [web]
---

# web/api/workspaces

Roughly 36 hooks at `lumi-web-v2/src/api/workspaces/` — the largest domain in the codebase. Workspaces are the **live lab session** primitive: an operator opens a workspace, picks a device, optionally attaches a protocol, runs through it, captures stills/clips, edits the well-plate state, sends live messages, and finalises into a record. This domain mirrors [experiments](experiments.md) almost feature-for-feature, plus a handful of workspace-only flows (`finaliseWorkspace`, `createDraft`, `wellPlate.getState`, `live.message`, ledger download).

Use this as the catch-all for "what hooks does the workspace page actually call" — it's most of them.

## The pattern, in a nutshell

```ts
// src/api/workspaces/useFinaliseWorkspace.ts (paraphrased)
const useFinaliseWorkspace = () =>
  useConfiguredMutation<FinaliseWorkspaceRequest, FinaliseWorkspaceResponse>({
    getRequestConfig: (request) => ({
      url: gatewayRoutes.workspace.finalise,
      method: "POST",
      data: request
    }),
    errorCodeMap,
    getKeysToInvalidate: (request) => [`queryCacheKeys.workspace`, request.workspaceId]
  });
```

Same canonical recipe as [experiments](experiments.md): `useConfiguredQuery` / `useConfiguredMutation`, routes from `gatewayRoutes.workspace.*`, types from `src/types/generated/`, mutations invalidate `[workspace, workspaceId]` so the workspace page repaints consistently across edits.

## What lives in the folder

A representative slice (36 hooks total — `ls lumi-web-v2/src/api/workspaces/` for the rest):

| Group | Hooks |
|-------|-------|
| Core CRUD | `useCreateWorkspace`, `useCreateWorkspaceDraft`, `useGetWorkspace`, `useUpdateWorkspace`, `useFinaliseWorkspace`, `useUpdateWorkspaceExpiration` |
| Status | `useGetWorkspaceStatus`, `useUpdateWorkspaceStatus` |
| Layout | `useGetWorkspaceLayout`, `useUpdateWorkspaceLayout` |
| Protocol tracking | `useGetProtocolTrackingProgress`, `useUpdateProtocolTrackingProgress`, `useResetProtocolTrackingProgress` |
| Files / data tables | `useGetWorkspaceFiles`, `useUploadWorkspaceFile`, `useDeleteWorkspaceFile`, `useGetWorkspaceDataTables`, `useUploadWorkspaceDataTable`, `useDeleteWorkspaceDataTable` |
| Internal resources | `useAddWorkspaceInternalResources`, `useListWorkspaceInternalResources`, `useRemoveWorkspaceInternalResources`, `useGetInternalResourcesVideoManifests` |
| Devices / media | `useGetWorkspaceDeviceList`, `useGetWorkspaceMediaList`, `useWorkspaceImageCapture`, `useBatchGenerateClips` |
| Well plate / live | `useGetWorkspaceWellPlate`, `useSendLiveMessage` |
| References | `useAddWorkspaceReferences`, `useRemoveWorkspaceReference`, `useUpdateWorkspaceReference` |
| Reports / ledger | `useGenerateWorkspaceReport`, `useDownloadWorkspaceLedger` |
| Subfolders | `aiAgent/` (6 hooks — workspace-scoped mirror of [aiAgents](aiAgents.md)), `comments/workspaceComments/`, `comments/deviceComments/` |

## Backend mapping

Routes under `/v2/lab/workspace/*` (lab service), `/v2/ai/workspace/monitor/*` (the aiAgent subfolder, monitor-lifecycle service), and `/v2/device/workspace/*` (device-comment / device-media subroutes). The live workspace page is wired to [arbiter:v2](../../ai-continuous/arbiters/v2.md) and [arbiter:v3](../../ai-continuous/arbiters/v3.md) for protocol-tracking status updates, and to [monitors:custom](../../ai-continuous/monitors/custom.md) for workspace-scoped agent runs.

## Mocks

`lumi-web-v2/mocks/routes/workspaces/` — 30+ fixtures mirroring the route list including the aiAgent and comment subroutes.

## Tests

E2E coverage is heaviest here — Playwright specs around workspace creation, live workspace, protocol tracking, finalise. No dedicated hook unit tests.

## See also

- [experiments](experiments.md) — sibling domain with near-identical shape
- [protocols](protocols.md), [notebookProtocols](notebookProtocols.md) — protocols a workspace runs against
- [arbiter:v2](../../ai-continuous/arbiters/v2.md), [arbiter:v3](../../ai-continuous/arbiters/v3.md) — live status sources
- [monitors:custom](../../ai-continuous/monitors/custom.md) — what the workspace AI agent runs
- [records](records.md) — what `finaliseWorkspace` produces
- [devices](devices.md) — pattern reference
