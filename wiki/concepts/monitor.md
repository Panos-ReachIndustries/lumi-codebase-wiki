---
name: Monitor
description: A long-running Python process that consumes a camera stream, runs V2 AI modules, and publishes structured results to Kafka.
type: concept
tags: [concepts]
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/colour/colour.py }
  - { repo: Lumi-AI-Continuous, path: Docs/architecture/system_architecture.md }
---

# Monitor

A **monitor** is a long-running Python subprocess that receives a video stream from the lab, runs one or more AI analysis modules against each frame, and publishes structured results to a Kafka topic. Every AI capability in Lumi maps to exactly one monitor — there are 11 today (weighing, colour, liquid volume, hand detection, object tracking, 3D calc, text recognition, dial gauge, homogeneity, object list, anonymiser).

## What a monitor receives

Each monitor gets a config JSON at startup containing:

- `connection.resolution_h` / `connection.resolution_w` — the expected frame dimensions
- `ai.*` — monitor-specific parameters (e.g. `ai.boxes` for the colour monitor defines named rectangular regions of interest)
- `monitorId` and `pipeline` — identifiers used in published output

The video stream itself arrives via WebRTC, managed by the Monitor Relay (a Go service on EC2). The monitor opens the stream using `Common.common.StreamCapture` (or `LocalStreamCapture` in `--is_local` mode for testing against a local file).

## What a monitor does

Inside the processing loop, each monitor calls one or more **V2 modules** from the `Lumi-AI-Core` library. For example, `Lumi-AI-Continuous/monitors/colour/colour.py` (line 35) imports `Lumi-AI-Core.V2.Colours.ColourAnalyser` and runs it against each frame cropped to the configured boxes. Coordinates are normalised to the [0, 1] range before being passed to V2 modules.

All monitors use `Common.common.StreamReporter` (or a subclass like `ColourStreamReporter`) to format and publish results.

## What a monitor emits

Results are published to the `monitor-data-topic` Kafka topic (controlled by the `MONITOR_DATA_TOPIC` environment variable). Each message contains the `monitorId`, a timestamp, and a monitor-specific payload — for example, the colour monitor emits a `boxes` array, each entry containing `dominantColours` statistics.

Errors are published to `error-topic`.

## Lifecycle

Monitors are **spawned and managed by the Monitor Relay** (Go). The relay starts, stops, and restarts monitors based on commands from the arbiter or user. In local development, any monitor can be run standalone:

```
python colour.py --config ./configs/default.json --is_local
```

Passing `--is_local` disables Kafka publishing and enables local print output instead, making it easy to iterate without a full cluster.

## See also

- [arbiter](arbiter.md) — the component that consumes monitor output and tracks protocol state
- [custom-agent](custom-agent.md) — a configurable pipeline that chains multiple monitors/modules together
- `Lumi-AI-Continuous/monitors/colour/colour.py` — the simplest production monitor; read this first
