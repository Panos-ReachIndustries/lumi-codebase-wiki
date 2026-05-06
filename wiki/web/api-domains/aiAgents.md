---
name: web/api/aiAgents
description: TanStack Query hooks for the device-scoped AI agent (monitor) lifecycle — create, list, stop, fetch results.
type: api-domain
graph_node: web:api:aiAgents
sources:
  - { repo: lumi-web-v2, path: src/api/aiAgents }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
  - { repo: Lumi-AI-Continuous, path: monitors/custom }
tags: [web]
---

# web/api/aiAgents

Seven hooks under `lumi-web-v2/src/api/aiAgents/` that drive the **device-scoped** AI agent (a.k.a. monitor) lifecycle: spawning a custom-agent run on a camera, listing the agents currently active on a device, stopping them, and pulling their latest results back for display on `/device/[deviceId]`.

This domain is the "free-running" sibling of [experiments](experiments.md) and [workspaces](workspaces.md), which both wrap the same backend with extra context (an experiment ID or workspace ID) baked into the route. All three eventually drive a [monitors:custom](../../ai-continuous/monitors/custom.md) process.

## The pattern, in a nutshell

```ts
// src/api/aiAgents/useCreateAiAgent.tsx (paraphrased)
const useCreateAiAgent = () =>
  useConfiguredMutation<CreateAiAgentRequest, CreateAiAgentResponse>({
    getRequestConfig: (request) => ({
      url: gatewayRoutes.aiAgent.create,
      method: "POST",
      data: request
    }),
    errorCodeMap,
    getKeysToInvalidate: () => [`queryCacheKeys.activeAiAgentsByDeviceList`]
  });
```

Every hook in this folder follows the wiki-wide [devices](devices.md) recipe: `useConfiguredQuery` / `useConfiguredMutation` from `useRemoteData.ts`, routes from `gatewayRoutes.aiAgent.*`, types from `src/types/generated/`, and mutations invalidate the active-agent list so the device page repaints.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useCreateAiAgent` | Spawns a new agent (POST `/v2/ai/monitor/create`). Used from the moment-creation flow and the device-page action menu. |
| `useStopAiAgent` | Stops a running agent. |
| `useGetDeviceAiAgents` | Lists agents that ran on a device in a date window. Coerces Luxon `DateTime` to ISO strings (`useGetDeviceAiAgents.tsx`). |
| `useGetAiAgentDetailsList` | Paged details list for the device-page agent table. |
| `useGetAiAgentResults` | Pulls per-agent result frames for a given run. |
| `useGetLatestAiAgentResultsList` | One-shot batch of "latest result per agent" — drives the device dashboard tiles. |
| `useExportAiAgent` | Triggers a CSV/JSON export job. |

## Backend mapping

These routes (`/v2/ai/monitor/...`) are served by the lumi-API gateway, which forwards to the Lumi-AI services that own monitor lifecycle. The agent that actually runs is a [monitors:custom](../../ai-continuous/monitors/custom.md) process — every "AI agent" the user creates from the web is a custom-agent JSON config dispatched onto a device. Live results stream back over Kafka and are flushed to the moment / agent storage that these `getResults` hooks read from.

## Mocks

`lumi-web-v2/mocks/routes/aiAgents/` has one fixture file per route (`createAiAgent.ts`, `stopAiAgent.ts`, `getAiAgentResults.ts`, …). Use `yarn use-env mocks && yarn dev` to point the app at the mocks-server-lite instance (port 3100, see `mocks/server.ts`).

## Tests

No hook-level unit tests; coverage comes from Playwright specs under `lumi-web-v2/test/e2e/ai-agents/` running against the mocks server.

## See also

- [devices](devices.md) — exemplar for the hook pattern this domain follows
- [experiments](experiments.md) and [workspaces](workspaces.md) — context-scoped variants
- [moments](moments.md) — how operators wrap an agent run for sharing
- [monitors:custom](../../ai-continuous/monitors/custom.md) — the backend that actually runs the agent
- [kubb-pipeline](../kubb-pipeline.md) — where `CreateAiAgentRequest` etc. come from
