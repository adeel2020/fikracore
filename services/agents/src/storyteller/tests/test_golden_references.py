"""Golden regression tests for the professional storyteller contract."""

from __future__ import annotations

import json
from pathlib import Path

from engine_stack.engines.telecom_brain.models import StoryAudience
from engine_stack.engines.telecom_brain.services.narrative import narrative_from_story
from engine_stack.engines.telecom_brain.services.visual_explanation import VisualExplanationService
from storyteller.conversation.intents import render_answer, render_spoken_answer
from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact
from storyteller.reasoning.pipeline import build_incident_story

AMF_INCIDENT = "mobile-core/incidents/amf-overload-2026-08-09"
GOLDEN_ROOT = Path(__file__).resolve().parents[5] / "docs" / "storyteller-references" / "golden" / "amf-overload"


def _golden_context() -> IncidentContext:
    return IncidentContext(
        incident={"slug": AMF_INCIDENT, "frontmatter": {"severity": "SEV-2", "status": "resolved"}},
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
        kpi_events=[
            fact(
                "RSR critical breach at 06:14",
                relationship="detected-by",
                extra={"value": 94.7, "event_type": "alarm", "threshold": "critical"},
            )
        ],
        symptoms=[fact("Spike in UE registration failures", relationship="has-symptom")],
        hypotheses=[
            fact(
                "AMF-01 CPU saturation from registration signaling burst",
                relationship="has-hypothesis",
                confidence=0.92,
                slug="mobile-core/hypotheses/amf-cpu-saturation",
                extra={"status": "confirmed", "explains": ["mobile-core/symptoms/registration-failure-spike"]},
            )
        ],
        evidence=[
            fact(
                "AMF-01 CPU utilization pegged at 98%",
                relationship="supported-by",
                extra={"hypothesis_slug": "mobile-core/hypotheses/amf-cpu-saturation"},
            ),
            fact(
                "NAS REGISTRATION REJECT 'congestion' cause codes",
                relationship="supported-by",
                extra={"hypothesis_slug": "mobile-core/hypotheses/amf-cpu-saturation"},
            ),
        ],
        remediations=[fact("Scale out AMF-01 and throttle registration signaling", relationship="has-remediation")],
        recovery_events=[fact("RSR recovery at 07:05", relationship="verified-by")],
        similar_incidents=[],
    )


def _story():
    return build_incident_story(_golden_context())


def _read_golden(name: str) -> str:
    return (GOLDEN_ROOT / name).read_text(encoding="utf-8").strip()


def test_golden_executive_story_is_stable() -> None:
    assert render_answer("executive", _story()).strip() == _read_golden("executive.md")


def test_golden_noc_brief_is_stable() -> None:
    assert render_answer("noc_brief", _story()).strip() == _read_golden("noc_brief.md")


def test_golden_customer_update_is_stable() -> None:
    assert render_answer("customer_update", _story()).strip() == _read_golden("customer_update.md")


def test_golden_spoken_brief_is_voice_safe() -> None:
    spoken = render_spoken_answer("executive", _story()).strip()

    assert spoken == _read_golden("spoken.txt")
    assert AMF_INCIDENT not in spoken
    assert "mobile-core/incidents" not in spoken
    assert "**" not in spoken
    assert "|" not in spoken
    assert "2026-08-09T" not in spoken


def test_golden_visual_contract_is_stable() -> None:
    story = _story()
    written = render_answer("executive", story)
    narrative = narrative_from_story(story, intent="executive", written_story=written, audience=StoryAudience.EXECUTIVE)
    visual = VisualExplanationService().build(narrative)
    expected = json.loads((GOLDEN_ROOT / "visual_contract.json").read_text(encoding="utf-8"))

    assert visual.incident_id == expected["incident_id"]
    assert visual.audience.value == expected["audience"]
    assert visual.primary_widget and visual.primary_widget.value == expected["primary_widget"]
    assert set(widget.type.value for widget in visual.widgets) >= set(expected["required_widget_types"])
    assert visual.metadata["presentation_modes"] == expected["presentation_modes"]

    evidence_widget = next(widget for widget in visual.widgets if widget.type.value == "evidence_confidence_matrix")
    assert evidence_widget.data["grade_counts"]["confirmed_fact"] == expected["claim_grades"]["confirmed_fact"]
    assert evidence_widget.data["grade_counts"]["inferred_relation"] == expected["claim_grades"]["inferred_relation"]
    assert evidence_widget.data["grade_counts"]["missing_evidence"] == expected["claim_grades"]["missing_evidence"]
