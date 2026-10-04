"""Evidence Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import EvidenceStatus


class HarnessEvidenceContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "Evidence"
    evidence_id: str
    source: str
    source_type: str = "telemetry"  # alarms, metrics, logs, traces, changes, tickets, kpis
    event_time: datetime
    ingestion_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    domain: str = "unknown"
    entity: str
    canonical_entity: Optional[str] = None
    service: List[str] = Field(default_factory=list)
    region: str = "default"
    observation: str = ""
    signal: str = ""
    polarity: str = "unknown"  # abnormal, healthy, context, unknown
    severity: str = "UNKNOWN"
    quality: float = Field(default=1.0, ge=0.0, le=1.0)
    source_reliability: float = Field(default=0.95, ge=0.0, le=1.0)
    freshness: float = Field(default=1.0, ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.NEUTRAL
    provenance: str = "operational_telemetry"
    duplicate_ids: List[str] = Field(default_factory=list)
    observed_path: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
