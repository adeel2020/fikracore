# FikraCore Step 5 — Epistemic Sequencing & Stage-Gated Reasoning Fix

## Purpose

Fix the simulator behavior where conclusions appear before FikraCore has visibly earned them through the investigation lifecycle.

Observed issues:

```text
hypotheses already ranked before Hypothesis Testing
root-cause-like graph state shown too early
ambiguous event names already containing interpretation
service impact quantified before causal reasoning is explained
knowledge gaps shown before the unknown boundary is established
Zaki describes activity but not what changed, why, or what remains unknown
```

The simulator must stop behaving like a precomputed answer with an animated progress bar.

Required behavior:

```text
Evidence becomes available
        ↓
FikraCore updates current belief
        ↓
Only stage-justified information becomes visible
        ↓
Next reasoning stage executes
        ↓
UI evolves
```

> **Never display knowledge before FikraCore has earned it through the visible reasoning lifecycle.**

---

# 1. Required Reasoning Lifecycle

Use:

```text
OBSERVE
  ↓
CORRELATE
  ↓
GENERATE CANDIDATES
  ↓
RANK
  ↓
TEST
  ↓
FALSIFY / SUPPORT
  ↓
DISCOVER UNKNOWN
  ↓
VALIDATE
  ↓
LEARN
  ↓
RECOMMEND
```

Do not pre-populate later-stage outputs at the beginning of a run.

---

# 2. Separate Health, Reasoning Role, and Knowledge State

## Network Health

```text
HEALTHY
DEGRADED
FAILED
UNKNOWN
```

## Reasoning Role

```text
UNSEEN
OBSERVED
SYMPTOM
CANDIDATE_CAUSE
ROOT_CANDIDATE
CONFIRMED_CAUSE
REJECTED
COINCIDENTAL
UNKNOWN
```

## Knowledge State

```text
KNOWN
INFERRED
CANDIDATE
UNKNOWN
STALE
REJECTED
```

Example early:

```text
DRA-01
Health: DEGRADED
Reasoning: OBSERVED
Knowledge: KNOWN
```

Later:

```text
DRA-01
Health: DEGRADED
Reasoning: CANDIDATE_CAUSE
Confidence: 43%
```

Only after testing:

```text
Shared NTP Source
Reasoning: ROOT_CANDIDATE
Confidence: 82%
```

---

# 3. Stage-Gated Disclosure

The simulator should expose only information justified by the active stage.

Recommended logical stages:

```text
0 Trigger
1 Signal Flood
2 Correlation
3 Hypothesis Generation
4 Hypothesis Testing
5 Knowledge Gap Check
6 Learning / Validation
7 Action / Recommendation
```

If the visible UI keeps 7 stages, introduce internal sub-stages as needed.

---

# 4. Stage 0 — Trigger

Purpose:

```text
Something happened.
```

Allowed visibility:

```text
first observed event
affected observed entity
timestamp
severity
raw source
```

Do not show:

```text
ranked hypotheses
root candidate
confirmed causal path
confirmed service impact
blast radius
knowledge-gap conclusion
learning candidate
recommendation
```

Example:

```text
Observed:
DRA-01 alarm received

Known:
entity
timestamp
severity

Unknown:
whether DRA-01 is causal
service impact
shared dependency
root cause
blast radius
```

Graph:

```text
DRA-01
OBSERVED ALARM
```

Not:

```text
DRA-01
ROOT CAUSE
```

---

# 5. Stage 1 — Signal Flood

Purpose:

```text
Collect raw observations.
```

Good event names:

```text
DRA-01 NTP offset threshold exceeded
DRA-02 NTP offset threshold exceeded
Diameter timeout rate increased on OCS-01
Authentication latency increased
Customer session failures increased
```

Avoid using reasoning conclusions as alarms:

```text
Correlated alarms across multiple domains
Common cause failure pattern detected
Shared dependency degradation
Hypothesis H1 created
```

---

# 6. Event Epistemic Classification

Every event should identify its type.

Example:

```json
{
  "event_id": "EVT-001",
  "event_type": "OBSERVATION",
  "source_type": "ALARM",
  "display_name": "DRA-01 NTP offset threshold exceeded",
  "scenario_id": "H4-WI-016",
  "run_id": "RUN-..."
}
```

Allowed:

```text
OBSERVATION
CORRELATION
HYPOTHESIS
TEST
EVIDENCE_REQUEST
VALIDATION
LEARNING
ACTION
```

The Unified Live Event Stream should primarily show `OBSERVATION` events.

Reasoning events should be visually distinguished or placed in a separate reasoning timeline.

---

# 7. Stage 2 — Correlation

Purpose:

```text
Determine which observations may be related.
```

Allowed:

```text
event groups
temporal clusters
shared entities
shared dependencies
candidate causal relationships
correlation strength
```

Do not yet show:

```text
confirmed root cause
final hypothesis confidence
confirmed causal path
```

Example "What FikraCore Is Doing":

```text
✓ Grouped 7 events inside a 3-minute window
✓ Identified DRA-01 and DRA-02 as sharing an NTP dependency
→ Checking whether clock skew precedes Diameter failures
→ Comparing healthy peers for negative evidence
```

Graph:

```text
candidate path
amber dashed relation
unknown boundary
```

---

# 8. Persistent Reasoning Explanation

Add a compact panel with:

```text
WHAT CHANGED?
WHY DOES IT MATTER?
WHAT IS STILL UNKNOWN?
WHAT IS FIKRACORE DOING NEXT?
```

Example:

```text
What changed?
Two redundant DRA nodes now show clock skew before Diameter failures.

Why does it matter?
A shared dependency may explain both failures better than two independent faults.

Still unknown?
Health of the common NTP source.

Next?
Fetch NTP offset and reachability evidence.
```

This panel must update whenever reasoning state materially changes.

---

# 9. Stage 3 — Hypothesis Generation

Purpose:

```text
Construct plausible explanations.
```

Show candidates without premature certainty.

Example:

```text
Candidate explanations

• Shared time synchronization problem
• DRA software degradation
• Downstream OCS congestion
```

State:

```text
CANDIDATE
UNRANKED
or
INITIAL_RANKING
```

Do not immediately show:

```text
#1 Shared NTP Clock Skew — 82%
```

unless ranking has actually executed.

---

# 10. Hypothesis Candidate Contract

Each candidate should include:

```text
hypothesis_id
display_name
creation_stage
basis
status
```

Example:

```json
{
  "hypothesis_id": "HYP-001",
  "display_name": "Shared NTP Clock Skew",
  "creation_stage": "HYPOTHESIS_GENERATION",
  "basis": [
    "DRA-01 and DRA-02 show time offset anomalies",
    "both depend on a shared clock source"
  ],
  "status": "CANDIDATE"
}
```

---

# 11. Stage 4 — Hypothesis Testing

Purpose:

```text
Rank, test, support, contradict, and falsify candidate explanations.
```

Only here should ranked confidence be presented.

Example:

```text
1. Shared NTP Clock Skew        58%
2. DRA Software Degradation    27%
3. OCS Overload                15%
```

As evidence arrives:

```text
58% → 71% → 82%
```

Every material confidence change must be explained.

---

# 12. Confidence Change Contract

Each update should include:

```text
previous confidence
new confidence
delta
reason
new evidence IDs
```

Example:

```json
{
  "hypothesis_id": "HYP-001",
  "previous_confidence": 0.58,
  "new_confidence": 0.71,
  "delta": 0.13,
  "reason": "Both affected DRA nodes show clock skew before Diameter failures",
  "evidence_ids": ["EVT-011", "EVT-014"]
}
```

UI:

```text
58% → 71%

Why:
Clock skew began before Diameter failures on both affected routing agents.
```

---

# 13. Falsification Must Stay Visible

Rejected hypotheses remain visible.

Example:

```text
DRA Software Degradation
27% → 8%
REJECTED

Why:
A healthy peer using the same software version remained unaffected.
```

---

# 14. Hypothesis State Model

Use:

```text
CANDIDATE
RANKED
TESTING
SUPPORTED
NEEDS_MORE_EVIDENCE
CONTRADICTED
REJECTED
ROOT_CANDIDATE
CONFIRMED
```

Do not display `CONFIRMED` unless the backend state is actually `CONFIRMED`.

---

# 15. Stage 5 — Knowledge Gap Check

Purpose:

```text
Identify what FikraCore cannot establish from current evidence and knowledge.
```

Example:

```text
Known:
DRA-01 and DRA-02 depend on the shared NTP source

Unknown:
Actual health of the shared NTP source

Missing Evidence:
NTP offset history
clock-source reachability
healthy-peer comparison
```

Avoid generic labels such as:

```text
3 key unknowns
```

without explanation.

---

# 16. Unknown Boundary Visualization

Differentiate:

```text
Known path
Candidate relationship
Unknown boundary
Missing entity/relationship
```

Use amber/dashed styling for candidate or unknown relations.

---

# 17. Next-Best Evidence Must Explain Why

Example:

```text
Next Best Evidence:
Fetch NTP offset history from DRA-01 and DRA-02

Why:
It can determine whether clock skew occurred before Diameter failures.

Expected Information Gain:
High
```

Do not show actions without rationale.

---

# 18. Stage 6 — Learning / Validation

Purpose:

```text
Capture only validated operational learning.
```

States:

```text
Candidate Learning
Awaiting Validation
Accepted
Rejected
Modified
Promoted
```

Example:

```text
Candidate Learning

Shared clock skew may cause correlated Diameter failures
across redundant routing agents.

Status:
AWAITING SME VALIDATION
```

Only after validation:

```text
SME Accepted
Eligible for Promotion
```

---

# 19. Stage 7 — Action / Recommendation

Purpose:

```text
Present the strongest supported explanation and recommended next action.
```

Example:

```text
Most Supported Explanation:
Shared NTP Clock Skew

Confidence:
82%

Recommended Next Action:
Validate shared NTP source and restore synchronization

Customer Impact:
~18,000 sessions affected
```

All values must come from the active run.

---

# 20. Service Impact Epistemic State

Impact must also carry status:

```text
OBSERVED
ESTIMATED
INFERRED
CONFIRMED
```

Early:

```text
Customer failures observed
scope still being estimated
```

Later:

```text
Estimated Impact:
~18,000 enterprise sessions
```

Do not present estimates as confirmed facts.

---

# 21. Causal Path Progression

Do not show `Confirmed Causal Path` too early.

Use:

```text
Observed Path
Candidate Dependency Path
Leading Causal Path
Confirmed Causal Path
```

Suggested progression:

```text
Correlation
→ Candidate Dependency Path

Hypothesis Testing
→ Leading Causal Path

Validation
→ Confirmed Causal Path
```

---

# 22. "What FikraCore Is Doing Now"

Avoid:

```text
Busy analyzing the common cause
Analyzing...
Processing...
```

Use specific tasks:

```text
Grouping alarms by timestamp and shared dependency
Comparing DRA-01 and DRA-02 clock offsets
Checking healthy DRA peers for negative evidence
Testing whether Diameter failures follow NTP skew
Requesting missing NTP-source health evidence
```

---

# 23. Zaki as Contextual Narrator

Zaki should explain:

```text
What did we observe?
What changed in FikraCore's belief?
Why did it change?
What remains unknown?
What is being tested next?
```

---

# 24. Zaki Stage Awareness

## Trigger

```text
Only one alarm is currently observed.
There is not enough evidence to identify a cause yet.
```

## Correlation

```text
Several events are now grouped because they share timing and dependency context.
No root cause is confirmed.
```

## Hypothesis Testing

```text
Shared NTP skew is currently ranked first because...
```

## Knowledge Gap

```text
The main unresolved point is...
```

## Action

```text
The strongest validated explanation is...
```

---

# 25. Zaki Must Preserve Uncertainty

If the backend state is:

```text
CANDIDATE
SUPPORTED
ROOT_CANDIDATE
```

Zaki must not say:

```text
The root cause is...
```

Use:

```text
The leading hypothesis is...
```

Only use `confirmed cause` when backend state is `CONFIRMED`.

---

# 26. Backend Reasoning Events

Emit explicit reasoning updates:

```text
observation_added
correlation_created
candidate_hypothesis_created
hypothesis_ranked
hypothesis_test_started
evidence_support_added
evidence_contradiction_added
hypothesis_rejected
root_candidate_changed
knowledge_gap_detected
next_best_evidence_requested
validation_started
validation_completed
learning_candidate_created
recommendation_created
```

---

# 27. Stage-Aware Event Contract

Each reasoning event should include:

```text
scenario_id
run_id
stage
timestamp
```

Example:

```json
{
  "type": "hypothesis_ranked",
  "scenario_id": "H4-WI-016",
  "run_id": "RUN-...",
  "stage": "HYPOTHESIS_TESTING",
  "hypothesis_id": "HYP-001",
  "rank": 1,
  "confidence": 0.58
}
```

The frontend must not render the update before its stage is active.

---

# 28. Snapshot Disclosure State

The run snapshot should include:

```json
{
  "current_stage": "CORRELATION",
  "allowed_disclosures": [
    "observations",
    "correlations",
    "candidate_relationships"
  ]
}
```

Use this to enforce UI gating.

---

# 29. Disclosure Policy

A backend disclosure policy may enforce stage visibility.

Example:

```python
DISCLOSURE_POLICY = {
    "TRIGGER": {
        "observations": True,
        "correlations": False,
        "ranked_hypotheses": False,
        "root_candidate": False,
        "confirmed_path": False,
        "knowledge_gaps": False,
        "recommendations": False,
    },
    "SIGNAL_FLOOD": {
        "observations": True,
        "correlations": False,
        "ranked_hypotheses": False,
        "root_candidate": False,
        "confirmed_path": False,
        "knowledge_gaps": False,
        "recommendations": False,
    },
    "CORRELATION": {
        "observations": True,
        "correlations": True,
        "ranked_hypotheses": False,
        "root_candidate": False,
        "confirmed_path": False,
        "knowledge_gaps": False,
        "recommendations": False,
    },
    "HYPOTHESIS_TESTING": {
        "observations": True,
        "correlations": True,
        "ranked_hypotheses": True,
        "root_candidate": True,
        "confirmed_path": False,
        "knowledge_gaps": True,
        "recommendations": False,
    },
    "ACTION": {
        "observations": True,
        "correlations": True,
        "ranked_hypotheses": True,
        "root_candidate": True,
        "confirmed_path": True,
        "knowledge_gaps": True,
        "recommendations": True,
    },
}
```

Adapt to the implemented stage model.

---

# 30. No Hidden Truth Leakage

Hidden Truth must never pre-populate:

```text
root candidate
hypothesis confidence
causal path
impact
knowledge gap
recommendation
Zaki context
```

Hidden Truth remains evaluator-only.

---

# 31. Observation vs Interpretation Labels

Important statements should use:

```text
OBSERVED
INFERRED
CANDIDATE
CONFIRMED
REJECTED
UNKNOWN
```

This must remain consistent across:

```text
event stream
causal graph
hypotheses
impact
knowledge gaps
Zaki
```

---

# 32. Human-Readable Event Naming

Good:

```text
NTP offset exceeded 120 ms on DRA-01
Diameter timeout rate increased on OCS-01
Session setup failures increased by 14%
```

Bad:

```text
Common cause detected
Correlated failure across domains
Shared dependency failure
```

The latter belong to the reasoning layer.

---

# 33. Causal Graph Visual Rules

Use:

```text
green/cyan = healthy
red = observed symptom/failure
amber dashed = candidate/unknown relation
blue/white = selected/investigated
grey = rejected/irrelevant
```

Do not use root-cause emphasis until reasoning state is `ROOT_CANDIDATE`.

---

# 34. Hypothesis Panel by Stage

Before generation:

```text
No hypotheses generated yet
FikraCore is collecting and correlating evidence.
```

Candidate stage:

```text
3 candidate explanations
Not yet ranked
```

Testing:

```text
rank
confidence
supports
against
missing evidence
confidence changes
```

Confirmed:

```text
confirmed explanation
validation basis
remaining caveats
```

---

# 35. Impact Panel by Stage

Early:

```text
Impact observed
scope still being estimated
```

Mid:

```text
Estimated affected services/users
```

Late:

```text
Validated impact / blast radius
```

Use `Observed`, `Estimated`, and `Confirmed` labels.

---

# 36. Learning Panel by Stage

Before validation:

```text
No validated learning yet
```

Candidate:

```text
Candidate insight
Awaiting SME validation
```

Accepted:

```text
Validated knowledge
Eligible for promotion
```

---

# 37. Required Tests

Add:

```text
test_trigger_stage_has_no_ranked_hypothesis
test_trigger_stage_has_no_root_candidate
test_signal_flood_contains_raw_observations_only
test_correlation_stage_has_no_confirmed_causal_path
test_hypothesis_generation_can_show_unranked_candidates
test_hypothesis_testing_enables_ranking
test_confidence_delta_has_reason
test_rejected_hypothesis_remains_visible
test_knowledge_gap_not_visible_before_detected
test_recommendation_not_visible_before_action_stage
test_learning_not_marked_validated_before_sme_validation
test_zaki_respects_stage_uncertainty
test_hidden_truth_not_used_for_early_disclosure
```

UI tests:

```text
test_graph_root_style_not_visible_before_root_candidate
test_confirmed_path_label_not_visible_before_validation
test_event_stream_does_not_label_reasoning_as_alarm
test_impact_status_changes_observed_to_estimated_to_confirmed
test_reasoning_explanation_panel_updates_with_state
```

Backend tests:

```text
test_reasoning_events_have_stage
test_reasoning_events_have_scenario_and_run_id
test_hypothesis_rank_event_occurs_after_candidate_creation
test_confirmation_occurs_after_testing
test_learning_candidate_occurs_after_validation_input
```

---

# 38. Acceptance Walkthrough

Use one scenario with a non-trivial shared dependency.

Expected progression:

```text
Stage 0:
one raw observation only

Stage 1:
several factual observations

Stage 2:
candidate correlations appear

Stage 3:
candidate hypotheses appear, initially unranked

Stage 4:
hypotheses become ranked and confidence evolves

Stage 5:
knowledge gap becomes explicit

Stage 6:
candidate learning appears only after validation workflow begins

Stage 7:
recommendation and final supported explanation appear
```

At every stage verify that the explanation panel answers:

```text
What changed?
Why does it matter?
What remains unknown?
What happens next?
```

---

# 39. Definition of Done

```text
[ ] Trigger shows only justified observations
[ ] raw event names are factual and unambiguous
[ ] correlation outputs are separate from raw alarms
[ ] hypotheses are not fully ranked before ranking occurs
[ ] confidence changes are explained
[ ] graph does not reveal root cause early
[ ] causal paths progress candidate → leading → confirmed
[ ] impact is labeled observed / estimated / confirmed
[ ] knowledge gaps appear only when discovered
[ ] next-best evidence includes rationale
[ ] learning is candidate-first and SME-validated
[ ] recommendations appear only at the appropriate stage
[ ] Zaki explains what changed, why, unknowns, and next action
[ ] Zaki preserves uncertainty
[ ] backend emits stage-aware reasoning events
[ ] frontend enforces stage-aware disclosure
[ ] Hidden Truth remains isolated
```

---

# Final Principle

> **The simulator must show FikraCore earning its conclusion, not reveal the conclusion first and animate the reasoning afterward.**

> **At every stage, the operator should understand what was observed, what FikraCore currently believes, why that belief changed, what remains unknown, and what happens next.**
