# Grafana LGTM Integration Plan

This integration treats Grafana LGTM as a telemetry evidence source and gbrain
as the deterministic incident memory. The storyteller continues to narrate from
gbrain only.

## Local LGTM Availability

The local development stack lives in:

```text
deploy/monitoring/lgtm/
```

It provides:

- `grafana/otel-lgtm` as the local LGTM backend
- `grafana/mcp-grafana` as the Grafana MCP server
- streamable HTTP MCP on `http://127.0.0.1:3132/mcp`
- stateful HTTP MCP initialization through Mark's MCP Hub before `tools/list` or `tools/call`
- Grafana UI on `http://localhost:3001`
- read-only MCP mode by default

Mark connects to Grafana through the shared MCP Hub by setting:

```env
GRAFANA_MCP_PROTOCOL=http
GRAFANA_MCP_URL=http://127.0.0.1:3132/mcp
GRAFANA_MCP_TOKEN=mark-local-dev-token
GRAFANA_URL=http://localhost:3001
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=admin
```

For production-like use, replace username/password with:

```env
GRAFANA_SERVICE_ACCOUNT_TOKEN=<grafana-service-account-token>
```

## Target Flow

```text
Grafana LGTM / Grafana MCP
-> normalize telemetry
-> AlarmEvent[] + EvidenceEvent[]
-> CorrelationEngine
-> GbrainWriter
-> grafana/* evidence pages linked to canonical incident/correlation pages
-> storyteller /ask or /story
```

## Namespaces

Grafana-origin source evidence is stored outside the mobile-core incident
namespace:

```text
grafana/alerts/...
grafana/metrics/...
grafana/logs/...
grafana/traces/...
grafana/dashboards/...
grafana/panels/...
```

Grafana is only the telemetry source namespace. The reasoning, incident,
storytelling, and learning objects live in their own explicit namespaces:

```text
incidents/mobile-core/<id>
correlation/mobile-core/clusters/<id>
correlation/mobile-core/decisions/<id>
correlation/mobile-core/hypotheses/<id>
domains/mobile-core/networks/<area>/service-procedures/<procedure>
domains/mobile-core/networks/<area>/functions/<node>
knowledge/mobile-core/kpis/<kpi>
assets/mobile-core/playbooks/<playbook>
assets/mobile-core/runbooks/<runbook>
storytelling/mobile-core/stories/<incident-id>
storytelling/mobile-core/story-runs/<incident-id>-<run-id>
learning/mobile-core/notes/<id>
```

Legacy `mobile-core/incidents/<id>` slugs are retained as aliases so existing UI
and curl commands continue to resolve, but new writes use
`incidents/mobile-core/<id>`.

Relevant Grafana evidence is linked into the correlation hypothesis:

```text
correlation/mobile-core/hypotheses/<id> supported-by grafana/metrics/<id>
correlation/mobile-core/hypotheses/<id> supported-by grafana/logs/<id>
correlation/mobile-core/hypotheses/<id> supported-by grafana/traces/<id>
correlation/mobile-core/hypotheses/<id> supported-by grafana/alerts/<id>
incidents/mobile-core/<id> has-story storytelling/mobile-core/stories/<id>
incidents/mobile-core/<id> has-learning-note learning/mobile-core/notes/<id>
```

FCAPS is used as a lens on every written object, not as a folder name. Alerts
and incidents are usually `fault`, KPI breaches are `performance`, missing or
related maintenance activity is `change`, subscriber/session-volume gaps are
`accounting`, and anomaly/security gaps are `security`.

## POC Intents

The first logical-topology POC covers:

- `cssr`: Call Setup Success Rate for `voice-call-setup`.
- `sgi_throughput`: SGi/Gi/N6 data service throughput for `sgi-data`.
- `4g_attach_sr`: LTE attach success rate for `lte-attach`.

Because physical topology is not available initially, fixtures use logical
standard mobile-core paths:

```text
voice-call-setup -> RAN, transport, mobile-core IMS P-CSCF/S-CSCF
sgi-data -> RAN, S1-U, mobile-core PS SGW/PGW, firewall/NAT, internet edge
lte-attach -> RAN, S1-MME, mobile-core LTE MME/HSS, mobile-core PS SGW/PGW
```

## Local Commands

Dry-run all synthetic Grafana LGTM inputs:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --source grafana-synthetic \
  --fixtures services/agents/src/correlation/fixtures/grafana-lgtm
```

Dry-run one intent:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --source grafana-synthetic \
  --fixtures services/agents/src/correlation/fixtures/grafana-lgtm \
  --intent 4g_attach_sr
```

Write synthetic Grafana evidence and correlated incidents to gbrain:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --source grafana-synthetic \
  --fixtures services/agents/src/correlation/fixtures/grafana-lgtm \
  --write
```

Seed live local LGTM with telecom-shaped OTLP metrics and logs:

```bash
python3 scripts/seed_lgtm_telecom.py --scenario all
```

Validate the Grafana MCP connector through Mark's MCP Hub:

```bash
python3 scripts/validate_lgtm_mcp_hub.py \
  --api-base http://127.0.0.1:8000 \
  --service-id voice-call-setup \
  --output docs/storyteller-references/lgtm-validation-voice-call-setup.json
```

## Real Grafana MCP Next Step

The code includes a small HTTP JSON-RPC client for `GRAFANA_MCP_URL` in:

```text
services/agents/src/correlation/adapters/grafana_mcp.py
```

The implementation now discovers Grafana MCP tool names through Mark's MCP Hub
and normalizes alert, metric, log, trace, and dashboard results into provenance
facts for storyteller evidence.
