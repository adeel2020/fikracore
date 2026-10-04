"""
S5 — Semantic Separation Validator
==================================
Enforces fundamental architectural distinctions:
Telemetry ≠ Evidence ≠ Emerging Condition ≠ Hypothesis ≠ Validated Finding ≠ Root Cause.

Hard Blocks:
- Raw telemetry or sensor metrics labeled directly as 'root_cause' or 'confirmed_rca'.
- Escalation of correlated alarms to causal findings without empirical validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


class SemanticSeparationValidator(SanityValidator):
    category = SanityCategory.S5_SEMANTICS

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})

        # 1. Raw Telemetry cannot declare Root Cause
        kind = str(data.get("kind", "")).lower()
        is_raw = "raw" in kind or "telemetry" in kind or "sensor" in kind
        if is_raw:
            for field in ("root_cause", "rca", "confirmed_finding", "causal_entity"):
                if field in data and data[field]:
                    results.append(
                        SanityResult(
                            check_id="S5-001",
                            category=self.category,
                            outcome=SanityOutcome.BLOCK,
                            message=f"Raw telemetry contract cannot declare '{field}'. Telemetry is observational, not causal.",
                            violating_fields=[field],
                            remediation_hint="Convert raw observation to EmergingEvidence, formulate Hypothesis, and test with Probes.",
                        )
                    )

        # 2. Hypothesis Rank #1 is not automatically confirmed Root Cause
        if "hypothesis" in kind or "ranked_hypotheses" in data:
            rank = data.get("rank") or (1 if data.get("is_leading") else None)
            status = str(data.get("status", "")).upper()
            if rank == 1 and status == "CONFIRMED":
                has_validated_probes = bool(data.get("discrimination_probe") or data.get("supporting_probes"))
                if not has_validated_probes:
                    results.append(
                        SanityResult(
                            check_id="S5-002",
                            category=self.category,
                            outcome=SanityOutcome.BLOCK,
                            message="Leading hypothesis (Rank #1) cannot be marked CONFIRMED without supporting discrimination probes.",
                            violating_fields=["status"],
                            remediation_hint="A ranked hypothesis remains a candidate until validated by active diagnostic testing.",
                        )
                    )

        # 3. Emerging Condition vs Incident separation
        if "emerging" in kind and data.get("is_incident"):
            results.append(
                SanityResult(
                    check_id="S5-003",
                    category=self.category,
                    outcome=SanityOutcome.WARN,
                    message="Emerging condition should not be prematurely flagged as a full incident.",
                    violating_fields=["is_incident"],
                    remediation_hint="Allow EmergingEvidenceFilter to reach significance threshold before incident escalation.",
                )
            )

        if not results:
            results.append(
                SanityResult(
                    check_id="S5-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Semantic separation verified successfully.",
                )
            )
        return results
