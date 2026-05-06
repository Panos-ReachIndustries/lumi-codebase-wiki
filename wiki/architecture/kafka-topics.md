---
name: Kafka Topics
description: Every Kafka topic Lumi-AI-Continuous uses, with producers, consumers, and where they're declared in code.
type: architecture
tags: [kafka, topics, data-flow]
---

# Kafka Topics

These are the topic env-var names you'll see in the Python and Go code. Default topic names vary by environment (`.env`, `.env.example`).

| Topic var | Producer(s) | Consumer(s) | Purpose |
|-----------|-------------|-------------|---------|
| `MONITOR_DATA_TOPIC` | every `monitors/*` process | `protocol_arbiter*`, ledger writers | Structured detections / readings from each monitor. |
| `ERROR_TOPIC` | every component | error reporting | Component error reports. |
| `PROTOCOL_ARBITER_COMMANDS_TOPIC` | external (web → gateway → here) | `protocol_arbiter*` | Start, stop, advance, abort. |
| `PROTOCOL_ARBITER_STATUS_TOPIC` | `protocol_arbiter*` | gateway → `lumi-web-v2` (live experiment view) | Current protocol state snapshot. |
| `PROTOCOL_ARBITER_HISTORY_TOPIC` | `protocol_arbiter*` | ledger writers | Append-only decision history. |
| `PROTOCOL_ARBITER_RESPONSES_TOPIC` | `protocol_arbiter*` | command issuers | Responses to commands. |
| `AGENT_PROTOCOL_SYNC_TOPIC` | `monitors/custom` | external | Custom-agent protocol sync heartbeat. |
| `AGENT_LIFECYCLE_COMMANDS_TOPIC` | external | `monitors/custom` | Custom-agent lifecycle commands. |
| `AGENT_STATE_MANIFEST_COMMANDS_TOPIC` | external | `monitors/custom` | State manifest commands. |
| `AGENT_DEVICE_CONNECTIONS_TOPIC` | `monitor_relay`, devices | `monitors/custom` (and others) | Device connection state events. |
| `AI_AGENT_RESULTS_TOPIC` | `monitors/custom` | external listeners | Custom-agent inference results stream. |

## How to find them in code

A grep across the two Python repos:

```bash
grep -rE "[A-Z_]+_TOPIC" Lumi-AI-Continuous/ Lumi-AI-Core/ --include="*.py" --include="*.go"
```

This is exactly what `tools/build_graph.py` does to seed the Kafka-topic nodes in the graph. Topics appear in the graph as **amber squares** so they stand out from code modules.

## Default topic names

The variable name (e.g. `PROTOCOL_ARBITER_STATUS_TOPIC`) is read from environment at runtime. Defaults are in `Lumi-AI-Continuous/.env.example` and `docker-compose.dev.yml`. If you're running locally with `IS_LOCAL=true`, Kafka is bypassed entirely — monitors print to stdout, the arbiter reads stdin.

## Adding a new topic

1. Define a new `*_TOPIC` env var in `.env.example` with a sensible default.
2. Read it in code via `os.environ["MY_NEW_TOPIC"]` (Python) or `os.Getenv("MY_NEW_TOPIC")` (Go).
3. Re-run `python tools/build_graph.py` from the wiki repo to pick it up.
4. Add a row to the table above.

## Caveats the auto-graph won't tell you

- Topic **direction** in the graph is inferred from the file the var appears in (e.g. anything under `monitors/` is treated as a producer). That's right ~90% of the time but not always — some monitors also consume from sibling topics. Treat the dashed pubsub edges as a starting point, not gospel.
- Some topic names are referenced only as *strings* in YAML configs rather than as `*_TOPIC` env vars. Those won't be auto-detected. If you find one, file it manually here.
