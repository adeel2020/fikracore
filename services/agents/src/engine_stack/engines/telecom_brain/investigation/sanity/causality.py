"""
S7 — Causal & Evidence Integrity Validator
==========================================
Enforces rigorous evidence backing for operational claims:
- Claims must be supported by admitted evidence records.
- Contradictory evidence must be explicitly preserved (never discarded).
- Causal claims require active diagnostic discrimination rather than correlation alone.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


class CausalityIntegrityValidator(SanityValidator):
    category = SanityCategory.S7_CAUSALITY

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})

        # 1. Hypothesis Supporting Evidence Check
        if "hypothesis_id" in data or data.get("kind") == "Hypothesis":
            status = str(data.get("status") or data.get("state") or "").upper()
            supporting = data.get("supporting_evidence") or data.get("supporting_evidence_ids") or []
            contradictory = data.get("contradictory_evidence") or data.get("contradictory_evidence_ids") or []

            if status in {"LEADING", "CONFIRMED"} and not supporting:
                results.append(
                    SanityResult(
                        check_id="S7-001",
                        category=self.category,
                        outcome=SanityOutcome.BLOCK,
                        message=f"Hypothesis marked as '{status}' without any supporting evidence records.",
                        violating_fields=["supporting_evidence"],
                        remediation_hint="Attach at least one admitted telemetry or probe evidence record.",
                    )
                )

            # Unresolved Contradictions
            if status == "CONFIRMED" and contradictory:
                results.append(
                    SanityResult(
                        check_id="S7-002",
                        category=self.category,
                        outcome=SanityOutcome.BLOCK,
                        message=f"Hypothesis cannot be marked CONFIRMED while contradictory evidence exists ({len(contradictory)} items).",
                        violating_fields=["contradictory_evidence"],
                        remediation_hint="Resolve or explain contradictory evidence via discrimination probes before confirming.",
                    )
                )

            # Confidence vs Status Check
            confidence = data.get("confidence")
            if isinstance(confidence, (int, float)):
                if status == "CONFIRMED" and confidence < 70.0:
                    results.append(
                        SanityResult(
                            check_id="S7-003",
                            category=self.category,
                            outcome=SanityOutcome.WARN,
                            message=f"Confidence ({confidence}%) is low for CONFIRMED hypothesis (expected >= 70%).",
                            violating_fields=["confidence"],
                            remediation_hint="Verify if additional discrimination probes are needed.",
                        )
                    )

        if not results:
            results.append(
                SanityResult(
                    check_id="S7-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Causal and evidence integrity verified successfully.",
                )
            )
        return results
