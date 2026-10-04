"""
FikraCore Sanity Validation Model (S1–S11)
=========================================
Central entrypoint for cross-cutting invariant validation across all contracts.
"""

from typing import Any, Dict, List, Optional

from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator
from .structural import StructuralValidator
from .references import ReferenceIntegrityValidator
from .temporal import TemporalConsistencyValidator
from .lifecycle import LifecycleIntegrityValidator
from .semantics import SemanticSeparationValidator
from .topology import TopologyIntegrityValidator
from .causality import CausalityIntegrityValidator
from .authority import AuthorityIntegrityValidator
from .knowledge import KnowledgeIntegrityValidator
from .indexes import IndexIntegrityValidator
from .simulation import OracleIsolationValidator, scan_for_oracle_leaks

ALL_VALIDATORS = [
    StructuralValidator(),
    ReferenceIntegrityValidator(),
    TemporalConsistencyValidator(),
    LifecycleIntegrityValidator(),
    SemanticSeparationValidator(),
    TopologyIntegrityValidator(),
    CausalityIntegrityValidator(),
    AuthorityIntegrityValidator(),
    KnowledgeIntegrityValidator(),
    IndexIntegrityValidator(),
    OracleIsolationValidator(),
]


def run_all_sanity_checks(
    contract: Any,
    context: Optional[Dict[str, Any]] = None,
    fail_on_block: bool = False,
) -> List[SanityResult]:
    """
    Run all S1–S11 invariant sanity checks against a contract instance.

    Args:
        contract: The contract instance or dictionary to validate.
        context: Optional operational context for reference checks.
        fail_on_block: If True, raises ValueError on any BLOCK result.

    Returns:
        List of SanityResult objects.
    """
    results: List[SanityResult] = []
    for validator in ALL_VALIDATORS:
        res = validator.validate(contract, context=context)
        results.extend(res)

    if fail_on_block:
        blocks = [r for r in results if r.outcome == SanityOutcome.BLOCK]
        if blocks:
            reasons = "; ".join(f"[{b.check_id}] {b.message}" for b in blocks)
            raise ValueError(f"Sanity Check BLOCK: {reasons}")

    return results


__all__ = [
    "SanityCategory",
    "SanityOutcome",
    "SanityResult",
    "SanityValidator",
    "StructuralValidator",
    "ReferenceIntegrityValidator",
    "TemporalConsistencyValidator",
    "LifecycleIntegrityValidator",
    "SemanticSeparationValidator",
    "TopologyIntegrityValidator",
    "CausalityIntegrityValidator",
    "AuthorityIntegrityValidator",
    "KnowledgeIntegrityValidator",
    "IndexIntegrityValidator",
    "IsolationValidator",
    "scan_for_oracle_leaks",
    "run_all_sanity_checks",
    "ALL_VALIDATORS",
]
