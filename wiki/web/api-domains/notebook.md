---
name: web/api/notebook
description: One hook — checks whether a user-supplied notebook reference (REF-001 etc.) is unique within the org.
type: api-domain
graph_node: web:api:notebook
sources:
  - { repo: lumi-web-v2, path: src/api/notebook }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/notebook

A single-hook domain. `lumi-web-v2/src/api/notebook/useCheckRefUniqueness.tsx` exposes one mutation — given a reference string the user is typing into a notebook entry (e.g. `EXP-2024-017`, `PROT-A`, `WS-Hep-3`), the backend returns whether the ref is already in use. The hook is consumed by the create-experiment / create-workspace / create-protocol forms to give the user inline "name taken" feedback before they submit.

This is deliberately a tiny domain because notebook references span multiple resource types (experiments, workspaces, protocols, records) — putting one shared validator behind `/v2/lab/check-ref-uniqueness` keeps the rule in one place.

## The pattern, in a nutshell

```ts
// src/api/notebook/useCheckRefUniqueness.tsx (paraphrased)
const useCheckRefUniqueness = () =>
  useConfiguredMutation<GetV2LabCheckRefUniquenessQueryParams, ...>({
    getRequestConfig: (request) => ({
      url: gatewayRoutes.notebook.checkRefUniqueness,
      method: "GET",
      params: request
    }),
    errorCodeMap
  });
```

A small oddity: it's a `useConfiguredMutation` despite being a GET. That's deliberate — the form wants to fire-and-await per keystroke (debounced) rather than maintain a query cache, so mutation semantics fit better than `useQuery`.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useCheckRefUniqueness` | The one and only — debounced ref-uniqueness check on the create-X forms. |

## Backend mapping

Single route: `/v2/lab/check-ref-uniqueness`. The lab-API checks against the org's notebook entries (across experiments, workspaces, protocols, records) and returns `{ isUnique: boolean }`. Backend: lumi-API gateway; specific service unclear from frontend code alone — likely the same lab service that owns [projects](projects.md) and [experiments](experiments.md).

## Mocks

`lumi-web-v2/mocks/routes/notebook/checkRefUniqueness.ts`.

## Tests

Behaviour is covered indirectly via the create-form E2E specs.

## See also

- [experiments](experiments.md), [workspaces](workspaces.md), [protocols](protocols.md), [records](records.md) — the four consumers
- [devices](devices.md) — pattern reference
