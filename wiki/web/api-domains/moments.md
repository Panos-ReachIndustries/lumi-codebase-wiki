---
name: web/api/moments
description: Operator "moment" notes and alerts — wraps an AI agent run with a story, a status, and an alert subscription.
type: api-domain
graph_node: web:api:moments
sources:
  - { repo: lumi-web-v2, path: src/api/moments }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/moments

Thirteen hooks under `lumi-web-v2/src/api/moments/` powering the **moment** primitive — the operator-facing wrapper around a live AI agent run. A moment is "I want to watch this camera for {colour change | dial reading | etc.}, share the result with my team, and optionally page someone if a threshold is crossed." Hooks here cover moment CRUD, results retrieval, status transitions, the moments dashboard layout, and the alert subsystem (create alert / list alerts / stop alert).

This is the user-facing wrapper over [aiAgents](aiAgents.md) — the agent provides the inference, the moment provides the narrative. Image-only moments live in [imageMoments](imageMoments.md).

## The pattern, in a nutshell

```ts
// src/api/moments/useCreateMoment.tsx (paraphrased)
const useCreateMoment = () =>
  useConfiguredMutation<CreateMomentRequest, CreateMomentResponse>({
    getRequestConfig: (request) => ({
      url: gatewayRoutes.moments.createMoment,
      method: "POST",
      data: request
    }),
    errorCodeMap,
    getKeysToInvalidate: () => [`queryCacheKeys.momentsList`]
  });
```

Same canonical shape: `useConfiguredMutation` from `useRemoteData.ts`, route from `gatewayRoutes.moments.*`, types from `src/types/generated/`, mutations invalidate `momentsList` (and ``[queryCacheKeys.moment, id]`` for single-moment updates).

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useCreateMoment`, `useGetMoment`, `useGetMomentList`, `useUpdateMoment` | Core CRUD. |
| `useGetMomentResults` | Results stream snapshot for the moment page. |
| `useUpdateMomentStatus` | Transition the moment's lifecycle state. |
| `useExportMoment` | CSV/JSON export. |
| `useGetAgentsLayout`, `useUpdateAgentsLayout` | Pinboard layout for the moment dashboard. |
| `useCreateMomentAlert`, `useGetMomentAlert`, `useGetMomentAlerts`, `useStopMomentAlert` | Alert subscriptions on top of a moment — phone / push notifications when conditions trigger. |

## Backend mapping

Routes under `/v2/ai/moment/*`, served by the lumi-API gateway. Moments persist a record around an underlying AI agent run, so the data path is: the moment record holds metadata + alert config; agent results stream into shared AI storage (same backing as [aiAgents](aiAgents.md)) and `useGetMomentResults` reads the persisted view. Alert dispatch and phone delivery are out-of-band — see [user/useAddPhoneNumber](user.md) for the verification side. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/moments/` — 13 fixtures (`createMoment.ts`, `getMoments.ts`, `getMomentResults.ts`, `createAlert.ts`, `stopAlert.ts`, `getAgentsLayout.ts`, …).

## Tests

E2E specs cover moment creation and alert flow; no hook unit tests.

## See also

- [aiAgents](aiAgents.md) — the inference layer underneath
- [imageMoments](imageMoments.md) — static-image counterpart
- [notifications](notifications.md) — where alerts surface in the bell icon
- [monitors:custom](../../ai-continuous/monitors/custom.md) — runs the actual analysis
