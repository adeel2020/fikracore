# Industry-Grade Data StoryTeller And VisualExplanationService Implementation Plan

## Purpose

Upgrade the current Data StoryTeller from a working POC into a professional NOC incident narrator. The target behavior is incident-agnostic, evidence-backed, audience-aware, voice-safe, and visually explainable.

The solution should preserve the current TelecomBrainEngine design:

```text
Evidence Sources
  gbrain + Grafana/LGTM + future MCP connectors
        ↓
Incident-Agnostic Retrieval
        ↓
Evidence Validation + Grading
        ↓
IncidentNarrative
        ↓
Written Story + Spoken Brief + VisualExplanation
        ↓
Mark Voice + Data Storyteller UI + HUD / Drawer / Investigation Mode
```

## Implementation Status

Last updated: 2026-09-05

- Phases 1-11 are implemented as a tested first pass.
- Phase 12 is implemented as a first production pass:
  - inline visual explanation is implemented in the Data Storyteller chat response
  - expandable evidence drawer is implemented inside the story card
  - investigation mini-canvas is implemented for graphable widget payloads
  - a dedicated investigation workspace is available from Mark's response card
  - the workspace exposes service impact, timeline, recommended actions, supporting claims, confidence, FCAPS tags, and provenance when present
- Phase 13 is implemented as a first production pass:
  - Mark receives written reply, curated spoken reply, narrative, visual explanation, and telemetry evidence as separate per-turn payloads
  - Mark HUD highlights the primary visual orb while a spoken brief is queued or playing
  - browser replay reuses the curated spoken brief while keeping the full technical answer on screen
  - live voice WebSocket responses carry presentation payloads and generation IDs
  - live voice interruption clears stale audio and prevents stale responses from replacing the current answer
- Phase 14 is implemented as a first pass:
  - golden executive, NOC, customer, spoken, and visual contract references are stored under `docs/storyteller-references/golden/`
  - regression tests compare deterministic output against those references
  - the capture script now stores `spoken_answer`, `narrative`, and `visual_explanation`
- Phase 15 is implemented as a first-pass validation matrix:
  - synthetic E2E tests cover intra-domain mobile core, inter-domain RAN/transport/core, IMS voice setup, cloud/platform, power/site, customer weak signal, contradiction/missing evidence, and lifecycle states
  - focused storyteller, telecom-brain, registry, golden, and frontend affected-file validations pass
  - MCP Hub/Grafana evidence hardening is implemented with tool discovery, HTTP/stdio hub support, streamable HTTP session initialization, and alert/metric/log/trace/dashboard normalization
  - local LGTM + Grafana MCP stack scaffolding is added under `deploy/monitoring/lgtm/`
- Phase 16 is implemented and live-validated:
  - local LGTM telemetry seed and MCP Hub validation scripts are added under `scripts/`
  - LGTM accepted synthetic OTLP metrics and logs for `voice-call-setup`, `sgi-data`, and `lte-attach`
  - Mark's MCP Hub discovered Grafana tools and called `query_prometheus` plus `query_loki_logs`
  - validation artifacts are stored under `docs/storyteller-references/lgtm-validation-*.json`
  - storyteller live telemetry enrichment is available on demand through `include_live_telemetry`
- Remaining production work:
  - sentence-level or claim-level audio-to-visual cue timing
  - richer NOC/RCA investigation graph interactions such as pan/zoom, filtering, and side-by-side telemetry panels
  - more real gbrain incident pages
  - production Grafana dashboard/alert ingestion beyond synthetic seed data

## Design Principles

- Data StoryTeller is the reasoning and narrative authority.
- VisualExplanationService explains the same reasoning visually; it does not perform independent RCA.
- Mark is the voice/conversation interface on top of the engine stack.
- gbrain, Grafana/LGTM, and future MCP connectors are evidence/context sources.
- Stored graph pages and telemetry are context, not text to read directly.
- Written output can be technical and traceable.
- Spoken output must be concise, professional, and free of raw slugs, hashes, markdown syntax, tables, punctuation artifacts, and long timestamps.
- FCAPS remains a cross-cutting lens for learning, evidence classification, operational gaps, and post-incident improvement.

## Phase 1: Professional Incident Narrative Contract

Create a canonical `IncidentNarrative` contract with:

- incident context
- lifecycle state
- impact summary
- causal chain
- evidence claims
- confidence
- provenance
- audience
- written story
- spoken brief
- next questions/actions
- visual explanation hints

Acceptance criteria:

- The contract is incident-agnostic.
- It works for intra-domain and inter-domain incidents.
- It can be produced from existing `IncidentStory` objects.
- Every major claim can carry confidence and provenance.

## Phase 1A: Local LGTM Stack And MCP Hub Connectivity

Make a local LGTM environment available before live telemetry validation.

Provide:

- local Grafana/LGTM backend for metrics, logs, traces, dashboards, and alerts
- Grafana MCP server connected to that backend
- MCP Hub configuration using `GRAFANA_MCP_URL`
- read-only MCP mode by default
- verification commands for Grafana health, MCP `tools/list`, and Mark connector status

Acceptance criteria:

- LGTM starts locally with Docker Compose.
- Grafana MCP exposes tools through `http://localhost:3132/mcp`.
- Mark's MCP Hub reports the Grafana connector as configured.
- TelecomBrainEngine can request Grafana evidence without bypassing MCP Hub.

## Phase 2: Incident-Agnostic Retrieval

Harden incident resolution so the storyteller can narrate any valid incident with graph context.

Support:

- `incidents/mobile-core/{id}`
- `mobile-core/incidents/{id}`
- plain incident ID with contextual namespace
- aliases
- registry lookup
- correlation group lookup
- candidate incident lookup

Acceptance criteria:

- No hardcoded sample incident is required.
- A valid incident slug should not return "needs an incident ID".
- Not-found responses explain what lookup paths were attempted.

## Phase 3: Evidence Validation And Grading

Normalize evidence into graded claims:

- `confirmed_fact`
- `inferred_relation`
- `weak_signal`
- `missing_evidence`
- `contradiction`

Each claim must include:

- claim ID
- statement
- grade
- confidence
- source
- provenance references
- related domain
- related service procedure
- related topology/service/object references

Acceptance criteria:

- Major story sections cite supporting claim IDs.
- Weak or missing evidence is visible, not hidden.
- Contradictions are surfaced explicitly.

## Phase 4: Lifecycle-Aware Storytelling

Support incident lifecycle states:

- `candidate`
- `open`
- `acknowledged`
- `mitigated`
- `resolved`
- `reopened`
- `merged`
- `suppressed`

Acceptance criteria:

- Story tone changes by lifecycle state.
- Candidate incidents ask validation questions.
- Resolved incidents focus on cause, fix, recovery, and prevention.
- Suppressed and merged incidents do not read like active outages.

## Phase 5: Audience-Specific Formatters

Implement audience profiles:

- executive summary
- NOC engineer brief
- RCA lead brief
- customer/stakeholder update
- post-incident review

Acceptance criteria:

- The same `IncidentNarrative` can produce all audience views.
- Executive output is ordered by decision relevance.
- NOC/RCA output keeps technical depth.
- Customer output avoids internal IDs and excessive implementation detail.

## Phase 6: Written Story Renderer

Default written story order:

1. Executive summary
2. Current state
3. Impact
4. Leading hypothesis / RCA status
5. Evidence and confidence
6. Timeline
7. Actions taken
8. Recommended next actions
9. Open questions
10. Provenance

Acceptance criteria:

- Written output is deterministic.
- Markdown is allowed for screen rendering.
- Confidence and provenance are visible for major claims.

## Phase 7: Spoken Brief Renderer

Create a voice-safe spoken brief from the narrative contract.

Acceptance criteria:

- No raw slugs, hashes, markdown, table syntax, punctuation artifacts, or long timestamps.
- Mark speaks 1-3 crisp sentences by default.
- Mark can say "Details are on your console" when deeper evidence is displayed.

## Phase 8: Next Best Questions And Actions

Generate:

- diagnostic questions
- remediation actions
- missing evidence requests
- approval-required actions
- stakeholder update suggestions

Acceptance criteria:

- Actions are ranked by urgency, confidence, lifecycle state, and approval requirement.
- Missing evidence becomes actionable.

## Phase 9: Multi-Domain Evidence Normalization

Support domains:

- RAN
- transport
- mobile core
- IMS
- cloud/platform
- power/site
- customer impact

Acceptance criteria:

- The story explains why evidence was grouped.
- The story distinguishes intra-domain and inter-domain incidents.
- Domain relationships are traceable through service procedures, topology, KPIs, alarms, tickets, and customer impact.

## Phase 10: Grafana/LGTM MCP Evidence Provider

Add Grafana/LGTM evidence through MCP Hub.

Evidence types:

- alert states
- Prometheus metric snapshots
- Loki log excerpts
- Tempo trace summaries
- dashboard/panel references

## Phase 16: Live LGTM Evidence Validation

Validate the operational telemetry path against the local LGTM stack.

Provide:

- OTLP seed script for telecom KPIs and logs
- MCP Hub validation script for Grafana tool discovery and live tool calls
- JSON validation artifact for review and regression capture
- commands that prove all telemetry access flows through Mark's MCP Hub

Acceptance criteria:

- Local LGTM accepts seeded telecom metrics and logs.
- Grafana MCP exposes tools through Mark's MCP Hub.
- Metrics/log tool calls can be made through `/api/jarvis/connectors/grafana/call`.
- Connector traces show `grafana` calls with `status=ok`.
- Storyteller validation can reference Grafana/LGTM provenance alongside gbrain incident context.

Acceptance criteria:

- Grafana evidence is normalized into claims.
- Raw telemetry is not dumped directly into the story.
- MCP unavailable fallback is graceful.

## Phase 11: VisualExplanationService Contract

Create `VisualExplanationService` that consumes `IncidentNarrative` and emits structured visual payloads:

- timeline
- causal chain
- domain impact map
- evidence confidence matrix
- KPI trend
- alarm correlation graph
- topology/service impact view
- missing evidence panel
- next-action decision tree

Each visual widget must include:

- widget ID
- title
- type
- data
- confidence
- provenance
- supported claim IDs

Acceptance criteria:

- Visuals are generated from claims, not raw markdown.
- Every visual is traceable back to narrative evidence.

## Phase 12: Layered Visual Experience

Implement four presentation modes:

- inline mini visuals inside the story
- floating HUD highlights while Mark speaks
- expandable side drawer for evidence drill-down
- full investigation mode for NOC/RCA analysis

Acceptance criteria:

- Pop-ups are not the only interaction model.
- The operator can stay in story context while drilling into evidence.
- Deep investigation has a dedicated mode.

## Phase 13: Frontend Integration

Integrate with:

- Data Storyteller action strip
- Mark HUD
- chat response card
- voice replay
- visual drawer
- investigation canvas

Acceptance criteria:

- Chat shows full written story.
- Mark speaks the spoken brief.
- Visual widgets render from structured payloads.
- The UI can handle missing visuals gracefully.

## Phase 14: Golden Reference Outputs

Store deterministic examples for:

- executive summary
- NOC engineer brief
- RCA lead brief
- customer update
- post-incident review
- spoken brief
- visual payload

Acceptance criteria:

- Golden files prevent regression to robotic responses.
- Story quality can be reviewed by comparing artifacts.

## Phase 15: End-To-End Validation

Test incidents covering:

- intra-domain mobile core issue
- inter-domain RAN + transport + core issue
- IMS voice setup issue
- cloud/platform issue
- power/site issue
- customer-impact-only weak signal
- contradiction/missing evidence
- resolved/reopened/merged/suppressed states

Acceptance criteria:

- gbrain retrieval works.
- Grafana MCP evidence works when available.
- Storyteller renders audience-specific outputs.
- Mark speaks clean summaries.
- Frontend visual widgets render.
- Investigation mode opens from a story claim.

## Initial Engineering Sequence

1. Add `IncidentNarrative`, `EvidenceClaim`, and visual explanation models.
2. Add adapter from existing `IncidentStory` to `IncidentNarrative`.
3. Add deterministic audience and spoken renderers.
4. Add `VisualExplanationService` with initial widget builders.
5. Add tests for narrative conversion, spoken safety, and visual payloads.
6. Wire `StorytellingService` to include narrative and visual payload data.
7. Extend frontend to render inline visuals and preserve full/spoken split.
8. Add Grafana/LGTM evidence provider through MCP Hub.
9. Add golden reference outputs and E2E tests.
