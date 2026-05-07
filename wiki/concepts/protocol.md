---
name: Protocol
description: A structured experimental procedure — the lab SOP that the arbiter executes step by step.
type: concept
tags: [concepts]
sources:
  - { repo: Lumi-AI-Continuous, path: Docs/architecture/system_architecture.md }
  - { repo: Lumi-AI-Continuous, path: protocol_arbiter_v2/README.md }
  - { repo: lumi-web-v2, path: src/app/(authenticated)/protocol/ }
---

# Protocol

A **protocol** is the structured experimental procedure that the arbiter executes — the digital equivalent of a lab SOP (standard operating procedure). It defines the sequence of operations a scientist should perform on the bench. The arbiter's job is to track progress through this sequence, using monitor data and manual user input as evidence that each step has been completed.

## Creating a protocol

From the web UI, a protocol can be created two ways:

1. **Upload a PDF** — the app OCR-converts the document and extracts the procedure text. Entry point: `lumi-web-v2/src/app/(authenticated)/protocol/new/` (both V1 and V2 variants have a `createFormWithFileUpload.tsx` that accepts `.pdf` files).
2. **Enter text manually** — paste or type a protocol description and let the AI structure it.

Protocols are versioned. Each protocol has a stable `protocolId`, and edits create new `ProtocolVersion` records. The web route `protocol/[protocolId]/` lists all versions; selecting one pushes a `?versionId=` query param.

## V1 protocol shape (legacy)

A nested tree: **stages** contain **steps**, which contain **actions**. Each action has a legacy string ID like `"1.2.3"` (stage.step.action). The V1 arbiter (`Lumi-AI-Continuous/protocol_arbiter/`) tracks progress through this hierarchy. User commands reference `{ stage, step, action }` integers explicitly.

## V2 protocol shape (current)

A **flat list of instructions**, each with a single numeric `id`. Sparse IDs (e.g. 10, 20, 35) are allowed; execution order is determined by ascending sort. Example:

```json
{
  "version": 2,
  "instructions": [
    { "id": 10, "label": "Weigh salicylic acid", "description": "...", "metadata": { "kind": "action" } }
  ]
}
```

The V2 arbiter (`Lumi-AI-Continuous/protocol_arbiter_v2/`) can load a legacy nested protocol and derive this flat view automatically via `load_v2_protocol_from_legacy`. The web routes under `protocol/v2/[protocolId]/` are built for this model and expose controls like export and version switching.

## Storage

Once created, protocol JSON is stored in **AWS S3** (the experiment bucket, under the `protocol/` prefix). The historian uploads versioned snapshots alongside the ledger during and after an experiment run. The VIS Lab Core API reads protocols from S3 to serve the web viewer.

## Web routes summary

| Route | Purpose |
|-------|---------|
| `protocol/` | Protocol list |
| `protocol/new/` | Create a V1 protocol (PDF or text) |
| `protocol/v2/new/` | Create a V2 protocol (PDF or text) |
| `protocol/[protocolId]/` | View protocol, list versions |
| `protocol/v2/[protocolId]/` | V2 protocol overview with version controls |

## See also

- [arbiter](arbiter.md) — the process that runs a protocol
- [ledger](ledger.md) — the append-only log that records what happened during a protocol run
