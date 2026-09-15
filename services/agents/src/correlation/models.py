"""Canonical models used by the correlation worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


Outcome = Literal["standalone", "candidate", "incident"]


@dataclass(frozen=True)
class AlarmEvent:
    tenant_id: str
    source_id: str
    timestamp: datetime
    severity: str
    domain: str
    source_system: str
    object_id: str
    alarm_code: str
    component_kind: str = "component"
    location: str | None = None
    service_ids: tuple[str, ...] = ()

    @property
    def novelty_key(self) -> tuple[str, str, str, str]:
        return (self.domain, self.source_system, self.alarm_code, self.component_kind)


@dataclass(frozen=True)
class EvidenceEvent:
    source_id: str
    kind: Literal["kpi", "ticket", "log", "trace", "change", "dashboard", "panel"]
    timestamp: datetime
    service_id: str | None = None
    breached: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def source_namespace(self) -> str:
        return str(self.attributes.get("source_namespace") or "mobile-core")


@dataclass(frozen=True)
class ServiceIntent:
    service_id: str
    intent_id: str
    target_kpi: str
    target_value: float
    comparator: Literal[">=", "<="] = ">="


@dataclass
class CorrelationResult:
    correlation_key: str
    tenant_id: str
    alarms: list[AlarmEvent]
    evidence: list[EvidenceEvent]
    services: list[str]
    score: int
    reasons: list[str]
    outcome: Outcome
    scope: Literal["intra-domain", "inter-domain"]
    intent_status: Literal["violated", "matched", "not_matched"]

    @property
    def domains(self) -> list[str]:
        return sorted({alarm.domain for alarm in self.alarms})
