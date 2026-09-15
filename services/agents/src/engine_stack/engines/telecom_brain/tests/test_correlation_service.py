from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from engine_stack.engines.telecom_brain import TelecomBrainEngine
from engine_stack.engines.telecom_brain.engine_context import create_default_context
from engine_stack.engines.telecom_brain.models import AlarmEvidence, KpiEvidence, TelecomRequest
from engine_stack.engines.telecom_brain.services.correlation import CorrelationService


NOW = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)


def _alarm(source_id: str, *, domain: str = "ran", severity: str = "major") -> AlarmEvidence:
    return AlarmEvidence(
        id=source_id,
        name="LINK_DOWN",
        severity=severity,
        source="nms",
        starts_at=NOW + timedelta(minutes=int(source_id[-1])),
        labels={
            "tenant_id": "tenant-a",
            "domain": domain,
            "object_id": source_id,
            "alarm_code": "LINK_DOWN",
            "service_id": "registration",
            "location": "site-1",
        },
    )


@pytest.mark.anyio
async def test_correlation_service_produces_incident_candidate_with_intent_context() -> None:
    service = CorrelationService()
    request = TelecomRequest(
        query="correlate these alarms with intent evidence",
        alarms=[
            _alarm("alarm-1", domain="ran", severity="critical"),
            _alarm("alarm-2", domain="transport"),
        ],
        kpis=[
            KpiEvidence(
                name="registration_success_rate",
                value=92.0,
                threshold=99.5,
                breached=True,
                labels={"service_id": "registration", "timestamp": NOW.isoformat()},
            )
        ],
        context={
            "intents": [
                {
                    "service_id": "registration",
                    "intent_id": "registration-availability",
                    "target_kpi": "registration_success_rate",
                    "target_value": 99.5,
                }
            ]
        },
    )

    result = await service.handle(request, create_default_context())

    assert result.data["correlation_results"][0]["outcome"] == "incident"
    assert result.data["correlation_results"][0]["intent_status"] == "violated"
    assert result.incidents[0].id.startswith("incidents/mobile-core/registration-")
    assert result.intent_violations[0].retained is True
    assert "correlation.CorrelationEngine" in result.trace.provenance


@pytest.mark.anyio
async def test_correlation_service_retains_unknown_unmatched_alarm() -> None:
    service = CorrelationService()
    request = TelecomRequest(
        query="correlate unknown alarm",
        alarms=[
            AlarmEvidence(
                name="UNKNOWN_SCTP_RESET",
                severity="minor",
                source="nms",
                starts_at=NOW,
                labels={"tenant_id": "tenant-a", "domain": "5g-core", "object_id": "amf-1"},
            )
        ],
    )

    result = await service.handle(request, create_default_context())

    assert result.data["correlation_results"][0]["outcome"] in {"candidate", "standalone"}
    assert result.alarm_evidence[0].retained_reason
    assert "intent_status=not_matched" in result.alarm_evidence[0].retained_reason


@pytest.mark.anyio
async def test_engine_routes_alarm_context_to_correlation_service() -> None:
    engine = TelecomBrainEngine()

    result = await engine.process(
        "correlate alarms",
        context={
            "alarms": [
                {
                    "id": "alarm-1",
                    "name": "LINK_DOWN",
                    "severity": "critical",
                    "source": "nms",
                    "starts_at": NOW,
                    "labels": {
                        "tenant_id": "tenant-a",
                        "domain": "ran",
                        "object_id": "cell-1",
                        "alarm_code": "LINK_DOWN",
                        "service_id": "registration",
                    },
                }
            ]
        },
    )

    assert result.service_id == "correlation"
    assert result.trace.selected_service == "correlation"
    assert result.alarm_evidence[0].retained_reason
