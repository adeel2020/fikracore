"""
Network Resilience & Redundancy Design Contract
================================================
Defines structural resilience properties of network elements, routes, and services
including redundancy topologies (1+1, N+1, N+M, AZs) and autonomous self-healing mechanisms
(e.g., MPLS Fast Reroute / TI-LFA, K8s Pod self-healing, Radio ANR).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class RedundancyModel(str, Enum):
    """Structural redundancy and high-availability architecture model."""
    ONE_PLUS_ONE = "1+1"                   # Dedicated hot standby with hitless/sub-50ms switchover
    ONE_TO_ONE = "1:1"                     # Warm/cold standby pairing
    N_PLUS_ONE = "N+1"                     # Shared standby instance for N active units
    N_PLUS_M = "N+M"                       # Multi-instance dynamic pool redundancy
    ACTIVE_ACTIVE = "ACTIVE_ACTIVE"         # Traffic load-shared concurrently across active units
    GEO_REDUNDANT = "GEO_REDUNDANT"         # Cross-region / multi-availability-zone deployment


class SelfHealingMechanism(str, Enum):
    """Inherent protocol or platform-level autonomous recovery mechanisms."""
    MPLS_FRR_TI_LFA = "MPLS_FRR_TI_LFA"     # Sub-50ms loop-free alternate fast reroute
    K8S_POD_AUTO_RESTART = "K8S_POD_AUTO_RESTART"  # Container/pod auto-restart and replica reconciliation
    BGP_PUPPET_SWITCH = "BGP_PUPPET_SWITCH" # Automated route withdrawal and reconvergence
    RADIO_ANR_TILT = "RADIO_ANR_TILT"       # Automatic neighbor relation & RF coverage compensation
    HARDWARE_APS = "HARDWARE_APS"           # Automatic Protection Switching at optical/physical layer
    NONE = "NONE"                           # No autonomous self-healing; requires external intervention


class NetworkResilienceDesignContract(BaseContract):
    """
    Structural resilience design profile of a Network Element, Link, or Cloud-Native Function.
    Zaki fetches this on demand to verify if autonomous self-healing exists or if a workaround is viable.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="NetworkResilienceDesign", description="Contract kind identifier")
    
    entity_id: str = Field(description="Unique identifier of the target Network Element, Link, or Service")
    domain: str = Field(description="Operational domain (e.g., IP_TRANSPORT, 5G_CORE, RAN, CLOUD_INFRA, CHARGING)")
    
    # Structural Redundancy Architecture
    redundancy_model: RedundancyModel = Field(
        default=RedundancyModel.N_PLUS_ONE,
        description="Configured redundancy architecture"
    )
    availability_zone: Optional[str] = Field(default=None, description="Availability zone identifier")
    region: Optional[str] = Field(default=None, description="Geographic region identifier")
    standby_peer_ids: List[str] = Field(
        default_factory=list,
        description="Available backup network elements, secondary routes, or redundant peers"
    )
    
    # Inherent Autonomous Self-Healing
    configured_self_healing: SelfHealingMechanism = Field(
        default=SelfHealingMechanism.NONE,
        description="Autonomous self-healing protocol configured on this entity"
    )
    self_healing_target_mttr_ms: int = Field(
        default=50,
        description="Expected autonomous recovery time in milliseconds (e.g. 50ms for MPLS FRR)"
    )
    
    # Dynamic Readiness & Capacity
    backup_path_healthy: bool = Field(
        default=True,
        description="True if backup entity/route is operational and ready to accept diverted traffic"
    )
    capacity_headroom_pct: float = Field(
        default=100.0,
        description="Available traffic capacity percentage on backup path (0.0 to 100.0)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional vendor or protocol metadata")
