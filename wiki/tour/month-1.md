---
name: Month 1 Tour
description: Three milestones to go from understanding the system to contributing to it.
type: tour
tags: [tour]
---

# Month 1 Tour

Week 1 gave you the map. Month 1 is about making the map yours — by changing something real, reading the deeper design docs, and leaving the codebase slightly better than you found it.

There are three milestones. Take them in order.

---

## Milestone 1 — Own the full data flow (weeks 1–2)

The goal: be able to explain the path from camera frame to web UI without consulting any docs.

The path is: **LabEye camera → WebRTC → Monitor Relay (Go) → monitor subprocess → `monitor-data-topic` Kafka → Curator → `history_cache` → Historian → ledger → S3 → VIS Lab Core API → web viewer**.

Read `Lumi-AI-Continuous/Docs/architecture/system_architecture.md` and `Lumi-AI-Continuous/Docs/system_message_flow.md` back to back. Then read `Lumi-AI-Continuous/protocol_arbiter_v2/README.md` for the arbiter's role. Verify your understanding by drawing the flow from memory and checking it against the Mermaid diagrams.

You're done when you can answer: what happens to a frame between the camera and the `monitor-data-topic` message, and what happens between that message and a status update on the web?

---

## Milestone 2 — Make a real change (weeks 2–3)

The goal: ship a small, tested change to either a monitor or a V2 module.

Good starting points:
- Add a new config parameter to an existing monitor (e.g. a threshold in `Lumi-AI-Continuous/monitors/colour/colour.py`) and update its config validation.
- Improve a V2 module's output schema in `Lumi-AI-Core/V2/` and update the corresponding monitor to use it.
- Add a test case to `Lumi-AI-Continuous/protocol_arbiter_v2/Testing/` for an edge case in ledger event handling.

Before you start, run the existing tests (`pytest` in the relevant directory). Make your change. Run tests again. Open a PR.

The goal isn't to fix a hard bug on day 15 — it's to get comfortable with the repo structure, CI, and review process.

---

## Milestone 3 — Add a wiki page (week 4)

The goal: identify something you had to work hard to understand, and write it up so the next person doesn't.

Good candidates: a V2 module that lacks a wiki page in `wiki/ai-core/modules/`, a web API domain that's missing detail in `wiki/web/api-domains/`, or a how-to guide for a local dev workflow you had to figure out.

Write the page using the frontmatter format in `lumi-codebase-wiki/CLAUDE.md`. Cross-link it from related pages. Append a line to `wiki/log.md`.

This matters beyond onboarding: the wiki is a compounding artifact. Every engineer who adds one page makes the next hire's month shorter.

---

By the end of month 1, you should be able to take a bug report against any of the three repos and know immediately which component to look at first.
