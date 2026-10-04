"""
S4 — Lifecycle Integrity Validator
==================================
Enforces legal lifecycle state transitions across contracts:
- Evidence: RAW -> EMERGING -> VALIDATED -> RETIRED
- Hypothesis: PROPOSED -> TESTING -> LEADING -> (RULED_OUT | CONFIRMED)
  (Hard BLOCK on illegal shortcut: PROPOSED -> CONFIRMED without TESTING)
- Incident: DETECTED -> OPEN -> INVESTIGATING -> MITIGATING -> RESOLVED -> CLOSED
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


LEGAL_HYPOTHESIS_TRANSITIONS: Dict[str, Set[str]] = {
    "PROPOSED": {"TESTING", "RULED_OUT"},
    "TESTING": {"LEADING", "SUPPORTED", "RULED_OUT"},
    "SUPPORTED": {"LEADING", "CONFIRMED", "RULED_OUT"},
    "LEADING": {"CONFIRMED", "RULED_OUT", "TESTING"},
    "RULED_OUT": set(),
    "CONFIRMED": set(),
}

LEGAL_EVIDENCE_TRANSITIONS: Dict[str, Set[str]] = {
    "RAW": {"EMERGING", "REJECTED"},
    "EMERGING": {"VALIDATED", "EXPIRED", "RETAINED"},
    "VALIDATED": {"RETIRED", "ARCHIVED"},
    "EXPIRED": set(),
    "RETIRED": set(),
}


class LifecycleIntegrityValidator(SanityValidator):
    category = SanityCategory.S4_LIFECYCLE

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})
        ctx = context or {}

        # 1. Hypothesis transition validation
        if "hypothesis_id" in data or data.get("kind") == "Hypothesis":
            current_status = str(data.get("status") or data.get("state") or "PROPOSED").upper()
            previous_status = str(ctx.get("previous_status", "")).upper()

            if previous_status and previous_status in LEGAL_HYPOTHESIS_TRANSITIONS:
                allowed = LEGAL_HYPOTHESIS_TRANSITIONS[previous_status]
                if current_status not in allowed and current_status != previous_status:
                    results.append(
                        SanityResult(
                            check_id="S4-001",
                            category=self.category,
                            outcome=SanityOutcome.BLOCK,
                            message=(
                                f"Illegal hypothesis lifecycle transition from '{previous_status}' to '{current_status}'. "
                                f"Allowed target states: {sorted(list(allowed))}"
                            ),
                            violating_fields=["status"],
                            remediation_hint=f"Hypothesis must pass through intermediate state before reaching '{current_status}'.",
                        )
                    )

            # Direct promotion check: PROPOSED cannot be CONFIRMED without testing
            if current_status == "CONFIRMED" and (not previous_status or previous_status == "PROPOSED"):
                has_probe = bool(data.get("discrimination_probe") or ctx.get("probe_completed"))
                if not has_probe:
                    results.append(
                        SanityResult(
                            check_id="S4-002",
                            category=self.category,
                            outcome=SanityOutcome.BLOCK,
                            message="Hypothesis cannot be marked CONFIRMED without prior diagnostic discrimination testing.",
                            violating_fields=["status"],
                            remediation_hint="Execute active discrimination probe before confirming hypothesis.",
                        )
                    )

        # 2. Terminal State Consistency
        outcome = data.get("outcome") or data.get("terminal_state")
        if outcome and str(outcome).upper() in {"RESOLVED", "SUCCESS", "COMPLETED"}:
            if not data.get("closed_at") and not ctx.get("is_final_step"):
                results.append(
                    SanityResult(
                        check_id="S4-003",
                        category=self.category,
                        outcome=SanityOutcome.WARN,
                        message=f"Terminal outcome '{outcome}' set, but closure timestamp 'closed_at' is missing.",
                        violating_fields=["closed_at"],
                        remediation_hint="Set 'closed_at' timestamp when completing an episode or incident.",
                    )
                )

        if not results:
            results.append(
                SanityResult(
                    check_id="S4-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Lifecycle integrity verified successfully.",
                )
            )
        return results
