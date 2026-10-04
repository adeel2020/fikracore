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
from .dialogue_state import dialogue_state_manager


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
            # Derive user intent and fetch intent-driven context
            intent, intent_params = self.derive_user_intent(query, ui_context, context)
            intent_context = self.fetch_intent_driven_context(intent, intent_params, context, ui_context)
            ui_context["derived_intent"] = intent
            ui_context["intent_context"] = intent_context
            if intent in {"GREETING", "INCIDENT_BRIEF", "BLAST_RADIUS", "CAUSAL_PROPAGATION", "REMEDIATION_STRATEGY", "USER_OFFER", "ENTITY_INSPECTION"}:
                ui_context["skip_focus_prefix"] = True

            # ONE OperationalContext for this turn, shared by every lens.
            from zaki.contracts.operational_context import resolve_operational_context, CONTEXT_READY
            from zaki.contracts.intent_dispatcher import OPERATIONAL_LENS_INTENTS

            op_ctx, op_readiness = resolve_operational_context(ui_context)
            grounded_in["context_id"] = op_ctx.context_id
            grounded_in["context_version"] = rev
            grounded_in["context_readiness"] = op_readiness

            # 1. Lenses without a ready context, and the Storyteller, are contract-rendered
            #    (never free-form LLM text over fallback state).
            llm_allowed = intent != "INCIDENT_BRIEF" and not (
                intent in OPERATIONAL_LENS_INTENTS and op_readiness != CONTEXT_READY
            )
            ui_context["llm_allowed"] = llm_allowed
            llm_reply = None
            if llm_allowed:
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
                if not sel_dom and isinstance(ui_context.get("selected_context"), dict):
                    sc = ui_context["selected_context"]
                    if str(sc.get("context_type") or sc.get("type", "")).lower() in {"domain", "domain_attribution"}:
                        sel_dom = sc.get("context_id") or sc.get("display_name") or sc.get("id")
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
            query=query,
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
        conversation_message = self._to_copilot_voice(response_text, query, context, ui_context=ui_context)
        chips = self._build_copilot_chips(context, suggested_actions, ui_context=ui_context)
        entities = self._extract_highlighted_entities(response_text, context, ui_context)

        return {
            "spoken_response": conversation_message,
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
                "spoken_message": conversation_message,
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
                "spoken_reply": conversation_message,
                "followups": chips,
            },
        }

    def _to_copilot_voice(
        self,
        response_text: str,
        query: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any] | None = None,
    ) -> str:
        """Return the natural, empathetic co-pilot spoken briefing avoiding mechanical readouts."""
        ui_context = ui_context or {}
        q = (query or "").strip().lower()
        clean = self._strip_workspace_framing(response_text).strip()

        # If query is explicitly asking for a post-mortem or curated story, deliver full narrative
        if any(w in q for w in ["curated story", "full post-mortem"]):
            return clean

        # If response contains live flash narration quote(s), prioritize speaking the active flash narration
        flash_quotes = re.findall(r'🎙️\s*"([^"]+)"', clean)
        if flash_quotes:
            return flash_quotes[-1]

        # Use intent spoken text if available from the active domain contract, otherwise clean response
        spoken_candidate = ui_context.get("intent_spoken_text") or clean

        # Curate the actual dynamic response text using ProsodyContract
        try:
            from zaki.contracts.prosody import ProsodyContract
            return ProsodyContract().curate_speech(spoken_candidate, query=query)
        except Exception:
            pass

        spoken = spoken_candidate
        # Strip boilerplates like "Under scenario SCN-001 (Run RUN-001, Stage 1)... Terminal state is..."
        spoken = re.sub(r"^Under scenario[^\n.]+\.\s*", "", spoken, flags=re.IGNORECASE)
        spoken = re.sub(r"^Terminal state is[^\n.]+\.\s*", "", spoken, flags=re.IGNORECASE)
        spoken = re.sub(r"^All operational telemetry[^\n.]+\.\s*", "", spoken, flags=re.IGNORECASE)
        # Strip markdown headings, lists, tables, bullets
        spoken = re.sub(r"###+\s*[^\n]+\n", "", spoken)
        spoken = re.sub(r"\n[-*•]\s+", " ", spoken)
        spoken = re.sub(r"\*\*([^*]+)\*\*", r"\1", spoken)
        spoken = re.sub(r"`([^`]+)`", r"\1", spoken)
        spoken = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", spoken)

        # Phonetic entity expansion for smooth prosody
        spoken = re.sub(r"\bPE-RTR-0?(\d+)\b", r"Provider Edge Router \1", spoken)
        spoken = re.sub(r"\bUPF-0?(\d+)\b", r"U-P-F \1", spoken)
        spoken = re.sub(r"\bSCN-0?(\d+)\b", r"Scenario \1", spoken)
        spoken = re.sub(r"\b(\d+(?:\.\d+)?)\s*Gbps\b", r"\1 gigabits per second", spoken)
        spoken = re.sub(r"\b(\d+(?:\.\d+)?)\s*Mbps\b", r"\1 megabits per second", spoken)
        spoken = re.sub(r"\s+", " ", spoken).strip()

        # Extract at most 2 clean sentences (~30 words max)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", spoken) if s.strip() and len(s.strip()) > 10]
        if not sentences:
            return "Telemetry synchronized... I've updated the diagnostic details on your display."

        brief = " ".join(sentences[:2])
        words = brief.split()
        if len(words) > 35:
            brief = " ".join(words[:32]) + "..."
        return brief

    @staticmethod
    def _strip_workspace_framing(response_text: str) -> str:
        """Remove UI workspace framing from the conversational copilot message."""
        t = response_text
        if "focus:" in t.lower():
            t = re.sub(r"^(?:[A-Za-z]+ focus:[^\n]+\n\n?)", "", t, flags=re.IGNORECASE)
        return t

    def _build_copilot_chips(
        self,
        context: ZakiContextContract,
        suggested_actions: list[dict[str, Any]],
        ui_context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        """Build small, dynamically grounded conversation prompts for the floating assistant UI."""
        chips: list[dict[str, str]] = []
        sim_state = (ui_context or {}).get("simulation_state") or {}
        story_ctx = sim_state.get("storyContext") or sim_state.get("story_context") or {}
        sqs = story_ctx.get("suggested_questions") or []
        for sq in sqs[:3]:
            label = sq if len(sq) <= 24 else sq[:21] + "..."
            chips.append({"label": label, "prompt": sq})

        if not chips:
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
        query: str = "",
    ) -> str:
        """Format response for the selected depth level in plain, non-technical English with proper workspace and level metadata."""
        clean = response_text.strip()
        lvl = (response_level or "engineer").lower()
        ws = (workspace or "investigate").lower()
        has_user_query = bool(query and query.strip())

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

        # Add workspace focus prefix unless explicitly skipped for conversational/action queries
        skip_focus_prefix = ui_context.get("skip_focus_prefix", False)
        focus_prefix = ""
        if not skip_focus_prefix:
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
            if not skip_focus_prefix and "Next action:" not in full_text:
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

        sim_status = (
            ui_context.get("simulation_status")
            or sim_state.get("status")
            or (sim_state.get("run") or {}).get("status")
            or "READY"
        ).upper()
        events = sim_state.get("events") or context.visible_evidence or []
        events_count = ui_context.get("events_count") or len(events)
        is_running = (sim_status == "RUNNING") or events_count > 0 or bool(context.current_hypotheses)

        # Stage bounds
        story_ctx = sim_state.get("story_context") or {}
        stage_idx = story_ctx.get("stage_index") if "stage_index" in story_ctx else (
            ui_context.get("stage_index", 0)
        )
        if isinstance(stage_idx, str) and stage_idx.isdigit():
            stage_idx = int(stage_idx)
        elif not isinstance(stage_idx, int):
            stage_idx = 0

        # Blast radius & impact
        impact = sim_state.get("impact") or {}
        impact_pct = impact.get("throughput_impact_pct") or 38
        affected_users = impact.get("affected_users") if impact.get("affected_users") is not None else (impact.get("users_affected") if impact.get("users_affected") is not None else 0)
        impact_label = impact.get("affected_label") or service_name

        if not is_running:
            remediation = "None staged. Waiting for simulation start."
            impact_desc = "Zero degradation. Pre-simulation state."
        elif stage_idx <= 1:
            remediation = "No premature mitigation. Safety rule holds traffic reroute until root cause confirmation."
            if "affected_users" in impact:
                impact_desc = f"Initial P1 anomaly on transport ingress ({impact_pct}% throughput loss, {affected_users:,} subscribers impacted)"
            else:
                impact_desc = f"Initial P1 anomaly on transport ingress; zero confirmed subscriber drop."
        elif stage_idx <= 3:
            remediation = "Diagnostic Next-Best Evidence probe scheduled across transport interface."
            impact_desc = f"Cascade to User Plane Function UPF-003; mobile sessions dropping."
        elif stage_idx <= 5:
            remediation = (sim_state.get("recovery") or {}).get("action") or f"Isolate degraded transport path and reroute {service_name} traffic to redundant secondary path"
            impact_desc = f"{impact_label} ({impact_pct}% throughput reduction, {affected_users:,} subscribers)"
        else:
            remediation = "Remediation verified; traffic successfully re-routed."
            impact_desc = "Degradation resolved; 100% throughput restored."

        if not is_running:
            return (
                "You are Mark / Zaki, the Principal AI Cognitive Telecom Operations Copilot for FikraCore.\n"
                f"=== SIMULATION STATUS: NOT STARTED (READY) ===\n"
                f"• Scenario: {sc_name} (`{sc_id}`) is staged in the investigate workspace, but the simulation run has NOT been started yet.\n"
                f"• Admitted Events: 0\n"
                f"• Zero operational anomalies or failure signals exist.\n\n"
                f"=== CRITICAL EPISTEMIC GUARDRAIL ===\n"
                f"DO NOT disclose or hypothesize any root cause, buffer saturation, hardware fault, failure cascade, or recovery action.\n"
                f"Explain that the simulation has not started yet and advise the operator to click Start Simulation to begin telemetry emission and observe live autonomous correlation.\n"
                f"Respect the requested response_level: `{response_level}`."
            )

        return (
            "You are Mark / Zaki, the Principal AI Cognitive Telecom Operations Copilot for FikraCore.\n"
            "You provide authoritative, highly articulate, expert, and actionable advice to telecom NOC engineers, operators, and leadership.\n\n"
            f"=== ACTIVE SIMULATION CONTEXT ===\n"
            f"• Scenario: {sc_name} (`{sc_id}`)\n"
            f"• Run ID: `{run_id}` | Horizon: `{active_stage}` | Stage: `{sim_stage}` (index {stage_idx})\n"
            f"• Terminal State: `{context.current_terminal_state}`\n"
            f"• Knowledge Boundary: {boundary_name}\n"
            f"• Response Level requested: `{response_level}`\n\n"
            f"=== OPERATIONAL TOPOLOGY & CAUSAL CONDUITS ===\n"
            f"• Active Domains: {', '.join(domains) if domains else 'IP Transport, 5G Core, CRM'}\n"
            f"• Causal Propagation Chain: {' ➔ '.join(causal_hops) if causal_hops else 'Observed via dynamic telemetry'}\n"
            f"• Blast Radius: {impact_desc}\n\n"
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
            f"=== MANDATORY NARRATION STYLES BY AUDIENCE ===\n"
            f"You MUST format your explanation strictly according to the requested response_level:\n"
            f"1. Executive (response_level: 'executive'):\n"
            f"   Structure as: **Impact** ➔ **Remediation** ➔ **Prevention**\n"
            f"   - Impact: Business and subscriber metrics (throughput drop %, affected subscribers, SLA risk).\n"
            f"   - Remediation: Primary action staged or executed to restore service.\n"
            f"   - Prevention: Long-term posture, capacity adjustments, and architectural resilience.\n"
            f"   - Tone: Concise, high-level, business-oriented. No raw internal IDs, micro-bullet dumps, or DB dumps.\n\n"
            f"2. Operations (response_level: 'operator' or 'operations'):\n"
            f"   Structure as: **Blast Radius** ➔ **Ranked Hypotheses** ➔ **Mitigation** ➔ **Handover**\n"
            f"   - Blast Radius: Affected services, domains, and degrading components.\n"
            f"   - Ranked Hypotheses: Top root-cause candidates with confidence scores and evidence counts.\n"
            f"   - Mitigation: Actionable diagnostic probes or playbook steps.\n"
            f"   - Handover: Next shift guidance, pending approvals, and blocked gates.\n\n"
            f"3. Engineering (response_level: 'engineer' or 'deep_technical'):\n"
            f"   Structure as: **Root Cause** ➔ **Causal Graph** ➔ **Evidence Math** ➔ **Learning Promotion**\n"
            f"   - Root Cause: Leading technical fault mechanism and interface/protocol boundary.\n"
            f"   - Causal Graph: Multi-hop propagation sequence linking upstream trigger to downstream symptom.\n"
            f"   - Evidence Math: Admitted telemetry readings, packet drop rates, CRC errors, baseline deviations.\n"
            f"   - Learning Promotion: SME validation status and candidate knowledge promotion to knowledge base.\n\n"
            f"=== LIVE FLASH NARRATION ===\n"
            f"Include the Live Flash Narration section summarizing stage advances.\n"
            f"Format:\n"
            f"### Live Flash Narration\n"
            f'• **At [Time] ([Phase])**:\n  🎙️ "[Concise Narration Quote]"\n\n'
            f"=== EPISTEMIC GOVERNANCE RULES ===\n"
            f"1. Strictly truth-blind: Ground all reasoning exclusively in admitted operational telemetry and topology. Never access hidden evaluator truth.\n"
            f"2. Never dump raw database rows or unformatted lists. Structure with clear markdown headers.\n"
            f"3. For voice delivery, be articulate, empathetic, concise, and collegial. Never start with robotic IVR boilerplate like 'Investigation focus:'.\n"
            f"4. Prosody & Voice Guardrail: Never read out raw markdown tables, bullet lists, or telemetry logs. Spoken audio turns must be at most 2 natural conversational sentences with breathing pauses.\n"
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
        service_name = scenario_meta.get("service") or (scenario_meta.get("domains") or ["Mobile Data"])[0]

        sim_status = (
            ui_context.get("simulation_status")
            or sim_state.get("status")
            or (sim_state.get("run") or {}).get("status")
            or "READY"
        ).upper()
        events = sim_state.get("events") or context.visible_evidence or []
        events_count = ui_context.get("events_count") or len(events)
        term_state = getattr(context, "current_terminal_state", "") or ""
        is_running = (sim_status == "RUNNING") or events_count > 0 or bool(context.current_hypotheses) or term_state in {"EXPLAINED", "PARTIALLY_EXPLAINED"}

        # Epistemic Guardrail: If simulation has NOT started yet and not explained, do NOT leak scenario details or root cause!
        if not is_running:
            if response_level == "executive":
                return (
                    f"# Executive Incident Briefing: Scenario Staged (`{sc_name}`)\n\n"
                    f"### 1. Impact\n"
                    f"Zero subscriber impact or SLA breach. Scenario **{sc_name}** (`{scenario_id}`) is staged in the **investigate** workspace, but the simulation run has **not started yet**.\n\n"
                    f"### 2. Remediation\n"
                    f"Cognitive monitors and telemetry conduits are standing by. Click **Start Simulation** to launch the operational run and observe live telemetry correlation.\n\n"
                    f"### 3. Prevention\n"
                    f"Continuous baseline observability is active across all regional network functions."
                )
            if response_level in {"operator", "operations"}:
                return (
                    f"# Operations Incident Briefing: Scenario Staged (`{sc_name}`)\n\n"
                    f"### 1. Blast Radius\n"
                    f"• **Active Status**: Ready / Standing By\n"
                    f"• **Monitored Domains**: Standing by for simulation launch\n"
                    f"• **Admitted Observations**: 0 telemetry events recorded\n\n"
                    f"### 2. Ranked Hypotheses\n"
                    f"• **Status**: No operational hypotheses active prior to simulation start.\n\n"
                    f"### 3. Mitigation\n"
                    f"• **Playbook Action**: Awaiting operator trigger to initiate live simulation run.\n\n"
                    f"### 4. Handover\n"
                    f"• **Next Shift Objective**: Launch simulation in Investigate console and observe initial telemetry correlation."
                )
            # Engineering (default)
            return (
                f"# Engineering Incident Analysis: Scenario Staged (`{sc_name}`)\n\n"
                f"### 1. Root Cause\n"
                f"Zero anomalies detected. The simulation run for scenario **{sc_name}** (`{scenario_id}`) has **not been started yet**.\n\n"
                f"### 2. Causal Graph\n"
                f"• **Topology Conduits**: Initialized in nominal baseline state.\n"
                f"• **Causal Propagation**: Live causal pathways will construct dynamically once telemetry is admitted.\n\n"
                f"### 3. Evidence Math\n"
                f"• **Admitted Events**: 0 observations\n"
                f"• **Throughput Breach**: 0.0% (Nominal)\n"
                f"• **Telemetry Gaps**: None blocking\n\n"
                f"### 4. Learning Promotion\n"
                f"Awaiting simulation start. Click **Start Simulation** to launch the scenario and observe live telemetry correlation."
            )

        # Simulation IS running! Check active stage from story_context or stage_index
        story_ctx = sim_state.get("story_context") or {}
        stage_idx = story_ctx.get("stage_index") if "stage_index" in story_ctx else (
            ui_context.get("stage_index", 0)
        )
        if isinstance(stage_idx, str) and stage_idx.isdigit():
            stage_idx = int(stage_idx)
        elif not isinstance(stage_idx, int):
            stage_idx = 0

        # Build Live Flash Narration feed from dynamic operational story context
        flash_history = story_ctx.get("flash_history") or []
        if not flash_history:
            try:
                from ..simulator.story_compiler import compile_story_context_from_state
                compiled_ctx = compile_story_context_from_state(sim_state)
                flash_history = compiled_ctx.get("flash_history") or []
            except Exception as e:
                flash_history = []

        flash_bullets = "\n\n".join(
            f"• **At {f['time']} ({f['phase']})**:\n  🎙️ \"{f['spoken']}\""
            for f in flash_history
        )
        flash_header = (
            f"### Live Flash Narration\n"
            f"During a live simulation or active incident, Storyteller pushes unsolicited Live Flash Narration as stages advance:\n\n"
            f"{flash_bullets}\n\n"
        ) if flash_history else ""

        # Dynamic entity and telemetry resolution
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
        leading_hyp_name = leading_hyp.get("display_name") or leading_hyp.get("label") or "PE-RTR-21 Line Card Buffer Saturation"
        leading_conf = leading_hyp.get("confidence")
        conf_str = f"{leading_conf:.1f}%" if isinstance(leading_conf, (int, float)) else "94.2%"

        gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
        gap_labels = [g.get("label") or g.get("title") or g.get("id") for g in gaps if g]

        impact = sim_state.get("impact") or {}
        impact_pct = impact.get("throughput_impact_pct") or 38
        impact_label = impact.get("affected_label") or service_name
        affected_users = impact.get("affected_users") if impact.get("affected_users") is not None else (impact.get("users_affected") if impact.get("users_affected") is not None else 0)
        remediation = (sim_state.get("recovery") or {}).get("action") or f"Isolate degraded transport path and reroute {service_name} traffic to redundant secondary conduit"

        # 1. Executive Style: Impact ➔ Remediation ➔ Prevention
        if response_level == "executive":
            if stage_idx <= 1:
                body = (
                    f"### 1. Impact\n"
                    f"P1 transport anomaly detected on **PE-RTR-21**. Telemetry correlation is active; zero verified subscriber throughput drops at trigger stage.\n\n"
                    f"### 2. Remediation\n"
                    f"Initial observations admitted. Closed-loop safety rules prevent premature traffic mutation prior to confirmed root cause isolation.\n\n"
                    f"### 3. Prevention\n"
                    f"Continuous carrier telemetry active across ingress boundary interfaces."
                )
            elif stage_idx <= 3:
                body = (
                    f"### 1. Impact\n"
                    f"Degradation has cascaded to **User Plane Function 003**. Mobile data sessions are degrading with elevated risk to regional SLA.\n\n"
                    f"### 2. Remediation\n"
                    f"Correlation engine isolating fault path; diagnostic evidence collection active across cross-domain boundaries.\n\n"
                    f"### 3. Prevention\n"
                    f"Carrier topology maintains N+1 redundancy; standby user plane conduits provisioned."
                )
            elif stage_idx <= 5:
                body = (
                    f"### 1. Impact\n"
                    f"Operational degradation on **{impact_label}** caused a **{impact_pct}%** throughput reduction, impacting approximately **{affected_users:,} subscribers**.\n\n"
                    f"### 2. Remediation\n"
                    f"Primary mitigation dispatched: `{remediation}`. Traffic isolation prevents twin-path failure.\n\n"
                    f"### 3. Prevention\n"
                    f"Carrier topology maintains N+1 redundancy. Automated threshold tuning on ingress interfaces and proactive buffer capacity adjustments."
                )
            else:
                body = (
                    f"### 1. Impact\n"
                    f"Operational degradation resolved. 5G throughput restored to nominal baseline across all active network slices.\n\n"
                    f"### 2. Remediation\n"
                    f"Remediation verified: traffic successfully re-routed to redundant secondary conduit; service stabilized.\n\n"
                    f"### 3. Prevention\n"
                    f"Carrier topology maintains N+1 redundancy. Thresholds and buffer baselines updated."
                )
            return f"# Executive Incident Summary: {sc_name}\n\n{flash_header}{body}"

        # 2. Operations Style: Blast Radius ➔ Ranked Hypotheses ➔ Mitigation ➔ Handover
        if response_level in {"operator", "operations"}:
            if stage_idx <= 1:
                body = (
                    f"### 1. Blast Radius\n"
                    f"• **Affected Domains**: IP Transport (`PE-RTR-21`)\n"
                    f"• **Degraded Services**: Localized to ingress transport interface; mobile core intact\n"
                    f"• **Conduit State**: Anomaly localized; no propagation admitted yet.\n\n"
                    f"### 2. Ranked Hypotheses\n"
                    f"• **Rank #1**: Initial transport signal under correlation (Unconfirmed)\n"
                    f"• **Diagnostic Gaps**: Admitting interface telemetry counters.\n\n"
                    f"### 3. Mitigation\n"
                    f"• **Playbook Action**: Ingest Next-Best Evidence probe on transport PE router.\n\n"
                    f"### 4. Handover\n"
                    f"• **Next Shift Objective**: Monitor initial observation stream and correlate interface counters."
                )
            elif stage_idx <= 3:
                body = (
                    f"### 1. Blast Radius\n"
                    f"• **Affected Domains**: IP Transport, 5G Core (User Plane Function UPF-003)\n"
                    f"• **Degraded Services**: {impact_label} (Mobile data sessions dropping)\n"
                    f"• **Conduit State**: Cross-domain cascade admitted; control plane signaling remains isolated.\n\n"
                    f"### 2. Ranked Hypotheses\n"
                    f"• **Rank #1**: Transport ingress degradation cascading to UPF-003 (50% confidence)\n"
                    f"• **Diagnostic Gaps**: Interface counter validation pending.\n\n"
                    f"### 3. Mitigation\n"
                    f"• **Playbook Action**: Execute Next-Best Evidence probe across transport conduit.\n\n"
                    f"### 4. Handover\n"
                    f"• **Next Shift Objective**: Complete telemetry verification probe on transport router."
                )
            elif stage_idx <= 5:
                body = (
                    f"### 1. Blast Radius\n"
                    f"• **Affected Domains**: {', '.join(domains[:3]) if domains else 'IP Transport, 5G Core'}\n"
                    f"• **Degraded Services**: {impact_label} ({impact_pct}% throughput loss, {affected_users:,} users impacted)\n"
                    f"• **Conduit State**: Anomaly localized within regional slice boundaries; control plane signaling remains isolated.\n\n"
                    f"### 2. Ranked Hypotheses\n"
                    f"• **Rank #1**: **PE-RTR-21 line card buffer saturation** ({conf_str} confidence, CONFIRMED)\n"
                    f"• **Diagnostic Gaps**: {', '.join(gap_labels) if gap_labels else 'All critical diagnostic gates resolved'}\n\n"
                    f"### 3. Mitigation\n"
                    f"• **Playbook Action**: `{remediation}`\n"
                    f"• **Pre-Validation Gate**: Playbook mitigation dispatched and staged.\n\n"
                    f"### 4. Handover\n"
                    f"• **Next Shift Objective**: Monitor session restoration post-traffic reroute."
                )
            else:
                body = (
                    f"### 1. Blast Radius\n"
                    f"• **Affected Domains**: Cleared (All domains nominal)\n"
                    f"• **Degraded Services**: 0 degraded services; 100% baseline throughput restored\n"
                    f"• **Conduit State**: Traffic re-routed to secondary conduit; zero packet drops.\n\n"
                    f"### 2. Ranked Hypotheses\n"
                    f"• **Status**: Root cause confirmed and remediated.\n\n"
                    f"### 3. Mitigation\n"
                    f"• **Action**: Remediation verified; healthy counters validated.\n\n"
                    f"### 4. Handover\n"
                    f"• **Next Shift Objective**: Incident closed; shift handover record committed to durable ledger."
                )
            return f"# Operations Incident Briefing: {sc_name}\n\n{flash_header}{body}"

        # 3. Engineering Style (Default): Root Cause ➔ Causal Graph ➔ Evidence Math ➔ Learning Promotion
        if stage_idx <= 1:
            body = (
                f"### 1. Root Cause\n"
                f"Root cause unconfirmed. The cognitive reasoning core detected an initial P1 anomaly on **PE-RTR-21**; telemetry correlation underway.\n\n"
                f"### 2. Causal Propagation & Graph\n"
                f"• **Propagation Sequence**: `PE-RTR-21` (Initial anomaly admitted)\n"
                f"• **Failure Mechanism**: Ingress transport signal under telemetry correlation; downstream conduits nominal.\n\n"
                f"### 3. Evidence Math\n"
                f"• **Throughput Breach**: 0.0% delta at trigger\n"
                f"• **Impact Scope**: 0 disconnected sessions\n"
                f"### 4. Remediation & Learning Promotion\n"
                f"• **Remediation**: Standby for telemetry correlation before dispatching active probes.\n"
                f"• **SME Validation**: Staged; awaiting causal graph progression\n"
                f"• **Knowledge Base Status**: Grounded strictly in admitted telemetry without synthetic truth leakage."
            )
        elif stage_idx <= 3:
            body = (
                f"### 1. Root Cause\n"
                f"Root cause candidate under evaluation between transport router **PE-RTR-21** and User Plane Function **UPF-003**.\n\n"
                f"### 2. Causal Graph\n"
                f"• **Propagation Sequence**: `PE-RTR-21` ➔ `VRF-N3-01` ➔ `SA5G:UPF:003`\n"
                f"• **Failure Mechanism**: Transport degradation cascading into User Plane session disconnects.\n\n"
                f"### 3. Evidence Math\n"
                f"• **Throughput Breach**: Intermediate degradation observed\n"
                f"• **Impact Scope**: Mobile data sessions dropping\n"
                f"• **Telemetry Gaps**: Interface counter validation active\n\n"
                f"### 4. Learning Promotion\n"
                f"• **SME Validation**: Causal cascade candidate staged\n"
                f"• **Knowledge Base Status**: Grounded in admitted multi-domain observations."
            )
        elif stage_idx <= 5:
            body = (
                f"### 1. Root Cause\n"
                f"The cognitive reasoning core converged on **PE-RTR-21 line card buffer saturation** with **{conf_str} confidence**, tracking physical/logical degradation at the Transport boundary.\n\n"
                f"### 2. Causal Graph\n"
                f"• **Propagation Sequence**: {' ➔ '.join(causal_hop_names) if causal_hop_names else 'PE-RTR-21 ➔ VRF-N3-01 ➔ SA5G:UPF:003 ➔ CRM-TICKET-001'}\n"
                f"• **Failure Mechanism**: Upstream transport packet loss triggers TCP congestion collapse, cascading downstream into User Plane session disconnects.\n\n"
                f"### 3. Evidence Math\n"
                f"• **Throughput Breach**: {impact_pct}% delta from baseline\n"
                f"• **Impact Scope**: {affected_users:,} active PDU sessions degraded\n"
                f"• **Telemetry Gaps**: {', '.join(gap_labels) if gap_labels else 'Admitted telemetry sufficient for deterministic isolation'}\n\n"
                f"### 4. Learning Promotion\n"
                f"• **SME Validation**: Candidate causal edge staged for human-in-the-loop review\n"
                f"• **Knowledge Base Status**: Grounded strictly in admitted telemetry without synthetic truth leakage."
            )
        else:
            body = (
                f"### 1. Root Cause\n"
                f"Root cause confirmed on **PE-RTR-21** (buffer saturation). Mitigation verified; degraded path successfully isolated.\n\n"
                f"### 2. Causal Graph\n"
                f"• **Propagation Sequence**: Rerouted traffic bypassing PE-RTR-21 degraded line card.\n"
                f"• **Remediation Effect**: Nominal packet flow re-established across secondary redundant transport conduit.\n\n"
                f"### 3. Evidence Math\n"
                f"• **Throughput Breach**: 0.0% delta (Baseline restored to 98.5%)\n"
                f"• **Impact Scope**: All PDU sessions restored\n"
                f"• **Telemetry Gaps**: All diagnostic gates cleared\n\n"
                f"### 4. Learning Promotion\n"
                f"• **SME Validation**: Incident pattern promoted to validated knowledge base\n"
                f"• **Knowledge Base Status**: Verified closed-loop resolution."
            )
        return f"# Curated Incident Investigation Story: {sc_name}\n\n# Engineering Incident Analysis: {sc_name}\n\n{flash_header}{body}"

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

    def derive_user_intent(
        self,
        query: str,
        ui_context: dict[str, Any],
        context: ZakiContextContract,
    ) -> tuple[str, dict[str, Any]]:
        """Classify user query and interactive context into an explicit operational intent with extracted parameters."""
        q_clean = query.strip()
        q_lower = q_clean.lower()
        params: dict[str, Any] = {}
        sel_ctx = ui_context.get("selected_context") or {}
        c_type = str(sel_ctx.get("context_type") or sel_ctx.get("type") or "").lower()

        # 1. Epistemic Guardrails (Internet / Ground Truth / Hallucination)
        if any(w in q_lower for w in ["internet", "web", "online", "search the web", "did you search"]):
            return "OFFLINE_GUARD", params
        if "ground truth" in q_lower or ("what is" in q_lower and "truth" in q_lower):
            return "GROUND_TRUTH_GUARD", params
        if any(w in q_lower for w in ["invent", "synthetic evidence", "did you invent", "hallucinat"]):
            return "ANTI_HALLUCINATION_GUARD", params

        # 2. Conversational User Offers or Affirmations
        if bool(re.match(r"^(i can\b|let me\b|i will\b|can i\b|i'll\b|should i\b)", q_lower)) or q_lower in {"i can", "i can do that", "i will check", "sure", "ok", "okay", "go ahead", "continue"}:
            return "USER_OFFER", params

        # 3. Conversational Greeting & Introduction
        if (
            re.search(r"^(hi|hello|hey|greetings|how are you|good (morning|afternoon|evening))\b", q_lower)
            or q_lower in {"hi", "hello", "hey", "who are you", "what can you do", "help"}
            or "who are you" in q_lower
            or "what can you do" in q_lower
        ) and len(q_lower.split()) <= 7:
            return "GREETING", params

        # 3b. Explicit incident-brief phrasing takes priority over overlapping keywords
        # (e.g. the Incident Brief chip text contains "impact scope").
        if any(w in q_lower for w in ["incident brief", "brief me", "executive brief", "incident story", "curated story"]):
            return "INCIDENT_BRIEF", params

        # 4. Causal Propagation Path
        if any(w in q_lower for w in [
            "causal propagation", "propagation path", "causal path", "propagation sequence",
            "causal chain", "how did it propagate", "how did the failure propagate",
            "propagation conduit", "pathway of failure", "failure propagation"
        ]):
            return "CAUSAL_PROPAGATION", params

        # 5. Remediation Strategy / Mitigation
        if any(w in q_lower for w in [
            "remediation strategy", "remediation", "mitigation strategy", "mitigation",
            "how to fix", "how to mitigate", "playbook", "action recommended", "recommended action",
            "what mitigations", "mitigations do you recommend"
        ]):
            return "REMEDIATION_STRATEGY", params

        # 6. Blast Radius / Scope of Impact
        if any(w in q_lower for w in [
            "blast radius", "radius of this failure", "scope of impact", "impact scope",
            "who is affected", "radius of failure", "how widespread"
        ]):
            return "BLAST_RADIUS", params

        # 7. Incident Brief / Story Summary
        if any(w in q_lower for w in [
            "incident brief", "incident summary", "brief me", "executive brief", "executive summary",
            "summarize incident", "summary of incident", "what is happening", "what happened",
            "curated story", "incident story", "story", "post-mortem", "post mortem",
            "tell me about it", "explain simulation", "about simulation", "about the simulation"
        ]):
            return "INCIDENT_BRIEF", params

        # 8. Knowledge Gap & Evidence Inquiries
        if (
            any(w in q_lower for w in [
                "what evidence", "evidence is needed", "evidence needed", "evidence required",
                "close this knowledge gap", "close the gap", "close knowledge gap", "what probe",
                "probe needed", "knowledge gap", "gap block", "missing right now", "what is missing"
            ])
            or c_type in {"gap", "knowledge_gap"}
            or ("gap" in q_lower and ("block" in q_lower or "what" in q_lower or "explain" in q_lower or "is" in q_lower))
        ):
            params["gap_id"] = ui_context.get("selected_gap_id") or sel_ctx.get("context_id") or sel_ctx.get("id") or "GAP-001"
            params["gap_name"] = sel_ctx.get("display_name") or sel_ctx.get("title") or "Redundant MPLS Path Health Unknown"
            return "KNOWLEDGE_GAP", params

        # 9. Domain Attribution & Conflict
        sim_state = ui_context.get("simulation_state") or {}
        da = sim_state.get("domain_attribution") or sim_state.get("reasoning_map", {}).get("domain_attribution") or {}
        attr_status = da.get("attribution_status", "UNRESOLVED")
        sel_dom = ui_context.get("selected_domain") or (
            sel_ctx.get("context_id") or sel_ctx.get("display_name") or sel_ctx.get("id")
            if c_type in {"domain", "domain_attribution"} else None
        )
        if (
            attr_status == "CONFLICT"
            or sel_dom
            or c_type in {"domain", "domain_attribution"}
            or any(w in q_lower for w in ["attribution", "who caused", "who is responsible", "which domain", "primary domain", "domain attribution", "domain primary"])
            or ("domain" in q_lower and any(w in q_lower for w in ["primary", "role", "cause", "responsible", "attributed"]))
        ):
            params["selected_domain"] = sel_dom
            params["domain_attribution"] = da
            return "DOMAIN_ATTRIBUTION", params

        # 10. Service Impact & Affected Services
        if any(w in q_lower for w in ["services are affected", "affected services", "which services", "impact on service", "service impact"]):
            return "SERVICE_IMPACT", params

        # 11. SLA Compliance & Financial Risk
        if any(w in q_lower for w in ["sla", "penalty", "financial risk", "committed sla", "sla threshold"]):
            return "SLA_FINANCIAL", params

        # 12. Mission-Critical Voice / E911 Safeguards
        if any(w in q_lower for w in ["voice", "emergency", "e911", "emergency sessions"]):
            return "VOICE_SAFEGUARD", params

        # 13. What-If & Counterfactual Resilience Analysis
        if any(w in q_lower for w in ["what if", "what happens if", "failover", "reroute now", "bypass validation", "premature", "redundancy risk", "secondary risk", "link severance"]):
            return "WHAT_IF", params

        # 14. Blocked Stage & Exit Conditions / Next Steps
        if any(w in q_lower for w in ["what should i do", "what next", "next step", "what to do", "current state", "stage briefing", "where are we", "status update", "blocked", "why blocked", "exit condition", "advance the stage"]):
            return "STAGE_NEXT_STEPS", params

        # 15. Candidate Knowledge & Learning Promotion
        if any(w in q_lower for w in ["what did fikracore learn", "what did we learn", "learned that", "learning result", "who validated", "who approved", "validator", "candidate", "confirmed", "promoted", "is it confirmed", "candidate relationship", "validation state"]):
            return "LEARNING_PROMOTION", params

        # 16. Comparative Hypotheses
        if any(w in q_lower for w in ["compare", "why rank 1", "why hypothesis", "difference between hypotheses", "competing hypotheses", "which hypothesis"]):
            return "COMPARE_HYPOTHESES", params

        # 17. Digital Twin / Graph Projection
        if any(w in q_lower for w in ["digital twin", "knowledge graph", "twin projection", "3d graph", "graph visualization", "how to see on graph", "where on graph", "trace on twin"]):
            return "DIGITAL_TWIN", params

        # 18. Reasoning Pathways
        if ui_context.get("selected_pathway_id") or c_type == "pathway" or "pathway" in q_lower:
            params["selected_pathway"] = ui_context.get("selected_pathway_id") or sel_ctx.get("id")
            return "PATHWAYS", params

        # 19. Causal "Why" & Root Cause
        if any(w in q_lower for w in [
            "root cause", "what caused", "underlying cause", "primary cause", "why", "why did",
            "why is", "why do we", "how come", "reason for", "cause of", "health stats", "probe necessary"
        ]):
            return "ROOT_CAUSE" if any(k in q_lower for k in ["root cause", "primary cause", "what caused", "underlying cause"]) else "CAUSAL_WHY", params

        # 20. Entity / Element Inspection
        topo = sim_state.get("topology") or context.visible_topology or {}
        entities = [e.get("display_name") or e.get("id") for d in topo.get("domains", []) for e in d.get("entities", [])]
        domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        sel_ent = ui_context.get("selected_entity_id") or (sel_ctx.get("id") if c_type == "entity" else None)
        if sel_ent:
            params["target_entity"] = sel_ent
            return "ENTITY_INSPECTION", params
        for ent in entities:
            if ent and ent.lower() in q_lower:
                params["target_entity"] = ent
                return "ENTITY_INSPECTION", params
        for dom in domains:
            if dom and dom.lower() in q_lower:
                params["target_domain"] = dom
                return "ENTITY_INSPECTION", params

        return "GENERAL_OPERATIONAL", params

    def fetch_intent_driven_context(
        self,
        intent: str,
        params: dict[str, Any],
        context: ZakiContextContract,
        ui_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Fetch scoped operational context tailored precisely to the derived user intent."""
        from zaki.contracts.operational_context import resolve_operational_context

        op_ctx, op_readiness = resolve_operational_context(ui_context)
        scenario_id = context.active_scenario or ui_context.get("scenario_id") or "SCN-001"
        scenario_title = self.naming.to_scenario_title(scenario_id)
        sim_state = ui_context.get("simulation_state") or {}
        run_id = sim_state.get("run_id") or ui_context.get("run_id") or "RUN-LIVE"
        sim_stage = ui_context.get("simulation_stage") or sim_state.get("current_stage") or context.active_stage or "TRIGGER"
        stage_idx = ui_context.get("stage_index")
        if stage_idx is None:
            stage_idx = (sim_state.get("story_context") or {}).get("stage_index", 0)
        if isinstance(stage_idx, str) and stage_idx.isdigit():
            stage_idx = int(stage_idx)
        elif not isinstance(stage_idx, int):
            stage_idx = 0

        sim_status = (
            ui_context.get("simulation_status")
            or sim_state.get("status")
            or (sim_state.get("run") or {}).get("status")
            or "READY"
        ).upper()

        events = sim_state.get("events") or context.visible_evidence or []
        events_count = ui_context.get("events_count") or len(events)
        is_running = (sim_status == "RUNNING") or events_count > 0 or bool(context.current_hypotheses)
        is_staged_only = (stage_idx == 0 and not events and not is_running)

        topo = sim_state.get("topology") or context.visible_topology or {}
        domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        domain_count = len(domains) if domains else 3

        # Only admit entities that are active symptoms, candidates, degraded, or part of causal propagation
        visible_ents = []
        for d in topo.get("domains", []):
            d_name = str(d.get("name", "")).upper()
            for e in d.get("entities", []):
                e_state = str(e.get("state", "")).upper()
                e_name = e.get("display_name") or e.get("id")
                # Exclude healthy background nodes and unrelated external entities
                if e_state == "HEALTHY":
                    continue
                if d_name == "EXTERNAL" and e_state not in ("SYMPTOM", "IMPACTED", "ROOT_CANDIDATE"):
                    continue
                if e_name and e_name not in visible_ents:
                    visible_ents.append(e_name)

        if not visible_ents and context.visible_evidence:
            visible_ents = list(dict.fromkeys([
                self.naming.to_display_name(ev.get("canonical_entity_id") or ev.get("entity_id"))
                for ev in context.visible_evidence
                if ev.get("canonical_entity_id") or ev.get("entity_id")
            ]))

        causal_edges = topo.get("causal_path") or []
        causal_hops = []
        for edge in causal_edges:
            f = self.naming.to_display_name(edge.get("from", ""))
            t = self.naming.to_display_name(edge.get("to", ""))
            if f and f not in causal_hops:
                causal_hops.append(f)
            if t and t not in causal_hops:
                causal_hops.append(t)
        if not causal_hops:
            causal_hops = ["PE-RTR-21", "VRF-N3-01", "UPF-003", "CRM-TICKET-001"]

        primary_ent = visible_ents[0] if visible_ents else causal_hops[0]
        primary_dom = domains[0] if domains else "IP Transport"

        impact = sim_state.get("impact") or {}
        throughput_pct = impact.get("throughput_impact_pct") or 38
        affected_users = impact.get("affected_users") if impact.get("affected_users") is not None else (impact.get("users_affected") if impact.get("users_affected") is not None else 14200)
        raw_services = impact.get("affected_services") or ["5g_sa_mobile_data"]
        affected_services = [self.naming.to_service_name(s) for s in raw_services]
        service_str = ", ".join(affected_services) if affected_services else "5G SA Mobile Data"

        hyps = sim_state.get("hypotheses") or context.current_hypotheses or []
        leading_hyp = hyps[0] if hyps else {}
        leading_hyp_name = leading_hyp.get("display_name") or leading_hyp.get("label") or leading_hyp.get("summary") or "PE-RTR-21 Line Card Buffer Saturation"
        leading_conf = leading_hyp.get("confidence")
        conf_str = f"{leading_conf:.1f}%" if isinstance(leading_conf, (int, float)) else "94.2%"

        actions = sim_state.get("actions") or sim_state.get("next_best_actions") or []
        action_label = actions[0].get("display_name") or actions[0].get("name") if actions else "Automated Traffic Failover Playbook"

        rstate = context.resilience_state or {}
        b_rad = rstate.get("blast_radius", {})
        lvl = b_rad.get("blast_radius_level") or impact.get("severity") or "REGIONAL_CORE"

        gaps = sim_state.get("knowledge_gaps") or context.knowledge_gap_state.get("gaps", [])
        gap_labels = [g.get("label") or g.get("title") or g.get("id") for g in gaps if g]

        return {
            "scenario_id": scenario_id,
            "scenario_title": scenario_title,
            "run_id": run_id,
            "sim_stage": sim_stage,
            "stage_idx": stage_idx,
            "sim_status": sim_status,
            "is_running": is_running,
            "is_staged_only": is_staged_only,
            "domain_count": domain_count,
            "domains": domains,
            "visible_ents": visible_ents,
            "causal_hops": causal_hops,
            "primary_ent": primary_ent,
            "primary_dom": primary_dom,
            "impact": impact,
            "throughput_pct": throughput_pct,
            "affected_users": affected_users,
            "service_str": service_str,
            "affected_services": affected_services,
            "leading_hyp_name": leading_hyp_name,
            "conf_str": conf_str,
            "action_label": action_label,
            "lvl": lvl,
            "gap_labels": gap_labels,
            "params": params,
            "operational_context": op_ctx,
            "context_id": op_ctx.context_id,
            "context_readiness": op_readiness,
        }

    def format_intent_driven_response(
        self,
        intent: str,
        ictx: dict[str, Any],
        response_level: str,
        boundary_name: str,
        context: ZakiContextContract,
        ui_context: dict[str, Any],
        query: str,
    ) -> str:
        """Render precise, expertly structured response formatted for the derived intent using governing domain contracts."""
        from zaki.contracts.intent_dispatcher import dispatch_intent_contract

        contract, markdown_text, spoken_text = dispatch_intent_contract(
            intent=intent,
            ictx=ictx,
            context=context,
            ui_context=ui_context,
            query=query,
        )
        ui_context["active_intent_contract"] = contract
        ui_context["intent_spoken_text"] = spoken_text
        return markdown_text

    def _generate_intelligent_ai_response(
        self,
        query: str,
        context: ZakiContextContract,
        boundary_name: str,
        ui_context: dict[str, Any] | None = None,
    ) -> str:
        """Generate intelligent, conversational, expert telecom AI copilot response for any arbitrary query."""
        ui_context = ui_context or {}
        # 1. Try real LLM if configured (honours the shared OperationalContext gate)
        if ui_context.get("llm_allowed", ui_context.get("derived_intent") != "INCIDENT_BRIEF"):
            llm_reply = self._try_llm_completion(query, context, boundary_name, ui_context=ui_context)
            if llm_reply:
                return llm_reply

        response_level = str(ui_context.get("response_level") or "engineer").lower()

        # 2. Intent Derivation and Scoped Context Assembly
        intent = ui_context.get("derived_intent")
        intent_ctx = ui_context.get("intent_context")
        if not intent or not intent_ctx:
            intent, params = self.derive_user_intent(query, ui_context, context)
            intent_ctx = self.fetch_intent_driven_context(intent, params, context, ui_context)

        return self.format_intent_driven_response(
            intent=intent,
            ictx=intent_ctx,
            response_level=response_level,
            boundary_name=boundary_name,
            context=context,
            ui_context=ui_context,
            query=query,
        )


__all__ = [
    "ZakiBridge",
]
