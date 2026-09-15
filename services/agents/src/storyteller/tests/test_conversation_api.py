"""Phase 3A tests — conversational storyteller API.

Tests use a fake knowledge layer (no gbrain) so they are fast and hermetic.
The FastAPI app is built per-test with ``dependency_overrides`` pointing at a
``ConversationService`` backed by the fake knowledge.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact
from storyteller.conversation.router import _service as conv_service_dep, router as conv_router
from storyteller.conversation.service import ConversationService
from storyteller.conversation.service import extract_incident_ref
from storyteller.conversation.session import SessionStore
from storyteller.conversation.intents import classify_intent
from storyteller.conversation.intents import render_executive, render_story
from storyteller.reasoning.pipeline import build_incident_story

AMF = "mobile-core/incidents/amf-overload-2026-08-09"
AMF_CANONICAL = "incidents/mobile-core/amf-overload-2026-08-09"


class FakeKnowledge:
    """A knowledge layer that returns a canned context for known incidents."""

    def __init__(self) -> None:
        self.contexts: dict[str, IncidentContext] = {AMF: self._amf_context(), AMF_CANONICAL: self._amf_context(AMF_CANONICAL)}

    def _amf_context(self, incident_id: str = AMF) -> IncidentContext:
        return IncidentContext(
            incident={"slug": incident_id, "frontmatter": {"severity": "SEV-2", "status": "resolved"}},
            timeline=[
                fact("2026-08-09T06:14:00Z RSR critical", relationship="timeline-entry"),
                fact("2026-08-09T07:05:00Z recovered", relationship="timeline-entry"),
            ],
            services=[fact("UE Registration Service", relationship="affects")],
            network_functions=[
                fact("AMF-01 (Access and Mobility Management Function)", relationship="involves"),
                fact("SMF-01 (Session Management Function)", relationship="involves"),
            ],
            kpis=[fact("Registration Success Rate (RSR)", relationship="measures")],
            kpi_events=[fact(
                "RSR critical breach at 06:14", relationship="detected-by",
                extra={"value": 94.7, "event_type": "alarm", "threshold": "critical"},
            )],
            symptoms=[fact("Spike in UE registration failures", relationship="has-symptom")],
            hypotheses=[fact(
                "AMF-01 CPU saturation from registration signaling burst",
                relationship="has-hypothesis",
                confidence=0.92,
                slug="mobile-core/hypotheses/amf-cpu-saturation",
                extra={"status": "confirmed", "explains": ["mobile-core/symptoms/registration-failure-spike"]},
            )],
            evidence=[
                fact("AMF-01 CPU utilization pegged at 98%", relationship="supported-by",
                     extra={"hypothesis_slug": "mobile-core/hypotheses/amf-cpu-saturation"}),
                fact("NAS REGISTRATION REJECT 'congestion' cause codes", relationship="supported-by",
                     extra={"hypothesis_slug": "mobile-core/hypotheses/amf-cpu-saturation"}),
            ],
            remediations=[fact("Scale out AMF-01 and throttle registration signaling", relationship="has-remediation")],
            recovery_events=[fact("RSR recovery at 07:05", relationship="verified-by")],
            similar_incidents=[],
        )

    def get_incident_context(self, incident_id: str) -> IncidentContext:
        return self.contexts.get(incident_id, IncidentContext())


@pytest.fixture()
def app() -> FastAPI:
    a = FastAPI()
    a.include_router(conv_router)
    svc = ConversationService(FakeKnowledge(), sessions=SessionStore())
    a.dependency_overrides[conv_service_dep] = lambda: svc
    return a


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def _ask(client: TestClient, incident: str, message: str, session_id: str | None = None, intent: str | None = None):
    body: dict = {"message": message}
    if session_id is not None:
        body["session_id"] = session_id
    if intent is not None:
        body["intent"] = intent
    return client.post(f"/api/incidents/{incident}/ask", json=body)


class TestStoryEndpoint:
    def test_story_returns_deterministic_story(self, client):
        resp = client.post(f"/api/incidents/{AMF}/story", json={})
        assert resp.status_code == 200
        body = resp.json()
        story = body["story"]
        assert story["incident_id"] == AMF
        assert story["severity"] == "SEV-2"
        assert story["status"] == "resolved"
        assert story["root_cause"] is not None

    def test_story_missing_incident_404(self, client):
        resp = client.post("/api/incidents/mobile-core/incidents/does-not-exist/story", json={})
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_story_sets_active_incident(self, client):
        client.post(f"/api/incidents/{AMF}/story", json={"session_id": "s1"})
        # Follow-up without incident in path/URL uses session context.
        resp = client.post(f"/api/incidents/{AMF}/ask", json={
            "message": "why did it happen?",
            "session_id": "s1",
        })
        assert resp.status_code == 200
        assert resp.json()["incident_id"] == AMF


class TestAskEndpoint:
    def test_ask_returns_answer_and_intent(self, client):
        resp = _ask(client, AMF, "what happened?")
        assert resp.status_code == 200
        body = resp.json()
        assert body["incident_id"] == AMF
        assert body["intent"] == "story"
        assert body["answer"]
        assert "story" in body

    def test_intent_explicit_override(self, client):
        resp = _ask(client, AMF, "tell me the root cause", intent="root_cause")
        assert resp.status_code == 200
        assert resp.json()["intent"] == "root_cause"

    def test_unknown_intent_422(self, client):
        resp = _ask(client, AMF, "hello", intent="not_a_real_intent")
        assert resp.status_code == 422
        assert "Unknown intent" in resp.json()["detail"]

    def test_ask_missing_incident_404(self, client):
        resp = _ask(client, "mobile-core/incidents/nope", "what happened?")
        assert resp.status_code == 404

    def test_ask_incident_context_required(self, client):
        # Path incident is empty, message has no ref, no session -> explicit 400.
        resp = client.post("/api/incidents//ask", json={"message": "why did it happen?"})
        assert resp.status_code == 400
        assert "incident" in resp.json()["detail"].lower()


class TestIntentClassification:
    @pytest.mark.parametrize(
        "message,expected",
        [
            ("what happened?", "story"),
            ("tell me the short version", "short"),
            ("give me the technical details", "technical"),
            ("executive summary please", "executive"),
            ("what was the root cause?", "root_cause"),
            ("show me the evidence", "evidence"),
            ("what's the timeline?", "timeline"),
            ("what remediation was applied?", "remediation"),
            ("how was it recovered?", "recovery"),
            ("any similar incidents?", "similar"),
            ("what was the impact?", "impact"),
            ("why did it happen?", "why"),
        ],
    )
    def test_classifier(self, message, expected):
        assert classify_intent(message) == expected


class TestIntentAnswers:
    def test_short(self, client):
        resp = _ask(client, AMF, "short version", intent="short")
        assert resp.json()["answer"]
        assert "resolved" in resp.json()["answer"].lower()

    def test_technical(self, client):
        resp = _ask(client, AMF, "technical", intent="technical")
        answer = resp.json()["answer"]
        assert "98%" in answer
        assert "RSR" in answer

    def test_executive(self, client):
        resp = _ask(client, AMF, "executive", intent="executive")
        assert "SEV-2" in resp.json()["answer"]
        assert "root cause" in resp.json()["answer"].lower()

    def test_root_cause_confirmed(self, client):
        resp = _ask(client, AMF, "root cause", intent="root_cause")
        assert "confirmed root cause" in resp.json()["answer"].lower()
        assert "CPU saturation" in resp.json()["answer"]

    def test_evidence(self, client):
        resp = _ask(client, AMF, "evidence", intent="evidence")
        answer = resp.json()["answer"]
        assert "98%" in answer
        assert "supported-by" in answer

    def test_timeline(self, client):
        resp = _ask(client, AMF, "timeline", intent="timeline")
        assert "06:14" in resp.json()["answer"]

    def test_remediation(self, client):
        resp = _ask(client, AMF, "remediation", intent="remediation")
        assert "Scale out AMF-01" in resp.json()["answer"]

    def test_recovery(self, client):
        resp = _ask(client, AMF, "recovery", intent="recovery")
        assert "RSR recovery" in resp.json()["answer"]

    def test_similar_no_fallback(self, client):
        # Fake knowledge returns NO similar incidents; must say so, not invent.
        resp = _ask(client, AMF, "similar", intent="similar")
        assert "no similar incidents" in resp.json()["answer"].lower()

    def test_impact(self, client):
        resp = _ask(client, AMF, "impact", intent="impact")
        assert "UE Registration Service" in resp.json()["answer"]
        assert "AMF-01" in resp.json()["answer"]

    def test_why(self, client):
        resp = _ask(client, AMF, "why", intent="why")
        answer = resp.json()["answer"]
        assert "confirmed root cause" in answer.lower()
        assert "CPU saturation" in answer

    def test_correlation_story_is_narrative_not_metadata_only(self):
        ctx = IncidentContext(
            incident={
                "slug": "mobile-core/incidents/ue-registration-1fe005ed908a3f26",
                "frontmatter": {"severity": "SEV-1", "status": "open"},
            },
            services=[fact("UE Registration", relationship="affects")],
            network_functions=[
                fact("gnodeb-17 (gnodeb, ran)", relationship="involves"),
                fact("agg-sw-03 (aggregation-switch, transport)", relationship="involves"),
            ],
            timeline=[fact("2026-08-28T10:00:00Z - Critical ran alarm", relationship="timeline-entry")],
            hypotheses=[fact(
                "Inter-domain alarm correlation impacting UE Registration",
                relationship="has-hypothesis",
                confidence=0.95,
                slug="mobile-core/hypotheses/correlation-1fe005ed908a3f26",
                extra={"status": "plausible"},
            )],
            evidence=[
                fact(
                    "Critical RAN alarm LINK_DOWN on gnodeb-17",
                    relationship="supported-by",
                    extra={"hypothesis_slug": "mobile-core/hypotheses/correlation-1fe005ed908a3f26"},
                ),
                fact(
                    "KPI breach for ue-registration",
                    relationship="supported-by",
                    extra={"hypothesis_slug": "mobile-core/hypotheses/correlation-1fe005ed908a3f26"},
                ),
            ],
            correlation_metadata={
                "correlation_score": 95,
                "correlation_scope": "inter-domain",
                "contributing_domains": ["ran", "transport"],
                "intent_status": "violated",
                "correlation_reasons": ["shared affected service", "KPI breach supports service impact"],
            },
        )
        story = build_incident_story(ctx)
        answer = render_story(story)
        executive = render_executive(story)

        assert "# Incident story" in answer
        assert "**Impact:**" in answer
        assert "**Why these alarms were grouped:**" in answer
        assert "**Supporting evidence:**" in answer
        assert "shared affected service" in answer
        assert "**Evidence:**" in executive


class TestUnresolvedRootCause:
    def test_unresolved_root_cause_no_fabrication(self, client):
        # A context where the hypothesis is NOT confirmed.
        from storyteller.knowledge.context import IncidentContext
        from storyteller.knowledge.provenance import fact

        unresolved = "mobile-core/incidents/unresolved-01"
        fake = FakeKnowledge()
        fake.contexts[unresolved] = IncidentContext(
            incident={"slug": unresolved, "frontmatter": {"severity": "SEV-3", "status": "investigating"}},
            hypotheses=[fact(
                "Possible SBC overload", relationship="has-hypothesis",
                confidence=0.5, extra={"status": "plausible"},
            )],
        )
        a = FastAPI()
        a.include_router(conv_router)
        a.dependency_overrides[conv_service_dep] = lambda: ConversationService(fake, sessions=SessionStore())
        client = TestClient(a)

        resp = _ask(client, unresolved, "root cause", intent="root_cause")
        assert resp.status_code == 200
        answer = resp.json()["answer"]
        assert "not confirmed" in answer.lower()
        assert "SBC overload" in answer
        # Must NOT claim a confirmed root cause.
        assert "confirmed root cause:" not in answer.lower()


class TestEvidenceMissing:
    def test_missing_evidence_says_so(self, client):
        from storyteller.knowledge.context import IncidentContext
        from storyteller.knowledge.provenance import fact

        no_evidence = "mobile-core/incidents/no-evidence-01"
        fake = FakeKnowledge()
        fake.contexts[no_evidence] = IncidentContext(
            incident={"slug": no_evidence, "frontmatter": {"severity": "SEV-3", "status": "open"}},
            hypotheses=[fact("Hypothesis without evidence", relationship="has-hypothesis")],
        )
        a = FastAPI()
        a.include_router(conv_router)
        a.dependency_overrides[conv_service_dep] = lambda: ConversationService(fake, sessions=SessionStore())
        client = TestClient(a)

        resp = _ask(client, no_evidence, "evidence", intent="evidence")
        assert resp.status_code == 200
        assert "no supporting evidence" in resp.json()["answer"].lower()


class TestSessionContext:
    def test_followup_uses_active_incident(self, client):
        # First turn: answer for AMF, session s-follow stores active incident.
        r1 = _ask(client, AMF, "what happened?", session_id="s-follow")
        assert r1.status_code == 200
        # Second turn: message has no incident ref, path uses a sentinel (no id),
        # so the session's active incident must be used.
        r2 = client.post("/api/incidents//ask", json={"message": "why did it happen?", "session_id": "s-follow"})
        assert r2.status_code == 200
        body = r2.json()
        assert body["incident_id"] == AMF
        assert body["intent"] == "why"

    def test_no_incident_and_no_session_returns_clear_error(self, client):
        resp = client.post("/api/incidents//ask", json={"message": "why did it happen?"})
        assert resp.status_code == 400
        detail = resp.json()["detail"].lower()
        assert "incident" in detail

    def test_message_ref_resolves_without_path(self, client):
        # Path is a sentinel but the message references the incident slug.
        resp = client.post("/api/incidents//ask", json={
            "message": "tell me about mobile-core/incidents/amf-overload-2026-08-09",
        })
        assert resp.status_code == 200
        assert resp.json()["incident_id"] == AMF

    def test_message_ref_resolves_canonical_incident_slug(self, client):
        resp = client.post("/api/incidents//ask", json={
            "message": "tell me about incidents/mobile-core/amf-overload-2026-08-09",
        })
        assert resp.status_code == 200
        assert resp.json()["incident_id"] == AMF_CANONICAL

    def test_message_ref_resolves_canonical_slug_with_trailing_punctuation(self, client):
        resp = client.post("/api/incidents//ask", json={
            "message": "Create an executive summary for incidents/mobile-core/amf-overload-2026-08-09.",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["incident_id"] == AMF_CANONICAL
        assert body["intent"] == "executive"
        assert body["spoken_answer"]
        assert body["narrative"]["audience"] == "executive"
        assert body["visual_explanation"]["widgets"]

    def test_live_telemetry_is_on_demand(self, client, monkeypatch):
        from engine_stack.engines.telecom_brain.services.grafana_evidence import GrafanaEvidenceProvider

        def fake_evidence(self, incident_id, *, query="", limit=10):
            return [
                fact(
                    "CSSR metric breach confirmed by Grafana",
                    source="grafana/query_prometheus",
                    relationship="telemetry-evidence",
                )
            ]

        monkeypatch.setattr(GrafanaEvidenceProvider, "evidence_for_incident", fake_evidence)

        default_resp = client.post("/api/incidents//ask", json={
            "message": "Create an executive summary for incidents/mobile-core/amf-overload-2026-08-09.",
        })
        live_resp = client.post("/api/incidents//ask", json={
            "message": "Create an executive summary for incidents/mobile-core/amf-overload-2026-08-09.",
            "include_live_telemetry": True,
        })

        assert default_resp.status_code == 200
        assert default_resp.json()["telemetry_evidence"] is None
        assert live_resp.status_code == 200
        assert live_resp.json()["telemetry_evidence"][0]["source"] == "grafana/query_prometheus"

    def test_extract_incident_ref_is_domain_agnostic(self):
        assert extract_incident_ref("summarize incidents/ims/voice-call-setup-123.") == "incidents/ims/voice-call-setup-123"
        assert extract_incident_ref("summarize ran/incidents/link-down-123.") == "ran/incidents/link-down-123"

    def test_no_semantic_fallback(self, client):
        # A message that mentions an UNKNOWN incident id must not silently pick
        # a similar incident; it must error with not-found.
        resp = client.post("/api/incidents//ask", json={
            "message": "what about mobile-core/incidents/unknown-99?",
        })
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestLlvmDisabled:
    def test_answer_is_deterministic_when_llm_off(self, client):
        # No STORYTELLER_* env vars -> no synthesis. Answers still generated.
        r1 = _ask(client, AMF, "what happened?")
        r2 = _ask(client, AMF, "what happened?")
        assert r1.json()["answer"] == r2.json()["answer"]
        assert r1.json()["answer"].strip() != ""
