"""
S11 — Simulation / Oracle Isolation Validator
=============================================
Enforces strict epistemic integrity between the Simulator Oracle and operational reasoning:
- Scans all visible contracts and outbound snapshots recursively for hidden ground truth.
- Hard BLOCK on any simulator oracle leak (e.g. root_entity, hidden_truth, expected_root).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


FORBIDDEN_ORACLE_FIELDS = {
    "hidden",
    "hidden_truth",
    "ground_truth",
    "root_condition",
    "root_entity",
    "root_domain",
    "expected_root",
    "evaluator_expectations",
    "noise_manifest",
    "simulator_world",
    "actual_blast_radius",
}


def scan_for_oracle_leaks(value: Any, path: str = "") -> List[str]:
    """Recursively search for forbidden oracle keys in any data structure."""
    leaks: List[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            norm_k = str(k).lower().replace("-", "_").strip()
            current_path = f"{path}.{k}" if path else str(k)
            if norm_k in FORBIDDEN_ORACLE_FIELDS:
                leaks.append(current_path)
            leaks.extend(scan_for_oracle_leaks(v, current_path))
    elif isinstance(value, (list, tuple, set)):
        for i, item in enumerate(value):
            leaks.extend(scan_for_oracle_leaks(item, f"{path}[{i}]"))
    return leaks


class OracleIsolationValidator(SanityValidator):
    category = SanityCategory.S11_SIMULATION

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})

        leaks = scan_for_oracle_leaks(data)
        if leaks:
            results.append(
                SanityResult(
                    check_id="S11-001",
                    category=self.category,
                    outcome=SanityOutcome.BLOCK,
                    message=f"Hard Epistemic Violation: Hidden simulator ground truth leaked into operational visibility: {leaks}",
                    violating_fields=leaks,
                    remediation_hint="Strip all oracle / evaluator fields before exporting state to FikraCore or Zaki.",
                )
            )

        if not results:
            results.append(
                SanityResult(
                    check_id="S11-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Zero Oracle Leakage verified successfully.",
                )
            )
        return results
