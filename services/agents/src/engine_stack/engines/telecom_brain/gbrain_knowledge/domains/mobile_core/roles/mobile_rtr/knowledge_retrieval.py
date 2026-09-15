"""
MobileRTRKnowledge: Knowledge retrieval adapter over gbrain MCP for Mobile RTR.

Talks to gbrain MCP over JSON-RPC via GbrainClient.
Zero coupling with incident storytelling: query scopes and namespaces are strictly ring-fenced.
Provides seamless fallback to the local declarative YAML files in gbrain_knowledge/
if the external gbrain daemon is restarting or running offline.
"""

from __future__ import annotations

import logging
import os
import yaml
from typing import Any, Dict, List, Optional

from storyteller.knowledge.gbrain_client import GbrainClient

logger = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_ONTOLOGY_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../shared_ontology"))


class MobileRTRKnowledge:
    """Retrieval layer connecting Mobile RTR services to gbrain MCP."""

    def __init__(self, client: Optional[GbrainClient] = None) -> None:
        self.client = client or GbrainClient()

    def get_sla_governance(self) -> Dict[str, float]:
        """
        Retrieve SLA thresholds (AOLA, OLA, E2E SLA) from gbrain MCP.
        Falls back to role.yaml if gbrain page is missing.
        """
        try:
            page = self.client.call(
                "get_page",
                {"slug": "domains/mobile-core/roles/mobile-rtr/customer-ticket-journey"}
            )
            if page and isinstance(page, dict) and "frontmatter" in page:
                fm = page["frontmatter"]
                return {
                    "aola_target_hours": float(fm.get("aola_target_hours", 2.0)),
                    "ola_target_hours": float(fm.get("ola_target_hours", 6.0)),
                    "sla_target_hours": float(fm.get("sla_target_hours", 48.0)),
                }
        except Exception as exc:
            logger.debug("[MobileRTRKnowledge] gbrain SLA page fetch exception: %s. Loading local YAML fallback.", exc)

        # Fallback to local role.yaml
        yaml_path = os.path.join(CURRENT_DIR, "role.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                gov = data.get("sla_governance", {})
                return {
                    "aola_target_hours": float(gov.get("aola_target_hours", 2.0)),
                    "ola_target_hours": float(gov.get("ola_target_hours", 6.0)),
                    "sla_target_hours": float(gov.get("sla_target_hours", 48.0)),
                }

        return {"aola_target_hours": 2.0, "ola_target_hours": 6.0, "sla_target_hours": 48.0}

    def get_queue_topology(self) -> Dict[str, Any]:
        """Retrieve queue routing matrix and bouncing rules from gbrain MCP or YAML."""
        data: Dict[str, Any] = {}
        yaml_path = os.path.join(CURRENT_DIR, "queue_topology.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        try:
            page = self.client.call(
                "get_page",
                {"slug": "domains/mobile-core/roles/mobile-rtr/queue-topology"}
            )
            if page and isinstance(page, dict):
                fm = page.get("frontmatter", {})
                if isinstance(fm, dict):
                    data.update(fm)
                data["compiled_truth"] = page.get("compiled_truth", "")
        except Exception as exc:
            logger.debug("[MobileRTRKnowledge] gbrain queue topology fetch exception: %s", exc)

        return data

    def get_ticket_journey_data(self, ticket_id: str) -> Dict[str, Any]:
        """
        Retrieve declarative ticket journey hops and findings from gbrain MCP.
        Falls back to local tickets/{ticket_slug}_journey.yaml.
        """
        clean_token = ticket_id.upper().strip()
        if not clean_token.startswith("TT-"):
            clean_token = f"TT-{clean_token}"
        slug_id = clean_token.lower().replace("-", "_")

        # Try fetching ticket page from gbrain MCP
        try:
            page = self.client.call(
                "get_page",
                {"slug": f"tickets/mobile-core/{clean_token.lower()}"}
            )
            if page and isinstance(page, dict) and "frontmatter" in page:
                return page["frontmatter"]
        except Exception as exc:
            logger.debug("[MobileRTRKnowledge] gbrain ticket page query exception: %s", exc)

        # Fallback to local declarative YAML
        yaml_candidates = [
            os.path.join(CURRENT_DIR, "tickets", f"{slug_id}_journey.yaml"),
            os.path.join(CURRENT_DIR, "tickets", "tt_984210_journey.yaml"),
        ]
        for y_path in yaml_candidates:
            if os.path.exists(y_path):
                with open(y_path, encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}

        return {}

    def get_huawei_mml_catalog(self) -> Dict[str, Any]:
        """Retrieve Huawei MML runbooks from gbrain MCP or local YAML."""
        data: Dict[str, Any] = {}
        yaml_path = os.path.join(CURRENT_DIR, "huawei_mml_catalog.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        try:
            page = self.client.call(
                "get_page",
                {"slug": "domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks"}
            )
            if page and isinstance(page, dict):
                fm = page.get("frontmatter", {})
                if isinstance(fm, dict):
                    data.update(fm)
                data["compiled_truth"] = page.get("compiled_truth", "")
        except Exception as exc:
            logger.debug("[MobileRTRKnowledge] gbrain MML catalog fetch exception: %s", exc)

        return data

    def get_telecom_services_catalog(self) -> Dict[str, Any]:
        """Retrieve telecom services portfolio from gbrain MCP or local YAML."""
        data: Dict[str, Any] = {}
        yaml_path = os.path.join(CURRENT_DIR, "telecom_services.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        try:
            page = self.client.call(
                "get_page",
                {"slug": "domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog"}
            )
            if page and isinstance(page, dict):
                fm = page.get("frontmatter", {})
                if isinstance(fm, dict):
                    data.update(fm)
                data["compiled_truth"] = page.get("compiled_truth", "")
        except Exception as exc:
            logger.debug("[MobileRTRKnowledge] gbrain services catalog fetch exception: %s", exc)

        return data

    def get_tools_matrix(self) -> Dict[str, Any]:
        """Retrieve tools matrix from gbrain MCP or local YAML."""
        data: Dict[str, Any] = {}
        yaml_path = os.path.join(CURRENT_DIR, "tools_matrix.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        try:
            page = self.client.call(
                "get_page",
                {"slug": "domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog"}
            )
            if page and isinstance(page, dict):
                fm = page.get("frontmatter", {})
                if isinstance(fm, dict):
                    data.update(fm)
                data["compiled_truth"] = page.get("compiled_truth", "")
        except Exception as exc:
            logger.debug("[MobileRTRKnowledge] gbrain tools matrix fetch exception: %s", exc)

        return data
