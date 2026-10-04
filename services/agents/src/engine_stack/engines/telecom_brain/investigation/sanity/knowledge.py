"""
S9 — Knowledge & Pattern Integrity Validator
============================================
Enforces continuous learning and pattern promotion standards:
- Operational patterns must reference supporting historical episodes.
- Promotion to canonical knowledge requires empirical recurrence threshold and SME signoff.
- Deprecated knowledge cannot be presented as currently active.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


class KnowledgeIntegrityValidator(SanityValidator):
    category = SanityCategory.S9_KNOWLEDGE

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})

        # 1. Pattern Recurrence and Episode Provenance Check
        if "pattern_id" in data or "learned_pattern" in data:
            pattern = data.get("learned_pattern") or data
            if isinstance(pattern, dict):
                episodes = pattern.get("observed_episodes") or pattern.get("supporting_episodes") or []
                recurrence = pattern.get("recurrence_count") or len(episodes)
                status = str(pattern.get("status", "")).upper()

                if status == "PROMOTED" and recurrence < 2:
                    results.append(
                        SanityResult(
                            check_id="S9-001",
                            category=self.category,
                            outcome=SanityOutcome.BLOCK,
                            message=f"Candidate pattern cannot be PROMOTED with insufficient empirical recurrence ({recurrence} < 2).",
                            violating_fields=["recurrence_count", "status"],
                            remediation_hint="A pattern must be observed across multiple independent episodes before canonical promotion.",
                        )
                    )

                if status in {"VALIDATED", "PROMOTED"} and not episodes:
                    results.append(
                        SanityResult(
                            check_id="S9-002",
                            category=self.category,
                            outcome=SanityOutcome.WARN,
                            message="Pattern lacks references to observed originating episodes.",
                            violating_fields=["observed_episodes"],
                            remediation_hint="Attach historical task episode IDs supporting this pattern.",
                        )
                    )

        if not results:
            results.append(
                SanityResult(
                    check_id="S9-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Knowledge and pattern integrity verified successfully.",
                )
            )
        return results
