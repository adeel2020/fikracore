"""Professional incident narrative builders for TelecomBrainEngine."""

from __future__ import annotations

import re
from typing import Any

from storyteller.conversation.intents import render_spoken_answer
from storyteller.reasoning.story import IncidentStory

from ..models import (
    EvidenceClaim,
    EvidenceGrade,
    FCAPSClassification,
    IncidentLifecycleState,
    IncidentNarrative,
    NarrativeAction,
    ProvenanceRef,
    StoryAudience,
)


def narrative_from_story(
    story: IncidentStory,
    *,
    intent: str = "story",
    written_story: str = "",
    audience: StoryAudience = StoryAudience.EXECUTIVE,
) -> IncidentNarrative:
    """Convert the current deterministic IncidentStory into the new narrative contract."""
    claims = _claims_from_story(story)
    actions = _actions_from_story(story, claims)
    lifecycle_state = _lifecycle_state(story.status)
    services = [_clean_value(f.value) for f in story.services if _clean_value(f.value)]
    components = [_clean_value(f.value) for f in story.network_functions if _clean_value(f.value)]
    domains = _domains(story)
    summary = story.summary or _fallback_summary(story, services, domains)

    narrative = IncidentNarrative(
        incident_id=story.incident_id,
        audience=audience,
        lifecycle_state=lifecycle_state,
        title=_title(summary, services),
        executive_summary=summary,
        impact_summary=_impact_summary(story, services, components),
        rca_status=_rca_status(story),
        domains=domains,
        services=services,
        components=components,
        claims=claims,
        causal_chain=_causal_chain(story),
        timeline=[_timeline_item(idx, item) for idx, item in enumerate(story.timeline, start=1)],
        next_actions=actions,
        open_questions=_open_questions(story),
        written_story=written_story,
        spoken_brief=render_spoken_answer(intent, story),
        provenance=_story_provenance(story),
        metadata={
            "generated_by": story.generated_by,
            "correlation": story.correlation_metadata,
            "intent": intent,
        },
    )
    return narrative


def _claims_from_story(story: IncidentStory) -> list[EvidenceClaim]:
    claims: list[EvidenceClaim] = []
    if story.summary:
        claims.append(
            EvidenceClaim(
                id="claim-summary",
                statement=story.summary,
                grade=EvidenceGrade.INFERRED_RELATION if story.hypotheses else EvidenceGrade.WEAK_SIGNAL,
                confidence=_correlation_confidence(story),
                fcaps=[FCAPSClassification.FAULT],
                provenance=_story_provenance(story),
            )
        )
    for idx, item in enumerate(story.kpi_events or story.kpis, start=1):
        claims.append(
            EvidenceClaim(
                id=f"claim-kpi-{idx}",
                statement=_clean_value(item.value),
                grade=EvidenceGrade.CONFIRMED_FACT,
                confidence=_confidence(item, 0.8),
                fcaps=[FCAPSClassification.PERFORMANCE],
                provenance=[_provenance(item)],
            )
        )
    for idx, hyp in enumerate(story.hypotheses, start=1):
        grade = EvidenceGrade.INFERRED_RELATION
        if hyp.status == "conflicting-evidence":
            grade = EvidenceGrade.CONTRADICTION
        elif hyp.status == "insufficient-evidence":
            grade = EvidenceGrade.WEAK_SIGNAL
        claims.append(
            EvidenceClaim(
                id=f"claim-hypothesis-{idx}",
                statement=_clean_value(hyp.hypothesis.value),
                grade=grade,
                confidence=max(0.0, min(1.0, hyp.score)),
                fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
                provenance=[_provenance(hyp.hypothesis), *[_provenance(ev) for ev in hyp.evidence]],
                metadata={"status": hyp.status, "explanation": hyp.explanation},
            )
        )
        for ev_idx, evidence in enumerate(hyp.evidence, start=1):
            claims.append(
                EvidenceClaim(
                    id=f"claim-hypothesis-{idx}-evidence-{ev_idx}",
                    statement=_clean_value(evidence.value),
                    grade=EvidenceGrade.CONFIRMED_FACT,
                    confidence=_confidence(evidence, 0.75),
                    fcaps=[FCAPSClassification.FAULT],
                    provenance=[_provenance(evidence)],
                    metadata={"supports": f"claim-hypothesis-{idx}"},
                )
            )
    if not story.root_cause:
        claims.append(
            EvidenceClaim(
                id="claim-missing-root-cause",
                statement="Root cause is not confirmed yet.",
                grade=EvidenceGrade.MISSING_EVIDENCE,
                confidence=1.0,
                fcaps=[FCAPSClassification.FAULT],
            )
        )
    if not story.recovery_events:
        claims.append(
            EvidenceClaim(
                id="claim-missing-recovery",
                statement="Recovery is not recorded yet.",
                grade=EvidenceGrade.MISSING_EVIDENCE,
                confidence=1.0,
                fcaps=[FCAPSClassification.PERFORMANCE],
            )
        )
    return claims


def _actions_from_story(story: IncidentStory, claims: list[EvidenceClaim]) -> list[NarrativeAction]:
    actions: list[NarrativeAction] = []
    if not story.root_cause:
        actions.append(
            NarrativeAction(
                id="action-confirm-root-cause",
                label="Confirm the leading root-cause hypothesis with targeted telemetry and logs.",
                action_type="diagnostic",
                priority=1,
                supports_claim_ids=[claim.id for claim in claims if claim.grade == EvidenceGrade.INFERRED_RELATION][:3],
            )
        )
    if not story.recovery_events:
        actions.append(
            NarrativeAction(
                id="action-verify-recovery",
                label="Verify service recovery against KPI and customer-impact evidence.",
                action_type="verification",
                priority=2,
                supports_claim_ids=["claim-missing-recovery"],
            )
        )
    if not story.remediations:
        actions.append(
            NarrativeAction(
                id="action-record-remediation",
                label="Record mitigation or remediation actions before closure.",
                action_type="governance",
                priority=3,
                requires_approval=False,
            )
        )
    return actions


def _timeline_item(index: int, item: Any) -> dict[str, Any]:
    value = _clean_value(getattr(item, "value", str(item)))
    return {
        "id": f"timeline-{index}",
        "label": value,
        "timestamp": getattr(item, "timestamp", None),
        "provenance": _provenance(item).model_dump(exclude_none=True),
    }


def _causal_chain(story: IncidentStory) -> list[str]:
    if not story.causal_chain:
        return []
    return [_clean_value(step.label) for step in story.causal_chain.steps if _clean_value(step.label)]


def _open_questions(story: IncidentStory) -> list[str]:
    questions = list(story.unresolved_questions)
    if not story.root_cause:
        questions.append("What evidence confirms or rejects the leading root-cause hypothesis?")
    if not story.remediations:
        questions.append("Which mitigation or remediation action was taken?")
    if not story.recovery_events:
        questions.append("Has the affected service recovered according to KPIs and customer impact?")
    return questions


def _impact_summary(story: IncidentStory, services: list[str], components: list[str]) -> str:
    if story.impact:
        return "; ".join(_clean_value(item.value) for item in story.impact if _clean_value(item.value))
    service = services[0] if services else "the affected service"
    if components:
        return f"{service} impact is linked to {', '.join(components[:3])}."
    return f"{service} impact requires confirmation."


def _rca_status(story: IncidentStory) -> str:
    if story.root_cause:
        return f"Confirmed root cause: {_clean_value(story.root_cause.value)}"
    if story.hypotheses:
        return f"Leading hypothesis: {_clean_value(story.hypotheses[0].hypothesis.value)}"
    return "Root cause is not confirmed yet."


def _lifecycle_state(status: str) -> IncidentLifecycleState:
    normalized = (status or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "active": "open",
        "closed": "resolved",
        "investigating": "open",
        "investigation": "open",
        "new": "candidate",
    }
    normalized = aliases.get(normalized, normalized)
    try:
        return IncidentLifecycleState(normalized)
    except ValueError:
        return IncidentLifecycleState.UNKNOWN


def _domains(story: IncidentStory) -> list[str]:
    meta = story.correlation_metadata or {}
    domains = meta.get("contributing_domains") or []
    if isinstance(domains, list):
        return [_clean_value(str(domain)) for domain in domains if _clean_value(str(domain))]
    return []


def _story_provenance(story: IncidentStory) -> list[ProvenanceRef]:
    refs: list[ProvenanceRef] = []
    for collection in (
        story.impact,
        story.timeline,
        story.services,
        story.network_functions,
        story.kpis,
        story.kpi_events,
        story.symptoms,
        story.remediations,
        story.recovery_events,
    ):
        for item in collection:
            ref = _provenance(item)
            if ref.source or ref.slug:
                refs.append(ref)
    return refs[:20]


def _provenance(item: Any) -> ProvenanceRef:
    return ProvenanceRef(
        source=getattr(item, "source", None),
        slug=getattr(item, "slug", None),
        timestamp=getattr(item, "timestamp", None),
        relationship=getattr(item, "relationship", None),
        confidence=getattr(item, "confidence", None),
    )


def _confidence(item: Any, default: float) -> float:
    value = getattr(item, "confidence", None)
    if value is None:
        return default
    return max(0.0, min(1.0, float(value)))


def _correlation_confidence(story: IncidentStory) -> float:
    score = (story.correlation_metadata or {}).get("correlation_score")
    if score is None:
        score = (story.correlation_metadata or {}).get("score")
    if isinstance(score, (int, float)):
        return max(0.0, min(1.0, float(score) / 100.0 if score > 1 else float(score)))
    if story.hypotheses:
        return max(0.0, min(1.0, story.hypotheses[0].score))
    return 0.5


def _fallback_summary(story: IncidentStory, services: list[str], domains: list[str]) -> str:
    target = services[0] if services else "the affected service"
    if domains:
        return f"Incident affecting {target} across {', '.join(domains)}."
    return f"Incident affecting {target}."


def _title(summary: str, services: list[str]) -> str:
    if services:
        return f"{services[0]} incident narrative"
    words = summary.split()
    return " ".join(words[:8]) if words else "Incident narrative"


def _clean_value(value: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", value or "")
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"[*_#~>|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.;:-")
    return text
