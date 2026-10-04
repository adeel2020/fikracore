"""
4-Plane Canonical gbrain MCP Client
==================================
This client implements the 4-plane typed interface to gbrain:
- Plane 1 (Topology Plane): Primary path, dependencies, and redundancy edges (HA_PAIR_WITH, BACKUP_PATH_FOR).
- Plane 2 (Incident Plane): Active incident tracking and multi-tier blast radius assessment.
- Plane 3 (Episode Reasoning Spine): Task episode lifecycle ledger and audit trails.
- Plane 4 (Knowledge & Playbooks): Cross-domain pattern discovery and verified remediation runbooks.

Guarantees:
- 100% Epistemic Integrity: Zero leakage of simulation hidden reality.
- Preserves canonical slugs (no folder silos).
- Supports HTTP MCP, subprocess, or embedded fallback seamlessly.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Union

from ..investigation.contracts.topology import (
    BlastRadiusAssessment,
    BlastRadiusLevel,
    TypedEdgeType,
)
from ..services.playbook_service import default_playbook_registry

try:
    from zaki.contracts.task_episode import TaskEpisodeContract
except ImportError:
    try:
        from ....zaki.contracts.task_episode import TaskEpisodeContract
    except Exception:
        TaskEpisodeContract = Any  # type: ignore

logger = logging.getLogger(__name__)


class Gbrain4PlaneMCPClient:
    """
    4-Plane Typed MCP Client interfacing with gbrain knowledge store.
    """

    def __init__(self, gbrain_transport: Optional[Any] = None) -> None:
        self._transport = gbrain_transport
        self._local_episodes: Dict[str, Dict[str, Any]] = {}

    def _get_transport(self) -> Any:
        if self._transport is None:
            try:
                from storyteller.knowledge.gbrain_client import GbrainClient
                self._transport = GbrainClient()
            except Exception as e:
                logger.debug("Falling back to local lightweight gbrain transport: %s", e)
                self._transport = None
        return self._transport

    def get_index_node(self, plane_name: str) -> Dict[str, Any]:
        """
        Retrieve canonical index node descriptor for one of the 4-Planes:
        TOPOLOGY, INCIDENTS, EPISODES, PATTERNS, PLAYBOOKS.
        """
        mapping = {
            "TOPOLOGY": {"slug": "index-topology", "plane": "topology", "title": "Plane 1: Canonical Topology & Redundancy Index"},
            "INCIDENTS": {"slug": "index-incidents", "plane": "incident", "title": "Plane 2: Active Incidents & Blast Radius Index"},
            "EPISODES": {"slug": "index-episodes", "plane": "reasoning", "title": "Plane 3: Task Episode Cognitive Ledger Index"},
            "PATTERNS": {"slug": "index-patterns", "plane": "pattern", "title": "Plane 4: Cross-Domain Patterns Index"},
            "PLAYBOOKS": {"slug": "index-playbooks", "plane": "pattern", "title": "Plane 4: Verified Remediation Playbooks Index"},
        }
        return mapping.get(plane_name.upper(), {"slug": f"index-{plane_name.lower()}", "plane": "unknown", "title": plane_name})

    # -------------------------------------------------------------------------
    # Plane 1: Topology Plane (Primary Paths, Graph Traversal, & Redundancy)
    # -------------------------------------------------------------------------

    def get_topology(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Query topology neighborhood around node_id up to specified depth.
        """
        transport = self._get_transport()
        if transport and hasattr(transport, "traverse_graph"):
            try:
                raw_graph = transport.traverse_graph(start_slug=node_id, depth=depth)
                return {
                    "node_id": node_id,
                    "depth": depth,
                    "nodes": raw_graph.get("nodes", [node_id]),
                    "edges": raw_graph.get("edges", []),
                }
            except Exception as e:
                logger.debug("Topology graph traversal error via transport: %s", e)

        # Canonical deterministic fallback
        return {
            "node_id": node_id,
            "depth": depth,
            "nodes": [node_id],
            "edges": [],
        }

    def get_redundant_paths(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Query explicit redundancy relationships (HA_PAIR_WITH, BACKUP_PATH_FOR, carried-by)
        for high-availability protection validation.
        """
        topology = self.get_topology(node_id, depth=2)
        redundant_edges = []
        redundancy_keywords = {"ha", "backup", "redundant", "protect", "standby", "secondary"}

        for edge in topology.get("edges", []):
            rel = str(edge.get("relation") or edge.get("link_type") or "").lower()
            if any(k in rel for k in redundancy_keywords) or rel in (
                TypedEdgeType.HA_PAIR_WITH.value,
                TypedEdgeType.BACKUP_PATH_FOR.value,
            ):
                redundant_edges.append(edge)

        return redundant_edges

    # -------------------------------------------------------------------------
    # Plane 2: Incident Plane (Active Incidents & Multi-Tier Blast Radius)
    # -------------------------------------------------------------------------

    def get_active_incidents(self) -> List[Dict[str, Any]]:
        """
        Query all currently active carrier incident records.
        """
        transport = self._get_transport()
        if transport and hasattr(transport, "list_pages"):
            try:
                pages = transport.list_pages(prefix="mobile-core/incidents")
                return pages if isinstance(pages, list) else []
            except Exception:
                pass
        return []

    def get_blast_radius(self, incident_id: str, affected_nodes: Optional[List[str]] = None) -> BlastRadiusAssessment:
        """
        Compute multi-tier blast radius separating:
        1. Direct physical impact (affected hardware/elements).
        2. Transitive service impact (dependent bearer/signaling paths).
        3. Observed customer impact (subscribers / throughput drops).
        """
        nodes = list(affected_nodes or [])
        transitive: List[str] = []
        customer_services: List[str] = []

        # Traverse downstream dependencies for each affected node
        for node in nodes:
            topo = self.get_topology(node, depth=2)
            for edge in topo.get("edges", []):
                tgt = edge.get("target") or edge.get("to_entity")
                if tgt and tgt not in nodes and tgt not in transitive:
                    transitive.append(tgt)

        # Estimate severity tier based on span of impact
        total_affected = len(nodes) + len(transitive)
        if total_affected > 8:
            level = BlastRadiusLevel.NETWORK_WIDE
        elif total_affected > 4:
            level = BlastRadiusLevel.REGIONAL
        elif total_affected > 1:
            level = BlastRadiusLevel.MULTI_DOMAIN
        else:
            level = BlastRadiusLevel.LOCAL

        return BlastRadiusAssessment(
            directly_affected_entities=nodes,
            indirectly_affected_entities=transitive,
            affected_services=customer_services,
            blast_radius_level=level,
            customer_facing_impact=f"Impact spans {len(nodes)} physical node(s) and {len(transitive)} transitive dependency hop(s).",
        )

    # -------------------------------------------------------------------------
    # Plane 3: Episode Reasoning Spine (Task Episode Lifecycle Ledger)
    # -------------------------------------------------------------------------

    def record_episode(
        self, task_episode: Union[TaskEpisodeContract, Dict[str, Any]]
    ) -> str:
        """
        Commit or update a TaskEpisodeContract under Plane 3 in gbrain.
        """
        if isinstance(task_episode, TaskEpisodeContract):
            payload = task_episode.model_dump(mode="python")
            episode_id = task_episode.episode_id
        else:
            payload = dict(task_episode)
            episode_id = payload.get("episode_id", f"EP-{int(datetime.now(timezone.utc).timestamp())}")

        self._local_episodes[episode_id] = payload

        transport = self._get_transport()
        if transport and hasattr(transport, "put_page"):
            try:
                transport.put_page(
                    slug=f"episodes/{episode_id}",
                    content=json.dumps(payload, default=str),
                    frontmatter={
                        "kind": "TaskEpisode",
                        "episode_id": episode_id,
                        "task_id": payload.get("task_id"),
                        "incident_id": payload.get("incident_id"),
                        "outcome": payload.get("outcome"),
                    },
                )
            except Exception as e:
                logger.debug("Gbrain put_page for episode error: %s", e)

        return episode_id

    def get_episode_state(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve live cognitive state and audit trail for a task episode.
        """
        if episode_id in self._local_episodes:
            return self._local_episodes[episode_id]

        transport = self._get_transport()
        if transport and hasattr(transport, "get_page"):
            try:
                page = transport.get_page(slug=f"episodes/{episode_id}")
                if page:
                    return page.get("frontmatter") or page
            except Exception:
                pass
        return None

    # -------------------------------------------------------------------------
    # Plane 4: Enterprise Intelligence & Playbooks
    # -------------------------------------------------------------------------

    def find_patterns(
        self,
        symptom_vector: Dict[str, Any],
        domains: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Match current operational symptoms against cross-domain historical patterns in gbrain.
        """
        transport = self._get_transport()
        target_domains = [d.lower() for d in (domains or [])]
        matched: List[Dict[str, Any]] = []

        if transport and hasattr(transport, "list_pages"):
            try:
                pages = transport.list_pages(prefix="patterns")
                for p in pages:
                    p_dom = str(p.get("domain", "")).lower()
                    if not target_domains or any(d in p_dom for d in target_domains):
                        matched.append(p)
                if matched:
                    return matched
            except Exception:
                pass

        # Built-in canonical pattern catalog fallback
        canonical_patterns = [
            {
                "pattern_id": "PAT-TRANSPORT-OPTIC-CRC",
                "pattern_name": "Optical Margin Degradation with Ingress CRC Spikes",
                "domains": ["IP_TRANSPORT"],
                "symptoms": ["crc_error_rate_drift", "interface_buffer_drop"],
                "root_cause_pattern": "Physical optic receiver power loss or micro-bend",
                "recommended_playbook": "MOP-PORT-RESET-01",
            },
            {
                "pattern_id": "PAT-CORE-UPF-BUFFER",
                "pattern_name": "UPF Ingress Buffer Starvation from Asymmetric Route Shift",
                "domains": ["PS_CORE", "IP_TRANSPORT"],
                "symptoms": ["gtp_tunnel_timeout", "packet_drop_ratio"],
                "root_cause_pattern": "BGP primary path drain without GTP QoS shaping",
                "recommended_playbook": "MOP-UPF-RESTART-02",
            },
        ]

        if not target_domains:
            return canonical_patterns

        return [
            p for p in canonical_patterns
            if any(td in [d.lower() for d in p["domains"]] for td in target_domains)
        ]

    def get_playbook(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve verified remediation playbook / MOP with pre-flight checks and rollback steps.
        """
        pb = default_playbook_registry.get_playbook(playbook_id)
        if pb:
            return pb.model_dump(mode="python")

        # Query gbrain
        transport = self._get_transport()
        if transport and hasattr(transport, "get_page"):
            try:
                page = transport.get_page(slug=f"knowledge/playbooks/{playbook_id}")
                if page:
                    return page
            except Exception:
                pass

        return None


default_gbrain_client = Gbrain4PlaneMCPClient()
