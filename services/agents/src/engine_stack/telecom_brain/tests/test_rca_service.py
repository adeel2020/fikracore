from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from engine_stack.telecom_brain import TelecomBrainEngine
from engine_stack.telecom_brain.engine_context import create_default_context
from engine_stack.telecom_brain.models import AlarmEvidence, TelecomRequest
from engine_stack.telecom_brain.services.rca import RCAService


NOW = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)


@dataclass
class FakeConfirmedStory:
    def to_dict(self) -> dict:
        return {
            "incident_id": "incidents/mobile-core/amf-overload",
            "root_cause": {"value": "AMF CPU saturation from registration load"},
            "hypotheses": [
                {
                    "hypothesis": {"value": "AMF CPU saturation from registration load"},
                    "status": "confirmed",
                    "score": 1.0,
                    "evidence": [{"value": "CPU at 98 percent and NAS rejects increased."}],
                }
            ],
            "unresolved_questions": [],
        }


class FakeConfirmedConversation:
    def ask(self, *, path_incident_id, message, session_id=None, intent=None):
        return FakeConfirmedStory(), "root_cause", "Confirmed root cause: AMF CPU saturation", path_incident_id


@pytest.mark.anyio
async def test_rca_from_correlation_never_confirms_root_cause() -> None:
    service = RCAService()
    request = TelecomRequest(
        query="what is root cause",
        context={
            "correlation_results": [
                {
                    "correlation_key": "abc123",
                    "outcome": "incident",
                    "scope": "inter-domain",
                    "score": 95,
                    "domains": ["ran", "transport", "mobile-core"],
                    "services": ["registration"],
                    "intent_status": "violated",
                    "reasons": [
                        "multiple alarms in the correlation window",
                        "shared affected service",
                        "KPI breach supports service impact",
                        "independent operational evidence",
                        "service intent is violated",
                    ],
                    "alarms": ["alarm-1", "alarm-2"],
                    "evidence": ["kpi-1", "ticket-1"],
                }
            ]
        },
    )

    result = await service.handle(request, create_default_context())

    assert result.data["root_cause_confirmed"] is False
    assert "Root cause is not confirmed" in result.text
    assert result.rca_hypotheses[0].confidence == 0.95
    assert "confirmed root-cause evidence" in result.rca_hypotheses[0].missing_proof


@pytest.mark.anyio
async def test_rca_reports_confirmed_root_only_from_story_evidence() -> None:
    service = RCAService(conversation=FakeConfirmedConversation())
    request = TelecomRequest(query="root cause for incidents/mobile-core/amf-overload")

    result = await service.handle(request, create_default_context())

    assert result.data["root_cause_confirmed"] is True
    assert "Confirmed root cause" in result.text
    assert result.rca_hypotheses[0].cause == "AMF CPU saturation from registration load"
    assert "storyteller.reasoning.pipeline" in result.trace.provenance


@pytest.mark.anyio
async def test_engine_routes_rca_alarm_questions_to_rca_service() -> None:
    engine = TelecomBrainEngine()

    result = await engine.process(
        "what is root cause for these alarms",
        context={
            "alarms": [
                {
                    "id": "alarm-1",
                    "name": "CPU_HIGH",
                    "severity": "critical",
                    "source": "nms",
                    "starts_at": NOW,
                    "labels": {
                        "tenant_id": "tenant-a",
                        "domain": "mobile-core",
                        "object_id": "amf-1",
                        "alarm_code": "CPU_HIGH",
                        "service_id": "registration",
                    },
                }
            ]
        },
    )

    assert result.service_id == "rca"
    assert result.data["root_cause_confirmed"] is False
    assert result.rca_hypotheses


@pytest.mark.anyio
async def test_rca_confidence_prefers_root_cause_questions() -> None:
    service = RCAService()
    score = await service.can_handle(TelecomRequest(query="why did attach fail and what is root cause?"))

    assert score >= 0.55
