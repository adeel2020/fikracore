"""Deterministic topology/service-aware investigation over operational evidence only.

Refactored to use the 4-Dimension Correlation Engine (Phases 2.1-2.4)
for temporal/identity, topological, pathway, and blast radius correlation.
"""

from itertools import combinations
from time import perf_counter

import networkx as nx

from .contracts import (Assumption, CandidateRelationship, CausalRole, Evidence,
                        EvidenceRequest, Hypothesis, InvestigationResult, KnowledgeState, Terminal)
from .evidence import load_evidence
from .knowledge import CanonicalKnowledge
from .correlation.engine import CorrelationEngine

# Dependency edges point from consumer to supplier. Connectivity alone is not causal direction.
ACTIVE = {KnowledgeState.CONFIRMED, KnowledgeState.SUPPORTED, KnowledgeState.INFERRED, KnowledgeState.UNKNOWN}


def _quality(evidence):
    observed = 1 if evidence.observed_or_inferred in {"OBSERVED", "CONFIRMED"} else .4
    return evidence.source_reliability * evidence.freshness * observed


class Investigator:
    def __init__(self, provider, resolver=None, step_callback=None):
        self.provider = provider
        self.resolver = resolver
        self.step_callback = step_callback

    def run(self, generated_input, operational_root, step_callback=None):
        callback = step_callback or self.step_callback
        evidence, hashes = load_evidence(generated_input, operational_root)
        if callback:
            callback("ingestion", {"raw_evidence_count": len(evidence), "hashes_count": len(hashes), "operational_root": str(operational_root)})
        return self.investigate(generated_input, evidence, hashes, step_callback=callback)

    def investigate(self, run, evidence: list[Evidence], input_hashes=None, step_callback=None):
        callback = step_callback or self.step_callback
        started = perf_counter()
        knowledge = CanonicalKnowledge(self.provider, self.resolver)

        # ── Stage 1: Ingestion ──────────────────────────────────────────────
        if callback:
            sources = {}
            types = {}
            for e in evidence:
                sources[e.source] = sources.get(e.source, 0) + 1
                types[e.evidence_type] = types.get(e.evidence_type, 0) + 1
            min_t = min((e.event_time for e in evidence), default=None)
            max_t = max((e.event_time for e in evidence), default=None)
            span = (max_t - min_t).total_seconds() if min_t and max_t else 0
            callback("ingestion", {
                "raw_count": len(evidence),
                "raw_evidence_count": len(evidence),
                "sources": sources,
                "types": types,
                "min_time": str(min_t) if min_t else "",
                "max_time": str(max_t) if max_t else "",
                "time_span": span,
                "hashes_count": len(input_hashes or []),
            })

        # ── Stage 2: Correlation Engine (Phases 2.1-2.4) ────────────────────
        correlation = CorrelationEngine(knowledge)
        corr_result = correlation.run(evidence, step_callback=callback)

        events = corr_result.events
        abnormal = corr_result.abnormal
        healthy = corr_result.healthy
        impacted = corr_result.impacted
        unrelated = corr_result.blast_radius.unrelated
        roots = corr_result.roots
        edges = corr_result.edges
        graph = corr_result.graph
        impacted_service = corr_result.blast_radius.impacted_service

        hypotheses = []
        first_useful = None

        if callback:
            earliest = min((item.event_time for item in abnormal), default=None)
            local_sources = {item.source for item in abnormal if item.evidence_type not in {"changes", "recovery", "tickets"}}
            independence = min(1.0, len(local_sources) / 2)
            avg_freshness = sum(item.freshness for item in abnormal) / max(1, len(abnormal))
            avg_reliability = sum(item.source_reliability for item in abnormal) / max(1, len(abnormal))
            has_changes = any(item.evidence_type == "changes" for item in events)

            score_dims = {
                "temporal_precedence": 1.0 if earliest else 0.5,
                "evidence_freshness": avg_freshness,
                "source_reliability": avg_reliability,
                "independent_telemetry": independence,
                "upstream_position": 1.0 if edges else 0.0,
                "knowledge_confidence": min((edge.confidence for edge in edges.values()), default=1.0),
                "change_relevance": 1.0 if has_changes else 0.0,
                "historical_support": 0.0,
                "symptom_likelihood_penalty": 0.0,
                "blast_radius_coverage": 1.0,
                "service_dependency_relevance": 1.0 if impacted_service else 0.0,
                "negative_evidence": 0.0,
            }
            callback("correlation_payload", {
                "score_dimensions": score_dims,
                "raw_count": len(evidence),
                "abnormal_count": len(abnormal),
                "impacted_count": len(impacted),
                "domain_count": len(corr_result.pathways.domains),
            })
            callback("pathways", {
                "evidence_count": len(events),
                "abnormal_count": len(abnormal),
                "root_count": len(roots),
                "domains": corr_result.pathways.domains,
                "relationship_count": len(edges),
                "knowledge_gap_count": len(knowledge.failures & impacted),
            })

        # ── Stage 3: Hypothesis Generation ──────────────────────────────────
        if callback:
            callback("hypotheses_generated", {
                "roots": roots,
                "dual_cause_count": 0,
            })

        # ── Stage 4: Hypothesis Testing (12-Factor Synthesis Core) ───────────
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
            direct = sum(_quality(item) for item in local) / max(1, len(local))
            negative_strength = max((_quality(item) for item in negative), default=0)
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
            if callback:
                callback("assess", {
                    "candidate": root,
                    "index": index,
                    "score": hypothesis.hypothesis_confidence,
                    "causal_confidence": hypothesis.causal_confidence,
                    "coverage": hypothesis.explanation_coverage,
                    "status": str(hypothesis.status),
                    "causal_role": str(hypothesis.causal_role),
                    "score_dimensions": hypothesis.score_dimensions,
                    "supporting_evidence": hypothesis.supporting_evidence,
                    "contradicting_evidence": hypothesis.contradicting_evidence,
                    "knowledge_relationships_used": hypothesis.knowledge_relationships_used,
                })
            if first_useful is None and hypothesis.status == KnowledgeState.SUPPORTED:
                first_useful = index

        # Two-cause hypotheses admitted only when both have direct independent evidence
        independent = [h for h in hypotheses if h.score_dimensions["independent_telemetry"] == 1 and not h.contradicting_evidence]
        for left, right in combinations(independent[:12], 2):
            if nx.has_path(graph, left.canonical_root_entity, right.canonical_root_entity) or nx.has_path(graph, right.canonical_root_entity, left.canonical_root_entity):
                continue
            joint = assess((left.canonical_root_entity, right.canonical_root_entity), len(hypotheses) + 1)
            if joint.explanation_coverage > max(left.explanation_coverage, right.explanation_coverage):
                hypotheses.append(joint)

        # ── Stage 5: Convergence & Knowledge Gap Detection ───────────────────
        hypotheses.sort(key=lambda h: (h.status == KnowledgeState.REJECTED, -h.hypothesis_confidence, h.hypothesis_id))
        best = next((h for h in hypotheses if h.status != KnowledgeState.REJECTED), None)
        if callback and best:
            callback("ranked", {"best_root": best.canonical_root_entity, "best_score": best.hypothesis_confidence, "coverage": best.explanation_coverage, "total_hypotheses": len(hypotheses)})
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

        if callback:
            ranked_info = [
                {"entity": h.canonical_root_entity, "score": h.hypothesis_confidence, "coverage": h.explanation_coverage}
                for h in hypotheses
            ]
            best_info = {
                "canonical_root_entity": best.canonical_root_entity,
                "score": best.hypothesis_confidence,
            } if best else None
            callback("convergence", {
                "hypotheses": hypotheses,
                "best": best_info,
                "ranked": ranked_info,
                "explained": len(explained),
                "total_abnormal": len(abnormal),
                "coverage": coverage,
                "residual_count": len(residual),
                "gap_count": len(candidates) + len(gaps),
                "terminal": terminal.value,
            })

            primary_dom = best.candidate_root_domain if best and best.candidate_root_domain != "unknown" else (
                corr_result.pathways.domains[0] if corr_result.pathways.domains else "transport"
            )
            chain = [best.canonical_root_entity] if best else []
            curr = best.canonical_root_entity if best else None
            if curr:
                while True:
                    succs = sorted(set(graph.successors(curr)) & impacted)
                    if not succs or succs[0] in chain:
                        break
                    curr = succs[0]
                    chain.append(curr)
                    if len(chain) >= 5:
                        break
            domain_list = []
            for d in corr_result.pathways.domains:
                is_prim = (d == primary_dom)
                domain_list.append({
                    "name": d,
                    "primary": is_prim,
                    "contributing": not is_prim,
                    "reason": "Root cause origin" if is_prim else "Impacted layer",
                })
            svc_ents = list(corr_result.blast_radius.service_entities.get(impacted_service or "", []))
            callback("domain_attribution", {
                "primary_domain": primary_dom,
                "domains": domain_list,
                "impacted_service": impacted_service or "NONE",
                "service_entities": svc_ents,
                "propagation_chain": " ──► ".join(chain) if chain else "",
            })

            req_data = [
                {"id": r.request_id, "question": r.question, "priority": r.priority, "cost": r.cost, "latency": r.latency}
                for r in requests
            ]
            callback("next_best_evidence", {
                "requests": req_data,
                "terminal": terminal.value,
            })

            callback("promotion", {
                "no_gaps": not bool(candidates),
                "gap_count": len(candidates),
            })
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
