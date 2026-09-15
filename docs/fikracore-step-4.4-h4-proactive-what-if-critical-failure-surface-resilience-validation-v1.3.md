# FikraCore Simulator — Step 4.4 / H4 Proactive What-If, Critical Failure Surface & Resilience Validation

## Revision v1.3

Adds a human-readable scenario registry, deterministic scenario resolution, alias support, and optional NLP/semantic matching for operator-friendly CLI, Simulator UI, Curated Demo Mode, and Mark / Zaki interaction. H4 reasoning and benchmark semantics remain unchanged.

## Purpose

Step 4.4 validates **H4 — Proactive What-If, Critical Failure Surface & Resilience Validation**.

H1 established that FikraCore can reason causally from current operational knowledge.

H2 established that FikraCore can recognize when its operational knowledge is incomplete, localize the gap, request useful next evidence, and avoid hallucinating topology.

H3 established that SME-validated operational knowledge can be safely promoted and reused to improve reasoning on a different future incident.

H4 asks:

> Can FikraCore use its validated operational knowledge proactively to identify critical vulnerabilities, likely blast radius, and resilience risks before an outage occurs?

H4 moves the system from:

```text
reactive incident reasoning
```

to:

```text
proactive resilience intelligence
```

The goal is not to predict the exact future. The goal is to stress-test plausible failures against known dependencies and identify where the network is fragile before a real incident occurs.

---

# 1. H4 Validation Question

Validate:

> Can FikraCore use the current validated telecombrain to simulate plausible failure and change conditions, estimate affected services and blast radius, identify critical failure surfaces, compare mitigation options, and produce explainable resilience recommendations without inventing unsupported dependencies?

H4 is successful only if:

```text
validated operational knowledge
→ proactive what-if scenario
→ forward causal propagation
→ blast-radius estimation
→ critical failure-surface discovery
→ mitigation comparison
→ resilience recommendation
```

---

# 2. Core H4 Principle

```text
Incident Mode:
Reason backward from symptoms to likely cause.

What-If Mode:
Reason forward from a hypothetical failure/change
to likely service impact.
```

H4 must not claim certainty about future outages.

It should answer:

```text
If this component fails,
what is likely to be affected,
why,
how badly,
and what could reduce the risk?
```

---

# 3. Preserve H1, H2, and H3

Freeze completed behavior of:

```text
H1 — causal RCA
H2 — knowledge-gap discovery
H3 — governed learning
```

Do not weaken:

```text
epistemic boundaries
human-readable naming
candidate-vs-confirmed knowledge semantics
promotion governance
Mark / Zaki grounding
Simulator UI shared-state architecture
```

All previous regression tests must continue to pass.

H4 must be additive.

---

# 4. H4 Uses the Existing telecombrain

H4 must use the same existing operational `telecombrain`.

Do not create a second resilience graph.

The same knowledge should support:

```text
incident investigation
knowledge-gap discovery
validated learning
proactive what-if analysis
```

---

# 5. Epistemic Boundary

H4 may use simulator Hidden Truth only for offline evaluation.

Runtime What-If reasoning must use only:

```text
current telecombrain knowledge
validated learned knowledge
scenario input
configured failure/change assumptions
```

Forbidden:

```text
Hidden Truth → What-If Engine
Hidden Truth → Mark / Zaki
Hidden Truth → Simulator UI
Hidden Truth → resilience recommendation
```

---

# 6. H4 Reasoning Direction

Incident reasoning:

```text
Observed Symptoms
      ↑
Propagation
      ↑
Root Cause
```

H4 proactive reasoning:

```text
Hypothetical Failure / Change
      ↓
Dependency Propagation
      ↓
Affected Network Functions
      ↓
Affected Services
      ↓
Customer / Business Impact
```

---

# 7. What-If Scenario Types

Support at least:

```text
1. Single network-function failure
2. Transport link failure
3. Shared dependency failure
4. Data-center failure
5. Site / power failure
6. Kubernetes / cloud host failure
7. Storage failure
8. Database failure
9. DNS failure
10. Load balancer failure
11. Firewall failure
12. Signaling congestion
13. Capacity exhaustion
14. Failover failure
15. Redundancy loss
16. Software change
17. Configuration change
18. Routing change
19. External carrier failure
20. Roaming/interconnect failure
21. Charging failure
22. BSS / provisioning failure
23. Security control failure
24. Multi-component failure
25. Cascading failure
```

---

# 8. H4 Failure Input Contract

Example:

```json
{
  "what_if_id": "H4-WI-001",
  "title": "Failure of MPLS Edge Router-07",
  "trigger": {
    "entity_display_name": "MPLS Edge Router-07",
    "canonical_id": "topology/transport/routers/mpls-pe-07",
    "event_type": "FAILURE",
    "severity": "CRITICAL"
  },
  "assumptions": {
    "failover_available": true,
    "failover_capacity": "LIMITED",
    "duration_minutes": 30
  }
}
```

---

# 9. Human-Readable Naming

Continue the persistent human-readable naming requirement.

Use:

```text
Transport Router-01
MPLS Edge Router-07
Data Center Gateway-01
Packet Gateway-01
User Plane Function-01
Database Cluster-01
```

Use canonical IDs only as technical traceability fields.

---

# 10. Forward Causal Propagation

The What-If Engine should traverse known operational relationships forward.

Relevant relations may include:

```text
DEPENDS_ON
CONNECTED_TO
ROUTES_THROUGH
CARRIED_BY
HOSTED_ON
RUNS_ON
BACKHAULED_BY
PROVISIONED_BY
MONITORED_BY
CHARGES_VIA
AUTHENTICATES_VIA
RESOLVES_VIA
TIMED_BY
POWERED_BY
COOLED_BY
STORED_ON
USES_DATABASE
USES_CACHE
USES_MESSAGE_BUS
PROTECTED_BY
FAILS_OVER_TO
PEERS_WITH
SERVES
SUPPORTS_SERVICE
IMPACTS
BELONGS_TO_SITE
BELONGS_TO_REGION
PART_OF_FAILURE_DOMAIN
SUPPLIED_BY
```

Use only relations known to `telecombrain`.

---

# 11. Propagation Semantics

Not every dependency means total outage.

Each relation should support propagation characteristics such as:

```text
hard dependency
soft dependency
redundant dependency
capacity dependency
control-plane dependency
monitoring-only dependency
optional dependency
```

Where semantics are unknown, H4 should state uncertainty.

---

# 12. Blast Radius

Define blast radius as:

> The set of network functions, services, customer journeys, locations, or business capabilities plausibly affected by the hypothetical failure.

Report at least:

```text
directly affected entities
indirectly affected entities
affected services
affected domains
affected regions/sites
customer-facing impact
confidence
```

---

# 13. Blast-Radius Levels

Recommended labels:

```text
LOCAL
DOMAIN
MULTI_DOMAIN
REGIONAL
NETWORK_WIDE
```

These are presentation labels, not substitutes for actual counts.

---

# 14. Critical Failure Surface

Define:

> The smallest set of components, dependencies, or conditions capable of causing unacceptable service impact.

Identify:

```text
single points of failure
shared hidden dependencies
insufficient redundancy
failover bottlenecks
capacity-constrained backups
common power dependencies
common transport paths
common database dependencies
common cloud-host dependencies
common security/control dependencies
```

---

# 15. Criticality Scoring

Create an explainable score from:

```text
number of dependent services
number of dependent domains
customer impact
lack of redundancy
failover weakness
dependency centrality
validated learned importance
geographical scope
recovery complexity
operational confidence
```

Keep component scores visible.

---

# 16. Vulnerability vs Failure

Distinguish:

```text
Vulnerability:
A condition that could amplify future impact.

Failure:
An actual or simulated event.
```

Example:

```text
MPLS Edge Router-07 has a redundant peer,
but backup capacity is only 40%.

That is a vulnerability even if nothing has failed yet.
```

---

# 17. Redundancy Validation

A `FAILS_OVER_TO` relation must not automatically imply resilience.

Evaluate:

```text
backup exists
backup health
backup capacity
backup dependency independence
shared failure domain
shared power
shared transport
shared software/version
```

---

# 18. Common-Cause Risk

Identify apparently redundant systems that share:

```text
same site
same power supply
same transport path
same database
same cloud host
same Kubernetes cluster
same software release
same upstream router
same external provider
```

---

# 19. Capacity-Aware What-If

Where capacity data exists, simulate:

```text
normal load
peak load
failover load
recovery surge
```

Example:

```text
Primary User Plane Function fails.
Backup User Plane Function can carry 70% of peak traffic.

Expected:
partial degradation, not full protection.
```

---

# 20. Change What-If

Support planned-change simulation.

Example:

```text
What if Transport Router-01 is rebooted during maintenance?
```

Estimate:

```text
affected services
available alternate paths
temporary redundancy loss
customer impact
safe/unsafe maintenance window
```

---

# 21. Change Risk Object

```json
{
  "change_id": "CR-SIM-001",
  "target": "Transport Router-01",
  "change_type": "REBOOT",
  "predicted_impact": {
    "services": [],
    "blast_radius": "MULTI_DOMAIN",
    "redundancy_loss": true
  },
  "recommendation": "Require backup path validation before execution."
}
```

---

# 22. Multi-Failure What-If

Support:

```text
component A failure
+
component B degraded
```

or:

```text
site power failure
+
backup transport congestion
```

---

# 23. Critical Failure Set

Identify minimal combinations:

```text
Failure of A alone → tolerable
Failure of B alone → tolerable
Failure of A + B → unacceptable
```

That combination forms a critical failure set.

---

# 24. Resilience Gap Object

```json
{
  "gap_id": "RG-001",
  "type": "INSUFFICIENT_FAILOVER_CAPACITY",
  "affected_service": "Mobile Data",
  "primary": "User Plane Function-01",
  "backup": "User Plane Function-02",
  "risk": "Backup supports only 70% of peak traffic.",
  "severity": "HIGH",
  "recommended_action": "Increase backup capacity or introduce an additional failover path."
}
```

---

# 25. Mitigation Comparison

Compare options such as:

```text
Option A — Add second transport path
Option B — Increase backup capacity
Option C — Move dependency to separate failure domain
```

Report:

```text
risk reduction
services protected
implementation complexity
operational disruption
confidence
```

---

# 26. Next-Best Resilience Action

Ask:

> What resilience action would reduce the most operational risk?

Possible actions:

```text
validate backup
increase capacity
remove shared dependency
separate failure domains
add monitoring
validate routing
test failover
update stale topology
perform resilience drill
```

---

# 27. What-If Confidence

Confidence should consider:

```text
knowledge completeness
relationship confidence
topology freshness
capacity-data availability
redundancy-data availability
observability coverage
validated learning provenance
```

---

# 28. Model Insufficiency Still Applies

H4 must not force a prediction if the operational model is incomplete.

Example:

```text
What-If Assessment:
MODEL_INSUFFICIENT

Reason:
Data Center Gateway-01 has an unknown upstream transport dependency,
so full blast radius cannot be estimated reliably.
```

---

# 29. Knowledge Contradiction Still Applies

If H4 encounters:

```text
stale
contradicted
conflicting
```

knowledge, lower confidence or block strong recommendations.

---

# 30. H3 Learning Reuse in H4

Explicitly test whether H3-learned knowledge improves proactive risk analysis.

Example:

```text
H3 learned:
Transport Router-01 routes through MPLS Edge Router-07.

H4 what-if:
What if MPLS Edge Router-07 fails?

Expected:
FikraCore includes all validated dependent services in the blast radius.
```

---

# 31. H4 Scenario Cohorts

Recommended benchmark:

```text
40 H4 scenarios
```

Suggested cohorts:

```text
10 single-point failure
10 shared/common-cause
10 failover/capacity
5 change-risk
5 multi-failure / complex resilience
```

---

# 32. Positive Control Cohort

Where topology is complete:

```text
expected:
high-confidence correct blast radius
```

---

# 33. Unknown-Knowledge Cohort

Where knowledge is intentionally incomplete:

```text
expected:
partial blast radius
MODEL_INSUFFICIENT
or explicit uncertainty
```

Never invent missing dependency.

---

# 34. Redundancy Trap Cohort

Example:

```text
Primary Router and Backup Router
both powered by the same site feed.
```

Expected:

```text
shared-risk detected
```

---

# 35. Capacity Trap Cohort

Example:

```text
Backup path exists
but cannot carry peak load.
```

Expected:

```text
partial resilience only
```

---

# 36. Change-Risk Cohort

Example:

```text
planned reboot of an apparently redundant router
```

while:

```text
backup is already degraded
```

Expected:

```text
unsafe change warning
```

---

# 37. H4 Baselines

### Baseline A — Static Dependency Count

```text
Rank risk by number of direct dependents only.
```

### Baseline B — Simple Reachability

```text
Traverse downstream dependencies without redundancy/capacity semantics.
```

### Method B — FikraCore Causal Resilience Reasoning

```text
forward propagation
+
dependency semantics
+
redundancy
+
capacity
+
failure domains
+
knowledge confidence
```

---

# 38. H4 Metrics

Measure:

```text
Blast-Radius Precision
Blast-Radius Recall
Affected-Service Accuracy
Critical Failure-Surface Accuracy
Shared-Dependency Detection
Failover-Risk Detection
Capacity-Risk Detection
Change-Risk Detection
False Risk Rate
Missed Critical Risk Rate
MODEL_INSUFFICIENT correctness
Hallucinated Dependency Rate
Mitigation Usefulness
```

---

# 39. Critical Metric — Hallucinated Risk

Track:

> Did H4 claim an impact path unsupported by operational knowledge?

Target:

```text
0 hallucinated dependency paths
```

Unsupported paths may be marked:

```text
CANDIDATE
UNKNOWN
MODEL_INSUFFICIENT
```

but never confirmed.

---

# 40. Critical Metric — Missed Risk

Track:

> Did H4 fail to identify a critical service dependency that was present in operational knowledge?

This prevents the engine from becoming overly conservative.

---

# 41. H4 Evaluator

The offline evaluator may compare predicted blast radius against Hidden Truth.

Score:

```text
correct impacted entities
correct unaffected entities
correct service impact
correct common-cause identification
correct failure-surface identification
correct uncertainty
```

Hidden Truth remains evaluation-only.

---

# 42. Blast-Radius Precision / Recall

Use:

```text
Precision:
Of everything predicted as impacted,
how much was truly impacted?

Recall:
Of everything truly impacted,
how much did FikraCore identify?
```

Report both.

---

# 43. Explainability

Every predicted impact should be explainable through a dependency path.

Example:

```text
MPLS Edge Router-07 failure
  ↓ Routes traffic for
Transport Router-01
  ↓ Carries
Packet Gateway-01 traffic
  ↓ Supports
Mobile Data Service
```

---

# 44. Path Provenance

Every impact path should retain:

```text
entity
relationship
relationship state
knowledge source
confidence
last validation
```

---

# 45. Resilience Recommendation Safety

Recommendations must be categorized:

```text
OBSERVATION
RISK
CANDIDATE_ACTION
VALIDATED_ACTION
```

H4 should generally output `CANDIDATE_ACTION` unless policy explicitly authorizes execution.

---

# 46. No Autonomous Network Changes

H4 must not:

```text
reconfigure routers
modify live traffic
execute failover
change capacity
apply firewall rules
```

H4 validates reasoning and recommendations only.

---

# 47. Simulator UI Integration

H4 must integrate into the same Simulator UI.

The same UI should support:

```text
H1 — Reason
H2 — Recognize the Unknown
H3 — Learn
H4 — Predict
```

---

# 48. H4 Investigation Mode

Support:

```text
what-if trigger
affected topology
predicted propagation
blast radius
affected services
redundancy state
capacity state
critical failure surface
resilience gaps
mitigation options
confidence
knowledge limitations
```

---

# 49. H4 Curated Demo Mode

Leadership demo:

```text
Step 1 — Select a critical component
Step 2 — Ask "What if this fails?"
Step 3 — Show forward propagation
Step 4 — Show affected services
Step 5 — Reveal shared dependency / resilience gap
Step 6 — Compare mitigation options
Step 7 — Show recommended resilience action
```

Final message:

> **FikraCore uses validated operational knowledge to identify risk before failure occurs.**

---

# 50. Curated Scenario Library

Example demos:

```text
1. What if MPLS Edge Router-07 fails?
2. What if the backup User Plane Function is overloaded?
3. What if Data Center-A loses power?
4. What if a shared database fails?
5. What if a planned router reboot happens while backup is degraded?
6. What if two redundant systems share the same transport path?
```

---

# 51. Mark / Zaki Integration

Mark and Zaki remain interchangeable names for the same assistant identity.

Mark / Zaki should support:

```text
What happens if this router fails?
Which services depend on this component?
Show the blast radius.
Why is Mobile Data affected?
Which dependency makes this critical?
Do we really have redundancy?
What happens at peak load?
What is the weakest point?
Which resilience action should we prioritize?
What knowledge is missing from this prediction?
```

---

# 52. Mark / Zaki Grounding

Mark / Zaki must consume the same structured H4 Simulator state.

Forbidden:

```text
inventing affected services
inventing redundancy
claiming unsupported blast radius
using Hidden Truth
```

---

# 53. Shared Presentation Contract

Extend the shared model with:

```json
{
  "resilience": {
    "what_if": {},
    "propagation_paths": [],
    "blast_radius": {},
    "affected_services": [],
    "critical_failure_surfaces": [],
    "resilience_gaps": [],
    "mitigation_options": [],
    "recommended_actions": [],
    "confidence": 0.0,
    "knowledge_limitations": []
  }
}
```

---

# 54. H4 Demo Metadata

```json
{
  "demo": {
    "enabled": true,
    "title": "What If the Shared Transport Edge Fails?",
    "audience": "leadership",
    "duration_minutes": 4,
    "steps": [
      "Select Failure",
      "Propagate Impact",
      "Show Blast Radius",
      "Reveal Shared Dependency",
      "Compare Mitigations",
      "Recommend Resilience Action"
    ],
    "final_message": "Find the weak point before it becomes an outage."
  }
}
```

Presentation metadata must not affect reasoning.

---

# 55. H4 Integrity Validator

Before benchmark execution verify:

```text
what-if trigger exists
operational topology is valid
hidden evaluator truth is segregated
predicted paths can be scored
redundancy metadata is internally consistent
capacity assumptions are explicit
failure domains are valid
scenario contains no truth leakage
```

---

# 56. H4 Scenario Consistency

Reject scenarios where:

```text
impact cannot causally propagate
required entities do not exist
backup capacity is undefined but exact overload is expected
failure-domain semantics contradict topology
hidden truth leaks through metadata
```

---

# 57. H4 Required Artifacts

Generate:

```text
artifacts/hypothesis/h4/
├── aggregate-report.json
├── aggregate-report.md
├── what-if-runs.jsonl
├── blast-radius-analysis.json
├── affected-service-analysis.json
├── critical-failure-surface-analysis.json
├── shared-dependency-analysis.json
├── redundancy-analysis.json
├── capacity-analysis.json
├── change-risk-analysis.json
├── model-insufficiency-analysis.json
├── hallucination-analysis.json
├── mitigation-analysis.json
├── baseline-comparison.json
├── integrity-report.json
└── final-h4-report.md
```

---


## CLI Command Convention

Use **`fikracore`** as the single CLI namespace for the Telecom Brain simulator, investigation, validation, reporting, and demo workflows.

It should map to the existing investigation CLI implementation under:

```text
services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py
```

Do not use `fikracore-mvp` in documentation, examples, or future H1-H4 commands.

Recommended command style:

```text
fikracore <command>
```

Future grouping may evolve into:

```text
fikracore h1 ...
fikracore h2 ...
fikracore h3 ...
fikracore h4 ...
fikracore simulator ...
fikracore demo ...
fikracore report ...
fikracore diagnose ...
```

The exact subcommand structure may adapt to the existing parser, but the root executable name should remain:

```text
fikracore
```

---


## `fikracore` CLI Registration Requirement

The project must expose **`fikracore`** as the primary console command for the Telecom Brain capability layer.

The command should invoke the existing CLI implementation under:

```text
services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py
```

The CLI module must expose a callable entry function, for example:

```python
def main():
    ...
```

Register the command in the repository's `pyproject.toml` using the actual importable package path.

Conceptual example:

```toml
[project.scripts]
fikracore = "services.agents.src.engine_stack.engines.telecom_brain.investigation.cli:main"
```

If the repository uses a `src`-layout or a different Python package root, use the real import path instead, for example:

```toml
[project.scripts]
fikracore = "engine_stack.engines.telecom_brain.investigation.cli:main"
```

Do not hard-code an invalid module path merely to match this document. The implementation must inspect the current package layout and register the correct importable module.

After registration, install/synchronize the project environment using the repository's existing `uv` workflow, for example:

```bash
uv sync
```

or, where appropriate:

```bash
uv pip install -e .
```

Verify:

```bash
uv run fikracore --help
```

and, when the environment is active and the console script is installed:

```bash
fikracore --help
```

The intended outcome is that the user can invoke FikraCore without navigating to the internal Python module.

Where project/environment packaging permits, the installed `fikracore` command should be runnable from any working directory.

### CLI Naming Principle

User-facing commands should be **task-oriented**, while H1-H4 remain validation-stage labels.

Preferred capability verbs:

```text
investigate
discover
learn
predict
simulate
present
inspect
benchmark
```

For H4, prefer commands such as:

```bash
fikracore predict what-if H4-WI-001
fikracore simulate H4-WI-001
fikracore inspect H4-WI-001
fikracore present H4-WI-001
fikracore benchmark h4
```

The exact subcommand nesting may adapt to the existing parser, but:

```text
fikracore
```

must remain the root command.

Do not use:

```text
fikracore-mvp
```

in current or future documentation.

---


---

# Human-Readable Scenario Registry & Resolution

H4 scenarios must have both a stable machine identifier and a human-readable presentation identity.

Example:

```yaml
id: H4-WI-001
display_name: MPLS Edge Router Failure
aliases:
  - MPLS router failure
  - edge router outage
  - transport edge failure
```

The stable ID is used for automation, benchmarking, CI/CD, artifact naming, deterministic replay, and internal references.

The human-readable display name is used for CLI interaction, Simulator UI, Curated Demo Mode, Mark / Zaki, reports, and leadership demonstrations.

## Scenario Resolution Order

Resolve user input in this order:

```text
1. Exact scenario ID
2. Exact display-name match
3. Exact alias match
4. Case-insensitive normalized match
5. Fuzzy / NLP semantic match
6. User disambiguation when multiple candidates are plausible
```

Execution must always resolve to one stable scenario ID before the scenario engine runs.

Example:

```text
User input:
"What if the transport edge router goes down?"

        ↓ semantic resolution

Matched scenario:
MPLS Edge Router Failure

        ↓ canonical resolution

H4-WI-001

        ↓

Execute scenario H4-WI-001
```

## Deterministic Mapping First

NLP must not be the authoritative scenario identifier.

Use deterministic mapping as the execution source of truth.

NLP / semantic matching is only a convenience layer for natural-language discovery.

> **Deterministic mapping for execution; NLP for natural-language discovery and convenience.**

## NLP Safety Rule

The NLP layer may:

```text
match natural language to an existing scenario
rank likely scenario candidates
suggest a scenario
ask for clarification
```

The NLP layer must not:

```text
invent a scenario ID
silently create a new benchmark scenario
modify scenario truth
alter scenario assumptions
skip ambiguity handling
```

If no reliable scenario exists, return:

```text
No existing scenario matched with sufficient confidence.
```

A separate explicit workflow may later support ad-hoc what-if creation.

## Scenario Registry

Maintain a reusable scenario registry, for example:

```text
simulator/scenarios/registry.yaml
```

or extend the existing catalog structure.

Recommended record:

```yaml
id: H4-WI-001
stage: H4
display_name: MPLS Edge Router Failure
description: Simulates loss of a shared transport edge and estimates downstream service impact.
aliases:
  - MPLS router failure
  - edge router outage
  - transport edge failure
tags:
  - transport
  - routing
  - shared-dependency
  - resilience
scenario_path: simulator/h4_runs/H4-WI-001/
demo_enabled: true
```

## Human-Friendly CLI Usage

All of these may resolve to the same scenario:

```bash
fikracore predict H4-WI-001
fikracore predict "MPLS Edge Router Failure"
fikracore predict "edge router outage"
```

Natural-language discovery may also support:

```bash
fikracore predict "what if the transport edge router goes down?"
```

The resolver must map accepted input to the stable scenario ID before execution.

## Shared Resolver Across CLI, UI, and Mark / Zaki

The same registry and resolver must support:

```text
CLI
Simulator UI search
Curated Demo scenario selection
Mark / Zaki voice commands
Mark / Zaki chat commands
```

Example:

```text
"Show me what happens if the transport edge router fails."
        ↓
scenario resolver
        ↓
MPLS Edge Router Failure
        ↓
H4-WI-001
        ↓
execute canonical scenario
```

## Ambiguity Handling

If input such as:

```text
router failure
```

matches multiple scenarios, do not guess silently.

Return the strongest candidates and request clarification.

## Scenario Display Convention

Human-facing surfaces should show:

```text
MPLS Edge Router Failure
```

with the stable ID secondarily:

```text
Scenario ID: H4-WI-001
```

Opaque IDs should not be the primary operator-facing label.

## Suggested Resolver Component

Implement or extend a reusable component such as:

```text
presentation/scenario_resolver.py
```

or equivalent.

Suggested functions:

```text
resolve_by_id()
resolve_by_display_name()
resolve_by_alias()
resolve_semantically()
resolve_or_disambiguate()
```

The same resolver should be reusable across H1-H4.

## Scenario Resolution Tests

Add tests such as:

```text
test_scenario_resolves_by_exact_id
test_scenario_resolves_by_display_name
test_scenario_resolves_by_alias
test_scenario_resolution_is_case_insensitive
test_semantic_resolution_maps_to_existing_id
test_semantic_resolution_does_not_invent_id
test_ambiguous_input_requires_disambiguation
test_cli_ui_and_zaki_share_same_scenario_resolver
```

---

# 58. Suggested CLI Commands

Use task-oriented commands and allow either stable IDs or human-readable scenario names.

```bash
fikracore simulate generate h4
fikracore simulate validate h4
fikracore benchmark h4

fikracore predict "MPLS Edge Router Failure"
fikracore inspect "MPLS Edge Router Failure"
fikracore present "MPLS Edge Router Failure"
fikracore report h4
```

Stable IDs remain supported for automation:

```bash
fikracore predict H4-WI-001
fikracore inspect H4-WI-001
fikracore present H4-WI-001
```

The scenario resolver must convert any accepted human-facing name or alias into the canonical scenario ID before execution.

---

# 59. Required Tests

Add at least:

```text
test_h4_forward_dependency_propagation
test_h4_blast_radius_precision_recall
test_h4_shared_dependency_detection
test_h4_failover_dependency_independence
test_h4_capacity_constrained_failover
test_h4_change_risk_detection
test_h4_multi_failure_propagation
test_h4_model_insufficient_when_topology_missing
test_h4_no_hallucinated_dependency_path
test_h4_critical_failure_surface_detection
test_h4_mitigation_comparison
test_h4_hidden_truth_not_visible_to_runtime
test_h4_mark_zaki_grounded_in_shared_state
test_h4_demo_metadata_does_not_change_reasoning
test_h4_h1_h2_h3_regression_suite_still_passes
test_fikracore_console_entry_point_registered
test_fikracore_help_invocation
```

---

# 60. Definition of Done

H4 is complete when:

```text
[ ] H1 behavior remains unchanged
[ ] H2 behavior remains unchanged
[ ] H3 behavior remains unchanged
[ ] dedicated H4 scenarios exist
[ ] forward causal propagation works
[ ] blast radius is computed
[ ] affected services are identified
[ ] redundancy semantics are evaluated
[ ] shared failure domains are detected
[ ] capacity-limited failover is evaluated
[ ] critical failure surfaces are identified
[ ] change-risk scenarios are supported
[ ] multi-failure scenarios are supported
[ ] mitigation options are compared
[ ] MODEL_INSUFFICIENT remains available
[ ] hallucinated paths are measured
[ ] Simulator UI supports H4
[ ] Curated Demo Mode supports H4
[ ] Mark / Zaki supports H4
[ ] zero Hidden Truth leakage occurs
[ ] `fikracore` console entry point is registered and verified
[ ] H4 scenario registry contains stable IDs, display names, and aliases
[ ] CLI resolves scenarios by ID, display name, and alias
[ ] optional NLP/semantic resolution maps only to existing scenario IDs
[ ] ambiguous scenario names require disambiguation
[ ] `fikracore --help` or `uv run fikracore --help` succeeds
[ ] full regression suite passes
[ ] final H4 report is generated
```

---

# 61. H4 Investment Gate

At the end answer:

> Can FikraCore use validated operational knowledge to identify important vulnerabilities, estimate likely blast radius, and recommend useful resilience actions before an outage occurs?

Classify:

```text
H4_SUPPORTED
H4_PARTIALLY_SUPPORTED
H4_NOT_SUPPORTED
```

---

# 62. Recommended H4 Gate Dimensions

Evaluate:

```text
Blast Radius Accuracy
Affected Service Accuracy
Critical Failure Surface Accuracy
Shared Dependency Detection
Failover Risk Detection
Capacity Risk Detection
Change Risk Detection
False Risk Rate
Missed Critical Risk Rate
Zero Hallucinated Paths
MODEL_INSUFFICIENT Correctness
Mitigation Usefulness
```

---

# 63. Suggested H4 Gate Philosophy

Do not require perfect future prediction.

H4 should demonstrate:

```text
known dependencies can be stress-tested
critical shared risks can be surfaced
uncertainty is explicit
missing knowledge blocks overconfident predictions
mitigations are explainable
```

---

# 64. H4 Pitch Language

Use:

> **H4 — Predict**

> FikraCore uses validated operational knowledge to identify likely blast radius, hidden shared dependencies, and resilience risks before they become outages.

Avoid:

> "FikraCore predicts every outage."

---

# 65. H4 Leadership Story

```text
H1 — REASON
Can FikraCore identify the actual root cause from evidence?
✅ Supported

H2 — RECOGNIZE THE UNKNOWN
Can FikraCore detect when its knowledge is incomplete?
✅ Supported

H3 — LEARN
Can validated operational experience improve a different future incident?
✅ Supported

H4 — PREDICT
Can validated knowledge be used proactively to expose risk before failure?
→ Validate now
```

---

# 66. End-to-End FikraCore Value Chain

```text
Evidence
   ↓
Causal Reasoning
   ↓
Knowledge-Gap Detection
   ↓
SME-Validated Learning
   ↓
Reusable telecombrain Knowledge
   ↓
Proactive What-If Analysis
   ↓
Critical Failure Surface
   ↓
Resilience Action
```

---

# 67. Final H4 Demonstration Goal

The strongest demonstration should show:

```text
1. Select a component that has not failed.
2. Ask Mark / Zaki:
   "What happens if this fails?"
3. FikraCore traverses current validated knowledge.
4. The Simulator highlights the likely blast radius.
5. A shared dependency or resilience weakness is exposed.
6. FikraCore explains why.
7. FikraCore proposes a candidate resilience action.
```

The audience should understand:

> **The same telecom brain that explains yesterday's incident can help prevent tomorrow's outage.**

---

# Final Principle

> Do not predict the future blindly. Stress-test what is known, expose what is fragile, state what is uncertain, and act before failure becomes customer impact.

H4 validates whether FikraCore can turn accumulated operational knowledge into proactive resilience intelligence.
