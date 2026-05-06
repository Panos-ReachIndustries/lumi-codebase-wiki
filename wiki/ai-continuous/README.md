---
name: Lumi-AI-Continuous
description: "Distributed AI monitoring platform: Python monitors, protocol arbiters, Go monitor relay, shared Common utilities."
type: repo
graph_node: repo:continuous
sources:
  - { repo: Lumi-AI-Continuous, path: README.md }
tags: [repo, overview]
---

# Lumi-AI-Continuous

`Lumi-AI-Continuous` is the distributed AI monitoring platform. It ingests live video from LabEye cameras, runs computer-vision monitors against the streams, and orchestrates laboratory experiment protocols — turning a recorded session into a replayable ledger. One repo, four cooperating component families, two languages (Python for AI and orchestration, Go for the camera-to-process bridge).

For the per-area deep dives, see the linked pages below. For environment variables, deploy setup, lint/test commands, and CI specifics, read `Lumi-AI-Continuous/README.md` directly — this page summarises and connects, it doesn't duplicate.

## The four component families

| Family | Folder | Language | What it does |
|--------|--------|----------|--------------|
| **Monitors** | `monitors/` | Python | One long-lived process per AI function (colour, dial, text, hands, liquids/*, objects, anonymiser, custom). Reads frames, calls a V2 module from [ai-core](../ai-core/README.md), prints `DATA:` lines. See [colour monitor](monitors/colour.md) for the canonical example. |
| **Arbiters** | `protocol_arbiter/`, `protocol_arbiter_v2/`, `protocol_arbiter_v3/` | Python | Orchestrate experiment protocols. [v1](arbiters/v1.md) (legacy stage/step/action), [v2](arbiters/v2.md) (production, flat instruction IDs), [v3](arbiters/v3.md) (in-progress redesign with pure domain layer). |
| **monitor_relay** | `monitor_relay/` | Go | Bridges WebRTC camera streams into local UDP ports, spawns and supervises monitor processes, parses their stdout, publishes results to Kafka. HTTP API for the web app's `devices` domain. See [monitor_relay](monitor-relay.md). |
| **Common** | `Common/` | Python | The shared platform layer: `StreamReporter` + `StreamCapture` base classes, Kafka connection pool, circuit breakers, phase-marker profiling, resource cleanup. See [Common](common.md). |

The platform also pulls `Lumi-AI-Core` in as a Git submodule (`Lumi-AI-Continuous/Lumi-AI-Core/`) for the V2 AI/CV class libraries — those are documented under [ai-core](../ai-core/).

## How it runs

### Local development

`Lumi-AI-Continuous/run_dev.py` is the one-shot dev launcher: it sets `IS_LOCAL=true`, points the monitors at `LOCAL_STORE_DIR` for protocol/ledger storage, and runs a configured monitor against a video file. See `video-sources.example.json` for the input shape.

```bash
# Single monitor against a local video
IS_LOCAL=true python monitors/colour/colour.py --config <cfg> --is_local --video <vid>

# Full local stack (relay + monitors + arbiter + Kafka + S3 mock)
docker compose -f docker-compose.dev.yml up -d --build
```

`IS_LOCAL=true` is the magic switch — it disables TLS on Kafka (`monitor_relay/const.go:19`, `Common/kafka_pool.py:62`), skips S3 uploads (the historians fall through to local `./ledgers/` and `./protocols/` folders), and tells the reporters to print to stdout instead of producing to MSK.

### Production

The relay is built from `Dockerfile.app`; the AI monitor base from `Dockerfile.ai`; arbiters and monitors are launched as subprocesses by [monitor_relay](monitor-relay.md) on EC2. Each relay handles one or many cameras up to its `MONITOR_RELAY_CAPACITY` budget (default 50, summed across monitor types — see `monitor_relay/monitor.go:55`).

## Tests

```bash
pytest                                # full suite
pytest monitors/colour -q             # one monitor
pytest protocol_arbiter_v2/Testing -q # v2 arbiter
go test ./...                         # monitor_relay (run from monitor_relay/)
```

`pytest.ini` and `conftest.py` at the repo root configure the suite. The Docker-based runner is `docker compose -f docker-compose.pytest.yml run --rm test-runner`.

## CI

GitHub Actions:

- `.github/workflows/ci.yml` — flake8, pytest, schema validation on every push.
- `.github/workflows/deploy.yml` — build and push images to ECR.
- `.github/workflows/trigger_dev.yml`, `trigger_main.yml` — branch-specific deploy triggers.

Schema validation runs `scripts/validate_monitor_schemas.py` against every `api/*/openapi.yaml` to keep the monitor I/O contracts honest.

## Where to look next

- New here? Start with [colour monitor](monitors/colour.md) — the simplest end-to-end example.
- Tracing a Kafka topic? See [architecture/kafka-topics](../architecture/kafka-topics.md) and [monitor_relay](monitor-relay.md).
- Wiring up a new protocol? Read [V2 arbiter](arbiters/v2.md) and `protocol_arbiter_v2/README.md`.
- Adding a new monitor? Subclass `StreamReporter` in [Common](common.md), register a `MonitorType` in `monitor_relay/monitor.go`, ship an `api/<name>/openapi.yaml`.
- For deeper architecture diagrams: `Lumi-AI-Continuous/Docs/`.
