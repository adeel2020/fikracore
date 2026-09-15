# Inter- and Intra-Domain Alarm Correlation - Low-Level Design

## 1. Scope and Runtime Boundary

This document specifies the local implementation of the fixture-driven,
intent-aware correlation worker and the small Storyteller retrieval extension
needed to narrate its results.

The worker writes to gbrain through MCP. The existing Storyteller continues to
read from gbrain through `storyteller.knowledge.GbrainClient` and serves:

```text
POST /api/incidents/{incident_id}/story
POST /api/incidents/{incident_id}/ask
```

No new public API or gbrain schema migration is required. The existing
`mobile-core` schema is used as the universal incident contract. Its page prefix
is a storage namespace, not a filter on source alarm domains.

## 2. Package Layout

```text
services/agents/src/correlation/
  __init__.py
  models.py
  config.py
  fixtures.py
  normalize.py
  topology.py
  identity.py
  intents.py
  engine.py
  registry.py
  lifecycle.py
  gbrain_writer.py
  worker.py
  fixtures/
    alarms.jsonl
    kpis.jsonl
    tickets.jsonl
    topology.json
    services.json
    intents.json
  tests/
    test_normalize.py
    test_topology.py
    test_identity.py
    test_engine.py
    test_lifecycle.py
    test_writer.py
    test_worker_integration.py
```

`gbrain_writer.py` must not reuse the Storyteller client as-is: its public
`call()` contract is explicitly read-only. The writer can reuse the same HTTP
MCP framing internally, but it owns a strict allow-list of gbrain write tools.

## 3. Configuration

Environment variables:

```env
GBRAIN_MCP_URL=http://127.0.0.1:3131/mcp
GBRAIN_MCP_TOKEN=<token>
CORRELATION_WINDOW_MINUTES=10
CORRELATION_INCIDENT_THRESHOLD=70
CORRELATION_CANDIDATE_THRESHOLD=40
CORRELATION_MAX_TOPOLOGY_HOPS=4
CORRELATION_MIN_INCIDENT_EVIDENCE_GROUPS=2
```

CLI:

```bash
cd /Users/adeelarshad/kagent/services
PYTHONPATH=agents/src python -m correlation.worker \
  --fixtures agents/src/correlation/fixtures \
  --window-minutes 10
```

Useful local options:

```text
--dry-run       Calculate outcomes without MCP writes.
--run-id        Override the generated run ID for reproducible tests.
--since         Process events at or after an ISO-8601 timestamp.
--max-events    Bound a test run.
```

## 4. Canonical Models

`models.py` defines frozen dataclasses or Pydantic models with validation.

```python
AlarmEvent:
    tenant_id: str
    source_id: str
    timestamp: datetime
    severity: Literal["critical", "major", "minor", "warning", "info"]
    domain: str
    source_system: str
    object_id: str
    location: str | None
    alarm_code: str
    dedupe_key: str
    raw_ref: str | None

CanonicalComponent:
    component_id: str
    domain: str
    component_kind: str
    source_identifiers: dict[str, str]
    topology_version: str
    service_ids: tuple[str, ...]

EvidenceEvent:
    source_id: str
    kind: Literal["kpi", "ticket", "log", "trace", "change"]
    timestamp: datetime
    service_id: str | None
    object_id: str | None
    attributes: dict[str, Any]

ServiceIntent:
    intent_id: str
    service_id: str
    target_kpi: str
    comparator: Literal[">=", "<="]
    target_value: float
    critical_dependencies: tuple[str, ...]

CorrelationCandidate:
    tenant_id: str
    correlation_key: str
    time_window_start: datetime
    alarms: list[AlarmEvent]
    evidence: list[EvidenceEvent]
    topology_path: list[str]
    affected_services: list[str]
    matched_intents: list[ServiceIntent]
    score: int
    score_reasons: list[str]
    state: Literal["standalone", "candidate", "incident"]

IncidentRecord:
    incident_id: str
    tenant_id: str
    state: Literal["candidate", "open", "acknowledged", "resolved", "reopened", "suppressed", "merged", "split"]
    owner: str | None
    priority: str | None
    parent_incident_id: str | None
    successor_incident_ids: tuple[str, ...]
    topology_version: str
    intent_version: str
    audit_revision: int
```

All timestamps are parsed to UTC. `source_id` is immutable source provenance.
`dedupe_key` is source-provided when available; otherwise it is generated from
domain, object ID, alarm code, severity, and a short time bucket.

## 5. Fixture Contracts

`alarms.jsonl` contains one JSON object per line. Required fields are
`id`, `timestamp`, `severity`, `domain`, `object_id`, and `alarm_code`.

```json
{"id":"ran-001","timestamp":"2026-08-28T10:00:00Z","severity":"critical","domain":"ran","source_system":"ran-nms","object_id":"gnodeb-17","alarm_code":"LINK_DOWN","location":"site-42"}
```

`topology.json` is a directed edge list:

```json
{
  "edges": [
    ["gnodeb-17", "connected-via", "agg-sw-03"],
    ["agg-sw-03", "reaches", "amf-01"],
    ["amf-01", "supports", "ue-registration"]
  ]
}
```

`services.json` maps topology objects to services. `intents.json` maps service
objectives to KPIs and critical dependencies. KPI and ticket fixtures use the
`EvidenceEvent` fields plus source-specific attributes.

## 6. Normalization and Deduplication

`normalize.py` must:

1. Validate the required fields and reject malformed records with a structured
   reason; one bad event must not end the full batch.
2. Convert timestamp, severity aliases, domain aliases, and object identifiers
   to canonical form.
3. Preserve the original input record in a local run report, not gbrain.
4. Deduplicate exact source events by `(source_system, source_id)`.
5. Collapse repeated alarm occurrences by `dedupe_key` within the configured
   time window, retaining count, first seen, last seen, and max severity.

The worker writes one normalized alarm evidence page per unique source event in
the local proof of concept. A production version can retain raw data elsewhere
and write only references plus summaries to gbrain.

## 7. Topology and Service Resolution

`topology.py` loads the fixture graph into adjacency maps. For each alarm:

1. Find the alarm object in the topology graph.
2. Search outward and inward up to `CORRELATION_MAX_TOPOLOGY_HOPS`.
3. Resolve all reachable services from `services.json` and `supports` edges.
4. Return the shortest path between objects in a candidate group.

The local traversal is deterministic breadth-first search. It must return no
path rather than infer a relationship when topology is incomplete.

`identity.py` resolves every source-specific object ID before topology traversal.
It maps `(tenant_id, source_system, source_object_id)` to a canonical component
ID and rejects ambiguous mappings into a review queue. The worker records the
identity and topology versions on every candidate so later replay is
reproducible.

## 8. Candidate Formation and Scoring

`engine.py` first evaluates alarms whose timestamps are within the configured
absolute time distance. It must compare adjacent fixed buckets so an event near
a bucket boundary is not missed. Candidates require at least two distinct
normalized alarms and use either a shared service or a topology path between
alarm objects. It then attaches evidence when evidence shares a candidate
service and falls in the same correlation window.

The engine takes normalized events as its only input. It must not accept an
existing incident slug, hard-code a known AMF event, restrict domains, or use
an alarm-code allow-list. A raw event always receives one persisted outcome:
`standalone`, `candidate`, or membership in an `incident`. Standalone records
are re-evaluated on later runs when new evidence becomes available.

Initial scoring rules:

```text
+25  at least two alarms are in the same configured window
+25  at least two alarm objects have a topology path
+20  alarms resolve to at least one common service
+15  KPI evidence breaches a relevant target
+10  ticket, log, trace, or change evidence supports the candidate
+15  an affected service intent is violated
+10  one or more critical alarms are present
```

Score each signal once per candidate. Do not award the same signal per event;
otherwise an alarm storm can falsely inflate confidence.

Promotion gates apply in addition to score. An incident requires at least two
distinct alarms, one structural group (topology or common service), and one
impact/support group (KPI breach, ticket/log/trace support, or verified intent
breach). Time proximity and severity are not a sufficient impact group. A
critical or novel single alarm is a provisional candidate, never a confirmed
incident. For fixture runs, novelty is a first-seen
`(domain, source_system, alarm_code, object kind)` tuple; production uses a
bounded historical baseline.

Classification:

```text
score >= incident threshold: incident
candidate threshold <= score < incident threshold: candidate
otherwise: standalone
```

An isolated critical alarm receives a provisional candidate with a reason such
as `critical alarm awaiting topology or service evidence`, even if its score is
below the normal candidate threshold.

## 9. Intent Evaluation

`intents.py` returns intents whose `service_id` is in the candidate's affected
services. An intent is violated only when relevant KPI evidence crosses its
configured comparator and target. It contributes score and narrative context,
but an unmatched alarm remains available for later correlation.

Example:

```text
intent: ue-registration-availability
service: ue-registration
target KPI: registration-success-rate >= 99.5
observed KPI: 82.0
intent status: violated
```

## 10. Idempotency and Incident Identity

The incident identity is stable across worker retries:

```text
correlation_key = SHA-256(
  tenant ID +
  primary affected service +
  canonical correlation-window start
)
```

Alarm and evidence IDs are deliberately excluded from the identity. They form a
separate `evidence_set_hash` and `correlation_revision`; adding later evidence
must update the same incident rather than create another one. The local release
uses the service and fixed window start as its canonical anchor. A production
release adds merge/split handling through a persistent correlation index and
incident aliases.

The page slug is readable and deterministic:

```text
incidents/mobile-core/{primary-service}-{key-prefix}
```

The writer searches or reads by the canonical slug before writing. Legacy
`mobile-core/incidents/{primary-service}-{key-prefix}` aliases are written for
backward compatibility and registry lookups canonicalize either form. Existing
pages are updated with newer evidence and `last_correlated_at`; they are not
duplicated.

## 11. gbrain Write Adapter

`gbrain_writer.py` exposes:

```python
class GbrainWriter:
    def upsert_page(self, page: GraphPage) -> None: ...
    def ensure_link(self, source: str, relation: str, target: str) -> None: ...
    def upsert_candidate(self, candidate: CorrelationCandidate) -> str: ...
```

`GraphPage` includes slug, title, type, frontmatter, and compiled truth. The
adapter must map these concepts to the exact gbrain write-tool names and JSON
payload confirmed by the local MCP `tools/list` response. The adapter should
allow only known write tools, use an HTTP timeout, and retry only transient
transport or 5xx failures.

Required incident frontmatter:

```yaml
status: candidate | open | resolved
started_at: ISO-8601 UTC
correlation_key: stable hash
correlation_score: integer
correlation_reasons: list of strings
contributing_domains: list of strings
correlation_scope: intra-domain | inter-domain
intent_status: matched | violated | not_matched
last_correlated_at: ISO-8601 UTC
evidence_set_hash: hash of current linked evidence IDs
correlation_revision: monotonically increasing integer
```

Candidates and confirmed records use the existing `incident` page type, with
`status: candidate` or `status: open`; do not introduce a gbrain page type
without validating its support. Use the existing schema path:

```text
incident -> affects -> service
incident -> involves -> network-function
incident -> detected-by -> kpi-event -> measures -> kpi
incident -> has-hypothesis -> correlation hypothesis
correlation hypothesis -> supported-by -> evidence
```

Every normalized alarm, ticket, log, topology-path result, and intent evaluation
is an `evidence` page. Its frontmatter includes `evidence_kind`, `domain`,
`source_system`, `object_id`, `component_kind`, `observed_at`, and
`source_event_id`. The existing `network-function` page type represents an
involved component with `component_kind` and `domain` metadata; the Storyteller
uses domain-neutral language in presentation. Every incident records
`contributing_domains` and `correlation_scope`; the worker sets scope to
`intra-domain` for one domain and `inter-domain` for two or more.

The live MCP contract confirms `put_page` for upserts and `add_link` for link
creation. Use `link_source: correlation-worker` with every worker-created
edge. `add_link` is idempotent only after the writer checks the existing links;
the writer must call `get_links` or maintain a per-run link set before adding.

The worker validates the active mobile-core schema before its first write.
Existing pages and links are preserved; no migration or duplication is needed.

## 12. Storyteller Retrieval Changes

Extend `storyteller/knowledge/context.py` with:

```python
correlation_metadata: dict[str, Any]
```

Extend `storyteller/knowledge/mobile_core_knowledge.py` to:

- retrieve the correlation hypothesis through `has-hypothesis` and all source
  records through `supported-by`;
- read correlation metadata from incident and hypothesis frontmatter;
- preserve all page provenance.

The existing `network_functions` field must not become the generic home for
gNodeBs, transport switches, power equipment, or cloud assets in user-facing
language. Keep the storage field for compatibility, expose component metadata,
and render it as `involved components` in the Storyteller.

Extend the deterministic reasoning story model and templates to report:

```text
The incident combines RAN, transport, and mobile-core evidence.
The affected service is UE registration.
The correlation confidence is <score> with reasons <reasons>.
The UE registration availability intent is violated/not violated/not matched.
```

Do not present a correlation as confirmed root cause unless the hypothesis has
explicit supporting evidence and the existing root-cause rules permit it.

## 13. Frontend Incident Selection and Routing

`frontend/src/lib/api/qna.ts` and the storyteller conversation parser accept
both `incidents/mobile-core/...` and legacy `mobile-core/incidents/...` slugs.
The canonical slug is preferred for new generated incidents, while the legacy
form stays valid for old links and previously captured references.

`streamStorytellerMessage` should return the `incident_id` supplied by the ask
response in addition to rendering its answer. `useAgenticQna` stores this as
the active incident for the conversation. The action strip then builds its
prompts from that active slug rather than the current hard-coded AMF slug.

The first Storyteller request must contain an explicit slug, either typed by
the user or selected through a compact incident selector. Before one is set,
disable the action-strip incident actions or present the normal incident-input
state. This prevents an action from accidentally narrating a stale incident.

## 14. Incident Registry and Lifecycle API

Add a dedicated router under `/api/incidents`:

```text
GET  /api/incidents
GET  /api/incidents/{incident_id}
POST /api/incidents/{incident_id}/lifecycle
GET  /api/incidents/{incident_id}/audit
```

`GET /api/incidents` requires tenant-scoped filters and pagination:

```text
status, domain, service, severity, min_score, from, to, owner, cursor, limit
```

The lifecycle request contains `action`, `reason`, `owner`, and optional target
incident IDs for `merge` or `split`. Supported actions are `open`,
`acknowledge`, `assign`, `suppress`, `merge`, `split`, `resolve`, and `reopen`.
The service validates permitted state transitions, authorizes the caller, writes
an immutable audit event, and updates incident frontmatter plus registry state.

The registry is a query-optimized store. For the local MVP it can be SQLite;
production uses a tenant-scoped relational store. gbrain remains the source of
story evidence, while the registry provides fast queue filtering, lifecycle
state, ownership, feedback labels, and incident lineage.

The frontend adds an incident queue beside the existing conversation panel. A
row selects the active incident, shows its status/score/domains, and enables
contextual lifecycle actions. The action strip uses that selection.

## 15. Tests

### Unit Tests

- Timestamp, severity, and domain normalization.
- Duplicate and alarm-storm collapse behavior.
- Topology path and service resolution.
- Scoring once per evidence class.
- Intent matching and comparator evaluation.
- Stable correlation key and threshold classification.
- Critical and previously unseen alarms become provisional candidates without
  an intent match.
- Time-only or time-plus-severity groups cannot become incidents without both
  structural and impact/support evidence.
- Existing AMF fixtures remain regression tests only; an arbitrary new fixture
  set produces its own incident slug and outcome.
- Identity mapping ambiguity is routed to review and cannot create a false
  topology path.
- Lifecycle transitions, tenant isolation, merge/split lineage, and audit
  records are enforced.
- Critical and previously unseen alarms become provisional candidates without
  an intent match.
- Existing AMF fixtures remain regression tests only; an arbitrary new fixture
  set produces its own incident slug and outcome.

### Writer Tests

- MCP payload formatting with mocked HTTP response.
- Write-tool allow-list enforcement.
- Idempotent re-run updates instead of duplicates.
- Transient retry and permanent failure reporting.

### Integration Tests

- Run the fixture set against the local gbrain MCP.
- Verify one correlated incident, one candidate, and one standalone event.
- Fetch the incident through `MobileCoreKnowledge` and assert correlation and
  intent fields are populated.
- Call the existing ask API and assert the narrative includes contributing
  domains, affected service, evidence, score, and intent status.

## 16. Failure Handling

| Failure | Behavior |
| --- | --- |
| Invalid fixture event | Record validation error and continue other events. |
| Missing topology object | Retain as standalone or candidate; do not invent a path. |
| gbrain write failure | Retry transient errors; fail the run with a report if required writes remain incomplete. |
| Partial graph write | Re-run safely using the stable page slug and link checks. |
| No KPI/ticket support | Keep candidate or standalone based on deterministic score. |
| No intent match | Continue normal correlation; mark `intent_status: not_matched`. |
| Ambiguous source-to-asset mapping | Retain the event and place it in identity review; do not assume a topology path. |
| Registry unavailable | Continue durable event/outbox processing; retry incident-index projection. |

## 17. Production Scale Adapter

The correlation engine is input-agnostic. Keep `fixtures.py` for local tests and
add these adapters for production without changing normalization or scoring:

```text
StreamConsumer      receives alarms with at-least-once delivery.
RawEventRepository  persists immutable raw events and replay cursors.
WindowStateStore    stores bounded per-partition event-time windows.
CorrelationOutbox   persists idempotent gbrain write work.
OutboxDispatcher    rate-limits, retries, and marks graph writes complete.
```

The stream partition key is `tenant_id + region + service_or_topology_shard`.
The window state key is that partition plus the canonical correlation window.
Workers commit a stream offset only after raw-event persistence and outbox
creation succeed; gbrain availability must not block ingestion. The outbox uses
the correlation key and revision as its idempotency key.

The production writer stores raw-event references on gbrain evidence pages or
incident frontmatter instead of creating one graph page for every input alarm.
Only candidates, incidents, and high-value evidence summaries are written to
gbrain. A replay job can recompute a chosen time range after topology, intent,
or scoring policy changes.

## 18. Delivery Sequence

1. Validate the existing `mobile-core` schema and implement the exact gbrain
   writer adapter.
2. Add models, fixture parser, normalizer, and deterministic engine with unit
   tests.
3. Add topology, service, and intent resolution using local worker state and
   provenance-rich evidence pages.
4. Add idempotent page/link writing and a local dry-run report.
5. Extend Storyteller context and deterministic narrative with correlation
   metadata and domain-neutral component language.
6. Add the registry, lifecycle API, audit storage, incident queue, and
   active-incident action-strip integration.
7. Add live MCP and end-to-end incident API tests for both intra- and
   inter-domain cases.
8. Run arbitrary fixture sets, lifecycle actions, and replay checks; verify the
   resulting incident narratives and audit lineage.
