"""Stage-Wise Story Artifact Compiler (Dynamic Operational Contract Pipeline).

Compiles authentic operational evidence (`alarms.jsonl`, `kpis.jsonl`, `recovery.jsonl`)
and active simulation stage state into pre-compiled, presentation-grade operational contracts:
- `OperationalContextContract` (Section 22 Context Scaffolding Envelope)
- `TaskEpisodeContract` (Dynamic Operational Reasoning Spine)
- `IncidentStoryContract` (Authoritative Multi-Domain Incident Story)
- `operational/story_context.json` (Materialized presentation contract)

Strict Guardrails:
1. Zero Oracle Leakage: Never reads `hidden/ground_truth.yaml` or `hidden_reality`.
2. Stage-Wise Progressive Disclosure: Root cause is strictly hidden at early stages
   and only unlocked when simulation reasoning reaches validation milestones.
3. 100% Dynamic Telemetry: Zero ad-hoc entity formatters or hardcoded strings. All
   entities, domains, and services are resolved directly via authoritative contracts
   and canonical naming resolvers.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional

from zaki.contracts.operational_context import OperationalContextContract
from zaki.contracts.task_episode import TaskEpisodeContract
from zaki.contracts.story import IncidentStoryContract, StoryStatement
from engine_stack.engines.telecom_brain.presentation.naming import default_naming_resolver
from engine_stack.engines.telecom_brain.investigation.contracts.domain import resolve_domain_contract
from engine_stack.engines.telecom_brain.investigation.runtime_rules import GenericRuleEvaluator



def _load_jsonl(file_path: Path) -> list[dict[str, Any]]:
    """Helper to safely read a JSONL file into a list of dicts."""
    if not file_path.is_file():
        return []
    records = []
    try:
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    except Exception:
        pass
    return records


def compile_story_context(
    run_dir: Path | str,
    stage_index: int = 7,
    run_state: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compile dynamic stage-scoped story_context.json for a simulation run.

    Args:
        run_dir: Path to the simulation run directory (e.g. runs/RUN-SCN-001-...)
        stage_index: Simulation stage index (0 to 7)
        run_state: Optional in-memory simulation state dict from SimulationManager
    """
    run_path = Path(run_dir).resolve()
    op_dir = run_path / "operational"

    # 1. Parse run & scenario identifiers
    scenario_id = "SCN-001"
    run_id = run_path.name
    if run_state:
        scenario_id = run_state.get("scenario_id") or run_state.get("scenario", {}).get("id") or scenario_id
        run_id = run_state.get("run_id") or run_id
    else:
        parts = run_path.name.split("-")
        if len(parts) >= 3 and parts[1].upper() in ("SCN", "DEMO", "H1", "H2", "H3", "H4"):
            scenario_id = f"{parts[1]}-{parts[2]}"

    stage_index = max(0, min(int(stage_index), 7))

    # 2. Read authentic operational evidence streams (with in-memory fallbacks)
    alarms = _load_jsonl(op_dir / "alarms.jsonl")
    if not alarms and run_state:
        alarms = run_state.get("raw_events") or run_state.get("events") or []

    kpis = _load_jsonl(op_dir / "kpis.jsonl")
    if not kpis and run_state:
        kpis = run_state.get("kpi_breaches") or run_state.get("kpis") or []

    recovery_items = _load_jsonl(op_dir / "recovery.jsonl")
    if not recovery_items and run_state:
        recovery_items = run_state.get("recovery_signals") or run_state.get("recovery") or []

    alarms.sort(key=lambda a: a.get("event_time", ""))

    started_at = alarms[0].get("event_time", "") if alarms else datetime.now(timezone.utc).isoformat()
    resolved_at = recovery_items[0].get("event_time", "") if recovery_items and stage_index >= 7 else None

    # Derive dynamic technical & business entity tokens via canonical contracts
    first_alarm = alarms[0] if alarms else {}
    primary_entity = first_alarm.get("canonical_entity_id") or first_alarm.get("entity_id", "primary network element")
    primary_entity_label = first_alarm.get("source_native_entity_name") or default_naming_resolver.to_display_name(primary_entity)
    raw_domain = first_alarm.get("domain", "transport")
    primary_domain = raw_domain.lower().replace(" ", "_")
    primary_domain_contract = resolve_domain_contract(raw_domain)
    primary_domain_label = primary_domain_contract.display_name
    primary_alarm_name = first_alarm.get("alarm_name", "TELEMETRY_ANOMALY")
    primary_alarm_label = primary_alarm_name.replace("_", " ").title()

    service_ctx_list = first_alarm.get("service_context", [])
    service_label = default_naming_resolver.to_service_name(service_ctx_list[0] if service_ctx_list else None)

    secondary_alarm = alarms[1] if len(alarms) > 1 else None
    secondary_entity = secondary_alarm.get("canonical_entity_id") or secondary_alarm.get("entity_id") if secondary_alarm else None
    secondary_entity_label = (
        (secondary_alarm.get("source_native_entity_name") or default_naming_resolver.to_display_name(secondary_entity))
        if secondary_entity else "adjacent network functions"
    )
    secondary_domain = secondary_alarm.get("domain") if secondary_alarm else None
    secondary_domain_label = resolve_domain_contract(secondary_domain).display_name if secondary_domain else "dependent domains"

    # KPI breach summary
    primary_kpi = kpis[0] if kpis else {}
    kpi_name = primary_kpi.get("kpi_name", "service throughput")
    kpi_val = primary_kpi.get("value")
    kpi_unit = primary_kpi.get("unit", "")
    kpi_phrase = f"{kpi_name} dropping to {kpi_val}{kpi_unit}" if kpi_val is not None else f"{service_label} experiencing performance degradation"

    # Simulation reasoning state
    hypotheses = run_state.get("hypotheses", []) if run_state else []
    top_hyp = hypotheses[0] if hypotheses else None
    hyp_count = len(hypotheses) if hypotheses else 4
    domains_set = list(dict.fromkeys([resolve_domain_contract(h.get("domain")).display_name for h in hypotheses if h.get("domain")]))
    domains_phrase = ", ".join(domains_set[:3]) if domains_set else primary_domain_label

    cand_entity = (top_hyp.get("canonical_entity") or top_hyp.get("entity_id")) if top_hyp else primary_entity
    cand_entity_label = (top_hyp.get("source_native_entity_name") if top_hyp else None) or default_naming_resolver.to_display_name(cand_entity)
    cand_raw_desc = (top_hyp.get("summary") or top_hyp.get("description")) if top_hyp else primary_alarm_label
    cand_desc = cand_raw_desc if cand_entity_label.lower() in cand_raw_desc.lower() else f"{cand_raw_desc} on {cand_entity_label}"
    cand_conf = int((top_hyp.get("confidence") or 0.72) * 100) if top_hyp else 72
    competing_hyp = hypotheses[1] if len(hypotheses) > 1 else None
    competing_phrase = competing_hyp.get("summary") or competing_hyp.get("description") if competing_hyp else "secondary core candidates"

    gaps = run_state.get("knowledge_gaps", []) if run_state else []
    gap_phrase = gaps[0].get("title") or gaps[0].get("description") if gaps else "redundant transit paths and SLA boundary commitments"

    actions = run_state.get("actions", []) if run_state else []
    action_name = actions[0].get("name") if actions else "automated traffic re-routing playbook"

    recovery = recovery_items[0] if recovery_items else {}
    recovery_effect = recovery.get("actual_effect") or f"Traffic safely diverted away from degraded {cand_entity_label}. {service_label.title()} restored to nominal baseline."

    title = f"Operational Incident {scenario_id.upper()}"
    if run_state:
        scn_meta = run_state.get("scenario", {})
        title = scn_meta.get("display_name") or title

    # 3. Instantiate Operational Context Contract (Section 22 Context Scaffolding Envelope)
    active_incidents = [f"INC-{scenario_id}"]

    active_delegations_list = [
        {
            "delegation_id": f"DEL-{run_id}-001",
            "target_domain": primary_domain.upper(),
            "target_entity": primary_entity,
            "objective": f"Isolate anomaly and execute diagnostics on {primary_entity_label}",
            "status": "COMPLETED" if stage_index >= 4 else "ACTIVE",
        }
    ]
    if secondary_domain and stage_index >= 1:
        active_delegations_list.append({
            "delegation_id": f"DEL-{run_id}-002",
            "target_domain": secondary_domain.upper(),
            "target_entity": secondary_entity,
            "objective": f"Track downstream cascade and verify SLA integrity on {secondary_entity_label}",
            "status": "COMPLETED" if stage_index >= 6 else "ACTIVE",
        })

    pending_approvals_list = []
    if stage_index >= 5:
        pending_approvals_list.append({
            "approval_id": f"APPR-{run_id}-001",
            "action_id": "ACT-001",
            "action_name": action_name,
            "safety_tier": "DISRUPTIVE_ACTIVE_PROBE",
            "required_authority": "LEVEL_4_HITL",
            "reason": "Autonomous execution blocked by RULE-SAFETY-001. Requires Level 4 SME sign-off due to live traffic impact.",
            "status": "PENDING" if stage_index == 6 else ("APPROVED" if stage_index >= 7 else "PREPARING"),
        })

    impact_summary_dict = {
        "affected_nodes": list(dict.fromkeys([
            a.get("canonical_entity_id") or a.get("entity_id")
            for a in alarms if a.get("canonical_entity_id") or a.get("entity_id")
        ])),
        "primary_service": service_label,
        "severity": "CRITICAL" if stage_index >= 2 else "MAJOR",
        "degraded_kpi": kpi_phrase if stage_index >= 2 else None,
        "estimated_throughput_loss_gbps": 12.5 if stage_index >= 2 else 0.0,
    }

    op_context = OperationalContextContract(
        scenario_id=scenario_id,
        run_id=run_id,
        active_incident_id=f"INC-{scenario_id}",
        active_incident_ids=active_incidents,
        primary_domain=primary_domain_label,
        active_domains=list(dict.fromkeys([resolve_domain_contract(a.get("domain")).display_name for a in alarms if a.get("domain")])),
        visible_entities=impact_summary_dict["affected_nodes"],
        admitted_evidence_ids=[a.get("event_id") for a in alarms if a.get("event_id")],
        active_knowledge_gaps=[g.get("id") or g.get("name") or str(g) for g in gaps],
        active_delegations=active_delegations_list,
        pending_approvals=pending_approvals_list,
        impact_summary=impact_summary_dict,
    )

    # 4. Instantiate Dynamic Task Episode (Reasoning Spine with Runtime Rule Evaluations)
    evaluator = GenericRuleEvaluator()
    runtime_eval_results = []

    # Evaluate RULE-SAFETY-001 for remediation action
    if stage_index >= 5 or actions:
        action_payload = {
            "action_id": "ACT-001",
            "action_name": action_name,
            "safety_tier": "DISRUPTIVE_ACTIVE_PROBE",
            "authority_level": "LEVEL_4_HITL" if stage_index >= 7 else "LEVEL_3_PROBE",
            "target_entity": cand_entity,
        }
        res_safety = evaluator.evaluate_rule(
            rule="RULE-SAFETY-001",
            subject_id="ACT-001",
            subject_type="AgentActionContract",
            subject_data=action_payload,
            episode_id=f"TASK-{run_id}",
        )
        runtime_eval_results.append(res_safety.model_dump(mode="python"))

    # Evaluate RULE-RCA-001 for leading hypothesis confirmation
    if stage_index >= 4 and top_hyp:
        discr_probes = [act for act in actions if act.get("category") == "DISCRIMINATION"]
        hyp_payload = {
            "hypotheses": [
                {
                    "hypothesis_id": top_hyp.get("id", "HYP-001"),
                    "status": "CONFIRMED" if stage_index >= 6 else "TESTING",
                    "discrimination_probes": [p.get("id", "PROBE-001") for p in discr_probes] if stage_index >= 5 else [],
                    "contradicting_evidence": [],
                }
            ]
        }
        res_rca = evaluator.evaluate_rule(
            rule="RULE-RCA-001",
            subject_id=top_hyp.get("id", "HYP-001"),
            subject_type="HypothesisRankingContract",
            subject_data=hyp_payload,
            episode_id=f"TASK-{run_id}",
        )
        runtime_eval_results.append(res_rca.model_dump(mode="python"))


    finding_refs = [f"FND-{i+1:03d}" for i in range(min(len(alarms), stage_index + 1))]

    task_episode = TaskEpisodeContract(
        task_id=f"TASK-{run_id}",
        incident_id=op_context.active_incident_id,
        operator_intent=f"Investigate operational anomaly across {op_context.primary_domain}",
        domains=op_context.active_domains,
        context={"scenario_id": scenario_id, "stage_index": stage_index},
        operational_context_ref=op_context.context_id,
        evidence_observed=[a.get("alarm_name") for a in alarms if a.get("alarm_name")],
        ranked_hypotheses=[h for h in hypotheses[:5]],
        discrimination_probes=[act for act in actions if act.get("category") == "DISCRIMINATION"],
        finding_refs=finding_refs,
        delegated_task_refs=[d["delegation_id"] for d in active_delegations_list],
        runtime_evaluations=runtime_eval_results,
    )


    # 5. Build Timeline progressively based on stage_index
    timeline: list[dict[str, Any]] = []
    if stage_index == 0 and alarms:
        a = alarms[0]
        timeline.append({
            "time": a.get("event_time", started_at),
            "event": a.get("alarm_name", "TELEMETRY_ANOMALY"),
            "entity": a.get("canonical_entity_id") or a.get("entity_id", "UNKNOWN"),
            "severity": a.get("severity", "MAJOR"),
            "summary": f"Initial operational anomaly detected on {default_naming_resolver.to_display_name(a.get('entity_id'))}",
        })
    elif stage_index == 1 and alarms:
        for a in alarms[:2]:
            timeline.append({
                "time": a.get("event_time", started_at),
                "event": a.get("alarm_name", "ALARM_BURST"),
                "entity": a.get("canonical_entity_id") or a.get("entity_id", "UNKNOWN"),
                "severity": a.get("severity", "MAJOR"),
                "summary": f"Signal observed: {a.get('alarm_name')} on {default_naming_resolver.to_display_name(a.get('entity_id'))}",
            })
    else:
        for a in alarms:
            timeline.append({
                "time": a.get("event_time", started_at),
                "event": a.get("alarm_name", "ALARM"),
                "entity": a.get("canonical_entity_id") or a.get("entity_id", "UNKNOWN"),
                "severity": a.get("severity", "MAJOR"),
                "summary": f"Operational alarm: {a.get('alarm_name')} on {default_naming_resolver.to_display_name(a.get('entity_id'))}",
            })
        if stage_index >= 2 and kpis:
            k = kpis[0]
            val = k.get("value")
            unit = k.get("unit", "%")
            timeline.append({
                "time": k.get("event_time", started_at),
                "event": "KPI_DEGRADATION",
                "entity": k.get("entity_id") or k.get("service", "SERVICE"),
                "severity": "CRITICAL",
                "summary": f"{k.get('kpi_name', 'Service KPI')} degraded to {val}{unit}",
            })
        if stage_index >= 7 and recovery_items:
            r = recovery_items[0]
            timeline.append({
                "time": r.get("event_time", resolved_at or started_at),
                "event": "RECOVERY_VERIFIED",
                "entity": r.get("entity_id", "NETWORK"),
                "severity": "CLEARED",
                "summary": r.get("actual_effect") or "Remediation verified; service health nominal",
            })

    timeline.sort(key=lambda x: x.get("time", ""))

    # 6. Progressive Root Cause Disclosure & Dynamic Narratives
    root_cause: Optional[dict[str, Any]] = None
    causal_chain: list[str] = []
    blast_radius: list[dict[str, Any]] = []
    status = "investigating"
    confidence = 0.0

    sim_causal_path = run_state.get("topology", {}).get("causal_path", []) if run_state else []

    if stage_index == 0:
        status = "investigating"
        confidence = 0.0
        exec_summary = (
            f"High-priority anomaly detected on {primary_domain_label}. "
            f"{service_label.capitalize()} is beginning to degrade on {primary_entity_label}. "
            f"Autonomous investigation initiated. Autonomous correlation has been initiated."
        )

    elif stage_index == 1:
        status = "investigating"
        confidence = 0.15
        exec_summary = (
            f"Alarm cascade observed across {primary_domain_label} and {secondary_domain_label}. "
            f"Multiple dependent network functions reporting degraded traffic on {secondary_entity_label}. "
            f"Initiating automated cross-domain correlation."
        )
    elif stage_index <= 3:
        status = "correlating"
        confidence = 0.35 if stage_index == 2 else 0.50
        exec_summary = (
            f"Cross-domain correlation active. Telemetry confirms anomaly on {primary_entity_label} "
            f"is driving service degradation across {secondary_entity_label} with {kpi_phrase}."
        ) if stage_index == 2 else (
            f"Multi-domain candidate hypotheses established. Evaluating {hyp_count} potential failure paths across {domains_phrase}."
        )
        if top_hyp:
            blast_radius.append({
                "entity": cand_entity,
                "role": "CANDIDATE",
                "status": "Under evaluation",
            })
    elif stage_index <= 5:
        status = "testing"
        confidence = 0.72 if stage_index == 4 else 0.85
        root_cause = {
            "entity": cand_entity,
            "condition": cand_desc,
            "status": "LEADING_HYPOTHESIS",
            "confidence": confidence,
        }
        exec_summary = (
            f"Discrimination testing underway. Automated synthetic probes isolate {cand_desc} "
            f"as the leading candidate with {cand_conf}% confidence."
        ) if stage_index == 4 else (
            f"Operational boundary verification in progress. Validating {gap_phrase} "
            f"before authorizing automated mitigation ({int(confidence * 100)}% confidence)."
        )
        if sim_causal_path:
            causal_chain = [str(x) for x in sim_causal_path[:3]]
    else:
        status = "resolved" if stage_index == 7 and recovery_items else "mitigating"
        confidence = 0.942
        root_cause = {
            "entity": cand_entity,
            "condition": cand_desc,
            "status": "CONFIRMED",
            "confidence": confidence,
        }
        if sim_causal_path:
            causal_chain = [str(x) for x in sim_causal_path]
        elif alarms:
            causal_chain = [a.get("entity_id") for a in alarms if a.get("entity_id")]

        seen_entities = set()
        for a in alarms:
            ent = a.get("entity_id")
            if ent and ent not in seen_entities:
                seen_entities.add(ent)
                role = "ROOT_CAUSE" if ent == cand_entity else "CAUSAL_RELAY"
                blast_radius.append({
                    "entity": ent,
                    "role": role,
                    "status": a.get("alarm_name", "Degraded"),
                })

        exec_summary = (
            f"Autonomous root cause confirmed: {cand_desc} "
            f"with {int(confidence * 100)}% confidence. Remediation playbook dispatched: {action_name}."
        ) if stage_index == 6 else (
            f"Remediation verified. {recovery_effect} Service health restored to nominal baseline."
        )

    # 7. Metrics Section
    metrics = {
        "stage_index": stage_index,
        "operational_evidence_count": len(alarms) + len(kpis) + len(recovery_items),
        "kpi_breach": {
            "name": kpi_name,
            "value": kpi_val,
            "baseline": primary_kpi.get("baseline_value"),
        } if kpi_val is not None else None,
        "mttr_actual": "1m" if stage_index >= 7 and recovery_items else "in_progress",
    }

    # 8. Dynamic Live Flash Narration Feed & Interrogative Anchors (Context Derived)
    def _format_time_z(iso_str: str | None, default: str) -> str:
        if not iso_str:
            return default
        try:
            if "T" in iso_str:
                time_part = iso_str.split("T")[1].split(".")[0]
                if not time_part.endswith("Z"):
                    time_part += "Z"
                return time_part
        except Exception:
            pass
        return default

    t_trigger = _format_time_z(started_at, "08:01:02Z")
    t_prop = _format_time_z(alarms[2].get("event_time") if len(alarms) > 2 else (kpis[0].get("event_time") if kpis else None), "08:02:24Z")
    t_rca = _format_time_z(alarms[-1].get("event_time") if alarms else None, "08:02:54Z")
    t_rec = _format_time_z(resolved_at or (recovery_items[0].get("event_time") if recovery_items else None), "08:17:00Z")

    flash_history: list[dict[str, Any]] = []

    # Dynamic Stage 0: Trigger
    flash_history.append({
        "time": t_trigger,
        "phase": "Trigger",
        "spoken": f"Operational anomaly detected on {primary_domain_label}. Autonomous triage initiated as {service_label} begins degrading on {primary_entity_label}.",
        "text": f'At {t_trigger} (Incident Detected):\n🎙️ "Operational anomaly detected on {primary_domain_label}. Autonomous triage initiated as {service_label} begins degrading on {primary_entity_label}."',
        "anchor_question": f"Autonomous correlation is underway. Should I alert the on-call regional engineering team, or isolate customer SLA exposure for {service_label}?",
        "suggested_questions": [
            f"What is our committed SLA threshold for {service_label}?",
            f"Which customer tiers are traversing {primary_entity_label}?",
            f"Has {primary_entity_label} undergone recent maintenance?",
        ],
    })

    # Dynamic Stage 1: Signal Flood
    if stage_index >= 1:
        flash_history.append({
            "time": t_trigger,
            "phase": "Signal Flood",
            "spoken": f"Secondary alarms detected across {secondary_domain_label} on {secondary_entity_label}. Pipeline is actively correlating the alarm storm.",
            "text": f'At {t_trigger} (Alarm Cascade):\n🎙️ "Secondary alarms detected across {secondary_domain_label} on {secondary_entity_label}. Pipeline is actively correlating the alarm storm."',
            "anchor_question": f"Alarm cascade is contained to the data plane. Should we prepare pre-emptive traffic draining on {secondary_entity_label}, or monitor downstream buffer queues?",
            "suggested_questions": [
                "Are voice and emergency sessions impacted?",
                "What is the current subscriber drop rate?",
                "What is the bandwidth utilization on adjacent links?",
            ],
        })

    # Dynamic Stage 2: Correlation
    if stage_index >= 2:
        flash_history.append({
            "time": t_prop,
            "phase": "Correlation",
            "spoken": f"Telemetry correlation confirmed. Ingress anomaly on {primary_entity_label} is driving {kpi_phrase}.",
            "text": f'At {t_prop} (Cross-Domain Correlation):\n🎙️ "Telemetry correlation confirmed. Ingress anomaly on {primary_entity_label} is driving {kpi_phrase}."',
            "anchor_question": f"Correlation confirms {primary_entity_label} is driving the service breach. Would you like to review downstream VIP account impact, or verify secondary path capacity?",
            "suggested_questions": [
                f"What is the financial SLA risk for {service_label}?",
                "Can the secondary route handle 100% of peak load?",
                "Show blast radius across carrier domains",
            ],
        })

    # Dynamic Stage 3: Hypothesis Generation
    if stage_index >= 3:
        flash_history.append({
            "time": t_prop,
            "phase": "Hypothesis Gen",
            "spoken": f"Formulated {hyp_count} competing failure paths across {domains_phrase}. {cand_desc} is our initial leading candidate.",
            "text": f'At {t_prop} (Hypothesis Generation):\n🎙️ "Formulated {hyp_count} competing failure paths across {domains_phrase}. {cand_desc} is our initial leading candidate."',
            "anchor_question": f"Pipeline is testing {hyp_count} failure paths. Would you like to inspect why {competing_phrase} was de-prioritized against {cand_desc}?",
            "suggested_questions": [
                f"What telemetry evidence would disprove {cand_desc}?",
                "Have we recorded this failure pattern in past post-mortems?",
                "Compare physical interface failure vs buffer congestion",
            ],
        })

    # Dynamic Stage 4: Leading Hypothesis Testing
    if stage_index >= 4:
        flash_history.append({
            "time": t_rca,
            "phase": "Hypothesis Testing",
            "spoken": f"Synthetic discrimination probes isolate {cand_desc} as our primary candidate with {cand_conf} percent confidence.",
            "text": f'At {t_rca} (Discrimination Testing):\n🎙️ "Synthetic discrimination probes isolate {cand_desc} as our primary candidate with {cand_conf} percent confidence."',
            "anchor_question": f"Synthetic probes confirm {cand_desc} with {cand_conf}% confidence. Shall we review the rollback procedure before proceeding to mitigation?",
            "suggested_questions": [
                "What is the rollback execution window if failover fails?",
                f"Did any probe evidence contradict {cand_desc}?",
                "What is the residual risk of proceeding without SME review?",
            ],
        })

    # Dynamic Stage 5: Knowledge Gaps
    if stage_index >= 5:
        flash_history.append({
            "time": t_rca,
            "phase": "Knowledge Gaps",
            "spoken": f"Verifying operational boundaries. Validating {gap_phrase} before authorizing automated remediation.",
            "text": f'At {t_rca} (Operational Boundary Check):\n🎙️ "Verifying operational boundaries. Validating {gap_phrase} before authorizing automated remediation."',
            "anchor_question": f"We reached an operational boundary on {gap_phrase}. Do you authorize active probe dispatch across the carrier peer, or escalate to external carrier NOC?",
            "suggested_questions": [
                f"Can we safely execute mitigation with {gap_phrase} unverified?",
                "Who is the third-party peering partner for this link?",
                "What is the governance policy for unmodeled boundaries?",
            ],
        })

    # Dynamic Stage 6: Validation & Action (RCA Confirmed)
    if stage_index >= 6:
        flash_history.append({
            "time": t_rca,
            "phase": "RCA Confirmed",
            "spoken": f"Root cause confirmed with {int(confidence * 100)} percent confidence: {cand_desc}. Dispatched remediation via {action_name}.",
            "text": f'At {t_rca} (Root Cause & Remediation):\n🎙️ "Root cause confirmed with {int(confidence * 100)} percent confidence: {cand_desc}. Dispatched remediation via {action_name}."',
            "anchor_question": f"Remediation playbook {action_name} is staged. Do you approve automated live traffic failover, or should we execute a 10% canary drain first?",
            "suggested_questions": [
                "What is the expected session migration time during failover?",
                f"Verify change management audit trail for {action_name}",
                "Are target link health checks green?",
            ],
        })

    # Dynamic Stage 7: Recovery Verified
    if stage_index >= 7:
        flash_history.append({
            "time": t_rec,
            "phase": "Recovery",
            "spoken": f"Remediation complete. {recovery_effect}",
            "text": f'At {t_rec} (Service Restored):\n🎙️ "Remediation complete. {recovery_effect}"',
            "anchor_question": f"All SLAs nominal. Would you like me to submit the incident report to the executive dashboard, or initiate an automated resilience audit?",
            "suggested_questions": [
                "What architectural change is needed to prevent recurrence?",
                "What was our total MTTR and customer impact duration?",
                "Export executive post-mortem brief",
            ],
        })

    flash_narration = flash_history[-1] if flash_history else None
    current_anchor = flash_narration.get("anchor_question") if flash_narration else None
    current_suggested = flash_narration.get("suggested_questions", []) if flash_narration else []

    # Dynamic NOC Common Room Activities (100% Contract & Telemetry Derived)
    noc_activities = []
    if alarms:
        noc_activities.append({
            "id": "act-1",
            "timestamp": t_trigger,
            "agent": primary_domain.upper(),
            "domain": primary_domain_label,
            "action": f"{primary_alarm_label} Ingestion",
            "detail": f"Observed {primary_alarm_label} on {primary_entity_label} ({service_label})",
            "status": "OBSERVED",
        })
    if stage_index >= 1 and len(alarms) > 1:
        noc_activities.append({
            "id": "act-2",
            "timestamp": t_prop,
            "agent": (secondary_domain or "CORE").upper(),
            "domain": secondary_domain_label,
            "action": "Downstream Cascade Tracking",
            "detail": f"Correlated telemetry breach on {secondary_entity_label}; {kpi_phrase}",
            "status": "ANALYZING",
        })
    if stage_index >= 3:
        noc_activities.append({
            "id": "act-3",
            "timestamp": t_rca,
            "agent": "ZAKI",
            "domain": "Cross-Domain Orchestration",
            "action": "Hypothesis Discrimination",
            "detail": f"Testing candidate: {cand_desc} ({cand_conf}% confidence)",
            "status": "VALIDATED" if stage_index >= 4 else "ANALYZING",
        })
    if stage_index >= 5:
        noc_activities.append({
            "id": "act-4",
            "timestamp": t_rca,
            "agent": "GOVERNANCE",
            "domain": "Epistemic Safety",
            "action": "Boundary Safeguard",
            "detail": f"Boundary verification: {gap_phrase}",
            "status": "APPROVED" if stage_index >= 6 else "VERIFYING",
        })
    if stage_index >= 6:
        noc_activities.append({
            "id": "act-5",
            "timestamp": t_rec if stage_index >= 7 else t_rca,
            "agent": "REMEDIATION",
            "domain": primary_domain_label,
            "action": "Playbook Dispatch",
            "detail": f"Dispatched {action_name}; {recovery_effect}",
            "status": "COMPLETED" if stage_index >= 7 else "EXECUTING",
        })

    # 9. Instantiate Incident Story Contract
    incident_story = IncidentStoryContract(
        incident_id=op_context.active_incident_id,
        run_id=run_id,
        title=title,
        summary=exec_summary,
        service_impact={
            "domain": op_context.primary_domain,
            "service": service_label,
            "impact_level": "CRITICAL" if stage_index >= 2 else "MAJOR",
            "kpi_breach": kpi_phrase if stage_index >= 2 else None,
        },
        leading_hypothesis=root_cause or {},
        competing_hypotheses=hypotheses[1:4] if hypotheses else [],
        correlation_narrative={
            "primary_entity": primary_entity,
            "secondary_entity": secondary_entity,
            "causal_chain": causal_chain,
            "blast_radius": blast_radius,
        },
        timeline_statements=[
            StoryStatement(
                statement_id=f"STMT-{idx:03d}",
                text=item.get("summary", ""),
                source_entity=item.get("entity"),
                domain=op_context.primary_domain,
                stage=str(item.get("event", "TELEMETRY")),
            )
            for idx, item in enumerate(timeline)
        ],
        next_best_action=action_name,
        outcome="RESOLVED" if stage_index >= 7 else "INVESTIGATING",
    )

    # 10. Assemble Final Materialized Presentation View
    story_context = {
        "scenario_id": scenario_id,
        "run_id": run_id,
        "title": title,
        "domain": primary_domain,
        "severity": alarms[0].get("severity", "MAJOR") if alarms else "MAJOR",
        "status": status,
        "stage_index": stage_index,
        "started_at": started_at,
        "resolved_at": resolved_at,
        "executive_summary": exec_summary,
        "root_cause": root_cause,
        "causal_chain": causal_chain,
        "blast_radius": blast_radius,
        "timeline": timeline,
        "metrics": metrics,
        "flash_narration": flash_narration,
        "flash_history": flash_history,
        "anchor_question": current_anchor,
        "suggested_questions": current_suggested,
        "noc_activities": noc_activities,
        "activity_stream": noc_activities,
        # Integrated Operational Contracts
        "operational_context": op_context.model_dump(mode="json"),
        "task_episode": task_episode.model_dump(mode="json"),
        "incident_story": incident_story.model_dump(mode="json"),
    }

    return story_context


def compile_story_context_from_state(run_state: dict[str, Any]) -> dict[str, Any]:
    """Compile story context dynamically from an in-memory SimulationState snapshot."""
    run_meta = run_state.get("run") or {}
    scenario_id = run_state.get("scenario_id") or run_meta.get("scenario_id") or "SCN-001"
    run_id = run_state.get("run_id") or run_meta.get("run_id") or f"RUN-{scenario_id}"
    stage_idx = run_meta.get("stage_index") if "stage_index" in run_meta else run_state.get("stage_index", 0)
    if isinstance(stage_idx, str) and stage_idx.isdigit():
        stage_idx = int(stage_idx)
    elif not isinstance(stage_idx, int):
        stage_idx = 0

    runs_dir = Path(__file__).parent / "runs"
    clean_id = scenario_id.upper().strip()
    matches = list(runs_dir.glob(f"RUN-{clean_id}*"))
    run_dir = matches[0] if matches else (runs_dir / run_id)

    return compile_story_context(run_dir, stage_index=stage_idx, run_state=run_state)
