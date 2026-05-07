---
name: Week 1 Tour
description: A day-by-day reading list to go from zero to understanding the full Lumi data flow.
type: tour
tags: [tour]
---

# Week 1 Tour

By the end of this week you should be able to sketch the full data path — camera frame to Kafka to web UI — on a whiteboard without notes. Each day has a concrete checklist. Start with `wiki/overview.md` if you haven't already.

---

## Monday — System orientation

- [ ] Read `Lumi-AI-Continuous/Docs/architecture/system_architecture.md` end to end (the Mermaid diagrams are the most important part)
- [ ] Read `Lumi-AI-Continuous/Docs/kafka-topics.md` — know what `monitor-data-topic`, `protocol-arbiter-commands`, and `protocol-arbiter-status` carry
- [ ] Read `Lumi-AI-Continuous/Docs/system-overview.md`
- [ ] Read `wiki/concepts/monitor.md`, `wiki/concepts/arbiter.md`, `wiki/concepts/protocol.md` in this wiki
- [ ] Sketch on paper: camera → relay → monitor → Kafka → arbiter → web

---

## Tuesday — Monitors in practice

- [ ] Read `Lumi-AI-Continuous/monitors/colour/colour.py` (first 80 lines) — this is the simplest production monitor
- [ ] Read `wiki/ai-continuous/monitors/colour.md` in this wiki
- [ ] Read `wiki/ai-core/modules/Detection.md` — the most-used V2 module
- [ ] Browse `Lumi-AI-Continuous/monitors/` to see the full list; match each folder to a V2 module in `Lumi-AI-Core/V2/`
- [ ] Run one monitor locally: `python colour.py --config ./configs/default.json --is_local` (uses a local video file, no Kafka needed)

---

## Wednesday — Protocol and arbiter V2 flow

- [ ] Read `Lumi-AI-Continuous/protocol_arbiter_v2/README.md` — understand the V1 vs V2 distinction
- [ ] Read `wiki/concepts/protocol.md` and `wiki/concepts/ledger.md` in this wiki
- [ ] Open `Lumi-AI-Continuous/protocol_arbiter_v2/arbiter_v2.py` and trace one instruction from a Kafka `protocol-arbiter-commands` message through to a `protocol-arbiter-status` publish
- [ ] Read `Lumi-AI-Continuous/protocol_arbiter_v2/historian_v2.py` — understand `LedgerEventV2` and how it gets written
- [ ] Open `Lumi-AI-Continuous/protocol_arbiter_v2/state.py` — understand `ProtocolStateV2`

---

## Thursday — Web routes

- [ ] Read `wiki/web/routes.md` for a map of the Next.js route tree
- [ ] Open `lumi-web-v2/src/app/(authenticated)/experiment/` — read what the `[experimentId]/live/` route does
- [ ] Open `lumi-web-v2/src/app/(authenticated)/moment/` — understand what a "moment" is and when the web creates one
- [ ] Read `wiki/web/api-domains/experiments.md` and `wiki/web/api-domains/moments.md`
- [ ] Trace a user command: web button click → `protocol-arbiter-commands` Kafka message → arbiter handles it → `protocol-arbiter-status` publish → web updates

---

## Friday — Explore and contribute

- [ ] Open this wiki's graph viewer (`app/index.html`) and navigate from a monitor node to its V2 module
- [ ] Ask one real question about the system in the chat panel — something you couldn't answer from the docs alone
- [ ] If you found something missing or wrong in the wiki, update the relevant page (this is encouraged, not optional)
- [ ] Read `wiki/concepts/custom-agent.md` — stretch goal: find where the relay spawns the custom agent subprocess in `Lumi-AI-Continuous/Docs/system_message_flow.md`

---

## End-of-week checkpoint

You're ready for Week 2 if you can:
- Name all 11 monitors and the V2 module(s) each uses
- Explain the difference between a V1 and V2 protocol in one sentence
- Describe what the historian writes to S3 and why
