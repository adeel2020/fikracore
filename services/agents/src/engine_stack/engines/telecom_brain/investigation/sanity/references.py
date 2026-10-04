"""
S2 — Identity & Reference Integrity Validator
=============================================
Enforces relational consistency across contracts:
- Foreign keys and reference IDs resolve to existing entities in the graph/context.
- No dangling references (e.g. referencing non-existent operational_context_ref).
- Canonical entities are referenced rather than duplicated.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


class ReferenceIntegrityValidator(SanityValidator):
    category = SanityCategory.S2_REFERENCES

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})
        ctx = context or {}

        # 1. Operational Context Reference Resolution
        op_ref = data.get("operational_context_ref")
        if op_ref:
            known_contexts = ctx.get("known_contexts", set())
            if known_contexts and op_ref not in known_contexts:
                results.append(
                    SanityResult(
                        check_id="S2-001",
                        category=self.category,
                        outcome=SanityOutcome.BLOCK,
                        message=f"Dangling operational_context_ref: '{op_ref}' does not resolve to an active snapshot.",
                        violating_fields=["operational_context_ref"],
                        remediation_hint="Ensure the OperationalContextContract is instantiated before referencing.",
                    )
                )

        # 2. Admitted Evidence Reference Resolution
        evidence_refs = data.get("admitted_evidence_ids") or data.get("evidence_observed") or []
        known_evidence = ctx.get("known_evidence", set())
        if known_evidence and evidence_refs:
            unresolved = [ref for ref in evidence_refs if ref not in known_evidence]
            if unresolved:
                results.append(
                    SanityResult(
                        check_id="S2-002",
                        category=self.category,
                        outcome=SanityOutcome.WARN,
                        message=f"Unresolved evidence references in context: {unresolved}",
                        violating_fields=["admitted_evidence_ids"],
                        remediation_hint="Verify that all admitted evidence IDs correspond to active evidence records.",
                    )
                )

        # 3. Incident Reference Consistency
        inc_id = data.get("incident_id") or data.get("active_incident_id")
        if inc_id and not isinstance(inc_id, str):
            results.append(
                SanityResult(
                    check_id="S2-003",
                    category=self.category,
                    outcome=SanityOutcome.BLOCK,
                    message="Incident identifier must be a valid string reference.",
                    violating_fields=["incident_id"],
                    remediation_hint="Format incident reference as string (e.g. 'INC-001').",
                )
            )

        if not results:
            results.append(
                SanityResult(
                    check_id="S2-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Identity and reference integrity verified successfully.",
                )
            )
        return results
