---
name: Web Routes
description: All 38 routes in lumi-web-v2, grouped by feature area.
type: route-group
tags: [web]
---

# Web Routes

`lumi-web-v2` has 38 routes total: 31 authenticated, 7 public. Routes are file-based via Next.js App Router, organised under `src/app/(authenticated)/` and `src/app/(public)/`.

For graph legibility, the graph collapses these 38 routes into 16 **route groups** keyed off the top-level segment.

## Authenticated routes

### overview
`(authenticated)/overview/page.tsx` — top-level dashboard.

### lab-ops
`(authenticated)/lab-ops/page.tsx` — lab operations dashboard.

### notifications-dashboard
`(authenticated)/notifications-dashboard/page.tsx`.

### notebook
`(authenticated)/notebook/page.tsx` — operator notebook.

### organisation
`(authenticated)/organisation/page.tsx` — org settings.

### profile
`(authenticated)/profile/page.tsx`.

### assist
`(authenticated)/assist/page.tsx` — assistant / AI helper.

### project
- `(authenticated)/project/new/page.tsx`
- `(authenticated)/project/[projectId]/page.tsx`

### experiment
- `(authenticated)/experiment/new/page.tsx`
- `(authenticated)/experiment/[experimentId]/page.tsx`
- `(authenticated)/experiment/[experimentId]/live/page.tsx`
- `(authenticated)/experiment/[experimentId]/device-selection/page.tsx`

The `live` route is the one wired to `PROTOCOL_ARBITER_STATUS_TOPIC` via the gateway.

### workspace
- `(authenticated)/workspace/new/page.tsx`
- `(authenticated)/workspace/[workspaceId]/page.tsx`
- `(authenticated)/workspace/[workspaceId]/live/page.tsx`
- `(authenticated)/workspace/[workspaceId]/device-selection/page.tsx`

### record
- `(authenticated)/record/new/page.tsx`
- `(authenticated)/record/[recordId]/page.tsx`

### device
`(authenticated)/device/[deviceId]/page.tsx`. Talks to `monitor_relay` via the `devices` API domain.

### protocol
- `(authenticated)/protocol/new/page.tsx`
- `(authenticated)/protocol/[protocolId]/page.tsx`
- `(authenticated)/protocol/v2/new/page.tsx`
- `(authenticated)/protocol/v2/[protocolId]/page.tsx`
- `(authenticated)/protocol/v2/selectAndPreview/page.tsx`

### protocol-version
`(authenticated)/protocol-version/[versionId]/page.tsx`.

### moment
- `(authenticated)/moment/new/page.tsx`
- `(authenticated)/moment/[momentType]/[momentId]/page.tsx`
- `(authenticated)/moment/image/new/page.tsx`
- `(authenticated)/moment/image/[imageAiAgentType]/[imageMomentId]/page.tsx`

## Public routes

### public
- `/page.tsx` (root)
- `/login/page.tsx`
- `/login/reset/page.tsx`
- `/accept-invite/page.tsx`
- `/create-starter-org/page.tsx`
- `/create-pro-org/page.tsx`
- `/stream/page.tsx`

## See also

- [api/devices](api-domains/devices.md) — exemplar API domain
- [Kubb pipeline](kubb-pipeline.md) — how route hooks get their types
