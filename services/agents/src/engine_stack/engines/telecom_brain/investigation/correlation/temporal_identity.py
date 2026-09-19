"""Phase 2.1: Temporal & Identity Correlation.

Canonical slug normalization, timestamp alignment, freshness decay, and deduplication/event collapse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..contracts import Evidence
from ..evidence import collapse, reject_truth
from ..knowledge import CanonicalKnowledge


@dataclass
class TemporalIdentityResult:
    """Output of Phase 2.1 temporal and identity correlation."""
    events: list[Evidence]
    raw_count: int
    normalized_count: int
    collapsed_count: int
    sources: dict[str, int] = field(default_factory=dict)
    types: dict[str, int] = field(default_factory=dict)
    time_span: float = 0.0
    avg_freshness: float = 0.0
    max_age_hours: float = 0.0
    min_time: str = ""
    max_time: str = ""


def normalize_evidence(
    evidence: list[Evidence],
    knowledge: CanonicalKnowledge,
) -> TemporalIdentityResult:
    """Normalize, canonicalize, apply freshness decay, and collapse duplicate evidence.

    This implements Phase 2.1 of the Correlation Engine:
    - Canonical slug resolution via knowledge provider
    - Freshness time decay based on event age
    - Deduplication via evidence collapse
    - Source and type aggregation for display
    """
    raw_count = len(evidence)
    observation_time = max((item.ingestion_time for item in evidence), default=None)

    normalized = []
    for item in evidence:
        reject_truth(item.model_dump(mode="json"))
        canonical = knowledge.resolve_entity(item.canonical_entity, item.source_native_entity)
        age_hours = max(0, (observation_time - item.event_time).total_seconds() / 3600) if observation_time else 0
        normalized.append(item.model_copy(update={
            "canonical_entity": canonical,
            "freshness": item.freshness / (1 + age_hours),
            "observed_path": [knowledge.canonical(entity) for entity in item.observed_path],
        }))

    events = collapse(normalized)

    # Aggregate sources and types for display
    sources: dict[str, int] = {}
    types: dict[str, int] = {}
    for item in evidence:
        sources[item.source] = sources.get(item.source, 0) + 1
        types[item.evidence_type] = types.get(item.evidence_type, 0) + 1

    # Compute time window
    event_times = [item.event_time for item in evidence if item.event_time]
    if event_times:
        min_t = min(event_times)
        max_t = max(event_times)
        time_span = (max_t - min_t).total_seconds()
        max_age_hours = max(0, (observation_time - min_t).total_seconds() / 3600) if observation_time else 0
        min_time_str = min_t.strftime("%H:%M:%S")
        max_time_str = max_t.strftime("%H:%M:%S")
    else:
        time_span = 0.0
        max_age_hours = 0.0
        min_time_str = ""
        max_time_str = ""

    # Average freshness
    avg_freshness = sum(e.freshness for e in events) / max(1, len(events))

    return TemporalIdentityResult(
        events=events,
        raw_count=raw_count,
        normalized_count=len(normalized),
        collapsed_count=len(events),
        sources=sources,
        types=types,
        time_span=time_span,
        avg_freshness=avg_freshness,
        max_age_hours=max_age_hours,
        min_time=min_time_str,
        max_time=max_time_str,
    )
