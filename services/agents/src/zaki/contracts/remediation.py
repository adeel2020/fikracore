"""
Remediation Strategy & Action Contract
======================================
Defines network element (NE) specific remediation strategies, actions, and classification
including self-healing verification, fast workarounds (metric depref, hot-billing bypass, throttle),
and definitive remedies (rollback, restart, failover, scale-out/in).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class RemediationClass(str, Enum):
    """Operational classification of remediation actions."""
    SELF_HEALING_VERIFICATION = "SELF_HEALING_VERIFICATION"  # Verifying autonomous protocol/subsystem switchover
    WORKAROUND = "WORKAROUND"                                # Fast traffic/SLA protection stopping MTTR clock
    DEFINITIVE_REMEDY = "DEFINITIVE_REMEDY"                  # Permanent root cause elimination


class RemediationStrategyType(str, Enum):
    """
    Standardized Network Element specific remediation strategy types.
    """
    # IP Transport & Routing
    METRIC_DEPREF = "METRIC_DEPREF"         # Cost/metric bumping (OSPF/IS-IS/BGP) to steer traffic away gracefully
    GRACEFUL_DRAIN = "GRACEFUL_DRAIN"       # Max-metric / IS-IS overload drain prior to maintenance
    REROUTE = "REROUTE"                     # Explicit path diversion or LSP re-signaling
    
    # Cloud-Native & Core Functions (K8s, CNFs, VNFs)
    SCALE_OUT = "SCALE_OUT"                 # Horizontal expansion (increase pods/instances)
    SCALE_IN = "SCALE_IN"                   # Terminate unhealthy/stuck instances
    RESTART = "RESTART"                     # Soft/graceful container, daemon, or process restart
    FAILOVER = "FAILOVER"                   # Active/standby plane switchover
    OFFLOAD = "OFFLOAD"                     # Shedding subscriber sessions to adjacent instance pool
    
    # Business, Charging & Billing Systems
    HOT_BILLING_BYPASS = "HOT_BILLING_BYPASS" # Bypass online charging system (OCS/CHF) to prevent dropped calls
    THROTTLE = "THROTTLE"                   # Traffic policing or rate-limiting to prevent buffer exhaustion/OOM
    
    # Lifecycle & Change Management
    ROLLBACK = "ROLLBACK"                   # Revert faulty software, patch, or config commit
    BYPASS = "BYPASS"                       # Hardware or middlebox circuit bypass


class RemediationAction(BaseContract):
    """
    Network Element (NE) Specific Remediation Execution Step.
    """
    action_id: str = Field(description="Unique action identifier within the strategy")
    target_ne_type: str = Field(
        description="Target Network Element category (e.g. ROUTER, UPF, AMF, SMF, ENODEB, OCS_CHF, K8S_CONTAINER)"
    )
    target_ne_id: str = Field(description="Unique entity identifier of the target Network Element")
    strategy_type: RemediationStrategyType = Field(description="NE-specific strategy applied")
    remediation_class: RemediationClass = Field(default=RemediationClass.WORKAROUND)
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="NE-specific execution parameters (e.g. metric delta, replica count, drain duration)"
    )
    rollback_step: Dict[str, Any] = Field(
        default_factory=dict,
        description="Exact inverse operation to revert the action if verification fails"
    )


class RemediationStrategyContract(BaseContract):
    """
    Parent Remediation Strategy formulated to mitigate or resolve an operational incident.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="RemediationStrategy", description="Contract kind identifier")
    
    remediation_id: str = Field(description="Unique remediation strategy plan identifier")
    incident_id: str = Field(description="Associated incident identifier")
    remediation_class: RemediationClass = Field(
        default=RemediationClass.WORKAROUND,
        description="Operational class: SELF_HEALING_VERIFICATION, WORKAROUND, DEFINITIVE_REMEDY"
    )
    is_auto_remediation: bool = Field(
        default=False,
        description="True if executable autonomously by closed-loop automation without human sign-off"
    )
    estimated_mttr_sec: int = Field(
        default=60,
        description="Projected time in seconds to restore service under this strategy"
    )
    target_actions: List[RemediationAction] = Field(
        default_factory=list,
        description="Ordered sequence of NE-specific remediation actions"
    )
    preflight_safety_checks: List[str] = Field(
        default_factory=list,
        description="Validation checks that must pass before execution (e.g., backup capacity headroom > 20%)"
    )
    requires_human_approval: bool = Field(
        default=True,
        description="True if human SME sign-off is required prior to execution"
    )
    projected_throughput_recovered_gbps: float = Field(
        default=0.0,
        description="Projected throughput volume restored upon successful execution in Gbps"
    )
    projected_sla_breach_prevented: bool = Field(
        default=True,
        description="True if this strategy halts the MTTR clock in time to prevent an SLA breach"
    )
