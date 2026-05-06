---
name: Arbiter
description: The component that runs a protocol against live monitor data.
type: concept
tags: [domain, stub]
---

# Arbiter

The **arbiter** is the component that decides what step of a protocol is currently active. It takes monitor output as input, evaluates predicates against the protocol, and publishes status.

Three coexisting versions:

- **v1** (`protocol_arbiter/`) — nested stage / step / action.
- **v2** (`protocol_arbiter_v2/`) — flat instruction-IDs. **Production default.**
- **v3** (`protocol_arbiter_v3/`) — domain-only redesign with pure state machine. Not yet runnable.

Inputs: `MONITOR_DATA_TOPIC`, `PROTOCOL_ARBITER_COMMANDS_TOPIC`.
Outputs: `PROTOCOL_ARBITER_STATUS_TOPIC`, `PROTOCOL_ARBITER_HISTORY_TOPIC`, `PROTOCOL_ARBITER_RESPONSES_TOPIC`.

## See also

- [protocol](protocol.md)
- [kafka-topics](../architecture/kafka-topics.md)
- [arbiter v2 wiki page](../ai-continuous/arbiters/v2.md)
