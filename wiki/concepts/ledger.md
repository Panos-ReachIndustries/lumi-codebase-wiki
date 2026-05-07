---
name: Ledger
description: The append-only event log that records everything that happened during an experiment run.
type: concept
tags: [concepts]
sources:
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter_v2/historian_v2.py }
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter_v2/history_v2.py }
  - { repo: Lumi-AI-Continuous, path: Docs/architecture/system_architecture.md }
---

# Ledger

The **ledger** is the append-only event log for a single experiment run. It records which protocol instructions completed, when, and what the AI saw at that moment. It is the primary artifact for audit, replay, and post-experiment analysis. The ledger is written by the historian component of the arbiter and uploaded to S3.

## Who writes it

The **Experiment Historian** (V1: `ExperimentHistorian` in `protocol_arbiter/historian.py`; V2: `ExperimentHistorianV2` in `protocol_arbiter_v2/historian_v2.py`) is the sole writer. It continuously watches the `history_cache` — a shared in-memory dict populated by the Curator — and appends a new ledger event each time a protocol instruction or action is considered completed.

Every N minutes, the historian uploads a versioned snapshot of both the protocol JSON and the ledger JSON to S3 (under the `ledger/` prefix in the experiment bucket). A final upload happens when the experiment ends.

## Who reads it

- The web viewer reads the ledger from S3 (via the VIS Lab Core API) to render experiment history and replay timelines.
- The historian itself reads its own in-progress ledger to avoid emitting duplicate events on restart.
- Test suites assert against ledger contents to verify arbiter correctness.

## LedgerEvent schemas

### V1

The V1 ledger event uses the nested stage/step/action coordinate system. Each event records the timestamp and the `{ stage, step, action, event }` tuple that was completed.

### V2 — `LedgerEventV2`

Defined in `Lumi-AI-Continuous/protocol_arbiter_v2/historian_v2.py` (line 48):

```python
class LedgerEventV2:
    timestamp: str
    instruction_id: int
    event: str        # e.g. "InstructionCompleted"
    data: Dict[str, Any]
```

`HistorianV2` consumes `history_cache["protocol_actions"]` entries and maps them to `LedgerEventV2` objects. Each entry can be in V1 format (`{ stage, step, action, event }`) or V2 format (`{ instructionId, state }`); `history_v2.py:append_protocol_events` handles both. The state field follows the enum `NOT_STARTED | IN_PROGRESS | PAUSED | COMPLETED`.

## How `history_cache` feeds the ledger

The flow is:

1. Monitors publish AI results to `monitor-data-topic`.
2. **CuratorV2** (`curator_v2.py`) consumes those results and writes curated data into `history_cache`.
3. User commands (from `protocol-arbiter-commands`) are also written into `history_cache["protocol_actions"]` by the arbiter.
4. **HistorianV2** reads `history_cache["protocol_actions"]`, matches events to instruction IDs in `ProtocolStateV2`, and appends `LedgerEventV2` entries.
5. **ExperimentHistorianV2** serialises the in-memory ledger and uploads it to S3.

## See also

- [arbiter](arbiter.md) — the orchestrator that drives ledger creation
- [protocol](protocol.md) — the procedure the ledger records progress against
- `Lumi-AI-Continuous/protocol_arbiter_v2/historian_v2.py` — V2 ledger implementation
- `Lumi-AI-Continuous/protocol_arbiter_v2/history_v2.py` — `history_cache` mutation helpers
