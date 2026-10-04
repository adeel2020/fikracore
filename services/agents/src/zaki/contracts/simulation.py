"""
What-If Simulation Contract
==========================
Defines counterfactual and predictive simulation results evaluating hypothetical
network actions, maintenance operations, or candidate remediations.
Fully incident- and event-agnostic (executable both proactively and reactively).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class SimulationMode(str, Enum):
    """Operational context in which simulation was dispatched."""
    PROACTIVE_PLANNING = "PROACTIVE_PLANNING"       # Pre-maintenance window validation, capacity planning
    REACTIVE_MITIGATION = "REACTIVE_MITIGATION"     # Pre-execution safety check of candidate remediation
    HYPOTHETICAL_AUDIT = "HYPOTHETICAL_AUDIT"       # Resilience / chaos testing of single point of failure


class BlastRadiusDelta(str, Enum):
    """Predicted change in failure or degradation envelope under simulated action."""
    ELIMINATED = "ELIMINATED"   # Outage/degradation completely resolved
    REDUCED = "REDUCED"         # Degradation reduced in scope or severity
    NEUTRAL = "NEUTRAL"         # Zero net change in blast radius
    EXPANDED = "EXPANDED"       # Warning: action worsens condition or causes secondary dropouts


class WhatIfSimulationContract(BaseContract):
    """
    Predictive evaluation of a proposed network change, maintenance step, or remediation.
    Agnostic to incident type, event trigger, or network vendor.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="WhatIfSimulation", description="Contract kind identifier")
    
    simulation_id: str = Field(description="Unique simulation execution identifier")
    simulation_mode: SimulationMode = Field(
        default=SimulationMode.PROACTIVE_PLANNING,
        description="PROACTIVE_PLANNING, REACTIVE_MITIGATION, or HYPOTHETICAL_AUDIT"
    )
    event_ref: Optional[str] = Field(default=None, description="Optional incident or maintenance ticket reference")
    
    # Proposed Action Specification
    simulated_action: str = Field(
        description="Description or command of the simulated action (e.g., 'BUMP_METRIC_TO_65535', 'DRAIN_NODE')"
    )
    target_entities: List[str] = Field(
        default_factory=list,
        description="Network elements, links, or software components targeted by the action"
    )
    action_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Simulated parameters (e.g., new metric values, shifted traffic percentage)"
    )
    
    # Predictive Impact & Safety Projections
    expected_blast_radius_delta: BlastRadiusDelta = Field(
        default=BlastRadiusDelta.REDUCED,
        description="Predicted outcome on operational failure envelope"
    )
    predicted_capacity_headroom_pct: float = Field(
        default=100.0,
        description="Predicted remaining capacity percentage on alternate/surviving paths (0.0 to 100.0)"
    )
    secondary_failure_risk_score: float = Field(
        default=0.0,
        description="Risk probability of triggering cascading failures on adjacent nodes (0.0 to 1.0)"
    )
    estimated_recovery_time_sec: int = Field(
        default=30,
        description="Projected seconds until network restabilizes after action"
    )
    is_safe_to_execute: bool = Field(
        default=True,
        description="True if capacity headroom and risk score satisfy safety policy thresholds"
    )
    risk_summary: str = Field(
        default="",
        description="Human-interpretable safety assessment and engineering recommendation"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extension metadata")
