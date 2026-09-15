"""Backward-compatible canonical slug resolver for telecombrain.

The resolver is intentionally data-driven: exact legacy-to-canonical mappings
live in ``mappings.json`` and can be audited independently of application code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from correlation.namespaces import canonicalize_incident_slug, incident_aliases


@dataclass(frozen=True)
class ResolutionResult:
    requested_slug: str
    resolved_slug: str
    candidates: tuple[str, ...]
    trace: tuple[str, ...]
    source: str


class CanonicalResolver:
    """Resolve legacy telecombrain slugs to canonical slugs without mutation."""

    def __init__(self, mappings: Iterable[dict[str, object]]) -> None:
        self._mapping_records = [dict(item) for item in mappings]
        self._aliases = {
            str(item["legacy_slug"]): str(item["canonical_slug"])
            for item in self._mapping_records
            if item.get("action") == "alias" and item.get("legacy_slug") and item.get("canonical_slug")
        }
        self._validate_no_cycles()

    @property
    def mapping_records(self) -> list[dict[str, object]]:
        return [dict(item) for item in self._mapping_records]

    def canonical_slug(self, slug: str) -> str:
        seen: set[str] = set()
        current = slug
        while current in self._aliases:
            if current in seen:
                raise ValueError(f"canonical alias cycle detected at {current}")
            seen.add(current)
            current = self._aliases[current]
        return canonicalize_incident_slug(current)

    def candidates(self, slug: str) -> list[str]:
        ordered = [
            slug,
            self.canonical_slug(slug),
            *incident_aliases(slug),
            *incident_aliases(self.canonical_slug(slug)),
        ]
        return list(dict.fromkeys(item for item in ordered if item))

    def resolve(self, slug: str, exists: Callable[[str], bool] | None = None) -> ResolutionResult:
        trace: list[str] = []
        candidates = self.candidates(slug)
        if exists is None:
            return ResolutionResult(slug, candidates[1] if len(candidates) > 1 else slug, tuple(candidates), tuple(trace), "canonical-policy")

        for candidate in candidates:
            trace.append(f"exists:{candidate}")
            if exists(candidate):
                source = "exact" if candidate == slug else "canonical-resolver"
                return ResolutionResult(slug, candidate, tuple(candidates), tuple(trace), source)
        return ResolutionResult(slug, candidates[1] if len(candidates) > 1 else slug, tuple(candidates), tuple(trace), "unresolved")

    def _validate_no_cycles(self) -> None:
        for start in self._aliases:
            seen: set[str] = set()
            current = start
            while current in self._aliases:
                if current in seen:
                    raise ValueError(f"canonical alias cycle detected at {current}")
                seen.add(current)
                current = self._aliases[current]


def load_default_resolver() -> CanonicalResolver:
    path = Path(__file__).with_name("mappings.json")
    return CanonicalResolver(json.loads(path.read_text(encoding="utf-8")))
