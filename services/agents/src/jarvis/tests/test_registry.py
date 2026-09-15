from __future__ import annotations

import asyncio

from assistant.mark import JARVIS
from jarvis.router import capabilities
from capability_registry import load_default_registry


def test_registry_loads_and_resolves_references():
    registry = load_default_registry()

    assert registry.id == "mark"
    assert "telecom_brain" in registry.engines
    assert "correlation" in registry.services
    assert "gbrain" in registry.connectors
    assert "incident-storytelling" in registry.skills


def test_telecom_brain_keeps_correlation_and_grafana_under_same_umbrella():
    registry = load_default_registry()
    telecom = registry.engines["telecom_brain"]

    assert "correlation" in telecom.services
    assert "telemetry_evidence" in telecom.services
    assert "grafana" in telecom.connectors
    assert registry.services["correlation"].engine == "telecom_brain"
    assert registry.connectors["grafana"].owner_engine == "telecom_brain"


def test_collaboration_is_draft_first_and_uses_whatsapp_and_gmail():
    registry = load_default_registry()
    collaboration = registry.engines["collaboration"]
    stakeholder_skill = registry.skills["stakeholder-update"]

    assert set(collaboration.connectors) == {"gmail", "whatsapp", "microsoft_teams"}
    assert stakeholder_skill.requires_approval is True
    assert "send_requires_approval" in collaboration.permissions


def test_knowledge_base_is_metadata_first_before_vector_retrieval():
    registry = load_default_registry()
    knowledge = registry.engines["knowledge_base"]
    skill = registry.skills["metadata-first-document-answering"]

    assert knowledge.services == ["document_catalog", "vector_retrieval"]
    assert "microsoft_office" in knowledge.connectors
    assert skill.services[0] == "document_catalog"
    assert skill.services[1] == "vector_retrieval"


def test_capabilities_api_shape_is_stable():
    payload = load_default_registry().to_capabilities()

    assert payload["name"] == "MARK"
    assert {engine["id"] for engine in payload["engines"]} >= {
        "telecom_brain",
        "knowledge_base",
        "collaboration",
        "calendar",
        "codex_engineering",
    }
    assert all("id" in item and "status" in item for item in payload["services"])
    assert all(connector["transport"] == "mcp" for connector in payload["connectors"])
    assert all(connector["managed_by"] == "mcp_client_hub" for connector in payload["connectors"])


def test_capabilities_endpoint_returns_registry_payload():
    payload = asyncio.run(capabilities())

    assert payload["id"] == "mark"
    assert any(engine["id"] == "telecom_brain" for engine in payload["engines"])
    assert any(skill["id"] == "incident-storytelling" for skill in payload["skills"])


def test_mark_can_answer_engine_inventory_from_registry():
    jarvis = JARVIS()
    jarvis.registry = load_default_registry()

    answer = asyncio.run(jarvis.process("How many brain engines do you have right now?"))

    assert "6 registered engines" in answer
    assert "Telecom Brain Engine" in answer
    assert "registered skills" in answer


def test_all_connectors_are_mcp_managed_by_the_shared_hub():
    registry = load_default_registry()

    assert len(registry.connectors) == 10
    assert all(connector.transport == "mcp" for connector in registry.connectors.values())
    assert all(connector.managed_by == "mcp_client_hub" for connector in registry.connectors.values())
    assert "microsoft_teams" in registry.connectors
    assert "microsoft_office" in registry.connectors


def test_hybrid_connector_runtime_protocols_are_declared():
    registry = load_default_registry()

    assert registry.connectors["codex"].raw["mcp_runtime"]["protocol"] == "stdio"
    assert registry.connectors["gbrain"].raw["mcp_runtime"]["protocol"] == "http"
    assert "stdio" in registry.connectors["gbrain"].fallback_transports
    assert registry.connectors["grafana"].raw["mcp_runtime"]["protocol"] == "http"


def test_registry_exposes_inbound_server_and_outbound_hub():
    registry = load_default_registry()

    assert registry.runtime["inbound_mcp_server"]["id"] == "mark_mcp_server"
    assert registry.runtime["outbound_mcp_client_hub"]["id"] == "mcp_client_hub"
