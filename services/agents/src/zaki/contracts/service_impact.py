"""
Service Impact Contract
========================
Defines customer-facing, business, 5G network slice, and SLA impact metrics
resulting from an operational incident.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class SlaStatus(str, Enum):
    """SLA breach status of impacted services or enterprise accounts."""
    NONE = "NONE"               # Normal operational baseline; no breach risk
    AT_RISK = "AT_RISK"         # Performance degradation approaching contract threshold
    BREACHED = "BREACHED"       # SLA contract threshold exceeded; penalty accrued


class SliceImpactItem(BaseContract):
    """5G Network Slice degradation record."""
    slice_id: str = Field(description="Network Slice Identifier (e.g. S-NSSAI or slice tag)")
    slice_type: str = Field(default="eMBB", description="eMBB, URLLC, mMTC, or custom enterprise")
    sla_tier: str = Field(default="STANDARD", description="Service tier (e.g., PLATINUM, GOLD, SILVER)")
    status: str = Field(default="DEGRADED", description="HEALTHY, DEGRADED, DOWN")
    dropped_sessions: int = Field(default=0, description="Estimated subscriber sessions lost on slice")


class ServiceImpactContract(BaseContract):
    """
    Evaluates the customer-facing, business, and SLA degradation caused by an incident.
    Embedded directly inside IncidentContract.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="ServiceImpact", description="Contract kind identifier")
    
    incident_id: str = Field(description="Associated incident identifier")
    
    # 5G Slices & Data Network Names (APNs/DNNs)
    impacted_slices: List[SliceImpactItem] = Field(
        default_factory=list,
        description="5G network slices experiencing degradation or packet loss"
    )
    impacted_apns_dnns: List[str] = Field(
        default_factory=list,
        description="Data Network Names or APNs affected (e.g., voice, internet, enterprise-vpn)"
    )
    
    # Traffic & Subscriber Volume
    dropped_throughput_gbps: float = Field(
        default=0.0,
        description="Total throughput volume lost across degraded interfaces in Gbps"
    )
    affected_active_subscribers: int = Field(
        default=0,
        description="Estimated count of active user sessions interrupted or dropped"
    )
    
    # SLA & Priority Exposure
    sla_status: SlaStatus = Field(
        default=SlaStatus.NONE,
        description="Current SLA breach status"
    )
    vip_enterprise_accounts: List[str] = Field(
        default_factory=list,
        description="High-priority enterprise or priority customer accounts affected"
    )
    critical_services_affected: bool = Field(
        default=False,
        description="True if emergency calling, critical national infrastructure, or public safety is impacted"
    )
    estimated_penalty_exposure_usd: float = Field(
        default=0.0,
        description="Estimated contractual SLA financial penalty exposure"
    )
