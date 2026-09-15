# Mark Enterprise Capability Registry

This document explains how Mark is extended without turning it into a collection of unrelated agents.

## Purpose

Mark remains one assistant. The registry gives Mark a machine-readable map of the engines, services, connectors, skills, permissions, and learning lenses available to it.

The registry is deliberately separate from execution code. Existing runtime paths can continue working while Mark gains a clearer capability model.

## Core Model

```text
Mark
  -> Engine: capability area
  -> Service: internal functional boundary
  -> Connector: named external system boundary
  -> Skill: human-readable operating procedure
  -> Trace: explanation of what Mark selected and used
```

There is one inbound MCP server and one outbound MCP client hub:

```text
External clients
  -> Mark MCP Server
      -> Mark Orchestrator
          -> MCP Client Hub
              -> gbrain / Grafana / Gmail / WhatsApp / Teams / Office / Calendar / Codex / Vector DB / Metadata DB
```

The MCP client hub is the shared transport runtime. Connector manifests still exist because each external system needs its own ownership, environment variables, allowed tools, permission policy, and audit behavior.

The canonical backend scaffolding lives here:

```text
/Users/adeelarshad/kagent/services/agents/src/assistant/mark/
/Users/adeelarshad/kagent/services/agents/src/capability_registry/
/Users/adeelarshad/kagent/services/agents/src/engine_stack/
/Users/adeelarshad/kagent/services/agents/src/mcp_hub/
```

The existing `/api/jarvis/*` routes and legacy imports remain available through compatibility wrappers:

```text
/Users/adeelarshad/kagent/services/agents/src/jarvis/core.py
/Users/adeelarshad/kagent/services/agents/src/jarvis/registry/
/Users/adeelarshad/kagent/services/agents/src/jarvis/mcp_client_hub/
```

The MCP hub implementation lives here:

```text
/Users/adeelarshad/kagent/services/agents/src/mcp_hub/
  hub.py
```

The hub is responsible for:

- connector status
- tool discovery
- downstream MCP tool calls
- approval enforcement for side-effect tools
- connector call traces
- persistent stdio MCP sessions for local/sandbox connectors

## Engines

Engines are not data stores. They are specialist capability areas.

| Engine | Responsibility |
| --- | --- |
| Telecom Brain Engine | Telecom incidents, alarms, KPIs, topology projections, service procedures, intents, RCA, storytelling, FCAPS learning |
| Knowledge Base Engine | Document inventory, Microsoft Office document access, metadata-first knowledge answering, selective vector retrieval |
| Collaboration Engine | Gmail, WhatsApp, and Microsoft Teams drafting/sending, stakeholder updates, handover notes |
| Calendar Engine | Incident bridge scheduling, maintenance-window context, reminders |
| Codex Engineering Engine | Controlled coding, debugging, tests, and sandbox execution |
| Automation Engine | Approved diagnostics, pre-checks, health checks, remediation proposals |

## Services

Services are internal boundaries. For example, the Telecom Brain Engine owns:

- Correlation Service
- Storytelling Service
- Telemetry Evidence Service
- Topology Service
- Incident Registry Service
- Intent Service
- FCAPS Learning Service

This keeps correlation and storytelling separate while still keeping both under the telecom brain umbrella.

## Connectors

Connectors are external boundaries.

| Connector | Role |
| --- | --- |
| gbrain MCP | Semantic telecom brain: knowledge, observations, learnings, projections |
| Grafana LGTM | Telemetry evidence: metrics, logs, traces, alerts, dashboards |
| Metadata DB | Document counts, lists, ownership, freshness, summaries |
| Vector DB | Chunk retrieval after metadata-first narrowing |
| Gmail | Approved email drafting/sending |
| WhatsApp | Approved operational messaging |
| Microsoft Teams | Approved Teams channel/chat updates and incident bridge summaries |
| Microsoft Office | Word, Excel, and PowerPoint document discovery and summarization |
| Google Calendar | Approved calendar coordination |
| Codex | Controlled engineering worker/sandbox |

Every connector is MCP-managed by default:

```yaml
transport: mcp
managed_by: mcp_client_hub
```

The MCP transport is hybrid by connector:

- stdio MCP for local/sandbox tools such as Codex
- HTTP MCP for shared or scalable services such as production gbrain, Grafana, Gmail, WhatsApp, Microsoft Teams, Microsoft Office, Calendar, Metadata DB, and Vector DB
- protocol overrides through connector-specific environment variables when a local stdio MCP server is preferred

Fallback transports such as stdio, Microsoft Graph API, Google API, SQL, REST, SDK, CLI, embedded data, or local sandbox are implementation fallbacks, not Mark's primary architecture.

Codex is configured as stdio MCP:

```yaml
mcp_runtime:
  protocol: stdio
  default_command: /usr/local/bin/codex
  stdio_framing: json_lines
  args:
    - mcp-server
```

Live Codex tool discovery currently exposes:

```text
codex
codex-reply
```

gbrain is configured as HTTP MCP primary with stdio/CLI/embedded fallback:

```yaml
mcp_runtime:
  protocol: http
  url_env: GBRAIN_MCP_URL
  default_url: http://localhost:3131/mcp
  token_env: GBRAIN_MCP_TOKEN
```

The existing storyteller and Telecom Brain gbrain paths now call through the shared MCP Client Hub first. The previous direct HTTP, CLI, and embedded graph paths remain as fallback safety.

Grafana is HTTP MCP by default for scale, but can be switched to persistent stdio:

```bash
export GRAFANA_MCP_PROTOCOL=stdio
export GRAFANA_MCP_COMMAND=/path/to/grafana-mcp-server
```

Then Mark will keep a persistent stdio session for Grafana inside the MCP Client Hub.

## gbrain Boundaries

gbrain should hold semantic context, not every raw source record.

Recommended namespace split:

```text
knowledge/mobile-core/...       stable domain knowledge
observations/mobile-core/...    semantic projections of incident/alarm/telemetry facts
learnings/mobile-core/...       reviewed learning from incidents and operator feedback
semantics/mobile-core/...       ontology, intent mappings, service-procedure relationships
```

Raw incidents remain in the incident registry. Raw telemetry remains in Grafana/LGTM. Raw documents remain in the document store/vector system.

## FCAPS Lens

FCAPS is used as a learning and enrichment lens, not as the whole taxonomy.

```text
F = Fault
C = Change Request / Configuration
A = Accounting
P = Performance
S = Security
```

Use FCAPS to classify evidence, identify missing context, enrich playbooks/runbooks, and review whether a learning note is complete.

## Skills

Skills are Markdown files with YAML frontmatter.

The frontmatter lets Mark select the right procedure. The Markdown body tells Mark how to behave.

Example:

```yaml
id: incident-storytelling
engine: telecom_brain
services:
  - incident_registry
  - storytelling
connectors:
  - gbrain
output_modes:
  - text
  - voice
```

This is better than pure YAML because the skill is operational guidance, not just configuration.

## Voice Rule

Brain content is context, not a script.

Mark should never read raw Markdown, incident slugs, punctuation, bullets, or table syntax aloud. Written answers can stay detailed. Spoken answers must be curated for a human conversation.

## API

The capability registry is exposed at:

```text
GET /api/jarvis/capabilities
```

This endpoint is intended for UI discovery, debugging, and future Mark self-awareness.

Connector runtime APIs:

```text
GET  /api/jarvis/connectors/status
GET  /api/jarvis/connectors/traces
GET  /api/jarvis/connectors/{connector_id}/tools
POST /api/jarvis/connectors/{connector_id}/call
```

Example:

```bash
curl -sS http://127.0.0.1:8000/api/jarvis/connectors/status | python3 -m json.tool
```
