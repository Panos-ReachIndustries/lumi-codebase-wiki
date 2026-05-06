---
name: Mocks
description: Local mocks-server-lite instance that mirrors the lumi-API gateway for offline frontend development.
type: architecture
tags: [web, mocks]
---

# Mocks

`lumi-web-v2/mocks/` runs a [mocks-server-lite](https://www.npmjs.com/package/mocks-server-lite) instance that stands in for the `lumi-API` gateway during local frontend development and Playwright E2E runs. With it, you can boot the web app with no backend dependencies and exercise specific scenarios — empty states, errors, multi-org users, paused experiments — without poking the dev cluster.

## Boot

`mocks/server.ts` calls `createServer({ routes, collections, webSockets, staticPaths }, { delay: 1000, port: 3100, defaultRouteVariantName: "success" })` — so the default port is **3100** and every endpoint adds **1000ms of latency** so loading states are visible while developing. The selected collection comes from `process.env.SELECTED_MOCKS_COLLECTION` (falls back to `"base"`), and `MSL_SKIP_SELECTION_PROMPT=true` skips the interactive picker for CI runs.

Two scripts wire it up:

- `yarn mocks` — spins up the mock server (`npx tsx mocks/server.ts`) on :3100.
- `yarn use-env mocks` — concatenates `.env.local.common` with `.env.local.mocks` into `.env.local`, pointing `NEXT_PUBLIC_GATEWAY_API_URL` at the mock. `yarn use-env dev` flips it back to the real dev gateway. The script lives in `lumi-web-v2/scripts/build-env.ts`.

So a typical local session is `yarn use-env mocks` → `yarn mocks` (in one terminal) → `yarn dev` (in another).

## Collections, routes, variants

`mocks/routes/index.ts` aggregates ~80 route files, organised by API domain (`mocks/routes/devices/`, `mocks/routes/experiments/`, `mocks/routes/aiAgents/`, etc. — same layout as `src/api/`). Every endpoint gets at least a `success` variant and usually some combination of `error`, `empty`, `pending`, `done`, `not-found`, etc. — see for example `experiment-get-experiment:pending` and `experiment-get-experiment:done` in `mocks/collections.ts`.

`mocks/collections.ts` then composes named scenarios out of those variants. A collection inherits from `base` via `useBaseRouteVariants: true`, then opts out of specific successes (`without: [...]`) and substitutes in alternative variants (`routes: [...]`). Examples in the file: `pending-experiment`, `done-workspace`, `invalid-login-details`, `phone-number-unverified`, `multiple-organisations`, `empty-vessel-mask`. Pick a collection at boot via `SELECTED_MOCKS_COLLECTION=<id> yarn mocks`, or switch mid-test via the `setMockCollection` Playwright helper.

## WebSocket mocks

`mocks/webSockets.ts` registers two handlers: a deprecated `protocol-convert` (sends a `processing` then `complete` payload to drive the v1 protocol upload flow) and the unified `messages` socket that the rest of the app subscribes to. Server-pushed scenarios for the `messages` socket are scripted under `mocks/ws-routines/` and triggered manually via `scripts/trigger-ws-message.ts` / `trigger-ws-routine.ts`.

## Static assets

`mocks/staticPaths.ts` mounts `mocks/public/` at `/web` on the mock server (so URLs like `http://localhost:3100/web/<file>`). `mocks/remoteSources.ts` collects external public assets — currently a list of S3-hosted sample MP4s used as stand-in device archive footage.

## When to add a mock vs hit the dev gateway

Add a mock whenever you need a deterministic scenario for development or an E2E test. The instructions in `lumi-web-v2/docs/mocks.md` are: (1) add the route to `src/consts/gatewayRoutes.ts`, (2) create a route file under `mocks/routes/<domain>/` with at least a `success` variant validated against the generated types, (3) export it from `mocks/routes/index.ts`, (4) wire collections in `mocks/collections.ts`. If you only need a one-off check against real data, run `yarn use-env dev` and hit the dev gateway directly.

## See also

- `lumi-web-v2/docs/mocks.md` — the canonical how-to (don't paraphrase, link)
- [routes.md](routes.md) — every route ultimately hits one of these mocks in dev
- [api-domains/](api-domains/) — the hooks the mocks replace
