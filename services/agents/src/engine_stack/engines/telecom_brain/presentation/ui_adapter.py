"""Standard UI Presentation Adapter for FikraCore Simulator.

Enforces unified presentation contract (§Standard UI Presentation Model) powering:
- Investigation Mode (detailed engineering drilldown)
- Curated Demo Mode (leadership walkthrough, step-by-step reveal)
using the exact same underlying scenario, evidence, and reasoning state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
import yaml

from .naming import default_naming_resolver
from ..investigation.contracts import (
    InvestigationResult,
    StandardPresentationModel,
)


def build_ui_presentation_model(
    result: InvestigationResult,
    scenario_path: Path | str,
    mode: Literal["INVESTIGATION", "DEMO"] = "INVESTIGATION",
    current_step: int = 1,
) -> StandardPresentationModel:
    """Build the unified UI presentation model from investigation result and scenario files."""
    run_dir = Path(scenario_path)
    demo_file = run_dir / "demo_metadata.yaml"
    demo_meta: dict[str, Any] = {}
    if demo_file.exists():
        with open(demo_file) as f:
            demo_meta = yaml.safe_load(f).get("demo", {})

    manifest_file = run_dir / "scenario_manifest.yaml"
    manifest: dict[str, Any] = {}
    if manifest_file.exists():
        with open(manifest_file) as f:
            manifest = yaml.safe_load(f)

    # 1. Scenario Block
    scenario_id = result.scenario_id
    title = demo_meta.get("title", f"Investigation Scenario {scenario_id}")
    objective = demo_meta.get("learning_objective", "Causal RCA & Knowledge-Gap Discovery")
    scenario_block = {
        "id": scenario_id,
        "run_id": result.run_id,
        "title": title,
        "stage": "H2" if "H2" in scenario_id else "H1",
        "objective": objective,
        "difficulty": manifest.get("difficulty_profile", "K1"),
        "demo_metadata": demo_meta if demo_meta else None,
    }

    # 2. Impact Block
    impacted_services = [result.diagnostics.get("impacted_service")] if result.diagnostics.get("impacted_service") else ["5g_sa_mobile_data"]
    impact_summary = (
        f"Degradation observed on {', '.join(impacted_services)} with "
        f"{result.diagnostics.get('input_evidence_count', 0)} operational telemetry signals."
    )
    impact_block = {
        "summary": impact_summary,
        "affected_services": impacted_services,
        "affected_entity_count": len(result.canonical_entities_used),
    }

    # 3. Timeline Block
    timeline: list[dict[str, Any]] = []
    evidence_items = result.metadata.get("evidence", [])
    for ev in evidence_items[:20]:  # Limit for UI presentation
        entity_name = default_naming_resolver.to_display_name(ev.get("canonical_entity", ""))
        evidence_label = default_naming_resolver.to_evidence_label(ev.get("evidence_type", ""))
        timeline.append({
            "evidence_id": ev.get("evidence_id"),
            "timestamp": ev.get("event_time"),
            "entity": entity_name,
            "canonical_id": ev.get("canonical_entity"),
            "evidence_label": evidence_label,
            "signal": ev.get("signal"),
            "severity": ev.get("severity"),
            "polarity": ev.get("polarity"),
        })
    timeline.sort(key=lambda t: str(t.get("timestamp", "")))

    # 4. Topology Block
    visible_entities = [
        default_naming_resolver.format_entity(e) for e in result.canonical_entities_used
    ]
    visible_relationships = []
    for r in result.metadata.get("relationships", []):
        src_name = default_naming_resolver.to_display_name(r.get("source", ""))
        tgt_name = default_naming_resolver.to_display_name(r.get("target", ""))
        rel_label = default_naming_resolver.to_relation_label(r.get("link_type", "depends-on"))
        visible_relationships.append({
            "relationship_id": r.get("relationship_id"),
            "source": src_name,
            "target": tgt_name,
            "relation": rel_label,
            "state": r.get("state"),
            "canonical_source": r.get("source"),
            "canonical_target": r.get("target"),
        })

    gap_records = result.diagnostics.get("knowledge_gap_records", [])
    gap_boundary = None
    if gap_records:
        raw_b = gap_records[0].get("suspected_missing_relation", {}).get("from_entity")
        if raw_b:
            gap_boundary = default_naming_resolver.format_entity(raw_b)

    topology_block = {
        "visible_entities": visible_entities,
        "visible_relationships": visible_relationships,
        "highlighted_path": [e["display_name"] for e in visible_entities[:3]],
        "gap_boundary": gap_boundary,
    }

    # 5. Reasoning Block
    hypotheses_ui = []
    for h in result.ranked_hypotheses[:5]:
        root_name = default_naming_resolver.to_display_name(h.candidate_root_entity)
        hypotheses_ui.append({
            "hypothesis_id": h.hypothesis_id,
            "candidate_root": root_name,
            "canonical_root": h.candidate_root_entity,
            "confidence": h.hypothesis_confidence,
            "causal_confidence": h.causal_confidence,
            "explanation_coverage": h.explanation_coverage,
            "status": h.status.value,
            "assumptions": [a.model_dump(mode="json") for a in h.assumptions],
        })

    reasoning_block = {
        "terminal_state": result.terminal_state.value,
        "confidence": result.ranked_hypotheses[0].hypothesis_confidence if result.ranked_hypotheses else 0.0,
        "explanation": result.reasoning_summary,
        "hypotheses": hypotheses_ui,
        "unexplained_residual": result.diagnostics.get("unexplained_residuals", []),
        "knowledge_gaps": gap_records,
    }

    # 6. Next-Best-Evidence Block
    nbe_ui = []
    for req in result.next_best_evidence:
        target_names = [default_naming_resolver.to_display_name(t) for t in req.target_entities]
        nbe_ui.append({
            "request_id": req.request_id,
            "question": req.question,
            "targets": target_names,
            "information_gain": req.information_gain,
            "priority": req.priority,
            "cost": req.cost,
            "risk": req.risk,
        })

    # 7. Candidate Knowledge Block
    candidate_ui = []
    for c in result.candidate_relationships:
        src_name = default_naming_resolver.to_display_name(c.source)
        tgt_name = default_naming_resolver.to_display_name(c.target)
        rel_label = default_naming_resolver.to_relation_label(c.proposed_type)
        candidate_ui.append({
            "candidate_id": c.candidate_id,
            "source": src_name,
            "target": tgt_name,
            "proposed_relation": rel_label,
            "canonical_source": c.source,
            "canonical_target": c.target,
            "state": c.state.value,
            "reason": c.reason,
            "supporting_evidence": c.supporting_evidence,
        })

    # 8. Validation Block
    validation_block = {
        "state": "PENDING" if candidate_ui else "NOT_REQUIRED",
        "pending_candidates": [c["candidate_id"] for c in candidate_ui],
        "allowed_actions": ["ACCEPT", "REJECT", "MODIFY", "NEED_MORE_EVIDENCE"],
    }

    # Check for H3 learning unit files
    learning_block = None
    h3_unit_dir = run_dir if (run_dir / "learning_unit_manifest.yaml").exists() else run_dir.parent if (run_dir.parent / "learning_unit_manifest.yaml").exists() else None
    if h3_unit_dir:
        lu_manifest_path = h3_unit_dir / "learning_unit_manifest.yaml"
        cand_path = h3_unit_dir / "candidate_knowledge.yaml"
        val_path = h3_unit_dir / "validation_decision.yaml"

        lu_manifest = {}
        if lu_manifest_path.exists():
            with open(lu_manifest_path) as f:
                lu_manifest = yaml.safe_load(f) or {}

        cands = []
        if cand_path.exists():
            with open(cand_path) as f:
                c_data = yaml.safe_load(f)
                if c_data:
                    cands.append(c_data)

        vals = []
        if val_path.exists():
            with open(val_path) as f:
                v_data = yaml.safe_load(f)
                if v_data:
                    vals.append(v_data)

        promoted_rels = []
        if lu_manifest.get("validated_relation"):
            promoted_rels.append(lu_manifest["validated_relation"])

        # Reused knowledge in top hypothesis
        reused = []
        if result.ranked_hypotheses:
            top_h = result.ranked_hypotheses[0]
            reused = [r for r in top_h.knowledge_relationships_used if "PROM" in r or "H3" in r]

        cov = result.ranked_hypotheses[0].explanation_coverage if result.ranked_hypotheses else 0.0
        learning_block = {
            "candidate_knowledge": cands,
            "validation_decisions": vals,
            "promoted_knowledge": promoted_rels,
            "before_snapshot": {"topology_visible": op_topo.get("visible_relationships", []) if 'op_topo' in locals() else []},
            "after_snapshot": {"relationships_active": len(promoted_rels)},
            "reused_knowledge": reused,
            "performance_delta": {
                "coverage": cov,
                "terminal_state": result.terminal_state.value,
                "rank_improvement": 1 if result.ranked_hypotheses and result.ranked_hypotheses[0].canonical_root_entity else 0,
            },
            "contradictions": [item for item in result.contradicting_evidence],
            "learning_ledger": [
                {
                    "action": "PROMOTION",
                    "unit_id": lu_manifest.get("learning_unit_id", scenario_id),
                    "status": "APPLIED",
                }
            ] if promoted_rels else [],
        }

    is_h3 = bool(learning_block or "H3" in scenario_id)
    if is_h3:
        scenario_block["stage"] = "H3"

    # 9. Presentation Block (Mode & Step Aware)
    default_steps = [
        "Step 1 — Incident A exposes a knowledge gap",
        "Step 2 — FikraCore proposes candidate knowledge",
        "Step 3 — SME validates it",
        "Step 4 — Knowledge is safely promoted",
        "Step 5 — Different Incident B occurs",
        "Step 6 — FikraCore reuses the validated knowledge",
        "Step 7 — Future investigation improves",
    ] if is_h3 else [
        "Observe operational evidence",
        "Trace known topology",
        "Evaluate competing causal hypotheses",
        "Identify model insufficiency and knowledge gap boundary",
        "Request utility-ranked next evidence",
        "Propose candidate relationship for SME validation",
    ]
    demo_steps = demo_meta.get("steps", default_steps)
    clamped_step = max(1, min(current_step, len(demo_steps)))
    step_headline = demo_steps[clamped_step - 1] if demo_steps else "Investigation State"

    default_msg = "FikraCore learns from validated operational experience." if is_h3 else "FikraCore recognizes when its network knowledge is incomplete."
    if mode == "DEMO":
        headline = f"Step {clamped_step}/{len(demo_steps)}: {step_headline}"
        key_message = demo_meta.get("final_message", default_msg)
    else:
        headline = f"Operational Investigation: {scenario_id} [{result.terminal_state.value}]"
        key_message = result.reasoning_summary

    presentation_block = {
        "active_mode": mode,
        "current_step": clamped_step,
        "total_steps": len(demo_steps),
        "available_steps": demo_steps,
        "headline": headline,
        "key_message": key_message,
        "technical_details_available": True,
    }

    return StandardPresentationModel(
        scenario=scenario_block,
        impact=impact_block,
        timeline=timeline,
        topology=topology_block,
        reasoning=reasoning_block,
        next_best_evidence=nbe_ui,
        candidate_knowledge=candidate_ui,
        validation=validation_block,
        presentation=presentation_block,
        learning=learning_block,
    )


def build_ui_presentation_model_h4(
    what_if_result: Any,
    scenario_path: Path | str,
    mode: Literal["INVESTIGATION", "DEMO"] = "INVESTIGATION",
    current_step: int = 1,
) -> StandardPresentationModel:
    """Build unified UI presentation model for H4 Proactive What-If simulation results."""
    run_dir = Path(scenario_path)
    demo_file = run_dir / "demo_metadata.yaml"
    demo_meta: dict[str, Any] = {}
    if demo_file.exists():
        with open(demo_file, "r", encoding="utf-8") as f:
            demo_meta = yaml.safe_load(f).get("demo", {})

    manifest_file = run_dir / "scenario_manifest.yaml"
    manifest: dict[str, Any] = {}
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

    scenario_id = what_if_result.what_if_id
    title = demo_meta.get("title", manifest.get("title", f"What-If Resilience: {scenario_id}"))

    scenario_block = {
        "id": scenario_id,
        "run_id": f"RUN-{scenario_id}",
        "title": title,
        "stage": "H4",
        "objective": "Forward Causal Propagation & Critical Failure Surface Discovery",
        "difficulty": "L1",
        "demo_metadata": demo_meta if demo_meta else None,
    }

    impact_block = {
        "summary": what_if_result.blast_radius.customer_facing_impact,
        "affected_services": what_if_result.blast_radius.affected_services,
        "affected_entity_count": (
            len(what_if_result.blast_radius.directly_affected_entities)
            + len(what_if_result.blast_radius.indirectly_affected_entities)
            + 1
        ),
    }

    # Timeline (Simulation events / sequence)
    timeline: list[dict[str, Any]] = [
        {
            "step": 1,
            "entity": what_if_result.trigger.entity_display_name,
            "event": f"Hypothetical {what_if_result.trigger.event_type}",
            "severity": what_if_result.trigger.severity,
        }
    ]

    # Topology
    topology_block = {
        "trigger_node": what_if_result.trigger.entity_display_name,
        "directly_affected": what_if_result.blast_radius.directly_affected_entities,
        "indirectly_affected": what_if_result.blast_radius.indirectly_affected_entities,
        "blast_radius_level": what_if_result.blast_radius.blast_radius_level.value,
        "visible_entities": [
            {"canonical_id": what_if_result.trigger.canonical_id, "display_name": what_if_result.trigger.entity_display_name}
        ] + [
            {"canonical_id": e, "display_name": default_naming_resolver.to_display_name(e)}
            for e in (what_if_result.blast_radius.directly_affected_entities + what_if_result.blast_radius.indirectly_affected_entities)
        ],
    }

    # Reasoning / Causal Propagation
    reasoning_block = {
        "terminal_state": what_if_result.terminal_state.value,
        "propagation_path_count": len(what_if_result.propagation_paths),
        "confidence": what_if_result.confidence,
        "summary": what_if_result.blast_radius.customer_facing_impact,
    }

    # Resilience Block (§53)
    resilience_block = {
        "what_if": what_if_result.trigger.model_dump(),
        "propagation_paths": [
            [step.model_dump() for step in path] for path in what_if_result.propagation_paths
        ],
        "blast_radius": what_if_result.blast_radius.model_dump(),
        "affected_services": what_if_result.blast_radius.affected_services,
        "critical_failure_surfaces": [c.model_dump() for c in what_if_result.critical_failure_surfaces],
        "resilience_gaps": [g.model_dump() for g in what_if_result.resilience_gaps],
        "mitigation_options": [m.model_dump() for m in what_if_result.mitigation_options],
        "recommended_actions": [r.model_dump() for r in what_if_result.recommended_actions],
        "confidence": what_if_result.confidence,
        "knowledge_limitations": what_if_result.knowledge_limitations,
    }

    # 7-Step Curated Demo steps for H4 (§49)
    default_h4_steps = [
        "Step 1 — Select a critical component",
        "Step 2 — Ask 'What if this fails?'",
        "Step 3 — Show forward propagation",
        "Step 4 — Show affected services",
        "Step 5 — Reveal shared dependency / resilience gap",
        "Step 6 — Compare mitigation options",
        "Step 7 — Show recommended resilience action",
    ]
    demo_steps = demo_meta.get("steps", default_h4_steps)
    clamped_step = max(1, min(current_step, len(demo_steps)))
    step_headline = demo_steps[clamped_step - 1] if demo_steps else "Proactive Resilience Simulation"

    key_msg = demo_meta.get(
        "final_message",
        "FikraCore uses validated operational knowledge to identify risk before failure occurs.",
    )
    if mode == "DEMO":
        headline = f"Step {clamped_step}/{len(demo_steps)}: {step_headline}"
    else:
        headline = f"Proactive Resilience: {scenario_id} [{what_if_result.terminal_state.value}]"

    presentation_block = {
        "active_mode": mode,
        "current_step": clamped_step,
        "total_steps": len(demo_steps),
        "available_steps": demo_steps,
        "headline": headline,
        "key_message": key_msg,
        "technical_details_available": True,
    }

    return StandardPresentationModel(
        scenario=scenario_block,
        impact=impact_block,
        timeline=timeline,
        topology=topology_block,
        reasoning=reasoning_block,
        next_best_evidence=[],
        candidate_knowledge=[],
        validation={},
        presentation=presentation_block,
        learning=None,
        resilience=resilience_block,
    )


__all__ = [
    "build_ui_presentation_model",
    "build_ui_presentation_model_h4",
]

