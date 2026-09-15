# Step 4.1 Calibration Changes Summary

This document records the exact, generalizable changes applied to the hypothesis reasoning engine and benchmark harness during Step 4.1.

---

## 1. Summary of Changes

| Component | File Modified | Nature of Change | Rationale |
|---|---|---|---|
| **Graph Edge Direction** | `services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py` | Classified relationships into `FORWARD_TYPES` (`member-of`, `monitored-by`, `supports-service`, `serves`) vs reverse dependency types. | Container/supplier relations like `INFRA:POWER:A MEMBER_OF INFRA:DC:A` were previously inverted, preventing power feed from reaching data center nodes. |
| **Model-Gap Decoupling** | `services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py` | Decoupled `residual` observations from `model_gap`. `model_gap = bool(candidates or gaps or not best)`. | Previously, any single residual noise alarm triggered `discovery = True`, prematurely aborting high-confidence valid investigations as `MODEL_INSUFFICIENT`. |
| **Sparse Alarm Coverage** | `services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py` | Added high-confidence sparse alarm coverage clause: `(coverage >= 0.75 or (coverage >= 0.35 and not candidates and not gaps and best.hypothesis_confidence >= 0.65))`. | High-level incidents where only partial downstream monitors triggered alarms were falsely marked `PARTIALLY_EXPLAINED` despite zero model gaps. |
| **Epistemic Operational Topology** | `services/agents/src/engine_stack/engines/telecom_brain/investigation/benchmark.py` | Switched fixture loading from hidden `causal_graph.yaml` to operational network catalog (`reference_synthetic_network.yaml`), preserving true semantic relationship types. | Restores epistemic boundary by eliminating operational reads of examiner-only hidden truth. |
| **Stratified Split Support** | `services/agents/src/engine_stack/engines/telecom_brain/investigation/benchmark.py` | Added `--split` and `--split-file` support to `benchmark_all()`. | Enables reproducible evaluation on 60 Calibration / 20 Validation / 20 Holdout splits. |
| **CLI Diagnostic Commands** | `services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py` | Added `diagnose-benchmark` and `diagnose-run` CLI commands. | Supports interactive scenario debugging and full taxonomy reporting via CLI. |

---

## 2. Verification of Generalizability (§26 Compliance)

- **Zero Scenario Literals**: Automated AST check (`test_no_scenario_specific_calibration_constants`) verified that no scenario IDs (`SCN-*`, `RUN-SCN-*`) or entity IDs exist in `investigator.py` or `benchmark.py`.
- **Zero Truth Leakage**: Evaluator expectations and ground truth remain strictly examiner-only. Operational reasoning remains completely truth-blind.
- **Stratified Workflow**: Policy was tuned strictly on the 60 Calibration runs, hyperparameters verified on the 20 Validation runs, frozen, and evaluated strictly once on the 20 Holdout runs.

---

## 3. Exact Thresholds & Hyperparameters

```python
# investigator.py
FORWARD_TYPES = {"member-of", "monitored-by", "supports-service", "serves"}

coverage = best.explanation_coverage if best else 0
model_gap = bool(candidates or gaps or not best)
discovery = model_gap or bool(residual and coverage < 0.70)
local_sources = best.score_dimensions["independent_telemetry"] if best else 0

if not abnormal or len({item.source for item in abnormal}) < 2:
    terminal = Terminal.INSUFFICIENT_EVIDENCE
elif best and best.contradicting_evidence and best.canonical_root_entity in impacted:
    terminal = Terminal.CONFLICTING_EVIDENCE
elif model_gap:
    terminal = Terminal.MODEL_INSUFFICIENT
elif best and (coverage >= 0.75 or (coverage >= 0.35 and not candidates and not gaps and best.hypothesis_confidence >= 0.65)) and best.causal_confidence >= 0.50 and local_sources >= 0.5:
    terminal = Terminal.EXPLAINED
elif best and coverage >= 0.35 and best.hypothesis_confidence >= 0.45:
    terminal = Terminal.PARTIALLY_EXPLAINED
else:
    terminal = Terminal.UNRESOLVED
```
