from correlation.registry import IncidentRegistry


def test_registry_lists_and_audits_lifecycle(tmp_path):
    registry = IncidentRegistry(tmp_path / "registry.db")
    registry.upsert({"incident_id": "mobile-core/incidents/test-1", "tenant_id": "tenant-a", "status": "candidate", "scope": "inter-domain", "score": 80, "domains": ["ran", "transport"], "services": ["registration"], "owner": None})
    registry.transition("mobile-core/incidents/test-1", "acknowledge", actor="adeel", reason="reviewing")
    record = registry.get("mobile-core/incidents/test-1")
    assert record["status"] == "acknowledged"
    assert record["incident_id"] == "incidents/mobile-core/test-1"
    assert "mobile-core/incidents/test-1" in record["aliases"]
    assert [item["incident_id"] for item in registry.list()] == ["incidents/mobile-core/test-1"]
    assert registry.list(tenant_id="tenant-a")[0]["incident_id"] == record["incident_id"]
    assert registry.audit(record["incident_id"])[0]["action"] == "acknowledge"
