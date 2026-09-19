# FikraCore Simulator Lab — Unified Scenario Library Fix Plan

## 1. Objective

Fix the Simulator Lab so it no longer behaves as an H4-only scenario browser.

The Scenario Library should expose the full FikraCore conceptual capability model:

**Understand → Discover → Learn → Anticipate**

with the internal validation mapping:

| Conceptual Model | Internal Stage | Primary Capability |
|---|---|---|
| Understand | H1 | Investigate / Reason |
| Discover | H2 | Knowledge Gap Discovery |
| Learn | H3 | Curated Learning |
| Anticipate | H4 | Predict / What-if / Resilience |

`DEMO-001` should therefore appear under **Understand** when its scenario definition contains `stage: H1`.

## 2. Current Problem

The current Simulator Lab is displaying primarily H4 scenarios such as:

```text
H4-WI-001
H4-WI-002
H4-WI-003
...
```

while scenarios such as:

```text
DEMO-001
```

are not visible in the library.

This indicates that one or more parts of the current Scenario Library path are probably:

- defaulting to `H4`;
- filtering the scenario catalog by `stage == H4`;
- reading only the H4 run/scenario directory;
- calling an API with `stage=H4`;
- or building the frontend list from an H4-specific scenario source.

The Simulator Lab should instead consume one unified scenario catalog.

## 3. Target User Experience

The Scenario Library should become capability-aware.

Recommended top-level filters:

```text
[ All ] [ Understand ] [ Discover ] [ Learn ] [ Anticipate ]
```

Example:

```text
SCENARIO LIBRARY

Understand
────────────────────────────────────
Transport-Induced Mobile Data Degradation
DEMO-001 · Transport, RAN, Mobile Core

SGi Throughput Degradation & MTU Blackhole
H1-INC-001 · Transport, Mobile Core

Discover
────────────────────────────────────
Missing OCS Charging Dependency
H2-GAP-001 · Mobile Core, OCS

Learn
────────────────────────────────────
Validated Charging Dependency
H3-LRN-001 · Mobile Core, OCS

Anticipate
────────────────────────────────────
MPLS Edge Router Failure
H4-WI-001 · Transport
```

The human-facing labels should be:

```text
H1 → Understand
H2 → Discover
H3 → Learn
H4 → Anticipate
```

The internal H1-H4 values should still remain available for automation, benchmarking, regression testing, internal identifiers, artifact naming, and compatibility with existing implementations.

## 4. Architecture Principle

Do not create separate Scenario Library implementations for H1, H2, H3 and H4.

Use one shared path:

```text
                  Unified Scenario Catalog
                           │
           ┌───────────────┼───────────────┐
           │               │               │
         CLI          Simulator Lab       Zaki
           │               │               │
           └───────────────┼───────────────┘
                           │
                    Scenario Resolver
                           │
                 Capability / Run Resolver
                           │
         H1 / H2 / H3 / H4 Execution Engines
```

The Scenario Library should be a projection of the same backend scenario catalog used by the rest of FikraCore.

## 5. Step 1 — Identify the H4-Only Filter

Search the backend and frontend for hard-coded H4 filtering.

```bash
grep -R '"H4"' \
services/agents/src/engine_stack/engines/telecom_brain \
--include="*.py" \
--include="*.ts" \
--include="*.tsx"
```

Also search:

```bash
grep -R "stage.*H4" \
services/agents/src \
--include="*.py" \
--include="*.ts" \
--include="*.tsx"
```

And:

```bash
grep -R "h4_runs" services/agents/src
```

Look for patterns such as:

```python
stage = stage or "H4"
```

```python
scenarios = [s for s in scenarios if s.stage == "H4"]
```

```ts
scenarios.filter((s) => s.stage === "H4")
```

```ts
useState("H4")
```

```text
GET /scenarios?stage=H4
```

or direct loading from:

```text
simulator/h4_runs/
```

The first goal is to identify which layer is limiting the UI.

## 6. Step 2 — Create One Unified Scenario Catalog

The backend should expose all scenario definitions through a single catalog.

Recommended logical source:

```text
telecom_brain/
└── simulator/
    ├── scenarios/
    │   ├── DEMO-001-transport-mobile-data.yaml
    │   └── ...
    ├── h2_runs/
    ├── h4_runs/
    └── scenario_catalog.py
```

The catalog should normalize scenarios from:

- authored declarative scenario YAMLs;
- existing H1 scenario definitions;
- H2 generated scenarios;
- H3 learning units where appropriate;
- H4 what-if scenarios;
- legacy scenarios such as `SCN-001`.

The UI should never need to know which physical folder originally contained the scenario.

## 7. Step 3 — Normalize the Scenario Contract

Every scenario exposed to the UI should have a common metadata contract.

Recommended model:

```json
{
  "id": "DEMO-001",
  "display_name": "Transport-Induced Mobile Data Degradation",
  "stage": "H1",
  "concept": "Understand",
  "scenario_type": "INCIDENT",
  "domains": ["Transport", "RAN", "Mobile Core"],
  "description": "Cross-domain transport-induced mobile data degradation.",
  "aliases": [],
  "demo_enabled": true,
  "source": "DECLARATIVE_SCENARIO"
}
```

For H4:

```json
{
  "id": "H4-WI-001",
  "display_name": "MPLS Edge Router Failure",
  "stage": "H4",
  "concept": "Anticipate",
  "scenario_type": "WHAT_IF",
  "domains": ["Transport"],
  "demo_enabled": true
}
```

For H3:

```json
{
  "id": "H3-LRN-001",
  "display_name": "Validated OCS Dependency",
  "stage": "H3",
  "concept": "Learn",
  "scenario_type": "LEARNING_UNIT",
  "domains": ["Mobile Core", "OCS"]
}
```

## 8. Step 4 — Centralize Stage-to-Concept Mapping

Create one shared mapping:

```python
STAGE_CONCEPT_MAP = {
    "H1": "Understand",
    "H2": "Discover",
    "H3": "Learn",
    "H4": "Anticipate",
}
```

Do not duplicate this mapping in multiple UI components.

Recommended terminology policy:

```text
Internal validation stage:
H1 / H2 / H3 / H4

Conceptual management model:
Understand / Discover / Learn / Anticipate

Operator capability:
Investigate / Discover / Learn / Predict
```

Example:

```text
H1
Concept = Understand
Operator Action = Investigate
```

## 9. Step 5 — Fix the Backend Scenario Listing API

The backend listing API must not default to H4.

Incorrect:

```python
def list_scenarios(stage="H4"):
    ...
```

Correct:

```python
def list_scenarios(stage=None):
    scenarios = scenario_catalog.all()

    if stage:
        scenarios = [
            scenario
            for scenario in scenarios
            if scenario.stage.upper() == stage.upper()
        ]

    return scenarios
```

Expected behavior:

```text
GET /scenarios
```

returns all scenarios.

Optional filters:

```text
GET /scenarios?stage=H1
GET /scenarios?stage=H2
GET /scenarios?stage=H3
GET /scenarios?stage=H4
```

If the API currently works from run directories rather than scenario definitions, split these concepts:

```text
Scenario Catalog ≠ Run Catalog
```

A scenario may exist before it has ever been executed.

## 10. Step 6 — Ensure DEMO-001 Is Discoverable

`DEMO-001-transport-mobile-data.yaml` should contain at minimum:

```yaml
id: DEMO-001

display_name: Transport-Induced Mobile Data Degradation

stage: H1

domains:
  - Transport
  - RAN
  - Mobile Core

scenario_type: INCIDENT

demo_enabled: true
```

The catalog should automatically derive:

```text
stage   = H1
concept = Understand
```

The user should not need to manually add `DEMO-001` to a separate frontend list.

## 11. Step 7 — Fix the Frontend Default Filter

The Simulator Lab should default to:

```ts
const [activeConcept, setActiveConcept] = useState("ALL");
```

Not:

```ts
useState("H4");
```

Recommended UI filters:

```ts
const filters = [
  "ALL",
  "UNDERSTAND",
  "DISCOVER",
  "LEARN",
  "ANTICIPATE",
];
```

Filtering:

```ts
const visibleScenarios =
  activeConcept === "ALL"
    ? scenarios
    : scenarios.filter(
        (scenario) =>
          scenario.concept.toUpperCase() === activeConcept
      );
```

## 12. Step 8 — Group Instead of Only Filter

For the best Simulator Lab experience, support both filter mode and grouped-all mode.

When `All` is selected:

```text
Understand
  scenario...

Discover
  scenario...

Learn
  learning unit...

Anticipate
  scenario...
```

This makes the FikraCore conceptual journey visible directly inside the Simulator Lab.

## 13. Step 9 — Fix Scenario Card Labels

Do not show `H4` as the only prominent capability badge.

Recommended card:

```text
Transport-Induced Mobile Data Degradation        Understand
DEMO-001 · Transport, RAN, Mobile Core
```

Optionally show internal stage smaller:

```text
Understand · H1
```

For H4:

```text
MPLS Edge Router Failure                         Anticipate
H4-WI-001 · Transport
```

## 14. Step 10 — Handle Legacy SCN-* IDs

Existing scenarios such as `SCN-001` should not be deleted immediately.

Normalize them into the unified catalog.

Example:

```json
{
  "id": "SCN-001",
  "display_name": "SGi Throughput Degradation & MTU Blackhole",
  "stage": "H1",
  "concept": "Understand",
  "scenario_type": "INCIDENT",
  "legacy": true
}
```

Longer term, optionally introduce a canonical ID such as:

```text
H1-INC-001
```

and keep `SCN-001` as a legacy alias.

Do not break existing benchmarks or stored runs just for naming consistency.

## 15. Step 11 — Treat H3 Differently but Keep It Unified

H3 is not always a normal incident scenario.

It may represent:

```text
candidate knowledge
→ SME validation
→ FCAPS classification
→ knowledge promotion
```

Therefore use:

```text
scenario_type = LEARNING_UNIT
```

but expose it under the same **Learn** conceptual group.

## 16. Step 12 — Scenario Selection Must Resolve or Create a Run

Selecting a scenario in the library should not require a pre-existing run.

Required flow:

```text
User selects DEMO-001
        ↓
Scenario definition resolved
        ↓
Existing active/latest run?
      /             \
    yes              no
     ↓                ↓
Select run       Create new run
      \              /
       ↓            ↓
      authoritative run_id
              ↓
      fetch full snapshot
              ↓
       hydrate Simulator Lab
```

This is especially important for new declarative scenarios such as `DEMO-001`.

## 17. Step 13 — Preserve Scenario / Run Separation

### Scenario Definition

```text
id
display_name
stage
concept
domains
services
description
difficulty
scenario_type
supported capabilities
```

### Run State

```text
run_id
scenario_id
current_stage
status
events
topology
evidence
hypotheses
impact
knowledge gaps
learning state
resilience state
sequence
snapshot version
```

Do not build the Scenario Library only from existing run directories.

Otherwise a newly created scenario definition will remain invisible until manually executed.

## 18. Step 14 — Keep the Existing Simulation Pipeline

Do not rename the simulator execution stages to:

```text
Understand
Discover
Learn
Anticipate
```

Those are conceptual capability groups.

The runtime simulation journey remains:

```text
TRIGGER
   ↓
SIGNAL_FLOOD
   ↓
CORRELATION
   ↓
HYPOTHESIS_GENERATION
   ↓
HYPOTHESIS_TESTING
   ↓
KNOWLEDGE_GAP_CHECK
   ↓
LEARNING_VALIDATION
   ↓
ACTION
```

Relationship:

```text
Understand
  └─ Trigger
     Signal Flood
     Correlation
     Hypothesis Generation
     Hypothesis Testing

Discover
  └─ Knowledge Gap Check

Learn
  └─ Learning Validation / Curated Learning

Anticipate
  └─ H4 proactive what-if / resilience execution
```

The conceptual model and runtime state machine should remain distinct.

## 19. Step 15 — Fix Scenario Library Backend-to-Frontend Flow

Target flow:

```text
Scenario Definitions / Generated Scenario Metadata
                     ↓
             Scenario Catalog
                     ↓
            Scenario Resolver
                     ↓
           Scenario List API
                     ↓
          Simulator Lab Store
                     ↓
   All / Understand / Discover /
         Learn / Anticipate
                     ↓
              Scenario Card
                     ↓
          Resolve/Create Run
                     ↓
         Authoritative Snapshot
                     ↓
            Simulation Panels
```

## 20. Recommended Backend Components

Use or extend:

```text
telecom_brain/
├── simulator/
│   ├── scenarios/
│   ├── scenario_catalog.py
│   ├── scenario_loader.py
│   ├── scenario_compiler.py
│   └── scenario_runtime.py
│
├── presentation/
│   ├── scenario_resolver.py
│   └── naming.py
│
├── capabilities/
│   ├── investigate.py
│   ├── discover.py
│   ├── learn.py
│   ├── predict.py
│   ├── simulate.py
│   └── present.py
│
└── api/
    └── capability_api.py
```

Reuse existing components where they already exist.

Do not create duplicate reasoning engines or separate scenario resolvers per capability.

## 21. Recommended API Contract

Example:

```text
GET /api/v1/fikracore/scenarios
```

Response:

```json
{
  "scenarios": [
    {
      "id": "DEMO-001",
      "display_name": "Transport-Induced Mobile Data Degradation",
      "stage": "H1",
      "concept": "Understand",
      "scenario_type": "INCIDENT",
      "domains": ["Transport", "RAN", "Mobile Core"]
    },
    {
      "id": "H4-WI-001",
      "display_name": "MPLS Edge Router Failure",
      "stage": "H4",
      "concept": "Anticipate",
      "scenario_type": "WHAT_IF",
      "domains": ["Transport"]
    }
  ]
}
```

## 22. Recommended UI Layout

```text
┌─────────────────────────────────────────────────────┐
│ SCENARIO LIBRARY                                    │
│                                                     │
│ [All] [Understand] [Discover] [Learn] [Anticipate] │
├─────────────────────────────────────────────────────┤
│ Transport-Induced Mobile Data Degradation           │
│ DEMO-001 · Transport, RAN, Mobile Core              │
│                                         Understand  │
├─────────────────────────────────────────────────────┤
│ Missing OCS Dependency                              │
│ H2-GAP-001 · Mobile Core, OCS                       │
│                                           Discover  │
├─────────────────────────────────────────────────────┤
│ MPLS Edge Router Failure                            │
│ H4-WI-001 · Transport                               │
│                                         Anticipate  │
└─────────────────────────────────────────────────────┘
```

## 23. Tests to Add

### Catalog Tests

```text
test_catalog_returns_h1_scenarios
test_catalog_returns_h2_scenarios
test_catalog_returns_h3_learning_units
test_catalog_returns_h4_scenarios
test_catalog_returns_demo_001
test_catalog_does_not_default_to_h4
```

### Mapping Tests

```text
test_h1_maps_to_understand
test_h2_maps_to_discover
test_h3_maps_to_learn
test_h4_maps_to_anticipate
```

### UI Tests

```text
test_all_filter_shows_all_capabilities
test_understand_filter_shows_h1
test_discover_filter_shows_h2
test_learn_filter_shows_h3
test_anticipate_filter_shows_h4
test_default_filter_is_all
```

### Scenario Selection Tests

```text
test_select_demo_001_resolves_h1
test_select_new_scenario_creates_run_if_missing
test_select_existing_scenario_reuses_or_selects_run
test_selected_run_matches_selected_scenario
```

### Regression Tests

```text
test_existing_h4_scenarios_still_visible
test_existing_h2_benchmarks_still_work
test_existing_h4_benchmarks_still_work
test_legacy_scn_001_still_resolves
```

## 24. Acceptance Criteria

The fix is complete when:

```text
[ ] Simulator Lab no longer defaults to H4-only
[ ] All four conceptual groups are available
[ ] All is the default library view
[ ] H1 is presented as Understand
[ ] H2 is presented as Discover
[ ] H3 is presented as Learn
[ ] H4 is presented as Anticipate
[ ] DEMO-001 appears under Understand
[ ] H4-WI-001 appears under Anticipate
[ ] legacy SCN-* scenarios remain resolvable
[ ] H3 learning units can be represented cleanly
[ ] scenario definitions are visible before execution
[ ] selecting a scenario resolves or creates a run
[ ] run_id remains authoritative after selection
[ ] Simulator Lab snapshot matches selected scenario/run
[ ] Zaki receives the same scenario_id/run_id
[ ] no duplicate scenario-resolution logic is introduced
[ ] H1-H4 benchmark behavior remains unchanged
```

## 25. Recommended Implementation Order

```text
1. Find/remove H4-only default/filter
            ↓
2. Build/extend unified Scenario Catalog
            ↓
3. Normalize scenario metadata
            ↓
4. Add H1-H4 → conceptual-name mapping
            ↓
5. Expose all scenarios from backend API
            ↓
6. Change frontend default to All
            ↓
7. Add conceptual filters/groups
            ↓
8. Verify DEMO-001 under Understand
            ↓
9. Connect scenario selection to run resolution
            ↓
10. Add regression and UI tests
```

Do not begin by changing H1-H4 reasoning logic.

This is primarily a:

```text
scenario catalog
+
metadata normalization
+
scenario/run resolution
+
Simulator Lab presentation
```

fix.

## 26. Final Target

```text
                    FikraCore Simulator Lab

                         Scenario Library
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   Understand              Discover                Learn
      H1                      H2                     H3
 Investigate            Find Unknowns         Curated Learning
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                           Anticipate
                              H4
                     What-if & Resilience
                               │
                               ▼
                      Selected Scenario
                               │
                      Resolve/Create Run
                               │
                       Simulation Pipeline
                               │
       Trigger → Signal Flood → Correlation → Reasoning
             → Gap Check → Validation → Action
                               │
                               ▼
                   Simulator Lab / Zaki / Storyteller
```

### Core Rule

> **H1-H4 remain internal capability-validation stages. Understand → Discover → Learn → Anticipate is the human-readable conceptual model. The Simulator Lab should expose all four through one unified Scenario Library.**
