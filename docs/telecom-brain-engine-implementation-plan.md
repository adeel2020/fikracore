# TelecomBrainEngine Implementation Plan

This plan reflects the current implementation in `/Users/adeelarshad/kagent` after the engine-stack scaffolding cleanup and normalization.

The architecture rule remains unchanged: **TelecomBrainEngine is one engine with internal services, not multiple telecom engines**. Mark/Jarvis stays the human-facing assistant layer. External systems are accessed through MCP Hub first. `capability_registry` is the source of truth for engine, service, connector, and skill metadata.

## Current Architecture

```text
Mark / Jarvis
  -> engine_stack.router
  -> engine_stack.engines.telecom_brain.TelecomBrainEngine
      -> internal telecom services
      -> mcp_hub
      -> connectors / MCP servers
```

Canonical implementation path:

```text
/Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/
  __init__.py
  models.py
  engine_context.py
  engine.py

  services/
    __init__.py
    base.py
    storytelling.py
    correlation.py
    rca.py
    grafana_evidence.py
    telemetry_evidence.py
    intent.py
    topology.py
    incident_registry.py
    fcaps_learning.py
    narrative.py
    playbook_runbook.py
    remediation_advisory.py
    network_health.py
    visual_explanation.py

  tests/
    test_models.py
    test_base_service_routing.py
    test_storytelling_service.py
    test_incident_registry_service.py
    test_correlation_service.py
    test_grafana_evidence.py
    test_rca_service.py
    test_remaining_services.py
    test_compatibility_bridge.py
```

Compatibility-only package:

```text
/Users/adeelarshad/kagent/services/agents/src/engine_stack/telecom_brain/
```

The old `engine_stack.telecom_brain.*` path is intentionally retained as import shims. It should not contain independent implementation logic. Runtime callers should prefer `engine_stack.engines.telecom_brain.*`.

Jarvis compatibility bridge:

```text
/Users/adeelarshad/kagent/services/agents/src/jarvis/superpowers/telecom_brain.py
```

This bridge preserves existing Jarvis behavior while delegating TelecomBrain work to:

```python
engine_stack.engines.telecom_brain.TelecomBrainEngine
```

## Current Scaffolding

The following normalized scaffolding is now part of the implementation and must be preserved in future phases.

```text
/Users/adeelarshad/kagent/services/agents/src/
  assistant/
    mark/
      __init__.py
      core.py
      ui_adapter.py
      voice/
        __init__.py
      persona/
        __init__.py
      conversation/
        __init__.py

  engine_stack/
    __init__.py
    router.py
    policy.py
    trace.py
    registry/
      __init__.py

    engines/
      __init__.py
      base.py
      telecom_brain/
      knowledge_base/
      collaboration/
      calendar/
      codex_engineering/
      automation/

    telecom_brain/
      compatibility shims only

    tests/
      test_normalized_structure.py

  mcp_hub/
    __init__.py
    hub.py
    stdio.py
    http.py
    policy.py
    trace.py

  connectors/
    __init__.py
    base.py
    gbrain/
    grafana/
    gmail/
    whatsapp/
    microsoft_teams/
    microsoft_office/
    google_calendar/
    codex/
    metadata_db/
    vector_db/

  capability_registry/
    engines/
    services/
    connectors/
    skills/
    schemas/
```

The non-telecom engine packages currently exist as registry-backed shells:

```text
engine_stack/engines/knowledge_base/
engine_stack/engines/collaboration/
engine_stack/engines/calendar/
engine_stack/engines/codex_engineering/
engine_stack/engines/automation/
```

They expose manifests from `capability_registry` and should be migrated to concrete engine implementations in later work. They are intentionally not duplicate Jarvis superpowers.

## Hard Constraints

- Mark is only the human-facing assistant layer.
- TelecomBrainEngine is one engine with internal services.
- `engine_stack/engines/telecom_brain/` is the canonical implementation location.
- `engine_stack/telecom_brain/` is compatibility-only.
- `jarvis/superpowers/telecom_brain.py` is a compatibility bridge.
- Existing `/api/jarvis/*` endpoints must continue working.
- Existing incident storyteller endpoints must continue working.
- `capability_registry` is the source of truth for metadata.
- `mcp_hub` is the single outbound MCP access layer.
- gbrain and Grafana access must go through MCP Hub first.
- Existing `correlation/` and `storyteller/` modules are wrapped behind services before rewrite/migration.
- Intent is relevance scoring and prioritization, not a hard filter.
- Unknown or unmatched alarms must be retained as standalone observations or candidates.
- gbrain stores semantic projections and context, not raw telemetry or every raw source record.
- FCAPS is used specifically as a learning and enrichment lens.

## Implemented Phases

### Phase 1: Engine Package, Models, Context, and Base Service

Status: implemented.

Implemented in:

```text
engine_stack/engines/telecom_brain/models.py
engine_stack/engines/telecom_brain/engine_context.py
engine_stack/engines/telecom_brain/engine.py
engine_stack/engines/telecom_brain/services/base.py
```

Models:

```text
TelecomRequest
TelecomResult
TelecomTrace
IncidentRef
AlarmEvidence
KpiEvidence
TopologyNode
ServiceProcedure
IntentViolation
FCAPSClassification
RCAHypothesis
RecommendedAction
EvidenceGrade
IncidentLifecycleState
StoryAudience
VisualWidgetType
ProvenanceRef
EvidenceClaim
NarrativeAction
IncidentNarrative
VisualWidget
VisualExplanation
```

The service contract is:

```python
class TelecomService:
    id: str

    async def can_handle(self, request: TelecomRequest) -> float:
        ...

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        ...
```

### Phase 2: Service Router

Status: implemented.

`ServiceRouter` uses `can_handle()` confidence scores. If no service meets the minimum confidence threshold, the request is retained as a standalone telecom observation.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/base.py
```

### Phase 3: Storytelling Service

Status: implemented.

`StorytellingService` wraps existing storyteller components:

```text
storyteller.conversation.ConversationService
storyteller.knowledge.MobileCoreKnowledge
storyteller.knowledge.GbrainClient
```

The service keeps storyteller behavior available behind the TelecomBrainEngine boundary.
It also uses the professional narrative/visual explanation contract already present in the implementation:

```text
engine_stack/engines/telecom_brain/services/narrative.py
engine_stack/engines/telecom_brain/services/visual_explanation.py
```

These modules produce audience-aware incident narratives, spoken briefs, visual widgets, evidence-grade claims, timelines, causal chains, and next-action structures. They are consumed by the storyteller conversation API and voice/realtime paths.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/storytelling.py
engine_stack/engines/telecom_brain/services/narrative.py
engine_stack/engines/telecom_brain/services/visual_explanation.py
```

### Phase 4: Incident Registry Service

Status: implemented.

`IncidentRegistryService` wraps the existing correlation incident registry and returns incident references, active incident lists, and candidate context. gbrain is used for semantic context where appropriate, not as raw incident storage.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/incident_registry.py
correlation/registry.py
```

### Phase 5: Correlation Service

Status: implemented.

`CorrelationService` wraps the existing correlation engine. It translates TelecomBrain request evidence into correlation inputs and preserves unmatched or unknown alarms.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/correlation.py
correlation/engine.py
```

Correlation scoring uses:

```text
time proximity
service procedure
topology path
location/site
KPI breach
intent signal
severity
novel alarm signature
change/customer/ticket context when present
```

Intent is used as relevance and prioritization signal only.

### Phase 6: RCA Service

Status: implemented.

`RCAService` builds RCA triage on top of correlation and storyteller evidence. It must not mark root cause as confirmed unless the wrapped evidence says so.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/rca.py
```

Output includes:

```text
candidate causes
supporting evidence
evidence against
confidence
missing proof
next diagnostic step
```

### Phase 7: Telemetry Evidence Service

Status: implemented.

`TelemetryEvidenceService` routes Grafana access through MCP Hub.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/telemetry_evidence.py
engine_stack/engines/telecom_brain/services/grafana_evidence.py
mcp_hub/hub.py
mcp_hub/http.py
mcp_hub/stdio.py
mcp_hub/policy.py
mcp_hub/trace.py
connectors/grafana/
```

`GrafanaEvidenceProvider` is the current provider-level scaffold for retrieving Grafana-backed evidence through the TelecomBrain service boundary. It must continue to route external access through MCP Hub.

Initial MCP tool intents:

```text
query_kpi_window
query_alarm_window
get_service_dashboard_evidence
get_component_health
```

Raw telemetry stays in Grafana/LGTM/source stores. Only compact semantic projections should go to gbrain.

### Phase 8: Intent Service

Status: implemented.

`IntentService` performs relevance scoring and intent-violation enrichment without filtering out unmatched alarms.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/intent.py
```

Initial intents:

```text
LTE attach SR
UE registration
VoLTE CSSR
SGi throughput
IMS registration
data session establishment
```

### Phase 9: Topology Service

Status: implemented.

`TopologyService` starts with logical topology and service-procedure dependency context. Future work can replace or supplement fixture-backed topology with Nautobot or another topology inventory.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/topology.py
correlation/fixtures/
connectors/gbrain/
```

gbrain stores semantic topology projections and incident-relevant relationships, not the authoritative topology database.

### Phase 10: FCAPS Learning Service

Status: implemented.

`FCAPSLearningService` uses FCAPS as a learning and enrichment lens.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/fcaps_learning.py
```

Learning candidates include:

```text
missing playbook
missing runbook
missing Grafana query
missing dashboard panel
missing topology relation
missing intent mapping
```

### Phase 11: Playbook / Runbook Service

Status: implemented.

`PlaybookRunbookService` recommends triage guides and executable procedures while distinguishing playbooks from runbooks.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/playbook_runbook.py
```

### Phase 12: Remediation Advisory Service

Status: implemented.

`RemediationAdvisoryService` produces safe advisory recommendations:

```text
diagnostic next step
pre-check
rollback suggestion
capacity action
escalation owner
MOP candidate
```

Execution remains approval-gated.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/remediation_advisory.py
```

### Phase 13: Network Health Service

Status: implemented.

`NetworkHealthService` supports general telecom status queries such as active incidents, degraded KPIs, intent violations, and alarm pressure.

Implemented in:

```text
engine_stack/engines/telecom_brain/services/network_health.py
```

### Phase 14: Compatibility and Normalized Scaffolding

Status: implemented.

Compatibility surfaces:

```text
jarvis/superpowers/telecom_brain.py
engine_stack/telecom_brain/
```

Normalized scaffolding:

```text
engine_stack/router.py
engine_stack/policy.py
engine_stack/trace.py
engine_stack/registry/
engine_stack/engines/
mcp_hub/http.py
mcp_hub/stdio.py
mcp_hub/policy.py
mcp_hub/trace.py
connectors/
assistant/mark/voice/
assistant/mark/persona/
assistant/mark/conversation/
assistant/mark/ui_adapter.py
```

The old TelecomBrain path is a compatibility bridge only. The canonical implementation is under `engine_stack/engines/telecom_brain/`.

### Phase 15: Tests and Graphify

Status: implemented.

Current focused tests cover:

```text
models
base service routing
storytelling service
incident registry service
correlation service
Grafana evidence provider
RCA service
remaining TelecomBrain services
compatibility bridge
normalized engine-stack structure
capability registry
MCP Hub
existing storyteller conversation/reasoning APIs
```

Latest focused verification:

```text
142 passed, 1 warning
```

Latest Graphify update:

```text
12220 nodes
25108 edges
754 communities
```

`graph.html` may be skipped by Graphify because the graph exceeds the default HTML visualization node limit. `graphify-out/graph.json` and `GRAPH_REPORT.md` should still be updated.

## Remaining Work

The implementation is now scaffolded and tested, but these follow-up phases remain useful.

### Phase 16: Reduce Compatibility Surface

Keep `engine_stack/telecom_brain/` as long as old imports exist. Once all callers use `engine_stack.engines.telecom_brain`, this package can be removed in a deliberate cleanup.

Do not remove it until import search and tests prove there are no direct callers.

### Phase 17: Migrate Other Registered Engines

The following engines are currently registry-backed shells:

```text
knowledge_base
collaboration
calendar
codex_engineering
automation
```

Each should eventually receive a concrete implementation package under:

```text
engine_stack/engines/<engine_id>/
```

Jarvis superpowers should remain compatibility or UI-facing adapters, not the canonical engine implementations.

### Phase 18: Deepen MCP Hub Transports

`mcp_hub/hub.py` owns the current implementation. The split modules exist and should be expanded carefully:

```text
mcp_hub/http.py
mcp_hub/stdio.py
mcp_hub/policy.py
mcp_hub/trace.py
```

Future work should move transport-specific internals from `hub.py` into these modules without changing the public MCP Hub contract.

### Phase 19: Harden Story and Evidence Presentation Contracts

The current implementation includes these scaffolds:

```text
StoryAudience
EvidenceGrade
IncidentLifecycleState
IncidentNarrative
VisualExplanation
VisualWidget
GrafanaEvidenceProvider
VisualExplanationService
narrative_from_story
```

Future work should harden these contracts with stable API schemas and end-to-end tests for written story, spoken brief, visual explanation, and Grafana-backed evidence.

### Phase 20: Harden Connector Packages

Connector packages currently describe integration ownership and route calls through MCP Hub:

```text
connectors/<connector_id>/
```

Future work can add typed tool argument/result helpers per connector, but connector packages must not bypass MCP Hub.

### Phase 21: Productionize Evidence and Storage

Replace fixture-backed or static assets with production sources behind service boundaries:

```text
Grafana MCP for telemetry evidence
gbrain MCP for semantic projections/context
topology inventory for dependency state
metadata DB for operational indexes where needed
vector DB for retrieval where needed
```

Keep raw telemetry and raw source records in their source systems unless a compact semantic projection is intentionally written.

## Recommended Build Order From Here

```text
1. Keep current tests green while callers move to engine_stack.engines.telecom_brain
2. Migrate any remaining direct imports away from engine_stack.telecom_brain
3. Expand MCP Hub split modules without changing public behavior
4. Add typed connector helpers that still call through MCP Hub
5. Harden narrative, visual explanation, and Grafana evidence contracts
6. Convert registry-backed engine shells into concrete engines one at a time
7. Replace fixture-backed telecom evidence with production MCP-backed sources
8. Broaden end-to-end tests for /api/jarvis/* and incident storyteller routes
9. Re-run graphify update after each code change
```

This keeps the existing storyteller and Jarvis behavior working while TelecomBrainEngine continues to mature as the canonical telecom cognition layer.
