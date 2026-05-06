---
name: monitor_relay
description: "Go service that bridges LabEye cameras (WebRTC) to Python monitor processes (UDP/GStreamer) and Kafka."
type: service
graph_node: monitor_relay
sources:
  - { repo: Lumi-AI-Continuous, path: monitor_relay/cmd/monitor_relay/main.go }
  - { repo: Lumi-AI-Continuous, path: monitor_relay/handler.go }
  - { repo: Lumi-AI-Continuous, path: monitor_relay/monitor.go }
  - { repo: Lumi-AI-Continuous, path: monitor_relay/msk.go }
  - { repo: Lumi-AI-Continuous, path: monitor_relay/types.go }
tags: [service, go, video, kafka]
---

# monitor_relay

`monitor_relay` is the Go service that lives between LabEye cameras and the Python AI world. One relay process runs per AWS EC2 relay instance; it accepts a WebRTC video stream from a camera, forwards the H.264 frames into a local UDP port, spawns the Python monitor (or arbiter) subprocess that opens that UDP port via GStreamer, and republishes the monitor's structured `DATA:` lines onto Kafka. Everything between "camera connects" and "monitor process emits results" is the relay's job.

## What it is

```
LabEye camera ──WebRTC──▶ monitor_relay ──UDP/GStreamer──▶ Python monitor
                              │                                 │
                              ▼                                 │ stdout
                         HTTP API (Echo)                        │
                              │                                 ▼
                         Kafka (MSK)  ◀────── parsed DATA / ERROR / METRICS
```

Source-of-truth for the diagram: `Lumi-AI-Continuous/monitor_relay/README.md` and `monitor_relay/monitor.go`.

The entry point is `Lumi-AI-Continuous/monitor_relay/cmd/monitor_relay/main.go`. It boots an [Echo](https://echo.labstack.com) HTTP server on `:8080`, creates the MSK Kafka writer (`monitor_relay/msk.go:10`), wires up the AI-agent service (`aiagents/core/`), and registers route groups for `/monitors`, `/ai-agents`, `/arbiters`. An idle-shutdown goroutine (`handler.go:259`) tears the relay down after `MONITOR_IDLE_SHUTDOWN_DURATION` of zero monitors.

## The HTTP handler API used by the web app's `devices` domain

`monitor_relay/handler.go` defines the CRUD surface. The web app's `devices` routes hit these endpoints:

| Method | Path | Handler | Purpose |
|--------|------|---------|---------|
| `GET`    | `/monitors`        | `GetMonitors` (`handler.go:112`) | Sorted list of active monitors. |
| `POST`   | `/monitors`        | `CreateMonitor` (`handler.go:137`) | Spawn a new monitor subprocess. Body: `CreateMonitorRequest` (`types.go:5`) — `monitorId`, `type`, `deviceId`, `args`. |
| `DELETE` | `/monitors/:id`    | `ShutdownMonitor` (`handler.go:181`) | Begin shutdown; returns `202` because cleanup is async. |
| `GET`    | `/monitors/:id`    | `GetMonitor` (`handler.go:205`) | Status of a single monitor. |
| `GET`    | `/status`          | `GetStatus` (`handler.go:225`) | Remaining capacity and active counts. |
| `GET`    | `/keepawake`       | `KeepAwake` (`handler.go:249`) | Bumps the idle timer so the relay isn't reaped while a long task is queued. |
| `GET`    | `/healthcheck`     | (inline) | Trivial liveness probe. |

Capacity is summed per-`MonitorType` via `GetMonitorTypeCapactity` (`monitor.go:55`). `Colour` costs 3, `LiquidDescription` costs 9, `Text` and `Dial` cost 12, etc., against the `MONITOR_RELAY_CAPACITY` budget (default 50).

## How it spawns and supervises monitor processes

`monitor.go:109-225` defines `MONITOR_CMD_DATA_MAP` — a hard-coded table of `MonitorType` → Python entry-point. For example `COLOUR` runs `/src/monitors/colour/colour.py` under the `/src/base/` venv; ML monitors (`LIQUID_VOLUME_YOLO`, `TEXT`, etc.) use `/src/ml/`. Notably, the `ARBITER` slot points at `arbiter_v2.py` (`monitor.go:113`) — that's how [v2](arbiters/v2.md) becomes the production default.

`Monitor.runWebRTC` (`monitor.go:450`) loops: subscribe to the LabEye's WebRTC stream, on `OnTrack` call `startGStreamerPipeline` (`monitor.go:942`), and pump RTP packets from the WebRTC track into a GStreamer `appsrc`. The pipeline (`monitor.go:1003-1019`) is:

```
appsrc ! application/x-rtp ! rtph264depay ! queue ! h264parse !
rtph264pay pt=96 config-interval=1 ! udpsink host=127.0.0.1 port=<port>
```

The Python child is launched with a matching `udpsrc port=<port> ! ... ! appsink` pipeline (`monitor.go:1028`), which is what `Common.StreamCapture` opens via OpenCV's `cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)`. PLI (Picture Loss Indication) RTCP packets are sent every 2 seconds (`monitor.go:946-969`) to keep the camera issuing keyframes.

A monitor that crashes or stops producing output for 5 minutes is killed and marked `FAILED` (`monitor.go:921-928`); finished monitors are reaped by the cleanup goroutine in `handler.go:62-80`.

## stdout parsing

`Monitor.parseMonitorLogLineAndWriteToMSK` (`monitor.go:686`) is the dispatcher for monitor output. It recognises four prefixes:

- `DATA:<unix_ts>:<json-or-csv>` — the per-frame result. Parsed as JSON first, falling back to comma-separated `label,type,value` triples. Published to `MONITOR_DATA_TOPIC` keyed by `{"monitorId": ..., "timestamp": ...}` (`monitor.go:780-798`).
- `ERROR:<unix_ts>:<message>:<errorCode>:<info>` — forwarded to the lumi-error-reporter on `OHDEAR_TOPIC` via `errorReporter.OhDearWhatHappened` (`monitor.go:719`).
- `LOG:` and `DEBUG:` — passed through to the relay's own log via `log.Printf("Monitor [%v] Subprocess: %s", ...)` (`monitor.go:908`); not forwarded to Kafka.
- `METRICS:<json>` — emitted by [Common.profiling.phase_marker](common.md); the CVM listener filters on this prefix to time process boot phases.

Anything that doesn't match is logged but discarded.

## Kafka topics (publishes via msk.go)

`monitor_relay/msk.go:10` is a thin factory that builds a `kafka.Writer` (segment.io's client) for `MONITOR_DATA_TOPIC`. TLS is enabled unless `IS_LOCAL` is set (`const.go:19`). Batching: 100 messages or 100 ms, whichever comes first.

Topics published by the relay:

- `MONITOR_DATA_TOPIC` (env `MONITOR_DATA_TOPIC`) — every parsed `DATA:` line. This is the single source of truth that every arbiter's curator subscribes to.
- `OHDEAR_TOPIC` (env `ERROR_TOPIC`) — every `ERROR:` line plus the relay's own startup/lifecycle errors.
- AI-agent topics (set by `aiagents/config`) — `DeviceConnections`, `StateManifest`, `LifecycleCommands`. Wired via `aiagents/cvmpublisher` from `cmd/monitor_relay/main.go:122-132`.

The relay does not consume any Kafka topics — all incoming work arrives over HTTP.

## Where the WebRTC / GStreamer pipeline lives

- `monitor.go:450-540` — WebRTC connection loop, ICE handling, OnTrack hookup.
- `monitor.go:942-1000` — RTP-to-GStreamer pumping; PLI keepalive.
- `monitor.go:1003-1019` — pipeline string construction. The Python side's pipeline is in [Common.common](common.md) as `GSTREAMER_PIPELINE`.

The AI-agent path (`aiagents/core/videopipeline/`) is the newer, multi-camera variant used by the v3-style fleet but supervised by the same relay.

## Tests

- `monitor_relay/handler_test.go`, `monitor_test.go` — Go tests exercising the HTTP surface and the monitor lifecycle with a mock `interfaces.WebRTC` and `interfaces.HttpClient`.
- `monitor_relay/test/` — integration harness wiring the relay against a local Kafka.
- `aiagents/core/types_test.go` — agent-side type round-trips.

Run with `go test ./...` from inside `monitor_relay/`.

## See also

- [V2 arbiter](arbiters/v2.md) — what the relay launches when `monitor.Type == "Arbiter"`.
- [colour monitor](monitors/colour.md) — exemplar Python monitor, simplest stdout shape.
- [Common](common.md) — `StreamCapture`, `phase_marker`, the `DATA:`/`ERROR:` print conventions.
- `monitor_relay/README.md` — repo-local quick reference.
- `monitor_relay/STATE_MAP.md` — the monitor lifecycle states (`STARTING`, `RUNNING`, `FAILED`, `FINISHED`).
