"""Phase 15 end-to-end validation matrix for professional storytelling.

These tests are hermetic synthetic incidents. They exercise the production
chain without requiring live gbrain/Grafana:

IncidentContext -> IncidentStory -> audience renderer -> spoken brief ->
IncidentNarrative -> VisualExplanation.
"""

from __future__ import annotations

import pytest

from engine_stack.engines.telecom_brain.models import (
    EvidenceGrade,
    IncidentLifecycleState,
    StoryAudience,
    VisualWidgetType,
)
from engine_stack.engines.telecom_brain.services.narrative import narrative_from_story
from engine_stack.engines.telecom_brain.services.visual_explanation import VisualExplanationService
from storyteller.conversation.intents import render_answer, render_spoken_answer
from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact
from storyteller.reasoning.pipeline import build_incident_story


def _incident(
    slug: str,
    *,
    status: str,
    severity: str,
    service: str,
    domains: list[str],
    components: list[str],
    hypothesis: str = "Shared service degradation is the leading cause",
    confidence: float | None = 0.82,
    evidence: list[str] | None = None,
    contradictory_evidence: list[str] | None = None,
    remediation: str | None = None,
    recovery: str | None = None,
    timeline: list[str] | None = None,
) -> IncidentContext:
    hypothesis_slug = f"{slug}/hypothesis/main"
    all_evidence = [
        fact(item, relationship="supported-by", extra={"hypothesis_slug": hypothesis_slug})
        for item in (evidence or [])
    ] + [
        fact(item, relationship="supported-by", extra={"hypothesis_slug": hypothesis_slug})
        for item in (contradictory_evidence or [])
    ]
    return IncidentContext(
        incident={"slug": slug, "frontmatter": {"severity": severity, "status": status}},
        services=[fact(service, relationship="affects", slug=f"{slug}/service")],
        network_functions=[
            fact(component, relationship="involves", slug=f"{slug}/component/{idx}")
            for idx, component in enumerate(components, start=1)
        ],
        kpis=[fact(f"{service} success rate", relationship="measures", slug=f"{slug}/kpi")],
        kpi_events=[
            fact(
                f"{service} KPI breached",
                relationship="detected-by",
                extra={"value": 91.2, "event_type": "breach", "threshold": "critical"},
                slug=f"{slug}/kpi-event",
            )
        ],
        symptoms=[fact(f"{service} degradation observed", relationship="has-symptom", slug=f"{slug}/symptom")],
        hypotheses=[
            fact(
                hypothesis,
                relationship="has-hypothesis",
                confidence=confidence,
                slug=hypothesis_slug,
                extra={"status": "confirmed" if status == "resolved" and recovery else "plausible"},
            )
        ],
        evidence=all_evidence,
        timeline=[
            fact(item, relationship="timeline-entry", slug=slug)
            for item in (timeline or [f"{service} alarm detected", f"{service} KPI breach confirmed"])
        ],
        remediations=[fact(remediation, relationship="has-remediation")] if remediation else [],
        recovery_events=[fact(recovery, relationship="verified-by")] if recovery else [],
        correlation_metadata={
            "correlation_scope": "inter-domain" if len(domains) > 1 else "intra-domain",
            "contributing_domains": domains,
            "correlation_score": 93 if len(domains) > 1 else 78,
            "intent_status": "violated",
            "correlation_reasons": ["shared affected service", "KPI breach supports service impact"],
        },
    )


def _contract(ctx: IncidentContext, *, intent: str = "executive", audience: StoryAudience = StoryAudience.EXECUTIVE):
    story = build_incident_story(ctx)
    written = render_answer(intent, story)
    spoken = render_spoken_answer(intent, story)
    narrative = narrative_from_story(story, intent=intent, written_story=written, audience=audience)
    visual = VisualExplanationService().build(narrative)
    return story, written, spoken, narrative, visual


@pytest.mark.parametrize(
    "name,ctx",
    [
        (
            "intra-domain mobile core",
            _incident(
                "incidents/mobile-core/amf-cpu-intra-001",
                status="open",
                severity="SEV-2",
                service="UE Registration",
                domains=["mobile-core"],
                components=["AMF-01", "SMF-01"],
                hypothesis="AMF CPU pressure is degrading UE Registration",
                evidence=["AMF CPU stayed above threshold", "Registration rejects increased"],
            ),
        ),
        (
            "inter-domain RAN transport core",
            _incident(
                "incidents/mobile-core/attach-inter-001",
                status="acknowledged",
                severity="SEV-1",
                service="LTE Attach",
                domains=["ran", "transport", "mobile-core"],
                components=["eNodeB-17", "Aggregation-SW-03", "MME-01"],
                hypothesis="RAN access drops and transport loss are degrading LTE Attach",
                evidence=["S1AP initial UE message drops increased", "Transport packet loss rose", "MME attach rejects increased"],
            ),
        ),
        (
            "IMS voice setup",
            _incident(
                "incidents/ims/voice-call-setup-001",
                status="mitigated",
                severity="SEV-2",
                service="Voice Call Setup",
                domains=["ims", "mobile-core"],
                components=["P-CSCF-01", "S-CSCF-02", "HSS-01"],
                hypothesis="IMS registration instability is delaying voice call setup",
                evidence=["SIP 408 responses increased", "Diameter latency rose for subscriber lookup"],
                remediation="Shifted voice registration traffic to standby CSCF pool",
            ),
        ),
        (
            "cloud platform",
            _incident(
                "incidents/cloud/upf-platform-001",
                status="reopened",
                severity="SEV-1",
                service="SGi Data",
                domains=["cloud", "mobile-core"],
                components=["UPF-CNF-02", "Kubernetes Node Pool B"],
                hypothesis="Cloud node pressure is impacting UPF data forwarding",
                evidence=["UPF pod restarts increased", "Node packet drops exceeded baseline"],
            ),
        ),
        (
            "power site",
            _incident(
                "incidents/power/site-power-001",
                status="resolved",
                severity="SEV-2",
                service="Site Availability",
                domains=["power", "ran"],
                components=["Site-DXB-1023", "eNodeB-1023"],
                hypothesis="Power rectifier failure caused site availability loss",
                evidence=["Rectifier alarm active", "Battery discharge crossed threshold"],
                remediation="Replaced failed rectifier and restored mains feed",
                recovery="Site availability recovered above SLA",
            ),
        ),
        (
            "customer weak signal",
            _incident(
                "incidents/customer/complaints-weak-001",
                status="candidate",
                severity="SEV-3",
                service="Customer Data Experience",
                domains=["customer-impact"],
                components=["Complaint Cluster Dubai"],
                hypothesis="Customer complaints may indicate localized data degradation",
                confidence=None,
                evidence=[],
            ),
        ),
    ],
)
def test_phase15_storytelling_matrix(name: str, ctx: IncidentContext) -> None:
    story, written, spoken, narrative, visual = _contract(ctx)

    assert story.incident_id == ctx.incident["slug"], name
    assert written
    assert spoken
    assert narrative.incident_id == story.incident_id
    assert narrative.services
    assert narrative.claims
    assert visual.widgets
    assert {widget.type for widget in visual.widgets} >= {
        VisualWidgetType.DOMAIN_IMPACT_MAP,
        VisualWidgetType.EVIDENCE_CONFIDENCE_MATRIX,
        VisualWidgetType.TIMELINE,
        VisualWidgetType.CAUSAL_CHAIN,
        VisualWidgetType.NEXT_ACTION_TREE,
    }
    assert "incidents/" not in spoken
    assert "mobile-core/incidents" not in spoken
    assert "**" not in spoken
    assert "|" not in spoken


@pytest.mark.parametrize(
    "status,expected",
    [
        ("candidate", IncidentLifecycleState.CANDIDATE),
        ("open", IncidentLifecycleState.OPEN),
        ("acknowledged", IncidentLifecycleState.ACKNOWLEDGED),
        ("mitigated", IncidentLifecycleState.MITIGATED),
        ("resolved", IncidentLifecycleState.RESOLVED),
        ("reopened", IncidentLifecycleState.REOPENED),
        ("merged", IncidentLifecycleState.MERGED),
        ("suppressed", IncidentLifecycleState.SUPPRESSED),
        ("investigating", IncidentLifecycleState.OPEN),
    ],
)
def test_phase15_lifecycle_states_are_mapped(status: str, expected: IncidentLifecycleState) -> None:
    _, _, _, narrative, _ = _contract(
        _incident(
            f"incidents/mobile-core/lifecycle-{status}",
            status=status,
            severity="SEV-3",
            service="UE Registration",
            domains=["mobile-core"],
            components=["AMF-01"],
            evidence=["Alarm evidence is present"],
        )
    )

    assert narrative.lifecycle_state == expected


def test_phase15_contradiction_and_missing_evidence_are_visible() -> None:
    _, written, spoken, narrative, visual = _contract(
        _incident(
            "incidents/mobile-core/contradiction-001",
            status="open",
            severity="SEV-2",
            service="UE Registration",
            domains=["mobile-core"],
            components=["AMF-01"],
            hypothesis="AMF CPU saturation is causing registration failures",
            evidence=["AMF CPU pressure observed"],
            contradictory_evidence=["Packet capture contradicts AMF CPU saturation as primary cause"],
        )
    )

    grades = {claim.grade for claim in narrative.claims}
    assert EvidenceGrade.CONTRADICTION in grades
    assert EvidenceGrade.MISSING_EVIDENCE in grades
    assert "root cause" in written.lower()
    assert "root cause confirmation" in spoken.lower()
    evidence_widget = next(widget for widget in visual.widgets if widget.type == VisualWidgetType.EVIDENCE_CONFIDENCE_MATRIX)
    assert evidence_widget.data["grade_counts"][EvidenceGrade.CONTRADICTION.value] >= 1
    assert evidence_widget.data["grade_counts"][EvidenceGrade.MISSING_EVIDENCE.value] >= 1


def test_phase15_customer_update_avoids_internal_technical_detail() -> None:
    story, written, spoken, narrative, _ = _contract(
        _incident(
            "incidents/ims/voice-call-customer-001",
            status="mitigated",
            severity="SEV-2",
            service="Voice Call Setup",
            domains=["ims"],
            components=["P-CSCF-01", "S-CSCF-01"],
            hypothesis="SIP registration timeout is delaying call setup",
            evidence=["SIP 408 responses increased"],
            remediation="Rerouted call setup traffic through healthy IMS pool",
        ),
        intent="customer_update",
        audience=StoryAudience.CUSTOMER,
    )

    assert story.incident_id
    assert narrative.audience == StoryAudience.CUSTOMER
    assert "P-CSCF" not in written
    assert "S-CSCF" not in written
    assert "incidents/" not in spoken
