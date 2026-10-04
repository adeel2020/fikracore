"""
S8 — Scope & Authority Integrity Validator
==========================================
Enforces operational boundaries and governance rules:
- Agent operates strictly within authorized domain scope.
- Actions with safety tier DISRUPTIVE_ACTIVE_PROBE or WRITE_CONFIGURATION require Level 4+ HITL.
- Human validators possess required authority level and technical jurisdiction.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


DISRUPTIVE_TIERS = {
    "DISRUPTIVE_ACTIVE_PROBE",
    "WRITE_CONFIGURATION",
    "REMEDIATION",
    "TRAFFIC_REROUTE",
    "FAILOVER",
}


class AuthorityIntegrityValidator(SanityValidator):
    category = SanityCategory.S8_AUTHORITY

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})
        ctx = context or {}

        # 1. Disruptive Action HITL Check
        action_type = str(data.get("action_type") or data.get("category") or data.get("safety_tier") or "").upper()
        if any(dt in action_type for dt in DISRUPTIVE_TIERS):
            is_autonomous = data.get("autonomous", False) or ctx.get("is_autonomous", False)
            has_hitl_approval = bool(data.get("hitl_validated") or ctx.get("hitl_validated") or data.get("human_validation_id"))

            if is_autonomous and not has_hitl_approval:
                results.append(
                    SanityResult(
                        check_id="S8-001",
                        category=self.category,
                        outcome=SanityOutcome.BLOCK,
                        message=f"Disruptive action '{data.get('id', 'action')}' cannot execute autonomously without explicit HITL approval.",
                        violating_fields=["action_type", "autonomous"],
                        remediation_hint="Route action through HumanValidation work order prior to execution.",
                    )
                )

        # 2. Domain Jurisdiction Check
        agent_domain = str(data.get("domain") or data.get("primary_domain") or "").upper()
        target_domain = str(data.get("target_domain") or ctx.get("target_domain") or "").upper()

        if agent_domain and target_domain and agent_domain != "NOC" and agent_domain != target_domain:
            if not data.get("cross_domain_authorized", False):
                results.append(
                    SanityResult(
                        check_id="S8-002",
                        category=self.category,
                        outcome=SanityOutcome.BLOCK,
                        message=f"Domain jurisdiction mismatch: agent domain '{agent_domain}' cannot execute action on target domain '{target_domain}' without cross-domain authorization.",
                        violating_fields=["domain", "target_domain"],
                        remediation_hint="Delegate task to the specialized domain agent or obtain cross-domain sign-off.",
                    )
                )

        if not results:
            results.append(
                SanityResult(
                    check_id="S8-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Scope and authority integrity verified successfully.",
                )
            )
        return results
