"""Correlation Finding Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class CorrelationFindingItem(BaseContract):
    finding_id: str
    dimension: str  # temporal_identity, topological, cross_domain_pathway, service_blast_radius
    funnel: Optional[str] = None  # operational_evidence, service_dependency, etc.
    title: str
    received: str = ""
    checks_performed: List[str] = Field(default_factory=list)
    found: str = ""
    why_it_matters: str = ""
    forwarded_to_reasoning: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    affected_entities: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    provenance: str = "correlation_engine"


class CorrelationFindingContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "CorrelationFindings"
    run_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    temporal_identity: Dict[str, Any] = Field(default_factory=dict)
    topological: Dict[str, Any] = Field(default_factory=dict)
    cross_domain_pathways: Dict[str, Any] = Field(default_factory=dict)
    service_blast_radius: Dict[str, Any] = Field(default_factory=dict)
    findings: List[CorrelationFindingItem] = Field(default_factory=list)
