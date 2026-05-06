---
name: Protocol
description: A protocol is a recipe for a lab experiment. Different shapes in v1 vs v2.
type: concept
tags: [domain, stub]
---

# Protocol

A **protocol** is the recipe for a lab experiment — the sequence of operations that should happen on the bench. The arbiter is the thing that runs it.

## V1 protocols

Nested: stages contain steps contain actions. Tracked top-down. Lives in `Lumi-AI-Continuous/protocol_arbiter/`.

## V2 protocols

Flat: a sparse list of integer-keyed *instructions*. Order is monotonically ascending. Each instruction has predicates that must hold for it to be considered satisfied. Lives in `Lumi-AI-Continuous/protocol_arbiter_v2/`.

The web app's `protocol/v2/*` routes edit and preview these.

## V3 protocols

Same conceptual shape as v2 but with a stricter separation between domain and effects. Currently only the domain layer is implemented (in `protocol_arbiter_v3/domain/`); the runtime is still TBD.

## See also

- [arbiter](arbiter.md)
- [Sample protocols](../../Lumi-AI-Continuous/protocols/) (in the source repo)
