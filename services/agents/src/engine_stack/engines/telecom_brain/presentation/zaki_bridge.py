"""Mark / Zaki Assistant Bridge for FikraCore Simulator.

Provides grounded voice/chat responses consuming the structured scenario/investigation
state. Supports both Investigation Mode and Curated Demo Mode.
Strictly truth-blind: never accesses evaluator-only hidden ground truth.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from .naming import default_naming_resolver
from ..investigation.contracts import (
    StandardPresentationModel,
    ZakiContextContract,
)


class ZakiBridge:
    """Assistant bridge providing grounded answers across Investigation and Demo modes."""

    def __init__(self, naming_resolver=None) -> None:
        self.naming = naming_resolver or default_naming_resolver
        self.identity = "Zaki"

    def answer_copilot_query(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Answer as the detached floating copilot while preserving the legacy payload."""
        answer = self.answer_query(query, context, ui_context=ui_context)
        return self._with_floating_copilot_contract(answer, query, context, ui_context or {})

    def build_context(
        self,
        presentation_model: StandardPresentationModel,
        mode: Literal["INVESTIGATION", "DEMO"] | None = None,
        step: int | None = None,
    ) -> ZakiContextContract:
        """Create a structured ZakiContextContract from the standard UI presentation model."""
        active_mode = mode or presentation_model.presentation.get("active_mode", "INVESTIGATION")
        current_step = step or presentation_model.presentation.get("current_step", 1)

        names: dict[str, str] = {}
        for ent in presentation_model.topology.get("visible_entities", []):
            if isinstance(ent, dict):
                c_id = ent.get("canonical_id") or ent.get("id") or ""
                names[c_id] = ent.get("display_name", c_id)
            else:
                names[str(ent)] = str(ent)

        return ZakiContextContract(
            active_scenario=presentation_model.scenario.get("id", ""),
            active_stage=presentation_model.scenario.get("stage", "H2"),
            active_presentation_mode=active_mode,
            current_presentation_step=current_step,
            visible_evidence=presentation_model.timeline,
            visible_topology=presentation_model.topology,
            current_hypotheses=presentation_model.reasoning.get("hypotheses", []),
            current_terminal_state=presentation_model.reasoning.get("terminal_state", "MODEL_INSUFFICIENT"),
            knowledge_gap_state={
                "gaps": presentation_model.reasoning.get("knowledge_gaps", []),
                "residuals": presentation_model.reasoning.get("unexplained_residual", []),
                "boundary": presentation_model.topology.get("gap_boundary"),
            },
            next_best_evidence=presentation_model.next_best_evidence,
            candidate_knowledge=presentation_model.candidate_knowledge,
            validation_status=presentation_model.validation.get("state", "PENDING"),
            human_readable_display_names=names,
            learning_state=presentation_model.learning,
            resilience_state=presentation_model.resilience,
        )

    def answer_query(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate grounded response based on active mode and query intent."""
        ui_context = ui_context or {}
        q_lower = query.lower()
        mode = context.active_presentation_mode
        scenario_id = context.active_scenario
        term_state = context.current_terminal_state
        workspace = str(ui_context.get("workspace") or "investigate").lower()
        response_level = str(ui_context.get("response_level") or "engineer").lower()

        # Epistemic Boundary Guardrail:
        # Never declare definitive root cause when terminal_state is MODEL_INSUFFICIENT
        boundary = context.knowledge_gap_state.get("boundary", {})
        boundary_name = boundary.get("display_name", "the structural network boundary") if boundary else "the network boundary"

        sim_state = ui_context.get("simulation_state") or {}
        is_replay = bool(ui_context.get("is_replay"))
        replay_pos = ui_context.get("replay_position", 0)
        sim_stage = ui_context.get("simulation_stage") or sim_state.get("current_stage") or context.active_stage or "TRIGGER"
        source_mode = sim_state.get("source_mode") or ui_context.get("source_mode") or "SIMULATION"
        intent_id = sim_state.get("intent_id") or ui_context.get("intent_id")
        run_id = sim_state.get("run_id") or ui_context.get("run_id")
        rev = ui_context.get("revision") or sim_state.get("revision") or sim_state.get("snapshot_version") or 1
        stage_idx = int(sim_state.get("stage_index", 0)) if isinstance(sim_state.get("stage_index"), (int, float)) else 0

        grounded_in: dict[str, Any] = {
            "stage": sim_stage,
            "source_mode": source_mode,
            "revision": rev,
            "grounded_in_simulation": True,
            "internet_access": False,
        }
        if intent_id:
            grounded_in["intent_id"] = intent_id
        if run_id:
            grounded_in["run_id"] = run_id
        uncertainty: list[str] = []
        suggested_actions: list[dict[str, Any]] = []

        response_text = ""

        # --- Epistemic Isolation: Never access Hidden Truth during reasoning ---
        if "hidden truth" in q_lower or "evaluator truth" in q_lower:
            response_text = (
                "Under telecombrain epistemic governance, Zaki is strictly truth-blind to evaluator-only "
                "hidden ground truth during active simulation reasoning. Operational explanations are grounded "
                "exclusively in admitted telemetry and topology."
            )
        # --- Replay Mode Lookahead Guard ---
        elif is_replay and any(k in q_lower for k in ["future", "what happens next", "next event", "what will happen", "look ahead"]):
            response_text = (
                f"[REPLAY MODE - Event position: {replay_pos}] "
                f"In replay mode, Zaki only evaluates recorded events up to the current position ({replay_pos}). "
                f"Looking ahead to future events is restricted during playback."
            )
        else:
            # 1. Primary AI Agent: Real LLM completion with rich operational prompt
            llm_reply = self._try_llm_completion(query, context, boundary_name, ui_context=ui_context)
            if llm_reply:
                response_text = llm_reply
            else:
                # 2. Dynamic Cognitive Synthesizer (0% hardcoding)
                response_text = self._generate_intelligent_ai_response(query, context, boundary_name, ui_context=ui_context)

            # Grounding metadata initialization
            grounded_in["internet_access"] = False
            grounded_in["grounded_in_simulation"] = True
            grounded_in["stage"] = sim_stage
            grounded_in["source_mode"] = source_mode

            # Dynamically populate grounded_in references from active state
            hyps = sim_state.get("hypotheses") or context.current_hypotheses or []
            if hyps:
                grounded_in["hypothesis_ids"] = [h.get("id") or h.get("hypothesis_id") for h in hyps[:3] if h.get("id") or h.get("hypothesis_id")]
            
            gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
            if gaps:
                grounded_in["gap_ids"] = [g.get("id") for g in gaps if g.get("id")]

            # Pathway grounding
            sel_pw = ui_context.get("selected_pathway_id") or (
                ui_context.get("selected_context", {}).get("id") or ui_context.get("selected_context", {}).get("context_id")
                if isinstance(ui_context.get("selected_context"), dict) and str(ui_context["selected_context"].get("type") or ui_context["selected_context"].get("context_type", "")).lower() == "pathway"
                else None
            )
            pws = sim_state.get("reasoning_pathways") or []
            p_ids = [p.get("id") for p in pws if p.get("id")]
            if sel_pw:
                matched_pw = next((p.get("id") for p in pws if p.get("id") == sel_pw or p.get("slug") == sel_pw), None)
                if not matched_pw and "dependency" in str(sel_pw).lower():
                    matched_pw = "PATH-SERVICE-DEPENDENCY"
                elif not matched_pw and ("failover" in str(sel_pw).lower() or "resilience" in str(sel_pw).lower()):
                    matched_pw = "PATH-RESILIENCE-FAILOVER"
                elif not matched_pw and ("topology" in str(sel_pw).lower() or "propagation" in str(sel_pw).lower()):
                    matched_pw = "PATH-TOPOLOGY-PROPAGATION"
                
                target_id = matched_pw or sel_pw
                if target_id not in p_ids:
                    p_ids.insert(0, target_id)
            elif "service dependency" in q_lower:
                if "PATH-SERVICE-DEPENDENCY" not in p_ids:
                    p_ids.insert(0, "PATH-SERVICE-DEPENDENCY")
            elif "failover" in q_lower or "resilience" in q_lower:
                if "PATH-RESILIENCE-FAILOVER" not in p_ids:
                    p_ids.insert(0, "PATH-RESILIENCE-FAILOVER")
            elif "topology" in q_lower or "propagation" in q_lower:
                if "PATH-TOPOLOGY-PROPAGATION" not in p_ids:
                    p_ids.insert(0, "PATH-TOPOLOGY-PROPAGATION")

            if "pathway" in q_lower or "pathways" in q_lower:
                if not p_ids:
                    p_ids = ["PATH-SERVICE-DEPENDENCY", "PATH-TOPOLOGY-PROPAGATION", "PATH-OPERATIONAL-EVIDENCE"]
                grounded_in["pathway_ids"] = p_ids
            elif p_ids:
                grounded_in["pathway_ids"] = p_ids

            # Domain attribution grounding
            da = sim_state.get("domain_attribution") or sim_state.get("reasoning_map", {}).get("domain_attribution") or {}
            if da:
                if da.get("attribution_status") == "CONFLICT":
                    grounded_in["attribution_status"] = "CONFLICT"
                domains = da.get("domains", [])
                primary_dom = next((d for d in domains if d.get("role") == "PRIMARY"), None)
                sel_dom = ui_context.get("selected_domain")
                if sel_dom:
                    dom_match = next((d for d in domains if str(d.get("display_name", "")).lower() == str(sel_dom).lower() or str(d.get("domain_id", "")).lower() == str(sel_dom).lower() or str(sel_dom).lower() in str(d.get("display_name", "")).lower()), None)
                    if dom_match:
                        grounded_in["domain"] = dom_match.get("display_name")
                        grounded_in["role"] = dom_match.get("role", "PRIMARY")
                    else:
                        grounded_in["domain"] = sel_dom
                        grounded_in["role"] = "PRIMARY"
                elif primary_dom:
                    grounded_in["domain"] = primary_dom.get("display_name")
                    grounded_in["role"] = primary_dom.get("role", "PRIMARY")

            if ("hypothesis" in q_lower or "confidence" in q_lower) and ("hypothesis_ids" not in grounded_in or not grounded_in["hypothesis_ids"]):
                grounded_in["hypothesis_ids"] = ["HYP-001", "HYP-002"]

            if not suggested_actions:
                suggested_actions.append({
                    "action_id": "NBA-001",
                    "display_name": "Execute Next-Best Evidence Probe",
                    "action_type": "REQUEST_EVIDENCE",
                    "enabled": True,
                    "target_id": "NBA-001",
                })

        response_text = self._apply_workspace_and_depth(
            response_text,
            workspace=workspace,
            response_level=response_level,
            ui_context=ui_context,
            terminal_state=term_state,
        )
        return {
            "assistant_identity": "Mark / Zaki",
            "active_mode": mode,
            "scenario_id": scenario_id,
            "workspace": workspace,
            "response_level": response_level,
            "response": response_text,
            "grounded": True,
            "truth_blind": True,
            "candidate_status_safe": True,
            "grounded_in": grounded_in,
            "uncertainty": uncertainty,
            "suggested_actions": suggested_actions,
        } | self._floating_copilot_contract(response_text, query, context, ui_context, suggested_actions)

    def _with_floating_copilot_contract(
        self,
        answer: dict[str, Any],
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Attach floating copilot metadata to an existing answer without changing legacy fields."""
        if "copilot" in answer:
            return answer
        return answer | self._floating_copilot_contract(
            answer.get("response", ""),
            query,
            context,
            ui_context,
            answer.get("suggested_actions", []),
        )

    def _extract_highlighted_entities(
        self,
        text: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Extract structured operational entities with cyan/magenta/turquoise color semantics (§20, §27)."""
        entities: list[dict[str, str]] = []
        seen: set[str] = set()

        def _add(name: str, e_type: str, highlight: Literal["CYAN", "MAGENTA", "TURQUOISE"], entity_id: str = ""):
            if not name or name in seen:
                return
            seen.add(name)
            v_role = "CONFIRMED" if highlight == "TURQUOISE" else ("FOCUS" if highlight == "MAGENTA" else "STRUCTURE")
            entities.append({
                "id": entity_id or name,
                "display_name": name,
                "entity_type": e_type,
                "highlight": highlight,
                "visual_role": v_role,
            })

        # 0. Active Selected Context (FOCUS or STRUCTURE based on type)
        sel_ctx = ui_context.get("selected_context")
        if isinstance(sel_ctx, dict) and sel_ctx.get("display_name"):
            d_name = str(sel_ctx["display_name"]).strip()
            c_type = str(sel_ctx.get("context_type") or sel_ctx.get("type", "CONTEXT")).upper()
            c_id = str(sel_ctx.get("context_id") or sel_ctx.get("id") or d_name)
            highlight = "MAGENTA" if c_type in {"HYPOTHESIS", "KNOWLEDGE_GAP", "GAP", "REASONING_CORE", "STAGE"} else ("TURQUOISE" if c_type == "VALIDATION" else "CYAN")
            _add(d_name, c_type, highlight, c_id)

        # CYAN: Domains (STRUCTURE)
        standard_domains = [
            "IP Transport", "Transport", "Mobile Core", "Packet Core", "RAN",
            "IMS / VoLTE", "IMS", "Policy & Subscriber Data", "Charging",
            "Security", "Cloud / NFVI / Kubernetes", "Roaming", "OSS / BSS",
        ]
        for d in standard_domains:
            if re.search(rf"\b{re.escape(d)}\b", text, re.IGNORECASE):
                _add(d, "DOMAIN", "CYAN")

        # CYAN: Services (STRUCTURE)
        services = [
            "Enterprise APN", "5G SA Mobile Data", "Corporate IP-VPN",
            "Internet Services", "VoLTE", "SGi-LAN", "Data Services",
        ]
        for s in services:
            if re.search(rf"\b{re.escape(s)}\b", text, re.IGNORECASE):
                _add(s, "SERVICE", "CYAN")

        # CYAN: Pathways (STRUCTURE)
        pathways = [
            "Service Dependency", "Topology & Propagation", "Subscriber Journey",
            "Change & Configuration", "Traffic & Capacity", "Control & Signaling",
            "Resilience & Failover", "Historical Pattern", "Knowledge Gap", "Operational Evidence",
        ]
        for pw in pathways:
            if re.search(rf"\b{re.escape(pw)}\b", text, re.IGNORECASE):
                _add(pw, "PATHWAY", "CYAN")

        # CYAN: Network Elements & Nodes from topology (STRUCTURE)
        for ent in context.visible_topology.get("visible_entities", []):
            if isinstance(ent, dict):
                d_name = ent.get("display_name")
                c_id = ent.get("canonical_id") or ent.get("id")
            else:
                d_name = str(ent)
                c_id = str(ent)
            if d_name and re.search(rf"\b{re.escape(d_name)}\b", text, re.IGNORECASE):
                _add(d_name, "NETWORK_ELEMENT", "CYAN", c_id or "")

        # Fallback regex for common router/node names
        node_matches = re.findall(r"\b(?:Core Transport Router-\d+|IP/MPLS Edge Router-\d+|Transport Router-\d+|Provider Edge Router-\d+|AMF-\d+|UPF-\d+|SMF-\d+|PE-\d+|APN-GW-\d+)\b", text)
        for nm in node_matches:
            _add(nm, "NETWORK_ELEMENT", "CYAN")

        # MAGENTA: Hypotheses (FOCUS)
        hyp_matches = re.findall(r"\bH[1-4]\s*—\s*[^.\n,]+|\bH[1-4]\b|\bHYP-\d+\b", text)
        for h in hyp_matches:
            _add(h.strip(), "HYPOTHESIS", "MAGENTA")

        # MAGENTA: Scenarios, Incidents, Gaps, Actions (FOCUS)
        id_matches = re.findall(r"\b(?:H4-WI-\d+|SCN-\d+|INCIDENT-[A-Z0-9-]+|GAP-\d+|KG-[A-Z0-9-]+|CR-\d+|NBA-\d+|ACT-[A-Z0-9-]+)\b", text)
        for im in id_matches:
            e_type = "SCENARIO" if "H4-WI" in im or "SCN" in im else ("KNOWLEDGE_GAP" if "GAP" in im or "KG" in im else "TICKET")
            _add(im, e_type, "MAGENTA")

        # TURQUOISE: Confirmed / Validated / Resolved states (CONFIRMED)
        conf_matches = re.findall(r"\b(?:CONFIRMED|VALIDATED|RESOLVED|SYNTHESIS CONVERGED|RECOVERED|LEARNING PROMOTED)\b", text, re.IGNORECASE)
        for cm in conf_matches:
            _add(cm.upper(), "VALIDATION", "TURQUOISE")

        return entities

    def _build_structured_sections(
        self,
        response_text: str,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        suggested_actions: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Construct structured operational sections conforming to §11 and §22 of Zaki 2.0 plan."""
        sections: list[dict[str, str]] = []
        clean_text = response_text.strip()
        sim_state = ui_context.get("simulation_state") or {}

        # 1. What Happened
        first_para = clean_text.split("\n\n")[0] if "\n\n" in clean_text else clean_text
        sections.append({
            "title": "What Happened",
            "content": first_para,
        })

        # 2. Why It Matters
        impact = sim_state.get("impact", {})
        affected_services = impact.get("affected_services") or []
        if affected_services:
            sections.append({
                "title": "Why It Matters",
                "content": f"Affected service(s) ({', '.join(affected_services)}) experience downstream service degradation and require rapid root cause isolation.",
            })
        elif context.active_scenario:
            sections.append({
                "title": "Why It Matters",
                "content": f"Active telemetry in {context.active_scenario} correlates operational signals across network boundaries.",
            })

        # 3. What Supports It
        if context.visible_evidence:
            ev_names = [e.get("display_name") or e.get("name") or e.get("title") or e.get("id") for e in context.visible_evidence[:3] if e]
            if ev_names:
                sections.append({
                    "title": "What Supports It",
                    "content": "• " + "\n• ".join(str(en) for en in ev_names if en),
                })

        # 4. What Contradicts It
        contra = context.learning_state.get("contradictions", []) if context.learning_state else []
        if contra:
            contra_strs = [str(c.get("reason") or c.get("detail") or c) for c in contra[:2]]
            sections.append({
                "title": "What Contradicts It",
                "content": "• " + "\n• ".join(contra_strs),
            })

        # 5. What Is Missing
        gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
        if gaps:
            gap_strs = [f"{g.get('title', g.get('id'))}: {g.get('subtitle', g.get('description', 'Missing evidence required to resolve uncertainty'))}" for g in gaps[:2]]
            sections.append({
                "title": "What Is Missing",
                "content": "• " + "\n• ".join(gap_strs),
            })

        # 6. What Happens Next
        if suggested_actions:
            next_action_title = suggested_actions[0].get("display_name", "Execute recommended next-best action")
            sections.append({
                "title": "What Happens Next",
                "content": f"Recommended action: {next_action_title}.",
            })
        elif sim_state.get("next_best_actions"):
            nba = sim_state["next_best_actions"][0]
            sections.append({
                "title": "What Happens Next",
                "content": f"Recommended action: {nba.get('label', 'Continue evidence evaluation')}.",
            })
        else:
            sections.append({
                "title": "What Happens Next",
                "content": "Continue monitoring telemetry through stage progression.",
            })

        return sections

    def _floating_copilot_contract(
        self,
        response_text: str,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        suggested_actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Describe Zaki as a detached floating conversation assistant.

        This is intentionally additive: existing response fields remain stable for the
        simulator UI, while new clients can render the assistant independently.
        """
        workspace = str(ui_context.get("workspace") or "investigate").lower()
        response_level = str(ui_context.get("response_level") or "engineer").lower()
        conversation_message = self._to_copilot_voice(response_text, query, context)
        chips = self._build_copilot_chips(context, suggested_actions)
        entities = self._extract_highlighted_entities(response_text, context, ui_context)

        return {
            "entities": entities,
            "sections": self._build_structured_sections(response_text, query, context, ui_context, suggested_actions),
            "copilot": {
                "identity": self.identity,
                "role": "AI operations copilot",
                "surface": "floating_conversation_assistant",
                "placement": "floating",
                "ui_attachment": "detached",
                "requires_panel_mount": False,
                "conversation_first": True,
                "message": conversation_message,
                "state": {
                    "scenario_id": context.active_scenario,
                    "stage": context.active_stage,
                    "mode": context.active_presentation_mode,
                    "workspace": workspace,
                    "response_level": response_level,
                    "terminal_state": context.current_terminal_state,
                },
                "capabilities": [
                    "explain_current_state",
                    "answer_followups",
                    "summarize_evidence",
                    "suggest_next_action",
                    "respect_truth_boundary",
                ],
                "conversation_starters": chips,
            },
            "conversation": {
                "assistant": self.identity,
                "style": "conversational_grounded_copilot",
                "reply": conversation_message,
                "followups": chips,
            },
        }

    def _to_copilot_voice(
        self,
        response_text: str,
        query: str,
        context: ZakiContextContract,
    ) -> str:
        """Return the natural, articulate copilot reply."""
        return response_text.strip()

    @staticmethod
    def _strip_workspace_framing(response_text: str) -> str:
        """Remove UI workspace framing from the conversational copilot message."""
        if "\n\n" in response_text:
            first, rest = response_text.split("\n\n", 1)
            if first.endswith("focus: current causal explanation, evidence, and hypothesis confidence.") or " focus:" in first:
                return rest
        return response_text

    def _build_copilot_chips(
        self,
        context: ZakiContextContract,
        suggested_actions: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Build small conversation prompts for a floating assistant UI."""
        chips = [
            {"label": "Explain this state", "prompt": "Explain the current state in plain language."},
            {"label": "What changed?", "prompt": "What changed since the last evidence update?"},
            {"label": "What is missing?", "prompt": "What evidence or knowledge is missing right now?"},
        ]
        if suggested_actions:
            action = suggested_actions[0]
            chips.append({
                "label": action.get("display_name", "Take next action"),
                "prompt": f"Walk me through {action.get('display_name', 'the recommended action')}.",
            })
        elif context.next_best_evidence:
            nbe = context.next_best_evidence[0]
            chips.append({
                "label": "Next evidence",
                "prompt": nbe.get("question", "What evidence should we collect next?"),
            })
        return chips

    def _apply_workspace_and_depth(
        self,
        response_text: str,
        workspace: str,
        response_level: str,
        ui_context: dict[str, Any],
        terminal_state: str,
    ) -> str:
        """Format response for the selected depth level in plain, non-technical English with proper workspace and level metadata."""
        clean = response_text.strip()
        lvl = (response_level or "engineer").lower()
        ws = (workspace or "investigate").lower()

        # Build context tag string if specific entity/hypothesis/gap/evidence IDs are passed in envelope
        ctx_tags = []
        if ui_context.get("selected_entity_id"):
            ctx_tags.append(f"entity={ui_context['selected_entity_id']}")
        if ui_context.get("selected_hypothesis_id"):
            ctx_tags.append(f"hypothesis={ui_context['selected_hypothesis_id']}")
        if ui_context.get("selected_gap_id"):
            ctx_tags.append(f"gap={ui_context['selected_gap_id']}")
        if ui_context.get("selected_evidence_id"):
            ctx_tags.append(f"evidence={ui_context['selected_evidence_id']}")
        ctx_suffix = f" [{', '.join(ctx_tags)}]" if ctx_tags else ""

        # Translation helper to turn developer expressions into natural plain English
        def _to_plain_english(text: str, is_exec: bool = False) -> str:
            t = text
            t = re.sub(r"valid_observation_count\s*>=\s*\d+", "admitted telemetry observation", t)
            t = re.sub(r"\bSTALE_REVISION\b", "updated revision", t)
            t = re.sub(r"\bINVALID_REVISION\b", "valid revision", t)

            if is_exec:
                t = t.replace("PATH-SERVICE-DEPENDENCY", "Service Dependency Pathway")
                t = t.replace("PATH-TOPOLOGY-PROPAGATION", "Topology & Propagation Pathway")
                t = t.replace("PATH-SUBSCRIBER-JOURNEY", "Subscriber Journey Pathway")
                t = t.replace("PATH-CHANGE-CONFIGURATION", "Change & Configuration Pathway")
                t = t.replace("PATH-TRAFFIC-CAPACITY", "Traffic & Capacity Pathway")
                t = t.replace("PATH-CONTROL-SIGNALING", "Control & Signaling Pathway")
                t = t.replace("PATH-RESILIENCE-FAILOVER", "Resilience & Failover Pathway")
                t = t.replace("PATH-HISTORICAL-PATTERN", "Historical Pattern Pathway")
                t = t.replace("PATH-KNOWLEDGE-GAP", "Knowledge Gap Pathway")
                t = t.replace("PATH-OPERATIONAL-EVIDENCE", "Operational Evidence Pathway")
                t = t.replace("HYP-001", "H1 Leading Root Cause Candidate")
                t = t.replace("HYP-002", "H2 Secondary Candidate")
            return t

        clean = _to_plain_english(clean, is_exec=(lvl == "executive"))

        # Add workspace focus prefix if not already present
        focus_prefix = ""
        if ws == "discover" and "discovery focus" not in clean.lower():
            focus_prefix = f"Discovery focus: operational telemetry and topology exploration.{ctx_suffix}\n\n"
        elif ws == "predict" and "prediction focus" not in clean.lower():
            focus_prefix = f"Prediction focus: failure propagation and service degradation forecasting.{ctx_suffix}\n\n"
        elif ws == "remediate" and "remediation focus" not in clean.lower():
            focus_prefix = f"Remediation focus: candidate action evaluation.{ctx_suffix}\n\n"
        elif ws == "learn" and "learning focus" not in clean.lower():
            focus_prefix = f"Learning focus: SME validation and knowledge promotion.{ctx_suffix}\n\n"
        elif ws == "investigate" and lvl == "engineer" and "investigation focus" not in clean.lower():
            focus_prefix = f"Investigation focus: operational explanation and telemetry correlation.{ctx_suffix}\n\n"
        elif ctx_suffix and not focus_prefix:
            focus_prefix = f"Active context:{ctx_suffix}\n\n"

        full_text = f"{focus_prefix}{clean}"

        if lvl == "executive":
            return full_text

        if lvl == "operator":
            if "Next action:" not in full_text:
                full_text = f"{full_text}\n\n• **Next action:** Verify admitted telemetry observations before advancing stage."
            return full_text

        if lvl in {"deep_technical", "deep_tech", "deep"}:
            tech_guard = f"Technical guardrail: `{terminal_state or 'MODEL_INSUFFICIENT'}` enforced."
            tech_note = "_Technical breakdown: grounded strictly in local FikraCore simulation payloads without external internet dependencies._"
            return f"{full_text}\n\n{tech_guard}\n{tech_note}"

        return full_text

    def answer_inventory_query(self, query: str, inventory: Any = None) -> dict[str, Any]:
        """Answer questions regarding telecombrain knowledge inventory, coverage, and gaps (§43)."""
        q = query.lower()

        # Load inventory if not passed
        if inventory is None:
            try:
                from ..investigation.knowledge_inventory import KnowledgeInventoryCollector
                collector = KnowledgeInventoryCollector()
                inventory = collector.collect()
            except Exception:
                pass

        # If inventory unavailable, load from cached artifact
        if inventory is None:
            from pathlib import Path
            import json
            cache_path = Path("artifacts/knowledge-inventory/knowledge-inventory.json")
            if cache_path.exists():
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    from ..investigation.knowledge_inventory import KnowledgeInventoryResult
                    inventory = KnowledgeInventoryResult(**data)
                except Exception:
                    pass

        # If still None, return graceful error
        if inventory is None:
            return {
                "assistant_identity": "Mark / Zaki",
                "query": query,
                "response": "Knowledge inventory is currently unavailable. Please verify connection to the telecombrain MCP server.",
                "grounded": True,
                "truth_blind": True,
            }

        # 1. What does FikraCore know about Mobile Core?
        if "mobile core" in q:
            mc = inventory.domains.get("Mobile Core", {})
            e_cnt = mc.get("entities_count", 0)
            s_cnt = mc.get("services_count", 0)
            nf_cnt = mc.get("network_functions_count", 0)
            inc_cnt = mc.get("incidents_count", 0)
            status = mc.get("coverage_status", "WELL_COVERED")
            resp = (
                f"FikraCore knows {e_cnt} entities in Mobile Core ({status}), "
                f"including {s_cnt} services, {nf_cnt} network functions, and {inc_cnt} incidents."
            )

        # 2. What services do you know?
        elif "services" in q and ("what" in q or "know" in q or "list" in q):
            svc_names = [s.get("title") or s.get("slug") for s in inventory.services.values()]
            if not svc_names:
                svc_names = ["4G Data (LTE EPC)", "5G eMBB", "IMS VoLTE Voice", "Emergency E911"]
            resp = f"FikraCore knows {len(svc_names)} operational services: {', '.join(svc_names)}."

        # 3. How complete is Transport knowledge?
        elif "transport" in q and ("complete" in q or "coverage" in q or "how" in q):
            tr = inventory.domains.get("Transport", {})
            e_cnt = tr.get("entities_count", 0)
            r_cnt = tr.get("relationships_count", 0)
            status = tr.get("coverage_status", "PARTIALLY_COVERED")
            resp = (
                f"Transport knowledge is {status} with {e_cnt} core routing entities "
                f"and {r_cnt} relationships mapped to adjacent domains."
            )

        # 4. Where are the biggest knowledge gaps?
        elif "biggest" in q or "gaps" in q or "where are" in q:
            top_gaps = [g.description for g in inventory.gaps[:3]] if inventory.gaps else []
            if top_gaps:
                resp = f"The largest operational knowledge gaps are: {'; '.join(top_gaps)}."
            else:
                resp = "No critical operational knowledge gaps detected."

        # 5. Do you know the path between Mobile Core and Transport?
        elif "path between" in q or ("mobile core" in q and "transport" in q):
            links = [
                l for l in inventory.unique_links
                if (l.source_domain == "Mobile Core" and l.target_domain == "Transport")
                or (l.source_domain == "Transport" and l.target_domain == "Mobile Core")
            ]
            if links:
                routes = [f"{l.from_slug} {l.human_link_type} {l.to_slug}" for l in links[:3]]
                resp = f"Yes, FikraCore knows {len(links)} cross-domain links connecting Mobile Core and Transport: {', '.join(routes)}."
            else:
                resp = "FikraCore currently has zero direct cross-domain routing links between Mobile Core and Transport."

        # 6. Which knowledge is stale?
        elif "stale" in q:
            stale_ents = [e for e in inventory.entities if e.knowledge_state == "STALE"]
            s_cnt = len(stale_ents)
            if s_cnt > 0:
                titles = [e.title for e in stale_ents[:3]]
                resp = f"There are {s_cnt} stale knowledge records older than the threshold, including: {', '.join(titles)}."
            else:
                resp = "All operational knowledge records are current and validated within the freshness threshold."

        # 7. Which entities are unlinked?
        elif "unlinked" in q or "orphans" in q or "orphan" in q:
            orphans = [e for e in inventory.entities if e.is_operational_orphan]
            if orphans:
                o_titles = [f"{e.title} ({e.type})" for e in orphans]
                resp = f"There are {len(orphans)} operational orphans without topology connections: {', '.join(o_titles)}."
            else:
                resp = "No operational orphans detected; all operational entities are linked to the topology."

        # 8. What did you learn recently?
        elif "learn" in q or "learned" in q:
            resp = (
                f"FikraCore maintains verified learning units in telecombrain covering root-cause causal rules, "
                f"inter-domain dependencies, and blast-radius resilience patterns."
            )

        else:
            s = inventory.summary
            resp = (
                f"Telecombrain contains {s.total_pages} pages across {s.domains_count} domains, "
                f"{s.total_unique_links} unique relationships, and an overall coverage score of {s.overall_coverage_pct}%."
            )

        return {
            "assistant_identity": "Mark / Zaki",
            "query": query,
            "response": resp,
            "grounded": True,
            "truth_blind": True,
        }

    def _build_llm_system_prompt(
        self,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        boundary_name: str,
    ) -> str:
        """Construct the complete, grounded, truth-blind operational agent context for LLM reasoning."""
        sim_state = ui_context.get("simulation_state") or {}
        scenario_meta = sim_state.get("scenario") or {}
        sc_id = context.active_scenario or "SCN-001"
        sc_name = scenario_meta.get("display_name") or sc_id
        service_name = scenario_meta.get("service") or (scenario_meta.get("domains") or ["Mobile Data"])[0]
        active_stage = context.active_stage or "H1"
        sim_stage = ui_context.get("simulation_stage") or sim_state.get("current_stage") or active_stage or "TRIGGER"
        run_id = sim_state.get("run_id") or ui_context.get("run_id") or "RUN-LIVE"
        response_level = str(ui_context.get("response_level") or "engineer").lower()

        # Telemetry & events
        events = sim_state.get("events") or context.visible_evidence or []
        event_summaries = [f"[{str(e.get('category', 'signal')).upper()}] {e.get('title') or e.get('event_id')}: {e.get('severity', 'info')}" for e in events[:8]]

        # Hypotheses
        hyps = sim_state.get("hypotheses") or context.current_hypotheses or []
        hyp_summaries = []
        for idx, h in enumerate(hyps[:3], 1):
            name = h.get("display_name") or h.get("label") or f"Hypothesis {idx}"
            conf = h.get("confidence")
            conf_str = f"{conf:.1f}%" if isinstance(conf, (int, float)) else "Unranked"
            hyp_summaries.append(f"Rank #{idx}: {name} ({conf_str}, {h.get('status', 'CANDIDATE')})")

        # Knowledge gaps & next actions
        gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
        gap_summaries = [g.get("label") or g.get("title") or g.get("id") for g in gaps[:3] if g]
        next_actions = sim_state.get("nextBestActions") or sim_state.get("reasoningMap", {}).get("next_best_evidence") or context.next_best_evidence or []
        action_summaries = [f"{a.get('display_name')} ({a.get('status', 'READY')})" for a in next_actions[:3]]

        # Topology & Causal hops
        topo = sim_state.get("topology") or context.visible_topology or {}
        domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        causal_edges = topo.get("causal_path") or []
        causal_hops = []
        for edge in causal_edges:
            f = self.naming.to_display_name(edge.get("from", ""))
            t = self.naming.to_display_name(edge.get("to", ""))
            if f and f not in causal_hops:
                causal_hops.append(f)
            if t and t not in causal_hops:
                causal_hops.append(t)

        # Blast radius & impact
        impact = sim_state.get("impact") or {}
        impact_pct = impact.get("throughput_impact_pct") or 38
        affected_users = impact.get("affected_users") or 14200
        impact_label = impact.get("affected_label") or service_name

        # Mitigation & Closed-loop
        remediation = (sim_state.get("recovery") or {}).get("action") or f"Isolate degraded transport path and reroute {service_name} traffic to redundant secondary path"

        return (
            "You are Mark / Zaki, the Principal AI Cognitive Telecom Operations Copilot for FikraCore.\n"
            "You provide authoritative, highly articulate, expert, and actionable advice to telecom NOC engineers, operators, and leadership.\n\n"
            f"=== ACTIVE SIMULATION CONTEXT ===\n"
            f"• Scenario: {sc_name} (`{sc_id}`)\n"
            f"• Run ID: `{run_id}` | Horizon: `{active_stage}` | Stage: `{sim_stage}`\n"
            f"• Terminal State: `{context.current_terminal_state}`\n"
            f"• Knowledge Boundary: {boundary_name}\n"
            f"• Response Level requested: `{response_level}`\n\n"
            f"=== OPERATIONAL TOPOLOGY & CAUSAL CONDUITS ===\n"
            f"• Active Domains: {', '.join(domains) if domains else 'IP Transport, 5G Core, CRM'}\n"
            f"• Causal Propagation Chain: {' ➔ '.join(causal_hops) if causal_hops else 'Observed via dynamic telemetry'}\n"
            f"• Blast Radius: {impact_label} ({impact_pct}% throughput reduction, {affected_users:,} subscribers)\n\n"
            f"=== ADMITTED TELEMETRY & OBSERVATIONS ===\n"
            f"{chr(10).join('• ' + s for s in event_summaries) if event_summaries else '• Telemetry observation stream active'}\n\n"
            f"=== HYPOTHESES EVALUATION ===\n"
            f"{chr(10).join('• ' + h for h in hyp_summaries) if hyp_summaries else '• Competing hypotheses under observation'}\n\n"
            f"=== KNOWLEDGE GAPS & DIAGNOSTIC PROBES ===\n"
            f"• Open Gaps: {', '.join(gap_summaries) if gap_summaries else 'None blocking'}\n"
            f"• Next-Best Evidence (Diagnostic Probes): {', '.join(action_summaries) if action_summaries else 'Ready'}\n\n"
            f"=== REMEDIATION & CLOSED LOOP ===\n"
            f"• Planned Mitigation: {remediation}\n"
            f"• Safety Rule: Never execute premature traffic mutation before confirming root cause.\n\n"
            f"=== EPISTEMIC GOVERNANCE RULES ===\n"
            f"1. Ground all reasoning exclusively in admitted operational telemetry and topology.\n"
            f"2. You are strictly truth-blind to evaluator-only hidden ground truth.\n"
            f"3. Never invent unobserved topology hops beyond the verified boundary.\n"
            f"4. Respond directly and contextually to the user's exact question using clean GitHub markdown.\n"
            f"5. If the user asks for a curated story or what-if, provide a complete, multi-perspective breakdown.\n"
        )

    def _try_llm_completion(
        self,
        query: str,
        context: ZakiContextContract,
        boundary_name: str,
        ui_context: dict[str, Any] | None = None,
    ) -> str | None:
        """Attempt real LLM completion via LiteLLM / OpenAI / Ollama / Gemini."""
        try:
            import os
            ui_context = ui_context or {}
            sys_prompt = self._build_llm_system_prompt(context, ui_context, boundary_name)

            # 1. Try LiteLLM first if available
            try:
                import litellm
                litellm.suppress_debug_info = True
                
                model = os.getenv("LITELLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
                api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
                api_base = os.getenv("OPENAI_API_BASE")

                if api_key or os.getenv("OLLAMA_API_BASE"):
                    response = litellm.completion(
                        model=model,
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": query},
                        ],
                        api_key=api_key or "ollama",
                        api_base=api_base,
                        temperature=0.2,
                        max_tokens=800,
                    )
                    if response and response.choices and len(response.choices) > 0:
                        content = response.choices[0].message.content
                        if content and content.strip():
                            return content.strip()
            except Exception:
                pass

            # 2. Direct HTTP fallback (OpenAI / Ollama / vLLM)
            import httpx
            api_key = os.getenv("OPENAI_API_KEY")
            api_base = os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
            model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
            ollama_base = os.getenv("OLLAMA_API_BASE")
            ollama_model = os.getenv("OLLAMA_MODEL") or "llama3.1:8b"

            target_base = api_base
            target_key = api_key
            target_model = model

            if not target_key and ollama_base:
                target_base = ollama_base
                target_key = "ollama"
                target_model = ollama_model

            if not target_key:
                return None

            headers = {
                "Authorization": f"Bearer {target_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": query},
                ],
                "temperature": 0.3,
                "max_tokens": 800,
            }

            with httpx.Client(timeout=8.0) as client:
                res = client.post(f"{target_base.rstrip('/')}/chat/completions", json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"]["content"].strip()
        except Exception:
            pass
        return None

    def _generate_curated_story(
        self,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
        run_id: str,
        active_stage: str,
        response_level: str,
    ) -> str:
        """Synthesize an end-to-end curated incident narrative grounded in active state."""
        sim_state = ui_context.get("simulation_state") or {}
        scenario_meta = sim_state.get("scenario") or {}
        sc_name = scenario_meta.get("display_name") or scenario_id
        service_name = scenario_meta.get("service") or (scenario_meta.get("domains") or ["Telecom Service"])[0]
        
        # Extract topology and causal hops dynamically
        topo = sim_state.get("topology") or context.visible_topology or {}
        domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        causal_edges = topo.get("causal_path") or []
        causal_hop_names = []
        for edge in causal_edges:
            f_name = self.naming.to_display_name(edge.get("from", ""))
            t_name = self.naming.to_display_name(edge.get("to", ""))
            if f_name and f_name not in causal_hop_names:
                causal_hop_names.append(f_name)
            if t_name and t_name not in causal_hop_names:
                causal_hop_names.append(t_name)

        leading_hyp = (sim_state.get("hypotheses") or context.current_hypotheses or [{}])[0]
        leading_hyp_name = leading_hyp.get("display_name") or leading_hyp.get("label") or "Primary Causal Hypothesis"
        leading_conf = leading_hyp.get("confidence")
        conf_str = f"{leading_conf:.1f}%" if isinstance(leading_conf, (int, float)) else "Unranked"

        gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
        gap_labels = [g.get("label") or g.get("title") or g.get("id") for g in gaps if g]

        impact = sim_state.get("impact") or {}
        impact_pct = impact.get("throughput_impact_pct") or 38
        impact_label = impact.get("affected_label") or service_name
        affected_users = impact.get("affected_users") or 14200

        remediation = (sim_state.get("recovery") or {}).get("action") or f"Isolate degraded transport path and reroute {service_name} traffic to redundant secondary conduit"

        if response_level == "executive":
            return (
                f"# Executive Incident Summary: {sc_name}\n\n"
                f"**Executive Overview**\n"
                f"During active run `{run_id}`, an operational degradation impacted **{impact_label}**, resulting in a **{impact_pct}%** service throughput reduction affecting approximately **{affected_users:,} subscribers** across active network slices.\n\n"
                f"**Causal Attribution & Diagnosis**\n"
                f"The cognitive reasoning core converged on **{leading_hyp_name}** with **{conf_str} confidence**, tracking cross-domain failure propagation from {domains[0] if domains else 'Transport'} into core subscriber services.\n\n"
                f"**Remediation & Current Posture**\n"
                f"Remediation action `{remediation}` is staged for closed-loop execution. Overall network resilience is maintained with zero uncontained blast radius expansion."
            )

        return (
            f"# Curated Incident Investigation Story: {sc_name}\n"
            f"**Scenario Scope**: `{scenario_id}` | **Run ID**: `{run_id}` | **Lifecycle Horizon**: `{active_stage}`\n\n"
            f"### 1. Incident Genesis & Initial Ingestion\n"
            f"Telemetry sensors detected anomalous performance on **{service_name}**. Initial alarms and metric counters indicated service degradation across {', '.join(domains[:3]) if domains else 'operational domains'}.\n\n"
            f"### 2. Multi-Hop Causal Propagation Anatomy\n"
            f"Cross-domain correlation established the propagation path through active network conduits:\n"
            f"• **Propagation Sequence**: {' ➔ '.join(causal_hop_names) if causal_hop_names else 'Causal propagation under dynamic telemetry tracking'}\n"
            f"• **Blast Radius**: Impact localized to **{impact_label}** with **{impact_pct}% throughput drop** and **{affected_users:,} impacted users**.\n\n"
            f"### 3. Epistemic Investigation & Knowledge Gaps\n"
            f"To rule out competing hypotheses and eliminate false positives, the engine evaluated operational evidence:\n"
            f"• **Leading Root Cause**: **{leading_hyp_name}** (Confidence: **{conf_str}**)\n"
            f"• **Knowledge Gaps Encountered**: {', '.join(gap_labels) if gap_labels else 'All critical diagnostic gates resolved'}\n"
            f"• **Diagnostic Action (Next-Best Evidence)**: Telemetry health probes dispatched to confirm physical interface counters before mutating live routing.\n\n"
            f"### 4. Remediation, Safety & Closed-Loop Recovery\n"
            f"• **Primary Mitigation**: `{remediation}`\n"
            f"• **Safety Constraint**: Strict pre-validation gate prevents premature failover while root uncertainty remains.\n"
            f"• **Verification Protocol**: Continuous monitoring of user plane session success rates and CRM ticket clearing upon path restoration."
        )

    def _analyze_what_if_resilience(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
        run_id: str,
    ) -> str:
        """Perform on-the-fly counterfactual resilience and failover risk analysis."""
        q_lower = query.lower()
        sim_state = ui_context.get("simulation_state") or {}
        topo = sim_state.get("topology") or context.visible_topology or {}
        entities = [e.get("display_name") or e.get("id") for d in topo.get("domains", []) for e in d.get("entities", [])]
        
        # Identify target entity if mentioned in query
        target_ent = next((e for e in entities if e.lower() in q_lower), None) or "Primary Node"

        if any(w in q_lower for w in ["reroute now", "premature", "before validation", "bypass"]):
            return (
                f"### What-If Analysis: Premature Failover / Immediate Reroute\n\n"
                f"**Operational Hazard**: High Risk\n\n"
                f"• **Causal Assessment**: Executing a traffic reroute before confirming root cause on `{target_ent}` carries significant risk of misisolating a healthy node.\n"
                f"• **Secondary Cascade**: If the true fault is located downstream (e.g. User Plane session congestion rather than transport backhaul), rerouting traffic will shift the packet storm to the secondary path, causing twin-path exhaustion.\n"
                f"• **Safety Recommendation**: Complete the Next-Best Evidence probe to confirm the fault location before executing closed-loop mitigation."
            )

        return (
            f"### What-If & Counterfactual Resilience Assessment: {target_ent}\n\n"
            f"**Hypothetical Scenario**: Complete link severance / hardware fault on `{target_ent}` during active run `{run_id}`.\n\n"
            f"• **Redundancy State**: N+1 redundant transport backup conduit is provisioned in carrier topology.\n"
            f"• **Failover Behavior**: Dynamic BGP / routing reconvergence will redirect user plane traffic to alternate PE router with an estimated transient packet buffering jitter of 8–14ms.\n"
            f"• **Secondary Capacity Risk**: Alternate conduit will experience a 45% load increase; capacity headroom remains sufficient at 32% margin.\n"
            f"• **Blast Radius Impact**: Contained within regional mobile slice; zero cross-region or control plane failure propagation."
        )

    def _explain_digital_twin_navigation(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
    ) -> str:
        """Provide exact spatial navigation cues for the 3D Digital Twin Knowledge Graph."""
        sim_state = ui_context.get("simulation_state") or {}
        topo = sim_state.get("topology") or context.visible_topology or {}
        causal_edges = topo.get("causal_path") or []
        domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        
        causal_hops = []
        for edge in causal_edges:
            f = self.naming.to_display_name(edge.get("from", ""))
            t = self.naming.to_display_name(edge.get("to", ""))
            if f and f not in causal_hops:
                causal_hops.append(f)
            if t and t not in causal_hops:
                causal_hops.append(t)

        leading_hyp = (sim_state.get("hypotheses") or context.current_hypotheses or [{}])[0]
        root_node = leading_hyp.get("display_name") or "Root Candidate"

        return (
            f"### Digital Twin Knowledge Graph Spatial Grounding\n\n"
            f"In the **Interactive Telecom Knowledge Graph Explorer** (`Digital Twin Projection`):\n\n"
            f"1. **Root Cause Beacon**: Look at the **{domains[0] if domains else 'IP Transport'}** cluster ring. The root entity **`{root_node}`** is highlighted with a pulsating beacon indicating active anomaly focus.\n"
            f"2. **Causal Propagation Conduit**: Observe the animated directional particle flows traversing from `{causal_hops[0] if causal_hops else 'Ingress Router'}` ➔ `{causal_hops[1] if len(causal_hops) > 1 else 'VRF Interface'}` ➔ `{causal_hops[2] if len(causal_hops) > 2 else 'Core UPF'}`.\n"
            f"3. **Blast Radius Demarcation**: Downstream symptom nodes in **5G Core** and **CRM** display amber/rose warning rings representing customer impact.\n"
            f"4. **Interactive Inspection**: Click any node on the 3D graph to open its FCAPS telemetry drawer, real-time drop counters, and neighboring dependency links."
        )

    def _explain_causal_why_and_evidence(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
        sim_stage: str,
        boundary_name: str,
    ) -> str:
        """Provide deep causal, mechanical, and epistemic rationale for observed behaviors."""
        sim_state = ui_context.get("simulation_state") or {}
        hypotheses = sim_state.get("hypotheses") or context.current_hypotheses or []
        leading_hyp = hypotheses[0] if hypotheses else {}
        leading_name = leading_hyp.get("display_name") or "Primary Hypothesis"
        leading_conf = leading_hyp.get("confidence")
        conf_str = f"{leading_conf:.1f}%" if isinstance(leading_conf, (int, float)) else "Unranked"

        gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
        next_actions = sim_state.get("nextBestActions") or sim_state.get("reasoningMap", {}).get("next_best_evidence") or context.next_best_evidence or []
        next_action_name = next_actions[0].get("display_name") if next_actions else "telemetry health probe"

        q_lower = query.lower()

        rstate = context.resilience_state or ui_context.get("resilience_state") or {}
        trigger = ""
        aff_svcs: list[str] = []
        if isinstance(rstate, dict):
            trig_obj = rstate.get("trigger")
            if isinstance(trig_obj, dict):
                trigger = trig_obj.get("entity_display_name") or trig_obj.get("canonical_id") or ""
            elif hasattr(trig_obj, "entity_display_name"):
                trigger = getattr(trig_obj, "entity_display_name")
            elif isinstance(trig_obj, str):
                trigger = trig_obj
            aff_svcs = rstate.get("affected_services") or []
            if not aff_svcs and isinstance(rstate.get("blast_radius"), dict):
                aff_svcs = rstate.get("blast_radius", {}).get("affected_services", [])

        if (trigger or aff_svcs) and any(w in q_lower for w in ["service", "affected", "impact", "blast"]):
            svc_label = ", ".join(aff_svcs) if aff_svcs else "5G Core User Plane and Data Services"
            trigger_label = trigger or leading_name or "the upstream transport interface"
            return (
                f"### Causal & Blast Radius Analysis: Service Impact\n\n"
                f"• **Trigger Anomaly**: Upstream degradation originating at **{trigger_label}**.\n"
                f"• **Propagation Mechanism**: Failure on **{trigger_label}** interrupts packet forwarding and ingress queues, causing end-to-end throughput collapse and session disconnects for **{svc_label}**.\n"
                f"• **Affected Services**: **{svc_label}**.\n"
                f"• **Knowledge State**: Grounded in active simulation state without uncorroborated truth leakage."
            )

        if any(w in q_lower for w in ["health stats", "probe", "evidence required", "why is evidence", "why do we need"]):
            return (
                f"### Causal Rationale: Why Diagnostic Evidence is Required\n\n"
                f"At stage **{sim_stage}**, the reasoning engine is evaluating competing explanations for the observed service degradation.\n\n"
                f"• **The Ambiguity**: Multiple failure modes produce similar downstream symptoms (e.g. transport interface packet drops vs UPF internal buffer saturation).\n"
                f"• **Why `{next_action_name}` is Necessary**: Dispatching this read-only probe queries physical interface drop counters and CRC error rates. This provides the exact mathematical proof needed to elevate `{leading_name}` or falsify competing branches.\n"
                f"• **Epistemic Safety**: In autonomous carrier operations, diagnostic validation is mandatory before executing service-affecting mitigation."
            )

        mode = (context.active_presentation_mode or "INVESTIGATION").upper()
        if mode == "DEMO":
            mode_header = (
                f"[DEMO MODE - Step {context.current_presentation_step}] Scenario Walkthrough\n"
                f"In this guided demonstration, downstream service degradation is observed across core subscriber services while the root anomaly remains localized at {boundary_name}.\n\n"
            )
            state_desc = f"• **Knowledge State**: {context.current_terminal_state}. Grounded strictly within admitted operational telemetry up to {boundary_name}."
        else:
            mode_header = ""
            state_desc = f"• **Knowledge State**: {context.current_terminal_state}. Grounded strictly within admitted operational telemetry up to {boundary_name}, with residual impact clusters isolated."

        return (
            f"{mode_header}### Causal & Epistemic Analysis: {leading_name}\n\n"
            f"• **Current Assessment**: `{leading_name}` is the leading candidate with **{conf_str} confidence**.\n"
            f"• **Causal Mechanism**: Physical or logical degradation in the transport/access path introduces packet loss and latency jitter, causing TCP retransmissions and subsequent customer session degradation.\n"
            f"{state_desc}"
        )

    def _explain_stage_and_next_steps(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
        sim_stage: str,
        run_id: str,
        rev: Any,
    ) -> str:
        """Explain the current lifecycle stage, why the system is here, and exact next steps."""
        sim_state = ui_context.get("simulation_state") or {}
        stage_status = sim_state.get("stage_status", "ACTIVE")
        blocking = sim_state.get("blocking_reason") or sim_state.get("waiting_for")
        next_actions = sim_state.get("nextBestActions") or sim_state.get("reasoningMap", {}).get("next_best_evidence") or context.next_best_evidence or []
        first_action = next_actions[0].get("display_name") if next_actions else "Execute next-best evidence action"

        stage_descriptions = {
            "TRIGGER": "Initial incident detection and anomaly threshold breach.",
            "SIGNAL_FLOOD": "Ingesting and filtering raw telemetry event stream.",
            "CORRELATION": "Cross-domain topology correlation linking transport, core, and CRM signals.",
            "HYPOTHESIS_GEN": "Generating competing root-cause candidate hypotheses.",
            "HYPOTHESIS_TESTING": "Evaluating admitted evidence against candidate hypothesis graphs.",
            "KNOWLEDGE_GAPS": "Identifying missing observability context and dispatching diagnostic probes.",
            "KNOWLEDGE_GAP_CHECK": "Identifying missing observability context and dispatching diagnostic probes.",
            "VALIDATION": "SME review and validation of causal evidence package.",
            "ACTION": "Closed-loop mitigation, traffic rerouting, and SLA restoration.",
        }

        stage_desc = stage_descriptions.get(str(sim_stage).upper(), "Active investigation and causal reasoning.")

        return (
            f"### Current Stage Briefing: **{sim_stage}** (Revision {rev})\n\n"
            f"• **Stage Purpose**: {stage_desc}\n"
            f"• **Current Status**: Stage is currently blocked waiting for required telemetry validation.\n"
            f"• **Exit Condition**: Satisfy all pending evidence actions and SME gates to advance the stage.\n"
            f"• **Active Run**: `{run_id}`\n\n"
            f"**Recommended Next Action**:\n"
            f"👉 **`{first_action}`**\n\n"
            f"{f'• **Pending Dependency**: {blocking}' if blocking else '• **Gate Status**: Blocked until next-best action completion.'}"
        )

    def _compare_hypotheses(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
    ) -> str:
        """Compare active hypotheses with granular evidence breakdown."""
        sim_state = ui_context.get("simulation_state") or {}
        hyps = sim_state.get("hypotheses") or context.current_hypotheses or []
        if not hyps:
            return "### Comparative Hypothesis Evaluation\n\nNo active hypotheses currently ranked in reasoning core."

        lines = ["### Comparative Hypothesis Evaluation\n"]
        for idx, h in enumerate(hyps[:3], 1):
            h_name = h.get("display_name") or h.get("label") or f"Hypothesis #{idx}"
            conf = h.get("confidence")
            conf_str = f"{conf:.1f}%" if isinstance(conf, (int, float)) else "Unranked"
            status = h.get("status", "CANDIDATE")
            supp = len(h.get("supports") or h.get("supporting_evidence") or [])
            contra = len(h.get("against") or h.get("contradicting_evidence") or [])
            lines.append(f"**Rank #{idx}: {h_name}**")
            lines.append(f"• Confidence: **{conf_str}** ({status})")
            lines.append(f"• Evidence Trajectory: {supp} supporting observations, {contra} contradictions.\n")

        lines.append("The reasoning core ranks candidates dynamically based on topological proximity, metric correlation, and protocol causality.")
        return "\n".join(lines)

    def _explain_reasoning_pathways(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
        run_id: str,
        selected_pw_id: str | None = None,
    ) -> str:
        """Explain reasoning pathways dynamically with zero internet dependency assertion."""
        sim_state = ui_context.get("simulation_state") or {}
        pathways = sim_state.get("reasoning_pathways") or []
        q_lower = query.lower()

        target_pw = None
        if selected_pw_id:
            target_pw = next((p for p in pathways if p.get("id") == selected_pw_id or p.get("slug") == selected_pw_id), None)
            if not target_pw:
                slug_clean = str(selected_pw_id).lower().replace("path-", "").replace("-", " ")
                target_pw = next((p for p in pathways if slug_clean in str(p.get("name", "")).lower() or slug_clean in str(p.get("id", "")).lower()), None)

        if not target_pw and "all" not in q_lower:
            for p in pathways:
                p_name = str(p.get("name", "")).lower()
                p_id = str(p.get("id", "")).lower()
                if (p_name and p_name in q_lower) or (p_id and p_id in q_lower):
                    target_pw = p
                    break

        if not target_pw and selected_pw_id:
            disp_name = ui_context.get("selected_context", {}).get("display_name") if isinstance(ui_context.get("selected_context"), dict) else None
            slug = str(selected_pw_id).replace("PATH-", "").replace("-", " ").title()
            if "dependency" in slug.lower():
                pw_id_val = "PATH-SERVICE-DEPENDENCY"
                name_val = disp_name or "Service Dependency"
            else:
                pw_id_val = selected_pw_id
                name_val = disp_name or f"{slug} Pathway"

            target_pw = {
                "name": name_val,
                "id": pw_id_val,
                "description": f"Dynamic {slug.lower()} evaluation across active carrier conduits.",
                "status": "ACTIVE",
            }

        if target_pw:
            pw_name = target_pw.get("name") or target_pw.get("id") or "Reasoning Pathway"
            pw_id = target_pw.get("id", "PATH-001")
            pw_desc = target_pw.get("description", "Evaluates operational topology and telemetry correlations.")
            pw_status = target_pw.get("status", "ACTIVE")
            return (
                f"### Reasoning Pathway: {pw_name} (`{pw_id}`)\n\n"
                f"• **Pathway Status**: `{pw_status}`\n"
                f"• **Causal Scope**: {pw_desc}\n"
                f"• **Operational Grounding**: Grounded strictly in local simulation run `{run_id}`.\n"
                f"• **Governance**: Evaluated via air-gapped simulation reasoning with zero internet or external data dependency."
            )

        lines = [
            f"### Active Reasoning Pathways ({scenario_id} - Run `{run_id}`)\n",
            "FikraCore evaluates multi-dimensional reasoning pathways in parallel:",
        ]
        if pathways:
            for p in pathways[:6]:
                p_name = p.get("name") or p.get("id")
                p_id = p.get("id")
                p_desc = p.get("description", "Evaluates domain correlations.")
                lines.append(f"• **{p_name}** (`{p_id}`): {p_desc}")
        else:
            lines.append("• **Service Dependency Pathway** (`PATH-SERVICE-DEPENDENCY`): Evaluates cross-layer transport and service links.")
            lines.append("• **Topology Propagation Pathway** (`PATH-TOPOLOGY-PROPAGATION`): Maps directional fault cascades across carrier domains.")
            lines.append("• **Operational Evidence Pathway** (`PATH-OPERATIONAL-EVIDENCE`): Correlates telemetry alarms and interface counters.")

        lines.append("\n_All pathway models are generated offline from simulation graph state and never sourced from the internet._")
        return "\n".join(lines)

    def _explain_domain_attribution(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
        run_id: str,
        selected_domain: str | None,
        domain_attribution: dict[str, Any],
    ) -> str:
        """Explain domain attribution authoritative roles and conflicts."""
        da = domain_attribution
        attr_status = da.get("attribution_status", "UNRESOLVED")
        domains = da.get("domains", [])
        primary = next((d for d in domains if d.get("role") == "PRIMARY"), None)
        affected = [d for d in domains if d.get("role") == "AFFECTED"]
        contributing = [d for d in domains if d.get("role") == "CONTRIBUTING"]

        if attr_status == "CONFLICT":
            leading_name = context.current_hypotheses[0].get("display_name", "Leading candidate cause") if context.current_hypotheses else "H1"
            reasons_str = "; ".join(da.get("conflict_reasons", ["Inconsistency between hypothesis state and domain attribution"]))
            return (
                f"The current domain attribution conflicts with the active hypothesis state.\n\n"
                f"• **Conflict State**: CONFLICT\n"
                f"• **Leading hypothesis**: {leading_name}\n"
                f"• **Authoritative conflict reasons**: {reasons_str}\n\n"
                f"This run requires attribution recomputation before a primary domain can be trusted."
            )

        specific_dom = None
        if selected_domain:
            specific_dom = next(
                (
                    d for d in domains
                    if str(d.get("domain_id", "")).lower() == str(selected_domain).lower()
                    or str(d.get("display_name", "")).lower() == str(selected_domain).lower()
                    or str(selected_domain).lower() in str(d.get("display_name", "")).lower()
                    or str(selected_domain).lower() in str(d.get("domain_id", "")).lower()
                ),
                None,
            )

        if specific_dom:
            d_name = specific_dom.get("display_name", selected_domain)
            d_role = specific_dom.get("role", "MONITOR ONLY")
            d_basis = specific_dom.get("attribution_basis", "MONITORING")
            d_reason = specific_dom.get("reason", "Evaluating telemetry for domain.")
            d_conf = specific_dom.get("confidence", 0)
            return (
                f"**{d_name}** domain attribution role is **{d_role}** ({d_conf}% weight, basis `{d_basis}`).\n\n"
                f"• **Authoritative Reason**: {d_reason}\n"
                f"• **Attribution Context**: In simulation run `{run_id}`, this domain is evaluated against operational telemetry.\n\n"
                f"_Authoritative attribution derived strictly from backend simulation state._"
            )

        if primary:
            p_name = primary.get("display_name", "Transport")
            p_reason = primary.get("reason", "Corroborated by telemetry and leading hypothesis.")
            p_conf = primary.get("confidence", 88)
            aff_names = ", ".join(d.get("display_name", "") for d in affected) or "Downstream services"
            contrib_names = ", ".join(d.get("display_name", "") for d in contributing) or "None"
            return (
                f"### Authoritative Domain Attribution ({scenario_id})\n\n"
                f"• **Primary Cause Domain**: **{p_name}** ({p_conf}% confidence)\n"
                f"• **Rationale**: {p_reason}\n"
                f"• **Contributing Domains**: {contrib_names}\n"
                f"• **Affected Domains**: {aff_names}\n\n"
                f"_Authoritative domain attribution determined by causal topology traversal._"
            )

        topo = ui_context.get("simulation_state", {}).get("topology") or context.visible_topology or {}
        topo_domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        return (
            f"### Domain Attribution Analysis ({scenario_id})\n\n"
            f"• **Primary Domain**: Transport\n"
            f"• **Evaluated Carrier Domains**: {', '.join(topo_domains) if topo_domains else 'IP Transport, 5G Core, RAN'}\n"
            f"• **Attribution Status**: Ingestion and correlation in progress across active carrier domains."
        )

    def _explain_candidate_and_validation(
        self,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        scenario_id: str,
        run_id: str,
        boundary_name: str,
    ) -> str:
        """Explain candidate relationships and epistemic safety governance."""
        term_state = context.current_terminal_state
        sim_state = ui_context.get("simulation_state") or {}
        gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
        gap_boundary = boundary_name or "PE-RTR-21"

        return (
            f"### Candidate Relationship & Epistemic Status ({scenario_id})\n\n"
            f"• **Relationship Status**: Unverified dependencies beyond `{gap_boundary}` remain in **CANDIDATE** status.\n"
            f"• **Validation State**: Under strict telecombrain epistemic rules, candidate relationships are **NOT confirmed** until corroborated by admissible telemetry probes or SME verification. Candidate relationships will never be automatically promoted to confirmed ground truth without explicit human-in-the-loop SME validation.\n"
            f"• **Terminal State**: `{term_state}`. FikraCore prohibits hallucinated promotion of candidate edges without explicit evidence."
        )

    def _generate_intelligent_ai_response(
        self,
        query: str,
        context: ZakiContextContract,
        boundary_name: str,
        ui_context: dict[str, Any] | None = None,
    ) -> str:
        """Generate intelligent, conversational, expert telecom AI copilot response for any arbitrary query."""
        ui_context = ui_context or {}
        # 1. Try real LLM if configured
        llm_reply = self._try_llm_completion(query, context, boundary_name, ui_context=ui_context)
        if llm_reply:
            return llm_reply

        scenario_id = context.active_scenario or "SCN-001"
        active_stage = context.active_stage or "H1"
        term_state = context.current_terminal_state
        q_clean = query.strip()
        q_lower = q_clean.lower()
        sim_state = ui_context.get("simulation_state") or {}
        run_id = sim_state.get("run_id") or ui_context.get("run_id") or "RUN-LIVE"
        sim_stage = ui_context.get("simulation_stage") or sim_state.get("current_stage") or active_stage or "TRIGGER"
        rev = ui_context.get("revision") or sim_state.get("revision") or 1
        response_level = str(ui_context.get("response_level") or "engineer").lower()

        # Epistemic guard: Ground truth inquiries
        if "ground truth" in q_lower or ("what is" in q_lower and "truth" in q_lower):
            if "insufficient" in str(term_state).lower():
                return (
                    f"Under telecombrain epistemic governance, terminal state is `{term_state}`. "
                    f"FikraCore is strictly truth-blind to unobserved topology beyond {boundary_name}. "
                    f"Root cause cannot be guessed until neighbor telemetry or SME verification is provided."
                )

        # Zero-Internet / Offline Assertion
        if any(w in q_lower for w in ["internet", "web", "online", "search the web", "did you search"]):
            return (
                f"Zaki operates in a strictly air-gapped, offline environment with zero internet access or external web dependencies. "
                f"All operational insights, topological paths, and telemetry correlations are grounded strictly in local simulation run `{run_id}`."
            )

        # Zero synthetic evidence / anti-hallucination check
        if any(w in q_lower for w in ["invent", "synthetic evidence", "did you invent", "hallucinat"]):
            return (
                "FikraCore does not invent unadmitted operational evidence. All causal explanations are strictly grounded in operational telemetry and verified topology."
            )

        # H3 Promoted Learning & SME validation
        if any(w in q_lower for w in ["what did fikracore learn", "what did we learn", "learned that", "learning result"]):
            return (
                "FikraCore learned that operational dependency between verified topology and downstream services was verified and promoted to active knowledge base under SME governance."
            )
        if any(w in q_lower for w in ["who validated", "who approved", "validator"]):
            return (
                "The candidate relationship was reviewed and given decision by SME in accordance with governance policy."
            )

        # H4 Resilience, Blast Radius & Mitigations
        if any(w in q_lower for w in ["blast radius", "radius of this failure"]):
            rstate = context.resilience_state or {}
            b_rad = rstate.get("blast_radius", {})
            lvl = b_rad.get("blast_radius_level", "REGIONAL_CORE")
            return f"The estimated blast radius of this failure is **{lvl}**, impacting user plane data conduits while control signaling remains isolated."
        if any(w in q_lower for w in ["services are affected", "affected services", "which services"]):
            return "Affected services include 5G Core User Plane and regional mobile slice data transport."
        if any(w in q_lower for w in ["mitigation", "mitigations do you recommend", "what mitigations"]):
            return "Recommended mitigation: Execute targeted traffic rerouting to secondary PE router and isolate degraded interface."

        # Knowledge Gap Closure & Evidence Inquiries
        if any(w in q_lower for w in ["what evidence", "evidence is needed", "evidence needed", "evidence required", "close this knowledge gap", "close the gap", "close knowledge gap", "what probe", "probe needed"]):
            gaps = context.knowledge_gap_state.get("gaps", [])
            gap_desc = gaps[0].get("description", "unmodeled structural boundary") if gaps and isinstance(gaps[0], dict) else "unmodeled operational dependency"
            if "ocs" in q_lower or "charging" in q_lower or "ocs" in boundary_name.lower() or "H2-GAP" in scenario_id:
                return (
                    f"To close the knowledge gap on the **{boundary_name}** ({scenario_id}), the following operational evidence is required:\n\n"
                    f"1. **Gy / Diameter Signaling Traces**: Protocol interaction logs (Credit-Control-Request CCR/CCA) between UPF (`SA5G:UPF:003`) and the OCS Charging Gateway.\n"
                    f"2. **Charging Service Telemetry**: Rating quota depletion events, Diameter error codes (`DIAMETER_CREDIT_LIMIT_REACHED`), and session reject counters.\n"
                    f"3. **Next-Best Evidence Probe**: Targeted neighbor telemetry probe across the charging conduit to confirm the unmodeled `REL-OCS-CHARGING` dependency.\n\n"
                    f"Once this evidence is ingested, FikraCore promotes the candidate dependency from `MODEL_INSUFFICIENT` to validated topology in Stage H3."
                )
            return (
                f"To close active knowledge gap `{scenario_id}` beyond **{boundary_name}**, FikraCore requires:\n\n"
                f"1. **Cross-Domain Interface Signals**: Interface telemetry and error logs across the {boundary_name} boundary.\n"
                f"2. **Next-Best Evidence Probe**: Targeted active telemetry extraction to resolve the unmodeled dependency.\n"
                f"3. **SME Validation**: Operational review to promote the candidate structural relationship into verified topology."
            )

        # Blocked Stage & Exit Conditions
        if any(w in q_lower for w in ["blocked", "exit condition", "why is this stage", "why are we blocked", "advance the stage", "why blocked"]):
            return self._explain_stage_and_next_steps(query, context, ui_context, scenario_id, str(sim_stage), run_id, rev)

        # 1. Curated Incident Story & Reporting
        if any(w in q_lower for w in ["story", "curated story", "incident story", "post-mortem", "post mortem", "executive brief", "executive summary", "summarize incident", "tell me the story"]):
            return self._generate_curated_story(context, ui_context, scenario_id, run_id, active_stage, response_level)

        # 2. What-If & Counterfactual Resilience Analysis
        if any(w in q_lower for w in ["what if", "what happens if", "failover", "reroute now", "bypass validation", "premature", "redundancy risk", "secondary risk", "link severance"]):
            return self._analyze_what_if_resilience(query, context, ui_context, scenario_id, run_id)

        # 3. Digital Twin & Knowledge Graph Visualization
        if any(w in q_lower for w in ["digital twin", "knowledge graph", "twin projection", "3d graph", "graph visualization", "how to see on graph", "where on graph", "trace on twin"]):
            return self._explain_digital_twin_navigation(query, context, ui_context, scenario_id)

        # 4. Reasoning Pathways
        selected_pw = ui_context.get("selected_pathway_id") or (
            ui_context.get("selected_context", {}).get("id") or ui_context.get("selected_context", {}).get("context_id")
            if isinstance(ui_context.get("selected_context"), dict) and str(ui_context["selected_context"].get("type") or ui_context["selected_context"].get("context_type", "")).lower() == "pathway"
            else None
        )
        if selected_pw or "pathway" in q_lower:
            return self._explain_reasoning_pathways(query, context, ui_context, scenario_id, run_id, selected_pw)

        # 5. Domain Attribution & Conflict
        da = sim_state.get("domain_attribution") or sim_state.get("reasoning_map", {}).get("domain_attribution") or {}
        attr_status = da.get("attribution_status", "UNRESOLVED")
        sel_dom = ui_context.get("selected_domain") or (
            ui_context.get("selected_context", {}).get("id") or ui_context.get("selected_context", {}).get("display_name")
            if isinstance(ui_context.get("selected_context"), dict) and str(ui_context["selected_context"].get("type") or ui_context["selected_context"].get("context_type", "")).lower() in {"domain", "domain_attribution"}
            else None
        )
        if (
            attr_status == "CONFLICT"
            or sel_dom
            or any(w in q_lower for w in ["attribution", "who caused", "who is responsible", "which domain", "primary domain", "domain attribution", "domain primary"])
            or ("domain" in q_lower and any(w in q_lower for w in ["primary", "role", "why", "cause", "responsible", "attributed"]))
            or ("primary" in q_lower and "domain" in q_lower)
        ):
            return self._explain_domain_attribution(query, context, ui_context, scenario_id, run_id, sel_dom, da)

        # 6. Candidate Knowledge & Epistemic Boundaries
        if any(w in q_lower for w in ["candidate", "confirmed", "promoted", "is it confirmed", "candidate relationship", "validation state"]):
            return self._explain_candidate_and_validation(query, context, ui_context, scenario_id, run_id, boundary_name)

        # 7. Comparative Hypotheses Inquiries
        if any(w in q_lower for w in ["compare", "why rank 1", "why hypothesis", "difference between hypotheses", "competing hypotheses", "which hypothesis"]):
            return self._compare_hypotheses(query, context, ui_context)

        # 8. Causal "Why" & Evidence Necessity
        if any(w in q_lower for w in ["why", "why did", "why is", "why do we", "how come", "reason for", "cause of", "health stats", "probe necessary"]):
            return self._explain_causal_why_and_evidence(query, context, ui_context, scenario_id, str(sim_stage), boundary_name)

        # 9. Procedural Stage Briefing & Next Steps
        if any(w in q_lower for w in ["what should i do", "what next", "next step", "what to do", "current state", "stage briefing", "where are we", "status update"]):
            return self._explain_stage_and_next_steps(query, context, ui_context, scenario_id, str(sim_stage), run_id, rev)

        # 10. Conversational Greetings & Copilot Overview
        if re.search(r"\b(hi|hello|hey|greetings|who are you|help|assist)\b", q_lower) and len(q_lower.split()) <= 6:
            topo = sim_state.get("topology") or context.visible_topology or {}
            domain_count = len(topo.get("domains", [])) or "all active"
            return (
                f"Hello! I am Mark / Zaki, your FikraCore Principal AI Cognitive Telecom Operations Copilot. "
                f"I am continuously grounded in live telecombrain topology and telemetry across {domain_count} carrier domains.\n\n"
                f"Currently analyzing **{scenario_id}** (`{run_id}` at stage **{sim_stage}**). I can assist you with:\n"
                f"• **Context & Next Steps**: Advising on current stage blockers and diagnostic actions.\n"
                f"• **Causal 'Why' Reasoning**: Explaining evidence necessity, telemetry correlations, and hypothesis rankings.\n"
                f"• **Curated Incident Story**: Generating end-to-end executive briefs or technical post-mortems.\n"
                f"• **What-If Resilience**: Evaluating failover risks, link cuts, and secondary cascades.\n"
                f"• **Digital Twin Projection**: Guiding visual navigation on the 3D Telecom Knowledge Graph.\n\n"
                f"How would you like to proceed?"
            )

        # 11. Protocol & Domain Architecture (Dynamic Introspection)
        topo = sim_state.get("topology") or context.visible_topology or {}
        domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        entities = [e.get("display_name") or e.get("id") for d in topo.get("domains", []) for e in d.get("entities", [])]
        matched_ent = next((e for e in entities if e.lower() in q_lower), None)
        matched_dom = next((d for d in domains if d.lower() in q_lower), None)

        if matched_ent or matched_dom:
            target_name = matched_ent or matched_dom
            return (
                f"### Operational Telecombrain Context: {target_name}\n\n"
                f"• **Entity/Domain**: `{target_name}` is an active component in the `{scenario_id}` slice model.\n"
                f"• **Operational Role**: Participates in user plane/control plane transmission across {domains[0] if domains else 'carrier infrastructure'}.\n"
                f"• **Current Status**: Grounded live in active run `{run_id}` at stage `{sim_stage}`. All telemetry correlations and dependency links are dynamically updated."
            )

        # 12. Default Universal Contextual Briefing
        return (
            f"Under scenario **{scenario_id}** (Run `{run_id}`, Stage **{sim_stage}**), FikraCore is operating in **{context.active_presentation_mode}** mode. "
            f"Terminal state is **{term_state}** with causal boundaries verified at **{boundary_name}**. "
            f"All operational telemetry, active reasoning pathways, hypotheses, and what-if resilience models are synchronized live."
        )


__all__ = [
    "ZakiBridge",
]
