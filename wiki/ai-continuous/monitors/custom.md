---
name: custom agent
description: "JSON-configurable AI pipeline runner — composes V2 modules into named blocks and ties them to camera generators. The most complex monitor in the system."
type: monitor
graph_node: monitors:custom
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/custom/custom_agent.py }
  - { repo: Lumi-AI-Continuous, path: monitors/custom/step_evaluator.py }
  - { repo: Lumi-AI-Continuous, path: monitors/custom/pipeline_telemetry.py }
  - { repo: Lumi-AI-Continuous, path: monitors/custom/detection_handlers/ }
  - { repo: Lumi-AI-Core, path: V2/Visualiser/WebViewer.py }
  - { repo: Lumi-AI-Core, path: V2/MultiCamera/InstanceMatcher.py }
tags: [monitor, agent]
---

# custom agent

The `custom` monitor is a *runtime-configurable AI pipeline*. Instead of a hard-coded V2 call like every other monitor, it reads a JSON `agent_definition` describing a graph of **blocks** (each `{module, class, function, initArgs, functionArgs, output}`) and a list of **generators** (per-camera processing pipelines), then dynamically `importlib.import_module`s every block, builds the dependency graph, and runs frames through it. Every other monitor is essentially a custom-agent config baked into Python; `custom` is the substrate.

It also runs an embedded `WebViewer` (port 5000), accepts protocol commands over Kafka, can pause/resume/`startWithConfig` mid-run, and integrates with a `StepEvaluator` (`monitors/custom/step_evaluator.py`) that watches block outputs and emits step-completion signals to a protocol arbiter.

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/custom/custom_agent.py:3970` (the `if __name__ == "__main__"` block).
- **Top-level classes:** `FrameBundleBuffer` (95), `GeneratorRunner` (126), `GeneratorManager` (1092), `CustomAgent` (1120) — all in `custom_agent.py`.
- **Block instantiation:** `GeneratorRunner._initialize_blocks` at `custom_agent.py:213` — dynamic `importlib.import_module(module_name)` with a `Lumi-AI-Core.` prefix fallback.
- **Step evaluator:** `monitors/custom/step_evaluator.py` — wraps tracks, emits step-completion judgements.
- **Telemetry:** `monitors/custom/pipeline_telemetry.py` — per-block timing rolled up to local store + optional Kafka.
- **Detection handlers:** `monitors/custom/detection_handlers/` (`base.py`, `wellplate_handler.py`) — per-class post-processors invoked after detection blocks.
- **Configs:** `monitors/custom/configs/` and `monitors/custom/liquid_end_to_end.json` (a worked example).
- **Docs:** `monitors/custom/Readme.md`, `monitors/custom/README_RUNNING.md`.

## How it runs

```bash
# Idle (no config, awaits manifest commands over Kafka)
python monitors/custom/custom_agent.py --agentId <id>

# Local with full config + WebViewer on a custom port
python monitors/custom/custom_agent.py --config liquid_end_to_end.json --is_local \
  --visualise --viewer_port 5050

# Production
python monitors/custom/custom_agent.py --config path/to/config.json --agentId <id>
```

`--config` is **optional** (`custom_agent.py:3978`) — without it the agent constructs an empty `CustomAgent` and waits for a `startWithConfig` command on the lifecycle topic.

## Inputs

Top-level config keys (`custom_agent.py:4068-4073`):

- `agent_definition.blocks` — flat list when used as a single-pipeline agent.
- `generators` — list of per-camera pipelines, each with its own `blocks`, `classGroups`, `instanceMatcher`, `intendedFps`, `workerThreads`.
- `pipelines` — list of camera sources for `MultiSourceCapture` (one block can fan-out across many cameras).
- `sharedInstances` — class instances reused across generators (e.g. one `Detection` model for everyone).
- `viewerFps` (default 30), `setupConfig`, `agentStartTime` for replay-safe Kafka filtering.

Each block declares its dependencies via `functionArgs` references like `"VesselDetector-points.output.points"` or the literal `"frame"` (see `monitors/custom/Readme.md` for the contract).

## Outputs

Two streams, both Kafka:

1. **Per-frame block outputs** → `MONITOR_DATA_TOPIC` and/or `AI_AGENT_RESULTS_TOPIC` (`custom_agent.py:2498, 2521, 3436`). Each output is published as its own message keyed by `{generator}.{block}.{outputKey}`. Heatmaps, raw frames, and any ndarray over 100 KB are dropped at the boundary by `_is_publishable_kafka_key` (`custom_agent.py` `_KAFKA_PUBLISH_DENY_KEYS`).
2. **Status / lifecycle events** → `AI_AGENT_RESULTS_TOPIC` via `_publish_status_event` (`custom_agent.py:2548`) and protocol heartbeats on `AGENT_PROTOCOL_SYNC_TOPIC` (`custom_agent.py:2860`).

## V2 modules used

The custom agent uses any V2 module dynamically — but the agent itself directly imports:

- [V2.Visualiser](../../ai-core/modules/Visualiser.md) — `WebViewer` (`custom_agent.py:33`).
- [V2.MultiCamera](../../ai-core/modules/MultiCamera.md) — `InstanceMatcher` (`custom_agent.py:34`).

Common downstream block targets include [V2.Detection](../../ai-core/modules/Detection.md), [V2.Tracking](../../ai-core/modules/Tracking.md), [V2.Vessels](../../ai-core/modules/Vessels.md), [V2.Pipetting](../../ai-core/modules/Pipetting.md), [V2.WellPlate](../../ai-core/modules/WellPlate.md), [V2.Colours](../../ai-core/modules/Colours.md), [V2.Interactions](../../ai-core/modules/Interactions.md).

## Common utilities used

- `Common.common.MultiSourceCapture` (multi-camera input), `StreamCapture`, `LocalStreamCapture`.
- `Common.common.GenericStreamReporter`, `NumpyEncoder`.
- `Common.profiling.phase_marker` — emits `started` / `imports_done` / `config_loaded` / `agent_constructed` markers consumed by the Go subprocess manager.
- `confluent_kafka.Producer` / `Consumer` directly (the agent talks Kafka in three roles: data emitter, command consumer, heartbeat publisher).

## Kafka topics published / subscribed

Subscribed:
- `AGENT_LIFECYCLE_COMMANDS_TOPIC` — start / stop / pause / resume / `startWithConfig` (`custom_agent.py:2617`).
- `AGENT_STATE_MANIFEST_COMMANDS_TOPIC` — full manifest reloads.
- `AGENT_DEVICE_CONNECTIONS_TOPIC` — device hot-plug events.

Published:
- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md) — block outputs (filtered).
- [`AI_AGENT_RESULTS_TOPIC`](../../architecture/kafka-topics.md) — detections, tracks, status events.
- [`AGENT_PROTOCOL_SYNC_TOPIC`](../../architecture/kafka-topics.md) — heartbeat (`AGENT_HEARTBEAT_INTERVAL` seconds, default 30).

## Tests

- `monitors/custom/test_custom_agent.py`
- `monitors/custom/test_agent_startup.py`
- `monitors/custom/test_kafka_publish_filter.py` — covers the deny-list logic.
- `monitors/custom/test_manifest_handler.py`
- `monitors/custom/test_step_evaluator.py`

## When it goes wrong

- **`Failed to initialize block X`** — usually a bad `module` path. Check the `Lumi-AI-Core.` prefix fallback at `custom_agent.py:235`; the agent tries the full path then strips the prefix.
- **Block silently disabled** — instantiation or first-call failure marks the block dead and the rest of the pipeline keeps going. Look for `Failed to initialize block` in logs.
- **`MSG_SIZE_TOO_LARGE`** — a new block is emitting a large ndarray under a key not in the deny-list. Add the key to `_KAFKA_PUBLISH_DENY_KEYS` or accept the size cap drop at 100 KB.
- **WebViewer port collision** — only an issue locally; production omits `--viewer_port`. Override on local with any free port.
- **No `startWithConfig` ever fires** — `--agentId` mismatch or wrong `MSK_BROKERS`. Without `--config` the agent legitimately just waits.
- **Heartbeats stop** — `_protocol_sync_topic` defaults to `agent-protocol-sync`; check `AGENT_PROTOCOL_SYNC_TOPIC` env var override.

## See also

- [V2.Detection](../../ai-core/modules/Detection.md) — the most-imported block target.
- [V2.MultiCamera](../../ai-core/modules/MultiCamera.md)
- [V2.Visualiser](../../ai-core/modules/Visualiser.md)
- [Kafka topics](../../architecture/kafka-topics.md)
- [monitor_relay](../monitor-relay.md) — sibling supervisor that hosts the simpler monitors.
