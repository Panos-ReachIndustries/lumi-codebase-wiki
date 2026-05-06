---
name: Glossary
description: Domain jargon for new hires. If you hear a term in standup that's not on this list, add it.
type: glossary
tags: [reference]
---

# Glossary

## Domain (what the science people say)

- **Protocol** — The recipe for an experiment. A sequence of *instructions* (v2) or nested *stages → steps → actions* (v1). Lives in `lumi-web-v2/src/app/(authenticated)/protocol*/` and is interpreted by the arbiter.
- **Instruction** — In v2 arbiters, the atomic unit of a protocol. Has a numeric ID; sparse and ordered. Replaces v1's stage/step/action hierarchy.
- **Stage / Step / Action** — V1 protocol hierarchy. Three nested levels. Mostly historical now; v2 flattens it.
- **Predicate** — A boolean check evaluated by the arbiter against the world model (e.g. "is the vessel filled?", "is the gauge ≥ 50?"). Used to decide if an instruction is satisfied.
- **Ledger** — The append-only record of an experiment run. Captured for audit / playback. Sample ledger files live in `Lumi-AI-Continuous/ledgers/`.
- **Moment** — A point-in-time observation by the operator (an image, a note, a measurement). The web app has dedicated routes for these.

## Components (what the engineering people say)

- **Monitor** — A long-running Python process that consumes a video stream and publishes structured AI results. One monitor per AI capability. See `Lumi-AI-Continuous/monitors/`.
- **Arbiter** — The protocol orchestrator. Consumes monitor data, evaluates predicates, decides protocol progression. Three coexisting versions: v1, v2, v3.
- **Monitor relay** — The Go service that handles WebRTC ingress, spawns monitors, and relays their stdout to Kafka. Also exposes an HTTP API for device CRUD.
- **Custom agent** — A configurable monitor (`monitors/custom/custom_agent.py`) that composes arbitrary V2 modules via JSON. The web app's `aiAgents` API domain talks to this.
- **V2 module** — A class library under `Lumi-AI-Core/V2/`. There are 37 of them. Each has its own README.
- **Gateway** — The HTTPS + WebSocket bridge between Kafka-side and the web app. Lives in a separate `lumi-API` repo.
- **Kubb** — TypeScript codegen tool. Reads the gateway's OpenAPI spec, emits typed hooks in `lumi-web-v2/src/types/generated/`.

## Infrastructure

- **MSK / Kafka** — AWS Managed Streaming for Kafka. The bus everything backend talks over. Locally bypassed via `IS_LOCAL=true`.
- **LabEye** — The lab camera hardware that streams over WebRTC into `monitor_relay`.
- **GStreamer** — The pipeline `monitor_relay` uses to decode WebRTC and pipe frames into Python monitors.
- **TanStack Query** — The web app's server-state library. Every API hook in `lumi-web-v2/src/api/` uses it.
- **shadcn/ui** — The base UI component library (`lumi-web-v2/src/components/ui/`).

## Conventions

- **`*_TOPIC`** — Convention for environment variables that name Kafka topics. The graph generator detects every match of this pattern.
- **`IS_LOCAL=true`** — Local-dev flag in Lumi-AI-Continuous. Bypasses Kafka and AWS; monitors print to stdout.
- **`mocks`** — Local mock server in lumi-web-v2 that mimics the gateway. Switch with `yarn use-env mocks`.
