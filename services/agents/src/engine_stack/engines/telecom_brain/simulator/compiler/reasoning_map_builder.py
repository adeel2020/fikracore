from typing import Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import json

def build_reasoning_map(
    
    scenario_id: str,
    run_id: str,
    manifest: Optional[dict[str, Any]],
    trigger_entity: str,
    trigger_display: str,
    affected_service: str,
    raw_events: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    knowledge_gaps: list[dict[str, Any]],
    next_best_actions: list[dict[str, Any]],
    learning: Optional[dict[str, Any]],
    impact: dict[str, Any],
    stage_index: int,
    current_stage: str,
    stage_watchdog: dict[str, Any],
    is_confirmed: bool,
    executed_actions: list[str],
 *, _derive_domains: Callable, _entity_domain: Callable) -> dict[str, Any]:
    """Build the authoritative Neural Reasoning Map contract for Step 5."""
    source_id = f"SRC-{scenario_id}"
    primary_hypothesis = hypotheses[0] if hypotheses else None
    primary_hypothesis_id = primary_hypothesis.get("id") if primary_hypothesis else None
    primary_gap = knowledge_gaps[0] if knowledge_gaps else None
    primary_gap_id = primary_gap.get("id") if primary_gap else None
    primary_action = next_best_actions[0] if next_best_actions else None
    primary_action_id = primary_action.get("id") if primary_action else None
    hitl_validated = any(act in executed_actions for act in ("HITL-001", "VAL-001", "HITL_VALIDATE", "VAL-APPROVE", "hitl-001", "val-001"))
    display_domains = _derive_domains(manifest.get("failure_domain_tags", []) if manifest else [])
    primary_domain = display_domains[0] if display_domains else _entity_domain(trigger_entity).replace("_", " ").title()
    supporting_evidence_ids = [event.get("event_id") for event in raw_events if event.get("event_id")]

    evidence_nodes = [
        {
            "id": event.get("event_id"),
            "evidence_id": event.get("event_id"),
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": event.get("title"),
            "type": event.get("badge") or event.get("category", "Evidence").upper(),
            "evidence_type": event.get("evidence_type") or (event.get("badge") or event.get("category", "Evidence")).upper(),
            "category": event.get("category"),
            "source_entity": event.get("entity_id"),
            "domain": event.get("domain"),
            "timestamp": event.get("time"),
            "status": "ACTIVE",
            "state": "ACTIVE",
            "event_time": event.get("event_time"),
            "evidence_ids": [event.get("event_id")],
            "explain": {
                "what": event.get("title"),
                "why": "Admitted as operational evidence for this run.",
                "supports": [event.get("event_id")],
                "affects": [primary_hypothesis_id] if primary_hypothesis_id and stage_index >= 3 else [],
                "unknown": "Causal role is still being evaluated." if stage_index < 6 else "Validation is assessing the final evidence package.",
                "recent": f"Observed at {event.get('time')}",
            },
        }
        for event in raw_events
        if event.get("event_id")
    ]

    category_ids = {event.get("category") for event in raw_events}
    has_change = "change" in category_ids
    has_metric = "metric" in category_ids
    has_trace = "trace" in category_ids or "log" in category_ids
    has_ticket = "ticket" in category_ids

    is_correlation_stage = stage_index >= 2

    pathway_specs = [
        (
            "PATH-OPERATIONAL-EVIDENCE",
            "Operational Evidence",
            "ACTIVE" if is_correlation_stage and raw_events else "DORMANT",
            "Raw alarms, KPIs and tickets have been admitted.",
            supporting_evidence_ids[:3],
            [primary_hypothesis_id] if primary_hypothesis_id else [],
        ),
        (
            "PATH-SERVICE-DEPENDENCY",
            "Service Dependency",
            "ACTIVE" if is_correlation_stage and (stage_index >= 2 or has_ticket) else "DISCOVERED",
            f"{affected_service} is being mapped to dependent network elements.",
            supporting_evidence_ids[:2],
            [primary_hypothesis_id] if primary_hypothesis_id else [],
        ),
        (
            "PATH-TOPOLOGY-PROPAGATION",
            "Topology & Propagation",
            "ACTIVE" if is_correlation_stage else "DISCOVERED",
            "Failure propagation tracked across physical and logical topological links.",
            supporting_evidence_ids[:2],
            [primary_hypothesis_id] if primary_hypothesis_id else [],
        ),
        (
            "PATH-SUBSCRIBER-JOURNEY",
            "Subscriber Journey",
            "ACTIVE" if is_correlation_stage and has_ticket else ("DISCOVERED" if is_correlation_stage else "DORMANT"),
            "Customer-impact evidence is available for journey correlation.",
            [event.get("event_id") for event in raw_events if event.get("category") == "ticket"],
            [],
        ),
        (
            "PATH-CHANGE-CONFIGURATION",
            "Change & Configuration",
            "ACTIVE" if is_correlation_stage and has_change else "DORMANT",
            "A change record is temporally relevant to the investigation." if has_change else "No admitted change evidence is active yet.",
            [event.get("event_id") for event in raw_events if event.get("category") == "change"],
            [primary_hypothesis_id] if primary_hypothesis_id and has_change else [],
        ),
        (
            "PATH-TRAFFIC-CAPACITY",
            "Traffic & Capacity",
            "ACTIVE" if is_correlation_stage and (has_metric or impact.get("impact_state") in {"ESTIMATED", "INFERRED", "CONFIRMED"}) else "DISCOVERED",
            "Traffic degradation evidence is being tested against capacity explanations.",
            [event.get("event_id") for event in raw_events if event.get("category") == "metric"],
            [hypotheses[1].get("id")] if len(hypotheses) > 1 else [],
        ),
        (
            "PATH-CONTROL-SIGNALING",
            "Control & Signaling",
            "ACTIVE" if is_correlation_stage and has_trace else ("DISCOVERED" if is_correlation_stage else "DORMANT"),
            "Trace or log signals can explain control-plane behavior.",
            [event.get("event_id") for event in raw_events if event.get("category") in {"trace", "log"}],
            [primary_hypothesis_id] if primary_hypothesis_id and has_trace else [],
        ),
        (
            "PATH-RESILIENCE-FAILOVER",
            "Resilience & Failover",
            "ACTIVE" if is_correlation_stage else "DORMANT",
            "Backup-path behavior is evaluated during topology correlation.",
            [],
            [primary_hypothesis_id] if primary_hypothesis_id and is_correlation_stage else [],
        ),
        (
            "PATH-HISTORICAL-PATTERN",
            "Historical Pattern",
            "ACTIVE" if is_correlation_stage else "DORMANT",
            "Similar incidents are matched for precedent during correlation.",
            [],
            [primary_hypothesis_id] if primary_hypothesis_id and is_correlation_stage else [],
        ),
        (
            "PATH-KNOWLEDGE-GAP",
            "Knowledge Gap",
            "ACTIVE" if is_correlation_stage and knowledge_gaps else "DORMANT",
            "Missing evidence is blocking a stronger conclusion." if knowledge_gaps else "No explicit knowledge gap has been raised yet.",
            [],
            [primary_hypothesis_id] if primary_hypothesis_id and knowledge_gaps else [],
        ),
    ]
    pathways = [
        {
            "id": pathway_id,
            "pathway_id": pathway_id,
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": display_name,
            "status": status,
            "state": status,
            "activation_reason": reason,
            "evidence_ids": [evidence_id for evidence_id in evidence_ids if evidence_id],
            "hypothesis_ids": [hyp_id for hyp_id in hypothesis_ids if hyp_id],
            "explain": {
                "what": f"{display_name} reasoning pathway",
                "why": reason,
                "supports": [evidence_id for evidence_id in evidence_ids if evidence_id],
                "affects": [hyp_id for hyp_id in hypothesis_ids if hyp_id],
                "unknown": "Awaiting more evidence." if status in {"DORMANT", "DISCOVERED"} else "Contribution is being evaluated by synthesis.",
                "recent": f"Pathway state is {status}.",
            },
        }
        for pathway_id, display_name, status, reason, evidence_ids, hypothesis_ids in pathway_specs
    ]
    active_pathways = [path for path in pathways if path["status"] in {"ACTIVE", "RESOLVED", "REJECTED"}]

    map_hypotheses = [
        {
            "id": hyp.get("id"),
            "hypothesis_id": hyp.get("id"),
            "display_id": hyp.get("display_id") or f"H{index + 1}",
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": hyp.get("display_name"),
            "status": hyp.get("lifecycle_state") or hyp.get("status"),
            "state": hyp.get("lifecycle_state") or hyp.get("status"),
            "confidence": hyp.get("confidence"),
            "supporting_evidence": hyp.get("evidence_ids", []),
            "contradicting_evidence": hyp.get("against", []),
            "contradictions": hyp.get("against", []),
            "missing_evidence": hyp.get("frontier_ids", []) or ([primary_gap_id] if index == 0 and primary_gap_id else []),
            "explain": {
                "what": f"H{index + 1} - {hyp.get('display_name')}",
                "why": hyp.get("last_delta_reason") or "Candidate explanation from backend reasoning.",
                "supports": hyp.get("evidence_ids", []),
                "affects": [hyp.get("id")],
                "unknown": "; ".join(hyp.get("missing", [])[:2]) or "No explicit missing evidence listed.",
                "recent": hyp.get("delta", "Unranked"),
            },
        }
        for index, hyp in enumerate(hypotheses)
        if hyp.get("id")
    ]
    gaps = [
        {
            "id": gap.get("id"),
            "gap_id": gap.get("id"),
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": gap.get("label"),
            "status": "RESOLVED" if primary_action and primary_action.get("status") == "COMPLETED" and index == 0 else "OPEN",
            "state": "RESOLVED" if primary_action and primary_action.get("status") == "COMPLETED" and index == 0 else (gap.get("state") or "OPEN"),
            "affected_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else [],
            "affected_pathway_ids": ["PATH-KNOWLEDGE-GAP", "PATH-RESILIENCE-FAILOVER"] if index == 0 else ["PATH-KNOWLEDGE-GAP"],
            "affected_hypotheses": [primary_hypothesis_id] if primary_hypothesis_id else [],
            "affected_pathways": ["PATH-KNOWLEDGE-GAP", "PATH-RESILIENCE-FAILOVER"] if index == 0 else ["PATH-KNOWLEDGE-GAP"],
            "required_evidence": primary_action.get("display_name") if index == 0 and primary_action else gap.get("reason"),
            "next_best_evidence_id": primary_action_id if index == 0 else None,
            "explain": {
                "what": gap.get("label"),
                "why": gap.get("reason"),
                "supports": [],
                "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
                "unknown": primary_action.get("display_name") if index == 0 and primary_action else gap.get("reason"),
                "recent": "Evidence request completed." if primary_action and primary_action.get("status") == "COMPLETED" and index == 0 else "Evidence request is pending.",
            },
        }
        for index, gap in enumerate(knowledge_gaps)
        if gap.get("id")
    ]

    if stage_index < 3:
        synthesis_state = "INSUFFICIENT_EVIDENCE"
        synthesis_summary = "Evidence is being admitted and organized; no candidate explanation is ready."
    elif stage_index < 5:
        synthesis_state = "PARTIAL"
        synthesis_summary = "Candidate explanations exist, but testing and gap resolution are still in progress."
    elif primary_gap and primary_action and primary_action.get("status") != "COMPLETED":
        synthesis_state = "MODEL_INSUFFICIENT"
        synthesis_summary = "The leading explanation is blocked by missing evidence."
    elif is_confirmed:
        synthesis_state = "ROOT_CANDIDATE"
        synthesis_summary = "Evidence, pathway fit, and returned telemetry strongly support the leading candidate."
    else:
        synthesis_state = "STRONGLY_SUPPORTED" if stage_index >= 6 else "PARTIAL"
        synthesis_summary = "The leading candidate is supported, with validation still required."

    synthesis = {
        "id": "SYNTHESIS-001",
        "scenario_id": scenario_id,
        "run_id": run_id,
        "display_name": "Intelligence Synthesis",
        "state": synthesis_state,
        "summary": synthesis_summary,
        "dimensions": [
            {"display_name": "Evidence Support", "state": "ACTIVE", "value": len(supporting_evidence_ids)},
            {"display_name": "Service Dependency Fit", "state": "ACTIVE" if stage_index >= 2 else "PENDING"},
            {"display_name": "Contradictions", "state": "LOW" if stage_index >= 5 else "UNKNOWN"},
            {"display_name": "Knowledge Gaps", "state": "OPEN" if gaps and gaps[0]["status"] == "OPEN" else "CLEAR"},
            {"display_name": "Validation State", "state": "ACCEPTED" if hitl_validated else ("PENDING" if stage_index >= 6 else "NOT_READY")},
        ],
        "leading_hypothesis_id": primary_hypothesis_id,
        "explain": {
            "what": "Convergence layer for the investigation.",
            "why": synthesis_summary,
            "supports": supporting_evidence_ids,
            "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
            "unknown": stage_watchdog.get("blocking_reason") or "Domain attribution waits for validation readiness.",
            "recent": f"Synthesis state is {synthesis_state}.",
        },
    }

    validation = {
        "id": "VAL-001",
        "scenario_id": scenario_id,
        "run_id": run_id,
        "display_name": (
            f"{primary_domain} SME Validated {trigger_display} as Primary Root Cause"
            if hitl_validated else f"{primary_domain} HITL SME Validation Pending"
        ),
        "status": "ACCEPTED" if hitl_validated else ("PENDING" if stage_index >= 6 else "NOT_READY"),
        "state": "ACCEPTED" if hitl_validated else ("PENDING" if stage_index >= 6 else "NOT_STARTED"),
        "reviewer_role": f"{primary_domain} SME / Engineer",
        "evidence_package_ids": supporting_evidence_ids,
        "explain": {
            "what": "Domain engineer HITL validation state.",
            "why": "Validation requires explicit Human-in-the-Loop review & sign-off.",
            "supports": supporting_evidence_ids,
            "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
            "unknown": "Awaiting SME sign-off." if not hitl_validated else "HITL SME validation accepted.",
            "recent": "Validation accepted." if hitl_validated else "Awaiting Human-in-the-Loop SME validation.",
        },
    }

    def _to_domain_id(name: str) -> str:
        n = name.lower()
        if "transport" in n: return "transport"
        if "ran" in n: return "ran"
        if "core" in n: return "mobile_core"
        if "ims" in n or "voice" in n: return "ims_voice"
        if "policy" in n or "subscriber" in n: return "policy_subscriber"
        if "security" in n: return "security"
        if "cloud" in n or "k8s" in n: return "cloud_k8s"
        if "roaming" in n: return "roaming"
        if "charging" in n: return "charging"
        if "oss" in n or "bss" in n: return "oss_bss"
        return n.replace(" ", "_")

    rev = stage_index
    seq = stage_index
    is_ready = stage_index >= 6

    domain_attribution_domains = []
    if is_ready:
        primary_reason = f"Validated reasoning on {trigger_display} identifies {primary_domain} as primary causal failure root."
        domain_attribution_domains.append({
            "domain_id": _to_domain_id(primary_domain),
            "display_name": primary_domain,
            "role": "PRIMARY",
            "attribution_basis": "CAUSAL",
            "confidence": 88 if is_confirmed else 76,
            "reason": primary_reason,
            "supporting_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else ["HYP-001"],
            "supporting_evidence_ids": supporting_evidence_ids[:4],
            "supporting_pathway_ids": ["PW-001"],
            "source_revision": rev,
        })

    if stage_index >= 2 and affected_service:
        aff_dom = "RAN" if any(k in affected_service for k in ["Mobile Data", "RAN", "Cell"]) else ("IP Transport" if "Transport" in affected_service else "Mobile Core")
        if aff_dom != primary_domain:
            domain_attribution_domains.append({
                "domain_id": _to_domain_id(aff_dom),
                "display_name": aff_dom,
                "role": "AFFECTED",
                "attribution_basis": "IMPACT",
                "confidence": 45,
                "reason": f"Service impact evidence admitted for {affected_service}.",
                "supporting_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else ["HYP-001"],
                "supporting_evidence_ids": supporting_evidence_ids[:2],
                "supporting_pathway_ids": ["PW-002"],
                "source_revision": rev,
            })

    if len(display_domains) > 1:
        for domain in display_domains[1:]:
            if domain != primary_domain and not any(d.get("display_name") == domain for d in domain_attribution_domains):
                domain_attribution_domains.append({
                    "domain_id": _to_domain_id(domain),
                    "display_name": domain,
                    "role": "CONTRIBUTING" if is_ready else "INVOLVED",
                    "attribution_basis": "DEPENDENCY",
                    "confidence": 62 if is_ready else 30,
                    "reason": f"Backend reasoning marked {domain} relevant to active failure path.",
                    "supporting_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else ["HYP-001"],
                    "supporting_evidence_ids": supporting_evidence_ids[:2],
                    "supporting_pathway_ids": [],
                    "source_revision": rev,
                })

    attr_status = "CONSISTENT" if is_ready else ("PARTIAL" if stage_index >= 2 else "UNRESOLVED")

    domain_attribution = {
        "id": "ATTR-001",
        "scenario_id": scenario_id,
        "run_id": run_id,
        "revision": rev,
        "sequence": seq,
        "attribution_status": attr_status,
        "status": "READY" if is_ready else "PENDING",
        "primary_domain": primary_domain if is_ready else None,
        "domains": domain_attribution_domains,
        "explain": {
            "what": "Domain responsibility and impact attribution.",
            "why": "Attribution appears after synthesis and validation readiness.",
            "supports": supporting_evidence_ids,
            "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
            "unknown": "Final responsibility awaits validation." if stage_index < 6 else "Attribution is ready for review.",
            "recent": "Primary attribution exposed." if stage_index >= 6 else "Attribution withheld until enough evidence converges.",
        },
    }

    learning_node = {
        "id": "LEARNING-001",
        "scenario_id": scenario_id,
        "run_id": run_id,
        "display_name": "Validated Learning Candidate" if learning and learning.get("enabled") else "No validated learning yet",
        "status": learning.get("status") if learning else "NOT_READY",
        "summary": learning.get("summary") if learning else "Learning is gated by validation.",
        "explain": {
            "what": "Learning eligibility for future investigations.",
            "why": "Learning is created only from validated run state.",
            "supports": supporting_evidence_ids if learning and learning.get("enabled") else [],
            "affects": [],
            "unknown": "Validation must complete before promotion." if not (learning and learning.get("enabled")) else "Candidate still requires governance review.",
            "recent": learning.get("status") if learning else "NOT_READY",
        },
    }

    source_node = {
        "id": source_id,
        "scenario_id": scenario_id,
        "run_id": run_id,
        "display_name": manifest.get("title", scenario_id) if manifest else scenario_id,
        "mode": "OFFLINE_SIMULATION",
        "status": "ACTIVE",
        "context": {
            "service": affected_service,
            "trigger_entity": trigger_entity,
        },
        "explain": {
            "what": "Offline simulation source selected for this run.",
            "why": "The scenario releases deterministic operational evidence without revealing hidden truth.",
            "supports": [],
            "affects": supporting_evidence_ids[:1],
            "unknown": "The source does not determine the root cause.",
            "recent": f"Current stage is {current_stage}.",
        },
    }

    connections: list[dict[str, Any]] = []

    def normalize_relation(relation_type: str) -> str:
        mapping = {
            "EMITS_EVIDENCE": "CONTRIBUTES_TO",
            "AFFECTS_HYPOTHESIS": "SUPPORTS",
            "FEEDS_SYNTHESIS": "SUPPORTS",
            "BLOCKS_OR_QUALIFIES": "REQUIRES",
            "REQUESTS_EVIDENCE": "REQUIRES",
            "RESOLVES_GAP": "RESOLVES",
            "REQUIRES_VALIDATION": "REQUIRES",
            "ENABLES_ATTRIBUTION": "ATTRIBUTES_TO",
            "ENABLES_LEARNING": "SUPPORTS",
        }
        return mapping.get(relation_type, relation_type)

    def normalize_connection_state(state: str) -> str:
        mapping = {
            "SUPPORTS": "SUPPORTING",
            "TESTING": "ACTIVE",
            "OPEN": "BLOCKED",
            "PENDING": "BLOCKED",
            "NOT_READY": "DORMANT",
            "READY": "ACTIVE",
            "COMPLETED": "RESOLVED",
            "ACCEPTED": "CONFIRMED",
        }
        return mapping.get(state, state)

    def add_connection(source: str, target: str, relation_type: str, state: str, reason: str, sequence: int) -> None:
        if not source or not target:
            return
        connection_id = f"CONN-{len(connections) + 1:03d}"
        connections.append({
            "id": connection_id,
            "connection_id": connection_id,
            "scenario_id": scenario_id,
            "run_id": run_id,
            "source_id": source,
            "target_id": target,
            "relation_type": normalize_relation(relation_type),
            "state": normalize_connection_state(state),
            "reason": reason,
            "sequence": sequence,
        })

    for event in evidence_nodes:
        add_connection(source_id, event["id"], "EMITS_EVIDENCE", "ACTIVE", "Simulation emitted admitted operational evidence.", len(connections) + 1)
        category = event.get("category")
        target_pathways = ["PATH-OPERATIONAL-EVIDENCE"]
        if category == "metric":
            target_pathways.append("PATH-TRAFFIC-CAPACITY")
        if category in {"trace", "log"}:
            target_pathways.append("PATH-CONTROL-SIGNALING")
        if category == "change":
            target_pathways.append("PATH-CHANGE-CONFIGURATION")
        if category == "ticket":
            target_pathways.extend(["PATH-SUBSCRIBER-JOURNEY", "PATH-SERVICE-DEPENDENCY"])
        for pathway_id in dict.fromkeys(target_pathways):
            pathway = next((path for path in pathways if path["id"] == pathway_id), None)
            add_connection(
                event["id"],
                pathway_id,
                "CONTRIBUTES_TO",
                pathway.get("status", "DISCOVERED") if pathway else "DISCOVERED",
                pathway.get("activation_reason", "Evidence contributes to this reasoning pathway.") if pathway else "Evidence contributes to this reasoning pathway.",
                len(connections) + 1,
            )

    for pathway in active_pathways:
        target_hypotheses = pathway.get("hypothesis_ids") or ([primary_hypothesis_id] if primary_hypothesis_id and pathway["id"] in {"PATH-OPERATIONAL-EVIDENCE", "PATH-SERVICE-DEPENDENCY"} else [])
        for hyp_id in target_hypotheses:
            add_connection(
                pathway["id"],
                hyp_id,
                "AFFECTS_HYPOTHESIS",
                pathway["status"],
                pathway["activation_reason"],
                len(connections) + 1,
            )

    for hyp in map_hypotheses:
        state = "REJECTED" if hyp["status"] == "REJECTED" else ("SUPPORTS" if hyp["id"] == primary_hypothesis_id else "TESTING")
        add_connection(
            hyp["id"],
            synthesis["id"],
            "FEEDS_SYNTHESIS",
            state,
            hyp["explain"]["why"],
            len(connections) + 1,
        )

    for gap in gaps:
        add_connection(gap["id"], synthesis["id"], "BLOCKS_OR_QUALIFIES", gap["status"], gap["explain"]["why"], len(connections) + 1)
        if gap.get("next_best_evidence_id"):
            add_connection(gap["id"], gap["next_best_evidence_id"], "REQUESTS_EVIDENCE", gap["status"], gap.get("required_evidence") or "Next best evidence required.", len(connections) + 1)

    if primary_action:
        add_connection(primary_action["id"], "PATH-KNOWLEDGE-GAP", "RESOLVES_GAP", primary_action.get("status", "PENDING"), primary_action.get("display_name"), len(connections) + 1)
    add_connection(synthesis["id"], validation["id"], "REQUIRES_VALIDATION", validation["status"], validation["display_name"], len(connections) + 1)
    add_connection(validation["id"], domain_attribution["id"], "ENABLES_ATTRIBUTION", domain_attribution["status"], "Domain attribution follows validation readiness.", len(connections) + 1)
    add_connection(validation["id"], learning_node["id"], "ENABLES_LEARNING", learning_node["status"], learning_node["summary"], len(connections) + 1)

    return {
        "contract_version": 2,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "source_mode": "OFFLINE_SIMULATION",
        "revision": stage_index,
        "sequence": stage_index,
        "stage": current_stage,
        "source": source_node,
        "evidence": evidence_nodes,
        "reasoning_pathways": pathways,
        "connections": connections,
        "hypotheses": map_hypotheses,
        "knowledge_gaps": gaps,
        "next_best_evidence": next_best_actions,
        "synthesis": synthesis,
        "validation": validation,
        "learning": learning_node,
        "domain_attribution": domain_attribution,
        "reasoning_focus": {
            "entity": trigger_display,
            "pathway": "Knowledge Gap" if knowledge_gaps else "Operational Evidence",
            "hypothesis": primary_hypothesis.get("display_name") if primary_hypothesis else None,
            "test": primary_action.get("display_name") if primary_action else None,
            "reason": stage_watchdog.get("blocking_reason") or synthesis_summary,
        },
    }



def build_causal_path(
    
    trigger_entity: str,
    entities: list[dict[str, Any]],
    topology: dict[str, Any],
    stage_vals: dict[str, Any],
    stage_index: int,
) -> list[dict[str, Any]]:
    """Build causal path edges."""
    if stage_index < 2:
        return []
    return topology.get("causal_path", [])



def build_operational_edges(
    
    topology: dict[str, Any],
    hypotheses: list[dict[str, Any]],
    stage_index: int,
) -> list[dict[str, Any]]:
    """Build graph edges for the shared investigation topology."""
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()
    for edge in topology.get("causal_path", []):
        edge_id = f"EDGE-CAUSAL-{edge.get('from')}-{edge.get('to')}"
        seen.add(edge_id)
        edges.append({
            "id": edge_id,
            "from": edge.get("from"),
            "to": edge.get("to"),
            "relation": edge.get("relation", "CAUSES"),
            "role": edge.get("status", "CANDIDATE"),
        })
    for hyp in hypotheses:
        path_entities = hyp.get("path_entity_ids", [])
        path_edges = hyp.get("path_edge_ids", [])
        for idx, edge_id in enumerate(path_edges):
            if idx + 1 >= len(path_entities) or edge_id in seen:
                continue
            seen.add(edge_id)
            edges.append({
                "id": edge_id,
                "from": path_entities[idx],
                "to": path_entities[idx + 1],
                "relation": "CANDIDATE_CAUSE" if idx == 0 else "IMPACTS",
                "role": hyp.get("path_role", "CANDIDATE"),
                "hypothesis_id": hyp.get("id"),
            })
    if stage_index >= 5:
        edges.append({
            "id": "EDGE-FRONTIER-001",
            "from": hypotheses[0].get("path_entity_ids", [""])[0] if hypotheses else "",
            "to": "FRONTIER-MISSING-EVIDENCE",
            "relation": "REQUIRES_EVIDENCE",
            "role": "UNKNOWN_FRONTIER",
            "hypothesis_id": "HYP-001",
        })
    return [edge for edge in edges if edge.get("from") and edge.get("to")]



def build_hypothesis_paths(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "hypothesis_id": hyp.get("id"),
            "entity_ids": hyp.get("path_entity_ids", []),
            "edge_ids": hyp.get("path_edge_ids", []),
            "role": hyp.get("path_role", "CANDIDATE"),
            "confidence": hyp.get("confidence"),
        }
        for hyp in hypotheses
    ]



def build_evidence_clusters(events: list[dict[str, Any]], stage_index: int) -> list[dict[str, Any]]:
    if stage_index < 2:
        return []
    event_ids = [event.get("event_id") for event in events if event.get("event_id")]
    return [{
        "cluster_id": "EC-001",
        "label": "Temporal dependency cluster",
        "event_ids": event_ids,
        "entity_ids": sorted({event.get("entity_id") for event in events if event.get("entity_id")}),
        "signal_count": len(event_ids),
        "noise_count": 0,
        "confidence": 0.52 if stage_index == 2 else min(0.86, 0.52 + (stage_index - 2) * 0.08),
    }]


