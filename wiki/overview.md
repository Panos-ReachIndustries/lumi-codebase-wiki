---
name: Welcome to Lumi
description: 5-minute orientation for new engineers — what Lumi is, the three repos, and the path data takes through them.
type: overview
tags: [onboarding, start-here]
---

# Welcome to Lumi

Lumi is a **distributed AI monitoring platform for laboratory experiments**. Cameras watch the bench. AI monitors interpret the video — what's in each vessel, what colour it is, what the gauge reads, what the operator's hands are doing. A *protocol arbiter* tracks experiment progress against a defined protocol. A web app lets scientists set protocols up, run them, and review the results.

Three repos do the work:

| Repo | What it is | Language |
|------|------------|----------|
| **Lumi-AI-Continuous** | The monitoring backend: ~11 AI monitors, 3 protocol arbiters (v1/v2/v3), the Go `monitor_relay` that bridges WebRTC cameras to monitor processes, Kafka glue. | Python + Go |
| **Lumi-AI-Core** | The CV/ML class libraries — 37 V2 modules (Detection, Tracking, Vessels, Gestures, Vortexing, …) imported by monitors and the custom agent. | Python |
| **lumi-web-v2** | The Next.js 15 web app — experiment UI, device management, live video viewer, protocol editor. | TypeScript / React |

## The path data takes

Read this paragraph twice; it's the spine of the system.

1. A camera (LabEye) streams video over WebRTC.
2. The Go **monitor_relay** picks up the stream, spawns a Python **monitor** process per AI capability, and pipes frames into it.
3. The monitor (e.g. `monitors/colour`) loads one or more **V2 modules** from Lumi-AI-Core (`V2/Colours`, `V2/Detection`, …) and produces structured results.
4. The monitor publishes to Kafka topic `MONITOR_DATA_TOPIC`.
5. The **protocol_arbiter** (currently v2 in production, v1 still running, v3 in design) consumes that topic, evaluates the active protocol's instructions, and publishes status to `PROTOCOL_ARBITER_STATUS_TOPIC`.
6. The **lumi-web-v2** app subscribes (via the gateway) to that status topic and renders the live experiment view.

That's the whole loop. Everything else — Kubb codegen, custom agents, ledger storage, Storybook, the 16 API domains, the 37 V2 modules — sits around this spine.

## What to do next

- Open the [graph view](../app/graph.html) and click `repo:continuous`, then `monitors:colour`. Walk an edge to `core:Colours`. Notice the dashed Kafka edges.
- Read the [Day 1 tour](tour/day-1.md) for a concrete first-day reading list.
- Skim the [glossary](glossary.md) so the jargon (protocol, arbiter, ledger, instruction, custom agent) makes sense before you dive in.

## How this wiki is maintained

This wiki is **LLM-maintained** in the spirit of [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). You don't need to keep it in sync — Claude does. If you find a gap, just ask Claude to fix it, and the change will land here. See [`CLAUDE.md`](../CLAUDE.md) for the page conventions.
