"""
Causal Propagation Path Contract
================================
Defines the directed physical, logical, or protocol dependency trajectory along which
a fault, degradation, or operational state propagated through the infrastructure.
Fully incident- and event-agnostic. Strictly enforces pure network infrastructure hops.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class CausalHop(BaseContract):
    """Individual directed dependency transition between two network infrastructure entities."""
    hop_index: int = Field(description="Zero-based sequence order along propagation path")
    from_entity: str = Field(description="Source network element or interface")
    to_entity: str = Field(description="Target downstream network element or interface")
    source_domain: str = Field(description="Domain of source entity")
    target_domain: str = Field(description="Domain of downstream entity")
    relationship_type: str = Field(
        default="DEPENDS_ON",
        description="Topological dependency type (e.g. CARRIES_TRAFFIC, HOSTED_ON, ROUTES_THROUGH, SESSIONS_BOUND_TO)"
    )
    delay_ms: Optional[float] = Field(default=None, description="Observed propagation latency between entities in ms")


class CausalPropagationContract(BaseContract):
    """
    Authoritative ordered causal trajectory from origin to terminal failure frontier.
    Guarantees pure network infrastructure hops with zero observational symptom pollution.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="CausalPropagation", description="Contract kind identifier")
    
    path_id: str = Field(description="Unique propagation path identifier")
    event_ref: Optional[str] = Field(default=None, description="Associated event or diagnostic run reference")
    
    # Strictly Ordered Network Infrastructure Entity Path (Pure Hops)
    propagation_path: List[str] = Field(
        default_factory=list,
        description="Ordered sequence of physical/logical network element identifiers from origin to frontier"
    )
    
    # Domain Trajectory Boundaries
    entry_domain: str = Field(description="Initial domain where fault or change originated")
    terminal_domain: str = Field(description="Frontier domain where downstream symptoms manifest")
    domains_traversed: List[str] = Field(
        default_factory=list,
        description="Chronological sequence of technical domains traversed by propagation"
    )
    
    # Detailed Hop Topologies
    hops: List[CausalHop] = Field(
        default_factory=list,
        description="Detailed transition records between adjacent entities along the path"
    )
    total_hops: int = Field(default=0, description="Total count of hops in propagation chain")
    is_cross_domain: bool = Field(default=False, description="True if path crosses multiple technical domains")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extension metadata")
