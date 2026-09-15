"""Deterministic topology/service-aware investigation over operational evidence only."""

from itertools import combinations
from time import perf_counter

import networkx as nx

from .contracts import (Assumption, CandidateRelationship, CausalRole, Evidence,
                        EvidenceRequest, Hypothesis, InvestigationResult, KnowledgeState, Terminal)
from .evidence import collapse, load_evidence, reject_truth
from .knowledge import CanonicalKnowledge

# Dependency edges point from consumer to supplier. Connectivity alone is not causal direction.
DEPENDENCIES = {"depends-on", "routes-through", "carried-by", "hosted-on", "runs-on",
                "backhauled-by", "powered-by", "charges-via", "authenticates-via", "resolves-via",
                "timed-by", "uses-database", "uses-cache", "uses-message-bus", "provisioned-by"}
ACTIVE = {KnowledgeState.CONFIRMED, KnowledgeState.SUPPORTED, KnowledgeState.INFERRED, KnowledgeState.UNKNOWN}


def quality(evidence):
    observed = 1 if evidence.observed_or_inferred in {"OBSERVED", "CONFIRMED"} else .4
    return evidence.source_reliability * evidence.freshness * observed


class Investigator:
    def __init__(self, provider, resolver=None):
        self.provider = provider
        self.resolver = resolver

    def run(self, generated_input, operational_root):
        evidence, hashes = load_evidence(generated_input, operational_root)
        return self.investigate(generated_input, evidence, hashes)

    def investigate(self, run, evidence: list[Evidence], input_hashes=None):
        started = perf_counter()
        knowledge = CanonicalKnowledge(self.provider, self.resolver)
        normalized = []
        observation_time = max((item.ingestion_time for item in evidence), default=None)
        for item in evidence:
            reject_truth(item.model_dump(mode="json"))
            canonical = knowledge.resolve_entity(item.canonical_entity, item.source_native_entity)
            age_hours = max(0, (observation_time - item.event_time).total_seconds() / 3600) if observation_time else 0
            normalized.append(item.model_copy(update={"canonical_entity": canonical,
                "freshness": item.freshness / (1 + age_hours),
                "observed_path": [knowledge.canonical(entity) for entity in item.observed_path]}))
        events = collapse(normalized)
        edges = {}
        for slug in sorted({item.canonical_entity for item in events}):
            for edge in knowledge.traverse(slug):
                edges[edge.relationship_id] = edge
        graph = nx.DiGraph()
        graph.add_nodes_from(item.canonical_entity for item in events)
        FORWARD_TYPES = {"member-of", "monitored-by", "supports-service", "serves"}
        for edge in sorted(edges.values(), key=lambda edge: edge.relationship_id):
            if edge.state not in ACTIVE:
                continue
            if edge.link_type in FORWARD_TYPES:
                source, target = edge.source, edge.target
            else:
                source, target = edge.target, edge.source
            graph.add_edge(source, target, relationship=edge)

        service_entities = {}
        for item in events:
            if item.polarity == "abnormal":
                for service in item.service:
                    service_entities.setdefault(service, set()).add(item.canonical_entity)
        impacted_service = min(service_entities, key=lambda service: (-len(service_entities[service]), service)) if service_entities else None
        unrelated = [item for item in events if item.service and impacted_service not in item.service]
        abnormal = [item for item in events if item.polarity == "abnormal" and quality(item) >= .3 and item not in unrelated]
        healthy = [item for item in events if item.polarity == "healthy" and quality(item) >= .5]
        # Equal weight per affected entity prevents an alarm flood from defining blast radius.
        impacted = {item.canonical_entity for item in abnormal}
        roots = sorted({item.canonical_entity for item in events})
        roots = sorted(set(roots) | {ancestor for entity in impacted for ancestor in nx.ancestors(graph, entity)})
        hypotheses = []
        first_useful = None

        def assess(root_set, index):
            reachable = set(root_set)
            for root in root_set:
                reachable.update(nx.descendants(graph, root))
            supported = [item for item in abnormal if item.canonical_entity in reachable]
            local = [item for item in abnormal if item.canonical_entity in root_set]
            negative = [item for item in healthy if item.canonical_entity in root_set and (
                item.signal.lower() in {"healthy", "local health normal", "all checks healthy"} or
                any(item.signal == observation.signal for observation in local))]
            coverage = len(impacted & reachable) / max(1, len(impacted))
            relations = {}
            for item in supported:
                for root in root_set:
                    if nx.has_path(graph, root, item.canonical_entity):
                        path = nx.shortest_path(graph, root, item.canonical_entity)
                        for source, target in zip(path, path[1:]):
                            edge = graph[source][target]["relationship"]
                            relations[edge.relationship_id] = edge
            earliest = min((item.event_time for item in abnormal), default=None)
            local_time = min((item.event_time for item in local), default=None)
            temporal = .5 if not local_time else float(local_time == earliest)
            sources = {item.source for item in local if item.evidence_type not in {"changes", "recovery", "tickets"}}
            independence = min(1, len(sources) / 2)
            direct = sum(quality(item) for item in local) / max(1, len(local))
            negative_strength = max((quality(item) for item in negative), default=0)
            service = float(any(item.service for item in supported))
            changes = [item for item in events if item.evidence_type == "changes" and
                       item.canonical_entity in root_set and local_time and item.event_time <= local_time]
            knowledge_confidence = min((edge.confidence for edge in relations.values()), default=1 if local else 0)
            freshness = sum(item.freshness for item in supported) / max(1, len(supported))
            reliability = sum(item.source_reliability for item in supported) / max(1, len(supported))
            symptom = float(bool(local) and all(item.evidence_type in {"tickets", "kpis"} for item in local))
            historical = 0.0
            absent_expected = []
            for root in root_set:
                page = knowledge.get_page(root)
                if page and page.get("frontmatter", {}).get("validated_fault_history"):
                    historical = .5
                expectations = page.get("frontmatter", {}) if page else {}
                if expectations.get("monitoring_complete") is True:
                    absent_expected.extend(signal for signal in expectations.get("expected_fault_signals", [])
                                           if not any(item.signal == signal for item in local))
            if absent_expected:
                negative_strength = max(negative_strength, .8)
            dimensions = {"temporal_precedence": temporal, "upstream_position": float(bool(relations)),
                          "blast_radius_coverage": coverage, "service_dependency_relevance": service,
                          "change_relevance": float(bool(changes)), "independent_telemetry": independence,
                          "historical_support": historical, "negative_evidence": negative_strength,
                          "symptom_likelihood_penalty": symptom, "knowledge_confidence": knowledge_confidence,
                          "evidence_freshness": freshness, "source_reliability": reliability}
            score = (.32 * coverage + .18 * independence + .15 * direct + .10 * temporal +
                     .08 * float(bool(relations)) + .05 * service + .05 * knowledge_confidence +
                     .03 * freshness + .02 * reliability + .01 * bool(changes) + .01 * historical -
                     .45 * negative_strength - .20 * symptom - .08 * (len(root_set) - 1))
            score = round(max(0, min(1, score)), 4)
            status = KnowledgeState.REJECTED if negative_strength >= .7 and direct < .5 else KnowledgeState.SUPPORTED if score >= .65 else KnowledgeState.CANDIDATE
            assumption = "A sustained local impairment exists at the proposed root entities"
            missing = [f"Expected signal absent despite complete monitoring: {signal}" for signal in absent_expected]
            if not local:
                missing.append("Direct local telemetry at " + ", ".join(root_set))
            if len(sources) < 2:
                missing.append("Independent source confirmation at " + ", ".join(root_set))
            if coverage < 1:
                missing.append("Operational dependency or alternate cause for residual impact")
            role = CausalRole.ROOT if coverage >= .8 and not symptom else CausalRole.SYMPTOM if symptom else CausalRole.CONTRIBUTING_CONDITION
            domain = next((item.domain for item in local), "unknown")
            return Hypothesis(
                hypothesis_id=f"H-{index:03d}", statement="Inferred local impairment at " + " and ".join(root_set),
                candidate_root_domain=domain, candidate_root_entity=root_set[0], canonical_root_entity=root_set[0],
                root_entities=list(root_set), causal_role=role,
                assumptions=[Assumption(statement=assumption, state="CONTRADICTED" if negative else "SUPPORTED" if local else "UNTESTED",
                                        evidence_ids=[item.evidence_id for item in negative or local]),
                             Assumption(statement="Known dependencies account for affected services", state="SUPPORTED" if coverage == 1 else "UNCERTAIN",
                                        evidence_ids=[item.evidence_id for item in supported])],
                expected_observations=["Local impairment precedes or coincides with dependent symptoms", "Independent local telemetry agrees"],
                supporting_evidence=[item.evidence_id for item in supported], contradicting_evidence=[item.evidence_id for item in negative],
                missing_evidence=missing, knowledge_relationships_used=sorted(relations), status=status,
                hypothesis_confidence=score, causal_confidence=round(score * knowledge_confidence, 4),
                explanation_coverage=coverage, score_dimensions=dimensions,
                failed_assumptions=([assumption] if negative else []) + missing[:len(absent_expected)],
            )

        for index, root in enumerate(roots, 1):
            hypothesis = assess((root,), index)
            hypotheses.append(hypothesis)
            if first_useful is None and hypothesis.status == KnowledgeState.SUPPORTED:
                first_useful = index
        # Explicit two-cause hypotheses are admitted only when both have direct independent evidence.
        independent = [h for h in hypotheses if h.score_dimensions["independent_telemetry"] == 1 and not h.contradicting_evidence]
        for left, right in combinations(independent[:12], 2):
            if nx.has_path(graph, left.canonical_root_entity, right.canonical_root_entity) or nx.has_path(graph, right.canonical_root_entity, left.canonical_root_entity):
                continue
            joint = assess((left.canonical_root_entity, right.canonical_root_entity), len(hypotheses) + 1)
            if joint.explanation_coverage > max(left.explanation_coverage, right.explanation_coverage):
                hypotheses.append(joint)
        hypotheses.sort(key=lambda h: (h.status == KnowledgeState.REJECTED, -h.hypothesis_confidence, h.hypothesis_id))
        best = next((h for h in hypotheses if h.status != KnowledgeState.REJECTED), None)
        explained = set(best.supporting_evidence) if best else set()
        residual = [item.evidence_id for item in abnormal if item.evidence_id not in explained]
        gaps = sorted(knowledge.failures & impacted)
        candidates = []
        known_pairs = {frozenset((edge.source, edge.target)) for edge in edges.values() if edge.state in ACTIVE}
        for item in events:
            if item in unrelated:
                continue
            for source, target in zip(item.observed_path, item.observed_path[1:]):
                if frozenset((source, target)) not in known_pairs and source != target:
                    pair = (source, target)
                    if any((candidate.source, candidate.target) == pair for candidate in candidates):
                        continue
                    candidates.append(CandidateRelationship(candidate_id=f"REL-{len(candidates)+1:03d}",
                        source=source, target=target, supporting_evidence=[item.evidence_id],
                        reason="Observed path adjacency is absent from operational knowledge; requires independent validation"))
                    gaps.append(f"Unverified path adjacency: {source} -> {target}")
        coverage = best.explanation_coverage if best else 0
        model_gap = bool(candidates or gaps or not best)
        discovery = model_gap or bool(residual and coverage < 0.70)
        local_sources = best.score_dimensions["independent_telemetry"] if best else 0

        # Operational Knowledge Gap Localization & Residual Diagnosis (H2)
        from .h2_gap_detector import localize_knowledge_gap
        h2_gaps, _, h2_residuals, h2_contradictions = localize_knowledge_gap(
            events=events,
            graph=graph,
            abnormal=abnormal,
            impacted=impacted,
            known_pairs=known_pairs,
            best_hypothesis=best,
        )

        if not abnormal or len({item.source for item in abnormal}) < 2:
            terminal = Terminal.INSUFFICIENT_EVIDENCE
        elif best and best.contradicting_evidence and best.canonical_root_entity in impacted:
            terminal = Terminal.CONFLICTING_EVIDENCE
        elif model_gap:
            terminal = Terminal.MODEL_INSUFFICIENT
        elif best and (coverage >= 0.75 or (coverage >= 0.35 and not candidates and not gaps and best.hypothesis_confidence >= 0.65)) and best.causal_confidence >= 0.50 and local_sources >= 0.5:
            terminal = Terminal.EXPLAINED
        elif best and coverage >= 0.35 and best.hypothesis_confidence >= 0.45:
            terminal = Terminal.PARTIALLY_EXPLAINED
        else:
            terminal = Terminal.UNRESOLVED
        requests = self._requests(hypotheses, candidates, residual) if terminal != Terminal.EXPLAINED else []
        summary = (f"{terminal.value}: best operational explanation covers {coverage:.0%} of affected entities; "
                   f"{len(residual)} abnormal observations remain unexplained. "
                   "Confidence is a deterministic heuristic, not a calibrated probability.")
        event_graph = []
        for source, target, attributes in graph.edges(data=True):
            upstream = [item for item in abnormal if item.canonical_entity == source]
            downstream = [item for item in abnormal if item.canonical_entity == target]
            for left in upstream:
                for right in downstream:
                    event_graph.append({"from_evidence": left.evidence_id, "to_evidence": right.evidence_id,
                                        "relationship_id": attributes["relationship"].relationship_id,
                                        "state": "INFERRED", "temporal_precedence": left.event_time <= right.event_time})
        provenance = [{"hypothesis_id": h.hypothesis_id, "state": "INFERRED", "evidence_ids": h.supporting_evidence,
                       "contradicting_evidence_ids": h.contradicting_evidence, "relationship_ids": h.knowledge_relationships_used,
                       "assumptions": [a.model_dump(mode="json") for a in h.assumptions]} for h in hypotheses]
        return InvestigationResult(
            run_id=run.run_id, scenario_id=run.scenario_id, terminal_state=terminal,
            ranked_hypotheses=hypotheses, selected_hypothesis_id=best.hypothesis_id if best and terminal in {Terminal.EXPLAINED, Terminal.PARTIALLY_EXPLAINED} else None,
            supporting_evidence=best.supporting_evidence if best else [], contradicting_evidence=best.contradicting_evidence if best else [],
            missing_evidence=best.missing_evidence if best else ["Independent operational observations"],
            explanation_coverage=coverage, unexplained_observations=residual, knowledge_gaps=sorted(set(gaps)),
            candidate_relationships=candidates, canonical_entities_used=sorted(set(roots)), reasoning_summary=summary,
            provenance=provenance, next_best_evidence=requests, discovery_mode=discovery, causal_event_graph=event_graph,
            metadata={**self.provider.metadata, "canonicalization_mapping_version": knowledge.mapping_version,
                      "seed": run.seed, "difficulty_profile": run.difficulty_profile, "evidence_inputs": input_hashes or {},
                      "knowledge_reads": list(knowledge.reads.values()),
                      "relationships": [edge.model_dump(mode="json") for edge in edges.values()],
                      "evidence": [item.model_dump(mode="json") for item in events]},
            diagnostics={"input_evidence_count": len(evidence), "collapsed_evidence_count": len(events),
                         "falsified_hypothesis_count": sum(h.status == KnowledgeState.REJECTED for h in hypotheses),
                         "repeated_falsified_hypothesis_count": 0, "candidate_relationship_count": len(candidates),
                         "canonical_resolution_failures": sorted(knowledge.failures), "topology_gap_detection": bool(gaps),
                         "evidence_requests_before_terminal": len(requests), "steps_to_first_useful_hypothesis": first_useful,
                         "investigation_duration_seconds": perf_counter() - started,
                         "impacted_service": impacted_service,
                         "coincidental_evidence": [item.evidence_id for item in unrelated],
                         "stopping_reason": "Single evidence pass complete; further tests require requested observations",
                         "knowledge_gap_records": [g.model_dump(mode="json") for g in h2_gaps],
                         "unexplained_residuals": [r.model_dump(mode="json") for r in h2_residuals],
                         "model_contradictions": [c.model_dump(mode="json") for c in h2_contradictions]},
        )

    @staticmethod
    def _requests(hypotheses, candidates, residual):
        requests = []
        leaders = [h for h in hypotheses if h.status != KnowledgeState.REJECTED][:2]
        targets = sorted({entity for h in leaders for entity in h.root_entities})
        options = []
        if candidates or residual:
            options.append(("Obtain an independent path trace and authoritative dependency inventory", .95, 1.5, 2., .05,
                            sorted({e for c in candidates for e in (c.source, c.target)}) or targets))
        if leaders:
            options.append(("Compare direct fault telemetry with a healthy peer over the incident interval", .8, 1., 1., 0., targets))
            options.append(("Verify change scope and pre/post-change service measurements", .35, 1., 2., 0., targets))
        if not options:
            options.append(("Collect timestamped fault and healthy-path telemetry from two independent sources", .9, 1., 1., 0., []))
        for question, gain, cost, latency, risk, entities in options:
            requests.append(EvidenceRequest(request_id=f"REQ-{len(requests)+1:03d}", question=question,
                target_entities=entities, discriminates=[h.hypothesis_id for h in leaders], information_gain=gain,
                cost=cost, latency=latency, risk=risk, priority=round(gain * .9 / (cost + latency + risk), 4)))
        return sorted(requests, key=lambda r: (-r.priority, r.request_id))[:2]
