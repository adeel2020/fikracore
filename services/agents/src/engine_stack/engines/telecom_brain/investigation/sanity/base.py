"""
Sanity Validation Model: Base Definitions & Types
=================================================
Defines the cross-cutting invariant validation framework for FikraCore and Zaki.
All validators enforce invariants and return standardized outcomes: PASS, WARN, BLOCK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SanityOutcome(str, Enum):
    """Determination rendered by an invariant check."""
    PASS = "PASS"    # Invariant fully satisfied
    WARN = "WARN"    # Condition allows continuation with explicit uncertainty
    BLOCK = "BLOCK"  # Hard safety, causal, structural, or authority violation


class SanityCategory(str, Enum):
    """Categorization matching the FikraCore Sanity Specification (§6–§16)."""
    S1_STRUCTURAL = "S1_STRUCTURAL"
    S2_REFERENCES = "S2_REFERENCES"
    S3_TEMPORAL = "S3_TEMPORAL"
    S4_LIFECYCLE = "S4_LIFECYCLE"
    S5_SEMANTICS = "S5_SEMANTICS"
    S6_TOPOLOGY = "S6_TOPOLOGY"
    S7_CAUSALITY = "S7_CAUSALITY"
    S8_AUTHORITY = "S8_AUTHORITY"
    S9_KNOWLEDGE = "S9_KNOWLEDGE"
    S10_INDEXES = "S10_INDEXES"
    S11_SIMULATION = "S11_SIMULATION"


class SanityResult(BaseModel):
    """
    Standardized result emitted by any sanity check.
    """
    check_id: str = Field(description="Unique check identifier (e.g. S1-001, S11-001)")
    category: SanityCategory = Field(description="Category of the invariant check")
    outcome: SanityOutcome = Field(description="PASS, WARN, or BLOCK")
    message: str = Field(description="Human-readable explanation of the check outcome")
    violating_fields: List[str] = Field(default_factory=list, description="Fields causing the warning or block")
    remediation_hint: Optional[str] = Field(default=None, description="Actionable suggestion to resolve issue")


class SanityValidator(ABC):
    """Abstract base class for all invariant sanity validators."""

    category: SanityCategory

    @abstractmethod
    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        """Validate invariant rules against a contract instance or dictionary."""
        pass
