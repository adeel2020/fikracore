"""
S10 — Index Integrity Validator
===============================
Enforces pointer-only index architecture:
- Indexes (Incidents, Episodes, Patterns, Topology) store lightweight lookup pointers.
- Indexes must NOT duplicate full semantic contract bodies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


FORBIDDEN_INDEX_DUPLICATION_FIELDS = {
    "raw_payload",
    "visible_topology_subgraph",
    "executive_summary",
    "activity_stream",
    "reasoning_narrative",
}


class IndexIntegrityValidator(SanityValidator):
    category = SanityCategory.S10_INDEXES

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})

        # Check if the contract is being used as an index record
        is_index = "index" in str(data.get("kind", "")).lower() or context and context.get("is_index_entry")
        if is_index:
            for field in FORBIDDEN_INDEX_DUPLICATION_FIELDS:
                if field in data and data[field]:
                    results.append(
                        SanityResult(
                            check_id="S10-001",
                            category=self.category,
                            outcome=SanityOutcome.WARN,
                            message=f"Index record duplicates heavy semantic body field '{field}'. Indexes should contain pointer keys only.",
                            violating_fields=[field],
                            remediation_hint=f"Strip '{field}' from index entry and reference the canonical entity by ID.",
                        )
                    )

        if not results:
            results.append(
                SanityResult(
                    check_id="S10-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Index integrity verified successfully.",
                )
            )
        return results
