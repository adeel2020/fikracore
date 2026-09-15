"""Synthetic Grafana LGTM adapter for local mobile-core correlation POC."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..models import AlarmEvent, EvidenceEvent, ServiceIntent


class SyntheticGrafanaAdapter:
    """Loads LGTM-shaped telemetry fixtures and normalizes them for correlation."""

    def __init__(self, fixtures: Path) -> None:
        self.fixtures = fixtures

    def load(self, *, service: str | None = None, intent: str | None = None) -> tuple[list[AlarmEvent], list[EvidenceEvent], list[ServiceIntent]]:
        alarms = [self._alarm(row) for row in _jsonl(self.fixtures / "alerts.jsonl")]
        evidence = [self._evidence(row) for row in _jsonl(self.fixtures / "evidence.jsonl")]
        intents = [self._intent(row) for row in _jsonl(self.fixtures / "intents.jsonl")]
        if service:
            alarms = [alarm for alarm in alarms if service in alarm.service_ids]
            evidence = [item for item in evidence if item.service_id == service]
            intents = [item for item in intents if item.service_id == service]
        if intent:
            intents = [item for item in intents if item.intent_id == intent]
            service_ids = {item.service_id for item in intents}
            if service_ids:
                alarms = [alarm for alarm in alarms if set(alarm.service_ids) & service_ids]
                evidence = [item for item in evidence if item.service_id in service_ids]
        return alarms, evidence, intents

    @staticmethod
    def _alarm(row: dict) -> AlarmEvent:
        return AlarmEvent(
            tenant_id=row.get("tenant_id", "local"),
            source_id=row["id"],
            timestamp=_time(row["timestamp"]),
            severity=row["severity"],
            domain=row["domain"],
            source_system=row.get("source_system", "grafana-alerting"),
            object_id=row["object_id"],
            alarm_code=row["alarm_code"],
            component_kind=row.get("component_kind", "component"),
            location=row.get("location"),
            service_ids=tuple(row.get("service_ids", [])),
        )

    @staticmethod
    def _evidence(row: dict) -> EvidenceEvent:
        attributes = dict(row)
        attributes.setdefault("source_namespace", "grafana")
        return EvidenceEvent(
            source_id=row["id"],
            kind=row["kind"],
            timestamp=_time(row["timestamp"]),
            service_id=row.get("service_id"),
            breached=row.get("breached", False),
            attributes=attributes,
        )

    @staticmethod
    def _intent(row: dict) -> ServiceIntent:
        return ServiceIntent(
            service_id=row["service_id"],
            intent_id=row["intent_id"],
            target_kpi=row["target_kpi"],
            target_value=float(row["target_value"]),
            comparator=row.get("comparator", ">="),
        )


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
