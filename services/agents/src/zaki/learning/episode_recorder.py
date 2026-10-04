"""
Task Episode Recorder and Dynamic Operational Spine Finalizer
============================================================
Records operational investigations as structured task episodes in episodic memory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from ..contracts.hypothesis import HypothesisRankingContract
from ..contracts.incident import IncidentContextContract
from ..contracts.intent import OperatorIntentContract
from ..contracts.task import TaskContract
from ..contracts.task_episode import TaskEpisodeContract
from ..memory.stores import default_episodic_memory


class EpisodeRecorder:
    """Records completed operational investigations as structured task episodes."""

    @staticmethod
    def record_episode(
        task: TaskContract,
        incident: IncidentContextContract,
        intent: OperatorIntentContract,
        hypotheses: HypothesisRankingContract,
        inv_result: Any,
        existing_episode: Optional[TaskEpisodeContract] = None,
    ) -> TaskEpisodeContract:
        leading = hypotheses.spec.hypotheses[0] if hypotheses.spec.hypotheses else None
        domains = list({h.domain for h in hypotheses.spec.hypotheses if h.domain and h.domain != "unknown"})

        if existing_episode:
            episode = existing_episode
            episode.domains = domains or episode.domains
            episode.ranked_hypotheses = [h.model_dump(mode="python") for h in hypotheses.spec.hypotheses]
            if leading:
                episode.evidence_observed = leading.supporting_evidence
                episode.agent_recommendation = f"Address root cause at {leading.root_entity}"
                episode.learned_pattern = {
                    "trigger_service": intent.spec.subject.get("service") if hasattr(intent.spec, "subject") else None,
                    "root_domain": leading.domain,
                    "root_entity": leading.root_entity,
                }
            episode.outcome = str(getattr(inv_result, "terminal_state", "SUCCESS"))
            episode.closed_at = datetime.now(timezone.utc)
        else:
            episode = TaskEpisodeContract(
                task_id=task.task_id,
                incident_id=incident.incident_id,
                operator_intent=intent.spec.natural_language,
                fcaps=intent.spec.fcaps,
                domains=domains,
                context={"scenario_id": incident.scenario_id, "terminal_state": str(getattr(inv_result, "terminal_state", "EXPLAINED"))},
                operational_context_ref=f"CTX-{task.task_id}",
                behavior_contract_ref="BEHAVIOR-NOC-SME-DEFAULT",
                evidence_observed=leading.supporting_evidence if leading else [],
                ranked_hypotheses=[h.model_dump(mode="python") for h in hypotheses.spec.hypotheses[:5]],
                agent_recommendation=f"Address root cause at {leading.root_entity}" if leading else None,
                outcome=str(getattr(inv_result, "terminal_state", "SUCCESS")),
                learned_pattern={
                    "trigger_service": intent.spec.subject.get("service") if hasattr(intent.spec, "subject") else None,
                    "root_domain": leading.domain if leading else "unknown",
                    "root_entity": leading.root_entity if leading else "unknown",
                },
                closed_at=datetime.now(timezone.utc),
            )

        default_episodic_memory.record_episode(episode)
        return episode
