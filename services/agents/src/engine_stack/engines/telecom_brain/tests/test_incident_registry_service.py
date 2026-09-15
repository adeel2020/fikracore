from __future__ import annotations

import pytest

from correlation.registry import IncidentRegistry
from engine_stack.engines.telecom_brain.engine_context import create_default_context
from engine_stack.engines.telecom_brain.models import AlarmEvidence, TelecomRequest
from engine_stack.engines.telecom_brain.services.incident_registry import IncidentRegistryService


@pytest.mark.anyio
async def test_incident_registry_service_lists_existing_registry_records(tmp_path) -> None:
    registry = IncidentRegistry(tmp_path / "registry.db")
    registry.upsert({
        "incident_id": "mobile-core/incidents/amf-overload",
        "tenant_id": "tenant-a",
        "status": "open",
        "scope": "intra-domain",
        "score": 82,
        "domains": ["5g-core"],
        "services": ["registration"],
        "owner": None,
    })
    service = IncidentRegistryService(registry)

    result = await service.handle(TelecomRequest(query="show current incidents"), create_default_context())

    assert "Current Incidents Under Management" in result.text
    assert result.incidents[0].id == "incidents/mobile-core/amf-overload"
    assert result.data["incidents"][0]["score"] == 82


@pytest.mark.anyio
async def test_incident_registry_service_retains_unknown_alarm_candidates(tmp_path) -> None:
    service = IncidentRegistryService(IncidentRegistry(tmp_path / "registry.db"))
    request = TelecomRequest(
        query="create incident candidate",
        alarms=[AlarmEvidence(name="unknown-sctp-reset", severity="major")],
    )

    result = await service.handle(request, create_default_context())

    assert result.data["candidate"] is True
    assert result.alarm_evidence[0].retained_reason == "not filtered by intent"
