# FikraCore Simulator — Step 4.1 Hypothesis Engine Benchmark Diagnosis & Calibration

## Purpose

This step follows completion of the CLI-first FikraCore Hypothesis / Investigation Engine MVP and its initial 100-scenario benchmark.

The implementation is complete, but the benchmark indicates a gap between candidate generation quality and strict final-decision quality.

Observed benchmark summary:

```text
Total Runs: 100
Root Cause Top-3 Accuracy: 100%
Method B (FikraCore Hypothesis Reasoning) Correct: 62 / 100
Method A (Earliest Severe Alarm Baseline) Correct: 75 / 100
Avg Steps to First Useful Hypothesis: 2.01
Avg Explanation Provenance Quality: 0.967

Terminal States:
EXPLAINED: 75
MODEL_INSUFFICIENT: 19
PARTIALLY_EXPLAINED: 6
```

The purpose of Step 4.1 is to determine why Method B underperforms the simple baseline on strict final decisions despite 100% Root Cause Top-3 accuracy, and to make only generalizable calibration corrections.

This is a diagnosis and calibration phase, not a topology expansion phase. Do not regenerate scenarios, hidden truth, seeds, or evaluator expectations.

---

# 1. Core Research Question

Answer:

> Why does the correct root cause appear in the Top-3 for all benchmark runs, yet Method B reaches the correct strict final decision in only 62% of runs?

Separate the answer into:

- Candidate generation
- Ranking
- Confidence calibration
- Terminal-state classification
- Knowledge sufficiency detection
- Evidence sufficiency detection
- Canonical entity resolution
- Evaluator strictness

Do not collapse all failures into one accuracy number.

---

# 2. Preserve the Benchmark

Do not modify:

```text
Reference Operator Model
100 Scenario Catalog
Generated Hidden Truth
Scenario seeds
Scenario difficulty metadata
Evaluator expectations
```

The same 100 scenarios must be used before and after calibration.

Do not manually edit scenarios based on failures.

---

# 3. Current Architecture

Keep the architecture unchanged:

```text
Scenario Generator
        ↓
Scenario Integrity Validator
        ↓
Operational Evidence
        +
FikraCore telecombrain
        ↓
CanonicalResolver
        ↓
KnowledgeProvider
        ↓
Hypothesis / Investigation Engine
        ↓
InvestigationResult
        ↓
Benchmark Evaluator
        ↑
Hidden Ground Truth
```

The validator must be a hard gate before hypothesis reasoning.

---

# 4. Epistemic Boundary

Preserve:

```text
Hidden Ground Truth → Evaluator only
```

Forbidden:

```text
Hidden Ground Truth → Hypothesis Engine
Hidden Ground Truth → telecombrain
Hidden Ground Truth → runtime calibration features
```

Calibration may analyze prior benchmark outputs offline, but production reasoning remains truth-blind.

---

# 5. Failure Taxonomy

Classify every Method B failure into one or more categories:

```text
A. Correct root ranked #2/#3, wrong root selected
B. Correct root ranked #1, wrong terminal state
C. False MODEL_INSUFFICIENT
D. False PARTIALLY_EXPLAINED
E. Canonical entity/alias mismatch
F. Causal-role mismatch
G. Confidence threshold too conservative
H. Negative-evidence penalty too aggressive
I. Topology traversal/direction/dependency-scoring problem
J. Evidence sufficiency logic too conservative
K. Change correlation over-weighted
L. Symptom node over-ranked as root
M. Shared-dependency/common-cause ranking failure
N. Multi-cause reduction to single root
O. Evaluator semantic mismatch
P. Other/uncategorized
```

A run may have multiple categories.

---

# 6. Failure-Level Diagnostic Record

For every run, generate:

```json
{
  "run_id": "RUN-SCN-001",
  "scenario_id": "SCN-001",
  "difficulty": "L1",
  "scenario_category": "...",
  "expected_root_entity": "...",
  "expected_terminal_state": "...",
  "method_b_top1": "...",
  "method_b_top2": "...",
  "method_b_top3": "...",
  "true_root_rank": 1,
  "method_b_terminal_state": "...",
  "method_b_strict_correct": true,
  "top1_score": 0.82,
  "true_root_score": 0.82,
  "explanation_coverage": 0.91,
  "unexplained_residual": 0.09,
  "knowledge_gap_detected": false,
  "evidence_requests": 2,
  "failure_categories": [],
  "diagnostic_notes": [],
  "recommended_general_fix": null
}
```

Output:

```text
artifacts/hypothesis/calibration/run-diagnostics.jsonl
```

---

# 7. Separate Ranking From Terminal-State Accuracy

Add these independent metrics:

```text
Top-1 Root Entity Accuracy
Top-2 Root Entity Accuracy
Top-3 Root Entity Accuracy
Terminal-State Accuracy
Strict Final-Decision Accuracy
```

Also report:

```text
Correct Top-1 Root + Wrong Terminal State
Wrong Top-1 Root + Correct Root in Top-3
Correct Root Not in Top-3
Canonicalization mismatch count
```

---

# 8. Terminal-State Confusion Matrix

Expected situation classes:

```text
RCA_IDENTIFIABLE
RCA_PARTIALLY_IDENTIFIABLE
KNOWLEDGE_MISSING
EVIDENCE_INSUFFICIENT
CONFLICTING_EVIDENCE
```

Predicted terminal states:

```text
EXPLAINED
PARTIALLY_EXPLAINED
MODEL_INSUFFICIENT
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
UNRESOLVED
```

Output:

```text
artifacts/hypothesis/calibration/terminal-state-confusion.json
artifacts/hypothesis/calibration/terminal-state-confusion.md
```

---

# 9. MODEL_INSUFFICIENT Audit

There are currently 19 MODEL_INSUFFICIENT outcomes.

Classify each:

```text
TRUE_MODEL_GAP
FALSE_MODEL_GAP
AMBIGUOUS_MODEL_GAP
```

For each run answer:

```text
Was a necessary relationship absent from operational knowledge?
Could the root still be identified from available knowledge?
Was the correct root already Top-1?
Did unexplained residual genuinely require missing topology?
Was model-insufficiency threshold too aggressive?
```

---

# 10. PARTIALLY_EXPLAINED Audit

There are currently 6 PARTIALLY_EXPLAINED outcomes.

Classify:

```text
CORRECTLY_PARTIAL
FALSELY_PARTIAL
```

Check:

```text
root entity correctness
explanation coverage
remaining residual importance
missing evidence necessity
threshold conservatism
```

---

# 11. Slice by Difficulty

Report all major metrics by:

```text
L1
L2
L3
L4
L5
```

For each:

```text
Method A accuracy
Method B strict accuracy
Top-1 root accuracy
Top-3 root accuracy
Terminal-state accuracy
MODEL_INSUFFICIENT rate
PARTIALLY_EXPLAINED rate
Average evidence requests
Average reasoning steps
Average explanation coverage
```

Output:

```text
artifacts/hypothesis/calibration/by-difficulty.json
artifacts/hypothesis/calibration/by-difficulty.md
```

---

# 12. Slice by Scenario Category

Use the existing 100-scenario taxonomy.

At minimum group by:

```text
cascading failure
common cause
control-plane amplification
signaling storm
gray failure
routing issue
resource exhaustion
failover overload
change-induced
observability blind spot
multi-cause
recovery surge
external dependency
split-brain
security
acceptance
microburst/asymmetry
transient topology
power/environment
shared infrastructure
```

For each category compare Method A and Method B.

Question:

> In which scenario classes does causal reasoning add value, and in which classes does the simple alarm heuristic remain stronger?

---

# 13. Root-Rank Distribution

Calculate:

```text
rank 1
rank 2
rank 3
not in top 3
```

If Top-3 remains 100%, quantify:

```text
rank-1 but wrong terminal state
rank-2
rank-3
```

---

# 14. Score-Margin Analysis

For every run compute:

```text
top1_score
top2_score
score_margin = top1_score - top2_score
true_root_score
```

Analyze correctness by buckets:

```text
0.00–0.02
0.02–0.05
0.05–0.10
>0.10
```

---

# 15. Confidence Calibration

Create confidence buckets:

```text
0.0–0.1
0.1–0.2
...
0.9–1.0
```

For each calculate:

```text
mean predicted confidence
actual correctness rate
sample count
```

Calculate a simple calibration-error metric.

---

# 16. Explanation-Coverage Calibration

Test whether explanation_coverage meaningfully predicts:

```text
EXPLAINED
PARTIALLY_EXPLAINED
MODEL_INSUFFICIENT
```

Detect pathologies such as:

```text
correct root
high support
high explanation coverage
small residual
→ MODEL_INSUFFICIENT
```

---

# 17. Negative Evidence Analysis

For every wrong decision record:

```text
negative-evidence penalties by hypothesis
evidence responsible
whether penalty was independent
whether missing telemetry was treated as healthy telemetry
```

Do not treat:

```text
absence of evidence
```

as equivalent to:

```text
explicit evidence of health
```

without justification.

---

# 18. Temporal Scoring Analysis

Check whether these are overweighted:

```text
earliest alarm
latest alarm
ingestion delay
source clock skew
```

Method B must not become Method A with additional complexity.

---

# 19. Change-Correlation Analysis

For noisy and change-induced scenarios evaluate:

```text
change temporal proximity
change topology relevance
change service relevance
independent support
```

Do not equate temporal proximity with causality.

---

# 20. Topology Traversal Analysis

Inspect failed runs for:

```text
traversal start node
path discovered
path direction
depth
canonical entities
missing edge
edge confidence
shared failure domain
```

Classify:

```text
wrong traversal direction
insufficient depth
missing topology
incorrect service mapping
canonical mismatch
shared dependency not considered
```

---

# 21. Canonicalization Diagnostics

For every run verify:

```text
source-native entity
requested slug
resolved canonical slug
knowledge-provider entity
evaluator root entity
```

Output:

```text
artifacts/hypothesis/calibration/canonical-resolution-report.json
```

---

# 22. Knowledge vs Evidence Sufficiency

Do not conflate:

```text
MODEL_INSUFFICIENT
```

with:

```text
INSUFFICIENT_EVIDENCE
```

Use MODEL_INSUFFICIENT when the operational model cannot represent the observed propagation.

Use INSUFFICIENT_EVIDENCE when the model supports plausible paths but evidence cannot discriminate them.

Add tests for this distinction.

---

# 23. Multi-Cause / Common-Cause Analysis

Audit whether strict evaluator semantics match the intended causal model.

Compare:

```text
single root
common cause
contributing condition
multi-cause
```

Do not force single-root logic where the scenario is truly multi-causal.

---

# 24. Evaluator Audit

Verify independently:

```text
root entity comparison
canonical alias comparison
terminal-state expectation
multi-cause handling
partial explanation handling
proper abstention handling
```

Classify evaluator issues as:

```text
EVALUATOR_SEMANTIC_MISMATCH
```

Do not loosen evaluator rules just to improve Method B score.

---

# 25. Baseline Audit

For Method A report:

```text
categories where baseline wins
categories where Method B wins
categories where both win
categories where both fail
```

---

# 26. Generalizable Calibration Only

Allowed:

```text
confidence thresholds
terminal-state thresholds
score normalization
negative-evidence weighting
score-margin handling
knowledge-gap criteria
evidence-gap criteria
common-cause handling
canonical comparison logic
```

Forbidden:

```text
if scenario_id == ...
if entity == ...
special-case scenario hacks
manual answer maps
hidden truth hints
```

Add tests to detect scenario-specific calibration.

---

# 27. Calibration / Validation / Holdout

Use deterministic stratified splits:

```text
Calibration: 60
Validation: 20
Holdout: 20
```

Stratify by:

```text
difficulty
scenario category
known/unknown RCA
```

Workflow:

```text
descriptive diagnosis
        ↓
tune on calibration
        ↓
select on validation
        ↓
freeze policy
        ↓
run holdout once
        ↓
run full 100 with frozen policy
```

Do not tune against holdout.

---

# 28. Preserve Original Benchmark

Store immutable original results under:

```text
artifacts/hypothesis/calibration/before/
```

Store calibrated results under:

```text
artifacts/hypothesis/calibration/after/
```

Never overwrite the original aggregate report.

---

# 29. Required Reports

Generate:

```text
artifacts/hypothesis/calibration/
├── run-diagnostics.jsonl
├── failure-taxonomy.json
├── failure-taxonomy.md
├── terminal-state-confusion.json
├── terminal-state-confusion.md
├── by-difficulty.json
├── by-difficulty.md
├── by-category.json
├── by-category.md
├── rank-analysis.json
├── score-margin-analysis.json
├── confidence-calibration.json
├── canonical-resolution-report.json
├── evaluator-audit.json
├── baseline-comparison.json
├── calibration-changes.md
├── before/
├── after/
└── final-calibration-report.md
```

---

# 30. Required CLI Commands

Add commands similar to:

```bash
fikracore-mvp diagnose-benchmark
fikracore-mvp diagnose-run RUN-SCN-042
fikracore-mvp calibration-report
fikracore-mvp benchmark --split calibration
fikracore-mvp benchmark --split validation
fikracore-mvp benchmark --split holdout
```

Adapt to existing CLI naming.

---

# 31. Required Tests

Add at least:

```text
test_true_root_rank_metrics
test_terminal_state_confusion
test_model_vs_evidence_insufficient
test_confidence_calibration_buckets
test_score_margin_behavior
test_negative_evidence_missing_vs_healthy
test_canonical_root_equivalence
test_no_scenario_specific_calibration
test_holdout_not_used_for_tuning
test_original_benchmark_immutable
```

---

# 32. Success Criteria

Success is not 100% Method B accuracy.

Success means:

```text
failure modes are explained
ranking and terminal-state errors are separated
calibration is evidence-based
no truth leakage
no scenario-specific overfitting
Method B value is clear by scenario type
holdout performance is measured honestly
```

A result where Method B still trails baseline overall is valid if understood.

---

# 33. H1 Investment Gate

Answer:

> Does FikraCore-style causal hypothesis reasoning provide measurable value beyond a cheap alarm heuristic on scenario classes where causal reasoning should matter?

Report:

```text
overall Method A vs Method B
L1–L5 comparison
category comparison
cross-domain comparison
missing-knowledge comparison
noisy-scenario comparison
multi-cause comparison
unknown/abstention accuracy
Top-1 / Top-3 accuracy
terminal-state accuracy
```

Classify:

```text
H1_SUPPORTED
H1_PARTIALLY_SUPPORTED
H1_NOT_SUPPORTED
```

---

# 34. Do Not Expand Investment Yet

Do not add during Step 4.1:

```text
Kafka
Grafana LGTM
Zaki integration
multi-agent orchestration
full production topology ingestion
new UI
Neo4j
automatic brain mutation
proactive What-If
```

---

# 35. Suggested Implementation Areas

Inspect as relevant:

```text
investigation/investigator.py
investigation/evaluator.py
investigation/benchmark.py
investigation/validator.py
investigation/contracts.py
canonicalization/resolver.py
knowledge provider / graph traversal code
scripts/run_full_benchmark.py
```

Diagnose before modifying.

---

# 36. Diagnostic Pipeline

```text
Load original benchmark
        ↓
Join run result + evaluator truth
        ↓
Canonicalize comparison
        ↓
Calculate true-root rank
        ↓
Classify terminal-state correctness
        ↓
Extract scoring dimensions
        ↓
Extract knowledge/evidence gaps
        ↓
Assign failure taxonomy
        ↓
Aggregate by difficulty/category
        ↓
Audit baseline and evaluator
        ↓
Select generalizable calibration
        ↓
Tune calibration set
        ↓
Check validation set
        ↓
Freeze policy
        ↓
Run holdout
        ↓
Run same full 100
        ↓
H1 decision
```

---

# 37. Interpretation of Current Result

The current combination:

```text
Top-3 RCA Accuracy = 100%
Strict Method B Accuracy = 62%
```

suggests candidate generation may already be strong.

Therefore investigate downstream decision mechanics before redesigning architecture.

Potential areas:

```text
Top-1 ranking
confidence calibration
terminal-state thresholds
knowledge-gap criteria
negative-evidence weighting
canonical equivalence
```

Treat this as a hypothesis to test, not an assumption.

---

# 38. Definition of Done

Step 4.1 is complete when:

```text
[ ] all 100 runs have diagnostics
[ ] all Method B failures classified
[ ] Top-1/Top-2/Top-3 metrics exist
[ ] terminal-state accuracy separate
[ ] confusion matrix exists
[ ] MODEL_INSUFFICIENT audited
[ ] PARTIALLY_EXPLAINED audited
[ ] L1-L5 slices produced
[ ] scenario-category slices produced
[ ] score-margin analysis exists
[ ] confidence calibration exists
[ ] negative-evidence analysis exists
[ ] topology traversal failures classified
[ ] canonical mismatches measured
[ ] evaluator audit complete
[ ] baseline audit complete
[ ] deterministic train/validation/holdout split exists
[ ] no holdout leakage
[ ] original benchmark immutable
[ ] only generalizable calibration applied
[ ] same 100 scenarios rerun
[ ] before/after comparison generated
[ ] H1 investment decision documented
```

---

# 39. Final Output Questions

The final report must answer:

```text
1. Why did Method B score 62/100 while Top-3 RCA was 100%?
2. What percentage of failures were ranking problems?
3. What percentage were terminal-state/calibration problems?
4. How many MODEL_INSUFFICIENT decisions were correct?
5. How many PARTIALLY_EXPLAINED decisions were correct?
6. Did canonical resolution cause failures?
7. Which scenario categories favor Method B?
8. Which favor Method A?
9. Which calibration changes were applied and why?
10. Did changes generalize to holdout?
11. What is the final H1 decision?
```

End with:

```text
H1_SUPPORTED
```

or:

```text
H1_PARTIALLY_SUPPORTED
```

or:

```text
H1_NOT_SUPPORTED
```

and explain the evidence.

---

# Final Principle

> Do more hypothesis testing before more investment.

Do not optimize for a perfect benchmark score.

Optimize for a reasoning system whose strengths, weaknesses, uncertainty, and operational value are measurable and explainable.
