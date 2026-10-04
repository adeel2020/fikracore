"""
Diagnostic Gap Contract
=======================
Defines observability blindspots, unmonitored topology segments, missing telemetry metrics,
or ambiguous causal branches identified during operational reasoning.
Fully incident- and event-agnostic.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class DiagnosticGapType(str, Enum):
    """Categorization of observability or knowledge gaps."""
    UNMONITORED_ENTITY = "UNMONITORED_ENTITY"       # Entity lacks active telemetry agent or probe
    MISSING_TELEMETRY = "MISSING_TELEMETRY"         # Sensor exists but specific metric is stale or absent
    AMBIGUOUS_BRANCH = "AMBIGUOUS_BRANCH"           # Causal fork where two hypotheses have equal confidence
    TOPOLOGY_BLINDSPOT = "TOPOLOGY_BLINDSPOT"       # Edge or link relationship unmapped in knowledge graph
    STALE_BASELINE = "STALE_BASELINE"               # Metric lacks historical baseline for anomaly discrimination


class DiagnosticGapItem(BaseContract):
    """Individual diagnostic gap record."""
    gap_id: str = Field(description="Unique identifier for the diagnostic gap")
    gap_type: DiagnosticGapType = Field(description="Classification of gap")
    affected_domain: str = Field(description="Domain where gap was discovered")
    affected_entities: List[str] = Field(
        default_factory=list,
        description="Network elements or links bounded by this observability gap"
    )
    description: str = Field(description="Technical description of what information is missing")
    recommended_probes: List[str] = Field(
        default_factory=list,
        description="Specific diagnostic probes or queries capable of resolving the gap"
    )
    severity: str = Field(default="MEDIUM", description="Impact on diagnostic confidence: HIGH, MEDIUM, LOW")


class DiagnosticGapContract(BaseContract):
    """
    Collection of active observability gaps discovered during operational reasoning.
    Agnostic to incident type, event trigger, or network vendor.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="DiagnosticGapAssessment", description="Contract kind identifier")
    
    assessment_id: str = Field(description="Unique assessment identifier")
    scope_ref: Optional[str] = Field(default=None, description="Scope or context reference where gaps were identified")
    
    gaps: List[DiagnosticGapItem] = Field(
        default_factory=list,
        description="List of active diagnostic gaps discovered"
    )
    total_gaps: int = Field(default=0, description="Total count of active gaps")
    has_blocking_gaps: bool = Field(
        default=False,
        description="True if any high-severity gap prevents confident diagnosis"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extension metadata")
