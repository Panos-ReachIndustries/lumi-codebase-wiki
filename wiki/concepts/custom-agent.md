---
name: Custom Agent
description: A configurable monitor that composes V2 modules via JSON.
type: concept
tags: [domain, stub]
---

# Custom Agent

The **custom agent** is `monitors/custom/custom_agent.py`. Unlike the other monitors (which hard-wire one V2 module each), the custom agent reads a JSON config describing a *pipeline* of V2 modules and runs it.

This is what the web app's `aiAgents/` API domain talks to. The custom agent listens on `AGENT_LIFECYCLE_COMMANDS_TOPIC` and `AGENT_STATE_MANIFEST_COMMANDS_TOPIC`, and publishes results to `AI_AGENT_RESULTS_TOPIC`.

Pipeline templates live in `Lumi-AI-Continuous/agent_definition_templates/`.

## See also

- [custom monitor stub](../ai-continuous/monitors/custom.md)
- [web/api/aiAgents](../web/api-domains/aiAgents.md)
- [V2.Detection](../ai-core/modules/Detection.md) — the most-imported building block
