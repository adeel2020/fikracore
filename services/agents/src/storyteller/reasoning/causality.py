"""Deterministic causal chain construction.

Builds the ordered chain:

    KPI degradation → symptom → hypothesis → evidence[] → root cause → recovery

using only provenance from the ``IncidentContext``. Each step is labelled with
its claim classification (FACT / OBSERVATION / CORRELATION / HYPOTHESIS /
EVIDENCE / CONFIRMED_ROOT_CAUSE) and keeps its source fact.

Rules:
  - The chain only includes the top-ranked hypothesis (the most confident
    plausible one, or the confirmed one when present).
  - If nothing supports a link (no KPI event, no symptom, no hypothesis), that
    step is simply omitted — the chain is a best-effort reconstruction, never a
    fabricated one.
  - ``root_cause`` is set only when the top hypothesis is confirmed.
"""

from __future__ import annotations

from ..knowledge.provenance import (
    CONFIRMED_ROOT_CAUSE,
    CORRELATION,
    EVIDENCE,
    FACT,
    HYPOTHESIS,
    OBSERVATION,
    ProvenanceFact,
)
from .hypothesis import CONFIRMED, HypothesisAssessment
from .story import CausalChain, CausalStep


def _top_assessment(assessments: list[HypothesisAssessment]) -> HypothesisAssessment | None:
    return assessments[0] if assessments else None


def build_causal_chain(
    kpi_events: list[ProvenanceFact],
    symptoms: list[ProvenanceFact],
    assessments: list[HypothesisAssessment],
    recovery_events: list[ProvenanceFact],
) -> CausalChain:
    """Deterministically reconstruct the causal chain from the context."""
    steps: list[CausalStep] = []

    if kpi_events:
        steps.append(CausalStep("KPI degradation", CORRELATION, kpi_events[0]))

    for symptom in symptoms:
        steps.append(CausalStep("Symptom", OBSERVATION, symptom))

    top = _top_assessment(assessments)
    if top:
        steps.append(CausalStep("Hypothesis", HYPOTHESIS, top.hypothesis))
        for ev in top.evidence:
            steps.append(CausalStep("Evidence", EVIDENCE, ev))
        if top.status == CONFIRMED:
            steps.append(CausalStep("Root cause", CONFIRMED_ROOT_CAUSE, top.hypothesis))

    for rec in recovery_events:
        steps.append(CausalStep("Recovery", FACT, rec))

    return CausalChain(steps=steps)


def resolved_root_cause(assessments: list[HypothesisAssessment]) -> ProvenanceFact | None:
    """Return the confirmed root cause if the top hypothesis is confirmed."""
    top = _top_assessment(assessments)
    if top and top.status == CONFIRMED:
        return top.hypothesis
    return None
