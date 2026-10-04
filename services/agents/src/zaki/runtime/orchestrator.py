"""Deterministic Agent Orchestrator for Zaki v1 Dark NOC."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..contracts.agent import AgentTaskContract
from ..contracts.hypothesis import HypothesisRankingContract
from ..contracts.incident import IncidentContextContract
from ..contracts.intent import OperatorIntentContract
from ..contracts.story import IncidentStoryContract, StoryStatement
from ..contracts.task import TaskContract
from ..contracts.task_episode import TaskEpisodeContract
from ..enums import AuthorityLevel, PresentationDepth, StatementProvenance, TaskStatus
from ..agents.registry import default_agent_registry
from ..agents.dispatcher import default_agent_dispatcher
from ..fikracore.adapter import FikraCoreAdapter, default_fikracore_adapter
from ..governance.audit import default_audit_logger
from ..governance.hitl import default_hitl_manager
from ..governance.policy_engine import default_policy_engine
from ..intent.manager import default_intent_manager
from ..operations.incident_ledger import default_incident_ledger
from ..operations.task_ledger import default_task_ledger
from .state import AuthoritativeRunState


class ZakiOrchestrator:
    """Stateful orchestrator coordinating Intent, Tasks, Domain Agents, and FikraCore."""

    def __init__(
        self,
        fikracore_adapter: Optional[FikraCoreAdapter] = None,
        agent_registry=None,
        agent_dispatcher=None,
        intent_manager=None,
        task_ledger=None,
        incident_ledger=None,
        policy_engine=None,
        audit_logger=None,
        hitl_manager=None,
    ) -> None:
        self.fikracore = fikracore_adapter or default_fikracore_adapter
        self.agents = agent_registry or default_agent_registry
        self.dispatcher = agent_dispatcher or default_agent_dispatcher
        self.intent_mgr = intent_manager or default_intent_manager
        self.task_ledger = task_ledger or default_task_ledger
        self.incident_ledger = incident_ledger or default_incident_ledger
        self.policy = policy_engine or default_policy_engine
        self.audit = audit_logger or default_audit_logger
        self.hitl = hitl_manager or default_hitl_manager

    def investigate(
        self,
        intent_or_query: Union[str, OperatorIntentContract],
        scenario_id: Optional[str] = None,
        run_directory: Optional[Path] = None,
        evidence: Optional[List[Any]] = None,
        run_input: Optional[Any] = None,
        provider: Optional[Any] = None,
        authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
        requested_by: str = "operator",
        step_callback: Optional[Callable[[str, Any], None]] = None,
    ) -> Dict[str, Any]:
        """Execute end-to-end Zaki investigation flow preserving FikraCore reasoning parity."""

        # 1. Capture & Normalize Intent
        if isinstance(intent_or_query, str):
            intent = self.intent_mgr.capture_intent(
                query=intent_or_query,
                requested_by=requested_by,
                authority=authority,
            )
        else:
            intent = intent_or_query

        self.audit.log_event("INTENT_RECEIVED", intent.model_dump(mode="python"))

        # 2. Resolve Incident Context & Create Task
        title = f"Investigation: {intent.spec.subject.get('service', 'Telecom Outage')}"
        incident = self.incident_ledger.create_incident(
            title=title,
            scenario_id=scenario_id,
            authority=authority,
            metadata={"intent_id": intent.intent_id},
        )
        task = self.task_ledger.create_task(
            incident_id=incident.incident_id,
            intent_id=intent.intent_id,
            owner=requested_by,
            metadata={"scenario_id": scenario_id},
        )
        self.incident_ledger.attach_task(incident.incident_id, task.task_id)

        # 2b. Initialize Dynamic Operational Spine (TaskEpisodeContract)
        task_episode = TaskEpisodeContract(
            task_id=task.task_id,
            incident_id=incident.incident_id,
            operator_intent=intent.spec.natural_language,
            fcaps=intent.spec.fcaps,
            domains=[],
            context={"scenario_id": scenario_id},
            operational_context_ref=f"CTX-{task.task_id}",
            behavior_contract_ref="BEHAVIOR-NOC-SME-DEFAULT",
        )

        self.audit.log_event(
            "TASK_CREATED",
            {"task_id": task.task_id, "incident_id": incident.incident_id, "episode_id": task_episode.episode_id},
            task_id=task.task_id,
            incident_id=incident.incident_id,
        )

        # 3. Policy & Tool Authorization Check
        policy_decision = self.policy.evaluate(
            actor="zaki_orchestrator",
            tool_id="fikracore.correlate",
            required_authority=AuthorityLevel.LEVEL_1_ANALYZE,
            current_authority=authority,
        )
        self.audit.log_event(
            "TOOL_AUTHORIZED" if policy_decision.decision.value == "ALLOW" else "TOOL_DENIED",
            policy_decision.to_dict(),
            task_id=task.task_id,
            incident_id=incident.incident_id,
        )

        # 4. Invoke FikraCore Authoritative Investigation
        run_state = AuthoritativeRunState(
            run_id=f"RUN-{task.task_id}",
            scenario_id=scenario_id,
            task_id=task.task_id,
            incident_id=incident.incident_id,
        )

        self.audit.log_event(
            "FIKRACORE_STAGE_STARTED",
            {"stage": "INGESTION"},
            task_id=task.task_id,
            incident_id=incident.incident_id,
            run_id=run_state.run_id,
        )

        if run_directory:
            inv_res = self.fikracore.investigate_directory(
                run_directory=Path(run_directory),
                provider=provider,
                step_callback=step_callback,
            )
        elif run_input and evidence is not None:
            inv_res = self.fikracore.start_investigation(
                run_input=run_input,
                evidence=evidence,
                step_callback=step_callback,
                provider=provider,
            )
        else:
            # Fallback: find scenario run directory if scenario_id given
            inv_res = None
            if scenario_id:
                base_dir = Path(__file__).resolve().parent.parent.parent / "engine_stack" / "engines" / "telecom_brain" / "simulator"
                # Check known run paths
                for rpath in [
                    base_dir / "runs" / f"RUN-{scenario_id}-L1-SEED-42001",
                    base_dir / "runs" / "RUN-SCN-001-L1-SEED-42001",
                    base_dir / "h4_runs" / f"RUN-{scenario_id}",
                ]:
                    if rpath.exists():
                        inv_res = self.fikracore.investigate_directory(rpath, provider=provider, step_callback=step_callback)
                        break

            if not inv_res:
                # Abstain gracefully with INSUFFICIENT_EVIDENCE
                from engine_stack.engines.telecom_brain.investigation.contracts import GeneratedRunInput
                dummy_run = GeneratedRunInput(run_id=run_state.run_id, scenario_id=scenario_id or "UNKNOWN", difficulty_profile="L1", seed=42)
                inv_res = self.fikracore.start_investigation(dummy_run, [], step_callback=step_callback, provider=provider)

        # 5. Harvest authoritatively ranked hypotheses without altering scores
        hypotheses_contract: HypothesisRankingContract = self.fikracore.get_ranked_hypotheses(inv_res.run_id)
        run_state.ranked_hypotheses = [h.model_dump(mode="python") for h in hypotheses_contract.spec.hypotheses]
        run_state.terminal_state = inv_res.terminal_state.value if hasattr(inv_res.terminal_state, "value") else str(inv_res.terminal_state)

        self.audit.log_event(
            "HYPOTHESES_UPDATED",
            {
                "count": len(hypotheses_contract.spec.hypotheses),
                "leading": hypotheses_contract.spec.leading_hypothesis_id,
                "terminal_state": run_state.terminal_state,
            },
            task_id=task.task_id,
            incident_id=incident.incident_id,
            run_id=inv_res.run_id,
        )

        # 6. Update Incident Ledger & Dynamic Task Episode Spine
        leading_id = hypotheses_contract.spec.leading_hypothesis_id
        leading_h = hypotheses_contract.spec.hypotheses[0] if hypotheses_contract.spec.hypotheses else None
        domains = list({h.domain for h in hypotheses_contract.spec.hypotheses if h.domain and h.domain != "unknown"})
        
        # Dynamically populate Task Episode Spine
        task_episode.domains = domains
        task_episode.ranked_hypotheses = [h.model_dump(mode="python") for h in hypotheses_contract.spec.hypotheses]
        task_episode.evidence_observed = leading_h.supporting_evidence if leading_h else []
        if leading_h:
            task_episode.agent_recommendation = f"Address root cause at {leading_h.root_entity}"

        self.incident_ledger.update_incident_state(
            incident_id=incident.incident_id,
            current_stage="CONVERGENCE",
            terminal_state=run_state.terminal_state,
            ranked_hypotheses=hypotheses_contract.spec.hypotheses,
            leading_hypothesis_id=leading_id,
            domain_involvement=domains,
        )

        # 7. Delegate to Domain Agents for localized verification
        delegation_results = []
        for dom in domains[:2]:  # Top domains
            agent_task = AgentTaskContract(
                task_id=f"SUBTASK-{task.task_id}-{dom}",
                incident_id=incident.incident_id,
                parent_task_id=task.task_id,
                intent=intent.spec.natural_language,
                domain=dom,
                objective=f"Verify localized telemetry impact for {dom}",
                evidence=[{"evidence_id": eid} for h in hypotheses_contract.spec.hypotheses if h.domain == dom for eid in h.supporting_evidence[:3]],
                requested_capability=f"{dom.lower()}-analysis",
            )
            d_res = self.dispatcher.dispatch(agent_task)
            delegation_results.append(d_res.model_dump(mode="python"))
            self.audit.log_event(
                "DOMAIN_AGENT_RESPONDED",
                {"agent_id": d_res.agent_id, "domain": dom, "status": d_res.status},
                task_id=task.task_id,
                incident_id=incident.incident_id,
                run_id=inv_res.run_id,
            )

        task_episode.human_actions.extend(delegation_results)

        # 7b. Step 3 Active Discrimination Probes (if multiple competing hypotheses)
        if len(hypotheses_contract.spec.hypotheses) > 1:
            try:
                from engine_stack.engines.telecom_brain.capabilities.probe_dispatcher import default_probe_dispatcher
                discrim_res = default_probe_dispatcher.run_discrimination_cycle(
                    hypotheses=hypotheses_contract.spec.hypotheses,
                    max_probes=2,
                )
                if discrim_res.get("probes_dispatched"):
                    task_episode.discrimination_probes.extend(discrim_res["probes_dispatched"])
                    self.audit.log_event(
                        "DISCRIMINATION_PROBES_DISPATCHED",
                        {"count": len(discrim_res["probes_dispatched"])},
                        task_id=task.task_id,
                        incident_id=incident.incident_id,
                        run_id=inv_res.run_id,
                    )
            except Exception:
                pass

        # 8. Check for Knowledge Gaps & Next Best Evidence
        gaps_data = self.fikracore.get_knowledge_gaps(inv_res.run_id)
        if gaps_data.get("discovery_mode"):
            self.audit.log_event(
                "KNOWLEDGE_GAP_DETECTED",
                {"candidate_count": len(gaps_data.get("candidate_relationships", []))},
                task_id=task.task_id,
                incident_id=incident.incident_id,
                run_id=inv_res.run_id,
            )

        # 9. Build Multi-Depth Incident Story
        from ..storyteller.presentation import PresentationProjector
        story = PresentationProjector.build_story(
            incident=incident,
            hypotheses=hypotheses_contract,
            inv_result=inv_res,
            intent=intent,
            gaps=gaps_data,
            depth=PresentationDepth.OPERATOR,
        )

        # 10. Record Task Episode for Structured Learning (Finalize Spine)
        from ..learning.episode_recorder import EpisodeRecorder
        episode = EpisodeRecorder.record_episode(
            task=task,
            incident=incident,
            intent=intent,
            hypotheses=hypotheses_contract,
            inv_result=inv_res,
            existing_episode=task_episode,
        )

        self.task_ledger.update_status(task.task_id, TaskStatus.COMPLETED)
        self.audit.log_event(
            "TASK_COMPLETED",
            {"task_id": task.task_id, "terminal_state": run_state.terminal_state},
            task_id=task.task_id,
            incident_id=incident.incident_id,
            run_id=inv_res.run_id,
        )

        return {
            "status": "SUCCESS",
            "task": task,
            "incident": incident,
            "intent": intent,
            "investigation_result": inv_res,
            "ranked_hypotheses": hypotheses_contract,
            "knowledge_gaps": gaps_data,
            "domain_delegations": delegation_results,
            "story": story,
            "episode": episode,
            "audit_events": self.audit.get_events(task_id=task.task_id),
        }


default_zaki_orchestrator = ZakiOrchestrator()
