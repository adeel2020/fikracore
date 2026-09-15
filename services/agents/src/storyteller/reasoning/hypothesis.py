"""Deterministic hypothesis assessment and ranking.

Rules (never fabricate):
  - A confirmed hypothesis (status == "confirmed", or an explicit
    ``extra["status"] == "confirmed"`` on the fact) is ranked highest and
    labeled ``confirmed``.
  - Otherwise, rank by confidence, with evidence support as a tie-breaker.
  - A hypothesis with NO confidence and NO evidence scores 0 and is labeled
    ``insufficient-evidence`` (never assigned a guessed score).
  - Conflicting evidence (explicitly negative evidence) demotes to
    ``conflicting-evidence``.

The score is deterministic and explainable: it is a function of the
hypothesis's own confidence plus a bounded bonus per piece of supporting
evidence. It never invents a status that the provenance does not support.
"""

from __future__ import annotations

from ..knowledge.provenance import ProvenanceFact
from .story import HypothesisAssessment

CONFIRMED = "confirmed"
PLAUSIBLE = "plausible"
INSUFFICIENT = "insufficient-evidence"
CONFLICTING = "conflicting-evidence"

_STATUS_LABELS = (CONFIRMED, PLAUSIBLE, INSUFFICIENT, CONFLICTING)

# Keywords that mark a piece of evidence as negative/conflicting.
_NEGATIVE_HINTS = ("not", "rejected", "ruled out", "refute", "contradicts", "fail")


def _is_confirmed(fact: ProvenanceFact) -> bool:
    raw = (fact.extra or {}).get("status")
    if isinstance(raw, str):
        return raw.strip().lower() == "confirmed"
    # Fallback: a confidence of exactly 1.0 with supporting evidence reads as
    # confirmed by the data owner.
    return bool(fact.confidence is not None and fact.confidence >= 1.0)


def _is_conflicting(evidence: ProvenanceFact) -> bool:
    value = str(evidence.value or "").lower()
    return any(hint in value for hint in _NEGATIVE_HINTS)


def _base_score(fact: ProvenanceFact) -> float:
    """Deterministic score from hypothesis confidence alone."""
    if fact.confidence is None:
        return 0.0
    # Clamp to [0, 1] then scale so confidence 1.0 -> 1.0.
    return max(0.0, min(1.0, float(fact.confidence)))


def assess_hypothesis(
    hypothesis: ProvenanceFact,
    evidence: list[ProvenanceFact],
    explains: list[ProvenanceFact],
) -> HypothesisAssessment:
    """Assess a single hypothesis. Pure function of its provenance."""
    confirmed = _is_confirmed(hypothesis)
    conflicting = [e for e in evidence if _is_conflicting(e)]
    supporting = [e for e in evidence if not _is_conflicting(e)]

    base = _base_score(hypothesis)
    bonus = min(0.2, 0.05 * len(supporting))
    score = min(1.0, base + bonus)

    if confirmed:
        status = CONFIRMED
        score = max(score, 0.9)
    elif conflicting:
        status = CONFLICTING
        score = min(score, 0.5)
    elif base == 0.0 and not supporting:
        status = INSUFFICIENT
    else:
        status = PLAUSIBLE

    explanation = _explain(status, confirmed, base, len(supporting), len(conflicting))
    return HypothesisAssessment(
        hypothesis=hypothesis,
        status=status,
        score=score,
        evidence=evidence,
        explains=explains,
        explanation=explanation,
    )


def _explain(status: str, confirmed: bool, base: float, n_support: int, n_conflict: int) -> str:
    if confirmed:
        return "confirmed status on the hypothesis page"
    if status == CONFLICTING:
        return f"{n_conflict} conflicting evidence item(s) demote this hypothesis"
    if status == INSUFFICIENT:
        return "no confidence and no supporting evidence recorded"
    parts = [f"base confidence {base:.2f}"]
    if n_support:
        parts.append(f"{n_support} supporting evidence item(s)")
    return "score = " + ", ".join(parts)


def rank_hypotheses(
    hypotheses: list[ProvenanceFact],
    evidence_by_hypothesis: dict[str, list[ProvenanceFact]],
    explains_by_hypothesis: dict[str, list[ProvenanceFact]] | None = None,
) -> list[HypothesisAssessment]:
    """Assess and sort all hypotheses, most-confident first."""
    explains_by_hypothesis = explains_by_hypothesis or {}
    assessed = [
        assess_hypothesis(
            h,
            evidence_by_hypothesis.get(h.slug, []) if h.slug else [],
            explains_by_hypothesis.get(h.slug, []) if h.slug else [],
        )
        for h in hypotheses
    ]
    # Stable sort: confirmed first, then descending score, then original order.
    return sorted(
        assessed,
        key=lambda a: (
            0 if a.status == CONFIRMED else 1,
            -a.score,
        ),
    )
