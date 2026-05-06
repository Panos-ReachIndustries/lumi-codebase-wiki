---
name: Monitor
description: A long-running process that consumes a video stream and publishes structured AI results.
type: concept
tags: [domain, stub]
---

# Monitor

A **monitor** is a long-running Python process that consumes a video stream and continuously publishes structured AI results to Kafka.

One monitor per AI capability. There are 11 today (see `Lumi-AI-Continuous/monitors/`).

Each monitor:

1. Takes a config JSON (regions of interest, model paths, thresholds).
2. Subclasses `Common.common.StreamReporter` for output and `Common.common.StreamCapture` for input.
3. Imports one or more V2 modules from Lumi-AI-Core.
4. Publishes to `MONITOR_DATA_TOPIC`.

Spawned by `monitor_relay` (Go service). In `IS_LOCAL=true` mode, can be run standalone against a video file.

## See also

- [colour monitor](../ai-continuous/monitors/colour.md) — exemplar
- [monitor_relay](../ai-continuous/monitor-relay.md)
- [kafka-topics](../architecture/kafka-topics.md)
