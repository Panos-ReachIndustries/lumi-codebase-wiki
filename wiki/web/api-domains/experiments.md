---
name: web/api/experiments
description: Experiment lifecycle hooks — CRUD, status, layout, protocol tracking, internal resources, plus an experiment-scoped AI agent subfolder.
type: api-domain
graph_node: web:api:experiments
sources:
  - { repo: lumi-web-v2, path: src/api/experiments }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter_v2 }
tags: [web]
---

# web/api/experiments

Roughly 23 hooks at `lumi-web-v2/src/api/experiments/` covering the full experiment lifecycle: create, fetch, update, status, layout, protocol-tracking progress, internal resources (videos, action screenshots), report generation, image capture. It also nests two subfolders, `aiAgent/` and `comments/`, for the experiment-scoped variants of those flows. This is the second-largest domain after [workspaces](workspaces.md), and the two are almost mirror images of each other — workspaces is the "lab session" twin, experiments is the "scientific run" twin.

## The pattern, in a nutshell

```ts
// src/api/experiments/useGetExperiment.tsx (paraphrased)
const useGetExperiment = (params, opts) =>
  useConfiguredQuery<GetExperimentResponse>({
    getRequestConfig: () => ({
      url: gatewayRoutes.experiment.getExperiment,
      params
    }),
    queryOptions: {
      enabled: opts?.enabled ?? true,
      queryKey: [queryCacheKeys.experiment, params.experimentId]
    }
  });
```

Standard recipe. Mutations follow the `useConfiguredMutation` shape (see `useUpdateExperimentStatus.tsx`) and invalidate `[queryCacheKeys.experiment, experimentId]` — that one cache key is what makes the experiment page eventually-consistent across status, layout, resources, and protocol-progress edits.

## What lives in the folder

A representative slice (`ls lumi-web-v2/src/api/experiments/` for the rest):

| Hook | Purpose |
|------|---------|
| `useCreateExperiment`, `useGetExperiment`, `useUpdateExperiment` | Core CRUD. |
| `useGetExperimentStatus`, `useUpdateExperimentStatus` | Lifecycle state machine. |
| `useGetExperimentLayout`, `useUpdateExperimentLayout` | Drag-and-drop pinboard layout for the experiment page. |
| `useGetProtocolProgress`, `useUpdateProtocolProgress` | Step-by-step protocol tracking — read by `/experiment/[id]/live`. |
| `useGetProtocolCapturesHistory`, `useGetExperimentMediaList` | Media galleries. |
| `useAddInternalResources`, `useListInternalResources`, `useGetInternalResourceVideoManifest` | Attach uploaded videos / past clips as evidence. |
| `useGenerateReport` | Kicks off PDF report generation. |
| `useExperimentImageCapture`, `useBatchGenerateClips` | Snap stills / clips into the experiment. |
| `aiAgent/useCreateExperimentAiAgent`, `aiAgent/useStopExperimentAiAgent`, … | Experiment-scoped mirror of [aiAgents](aiAgents.md). |
| `comments/...` | Experiment-thread and per-device comment threads. |

## Backend mapping

Routes split by concern. The experiment record itself (`/v2/lab/experiment/...`) is a lab-API resource. The `aiAgent` subroutes (`/v2/ai/experiment/monitor/...`) forward to the same monitor-lifecycle service as [aiAgents](aiAgents.md), but tagged with the experiment ID so results are persisted against it. Live protocol tracking is fed from [arbiter:v2](../../ai-continuous/arbiters/v2.md) — the live page subscribes to status events, and these hooks read the persisted progress snapshot.

## Mocks

`lumi-web-v2/mocks/routes/experiments/` — 30+ fixture files mirroring the route list (`createExperiment.ts`, `getExperiment.ts`, `updateExperimentStatus.ts`, `getProtocolProgress.ts`, `listActionScreenshots.ts`, plus aiAgent and comment fixtures).

## Tests

End-to-end flows under `lumi-web-v2/test/e2e/experiments/` and the live-experiment spec at `test/e2e/live-experiment.spec.ts`.

## See also

- [workspaces](workspaces.md) — sibling domain with near-identical shape
- [protocols](protocols.md) — the protocols experiments are run against
- [arbiter:v2](../../ai-continuous/arbiters/v2.md) — live status source
- [monitors:custom](../../ai-continuous/monitors/custom.md) — what the experiment AI agent runs
- [devices](devices.md) — pattern reference
