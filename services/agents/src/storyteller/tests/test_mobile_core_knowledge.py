"""Layer 1 (Knowledge / Retrieval) tests against the AMF example.

Requirements §24 / Layer 1:
  get_incident()
  get_kpis()
  get_network_functions()
  get_hypotheses()
  get_evidence()
  get_remediation()
  get_recovery()
  find_similar_incidents()

These are integration tests against the real gbrain graph (mobile-core schema).
Skipped when gbrain is locked/unavailable.
"""

from __future__ import annotations

import pytest
from storyteller.knowledge import MobileCoreKnowledge
from storyteller.tests.conftest import AMF_INCIDENT


class FakeResolverClient:
    def call(self, tool: str, params: dict):
        if tool == "get_page":
            slug = params["slug"]
            if slug == "incidents/ims/voice-call-setup-05841af2e3f4f430":
                return {"slug": slug, "type": "incident", "title": "IMS Voice Call Setup Degradation", "frontmatter": {}}
            return None
        if tool == "list_pages":
            return [
                {
                    "slug": "incidents/ims/voice-call-setup-05841af2e3f4f430",
                    "type": "incident",
                    "title": "IMS Voice Call Setup Degradation",
                }
            ]
        if tool == "query":
            return {"results": []}
        if tool == "traverse_graph":
            return []
        return None


@pytest.fixture(scope="module")
def k(knowledge: MobileCoreKnowledge | None) -> MobileCoreKnowledge:
    if knowledge is None:
        pytest.skip("gbrain MCP unavailable or credentials rejected")
    return knowledge


def test_resolve_incident_id_is_domain_agnostic_and_traceable() -> None:
    knowledge = MobileCoreKnowledge(FakeResolverClient())

    resolved, trace = knowledge.resolve_incident_id("ims/incidents/voice-call-setup-05841af2e3f4f430")

    assert resolved == "incidents/ims/voice-call-setup-05841af2e3f4f430"
    assert trace[0] == "get_page:ims/incidents/voice-call-setup-05841af2e3f4f430"
    assert any(item.startswith("get_page:incidents/ims/") for item in trace)


def test_resolve_incident_id_uses_canonical_mapping_before_search() -> None:
    knowledge = MobileCoreKnowledge(FakeResolverClient())
    target = "incidents/mobile-core/sgi-data-a154bb7a3997859c"

    def call(tool: str, params: dict):
        if tool == "get_page" and params["slug"] == target:
            return {"slug": target, "type": "incident", "title": "SGi Data Forwarding Throughput Drop", "frontmatter": {}}
        if tool == "traverse_graph":
            return []
        if tool == "list_pages":
            return []
        if tool == "query":
            return {"results": []}
        return None

    knowledge.client.call = call  # type: ignore[method-assign]

    resolved, trace = knowledge.resolve_incident_id("mobile-core/incidents/sgi-throughput-drop")

    assert resolved == target
    assert f"get_page:{target}" in trace


def test_get_incident(k: MobileCoreKnowledge) -> None:
    incident = k.get_incident(AMF_INCIDENT)
    assert incident is not None
    assert incident["slug"] == AMF_INCIDENT
    assert incident["type"] == "incident"
    assert incident["frontmatter"]["severity"] == "SEV-2"
    assert incident["frontmatter"]["status"] == "resolved"
    assert "AMF-01 overload" in incident["title"]


def test_get_incident_timeline(k: MobileCoreKnowledge) -> None:
    timeline = k.get_incident_timeline(AMF_INCIDENT)
    assert len(timeline) >= 2
    joined = " ".join(f.value for f in timeline)
    assert "06:14" in joined  # detection moment present
    assert "07:05" in joined  # recovery moment present
    for f in timeline:
        assert f.slug == AMF_INCIDENT
        assert f.source is not None


def test_get_incident_kpis(k: MobileCoreKnowledge) -> None:
    kpi_events, kpis = k.get_incident_kpis(AMF_INCIDENT)
    assert len(kpi_events) == 1
    assert kpi_events[0].relationship == "detected-by"
    assert kpi_events[0].value
    assert kpis
    for kp in kpis:
        assert kp.value
        assert kp.relationship == "measures"


def test_get_network_functions(k: MobileCoreKnowledge) -> None:
    nfs = k.get_network_functions(AMF_INCIDENT)
    assert nfs
    for f in nfs:
        assert f.value
        assert f.slug
        assert f.relationship == "involves"


def test_get_services(k: MobileCoreKnowledge) -> None:
    services = k.get_services(AMF_INCIDENT)
    assert len(services) == 1
    assert services[0].value
    assert services[0].relationship == "affects"


def test_get_symptoms(k: MobileCoreKnowledge) -> None:
    symptoms = k.get_symptoms(AMF_INCIDENT)
    assert len(symptoms) >= 1
    assert symptoms[0].relationship == "has-symptom"


def test_get_hypotheses(k: MobileCoreKnowledge) -> None:
    hypotheses = k.get_hypotheses(AMF_INCIDENT)
    assert len(hypotheses) == 1
    h = hypotheses[0]
    assert h.value
    assert h.confidence is None or h.confidence > 0
    assert h.relationship == "has-hypothesis"


def test_get_evidence(k: MobileCoreKnowledge) -> None:
    hypotheses = k.get_hypotheses(AMF_INCIDENT)
    assert hypotheses and hypotheses[0].slug
    evidence = k.get_evidence(hypotheses[0].slug)
    assert evidence
    for f in evidence:
        assert f.value
        assert f.relationship == "supported-by"


def test_get_remediations(k: MobileCoreKnowledge) -> None:
    remediations = k.get_remediations(AMF_INCIDENT)
    assert len(remediations) == 1
    r = remediations[0]
    assert r.value
    assert r.relationship == "has-remediation"
    targets = r.extra.get("targets", [])
    verified = r.extra.get("verified_by", [])
    assert targets
    assert verified


def test_get_recovery(k: MobileCoreKnowledge) -> None:
    recovery = k.get_recovery(AMF_INCIDENT)
    assert len(recovery) == 1
    assert recovery[0].value
    assert recovery[0].relationship == "verified-by"


def test_find_similar_incidents(k: MobileCoreKnowledge) -> None:
    # Only one incident exists in the graph today — must not fabricate any.
    similar = k.find_similar_incidents(AMF_INCIDENT)
    for f in similar:
        assert f.slug != AMF_INCIDENT  # never self-similar


def test_search(k: MobileCoreKnowledge) -> None:
    hits = k.search("AMF-01 registration", limit=5)
    assert len(hits) >= 1
    assert hits[0].slug is not None


def test_get_incident_context_complete(k: MobileCoreKnowledge) -> None:
    ctx = k.get_incident_context(AMF_INCIDENT)
    assert ctx.incident is not None
    assert ctx.incident_id == AMF_INCIDENT
    assert ctx.network_functions
    assert ctx.services
    assert ctx.kpi_events
    assert ctx.kpis
    assert ctx.symptoms
    assert ctx.hypotheses
    assert ctx.evidence
    assert ctx.remediations
    assert ctx.recovery_events
    # Provenance preserved everywhere.
    for bucket_name in ("timeline", "services", "network_functions", "kpis",
                        "kpi_events", "symptoms", "hypotheses", "evidence",
                        "remediations", "recovery_events"):
        for f in getattr(ctx, bucket_name):
            assert f.slug is not None
            assert f.relationship is not None
