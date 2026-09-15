# Local LGTM And Grafana MCP Stack

This stack makes a local Grafana LGTM backend available to Mark through the MCP Hub.

It uses:

- `grafana/otel-lgtm` for local Grafana, Prometheus-compatible metrics, Loki logs, Tempo traces, and OpenTelemetry ingest
- `grafana/mcp-grafana` for the Grafana MCP server
- Mark's shared MCP Hub as the only application-side MCP client

## Commands

Use these from the repository root:

```bash
cd /Users/adeelarshad/kagent
```

Validate the Compose file:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml config --quiet
```

Start the full LGTM + Grafana MCP stack:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml up -d
```

Recreate only the Grafana MCP server after command/auth/host changes:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml up -d --force-recreate grafana-mcp
```

Recreate the full stack:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml up -d --force-recreate
```

Show running services:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml ps
```

Follow logs:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml logs -f
```

Follow only LGTM logs:

```bash
docker logs -f kagent-lgtm
```

Follow only Grafana MCP logs:

```bash
docker logs -f kagent-grafana-mcp
```

Stop the stack:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml down
```

Stop the stack and remove the local LGTM volume:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml down -v
```

## Environment For Mark

Add this to `/Users/adeelarshad/kagent/backend/.env` or export it in the backend shell:

```env
GRAFANA_MCP_PROTOCOL=http
GRAFANA_MCP_URL=http://127.0.0.1:3132/mcp
GRAFANA_MCP_TOKEN=mark-local-dev-token
GRAFANA_URL=http://localhost:3001
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=admin
```

For a shared or production-like Grafana, prefer a service account token:

```env
GRAFANA_SERVICE_ACCOUNT_TOKEN=<grafana-service-account-token>
```

If `GRAFANA_MCP_TOKEN` is set, the MCP server also requires the MCP Hub caller to send it as a bearer token.

## Verify Stack

Grafana MCP uses stateful streamable HTTP. A raw curl session must first call `initialize`; Mark's MCP Hub does this automatically before `tools/list` or `tools/call`.

Check Grafana/LGTM health:

```bash
curl -sS http://localhost:3001/api/health
```

Check the Grafana MCP server with the required initialize handshake:

```bash
curl -i -X POST http://127.0.0.1:3132/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Authorization: Bearer mark-local-dev-token' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {
        "name": "curl-client",
        "version": "1.0"
      }
    }
  }'
```

Do not use a raw one-shot `tools/list` curl as the manual Grafana MCP smoke test. The server expects a streamable-HTTP MCP session after `initialize`; the backend MCP Hub manages that session for application calls.

If this returns `forbidden: host not allowed`, confirm the `grafana-mcp` service was recreated after the compose file added `localhost:3132` and `127.0.0.1:3132` to `--allowed-hosts`.

Check Mark backend MCP connector status:

```bash
curl -sS http://127.0.0.1:8000/api/jarvis/connectors/status
```

List Grafana tools through Mark's MCP Hub:

```bash
curl -sS http://127.0.0.1:8000/api/jarvis/connectors/grafana/tools
```

Check recent MCP Hub traces:

```bash
curl -sS 'http://127.0.0.1:8000/api/jarvis/connectors/traces?limit=20' | python3 -m json.tool
```

## Seed Telecom Evidence

Send synthetic telecom KPIs and logs into the local OTLP endpoint:

```bash
python3 scripts/seed_lgtm_telecom.py --scenario all
```

Seed one service procedure only:

```bash
python3 scripts/seed_lgtm_telecom.py --scenario voice-call-setup
python3 scripts/seed_lgtm_telecom.py --scenario sgi-data
python3 scripts/seed_lgtm_telecom.py --scenario lte-attach
```

Validate Grafana MCP through Mark's MCP Hub:

```bash
python3 scripts/validate_lgtm_mcp_hub.py \
  --api-base http://127.0.0.1:8000 \
  --service-id voice-call-setup \
  --output docs/storyteller-references/lgtm-validation-voice-call-setup.json
```

Validate all seeded service procedures:

```bash
python3 scripts/validate_lgtm_mcp_hub.py \
  --api-base http://127.0.0.1:8000 \
  --service-id voice-call-setup \
  --output docs/storyteller-references/lgtm-validation-voice-call-setup.json

python3 scripts/validate_lgtm_mcp_hub.py \
  --api-base http://127.0.0.1:8000 \
  --service-id sgi-data \
  --output docs/storyteller-references/lgtm-validation-sgi-data.json

python3 scripts/validate_lgtm_mcp_hub.py \
  --api-base http://127.0.0.1:8000 \
  --service-id lte-attach \
  --output docs/storyteller-references/lgtm-validation-lte-attach.json
```

Expected live validation result:

```text
voice-call-setup: metric rows >= 1, log rows >= 1
sgi-data: metric rows >= 1, log rows >= 1
lte-attach: metric rows >= 1, log rows >= 1
```

The validation artifacts are stored in:

```text
docs/storyteller-references/lgtm-validation-voice-call-setup.json
docs/storyteller-references/lgtm-validation-sgi-data.json
docs/storyteller-references/lgtm-validation-lte-attach.json
```

## Storyteller With Live Telemetry

Default storyteller behavior stays deterministic and gbrain-backed. Add `include_live_telemetry` only when you want the story response enriched with live Grafana/LGTM evidence:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/incidents/mobile-core/voice-call-setup-05841af2e3f4f430/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "lgtm-story-test",
    "message": "Create an executive summary for incidents/mobile-core/voice-call-setup-05841af2e3f4f430.",
    "include_live_telemetry": true
  }' | python3 -m json.tool
```

If the endpoint path looks awkward with `incidents/incidents/...`, use the legacy domain-first route:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/mobile-core/incidents/voice-call-setup-05841af2e3f4f430/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "lgtm-story-test",
    "message": "Create an executive summary for mobile-core/incidents/voice-call-setup-05841af2e3f4f430.",
    "include_live_telemetry": true
  }' | python3 -m json.tool
```

## Role In The Architecture

LGTM remains the telemetry system of record. gbrain stores compact semantic projections and incident links. The storyteller uses gbrain and on-demand Grafana MCP evidence as context, then creates written stories, spoken briefs, and visual explanations.
