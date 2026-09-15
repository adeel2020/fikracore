from __future__ import annotations

from datetime import datetime, timezone

import pytest

from correlation.registry import IncidentRegistry
from engine_stack.telecom_brain import TelecomBrainEngine
from engine_stack.telecom_brain.engine_context import create_default_context
from engine_stack.telecom_brain.models import AlarmEvidence, KpiEvidence, ServiceProcedure, TelecomRequest
from engine_stack.telecom_brain.services.fcaps_learning import FCAPSLearningService
from engine_stack.telecom_brain.services.intent import IntentService
from engine_stack.telecom_brain.services.network_health import NetworkHealthService
from engine_stack.telecom_brain.services.playbook_runbook import PlaybookRunbookService
from engine_stack.telecom_brain.services.remediation_advisory import RemediationAdvisoryService
from engine_stack.telecom_brain.services.telemetry_evidence import TelemetryEvidenceService
from engine_stack.telecom_brain.services.topology import TopologyService


NOW = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)


class FakeHub:
    def __init__(self) -> None:
        self.calls = []

    async def call_tool(self, connector_id, tool_name, arguments=None, **kwargs):
        self.calls.append((connector_id, tool_name, arguments or {}))
        if connector_id == "grafana":
            return {
                "ref": "grafana/result/1",
                "kpis": [
                    {
                        "id": "kpi-1",
                        "name": "registration_success_rate",
                        "value": 92.0,
                        "threshold": 99.5,
                        "breached": True,
                        "service_id": arguments.get("service_id"),
                    }
                ],
            }
        return {"ok": True}


def _context_with_fake_hub():
    context = create_default_context()
    context.mcp_hub = FakeHub()
    return context


def _alarm(name: str = "AMF CPU HIGH") -> AlarmEvidence:
    return AlarmEvidence(
        id="alarm-1",
        name=name,
        severity="critical",
        source="nms",
        starts_at=NOW,
        labels={"tenant_id": "tenant-a", "domain": "mobile-core", "object_id": "amf-1", "service_id": "registration"},
    )


@pytest.mark.anyio
async def test_telemetry_service_uses_mcp_hub_for_grafana_first() -> None:
    context = _context_with_fake_hub()
    service = TelemetryEvidenceService()

    result = await service.handle(
        TelecomRequest(query="show Grafana KPI evidence", context={"service_id": "registration"}),
        context,
    )

    assert context.mcp_hub.calls[0][0] == "grafana"
    assert context.mcp_hub.calls[0][1] == "query_kpi_window"
    assert any(call[0] == "gbrain" for call in context.mcp_hub.calls)
    assert result.kpi_evidence[0].breached is True
    assert "raw telemetry remains in Grafana" in result.data["gbrain_projection"]["summary"]


@pytest.mark.anyio
async def test_intent_service_scores_and_retains_unmatched_alarm() -> None:
    result = await IntentService().handle(
        TelecomRequest(
            query="score service intent",
            alarms=[_alarm("UNKNOWN SCTP RESET")],
            kpis=[KpiEvidence(name="registration_success_rate", breached=True, labels={"service_id": "registration"})],
        ),
        create_default_context(),
    )

    assert result.alarm_evidence[0].retained_reason
    assert result.alarm_evidence[0].retained_reason.startswith("unmatched intent") or "intent_score" in result.alarm_evidence[0].retained_reason
    assert result.trace.warnings


@pytest.mark.anyio
async def test_topology_service_resolves_logical_dependency_path() -> None:
    context = _context_with_fake_hub()

    result = await TopologyService().handle(
        TelecomRequest(query="show LTE attach blast radius"),
        context,
    )

    assert result.data["service_id"] == "lte-attach"
    assert "mobile-core.lte.mme" in result.data["dependency_path"]
    assert any(call[0] == "gbrain" for call in context.mcp_hub.calls)


@pytest.mark.anyio
async def test_fcaps_learning_service_proposes_reviewed_learning_candidates() -> None:
    context = _context_with_fake_hub()

    result = await FCAPSLearningService().handle(
        TelecomRequest(query="what did we learn: missing playbook and missing Grafana query after CPU alarm"),
        context,
    )

    assert "fault" in result.data["learning_candidate"]["fcaps"]
    assert any("playbook" in gap for gap in result.data["learning_candidate"]["gaps"])
    assert any(call[0] == "gbrain" for call in context.mcp_hub.calls)


@pytest.mark.anyio
async def test_playbook_runbook_service_recommends_assets() -> None:
    result = await PlaybookRunbookService().handle(
        TelecomRequest(query="find LTE attach playbook and runbook", service_procedure_refs=[ServiceProcedure(id="lte-attach", name="LTE Attach")]),
        create_default_context(),
    )

    assert result.data["assets"]["playbook"].endswith("lte-attach-failure-triage")
    assert any(action.action_type == "runbook" and action.requires_approval for action in result.recommended_actions)


@pytest.mark.anyio
async def test_remediation_advisory_requires_approval_for_execution_like_actions() -> None:
    result = await RemediationAdvisoryService().handle(
        TelecomRequest(query="what should I do next for CPU capacity issue and rollback candidate"),
        create_default_context(),
    )

    assert result.data["approval_required"] is True
    assert any(action.requires_approval for action in result.recommended_actions)
    assert "Advisory only" in result.trace.warnings[0]


@pytest.mark.anyio
async def test_network_health_service_summarizes_registry_kpis_and_alarm_pressure(tmp_path) -> None:
    registry = IncidentRegistry(tmp_path / "registry.db")
    registry.upsert({
        "incident_id": "mobile-core/incidents/amf-overload",
        "tenant_id": "tenant-a",
        "status": "open",
        "scope": "intra-domain",
        "score": 75,
        "domains": ["mobile-core"],
        "services": ["registration"],
        "owner": None,
    })
    service = NetworkHealthService(registry)

    result = await service.handle(
        TelecomRequest(
            query="brief me on network health",
            alarms=[_alarm()],
            kpis=[KpiEvidence(name="registration_success_rate", breached=True)],
        ),
        create_default_context(),
    )

    assert result.incidents[0].id == "incidents/mobile-core/amf-overload"
    assert result.data["alarm_pressure"]["mobile-core"] == 1
    assert result.kpi_evidence[0].breached is True


@pytest.mark.anyio
async def test_engine_registers_all_planned_services() -> None:
    service_ids = [service.id for service in TelecomBrainEngine().services]

    assert service_ids == [
        "storytelling",
        "rca",
        "correlation",
        "telemetry_evidence",
        "intent",
        "topology",
        "fcaps_learning",
        "playbook_runbook",
        "remediation_advisory",
        "network_health",
        "incident_registry",
    ]
