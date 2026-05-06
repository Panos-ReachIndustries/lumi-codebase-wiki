---
name: System Overview
description: Cross-repo data flow from camera to web — the spine of the Lumi platform.
type: architecture
tags: [architecture, data-flow, kafka]
---

# System Overview

Lumi is three repos held together by **Kafka topics** and a **gateway HTTP/WS API**. Once you internalise the path data takes, the rest is just naming.

## Diagram (logical)

```
                                  ┌─────────────────────────────┐
                                  │  Camera (LabEye, WebRTC)    │
                                  └──────────────┬──────────────┘
                                                 │ video
                                                 ▼
                              ┌──────────────────────────────────────┐
                              │  monitor_relay  (Go, Lumi-AI-Cont.) │
                              │  - WebRTC ingress                    │
                              │  - GStreamer pipeline                │
                              │  - Spawns + supervises monitors      │
                              └──────────┬───────────────────────────┘
                                         │ stdin frames / stdout JSON
                                         ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  monitors/*  (Python)                                           │
   │  colour, dial, hands, liquids, object, text, custom, ...        │
   │  each imports modules from Lumi-AI-Core/V2/                     │
   └──────────┬─────────────────────────────────────┬────────────────┘
              │ MONITOR_DATA_TOPIC                  │ AI_AGENT_RESULTS_TOPIC
              ▼                                     ▼
   ┌──────────────────────────┐         ┌────────────────────────┐
   │  protocol_arbiter (v2)   │         │  custom-agent listeners │
   │  (v1 running, v3 design) │         └────────────┬────────────┘
   └──────────┬───────────────┘                      │
              │ PROTOCOL_ARBITER_STATUS_TOPIC        │
              │ PROTOCOL_ARBITER_HISTORY_TOPIC       │
              ▼                                     │
   ┌──────────────────────────────────────────────────────────────┐
   │  lumi-API gateway (separate repo, not cloned locally)        │
   │  - REST + WebSocket bridge between Kafka and web             │
   └──────────┬───────────────────────────────────────────────────┘
              │ HTTPS + WSS
              ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  lumi-web-v2  (Next.js 15)                                   │
   │  - 38 routes, 16 API domains, TanStack Query + Kubb codegen  │
   └──────────────────────────────────────────────────────────────┘
```

## Component map

### Lumi-AI-Continuous

| Folder | Role |
|--------|------|
| `monitor_relay/` | Go service. The bridge between cameras (WebRTC) and monitor processes (stdio). Also handles device CRUD over HTTP (used by the web app's `device-selection` flow). |
| `monitors/<name>/` | One folder per AI capability. Each is an independent Python process that consumes frames and publishes to `MONITOR_DATA_TOPIC`. See [Monitors](../ai-continuous/README.md). |
| `protocol_arbiter*/` | Three side-by-side arbiter implementations. v1 = nested stage/step/action. v2 = flat instruction-IDs (current default). v3 = pure state-machine domain layer (in progress; see `Lumi-AI-Continuous/Docs/`). |
| `Common/` | Shared Python utilities: stream reporters, Kafka pool, resilience, profiling. Imported by every monitor. |
| `api/<monitor>/openapi.yaml` | The contract for each monitor's input/output. Useful when wiring a new consumer. |

### Lumi-AI-Core

37 modules under `V2/`. Three families to know on day 1:

- **Infrastructure** — `Utils`, `BasicOps`, `ModelInference`. Used everywhere.
- **Vision primitives** — `Detection`, `Tracking`, `SegmentAnything`. Building blocks for higher-level tasks.
- **Task-specific** — `Vessels`, `Pipetting`, `LabContainerTracking`, `Vortexing`, `Weighing`, `WellPlate`. The lab-specific logic.

The contract between modules is documented in [`Lumi-AI-Core/agreedDataSchema.md`](../../../Lumi-AI-Core/agreedDataSchema.md).

### lumi-web-v2

| Layer | Where | Notes |
|-------|-------|-------|
| Routes | `src/app/(authenticated)/`, `src/app/(public)/` | 38 routes total. Grouped in the graph by top-level segment (devices, experiments, protocols, …). |
| API hooks | `src/api/<domain>/` | 16 domains. ~178 hooks. All TanStack Query. Routes resolved via `src/consts/gatewayRoutes.ts`. |
| Type generation | `kubb.config.ts` | Reads `../lumi-API/src/output/full-api.yml`, emits `src/types/generated/`. The 4th repo lumi-API is **not cloned locally** — it shows up in the graph as `repo:lumi-api` (greyed-out). |
| UI library | `src/components/ui/` | shadcn/ui-derived. Tailwind v4. Storybook on `:6006`. |

## The two gateways you'll meet

1. **Kafka** — the backbone between monitors and arbiters and the Python ↔ Go boundary inside Lumi-AI-Continuous. See [kafka-topics.md](kafka-topics.md).
2. **lumi-API** — the HTTPS + WSS gateway between the Kafka-side and the web app. The web repo never speaks Kafka directly.

## Where the bodies are buried

- `lumi-API` is referenced (Kubb reads from it) but lives in a separate repo we haven't cloned here. If your wiki link points to "lumi-API" and 404s, that's expected.
- The **submodule placeholder** `Lumi-AI-Continuous/Lumi-AI-Core/` is intentionally **empty**; the real Lumi-AI-Core is cloned as a sibling. Don't `git submodule update` unless you want to re-pin.
- `protocol_arbiter_v3` ships only the **domain** layer right now — no Kafka, no lifecycle. Read it as a reference for where v2 is heading, not as something to run.

## Read next

- [Kafka topics](kafka-topics.md) — every topic, who produces, who consumes
- [Day 1 tour](../tour/day-1.md) — the concrete reading order for your first day
- [Glossary](../glossary.md) — domain jargon
