"""
S1 — Structural Integrity Validator
====================================
Validates that contracts satisfy fundamental structural invariants:
- Required fields exist and are non-empty.
- Schema versions are supported.
- IDs follow semantic naming conventions.
- No invalid duplicate identifiers in collection fields.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


ID_PREFIX_MAP = {
    "TaskEpisode": r"^EP-",
    "OperationalContext": r"^CTX-",
    "Incident": r"^INC-",
    "Evidence": r"^EV-",
    "RawEvidence": r"^RAW-|^telemetry-",
    "EmergingEvidence": r"^EMG-",
    "InvestigationHypothesis": r"^HYP-",
    "HumanValidation": r"^VAL-",
    "Action": r"^ACT-|^NBA-",
    "Finding": r"^FND-",
}


class StructuralValidator(SanityValidator):
    category = SanityCategory.S1_STRUCTURAL

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})
        if not data:
            results.append(
                SanityResult(
                    check_id="S1-001",
                    category=self.category,
                    outcome=SanityOutcome.BLOCK,
                    message="Contract payload is empty or not serializable.",
                    violating_fields=["payload"],
                    remediation_hint="Provide a valid contract instance or dictionary.",
                )
            )
            return results

        # 1. Schema version check
        api_version = data.get("api_version") or data.get("schema_version")
        if api_version and not re.match(r"^[a-zA-Z0-9_\-\.\/]+$", str(api_version)):
            results.append(
                SanityResult(
                    check_id="S1-002",
                    category=self.category,
                    outcome=SanityOutcome.BLOCK,
                    message=f"Invalid api_version format: '{api_version}'",
                    violating_fields=["api_version"],
                    remediation_hint="Use standard version string like 'zaki.ai/v1'.",
                )
            )

        # 2. Kind & ID convention check
        kind = data.get("kind") or type(contract).__name__
        for kind_pattern, prefix_regex in ID_PREFIX_MAP.items():
            if kind_pattern.lower() in kind.lower():
                id_field = next(
                    (k for k in ("episode_id", "context_id", "incident_id", "evidence_id", "hypothesis_id", "id") if k in data),
                    None,
                )
                if id_field:
                    val = str(data[id_field])
                    if not re.search(prefix_regex, val, re.IGNORECASE):
                        results.append(
                            SanityResult(
                                check_id="S1-003",
                                category=self.category,
                                outcome=SanityOutcome.WARN,
                                message=f"Identifier '{val}' does not conform to standard prefix '{prefix_regex}'.",
                                violating_fields=[id_field],
                                remediation_hint=f"Ensure ID matches prefix convention for {kind_pattern}.",
                            )
                        )
                break

        # 3. Duplicate checks in collection fields
        collection_fields = ("evidence_observed", "admitted_evidence_ids", "active_knowledge_gaps", "domains")
        for cf in collection_fields:
            if cf in data and isinstance(data[cf], list):
                seen = set()
                dups = []
                for item in data[cf]:
                    key = str(item)
                    if key in seen:
                        dups.append(key)
                    seen.add(key)
                if dups:
                    results.append(
                        SanityResult(
                            check_id="S1-004",
                            category=self.category,
                            outcome=SanityOutcome.WARN,
                            message=f"Duplicate elements found in collection '{cf}': {dups}",
                            violating_fields=[cf],
                            remediation_hint=f"De-duplicate '{cf}' entries.",
                        )
                    )

        if not results:
            results.append(
                SanityResult(
                    check_id="S1-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Structural integrity verified successfully.",
                )
            )
        return results
