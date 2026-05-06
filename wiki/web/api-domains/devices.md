---
name: web/api/devices
description: The TanStack Query hooks for device CRUD. The cleanest API domain in lumi-web-v2 — read this for the pattern.
type: api-domain
graph_node: web:api:devices
sources:
  - { repo: lumi-web-v2, path: src/api/devices }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
  - { repo: Lumi-AI-Continuous, path: monitor_relay }
tags: [web, exemplar]
---

# web/api/devices

Sixteen hooks under `lumi-web-v2/src/api/devices/`. They power the device list, the per-device page, the device-selection step inside experiment / workspace creation, and the live video manifest.

This is the cleanest domain to read first because:

- The naming is straightforward (`useGetDeviceList`, `useGetDevice`, `useGetVideoManifest`).
- It maps 1:1 to a single backend service: `monitor_relay`'s HTTP API.
- It uses the canonical `gatewayRoutes` lookup pattern that `CLAUDE.md` calls out as required.

## The pattern, in a nutshell

```ts
// src/api/devices/useGetDevice.tsx (paraphrased)
import { useQuery } from "@tanstack/react-query";
import { gatewayRoutes } from "@/consts/gatewayRoutes";
import type { Device } from "@/types/api";

export function useGetDevice(deviceId: string) {
  return useQuery<Device>({
    queryKey: ["device", deviceId],
    queryFn: () => fetch(gatewayRoutes.device.get(deviceId)).then(r => r.json()),
  });
}
```

Things to internalise:

1. Routes always come from `gatewayRoutes`. Never inline a URL string in a hook. (See `lumi-web-v2/CLAUDE.md`: "routes should always be imported from gatewayRoutes.ts rather than defined inline".)
2. Types come from `src/types/generated/` (Kubb-generated) when the OpenAPI spec covers them, or hand-rolled `src/types/api.ts` otherwise.
3. Query keys are arrays starting with the resource name. Mutations invalidate them.
4. Hooks return raw TanStack Query state — let the component handle loading / error UI.

## What lives in the folder

A representative slice:

| Hook | Purpose |
|------|---------|
| `useGetDeviceList` | Paginated device list. Used on `/device` and inside experiment device-selection. |
| `useGetDevice` | Single device by ID. Powers `(authenticated)/device/[deviceId]/page.tsx`. |
| `useGetVideoManifest` | Live video stream URLs for a device. Drives the live video viewer. |
| Mutations: `useUpdateDevice`, `useDeleteDevice`, … | Standard CRUD. Invalidate the list query on success. |

(Run `ls lumi-web-v2/src/api/devices/` for the full list.)

## Backend mapping

The `devices` domain talks to **`monitor_relay`** (Go service in Lumi-AI-Continuous), routed through the `lumi-API` gateway. So the call path is:

```
useGetDevice
  → gatewayRoutes.device.get(id)
  → HTTPS → lumi-API
  → monitor_relay handler.go
  → camera state / connection registry
```

That's why the graph has an edge from `web:api:devices` to `monitor_relay`. Toggle off the other repos in the graph view and you'll see the bridge clearly.

## Mocks

`mocks/` at the repo root has a mocks-server-lite instance. Switch with:

```bash
yarn use-env mocks
yarn dev
```

The mocks for the device domain are in `mocks/collections.ts` and `mocks/routes.ts`. Variant switching (success / error / empty) is handled by mocks-server-lite — check `mocks/server.ts` for the port and config.

## Tests

Component tests live next to the components that consume these hooks (e.g. `src/components/.../deviceCard.test.tsx`). Hooks themselves usually don't have unit tests because they're 90% TanStack Query plumbing — the value is in mock-server-backed integration tests under `test/`.

## See also

- [routes.md](../routes.md) — the device-related routes
- [Kubb pipeline](../kubb-pipeline.md) — how the `Device` type gets generated
- [monitor_relay](../../ai-continuous/monitor-relay.md) — the backend on the other side
