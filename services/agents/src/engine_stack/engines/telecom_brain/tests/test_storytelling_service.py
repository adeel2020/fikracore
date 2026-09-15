from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine_stack.engines.telecom_brain.engine_context import create_default_context
from engine_stack.engines.telecom_brain.models import (
    EvidenceGrade,
    IncidentNarrative,
    TelecomRequest,
    VisualWidgetType,
)
from engine_stack.engines.telecom_brain.services.storytelling import StorytellingService
from engine_stack.engines.telecom_brain.services.visual_explanation import VisualExplanationService
from storyteller.knowledge.provenance import fact
from storyteller.reasoning.story import IncidentStory


@dataclass
class FakeStory:
    incident_id: str = "incidents/mobile-core/amf-overload"

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "summary": "AMF overload reduced registration success.",
            "status": "open",
            "severity": "critical",
        }


class FakeConversation:
    def ask(self, *, path_incident_id, message, session_id=None, intent=None):
        return FakeStory(), "story", "AMF overload reduced registration success.", "incidents/mobile-core/amf-overload"


class FakeStructuredConversation:
    def ask(self, *, path_incident_id, message, session_id=None, intent=None):
        story = IncidentStory(
            incident_id="incidents/mobile-core/ue-registration-1fe005ed908a3f26",
            summary="inter-domain correlation impacting UE Registration across mobile-core, ran, transport",
            status="open",
            severity="SEV-1",
            services=[fact("UE Registration", relationship="affects")],
            network_functions=[
                fact("core-amf-01", relationship="involves"),
                fact("ran-gnodeb-17", relationship="involves"),
                fact("transport-agg-sw-03", relationship="involves"),
            ],
            timeline=[
                fact("2026-08-28T10:00:00+00:00 Critical ran alarm LINK_DOWN", relationship="timeline-entry"),
                fact("2026-08-28T10:05:00+00:00 KPI breach for ue-registration", relationship="timeline-entry"),
            ],
            correlation_metadata={
                "correlation_scope": "inter-domain",
                "contributing_domains": ["mobile-core", "ran", "transport"],
            },
        )
        answer = (
            "# Incident story — incidents/mobile-core/ue-registration-1fe005ed908a3f26\n\n"
            "**Status:** open  **Severity:** SEV-1\n\n"
            "| Field | Value |\n| --- | --- |\n| incident_id | incidents/mobile-core/ue-registration-1fe005ed908a3f26 |\n"
        )
        return story, "story", answer, story.incident_id


@pytest.mark.anyio
async def test_storytelling_service_wraps_existing_conversation_service() -> None:
    service = StorytellingService(conversation=FakeConversation())
    request = TelecomRequest(
        query="tell the story for incidents/mobile-core/amf-overload",
        session_id="s1",
    )

    result = await service.handle(request, create_default_context())

    assert result.text == "AMF overload reduced registration success."
    assert result.incidents[0].id == "incidents/mobile-core/amf-overload"
    assert "storyteller.ConversationService" in result.trace.provenance


@pytest.mark.anyio
async def test_storytelling_service_separates_full_text_from_spoken_summary() -> None:
    service = StorytellingService(conversation=FakeStructuredConversation())
    request = TelecomRequest(
        query="tell the story for incidents/mobile-core/ue-registration-1fe005ed908a3f26",
        session_id="s1",
    )

    result = await service.handle(request, create_default_context())

    assert result.text.startswith("# Incident story")
    assert "| incident_id |" in result.text
    assert result.spoken_response
    assert "UE Registration" in result.spoken_response
    assert "incidents/mobile-core" not in result.spoken_response
    assert "**" not in result.spoken_response
    assert "|" not in result.spoken_response


@pytest.mark.anyio
async def test_storytelling_service_returns_narrative_and_visual_payloads() -> None:
    service = StorytellingService(conversation=FakeStructuredConversation())

    result = await service.handle(
        TelecomRequest(query="create an executive summary for incidents/mobile-core/ue-registration-1fe005ed908a3f26"),
        create_default_context(),
    )

    narrative = result.data["narrative"]
    visual = result.data["visual_explanation"]

    assert narrative["incident_id"] == "incidents/mobile-core/ue-registration-1fe005ed908a3f26"
    assert narrative["lifecycle_state"] == "open"
    assert narrative["audience"] == "executive"
    assert narrative["services"] == ["UE Registration"]
    assert any(claim["grade"] == EvidenceGrade.MISSING_EVIDENCE.value for claim in narrative["claims"])
    assert visual["incident_id"] == narrative["incident_id"]
    assert {widget["type"] for widget in visual["widgets"]} >= {
        VisualWidgetType.DOMAIN_IMPACT_MAP.value,
        VisualWidgetType.EVIDENCE_CONFIDENCE_MATRIX.value,
        VisualWidgetType.TIMELINE.value,
        VisualWidgetType.NEXT_ACTION_TREE.value,
    }


@pytest.mark.anyio
async def test_storytelling_service_adds_live_telemetry_only_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    from engine_stack.engines.telecom_brain.services.grafana_evidence import GrafanaEvidenceProvider

    def fake_evidence(self, incident_id, *, query="", limit=10):
        return [fact("Live Grafana CSSR evidence", source="grafana/query_prometheus")]

    monkeypatch.setattr(GrafanaEvidenceProvider, "evidence_for_incident", fake_evidence)
    service = StorytellingService(conversation=FakeStructuredConversation())

    default_result = await service.handle(
        TelecomRequest(query="tell the story for incidents/mobile-core/ue-registration-1fe005ed908a3f26"),
        create_default_context(),
    )
    live_result = await service.handle(
        TelecomRequest(
            query="tell the story for incidents/mobile-core/ue-registration-1fe005ed908a3f26",
            context={"include_live_telemetry": True},
        ),
        create_default_context(),
    )

    assert default_result.data["telemetry_evidence"] == []
    assert live_result.data["telemetry_evidence"][0]["source"] == "grafana/query_prometheus"


@pytest.mark.anyio
async def test_visual_explanation_widgets_trace_back_to_claims() -> None:
    result = await StorytellingService(conversation=FakeStructuredConversation()).handle(
        TelecomRequest(query="tell the story for incidents/mobile-core/ue-registration-1fe005ed908a3f26"),
        create_default_context(),
    )
    visual = VisualExplanationService().build(
        # Rehydrate only the contract fields needed by the service path under test.
        IncidentNarrative(**result.data["narrative"])
    )

    evidence_widget = next(widget for widget in visual.widgets if widget.type == VisualWidgetType.EVIDENCE_CONFIDENCE_MATRIX)
    assert evidence_widget.supports_claim_ids
    assert evidence_widget.confidence > 0


@pytest.mark.anyio
async def test_storytelling_confidence_prefers_incident_story_queries() -> None:
    confidence = await StorytellingService(conversation=FakeConversation()).can_handle(
        TelecomRequest(query="tell the incident story for incidents/mobile-core/amf-overload")
    )

    assert confidence >= 0.8
