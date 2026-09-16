"""Human-Readable Scenario Registry & Multi-Tier Scenario Resolver for FikraCore.

Enforces deterministic scenario resolution in strict order:
1. Exact scenario ID (e.g. H4-WI-001)
2. Exact display-name match
3. Exact alias match
4. Case-insensitive normalized match
5. Fuzzy / NLP semantic match (strictly maps to an existing ID, never invents an ID)
6. Ambiguity handling (requests disambiguation when multiple candidates match closely)

Shared across:
- CLI commands
- Simulator UI search
- Curated Demo scenario selection
- Mark / Zaki voice and chat interfaces
"""

from __future__ import annotations

import difflib
from enum import Enum
from pathlib import Path
import re
from typing import Any
import yaml
from pydantic import BaseModel, Field


class ResolutionMatchTier(str, Enum):
    EXACT_ID = "EXACT_ID"
    EXACT_NAME = "EXACT_NAME"
    ALIAS = "ALIAS"
    NORMALIZED = "NORMALIZED"
    SEMANTIC = "SEMANTIC"
    AMBIGUOUS = "AMBIGUOUS"
    NONE = "NONE"


class ScenarioRecord(BaseModel):
    id: str
    stage: str = "H1"
    concept: str = "Understand"
    scenario_type: str = "INCIDENT"
    display_name: str
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    scenario_path: str = ""
    demo_enabled: bool = True

    @property
    def scenario_id(self) -> str:
        return self.id


class ResolutionResult(BaseModel):
    record: ScenarioRecord | None = None
    tier: ResolutionMatchTier = ResolutionMatchTier.NONE
    confidence: float = 0.0
    candidates: list[ScenarioRecord] = Field(default_factory=list)
    requires_disambiguation: bool = False
    message: str | None = None


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and stripping punctuation and excess whitespace."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", " ", s)
    return " ".join(s.split())


class ScenarioRegistry:
    """Registry holding scenario records loaded from YAML or runtime registration."""

    def __init__(self, records: list[ScenarioRecord] | None = None) -> None:
        self.records: dict[str, ScenarioRecord] = {}
        self.by_display_name: dict[str, ScenarioRecord] = {}
        self.by_alias: dict[str, ScenarioRecord] = {}
        self.normalized_index: dict[str, str] = {}  # normalized_text -> scenario_id

        if records:
            for r in records:
                self.register(r)

    def register(self, record: ScenarioRecord) -> None:
        self.records[record.id.upper()] = record
        norm_name = normalize_text(record.display_name)
        self.by_display_name[norm_name] = record
        self.normalized_index[norm_name] = record.id

        # Index aliases
        for alias in record.aliases:
            norm_alias = normalize_text(alias)
            self.by_alias[norm_alias] = record
            self.normalized_index[norm_alias] = record.id

    @classmethod
    def from_yaml_file(cls, path: Path | str) -> ScenarioRegistry:
        p = Path(path)
        if not p.exists():
            return cls([])
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        records = []
        for item in data:
            records.append(ScenarioRecord(**item))
        return cls(records)

    @classmethod
    def get_default(cls) -> ScenarioRegistry:
        return get_default_h4_registry()

    def get(self, scenario_id: str) -> ScenarioRecord | None:
        return self.records.get(scenario_id.upper())

    def list_all(self) -> list[ScenarioRecord]:
        return list(self.records.values())


class ScenarioResolver:
    """Multi-tier scenario resolver adhering to deterministic mapping first and NLP safety."""

    def __init__(self, registry: ScenarioRegistry) -> None:
        self.registry = registry

    def resolve_by_id(self, query: str) -> ScenarioRecord | None:
        """Tier 1: Exact scenario ID."""
        cleaned = query.strip().upper()
        return self.registry.get(cleaned)

    def resolve_by_display_name(self, query: str) -> ScenarioRecord | None:
        """Tier 2: Exact display-name match (case-insensitive)."""
        norm = normalize_text(query)
        for rec in self.registry.list_all():
            if rec.display_name.lower() == query.strip().lower() or normalize_text(rec.display_name) == norm:
                return rec
        return None

    def resolve_by_alias(self, query: str) -> ScenarioRecord | None:
        """Tier 3: Exact alias match (case-insensitive)."""
        norm = normalize_text(query)
        for rec in self.registry.list_all():
            for al in rec.aliases:
                if al.lower() == query.strip().lower() or normalize_text(al) == norm:
                    return rec
        return None

    def resolve_by_normalized(self, query: str) -> ScenarioRecord | None:
        """Tier 4: Normalized substring or index match."""
        norm = normalize_text(query)
        if norm in self.registry.normalized_index:
            sc_id = self.registry.normalized_index[norm]
            return self.registry.get(sc_id)
        return None

    def resolve_semantically(self, query: str, threshold: float = 0.35) -> list[tuple[ScenarioRecord, float]]:
        """Tier 5: Fuzzy / NLP token overlap match.
        
        NLP Safety Rule: Only returns records existing in registry; never invents an ID.
        """
        norm_query = normalize_text(query)
        query_tokens = set(norm_query.split())
        scored: list[tuple[ScenarioRecord, float]] = []

        for rec in self.registry.list_all():
            candidates_text = [
                rec.display_name,
                rec.description,
                rec.id,
            ] + rec.aliases + rec.tags

            best_sim = 0.0
            for cand in candidates_text:
                cand_norm = normalize_text(cand)
                cand_tokens = set(cand_norm.split())

                # Token Jaccard overlap
                overlap = len(query_tokens & cand_tokens)
                union = len(query_tokens | cand_tokens)
                jaccard = overlap / union if union > 0 else 0.0

                # SequenceMatcher ratio
                seq_ratio = difflib.SequenceMatcher(None, norm_query, cand_norm).ratio()

                # Boost if query tokens are subset of candidate or vice versa
                subset_boost = 0.2 if query_tokens.issubset(cand_tokens) or cand_tokens.issubset(query_tokens) else 0.0
                if overlap == 0 and seq_ratio < 0.75:
                    sim = 0.0
                else:
                    sim = max(jaccard * 0.7 + subset_boost, seq_ratio)
                if sim > best_sim:
                    best_sim = sim

            if best_sim >= threshold:
                scored.append((rec, best_sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def resolve_or_disambiguate(
        self, query: str
    ) -> tuple[ScenarioRecord | None, list[ScenarioRecord], str | None]:
        """Resolves query in strict order: ID -> display name -> alias -> normalized -> NLP.
        
        Returns:
            (matched_record, disambiguation_candidates, message)
        """
        # 1. Exact ID
        by_id = self.resolve_by_id(query)
        if by_id:
            return by_id, [], None

        # 2. Display Name
        by_name = self.resolve_by_display_name(query)
        if by_name:
            return by_name, [], None

        # 3. Exact Alias
        by_alias = self.resolve_by_alias(query)
        if by_alias:
            return by_alias, [], None

        # 4. Normalized
        by_norm = self.resolve_by_normalized(query)
        if by_norm:
            return by_norm, [], None

        # 5. Semantic / Fuzzy
        semantic_matches = self.resolve_semantically(query)
        if not semantic_matches:
            return None, [], "No existing scenario matched with sufficient confidence."

        # Check for ambiguity
        top_rec, top_score = semantic_matches[0]
        # Candidates within 0.06 of top score
        close_candidates = [
            rec for rec, sc in semantic_matches if abs(sc - top_score) < 0.06 and sc >= 0.4
        ]

        if len(close_candidates) > 1 and top_score < 0.85:
            # Ambiguity: requires disambiguation
            return (
                None,
                close_candidates,
                f"Ambiguous query '{query}'. Matches multiple scenarios: "
                + ", ".join(f"'{c.display_name}' ({c.id})" for c in close_candidates),
            )

        return top_rec, [], None

    def resolve(self, query: str) -> ResolutionResult | None:
        """Resolves query and returns a structured ResolutionResult."""
        # 1. Exact ID
        by_id = self.resolve_by_id(query)
        if by_id:
            return ResolutionResult(
                record=by_id,
                tier=ResolutionMatchTier.EXACT_ID,
                confidence=1.0,
            )

        # 2. Display Name
        by_name = self.resolve_by_display_name(query)
        if by_name:
            return ResolutionResult(
                record=by_name,
                tier=ResolutionMatchTier.EXACT_NAME,
                confidence=0.98,
            )

        # 3. Exact Alias
        by_alias = self.resolve_by_alias(query)
        if by_alias:
            return ResolutionResult(
                record=by_alias,
                tier=ResolutionMatchTier.ALIAS,
                confidence=0.95,
            )

        # 4. Normalized
        by_norm = self.resolve_by_normalized(query)
        if by_norm:
            return ResolutionResult(
                record=by_norm,
                tier=ResolutionMatchTier.NORMALIZED,
                confidence=0.90,
            )

        # 5. Semantic / Fuzzy
        semantic_matches = self.resolve_semantically(query)
        if not semantic_matches:
            return None

        top_rec, top_score = semantic_matches[0]
        close_candidates = [
            rec for rec, sc in semantic_matches if abs(sc - top_score) < 0.06 and sc >= 0.4
        ]
        if len(close_candidates) > 1 and top_score < 0.85:
            return ResolutionResult(
                record=None,
                tier=ResolutionMatchTier.AMBIGUOUS,
                confidence=top_score,
                candidates=close_candidates,
                requires_disambiguation=True,
                message=f"Ambiguous query '{query}'. Matches multiple scenarios: "
                + ", ".join(f"'{c.display_name}' ({c.id})" for c in close_candidates),
            )

        return ResolutionResult(
            record=top_rec,
            tier=ResolutionMatchTier.SEMANTIC,
            confidence=round(top_score, 2),
        )


def get_unified_registry() -> ScenarioRegistry:
    """Build unified scenario registry covering Understand, Discover, Learn, Anticipate."""
    try:
        from ..simulator.scenario_catalog import scenario_catalog
        records = []
        for s in scenario_catalog.all():
            records.append(
                ScenarioRecord(
                    id=s.id,
                    stage=s.stage,
                    concept=s.concept,
                    scenario_type=s.scenario_type,
                    display_name=s.display_name,
                    description=s.description,
                    aliases=s.aliases,
                    tags=s.tags,
                    domains=s.domains,
                    services=s.services,
                    scenario_path=s.scenario_path,
                    demo_enabled=s.demo_enabled,
                )
            )
        return ScenarioRegistry(records)
    except Exception:
        pass

    registry_file = (
        Path(__file__).parent.parent / "simulator" / "scenarios" / "h4_registry.yaml"
    )
    if registry_file.exists():
        return ScenarioRegistry.from_yaml_file(registry_file)
    return ScenarioRegistry([])


def get_default_h4_registry() -> ScenarioRegistry:
    """Return the unified scenario registry (backward-compatible alias)."""
    return get_unified_registry()
