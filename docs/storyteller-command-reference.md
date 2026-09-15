# Storyteller Command Reference

Useful local commands for validating incident storytelling, gbrain MCP access,
and fixture-driven inter-domain / intra-domain alarm correlation.

Run commands from:

```bash
cd /Users/adeelarshad/kagent
```

## 1. Required Environment

The backend reads gbrain settings from:

```text
/Users/adeelarshad/kagent/backend/.env
```

Expected keys:

```bash
GBRAIN_MCP_URL=http://localhost:3131/mcp
GBRAIN_MCP_TOKEN=<your-token>
```

For direct shell MCP tests, load the values without printing secrets:

```bash
set -a
source backend/.env
set +a
```

Canonical incident slugs now use:

```text
incidents/mobile-core/<id>
```

Legacy slugs are still accepted as aliases:

```text
mobile-core/incidents/<id>
```

Because the backend route starts with `/api/incidents/`, canonical incident API
URLs contain `api/incidents/incidents/mobile-core/...`.

## 2. Start Or Check Services

Check gbrain MCP. `GET` should return `405 Method Not Allowed`; that means the
HTTP MCP endpoint is reachable and expects JSON-RPC `POST`.

```bash
curl -i http://127.0.0.1:3131/mcp
```

If gbrain is not running:

```bash
/Users/adeelarshad/.bun/bin/gbrain serve --http --port 3131
```

Check the backend:

```bash
curl -i http://127.0.0.1:8000/health
```

If the backend is not running on `8000`:

```bash
set -a
source /Users/adeelarshad/kagent/backend/.env
set +a
PYTHONPATH=/Users/adeelarshad/kagent/services/agents/src \
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 3. Correlation Worker

Dry-run the original local synthetic fixtures without writing to gbrain:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --fixtures services/agents/src/correlation/fixtures
```

Write the original local synthetic fixtures to gbrain:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --fixtures services/agents/src/correlation/fixtures \
  --write
```

Dry-run synthetic Grafana LGTM evidence for CSSR, SGi throughput, and 4G attach
SR:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --source grafana-synthetic \
  --fixtures services/agents/src/correlation/fixtures/grafana-lgtm
```

Dry-run one Grafana-backed intent:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --source grafana-synthetic \
  --fixtures services/agents/src/correlation/fixtures/grafana-lgtm \
  --intent 4g_attach_sr
```

Write synthetic Grafana evidence into `grafana/*` pages and link it to
canonical incident, correlation, storytelling, learning, and asset pages:

```bash
PYTHONPATH=services/agents/src \
python3 -m correlation.worker \
  --source grafana-synthetic \
  --fixtures services/agents/src/correlation/fixtures/grafana-lgtm \
  --write
```

Expected canonical Grafana-derived incident IDs:

```text
incidents/mobile-core/voice-call-setup-05841af2e3f4f430
incidents/mobile-core/sgi-data-a154bb7a3997859c
incidents/mobile-core/lte-attach-54db6ef325fbf758
```

## 3A. Local LGTM Stack And Grafana MCP Hub

Start the local LGTM and Grafana MCP stack:

```bash
cd /Users/adeelarshad/kagent
docker compose -f deploy/monitoring/lgtm/compose.yaml up -d
```

Recreate the Grafana MCP container after command, auth, or host allowlist changes:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml up -d --force-recreate grafana-mcp
```

Check stack status and logs:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml ps
docker logs -f kagent-lgtm
docker logs -f kagent-grafana-mcp
```

Stop the stack:

```bash
docker compose -f deploy/monitoring/lgtm/compose.yaml down
```

Verify Grafana/LGTM health:

```bash
curl -sS http://localhost:3001/api/health
```

Manual Grafana MCP streamable-HTTP smoke test. Direct curl must initialize first:

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

Verify Grafana through Mark's MCP Hub:

```bash
curl -sS http://127.0.0.1:8000/api/jarvis/connectors/status | python3 -m json.tool
curl -sS http://127.0.0.1:8000/api/jarvis/connectors/grafana/tools | python3 -m json.tool
curl -sS 'http://127.0.0.1:8000/api/jarvis/connectors/traces?limit=20' | python3 -m json.tool
```

Seed local LGTM with telecom metrics and logs:

```bash
python3 scripts/seed_lgtm_telecom.py --scenario all
```

Validate live Grafana evidence through MCP Hub:

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

## 4. Incident Registry API

List current incident/candidate outcomes:

```bash
curl -sS 'http://127.0.0.1:8000/api/incidents?limit=50' \
  | python3 -m json.tool
```

Compact incident list:

```bash
curl -sS 'http://127.0.0.1:8000/api/incidents?limit=50' \
  | python3 -c 'import json,sys; data=json.load(sys.stdin); [print("{} | {} | {} | score={}".format(i.get("incident_id"), i.get("status"), i.get("scope"), i.get("score"))) for i in data]'
```

Fetch one canonical registry item:

```bash
curl -sS \
  http://127.0.0.1:8000/api/incidents/incidents/mobile-core/lte-attach-54db6ef325fbf758 \
  | python3 -m json.tool
```

Fetch lifecycle audit for one canonical registry item:

```bash
curl -sS \
  http://127.0.0.1:8000/api/incidents/incidents/mobile-core/lte-attach-54db6ef325fbf758/audit \
  | python3 -m json.tool
```

## 5. Storyteller Ask API

Print only the rendered storyteller answer for the canonical LTE attach
incident:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/incidents/mobile-core/lte-attach-54db6ef325fbf758/ask \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"curl-mcp-test","message":"Tell the incident story for incidents/mobile-core/lte-attach-54db6ef325fbf758."}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["answer"])'
```

Print the full JSON response, including `answer`, `story`, and detected
`intent`:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/incidents/mobile-core/lte-attach-54db6ef325fbf758/ask \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"curl-mcp-test","message":"Tell the incident story for incidents/mobile-core/lte-attach-54db6ef325fbf758."}' \
  | python3 -m json.tool
```

Ask for a specific deterministic answer type:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/incidents/mobile-core/lte-attach-54db6ef325fbf758/ask \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"curl-mcp-test","intent":"evidence","message":"Show me the evidence for this incident."}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["answer"])'
```

Useful `intent` values:

```text
story
executive
technical
root_cause
evidence
timeline
impact
why
remediation
recovery
similar
```

Legacy alias check:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/mobile-core/incidents/lte-attach-54db6ef325fbf758/ask \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"curl-alias-test","message":"Tell the incident story for mobile-core/incidents/lte-attach-54db6ef325fbf758."}' \
  | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("incident_id")); print(data["answer"].splitlines()[0])'
```

Regression check against the older AMF incident:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/mobile-core/incidents/amf-overload-2026-08-09/ask \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"curl-amf-test","message":"Tell the incident story for mobile-core/incidents/amf-overload-2026-08-09."}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["answer"])'
```

## 6. Story API

Return the structured deterministic story object:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/incidents/incidents/mobile-core/lte-attach-54db6ef325fbf758/story \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"curl-mcp-test","synthesize":false}' \
  | python3 -m json.tool
```

## 7. Capture A Reference Story Bundle

Capture a reusable reference bundle for any incident. This stores:

```text
answer.md      rendered story
response.json  full API response
story.json     structured build trace
command.txt    replay command
request.json   original request body
```

Canonical example:

```bash
scripts/capture_story_reference.sh \
  incidents/mobile-core/lte-attach-54db6ef325fbf758 \
  'Tell the incident story for incidents/mobile-core/lte-attach-54db6ef325fbf758.'
```

Legacy example:

```bash
scripts/capture_story_reference.sh \
  mobile-core/incidents/ue-registration-1fe005ed908a3f26 \
  'Tell the incident story for mobile-core/incidents/ue-registration-1fe005ed908a3f26.'
```

## 8. Direct gbrain MCP JSON-RPC

MCP requires both the bearer token and an accept header that includes
`text/event-stream`.

Fetch a canonical gbrain page:

```bash
set -a
source backend/.env
set +a
curl -sS -N http://127.0.0.1:3131/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Authorization: Bearer ${GBRAIN_MCP_TOKEN}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_page","arguments":{"slug":"incidents/mobile-core/lte-attach-54db6ef325fbf758"}}}' \
  | sed -n '1,20p'
```

Fetch outgoing links for a canonical page:

```bash
set -a
source backend/.env
set +a
curl -sS -N http://127.0.0.1:3131/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Authorization: Bearer ${GBRAIN_MCP_TOKEN}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_links","arguments":{"slug":"incidents/mobile-core/lte-attach-54db6ef325fbf758"}}}' \
  | sed -n '1,40p'
```

Fetch the learning note and verify FCAPS review exists:

```bash
set -a
source backend/.env
set +a
curl -sS -N http://127.0.0.1:3131/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Authorization: Bearer ${GBRAIN_MCP_TOKEN}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_page","arguments":{"slug":"learning/mobile-core/notes/lte-attach-54db6ef325fbf758"}}}' \
  | sed -n '1,30p'
```

## 9. Backend And Frontend Checks

Run focused backend tests for correlation and storyteller:

```bash
PYTHONPATH=services/agents/src \
pytest \
  services/agents/src/correlation/tests \
  services/agents/src/storyteller/tests/test_conversation_api.py \
  services/agents/src/storyteller/tests/test_reasoning.py \
  -q
```

Run frontend TypeScript validation:

```bash
cd frontend
npx tsc --noEmit
```

Check diff whitespace before committing:

```bash
git diff --check
```

Refresh the code graph after code changes:

```bash
graphify update .
```

## 10. Troubleshooting

`SyntaxError: f-string expression part cannot include a backslash`

Use `.format(...)` instead of nested escaped f-strings in one-line Python:

```bash
curl -sS 'http://127.0.0.1:8000/api/incidents?limit=50' \
  | python3 -c 'import json,sys; data=json.load(sys.stdin); [print("{} | {} | {} | score={}".format(i.get("incident_id"), i.get("status"), i.get("scope"), i.get("score"))) for i in data]'
```

`Not Acceptable: Client must accept both application/json and text/event-stream`

Add this header to direct MCP calls:

```bash
-H 'Accept: application/json, text/event-stream'
```

`Missing Authorization header` or `Invalid Authorization header format`

Load `GBRAIN_MCP_TOKEN` from `backend/.env` and pass it as:

```bash
-H "Authorization: Bearer ${GBRAIN_MCP_TOKEN}"
```

`GET /mcp` returns `405 Method Not Allowed`

That is expected. Use `POST` with a JSON-RPC body for actual MCP tool calls.
