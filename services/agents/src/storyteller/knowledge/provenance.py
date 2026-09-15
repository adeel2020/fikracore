"""Provenance metadata for facts retrieved from gbrain (spec §5).

Every fact passed to the reasoning layer MUST wrap its provenance so the
final story can attribute its claims back to specific graph pages, source
systems, or telemetry events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Claim types used for provenance classification (§5)
FACT = "fact"
OBSERVATION = "observation"
HYPOTHESIS = "hypothesis"
EVIDENCE = "evidence"
CORRELATION = "correlation"
CONFIRMED_ROOT_CAUSE = "confirmed-root-cause"

CLAIM_TYPES = (
    FACT,
    OBSERVATION,
    HYPOTHESIS,
    EVIDENCE,
    CORRELATION,
    CONFIRMED_ROOT_CAUSE,
)


@dataclass(frozen=True)
class ProvenanceFact:
    """A fact retrieved from gbrain, wrapped with provenance metadata.

    Attributes:
        value: Human-readable claim or raw payload string.
        source: Provenance URI / source identifier (e.g. "gbrain/mobile-core/...").
        timestamp: When the fact was recorded / observed, if known (ISO-8601 string).
        confidence: Confidence score in [0.0, 1.0], if the source provided one.
        relationship: Link type by which this fact was reached (e.g. "detected-by").
        slug: The gbrain page slug the fact originates from, if applicable.
        extra: Freeform dictionary of additional raw fields from the page.
    """

    value: str
    source: str | None = None
    timestamp: str | None = None
    confidence: float | None = None
    relationship: str | None = None
    slug: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        out: dict[str, Any] = {"value": self.value}
        if self.source is not None:
            out["source"] = self.source
        if self.timestamp is not None:
            out["timestamp"] = self.timestamp
        if self.confidence is not None:
            out["confidence"] = self.confidence
        if self.relationship is not None:
            out["relationship"] = self.relationship
        if self.slug is not None:
            out["slug"] = self.slug
        if self.extra:
            out["extra"] = self.extra
        return out


def fact(
    value: str,
    *,
    source: str | None = None,
    timestamp: str | None = None,
    confidence: float | None = None,
    relationship: str | None = None,
    slug: str | None = None,
    extra: dict[str, Any] | None = None,
) -> ProvenanceFact:
    """Convenience constructor for a provenance-wrapped fact."""
    return ProvenanceFact(
        value=value,
        source=source,
        timestamp=timestamp,
        confidence=confidence,
        relationship=relationship,
        slug=slug,
        extra=extra or {},
    )


def _frontmatter_field(page: dict[str, Any] | None, key: str) -> Any | None:
    if not isinstance(page, dict):
        return None
    fm = page.get("frontmatter")
    if not isinstance(fm, dict):
        return None
    return fm.get(key)


def provenance_from_page(page: dict[str, Any] | None, relationship: str | None = None) -> dict[str, Any]:
    """Extract common provenance fields from a gbrain page dict."""
    if not isinstance(page, dict):
        return {
            "source": "gbrain/embedded",
            "timestamp": None,
            "confidence": None,
            "relationship": relationship,
            "slug": None,
        }
    source = _frontmatter_field(page, "source") or page.get("source_uri") or page.get("source_kind") or "gbrain"
    timestamp = (
        _frontmatter_field(page, "observed_at")
        or _frontmatter_field(page, "collected_at")
        or _frontmatter_field(page, "proposed_at")
        or _frontmatter_field(page, "started_at")
        or page.get("updated_at")
    )
    conf = _frontmatter_field(page, "confidence")
    try:
        confidence = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        confidence = None
    return {
        "source": source,
        "timestamp": timestamp,
        "confidence": confidence,
        "relationship": relationship,
        "slug": page.get("slug"),
    }
