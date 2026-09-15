# Simulator Implementation Prompt

## Purpose

Implement a local hypothesis-validation Simulator inside the existing `kagent` codebase.

The Simulator should validate whether causal hypothesis testing improves telecom incident reasoning before expanding into production-scale learning, automation, or digital twin work.

This is not a separate product, repository, or top-level engine. It is an internal capability of the existing `TelecomBrainEngine`.

## Current Naming Rules

Keep all current code and configuration names unchanged.

Use:

```text
TelecomBrainEngine
telecom_brain
assistant/mark
gbrain
GBRAIN_MCP_URL
GBRAIN_MCP_TOKEN
```

Do not rename environment variables.

Do not rename the gbrain connector.

Do not rename `Mark` or `TelecomBrainEngine` as part of this implementation.

The new capability name is simply:

```text
Simulator
```

## Architecture Fit

The Simulator belongs under the existing `TelecomBrainEngine`.

Target flow:

```text
Mark Voice Assistant
  -> engine_stack.router
  -> TelecomBrainEngine
      -> SimulatorService
      -> CorrelationService
      -> RCAService
      -> StorytellingService
      -> Customer Ticket Journey
      -> VisualExplanationService
      -> MCP Hub
          -> gbrain MCP
          -> Grafana/LGTM MCP
          -> Codex MCP
```

Mark should not own simulator logic.

Storyteller should not own simulator logic.

Customer Ticket Journey should not own simulator logic.

The Simulator produces structured reasoning output that those services can consume.

## Canonical Implementation Location

Implement under:

```text
services/agents/src/engine_stack/engines/telecom_brain/
```

Recommended structure:

```text
services/agents/src/engine_stack/engines/telecom_brain/
  services/
    simulator.py

  simulator/
    __init__.py
    contracts.py
    world.py
    evidence.py
    operational_graph.py
    hypotheses.py
    investigator.py
    discovery.py
    evaluator.py
    runner.py
    fixtures/
      s1_ps_fault.yaml
      s2_transport_ps.yaml
      s3_noisy_transport_ps.yaml
      s4_missing_relationship.yaml
      s5_unresolved.yaml

  tests/
    test_simulator_contracts.py
    test_simulator_h1.py
    test_simulator_h2.py
```

Do not create:

```text
fikracore/
zaki/
fikra_simulator/
hypothesis_validation/
```

Those names are intentionally not part of this implementation.

## Integration With Existing Services

The Simulator should integrate with the existing engine stack by returning structured results through `TelecomResult`.

Expected consumers:

```text
StorytellingService
RCAService
CorrelationService
VisualExplanationService
Customer Ticket Journey
Mark Voice Assistant
```

The Simulator should provide:

```text
full_answer
spoken_answer
visual_explanation
reasoning_trace
evidence_summary
next_best_actions
ticket_update
story_context
```

The full answer is for UI and technical inspection.

The spoken answer is for Mark voice and must be concise, conversational, and free of raw technical artifacts.

## Voice Output Rule

Mark voice output must not read:

```text
raw slugs
UUIDs
long incident IDs
raw evidence IDs
markdown syntax
tables
punctuation artifacts
unnecessary timestamps
code-like field names
```

Preferred spoken style:

```text
The strongest explanation is transport-side degradation causing packet loss toward the UPF. The packet-core fault hypothesis was weakened because UPF resources and PFCP health remained normal. I have shown the detailed evidence trace on your screen.
```

## Storyteller Integration

The existing Storyteller should consume Simulator output as structured context.

Storyteller should use:

```text
supported hypotheses
falsified hypotheses
evidence grades
causal chain
missing evidence
confidence
provenance
next best actions
unresolved residual
```

Storyteller should not narrate raw gbrain pages directly.

Storyteller should support multiple audiences:

```text
executive_summary
noc_engineer_brief
rca_lead_brief
customer_update
post_incident_review
voice_brief
```

## Customer Ticket Journey Integration

Customer Ticket Journey should use the same Simulator reasoning context.

It should answer:

```text
which customer symptoms are explained
which customer symptoms are unexplained
whether the ticket links to a confirmed incident
whether the ticket links to a candidate incident
whether more evidence is needed
whether the customer update should say confirmed, probable, or under investigation
```

When the Simulator returns:

```text
UNRESOLVED
INSUFFICIENT_EVIDENCE
MODEL_INSUFFICIENT
```

the ticket journey must not force RCA.

Example customer-safe language:

```text
Current evidence suggests a probable transport contribution, but root cause is not yet confirmed. Additional packet-loss and path evidence is required before confirming RCA.
```

## Relationship To gbrain

gbrain remains the underlying semantic backend and MCP identity.

The Simulator may read operational graph/context from gbrain through MCP Hub when needed.

The Simulator must not write hidden truth into gbrain.

Only validated outputs may later become operational knowledge.

Allowed future write candidates:

```text
validated relationship
validated RCA pattern
confirmed learning note
new playbook candidate
new runbook candidate
knowledge gap
evidence-backed causal pattern
```

Forbidden:

```text
hidden ground truth -> gbrain
simulated truth -> operational knowledge
candidate relationship -> confirmed relationship without validation
```

## Main Investment Question

Does causal hypothesis testing improve telecom incident reasoning compared with naive correlation?

The MVP should test whether the system can:

```text
reject wrong RCA candidates
avoid first-alarm-equals-root-cause
avoid highest-severity-alarm-equals-root-cause
avoid blaming unrelated recent changes
retain unknown alarms as observations
detect missing topology or knowledge gaps
say INSUFFICIENT_EVIDENCE when appropriate
preserve provenance for every major claim
support Storyteller, Mark voice, and Customer Ticket Journey from the same reasoning trace
```

## Scope

Use only three initial areas:

```text
Mobile Core Packet Core / PS
IP Transport
Infrastructure / Cloud
```

Target size:

```text
15 to 30 entities
20 to 60 relationships
50 to 200 evidence records per scenario
3 to 5 competing hypotheses
5 deterministic scenarios
```

This is not a scale benchmark.

## Core Scenarios

### S1: Simple Packet Core Fault

Hidden reality:

```text
UPF internal fault
-> packet-core symptoms
-> mobile data degradation
```

Purpose:

Validate basic hypothesis generation, evidence support, contradiction, and final RCA candidate.

### S2: Transport Fault Producing Packet Core Symptoms

Hidden reality:

```text
Transport interface degradation
-> N3 packet loss
-> UPF connectivity degradation
-> PDU session failures
-> mobile data degradation
```

Purpose:

Prove cross-domain reasoning and distinguish origin fault from downstream packet-core symptoms.

### S3: Transport Fault With Noise And Misleading Change

Use the S2 causal family, but inject:

```text
duplicate alarms
unrelated noisy events
delayed transport alarm
unrelated pod restart
unrelated recent packet-core change
varied alarm ordering
```

Purpose:

Test resistance to misleading temporal, severity, volume, and change-bias signals.

### S4: Missing Operational Relationship

Hidden world knows:

```text
UPF-03 -> Router-R21 -> MPLS-PE7 -> DC-GW2
```

Operational graph knows only:

```text
UPF-03 -> Router-R21 -> UNKNOWN -> DC-GW2
```

Expected result:

```text
MODEL_INSUFFICIENT
TOPOLOGY_GAP_DETECTED
```

The system may propose a candidate relationship, but must not confirm it automatically.

### S5: Correct Answer Is Unknown

Evidence is intentionally insufficient.

Expected result:

```text
UNRESOLVED
INSUFFICIENT_EVIDENCE
```

Unknown is a valid answer.

## Non-Negotiable Boundary

Separate these concepts strictly.

### Simulation World

Contains hidden reality:

```text
real topology
true root condition
trigger
propagation
hidden relationships
generated evidence
injected noise
```

### Operational Evidence

Only what an operator could observe.

It may be:

```text
incomplete
delayed
noisy
contradictory
duplicated
missing
```

### Operational Graph

Represents current known operational knowledge.

It may be:

```text
incomplete
stale
wrong
```

### Reasoning Engine

May access only:

```text
operational evidence
operational graph
hypothesis state
```

It must not access hidden ground truth.

### Evaluator

May compare final operational result against hidden truth.

Allowed:

```text
Hidden Ground Truth -> Evaluator <- Operational Prediction
```

Forbidden:

```text
Hidden Ground Truth -> Reasoning Engine
Hidden Ground Truth -> Operational Graph
Hidden Ground Truth -> gbrain
Hidden Ground Truth -> Mark
Hidden Ground Truth -> Storyteller
Hidden Ground Truth -> Customer Ticket Journey
```

Ground truth evaluates the experiment. It does not teach the operational system.

## Causal Evidence Generation Model

Generate scenario evidence from causal reality:

```text
ROOT CONDITION
-> TRIGGER
-> PROPAGATION
-> SYMPTOMS
-> SERVICE IMPACT
```

Propagation may be deterministic or use seeded probabilities and seeded delays.

The Simulation World generates the complete evidence set from hidden causal reality.

Operational Evidence exposes only the observable subset.

The Reasoning Engine must reconstruct the likely explanation using only that observable subset, operational graph, and hypothesis state.

The Reasoning Engine must never read hidden causal reality, hidden relationships, or evaluator truth.

## Minimal Operational Graph Vocabulary

Use only relationship types needed for the five scenarios:

```text
DEPENDS_ON
CONNECTED_TO
ROUTES_THROUGH
HOSTED_ON
CARRIES
AFFECTS
PART_OF
```

Do not build a telecom-wide ontology.

Keep these identifiers distinct:

```text
interfaces
protocols
entities
incident IDs
correlation IDs
evidence IDs
relationship IDs
```

Correlation IDs must not be reused as entity names, interface names, protocol names, incident IDs, or relationship IDs.

## Minimal Contracts

Use Pydantic models consistent with the existing `TelecomBrainEngine` style.

### Scenario

Fields:

```text
scenario_id
seed
world_graph
operational_graph
hidden_ground_truth
observable_evidence_config
noise_config
missing_evidence_config
```

### HiddenGroundTruth

Fields:

```text
root_condition
trigger
origin_domain
actual_propagation
affected_service
hidden_relationships
```

Operational services must not accept this type.

### Evidence

Fields:

```text
evidence_id
event_time
ingestion_time
domain
entity
entity_type
service
evidence_type
value
source
source_reliability
observed_or_inferred
correlation_group
provenance
```

### Hypothesis

Fields:

```text
hypothesis_id
statement
candidate_root_domain
candidate_root_entity
assumptions
expected_observations
supporting_evidence
contradicting_evidence
missing_evidence
status
hypothesis_confidence
causal_confidence
explanation_coverage
```

Statuses:

```text
ACTIVE
SUPPORTED
WEAKENED
FALSIFIED
UNRESOLVED
```

### FailedExplanation

Capture:

```text
failed hypothesis
expected observations
actual observations
contradiction
failed assumptions
uncertainty reduced
next question
```

Never silently discard falsified hypotheses.

### Assumption

Every serious hypothesis must expose assumptions.

Assumption states:

```text
CONFIRMED
SUPPORTED
UNCERTAIN
UNTESTED
CONTRADICTED
REJECTED
```

When a hypothesis fails, identify the failed assumption or assumptions.

Assumptions should be visible in the reasoning trace and available to Storyteller, RCA, visual explanation, and customer-impact consumers.

### EvidenceRequest

Capture:

```text
requested evidence
hypotheses discriminated
reason
information value: HIGH / MEDIUM / LOW
result
```

### CandidateRelationship

Statuses:

```text
CANDIDATE
REJECTED
CONFIRMED
```

`CONFIRMED` requires explicit simulated human validation.

Manual validation/rejection must record:

```text
candidate
supporting evidence
contradicting evidence
validator
decision
reason
decision_time
```

Human validation is a governance gate, not simulator ground truth.

Only validated knowledge may be used in an explicitly approved future H3-style learning experiment.

### InvestigationResult

Terminal states:

```text
EXPLAINED
PARTIALLY_EXPLAINED
UNRESOLVED
MODEL_INSUFFICIENT
CONFLICTING_EVIDENCE
```

## Reasoning Loop

Implement:

```text
OBSERVE
-> GENERATE 3-5 COMPETING HYPOTHESES
-> DECLARE ASSUMPTIONS
-> PREDICT EXPECTED OBSERVATIONS
-> SELECT NEXT-BEST EVIDENCE
-> TEST
-> SUPPORT / CONTRADICT
-> UPDATE CONFIDENCE
-> FALSIFY WHEN JUSTIFIED
-> RECORD FAILED EXPLANATION
-> CALCULATE UNEXPLAINED RESIDUAL
-> REPEAT OR ABSTAIN
```

A rejected hypothesis is useful progress when rejected with evidence.

## Evidence Semantics

Evidence states:

```text
confirmed_fact
inferred_relation
weak_signal
missing_evidence
contradiction
untrusted
neutral
```

Rules:

```text
absence of evidence is not automatically evidence of absence
missing evidence only weakens a hypothesis if the signal should have been observable
duplicate evidence from one source is not independent confirmation
correlation does not prove causality
recent change does not automatically mean RCA
severe alarm does not automatically mean root cause
```

Every major claim must include:

```text
evidence grade
confidence
provenance
source
whether it is observed or inferred
```

## Next-Best Evidence

Do not collect every possible signal.

Prefer evidence that best discriminates the leading hypotheses.

Example:

```text
H1 Transport fault
H2 UPF internal fault

N3 packet loss        HIGH
Transport counters   HIGH
UPF CPU/memory        MEDIUM
Unrelated logs        LOW
```

A simple ordinal information-value strategy is sufficient.

Record every evidence request and its result.

## Falsification Rules

For each hypothesis:

```text
state expected observations
state material contradictions
retrieve discriminating evidence
compare expectation to observation
update support and contradiction
mark FALSIFIED when justified
record why it failed
do not reintroduce it without materially new evidence
```

Required shape:

```text
Hypothesis -> Prediction -> Evidence -> Contradiction -> Rejection -> Reduced Uncertainty
```

Avoid:

```text
Hypothesis -> Vague mismatch -> Random next hypothesis
```

## Unexplained Residual

For the best explanation, calculate:

```text
observations explained
observations contradicted
observations unexplained
expected observations missing
```

A simple ratio is enough.

If material residual remains, do not force RCA.

Permit:

```text
PARTIALLY_EXPLAINED
UNRESOLVED
MODEL_INSUFFICIENT
CONFLICTING_EVIDENCE
```

## Discovery Mode

Enter discovery mode when:

```text
major hypotheses are falsified
explanation coverage remains low
operational graph cannot explain propagation
material observations contradict the model
```

Discovery mode should:

```text
identify violated assumptions
list unexplained observations
declare the model may be incomplete
request topology/path evidence
generate candidate relationship hypotheses
keep candidates non-authoritative
permit MODEL_INSUFFICIENT
```

Never automatically write candidate relationships into authoritative operational knowledge.

## LLM Usage Boundary

Use deterministic Python for:

```text
graph traversal
timestamps
evidence counting
scenario generation
seeded noise
seeded delays
metric calculation
hidden-truth evaluation
baseline comparison
anti-leakage enforcement
```

LLM assistance is optional and may only assist with:

```text
candidate hypothesis wording
assumption explanations
next-best-evidence suggestions
failed-hypothesis explanation
concise investigation summary
audience-specific wording
```

All LLM-generated claims must either cite evidence IDs or be explicitly marked as hypotheses.

Never allow an LLM to fabricate a missing relationship as confirmed fact.

Never allow an LLM to convert a candidate relationship into operational truth.

LLM output must not be required for deterministic tests to pass.

## Visual Explanation

The Simulator should emit structured visual explanation data usable by the existing `VisualExplanationService`.

Useful widgets:

```text
hypothesis_race
causal_chain
evidence_matrix
confidence_timeline
topology_gap
customer_impact
next_best_action
```

Emit structured data that the current frontend can later render.

## Dedicated Simulator UI

Build a dedicated Simulator UI inside the existing frontend.

It may replace the existing route:

```text
http://localhost:3000/templates
```

Preferred route behavior:

```text
/templates -> Simulator workspace
```

Do not create a separate frontend application.

Do not create a full customer portal.

Do not redesign unrelated application areas.

The UI should feel like a professional mobile-network-level simulator console.

It should provide deep operational insight into what is happening at every relevant level of the simulated incident.

The UI should be highly organized, professional, and easy to understand.

The UI must avoid overlapping content, crowded controls, clipped text, ambiguous grouping, and visually noisy layouts.

The first screen should be the usable Simulator workspace, not a marketing or explainer page.

The Simulator workspace should support:

```text
scenario selection
seed selection
run controls
scenario summary
current terminal state
mobile service impact overview
domain health summary
packet core view
transport view
infrastructure/cloud view
entity-level drilldown
interface/path-level drilldown
event timeline
hypothesis race
active hypotheses
supported hypotheses
falsified hypotheses
assumption ledger
expected observations
evidence matrix
next-best evidence requests
reasoning trace
unexplained residual
causal chain
propagation path
blast-radius summary
affected customer/service symptoms
baseline comparison
metrics
visual explanation payload
customer-safe update
Mark spoken summary preview
topology gap view for S4
candidate relationship review for S4
manual validation/rejection controls for H2
investment decision report after H1/H2 review
```

Organize the UI into clear task areas:

```text
Run setup
Network overview
Service impact
Domain drilldown
Topology and propagation
Investigation state
Hypotheses
Evidence
Reasoning trace
Baseline and metrics
Customer and voice outputs
Discovery and validation
Investment report
```

Use progressive disclosure where needed so the page remains readable.

Tables, timelines, graph views, and panels must have stable dimensions and responsive constraints.

Long IDs, evidence references, hypothesis statements, and customer updates must wrap or truncate gracefully without breaking layout.

The UI should make operational separation visible:

```text
hidden truth is only visible in evaluator/report views
operational evidence is separate from hidden truth
operational graph is separate from world graph
candidate relationships are clearly marked as non-authoritative
manual validation is clearly distinct from simulator ground truth
```

The UI should expose structured outputs from the Simulator rather than reimplementing reasoning in the frontend.

All simulation tasks should be presented as organized workflows with clear labels, status, and next action.

The UI should support layered investigation:

```text
service level: mobile data degradation and customer-facing symptoms
domain level: packet core, transport, infrastructure/cloud health
topology level: dependencies, paths, candidate gaps, and propagation
entity level: UPF, router, interface, gateway, pod, node, and service state
evidence level: alarms, counters, logs, changes, missing evidence, weak signals
hypothesis level: support, contradiction, falsification, confidence, residual
decision level: terminal state, baseline comparison, metrics, next action
```

Each level should answer:

```text
what changed
what is affected
what evidence supports it
what evidence contradicts it
what remains unknown
what action or evidence is needed next
```

The interface should make causal propagation visible, not just list events.

It should help distinguish:

```text
origin fault
downstream symptom
correlated but unrelated event
misleading recent change
missing topology relationship
insufficient evidence
```

For S2/S3, the UI should clearly show how transport degradation causes packet-core-facing symptoms without incorrectly blaming the packet core.

For S4, the UI should clearly show where the known operational graph cannot explain observed propagation.

For S5, the UI should make justified abstention visible and understandable rather than looking like a failed run.

## Customer Ticket Journey Contract

For customer-impact workflows, produce:

```text
ticket_status
customer_impact_summary
probable_cause
confirmed_cause
confidence
affected_services
affected_domains
customer_safe_update
internal_noc_note
next_evidence_needed
```

Customer updates must avoid unsupported certainty.

## Metrics

Track:

```text
1. Root Cause Top-3 Accuracy
2. Wrong Hypotheses Correctly Falsified
3. Evidence Requests Before Terminal Decision
4. Steps To First Useful Hypothesis
5. Forced-RCA Rate When UNKNOWN Is Correct
6. Explanation / Provenance Quality
7. Storyteller Usability
8. Mark Voice Usability
9. Customer Update Safety
```

Do not invent ROI.

## Baseline Comparison

Compare:

```text
Baseline A:
earliest severe alarm or highest alarm-count domain
```

Against:

```text
Method B:
Simulator causal hypothesis reasoning using operational graph context,
service context, evidence grading, contradiction,
falsification, and next-best evidence.
```

Both run against identical hidden reality.

The goal is not to prove the Simulator wins.

If Method B does not materially outperform the baseline, report that clearly.

Do not weaken tests, scenarios, metrics, or scoring to make Method B look better.

## Reproducibility

Every scenario must accept a random seed.

For S2 and S3, seeded variants should vary:

```text
alarm ordering
duplicates
evidence delay
unrelated noise
missing evidence
unrelated recent change
```

This prevents handcrafted scenario behavior from being mistaken for reasoning.

Seeded runs must be reproducible for:

```text
world graph
operational graph
observable evidence
noise injection
missing evidence
reasoning inputs
metrics
baseline results
```

## Investment Decision Report

After H1 and H2 are run and reviewed, generate a small report:

```text
Hypothesis
What was tested
Baseline
Results
Where the Simulator helped
Where it failed
Unexpected observations
Observed implementation complexity
Evidence for further investment
Evidence against further investment
Recommendation:
  PROCEED
  MODIFY_AND_RETEST
  STOP
```

Do not bias the recommendation toward proceeding.

A failed hypothesis is a valid experiment result.

Do not invent ROI.

## Local Commands

Prefer pytest and direct Python entrypoints over a new production CLI.

Expected test command:

```bash
PYTHONPATH=services/agents/src .venv/bin/python -m pytest \
  services/agents/src/engine_stack/engines/telecom_brain/tests/test_simulator_h1.py -q
```

Optional local module runner:

```bash
PYTHONPATH=services/agents/src .venv/bin/python -m \
  engine_stack.engines.telecom_brain.simulator.runner \
  --scenario S2 --seed 42
```

The local runner should prioritize inspectability over UI polish.

It should support inspecting:

```text
available scenarios
hypotheses
evidence
reasoning trace
evaluation result
topology gaps
candidate relationships
validation and rejection decisions
```

It does not need to be a production CLI.

Simple Python module flags or pytest fixtures are acceptable if they expose the same inspection capability.

Do not add Docker, Kafka, Neo4j, Kubernetes, or production databases.

## Definition Of Done: H1

H1 is complete when:

```text
S1 to S3 run locally
hidden truth cannot leak into reasoning
3 to 5 hypotheses are visible
assumptions are visible
expected observations are visible
next-best evidence is selected
positive and negative evidence update hypothesis state
wrong hypotheses are explicitly falsified
failed explanations are retained
terminal conclusion is produced
baseline comparison works
seeded variants are reproducible
metrics are produced
Storyteller can consume the result
Mark can speak a curated summary
Customer Ticket Journey can consume the result
```

Stop after H1 and review.

## Definition Of Done: H2

H2 is complete when:

```text
S4 runs
current operational graph fails to explain material evidence
unexplained residual is shown
Discovery Mode activates
candidate relationship is generated
supporting and contradicting evidence are shown
candidate remains non-authoritative
manual validation/rejection works
hidden truth is not used to generate the candidate
S5 returns unresolved when appropriate
```

Stop after H2 and review.

## Tests Required

Add tests proving:

```text
reasoning cannot access hidden truth
evaluator access is isolated
seeds are reproducible
correlation IDs are not entity/interface names
healthy evidence can weaken a hypothesis
missing evidence is not automatically health
unrelated change does not automatically become RCA
falsified hypotheses retain rejection evidence
falsified hypotheses are not silently recycled
candidate relationships remain non-authoritative
model insufficiency is detected
unresolved is returned when evidence is insufficient
justified abstention is not scored as ordinary wrong RCA
evaluator truth is never written into gbrain
```

## Explicitly Out Of Scope

Do not implement in this MVP:

```text
standalone simulator repo
engine/package rename
assistant rename
environment variable rename
gbrain connector rename
production topology database
production digital twin
Kafka
Neo4j
Kubernetes
large-scale alarm benchmark
autonomous remediation
full customer portal
full unrelated UI rewrite
live Grafana dependency
automatic gbrain learning write-back
multi-agent fleet
H3/H4 without explicit approval
```

## Optional H3 Shape

Do not implement H3 without explicit approval.

If later approved, the smallest useful H3 experiment is:

```text
S4 -> candidate relationship
-> manual evidence review
-> validation or rejection
-> updated operational knowledge
-> different related future scenario
-> compare with and without the validated relationship
```

Do not call an identical scenario replay "learning."

Learning claims require improvement on a varied future case.

## Implementation Order

### Step 0: Inspect

Inspect current:

```text
TelecomBrainEngine
StorytellingService
VisualExplanationService
Customer Ticket Journey
MCP Hub
gbrain connector
Mark voice pipeline
```

Reuse existing patterns.

### Step 1: Contracts And Isolation

Implement contracts and anti-leakage tests.

### Step 2: Tiny World

Implement S1 and deterministic evidence generation.

### Step 3: Hypothesis Loop

Implement competing hypotheses, assumption ledger, expected observations, support, contradiction, falsification, and failed-explanation trace.

### Step 4: Evidence Selection

Implement next-best-evidence ranking.

### Step 5: H1 Integration

Connect result to:

```text
Storyteller context
Mark spoken answer
Customer Ticket Journey summary
VisualExplanationService payload
```

### Step 6: H1 Metrics

Run S1 to S3 and compare against baseline.

Stop and review.

### Step 7: H2 Discovery

Implement S4/S5, model insufficiency, topology gap detection, candidate relationship, and validation flow.

Stop and review.

### Step 8: H2 Report

After H1 and H2 are reviewed, generate the investment decision report.

Stop and review before any future H3/H4 work.

## Final Principle

The Simulator exists to test investment hypotheses, not to demonstrate the entire telecom brain vision.

Evidence outranks narrative.

Unknown is better than unsupported certainty.

Rejected hypotheses are useful progress when rejected with evidence.

Candidate learning must be validated before becoming operational knowledge.
