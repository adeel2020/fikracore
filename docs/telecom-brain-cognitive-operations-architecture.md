# Telecom Brain Cognitive Operations Architecture

This note consolidates the working model for building a telecom brain starting
from the mobile-core domain. The goal is not to prebuild everything. The goal is
to create a structure that can learn over time, improve context, and keep every
learning traceable.

## 1. Core Principle

The telecom brain should learn from operational situations and improve reusable
context assets.

```text
telemetry + topology/twin + domain context + knowledge assets
-> correlation
-> incident
-> story
-> learning note
-> proposed asset updates
-> reviewed/approved context improvement
```

Learning should not silently mutate trusted assets. It should create a learning
note and, when useful, propose new or updated assets.

## 2. Main Building Blocks

### Nautobot / Topology DB

Owns the actual topology and digital twin authority.

```text
devices, interfaces, links, sites, circuits, IPs, VRFs, VLANs,
physical/virtual resources, discovery confidence, lifecycle, ownership
```

### gbrain

Owns the semantic reasoning graph used by correlation, storytelling, and
learning. It stores projections, evidence references, incidents, assets, and
learning notes, but it is not the authoritative topology database.

### Grafana LGTM

Owns runtime telemetry evidence.

```text
metrics, logs, traces, alerts, dashboards, panels, query links
```

### Correlation Engine

Groups related alarms/evidence using time, service procedure relevance,
logical/domain relationships, telemetry support, and intent violation.

### Storyteller

Explains the incident deterministically from gbrain facts and links.

### Learning Loop

Creates learning notes from incidents, evidence, operator feedback, and asset
gaps. These notes propose improvements to assets and context.

## 3. Clean Namespace Split In gbrain

Use namespaces by responsibility, not by implementation convenience.

```text
knowledge/*
  reusable telecom knowledge

assets/*
  reusable context assets such as playbooks, runbooks, queries, dashboards,
  templates, knowledge articles, change request templates, and MCP tool notes

domains/*
  operator-specific semantic mobile-core model: networks, service procedures,
  intents, function roles, protocol/interface meaning

twin/*
  projection from Nautobot/topology authority, not the authority itself

grafana/*
  runtime telemetry evidence from Grafana LGTM

correlation/*
  correlation clusters, grouped signals, scores, decisions, and reasons

incidents/*
  operational incident lifecycle and canonical incident identity

storytelling/*
  generated story artifacts, story runs, and story build traces

learning/*
  learning notes, context gaps, proposed asset updates, and validated patterns
```

## 4. Mobile-Core Domain Structure

Mobile core is the domain. Do not model `signaling` as a domain. Signaling is
protocol/control-plane behavior inside mobile-core networks.

Recommended semantic structure:

```text
domains/mobile-core/networks/cs/...
domains/mobile-core/networks/ps/...
domains/mobile-core/networks/ims/...
domains/mobile-core/networks/lte/...
domains/mobile-core/networks/5gcn/...
domains/mobile-core/networks/vas/...
domains/mobile-core/networks/iot/...

domains/mobile-core/protocols/diameter
domains/mobile-core/protocols/sip
domains/mobile-core/protocols/gtp-c
domains/mobile-core/protocols/gtp-u
domains/mobile-core/protocols/nas
```

Intent belongs under the network area that owns the measured service procedure:

```text
domains/mobile-core/networks/lte/intents/4g-attach-sr
domains/mobile-core/networks/ps/intents/sgi-throughput
domains/mobile-core/networks/ims/intents/cssr
```

Service procedures live beside intents:

```text
domains/mobile-core/networks/lte/service-procedures/lte-attach
domains/mobile-core/networks/ps/service-procedures/sgi-data-forwarding
domains/mobile-core/networks/ims/service-procedures/voice-call-setup
```

## 5. Knowledge Vs Domain Model

Keep reusable telecom knowledge separate from the operator-specific domain
model.

```text
knowledge/mobile-core/procedures/lte-attach
```

Means the general telecom definition of LTE attach.

```text
domains/mobile-core/networks/lte/service-procedures/lte-attach
```

Means this operator's semantic service procedure instance.

Link them:

```text
domains/mobile-core/networks/lte/service-procedures/lte-attach
  instance-of -> knowledge/mobile-core/procedures/lte-attach
```

## 6. Assets

An asset is any reusable object that improves context.

Examples:

```text
assets/mobile-core/playbooks/lte-attach-failure-triage
assets/mobile-core/runbooks/check-hss-diameter-peer
assets/mobile-core/queries/promql/4g-attach-sr
assets/mobile-core/dashboards/lte-attach-health
assets/mobile-core/change-templates/mme-pool-scale-out
assets/mobile-core/knowledge-articles/lte-attach-procedure
assets/mobile-core/correlation-rules/hss-timeout-attach-drop
assets/mobile-core/mcp-tools/grafana-lgtm-querying
```

Assets are both source and destination of learning:

```text
asset as source -> provides context during correlation/storytelling
learning note -> records what was learned
asset update proposal -> suggests improvement
approved asset version -> becomes better source next time
```

If no asset exists for a new incident, the incident still proceeds. The learning
note should mark an asset gap and propose candidate assets.

## 7. Playbooks And Runbooks

Use playbook/runbook naming instead of SOP/MOP in the gbrain model.

```text
Playbook = broad decision guide for triage/investigation.
Runbook = executable steps for checks, validation, remediation, or rollback.
```

One playbook can recommend many runbooks:

```text
assets/mobile-core/playbooks/lte-attach-failure-triage
  recommends -> assets/mobile-core/runbooks/check-mme-health
  recommends -> assets/mobile-core/runbooks/check-hss-diameter-peer
  recommends -> assets/mobile-core/runbooks/check-s1-mme-connectivity
  recommends -> assets/mobile-core/runbooks/mme-drain-and-traffic-shift
```

## 8. FCAPS As The Learning Lens

Use FCAPS as a cross-cutting learning methodology, not as the top-level folder
for everything.

```text
F - Fault
C - Change / Configuration
A - Accounting
P - Performance
S - Security
```

FCAPS tags should enrich assets, incidents, evidence, and learning notes:

```yaml
fcaps:
  primary: fault
  related:
    - performance
    - change
```

Where FCAPS is used as a lens:

- Evidence classification: alarms map primarily to Fault, KPI breaches to
  Performance, change records to Change, usage/session-volume evidence to
  Accounting, and threat/anomaly records to Security.
- Correlation explanation: correlation decisions carry FCAPS reasons and gaps,
  so the system can explain whether a cluster is mostly a fault, a performance
  breach, a change side effect, or a security/accounting blind spot.
- Storytelling: incident stories can say which FCAPS views were observed and
  which were missing, without changing the deterministic story format.
- Learning notes: every learning note includes an FCAPS review, making the
  learned context auditable before it becomes trusted knowledge.
- Asset improvement: playbooks, runbooks, Grafana queries, dashboard panels,
  correlation rules, and change templates can be proposed or updated through
  the FCAPS review.
- Knowledge browsing: prebuilt mobile-core knowledge can be filtered through the
  same FCAPS lens to find all LTE attach Performance checks or all Change
  templates relevant to MME/HSS maintenance.

Every learning note should include an FCAPS review. This makes learning
structured and reveals missing context.

```yaml
fcaps_review:
  fault:
    findings:
      - HSS Diameter timeout alarm and MME attach rejects were present.
  change:
    findings:
      - No linked change request was found in the window.
    gaps:
      - Need change-feed integration.
  accounting:
    findings:
      - Subscriber attach volume was not available.
    gaps:
      - Need usage/session-volume evidence.
  performance:
    findings:
      - 4G Attach SR breached target.
  security:
    findings:
      - No security evidence checked.
    gaps:
      - Need signaling anomaly source.
```

## 9. Change Request As First-Class Context

FCAPS-C should include Change, not only static configuration.

Use dedicated change assets:

```text
assets/mobile-core/change-requests/crq-scale-mme-pool-20260901
assets/mobile-core/change-templates/mme-pool-scale-out
```

Change requests can be proposed from learning, linked to incidents, and
validated by performance recovery.

## 10. Learning Pivot

The pivot of learning should not be intent alone.

Use the simpler question:

```text
What situation did we learn from?
```

For mobile-core operations, that situation is usually:

```text
area + service procedure + problem + suspected/confirmed cause + evidence
```

Intent is a lens on the situation, not the only pivot.

New intents can be discovered later, but the first learning outputs should be:

```text
new correlation pattern
new failure pattern
better evidence weighting
better query/dashboard
better playbook/runbook recommendation
new candidate asset
new candidate intent when repeated incidents expose an untracked objective
```

## 11. Learning Note Template

A learning note should be readable by humans and structured for machines.

```yaml
type: learning_note
title: LTE attach degradation linked to HSS Diameter timeouts
status: needs_review
confidence: 0.72

summary: >
  This is the first captured pattern where LTE attach success degraded while
  HSS Diameter timeouts and MME attach rejects were present in the same
  investigation window. No approved playbook, runbook, or reusable Grafana
  query was linked at the time of analysis, so this note proposes new context
  assets for future incidents.

learned_from:
  incidents:
    - incidents/mobile-core/lte-attach-54db6ef325fbf758
  evidence:
    - grafana/alerts/grafana-alert-attach-hss-001
    - grafana/alerts/grafana-alert-attach-mme-001
    - grafana/metrics/grafana-prom-attach-001

context:
  domain: mobile-core
  network_area: lte
  service_procedure: lte-attach
  intent: 4g-attach-sr
  fcaps:
    primary: fault
    related:
      - performance
      - change

observed_problem:
  description: Attach success rate dropped below the service intent target.
  observed_signals:
    - MME attach reject rate increased.
    - HSS Diameter ULR timeouts increased.
    - 4G Attach SR breached the configured threshold.

current_interpretation:
  suspected_cause: HSS Diameter timeout contributing to LTE attach failures.
  why_it_matters: >
    LTE attach depends on timely subscriber authentication and location update
    responses. When HSS/Diameter responses are delayed or lost, MME attach
    processing can reject or time out subscriber attach attempts.

asset_gap:
  missing:
    - LTE attach failure triage playbook
    - HSS Diameter peer check runbook
    - reusable PromQL query for 4G Attach SR
    - dashboard panel for attach failure evidence

proposed_assets:
  playbooks:
    - assets/mobile-core/playbooks/lte-attach-failure-triage
  runbooks:
    - assets/mobile-core/runbooks/check-hss-diameter-peer
  queries:
    - assets/mobile-core/queries/promql/4g-attach-sr
  dashboards:
    - assets/mobile-core/dashboards/lte-attach-health

review:
  required: true
  reviewer_group: mobile-core-operations
  decision: pending
```

## 12. End-To-End Example

```text
Grafana alert: HSS Diameter timeouts
Grafana KPI: 4G Attach SR breached
Twin object: hss-01 from Nautobot
Domain model: LTE attach depends on MME and HSS
Knowledge: LTE attach procedure definition
Correlation: grouped MME, HSS, RAN, KPI, and log evidence
Incident: incidents/mobile-core/lte-attach-54db6ef325fbf758
Storytelling: generated deterministic story and build trace
Learning: note says this pattern may need a playbook, runbook, query, dashboard
Review: operator validates or rejects the learning
Asset update: approved context improves the next incident
```

## 13. Plain-English Summary

```text
Grafana tells us what happened.
Nautobot tells us where it happened.
Domains tell us what it affects in our mobile-core model.
Knowledge tells us what it means in telecom terms.
Assets provide reusable context.
Correlation groups the evidence.
Incidents track the operational case.
Storytelling explains the case.
Learning notes remember what we learned.
Asset updates improve future context.
FCAPS keeps learning structured and auditable.
```
