---
name: Week 1 Tour
description: After the day-1 spine, deepen across all three repos.
type: tour
tags: [onboarding, week-1, stub]
---

# Week 1 Tour

> **Stub.** This page is a placeholder. Ask Claude to flesh it out once the day-1 tour has been used by the first wave of new hires.

Outline:

- Day 2: pick one V2 module and read its tests + README front-to-back
- Day 3: read every monitor README in `Lumi-AI-Continuous/api/<monitor>/openapi.yaml`; you should be able to map each to a V2 module
- Day 4: clone all three repos and get them all running locally (web with mocks, continuous with `IS_LOCAL=true`, core via docker pytest)
- Day 5: shadow an arbiter execution end-to-end. Read `Lumi-AI-Continuous/protocol_arbiter_v2/arbiter_v2.py` and trace one instruction from receipt to status publish

By the end of week 1, you should be able to:

- Sketch the data flow on a whiteboard without notes
- Open a PR on any of the three repos and know which CI check will run first
- Name three V2 modules and where they're used
