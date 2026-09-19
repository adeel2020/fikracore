"""Deterministic reasoning pipeline: IncidentContext → StoryResponse.

Layer 2 entry point. Composition:

    IncidentContext (L1)
        → rank_hypotheses (deterministic assessment + ranking)
        → build_causal_chain (deterministic KPI→…→recovery chain)
        → IncidentStory (deterministic artifact, the testable contract)
        → synthesize_narrative (OPTIONAL LLM presentation step)

Every provenance field on every fact is preserved through the story. Claim
classifications come from the shared taxonomy in ``provenance.py``.
"""

from __future__ import annotations

from typing import Any

from ..knowledge.context import IncidentContext
from . import causality, hypothesis as hyp_mod, llm as llm_mod
from .story import IncidentStory, StoryResponse


def build_incident_story(ctx: IncidentContext) -> IncidentStory:
    """Deterministically build the story artifact from an incident context."""
    if not ctx.incident:
        return IncidentStory(incident_id=ctx.incident_id or "unknown")

    # Evidence / explains indexed by hypothesis slug (provenance preserved).
    evidence_by_hyp: dict[str, list[Any]] = {}
    explains_by_hyp: dict[str, list[Any]] = {}
    for e in ctx.evidence:
        h_slug = (e.extra or {}).get("hypothesis_slug")
        if h_slug:
            evidence_by_hyp.setdefault(h_slug, []).append(e)
    for h in ctx.hypotheses:
        explains = (h.extra or {}).get("explains", [])
        if h.slug and explains:
            explains_by_hyp[h.slug] = [
                f for f in ctx.symptoms if f.slug in explains
            ]

    assessments = hyp_mod.rank_hypotheses(
        ctx.hypotheses, evidence_by_hyp, explains_by_hyp
    )
    chain = causality.build_causal_chain(
        ctx.kpi_events, ctx.symptoms, assessments, ctx.recovery_events
    )
    root = causality.resolved_root_cause(assessments)

    incident = ctx.incident
    severity = (incident.get("frontmatter", {}) or {}).get("severity", "")
    status = (incident.get("frontmatter", {}) or {}).get("status", "")

    unresolved = _unresolved_questions(ctx, assessments, root)

    summary = _summary(ctx, root, assessments)

    return IncidentStory(
        incident_id=ctx.incident_id or "unknown",
        summary=summary,
        severity=str(severity),
        status=str(status),
        impact=ctx.services + ctx.network_functions,
        timeline=ctx.timeline,
        services=ctx.services,
        network_functions=ctx.network_functions,
        kpis=ctx.kpis,
        kpi_events=ctx.kpi_events,
        symptoms=ctx.symptoms,
        hypotheses=assessments,
        causal_chain=chain,
        root_cause=root,
        remediations=ctx.remediations,
        recovery_events=ctx.recovery_events,
        similar_incidents=ctx.similar_incidents,
        correlation_metadata=ctx.correlation_metadata,
        unresolved_questions=unresolved,
        generated_by="deterministic",
    )


def build_story_response(ctx: IncidentContext, *, synthesize: bool = True) -> StoryResponse:
    """Deterministic story + optional LLM narrative."""
    story = build_incident_story(ctx)
    narrative: str = ""
    model: str | None = None
    synthesized = False
    if synthesize:
        narrative, model = llm_mod.synthesize_narrative(story)
        synthesized = bool(narrative)
    return StoryResponse(story=story, narrative=narrative, synthesized=synthesized, model=model)


def _summary(
    ctx: IncidentContext,
    root: Any,
    assessments: list[Any],
) -> str:
    """Deterministic, professional executive summary; only uses present facts."""
    incident = ctx.incident or {}
    fm = incident.get("frontmatter", {}) or {}
    severity = fm.get("severity") or "SEV-UNKNOWN"
    status = fm.get("status") or "active"
    correlation = ctx.correlation_metadata or {}

    services = ", ".join(str(s.value) for s in ctx.services[:2]) or "affected telecom services"

    if root is not None:
        cause_str = f"confirmed root cause: {root.value}"
    elif assessments and assessments[0].status != hyp_mod.CONFIRMED:
        cause_str = f"leading hypothesis: {assessments[0].hypothesis.value}"
    elif assessments:
        cause_str = f"leading hypothesis: {assessments[0].hypothesis.value}"
    else:
        cause_str = "root cause under investigation"

    if correlation:
        scope = correlation.get("correlation_scope") or "correlated"
        domains = correlation.get("contributing_domains") or []
        domain_phrase = f" across {', '.join(str(d) for d in domains)}" if domains else ""
        score = correlation.get("correlation_score")
        score_phrase = f" (correlation score: {score})" if score is not None else ""

        return (
            f"A {severity} {status} incident with {scope} scope{score_phrase} impacted {services}{domain_phrase}. "
            f"Investigation {cause_str}."
        )

    parts: list[str] = []
    if fm.get("severity"):
        parts.append(f"severity {fm['severity']}")
    if root is not None:
        parts.append(f"root cause: {root.value}")
    elif assessments and assessments[0].status != hyp_mod.CONFIRMED:
        top = assessments[0].hypothesis.value
        parts.append(f"leading hypothesis: {top}")
    if ctx.services:
        parts.append("affected service: " + ", ".join(str(s.value) for s in ctx.services[:2]))
    if ctx.remediations:
        parts.append(f"{len(ctx.remediations)} remediation(s) applied")
    if ctx.recovery_events:
        parts.append("recovery observed")
    if not parts:
        return f"incident {ctx.incident_id or 'unknown'}: no confirming facts yet"
    return f"incident {ctx.incident_id or 'unknown'} — " + ", ".join(parts)


def _unresolved_questions(
    ctx: IncidentContext,
    assessments: list[Any],
    root: Any,
) -> list[str]:
    """Questions that remain unanswered, based on missing provenance."""
    questions: list[str] = []
    if root is None and assessments:
        questions.append("root cause is not confirmed")
    if not ctx.remediations:
        questions.append("no remediation recorded")
    if not ctx.recovery_events:
        questions.append("no recovery observed")
    if not ctx.similar_incidents:
        questions.append("no similar incidents found to corroborate the story")
    return questions
