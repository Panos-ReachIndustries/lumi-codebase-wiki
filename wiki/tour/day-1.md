---
name: Day 1 Tour
description: A concrete reading list for your first day. About 90 minutes of reading + 30 of clicking around.
type: tour
tags: [onboarding, day-1]
---

# Day 1 Tour

Goal by end of day: you can describe **the path data takes from camera to web** in one sentence, and you know which repo to open for any given question.

## Block 1 — The 30,000ft view (15 min)

- [ ] Read [overview.md](../overview.md). Twice if it's your first day.
- [ ] Open the [graph view](../../app/graph.html). Toggle off everything except `repo` and `monitor` nodes. Note the three repo anchors and the 11 monitors clustered around `Lumi-AI-Continuous`.
- [ ] Read [system-overview.md](../architecture/system-overview.md), specifically the ASCII diagram. You don't need to memorise the topic names yet — just remember "video → monitor → topic → arbiter → web".

## Block 2 — Walk one path end-to-end (45 min)

We'll trace a single monitor (`colour`) from frame to web. This is the smallest example that touches every layer.

- [ ] Open the graph. Click `monitors:colour`. Read the side panel (the monitor's wiki page). Note its imports of V2 modules.
- [ ] Open `Lumi-AI-Continuous/monitors/colour/colour.py` in your editor. Skim it. Look for the `MONITOR_DATA_TOPIC` env var.
- [ ] Click `core:Colours` in the graph. Read its README via the side panel.
- [ ] Open `Lumi-AI-Core/V2/Colours/ColourAnalyser.py`. You don't need to understand the algorithm — just confirm it's a class with a public method that takes a frame.
- [ ] Click `topic:MONITOR_DATA_TOPIC` (amber square). Read [kafka-topics.md](../architecture/kafka-topics.md).
- [ ] Click `arbiter:v2`. Read its wiki page. Open `Lumi-AI-Continuous/protocol_arbiter_v2/arbiter_v2.py`. Look for where it consumes `MONITOR_DATA_TOPIC`.
- [ ] Click `web:route:experiment`. The web side of the loop is `(authenticated)/experiment/[experimentId]/live/page.tsx`.

You've now seen all four layers in <1 hour.

## Block 3 — Get something running (30 min)

- [ ] Pick **one** of the three repos to clone-and-run. Recommended for day 1:
  - **Easiest:** lumi-web-v2 with mocks. `yarn install && yarn use-env mocks && yarn dev`.
  - **Most educational:** Lumi-AI-Continuous in `IS_LOCAL=true` mode. Kafka bypassed; one monitor reads a video file. See `Lumi-AI-Continuous/run_dev.py`.
- [ ] Whichever you picked, get it to `Hello World`. You will hit at least one missing env var. That's normal.

## Block 4 — Scan the surface area (20 min)

- [ ] Skim the [glossary](../glossary.md) — top to bottom, no need to memorise.
- [ ] Skim `Lumi-AI-Continuous/README.md` and `lumi-web-v2/CLAUDE.md`.
- [ ] In the graph, toggle on **all** node types and zoom out. Take a screenshot for yourself. This is the surface area of what you'll come to know.

## Done?

Pick one of:

- [ ] Continue with [week-1.md](week-1.md) tomorrow.
- [ ] Pair with someone for an hour. Ask them: "What's the single thing about this codebase that surprised you in your first month?"

If you got stuck on anything, that's a wiki gap — tell Claude and it'll be fixed for the next person.
