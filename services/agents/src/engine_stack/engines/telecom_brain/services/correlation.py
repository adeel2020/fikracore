"""Correlation service wrapper over the existing correlation engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from correlation.engine import CorrelationEngine
from correlation.models import AlarmEvent, CorrelationResult, EvidenceEvent, ServiceIntent
from correlation.namespaces import incident_slug

from ..engine_context import TelecomContext
from ..models import (
    AlarmEvidence,
    FCAPSClassification,
    IncidentRef,
    IntentViolation,
    KpiEvidence,
    TelecomRequest,
    TelecomResult,
    TelecomTrace,
)


class CorrelationService:
    id = "correlation"

    def __init__(self, engine: CorrelationEngine | None = None) -> None:
        self.engine = engine or CorrelationEngine()

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if request.alarms:
            score += 0.45
        if any(term in query for term in ("correlate", "correlation", "cluster alarms", "alarm storm")):
            score += 0.4
        if any(term in query for term in ("candidate", "incident candidate", "related alarms")):
            score += 0.2
        if any(term in query for term in ("intent", "kpi", "breach", "violated")):
            score += 0.1
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        alarms = self._to_alarm_events(request)
        if not alarms:
            return TelecomResult(
                text="Please provide alarms to correlate.",
                spoken_response="Please provide alarms to correlate.",
                service_id=self.id,
                trace=TelecomTrace(selected_service=self.id, warnings=["correlation requested without alarms"]),
            )

        results = self.engine.correlate(
            alarms,
            evidence=self._to_evidence_events(request),
            intents=self._to_service_intents(request),
        )
        incidents = [self._incident_ref(result) for result in results if result.outcome in {"incident", "candidate"}]
        retained = self._retained_alarm_evidence(request, results)
        intent_violations = [self._intent_violation(result) for result in results if result.intent_status == "violated"]
        text = self._format_results(results)
        warnings = []
        if any(result.outcome == "standalone" for result in results):
            warnings.append("Standalone alarms retained; intent matching was not used as a hard filter.")

        return TelecomResult(
            text=text,
            spoken_response=self._spoken_summary(results),
            service_id=self.id,
            trace=TelecomTrace(
                selected_service=self.id,
                provenance=["correlation.CorrelationEngine"],
                warnings=warnings,
            ),
            incidents=incidents,
            alarm_evidence=retained,
            kpi_evidence=request.kpis,
            intent_violations=intent_violations,
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
            data={"correlation_results": [self._serialize_result(result) for result in results]},
        )

    @staticmethod
    def _to_alarm_events(request: TelecomRequest) -> list[AlarmEvent]:
        default_services = tuple(proc.id for proc in request.service_procedure_refs)
        events = []
        now = datetime.now(timezone.utc)
        for idx, alarm in enumerate(request.alarms):
            labels = alarm.labels
            source_id = CorrelationService._alarm_source_id(alarm, idx)
            service_ids = labels.get("service_ids") or labels.get("services") or labels.get("service_id")
            if isinstance(service_ids, str):
                services = (service_ids,)
            elif service_ids:
                services = tuple(str(item) for item in service_ids)
            else:
                services = default_services
            events.append(
                AlarmEvent(
                    tenant_id=str(labels.get("tenant_id") or request.context.get("tenant_id") or "default"),
                    source_id=source_id,
                    timestamp=alarm.starts_at or now,
                    severity=alarm.severity or "minor",
                    domain=str(labels.get("domain") or "unknown"),
                    source_system=alarm.source or str(labels.get("source_system") or "telecom_brain"),
                    object_id=str(labels.get("object_id") or labels.get("component") or alarm.name),
                    alarm_code=str(labels.get("alarm_code") or labels.get("code") or alarm.name),
                    component_kind=str(labels.get("component_kind") or "component"),
                    location=labels.get("location"),
                    service_ids=services,
                )
            )
        return events

    @staticmethod
    def _to_evidence_events(request: TelecomRequest) -> list[EvidenceEvent]:
        events = []
        now = datetime.now(timezone.utc)
        for idx, kpi in enumerate(request.kpis):
            labels = kpi.labels
            events.append(
                EvidenceEvent(
                    source_id=kpi.raw_ref or str(labels.get("source_id") or f"kpi-{idx}"),
                    kind="kpi",
                    timestamp=CorrelationService._coerce_timestamp(labels.get("timestamp")) or now,
                    service_id=labels.get("service_id"),
                    breached=bool(kpi.breached),
                    attributes={
                        "name": kpi.name,
                        "value": kpi.value,
                        "unit": kpi.unit,
                        "threshold": kpi.threshold,
                        "source_namespace": labels.get("source_namespace", "mobile-core"),
                    },
                )
            )
        return events

    @staticmethod
    def _to_service_intents(request: TelecomRequest) -> list[ServiceIntent]:
        intents = []
        for raw in request.context.get("intents", []):
            if not isinstance(raw, dict):
                continue
            service_id = raw.get("service_id")
            intent_id = raw.get("intent_id") or raw.get("id")
            target_kpi = raw.get("target_kpi") or raw.get("kpi")
            target_value = raw.get("target_value") or raw.get("threshold")
            if service_id and intent_id and target_kpi and target_value is not None:
                intents.append(
                    ServiceIntent(
                        service_id=str(service_id),
                        intent_id=str(intent_id),
                        target_kpi=str(target_kpi),
                        target_value=float(target_value),
                        comparator=raw.get("comparator", ">="),
                    )
                )
        return intents

    @staticmethod
    def _incident_ref(result: CorrelationResult) -> IncidentRef:
        service_id = result.services[0] if result.services else "unmapped"
        return IncidentRef(
            id=incident_slug(service_id, result.correlation_key),
            status="open" if result.outcome == "incident" else "candidate",
            severity=str(result.score),
            source="correlation",
            metadata={
                "correlation_key": result.correlation_key,
                "scope": result.scope,
                "domains": result.domains,
                "services": result.services,
                "intent_status": result.intent_status,
                "reasons": result.reasons,
            },
        )

    @staticmethod
    def _intent_violation(result: CorrelationResult) -> IntentViolation:
        procedure = result.services[0] if result.services else None
        return IntentViolation(
            procedure=procedure,
            description=f"Correlation {result.correlation_key} indicates intent violation for {procedure or 'unmapped service'}.",
            confidence=min(result.score / 100, 1.0),
            retained=True,
        )

    @staticmethod
    def _retained_alarm_evidence(request: TelecomRequest, results: list[CorrelationResult]) -> list[AlarmEvidence]:
        by_source_id = {}
        for result in results:
            for alarm in result.alarms:
                by_source_id[alarm.source_id] = result

        retained = []
        for idx, alarm in enumerate(request.alarms):
            source_id = CorrelationService._alarm_source_id(alarm, idx)
            result = by_source_id.get(source_id)
            reason = "not filtered by intent"
            if result is not None:
                reason = f"{result.outcome}; intent_status={result.intent_status}"
            retained.append(alarm.model_copy(update={"retained_reason": alarm.retained_reason or reason}))
        return retained

    @staticmethod
    def _alarm_source_id(alarm: AlarmEvidence, idx: int) -> str:
        return str(alarm.id or alarm.raw_ref or alarm.labels.get("source_id") or f"alarm-{idx}")

    @staticmethod
    def _coerce_timestamp(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def _serialize_result(result: CorrelationResult) -> dict[str, Any]:
        return {
            "correlation_key": result.correlation_key,
            "tenant_id": result.tenant_id,
            "outcome": result.outcome,
            "scope": result.scope,
            "score": result.score,
            "domains": result.domains,
            "services": result.services,
            "intent_status": result.intent_status,
            "reasons": result.reasons,
            "alarms": [alarm.source_id for alarm in result.alarms],
            "evidence": [item.source_id for item in result.evidence],
        }

    @staticmethod
    def _format_results(results: list[CorrelationResult]) -> str:
        lines = ["**Correlation Results**"]
        for result in results:
            service_text = ", ".join(result.services) if result.services else "unmapped service"
            lines.append(
                f"- {result.outcome}: {service_text} | {result.scope} | score={result.score} | intent={result.intent_status}"
            )
            for reason in result.reasons[:4]:
                lines.append(f"  - {reason}")
        return "\n".join(lines)

    @staticmethod
    def _spoken_summary(results: list[CorrelationResult]) -> str:
        incidents = sum(1 for result in results if result.outcome == "incident")
        candidates = sum(1 for result in results if result.outcome == "candidate")
        standalone = sum(1 for result in results if result.outcome == "standalone")
        return f"Correlation found {incidents} incidents, {candidates} candidates, and retained {standalone} standalone alarm groups."
