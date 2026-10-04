"""Memory subsystem for Zaki v1 Dark NOC."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..contracts.task_episode import TaskEpisodeContract


class EpisodicMemory:
    """Stores structured task episodes and incident histories."""

    def __init__(self) -> None:
        self._episodes: Dict[str, TaskEpisodeContract] = {}

    def record_episode(self, episode: TaskEpisodeContract) -> None:
        self._episodes[episode.episode_id] = episode

    def get_episode(self, episode_id: str) -> Optional[TaskEpisodeContract]:
        return self._episodes.get(episode_id)

    def list_episodes(self, domain: Optional[str] = None) -> List[TaskEpisodeContract]:
        episodes = list(self._episodes.values())
        if domain:
            episodes = [e for e in episodes if domain in e.domains]
        return episodes


class WorkflowMemory:
    """Stores operational engineering workflows and playbooks."""

    def __init__(self) -> None:
        self._workflows: Dict[str, Dict[str, Any]] = {
            "TRANSPORT_BGP_DEGRADATION": {
                "name": "IP Transport BGP Recovery",
                "domain": "IP_TRANSPORT",
                "recommended_steps": [
                    "Query router BGP neighbor telemetry",
                    "Analyze MPLS/LSP path continuity",
                    "Verify interface error counters",
                    "Propose traffic reroute with HITL",
                ],
            }
        }

    def get_workflow(self, key: str) -> Optional[Dict[str, Any]]:
        return self._workflows.get(key)


class SemanticMemory:
    """Stores validated operational knowledge (delegated to FikraCore knowledge graph)."""

    def __init__(self) -> None:
        self._validated_relations: List[Dict[str, Any]] = []

    def add_validated_knowledge(self, rel: Dict[str, Any]) -> None:
        self._validated_relations.append(rel)

    def list_validated_knowledge(self) -> List[Dict[str, Any]]:
        return list(self._validated_relations)


class ProceduralMemory:
    """Stores certified agent skills and automation procedures."""

    def __init__(self) -> None:
        self._skills: Dict[str, Dict[str, Any]] = {
            "pdu-session-investigation": {"certified": True, "level": 1},
            "router-bgp-investigation": {"certified": True, "level": 1},
        }

    def is_certified(self, skill_id: str) -> bool:
        return self._skills.get(skill_id, {}).get("certified", False)


default_episodic_memory = EpisodicMemory()
default_workflow_memory = WorkflowMemory()
default_semantic_memory = SemanticMemory()
default_procedural_memory = ProceduralMemory()
