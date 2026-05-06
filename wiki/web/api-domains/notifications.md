---
name: web/api/notifications
description: In-app notifications — list, unread count, mark single / mark all as read.
type: api-domain
graph_node: web:api:notifications
sources:
  - { repo: lumi-web-v2, path: src/api/notifications }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/notifications

Four hooks under `lumi-web-v2/src/api/notifications/` powering the bell-icon in the topbar and the `(authenticated)/notifications-dashboard` page. They list dashboard notifications (mentions, alert triggers, share invites), expose an unread badge, and let the user mark one or all as read. This is a thin domain — the heavy lifting (delivery, ordering, dedupe) happens server-side; the frontend is just CRUD over a notification feed.

## The pattern, in a nutshell

```ts
// src/api/notifications/useGetNotifications.tsx (paraphrased)
const useGetNotifications = (params, opts) =>
  useConfiguredQuery<DashboardNotificationResponse>({
    getRequestConfig: () => ({
      url: gatewayRoutes.notification.getNotifications,
      params
    }),
    queryOptions: {
      enabled: opts?.enabled ?? true,
      queryKey: [queryCacheKeys.notificationsList]
    }
  });
```

Standard `useConfiguredQuery`. Mutations (`useMarkAsRead`, `useMarkAllAsRead`) invalidate the list cache so the unread badge re-decrements without a full refetch round-trip.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useGetNotifications` | Paginated feed for the bell dropdown and the dashboard page. |
| `useGetUnreadCount` | Lightweight badge endpoint — polled. |
| `useMarkAsRead` | Marks a single notification read. |
| `useMarkAllAsRead` | Bulk clear. |

## Backend mapping

Routes under `/v2/notification/dashboard/*`. The dashboard service aggregates push events from across the system — moment alerts (see [moments](moments.md)), share invites (see [organisation](organisation.md)), comment mentions on experiments / workspaces, system messages — and persists a per-user feed. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/notifications/` — `getNotifications.ts`, `getUnreadCount.ts`, `markAsRead.ts`, `markAllAsRead.ts`.

## Tests

Smoke-tested through the topbar component test and the notifications-dashboard E2E spec.

## See also

- [moments](moments.md) — biggest source of alert-type notifications
- [organisation](organisation.md) — invite notifications
- [user](user.md) — phone / contact-detail config that influences delivery
- [devices](devices.md) — pattern reference
