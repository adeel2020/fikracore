"""Registry-backed engine router."""

from __future__ import annotations

from capability_registry import EngineManifest, MarkRegistry, load_default_registry

from .policy import EnginePolicy
from .trace import EngineCandidate, EngineRouteTrace


class EngineRouter:
    """Route a user query to a registered MARK engine by relevance score."""

    def __init__(self, registry: MarkRegistry | None = None, minimum_confidence: float = 0.2) -> None:
        self.registry = registry or load_default_registry()
        self.minimum_confidence = minimum_confidence
        self.policy = EnginePolicy(self.registry)

    def route(self, query: str) -> tuple[EngineManifest | None, EngineRouteTrace]:
        normalized = " ".join(query.lower().split())
        candidates = [self._candidate(engine, normalized) for engine in self.registry.engines.values()]
        candidates.sort(key=lambda candidate: candidate.confidence, reverse=True)

        trace = EngineRouteTrace(query=query, candidates=candidates)
        for candidate in candidates:
            if candidate.confidence < self.minimum_confidence:
                break
            engine = self.registry.engines[candidate.engine_id]
            decision = self.policy.evaluate(engine)
            trace.warnings.extend(decision.warnings)
            if decision.allowed:
                trace.selected_engine = engine.id
                trace.engine_confidence = candidate.confidence
                return engine, trace
            trace.warnings.append(f"{engine.id} blocked: {decision.reason}")

        trace.warnings.append("No registered engine met routing confidence.")
        return None, trace

    @staticmethod
    def _candidate(engine: EngineManifest, normalized_query: str) -> EngineCandidate:
        if not normalized_query:
            return EngineCandidate(engine.id, 0.0, "empty query")

        matched_terms = []
        for intent in engine.routing_intents:
            for term in intent.lower().replace("_", " ").split():
                if len(term) > 2 and term in normalized_query and term not in matched_terms:
                    matched_terms.append(term)

        if not matched_terms:
            return EngineCandidate(engine.id, 0.0, "no routing intent terms matched")

        confidence = min(1.0, 0.15 + len(matched_terms) * 0.12)
        return EngineCandidate(engine.id, confidence, f"matched terms: {', '.join(matched_terms)}")
