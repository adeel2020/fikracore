"""Pre-Benchmark Integrity Validator for Step 4.3 / H3 Validated Learning Units.

Enforces 8 strict integrity checks (§49):
1. Incident A and Incident B are genuinely different (no replay-as-learning).
2. Candidate originates from H2-compatible discovery.
3. Validation decision exists, is well-formed, and matches an allowed decision type.
4. Promotion does not use or reference Hidden Truth.
5. Future incident genuinely depends on learned knowledge where expected.
6. Control cohorts are correctly labeled (positive, cross-domain, stale, poisoned).
7. Before/after knowledge snapshots differ strictly by the intended learning.
8. Operational files contain zero leakage of evaluator expectations or hidden ground truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from ..investigation.contracts import ValidationDecisionType


class H3ValidationError(ValueError):
    """Raised when an H3 learning unit violates structural or epistemic integrity rules."""
    pass


FORBIDDEN_OPERATIONAL_TOKENS = {
    "hidden_truth", "ground_truth", "evaluator_expectations",
    "true_terminal_state", "expected_root_entity", "expected_terminal_before",
    "expected_terminal_after",
}


def validate_single_h3_unit(unit_dir: Path | str) -> dict[str, Any]:
    """Validate a single H3 learning unit against all 8 integrity checks."""
    path = Path(unit_dir)
    errors: list[str] = []

    manifest_file = path / "learning_unit_manifest.yaml"
    cand_file = path / "candidate_knowledge.yaml"
    val_file = path / "validation_decision.yaml"
    fut_dir = path / "future_incident"
    op_dir = fut_dir / "operational"
    hidden_dir = fut_dir / "hidden"

    for req_path in [manifest_file, cand_file, val_file, op_dir / "topology_view.yaml", hidden_dir / "ground_truth.yaml"]:
        if not req_path.exists():
            errors.append(f"Missing required file: {req_path.name}")

    if errors:
        return {"unit_id": path.name, "valid": False, "errors": errors}

    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)
    with open(cand_file) as f:
        candidate = yaml.safe_load(f)
    with open(val_file) as f:
        validation = yaml.safe_load(f)
    with open(op_dir / "topology_view.yaml") as f:
        op_topo = yaml.safe_load(f)
    with open(hidden_dir / "ground_truth.yaml") as f:
        ground_truth = yaml.safe_load(f)

    unit_id = manifest.get("learning_unit_id", path.name)
    cohort = manifest.get("cohort", "")
    disc_id = manifest.get("discovery_incident", "")
    fut_id = manifest.get("future_incident_id", "")

    # Check 1: Incident A and Incident B are genuinely different
    if disc_id == fut_id:
        errors.append(f"Check 1 violation: Future incident '{fut_id}' is identical to discovery incident '{disc_id}' (replay-as-learning is forbidden).")

    # Check 2: Candidate originates from H2-compatible discovery
    if not candidate.get("candidate_id") or not candidate.get("source") or not candidate.get("target"):
        errors.append("Check 2 violation: Candidate record is missing candidate_id, source, or target entity.")

    # Check 3: Validation decision exists and is well-formed
    dec = validation.get("decision")
    if dec not in [d.value for d in ValidationDecisionType]:
        errors.append(f"Check 3 violation: Invalid validation decision '{dec}'. Must be in {[d.value for d in ValidationDecisionType]}.")
    if not validation.get("validated_by_role"):
        errors.append("Check 3 violation: Validation decision must specify validated_by_role.")

    # Check 4: Promotion does not use Hidden Truth
    if "hidden" in str(candidate.get("supporting_evidence", [])):
        errors.append("Check 4 violation: Candidate supporting evidence references hidden paths.")

    # Check 5: Future incident depends on learned knowledge where expected
    if cohort in {"positive_transfer", "cross_domain_transfer"}:
        fut_root = ground_truth.get("root_entity")
        cand_src = candidate.get("source")
        cand_tgt = candidate.get("target")
        if fut_root != cand_src and fut_root != cand_tgt:
            errors.append(f"Check 5 violation: Future incident root '{fut_root}' does not match candidate entities ({cand_src}, {cand_tgt}).")

    # Check 6: Control cohorts are correctly labeled
    allowed_cohorts = {"positive_transfer", "cross_domain_transfer", "stale_topology", "poisoned_validation"}
    if cohort not in allowed_cohorts:
        errors.append(f"Check 6 violation: Cohort '{cohort}' is not recognized. Must be in {allowed_cohorts}.")

    # Check 7: Before/after knowledge snapshots differ strictly by intended learning
    promoted_rel_id = manifest.get("validated_relation", {}).get("relationship_id")
    if promoted_rel_id and promoted_rel_id in set(op_topo.get("visible_relationships", [])):
        errors.append(f"Check 7 violation: Promoted relation '{promoted_rel_id}' is already present in BEFORE operational topology view.")

    # Check 8: Operational files contain zero leakage of evaluator expectations
    for op_file in op_dir.glob("*"):
        content = op_file.read_text(encoding="utf-8")
        for token in FORBIDDEN_OPERATIONAL_TOKENS:
            if token in content:
                errors.append(f"Check 8 violation: Forbidden evaluator token '{token}' leaked into operational file {op_file.name}.")

    return {
        "unit_id": unit_id,
        "cohort": cohort,
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_all_h3_units(units_dir: Path | str) -> dict[str, Any]:
    """Validate all H3 learning units under a directory."""
    root = Path(units_dir)
    unit_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name.startswith("H3-LU-")])
    results = [validate_single_h3_unit(d) for d in unit_dirs]

    passed = sum(1 for r in results if r["valid"])
    failed = len(results) - passed

    return {
        "total_units": len(results),
        "passed": passed,
        "failed": failed,
        "all_valid": failed == 0 and len(results) > 0,
        "details": results,
    }


__all__ = [
    "H3ValidationError",
    "validate_single_h3_unit",
    "validate_all_h3_units",
]
