"""TelecomBrainEngine facade."""

from __future__ import annotations

from typing import Any

from .engine_context import TelecomContext, create_default_context
from .models import AlarmEvidence, KpiEvidence, ServiceProcedure, TelecomRequest, TelecomResult, TopologyNode
from .services import (
    CorrelationService,
    FCAPSLearningService,
    IncidentRegistryService,
    IntentService,
    MobileRTRService,
    NetworkHealthService,
    PlaybookRunbookService,
    RCAService,
    RemediationAdvisoryService,
    ServiceRouter,
    StorytellingService,
    TelemetryEvidenceService,
    TelecomService,
    TopologyService,
)


class TelecomBrainEngine:
    """One telecom cognition engine composed of internal services."""

    def __init__(
        self,
        context: TelecomContext | None = None,
        services: list[TelecomService] | None = None,
    ) -> None:
        self.context = context or create_default_context()
        self.services = services or [
            MobileRTRService(),
            StorytellingService(),
            RCAService(),
            CorrelationService(),
            TelemetryEvidenceService(),
            IntentService(),
            TopologyService(),
            FCAPSLearningService(),
            PlaybookRunbookService(),
            RemediationAdvisoryService(),
            NetworkHealthService(),
            IncidentRegistryService(),
        ]
        self.router = ServiceRouter(self.services)

    async def initialize(self) -> None:
        """Match Jarvis superpower lifecycle; current services are lazy."""

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> TelecomResult:
        request = TelecomRequest(
            query=self._normalize_speech_terms(query),
            session_id=session_id,
            context=context or {},
            alarms=self._extract_alarm_evidence(context or {}),
            kpis=self._extract_kpi_evidence(context or {}),
            topology_refs=self._extract_topology_refs(context or {}),
            service_procedure_refs=self._extract_service_procedures(context or {}),
        )
        service, trace = await self.router.route(request)
        if service is None:
            result = TelecomResult(
                text=f"Retained standalone telecom observation: {request.query}",
                spoken_response=f"I retained this as a standalone telecom observation: {request.query}",
                service_id=None,
                trace=trace,
                alarm_evidence=request.alarms,
                data={"retained_observation": True},
            )
            return result

        result = await service.handle(request, self.context)
        result.service_id = result.service_id or service.id
        result.trace.selected_service = trace.selected_service
        result.trace.service_confidence = trace.service_confidence
        result.trace.candidates = trace.candidates
        result.trace.warnings = [*trace.warnings, *result.trace.warnings]
        return result

    @staticmethod
    def _normalize_speech_terms(query: str) -> str:
        return " ".join(query.strip().split())

    @staticmethod
    def _extract_alarm_evidence(context: dict[str, Any]) -> list[AlarmEvidence]:
        alarms = context.get("alarms") or []
        evidence = []
        for idx, alarm in enumerate(alarms):
            if isinstance(alarm, AlarmEvidence):
                evidence.append(alarm)
            elif isinstance(alarm, dict):
                evidence.append(AlarmEvidence(name=str(alarm.get("name") or alarm.get("alarm") or f"alarm-{idx}"), **{
                    key: value for key, value in alarm.items() if key not in {"name", "alarm"}
                }))
            else:
                evidence.append(AlarmEvidence(name=str(alarm), retained_reason="unstructured alarm input"))
        return evidence

    @staticmethod
    def _extract_kpi_evidence(context: dict[str, Any]) -> list[KpiEvidence]:
        kpis = context.get("kpis") or []
        evidence = []
        for idx, kpi in enumerate(kpis):
            if isinstance(kpi, KpiEvidence):
                evidence.append(kpi)
            elif isinstance(kpi, dict):
                evidence.append(KpiEvidence(name=str(kpi.get("name") or kpi.get("kpi") or f"kpi-{idx}"), **{
                    key: value for key, value in kpi.items() if key not in {"name", "kpi"}
                }))
            else:
                evidence.append(KpiEvidence(name=str(kpi)))
        return evidence

    @staticmethod
    def _extract_topology_refs(context: dict[str, Any]) -> list[TopologyNode]:
        refs = context.get("topology_refs") or context.get("topology") or []
        nodes = []
        for idx, ref in enumerate(refs):
            if isinstance(ref, TopologyNode):
                nodes.append(ref)
            elif isinstance(ref, dict):
                nodes.append(TopologyNode(id=str(ref.get("id") or f"topology-{idx}"), name=str(ref.get("name") or ref.get("id") or f"topology-{idx}"), **{
                    key: value for key, value in ref.items() if key not in {"id", "name"}
                }))
            else:
                nodes.append(TopologyNode(id=str(ref), name=str(ref)))
        return nodes

    @staticmethod
    def _extract_service_procedures(context: dict[str, Any]) -> list[ServiceProcedure]:
        refs = context.get("service_procedure_refs") or context.get("service_procedures") or []
        procedures = []
        for idx, ref in enumerate(refs):
            if isinstance(ref, ServiceProcedure):
                procedures.append(ref)
            elif isinstance(ref, dict):
                procedures.append(ServiceProcedure(id=str(ref.get("id") or f"procedure-{idx}"), name=str(ref.get("name") or ref.get("id") or f"procedure-{idx}"), **{
                    key: value for key, value in ref.items() if key not in {"id", "name"}
                }))
            else:
                procedures.append(ServiceProcedure(id=str(ref), name=str(ref)))
        return procedures
