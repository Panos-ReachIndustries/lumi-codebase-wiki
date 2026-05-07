---
name: Custom Agent
description: A user-defined AI pipeline made of configurable blocks, each wrapping a V2 module, resolved and executed at runtime.
type: concept
tags: [concepts]
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/custom/Readme.md }
  - { repo: Lumi-AI-Continuous, path: monitors/custom/custom_agent.py }
  - { repo: Lumi-AI-Continuous, path: Docs/system_message_flow.md }
---

# Custom Agent

A **custom agent** is a user-defined AI processing pipeline assembled from composable **blocks**, where each block wraps a single V2 module from `Lumi-AI-Core`. The pipeline is described entirely in a JSON config file — no code changes needed to wire up a new combination of capabilities. This is the engine behind the "AI Assist" feature in the Lumi web UI.

## Core idea

Rather than writing a new monitor for every new combination of AI tasks, you declare a pipeline as a list of blocks. The custom agent resolves their dependencies, sorts them into execution order (topological sort), and runs them against each video frame in the right sequence.

## Block definition

Each block in the JSON config has this shape (from `Lumi-AI-Continuous/monitors/custom/Readme.md`):

```json
{
  "blockName": "unique_block_identifier",
  "module": "Lumi-AI-Core.ModuleName.ClassName",
  "class": "ClassName",
  "initArgs": { "param": "value" },
  "function": "method_to_call",
  "functionArgs": {
    "arg1": "frame",
    "arg2": "otherBlock.output.property"
  },
  "output": { "outputName": "type" }
}
```

The reference system in `functionArgs` supports three forms:
- `"frame"` — the current video frame
- `"blockName.output.property"` — a specific output field from another block
- `"blockName"` — the entire output object of another block

## Runtime behaviour

The `CustomAgent` class (`Lumi-AI-Continuous/monitors/custom/custom_agent.py`) is the main orchestrator. At startup it:

1. Reads the JSON config and instantiates each block's class dynamically via `importlib`.
2. Computes execution order by topological sort of the dependency graph.
3. Enters the main loop: for each frame, runs each block in order, passing resolved arguments.
4. If a block fails, it is disabled automatically — the rest of the pipeline continues.
5. Publishes results to Kafka and serves frames via a Flask WebViewer on port 5000.

The agent process is spawned as a **subprocess by the Monitor Relay** (Go). The arbiter tells the relay to start it via `POST /v2/ai/internal/ai-agent/start`, and can replace the running pipeline by calling `POST /api/cameras/connect` (which kills the old agent and spawns a new one with video-aware pipelines). The frontend polls frames directly from the agent at `GET http://relay:5000/frame/<camera_id>`.

## Kafka integration

When `KAFKA_AVAILABLE`, the agent publishes results to `MONITOR_DATA_TOPIC` using a `GenericStreamReporter`. It also consumes from Kafka for filter/control messages. This makes it a first-class citizen alongside the fixed-capability monitors from an arbiter's perspective.

## Relation to "AI Assist" in the web UI

The web UI's AI Assist feature works by constructing a custom-agent pipeline config and sending it to the relay. The user selects capabilities (e.g. object detection + colour analysis), the web app serialises that as a block JSON, and the relay spawns a custom agent running that exact pipeline. This means any new V2 module can be exposed to users without a deploy — only a config change is needed.

Pipeline templates live in `Lumi-AI-Continuous/agent_definition_templates/`.

## See also

- [monitor](monitor.md) — the simpler, single-capability alternative to a custom agent
- `Lumi-AI-Continuous/monitors/custom/Readme.md` — full configuration reference with examples
- `Lumi-AI-Continuous/Docs/system_message_flow.md` — HTTP + Kafka flow showing how the relay spawns and manages agents
- [web/api/aiAgents](../web/api-domains/aiAgents.md)
