"""Zaki Incident Storyteller Service."""

from __future__ import annotations

from typing import Any, Dict, Optional
from ..contracts.story import IncidentStoryContract
from ..enums import PresentationDepth
from .presentation import PresentationProjector


class ZakiStoryteller:
    """Provides human-readable and operator narratives grounded in FikraCore state."""

    def format_story_for_cli(self, story: IncidentStoryContract) -> str:
        depth = story.presentation_depth
        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"  ZAKI INCIDENT STORY  [{depth.value} VIEW]")
        lines.append(f"{'='*70}\n")
        lines.append(f"INCIDENT: {story.title}")
        lines.append(f"RUN ID:   {story.run_id}\n")
        lines.append(f"SUMMARY:\n  {story.summary}\n")

        if story.leading_hypothesis:
            lh = story.leading_hypothesis
            lines.append("CURRENT LEADING HYPOTHESIS:")
            lines.append(f"  Root Entity: {lh.get('root_entity')} ({lh.get('domain')})")
            lines.append(f"  Confidence:  {lh.get('score')}  [{lh.get('role')}]")
            lines.append(f"  Statement:   {lh.get('statement')}")
            lines.append(f"  Supporting:  {len(lh.get('supporting_evidence', []))} signals")
            lines.append(f"  Contradicting: {len(lh.get('contradicting_evidence', []))} signals\n")

        if depth in (PresentationDepth.OPERATOR, PresentationDepth.DEEP_TECHNICAL):
            if story.competing_hypotheses:
                lines.append(f"COMPETING HYPOTHESES ({len(story.competing_hypotheses)}):")
                for ch in story.competing_hypotheses[:3]:
                    lines.append(f"  • #{ch.get('rank')} {ch.get('root_entity')} ({ch.get('domain')}): score {ch.get('score')} [{ch.get('role')}]")
                lines.append("")

            lines.append("PROVENANCE-BACKED TIMELINE:")
            for stmt in story.timeline_statements:
                lines.append(f"  [{stmt.provenance.value}] {stmt.text}")
            lines.append("")

        if depth == PresentationDepth.DEEP_TECHNICAL and story.technical_details:
            lines.append("12-FACTOR SYNTHESIS CORE BREAKDOWN:")
            for dim, val in story.technical_details.get("score_dimensions", {}).items():
                lines.append(f"  - {dim}: {val}")
            lines.append("")

        lines.append(f"NEXT RECOMMENDED ACTION:\n  {story.next_best_action}\n")
        lines.append(f"{'='*70}\n")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Zaki Chat UI — Incident Brief (8-section structured Markdown)
    # ------------------------------------------------------------------

    def render_incident_brief(self, ictx: Dict[str, Any], ui_context: Optional[Dict[str, Any]] = None) -> str:
        """Build an IncidentStory from live operational context and format it
        using the canonical storyteller render_story() formatter.

        Zaki owns the build (cognitive augmentation of live sim state).
        storyteller.conversation.intents.render_story() owns the format contract.
        The built story is stashed on ``ui_context['incident_story']`` so the API
        layer can derive the narrative / visual explanation from the same object.
        """
        from storyteller.conversation.intents import render_story

        story = self.build_incident_story(ictx)
        if ui_context is not None:
            ui_context["incident_story"] = story
        return render_story(story)

    def build_incident_story(self, ictx: Dict[str, Any]) -> Any:
        """Build a storyteller IncidentStory from live operational context."""

        from storyteller.reasoning.story import (
            IncidentStory,
            CausalChain,
            CausalStep,
            HypothesisAssessment,
        )
        from storyteller.knowledge.provenance import ProvenanceFact, CONFIRMED_ROOT_CAUSE

        # --- Services ---
        raw_services = ictx.get("affected_services") or []
        service_str = ictx.get("service_str", "")
        if raw_services:
            services = [ProvenanceFact(value=s) for s in raw_services if s]
        elif service_str:
            services = [ProvenanceFact(value=s.strip()) for s in service_str.split(",") if s.strip()]
        else:
            services = []

        # --- Network functions / topology entities ---
        # Strictly include entities relevant to the incident, ignoring generic baseline placeholders
        nf_entities: list[ProvenanceFact] = []
        visible_ents = ictx.get("visible_ents") or []
        causal_hops = ictx.get("causal_hops") or []
        entity_sources = visible_ents or causal_hops
        unrelated_placeholders = {
            "External Internet",
            "Roaming Partner 01",
            "Third Party VAS Gateway",
            "Enterprise Users",
            "Network Services",
        }
        for ent in entity_sources:
            if ent and str(ent).strip() not in unrelated_placeholders:
                slug = str(ent).replace(":", "-").replace(" ", "-").upper()
                nf_entities.append(ProvenanceFact(
                    value=f"Network entity {ent}",
                    slug=slug,
                ))

        # --- Hypothesis assessments ---
        sim_state = ictx.get("_sim_state") or {}
        hyps_raw = sim_state.get("hypotheses") or []
        hyp_assessments: list[HypothesisAssessment] = []
        sim_status = ictx.get("sim_status", "ACTIVE").upper()
        leading_hyp_name = ictx.get("leading_hyp_name", "")
        leading_conf_raw = ictx.get("_leading_conf")  # float or None

        if hyps_raw:
            for i, h in enumerate(hyps_raw):
                name = (
                    h.get("display_name")
                    or h.get("label")
                    or h.get("summary")
                    or h.get("name")
                    or f"Hypothesis {i + 1}"
                )
                conf_raw = h.get("confidence")
                if isinstance(conf_raw, (int, float)):
                    # confidence comes as percentage (e.g. 61.0) — normalise to [0,1]
                    score = conf_raw / 100.0 if conf_raw > 1 else float(conf_raw)
                else:
                    score = 0.0
                is_leading = i == 0
                if is_leading and sim_status == "RESOLVED":
                    status = "confirmed"
                elif is_leading:
                    status = "plausible"
                else:
                    status = "candidate"
                ev_ids = h.get("supporting_evidence") or h.get("evidence_ids") or []
                evidence_facts = self._resolve_evidence(ev_ids, sim_state)
                hyp_assessments.append(HypothesisAssessment(
                    hypothesis=ProvenanceFact(value=name),
                    status=status,
                    score=score,
                    evidence=evidence_facts,
                    explanation=h.get("statement") or h.get("summary") or "",
                ))
        elif leading_hyp_name:
            # Fallback: build a single entry from the flat ictx fields
            conf_str = ictx.get("conf_str", "")
            try:
                score = float(conf_str.rstrip("%")) / 100.0 if conf_str else 0.0
            except (ValueError, AttributeError):
                score = 0.0
            status = "confirmed" if sim_status == "RESOLVED" else "plausible"
            hyp_assessments.append(HypothesisAssessment(
                hypothesis=ProvenanceFact(value=leading_hyp_name),
                status=status,
                score=score,
                evidence=[],
                explanation=leading_hyp_name,
            ))

        # --- Causal chain from causal_hops (topology edges) ---
        causal_steps: list[CausalStep] = []
        for hop in causal_hops:
            if hop and str(hop).strip() not in unrelated_placeholders:
                causal_steps.append(CausalStep(
                    label=hop,
                    claim_type="observation",
                    fact=ProvenanceFact(value=hop),
                ))
        chain = CausalChain(steps=causal_steps) if causal_steps else None

        # --- Root cause (only when resolved and confirmed) ---
        root_cause: Optional[ProvenanceFact] = None
        if sim_status == "RESOLVED" and leading_hyp_name:
            root_cause = ProvenanceFact(
                value=leading_hyp_name,
                relationship=CONFIRMED_ROOT_CAUSE,
            )

        # --- Remediations ---
        remediations: list[ProvenanceFact] = []
        action_label = ictx.get("action_label")
        if action_label:
            remediations.append(ProvenanceFact(value=str(action_label)))

        # --- Correlation Metadata & Contextual Coverage ---
        # Correlation Coverage measures whether FikraCore was able to establish
        # a meaningful correlation across the admitted evidence and involved entities.
        domains = ictx.get("domains") or []
        events_count = ictx.get("events_count") or len(ictx.get("_sim_state", {}).get("events", []))
        ev_admitted = len(hyp_assessments[0].evidence) if hyp_assessments and hyp_assessments[0].evidence else events_count

        coverage_score = 0.0
        if hyp_assessments and ev_admitted > 0:
            # If leading hypothesis has admitted evidence and causal path is mapped
            coverage_score = min(1.0, 0.65 + (0.05 * min(len(domains), 3)) + (0.1 if chain else 0.0) + (0.1 if leading_conf_raw and leading_conf_raw >= 0.7 else 0.05))
        elif hyp_assessments:
            coverage_score = 0.60
        elif events_count > 0:
            coverage_score = 0.40

        scenario_title = (
            ictx.get("scenario_title")
            or ictx.get("incident_name")
            or ictx.get("display_name")
            or ""
        )
        if not scenario_title and ictx.get("scenario_id"):
            try:
                from engine_stack.engines.telecom_brain.presentation.naming import default_naming_resolver
                resolved = default_naming_resolver.to_scenario_title(ictx["scenario_id"])
                if resolved and not resolved.lower().startswith("scenario "):
                    scenario_title = resolved
            except Exception:
                pass
        if not scenario_title and hyp_assessments:
            scenario_title = hyp_assessments[0].hypothesis.value

        correlation_metadata: Dict[str, Any] = {
            "correlation_scope": "correlated",
            "contributing_domains": [d for d in domains if str(d).upper() not in ("UNKNOWN", "NONE", "EXTERNAL")],
            "correlation_score": leading_conf_raw,
            "coverage": round(coverage_score, 2),
            "evidence_admitted_count": ev_admitted,
            "scenario_title": scenario_title,
            "incident_name": scenario_title,
        }

        # --- Timeline (gap labels as open findings) ---
        gap_labels = ictx.get("gap_labels") or []

        # --- Unresolved questions derived from evidence state ---
        unresolved: list[str] = list(gap_labels)
        if not hyp_assessments:
            unresolved.append("root cause not yet confirmed — insufficient evidence")
        if not remediations:
            unresolved.append("no remediation recorded")

        story = IncidentStory(
            incident_id=ictx.get("scenario_id", "SCN-UNKNOWN"),
            title=scenario_title,
            summary=self._build_operational_summary(ictx),
            severity=ictx.get("severity") or "MAJOR",
            status=sim_status,
            services=services,
            network_functions=nf_entities,
            hypotheses=hyp_assessments,
            causal_chain=chain,
            root_cause=root_cause,
            remediations=remediations,
            recovery_events=[],
            correlation_metadata=correlation_metadata,
            unresolved_questions=unresolved,
            generated_by="zaki-cognitive",
        )

        return story

    @staticmethod
    def _resolve_evidence(ev_ids: list, sim_state: Dict[str, Any]) -> list:
        """Translate evidence IDs into operator-readable signal statements.

        Each ID is resolved against the admitted events in the live state. IDs
        that do not resolve to a real event are dropped (never rendered as bare
        machine IDs). Identical signals (e.g. duplicate alarm re-deliveries) are
        collapsed. The original event ID is retained as the provenance slug so
        every line stays traceable to its source record.
        """
        from storyteller.knowledge.provenance import ProvenanceFact

        events = list(sim_state.get("events") or []) + list(sim_state.get("raw_events") or [])
        by_id: Dict[str, Dict[str, Any]] = {}
        for e in events:
            for key in ("event_id", "evidence_id"):
                if e.get(key):
                    by_id.setdefault(str(e[key]), e)

        facts: list = []
        seen_text: set = set()
        for raw in dict.fromkeys(str(x) for x in ev_ids if x):
            evt = by_id.get(raw)
            if not evt:
                continue
            kind = str(evt.get("badge") or evt.get("evidence_type") or evt.get("category") or "SIGNAL").upper()
            title = str(evt.get("title") or evt.get("display_name") or "").strip()
            if not title:
                continue
            # "INFRA:K8S:CORE-A: KUBERNETES_CLUSTER_DEGRADED" -> entity + readable condition
            entity, _, condition = title.partition(": ")
            if condition:
                condition = condition.replace("_", " ").title()
                text = f"{kind} · {entity} — {condition}"
            else:
                text = f"{kind} · {title}"
            ts = evt.get("time")
            if ts:
                text = f"{text} ({ts})"
            dedupe_key = f"{kind}|{title}"
            if dedupe_key in seen_text:
                continue
            seen_text.add(dedupe_key)
            facts.append(ProvenanceFact(value=text, slug=raw))
        return facts

    @staticmethod
    def _build_operational_summary(ictx: Dict[str, Any]) -> str:
        """Construct a dynamic, executive-grade operational narrative (Option A)
        strictly grounded in realtime telemetry and active findings.
        Prominently highlights entities, numbers, percentages, and metrics.
        Never outputs static mock strings or unhandled raw enums like UNKNOWN.
        """
        name = str(ictx.get("scenario_title") or "Operational Incident").strip()
        severity = str(ictx.get("severity") or "P1").upper()
        if not severity.startswith("P") and severity not in ("CRITICAL", "MAJOR", "MINOR"):
            severity = "P1"

        service_str = str(ictx.get("service_str") or "").strip()

        # Clean domain names, filtering out UNKNOWN/EXTERNAL/NONE/UNASSIGNED
        raw_domains = ictx.get("domains") or []
        clean_domains = [
            str(d).replace("_", " ").title()
            for d in raw_domains
            if str(d).upper() not in ("UNKNOWN", "NONE", "UNASSIGNED", "EXTERNAL")
        ]
        if not clean_domains and ictx.get("primary_dom"):
            p_dom = str(ictx.get("primary_dom")).replace("_", " ").title()
            if p_dom.upper() not in ("UNKNOWN", "NONE", "UNASSIGNED", "EXTERNAL"):
                clean_domains = [p_dom]
        domain_str = " & ".join(clean_domains) if clean_domains else ""

        leading_hyp = str(ictx.get("leading_hyp_name") or "").strip()
        conf_str = str(ictx.get("conf_str") or "").strip()
        throughput_pct = ictx.get("throughput_pct")
        affected_users = ictx.get("affected_users")
        sim_status = str(ictx.get("sim_status") or "ACTIVE").upper()
        action_label = str(ictx.get("action_label") or ictx.get("remediation_strategy") or "").strip()

        # Sentence 1: Incident nature & business degradation
        if service_str and name and service_str.lower() not in name.lower():
            lead_phrase = f"{severity} Operational Incident: Active degradation on **{service_str}** ({name})"
        elif service_str:
            lead_phrase = f"{severity} Operational Incident: Active degradation on **{service_str}**"
        else:
            lead_phrase = f"{severity} Operational Incident: **{name}**"

        impact_clauses: list[str] = []
        if throughput_pct is not None:
            impact_clauses.append(f"a **{throughput_pct}% throughput loss**")
        if affected_users is not None:
            impact_clauses.append(f"impacting approximately **{affected_users:,} subscribers**")
        if domain_str:
            impact_clauses.append(f"across the **{domain_str}** domain")

        if impact_clauses:
            first_sentence = f"{lead_phrase} with {', '.join(impact_clauses)}."
        else:
            first_sentence = f"{lead_phrase}."

        # Sentence 2: Root cause / Hypothesis localization
        second_sentence = ""
        if leading_hyp:
            conf_suffix = f" with **{conf_str} confidence**" if conf_str else ""
            if leading_hyp.lower() in name.lower() or name.lower() in leading_hyp.lower():
                second_sentence = f"Root cause localized to **{leading_hyp}**{conf_suffix}."
            else:
                second_sentence = f"Telemetry and correlation point to **{leading_hyp}**{conf_suffix}."

        # Sentence 3: Remediation / Status
        third_sentence = ""
        if action_label:
            third_sentence = f"Mitigation strategy **{action_label}** is staged for execution."
        elif sim_status == "RESOLVED":
            third_sentence = "Investigation concluded: corrective actions validated and nominal telemetry restored."
        elif sim_status == "ACTIVE":
            third_sentence = "Dynamic telemetry correlation and containment in progress."

        narrative_parts = [s for s in (first_sentence, second_sentence, third_sentence) if s]
        return " ".join(narrative_parts)


default_storyteller = ZakiStoryteller()
