"""Task Episode Recorder and Learning Integration for Zaki v1."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..domain.contracts.hypothesis import HypothesisRankingContract
from ..domain.contracts.incident import IncidentContextContract
from ..domain.contracts.intent import OperatorIntentContract
from ..domain.contracts.task import TaskContract
from ..domain.contracts.task_episode import TaskEpisodeContract
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
    ) -> TaskEpisodeContract:
        leading = hypotheses.spec.hypotheses[0] if hypotheses.spec.hypotheses else None
        domains = list({h.domain for h in hypotheses.spec.hypotheses if h.domain and h.domain != "unknown"})

        episode = TaskEpisodeContract(
            task_id=task.task_id,
            incident_id=incident.incident_id,
            operator_intent=intent.spec.natural_language,
            fcaps=intent.spec.fcaps,
            domains=domains,
            context={"scenario_id": incident.scenario_id, "terminal_state": str(getattr(inv_result, "terminal_state", "EXPLAINED"))},
            evidence_observed=leading.supporting_evidence if leading else [],
            ranked_hypotheses=[h.model_dump(mode="python") for h in hypotheses.spec.hypotheses[:5]],
            agent_recommendation=f"Address root cause at {leading.root_entity}" if leading else None,
            outcome=str(getattr(inv_result, "terminal_state", "SUCCESS")),
            learned_pattern={
                "trigger_service": intent.spec.subject.get("service"),
                "root_domain": leading.domain if leading else "unknown",
                "root_entity": leading.root_entity if leading else "unknown",
            },
        )
        default_episodic_memory.record_episode(episode)
        return episode
