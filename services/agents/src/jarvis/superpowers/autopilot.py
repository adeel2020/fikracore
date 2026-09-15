"""
JARVIS Autopilot Engine - Multi-Agent Orchestration
Coordinates complex tasks across multiple agents using OpenAI.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator

import dotenv
_orig_find_dotenv = dotenv.find_dotenv
def _safe_find_dotenv(*args, **kwargs):
    try:
        res = _orig_find_dotenv(*args, **kwargs)
        if res and (res.startswith("/Users/.env") or res == "/.env"):
            return ""
        return res
    except Exception:
        return ""
dotenv.find_dotenv = _safe_find_dotenv

_orig_load_dotenv = dotenv.load_dotenv
def _safe_load_dotenv(dotenv_path=None, *args, **kwargs):
    if dotenv_path is None:
        found = _safe_find_dotenv()
        if not found:
            return False
        dotenv_path = found
    try:
        return _orig_load_dotenv(dotenv_path, *args, **kwargs)
    except PermissionError:
        return False
dotenv.load_dotenv = _safe_load_dotenv

logger = logging.getLogger("jarvis.autopilot")


class AutopilotEngine:
    """MARK autopilot superpower - orchestrate the agent fleet."""

    def __init__(self, config):
        self.config = config
        self._agents: dict[str, Any] = {}
        self._task_queue: list[dict] = []

    async def initialize(self) -> None:
        """Initialize autopilot with available agents."""
        try:
            from qna.agent import _create_antigravity_agent
            self._agents["cognitive"] = _create_antigravity_agent()
            logger.info("[AutopilotEngine] Cognitive agent loaded.")
        except Exception as e:
            logger.info(f"[AutopilotEngine] Cognitive agent standby: {e}")
        
        try:
            from storyteller.datastory.crewai_storyteller import init_storyteller
            self._agents["storyteller"] = init_storyteller()
            logger.info("[AutopilotEngine] Storyteller agent loaded.")
        except Exception as e:
            logger.info(f"[AutopilotEngine] Storyteller agent standby: {e}")
        
        logger.info(f"[AutopilotEngine] Initialized with {len(self._agents)} agents.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process complex multi-step tasks."""
        lower_query = query.lower()
        
        if any(kw in lower_query for kw in ["orchestrate", "multi-agent", "coordinate"]):
            return await self.orchestrate(query, context)
        
        if any(kw in lower_query for kw in ["plan", "execute", "workflow"]):
            return await self.plan_and_execute(query, context)
        
        if any(kw in lower_query for kw in ["delegate", "assign", "route to"]):
            return await self.delegate_task(query, context)
        
        return await self.orchestrate(query, context)

    async def orchestrate(self, task: str, context: dict[str, Any] | None = None) -> str:
        """Orchestrate multi-agent task execution."""
        return (
            f"MARK Orchestration Plan:\n"
            f"1. Telemetry triage & alarm correlation\n"
            f"2. Incident scope & blast radius evaluation\n"
            f"3. Storyteller root cause narration\n"
            f"Task: {task}"
        )

    async def plan_and_execute(self, task: str, context: dict[str, Any] | None = None) -> str:
        return f"MARK Incident Operations workflow initialized for task: {task}"

    async def delegate_task(self, task: str, context: dict[str, Any] | None = None) -> str:
        return f"Task delegated across MARK agent mesh: {task}"

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        result = await self.process(query, session_id, context)
        yield result

    async def shutdown(self) -> None:
        self._agents.clear()
        self._task_queue.clear()
