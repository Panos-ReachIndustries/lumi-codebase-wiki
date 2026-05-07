---
name: Arbiter
description: The orchestration process that owns experiment state, drives protocol execution, and coordinates monitors via Kafka.
type: concept
tags: [concepts]
sources:
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter/README.md }
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter_v2/README.md }
  - { repo: Lumi-AI-Continuous, path: Docs/architecture/system_architecture.md }
---

# Arbiter

The **arbiter** is the central orchestration process for a Lumi experiment. It owns experiment state, starts and stops monitors, and drives execution of a protocol by consuming monitor output and user commands from Kafka. Think of it as the conductor: it knows what step the experiment is on and decides when to advance.

## Three components inside an arbiter

Every arbiter instance runs three co-operating pieces:

1. **arbiter.py** — the main controller. Initialises everything, handles user commands (pause, resume, stop, add/remove lab eyes), starts/stops monitors.
2. **curator.py** — the data collector. Listens to `monitor-data-topic` (and any other topics the user added via `addListener`) and writes curated data into a shared `history_cache`.
3. **historian.py** — the ledger keeper. Continuously analyses `history_cache`, writes a ledger of replayable experiment events, stamps the protocol with timestamps, and uploads versioned snapshots to S3 every N minutes.

## V1 vs V2

There are two production versions of the arbiter; both share the same Kafka topics and external behaviour.

**V1** (`Lumi-AI-Continuous/protocol_arbiter/`) uses a **nested stage / step / action** model. A protocol is a tree: stages contain steps, steps contain actions. Progression is tracked by (stage, step, action) indices. User commands like `updateProtocolEvent` reference this hierarchy explicitly.

**V2** (`Lumi-AI-Continuous/protocol_arbiter_v2/`) uses a **flat instruction-ID** model. A protocol is a list of instructions, each with a single numeric `id`. Sparse IDs (e.g. 10, 20, 35) are allowed; order is determined by ascending sort. `ProtocolStateV2` (in `state.py`) tracks `currentInstructionId`, `completedInstructionIds`, and protocol-level `status`. The arbiter loads a legacy nested protocol and derives the flat instruction view automatically via `load_v2_protocol_from_legacy`. V2 is the current production default.

## Kafka topics

| Direction | Topic | Purpose |
|-----------|-------|---------|
| Consume | `protocol-arbiter-commands` | User/web commands (start, pause, stop, camera events) |
| Consume | `monitor-data-topic` | AI results from all running monitors |
| Publish | `protocol-arbiter-status` | Current experiment/instruction state |
| Publish | `protocol-arbiter-history` | Ledger events and experiment history |

The web viewer sends commands to `protocol-arbiter-commands` and consumes status from `protocol-arbiter-status` and `monitor-events`.

## User commands (V1 example)

```json
{ "command": "pauseArbiter" }
{ "command": "stopArbiter" }
{ "command": "updateProtocolEvent", "stage": 1, "step": 2, "action": 3, "event": true }
```

For V2, protocol events reference `instructionId` instead of stage/step/action.

## See also

- [protocol](protocol.md) — the structured procedure that the arbiter executes
- [ledger](ledger.md) — the append-only event log the historian produces
- `Lumi-AI-Continuous/protocol_arbiter_v2/README.md` — V2 design notes
- `Lumi-AI-Continuous/protocol_arbiter/README.md` — V1 design notes
