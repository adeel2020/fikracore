"""
JARVIS Autopilot Engine - Multi-Agent Orchestration
Coordinates complex tasks across multiple agents.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.autopilot")


class AutopilotEngine:
    """JARVIS autopilot superpower - orchestrate the agent fleet."""

    def __init__(self, config):
        self.config = config
        self._agents: dict[str, Any] = {}
        self._task_queue: list[dict] = []

    async def initialize(self) -> None:
        """Initialize autopilot with available agents."""
        try:
            from ..qna.agent import _create_antigravity_agent
            self._agents["cognitive"] = _create_antigravity_agent()
            logger.info("[AutopilotEngine] Cognitive agent loaded.")
        except Exception as e:
            logger.warning(f"[AutopilotEngine] Failed to load cognitive agent: {e}")
        
        try:
            from ..storyteller.datastory.crewai_storyteller import init_storyteller
            self._agents["storyteller"] = init_storyteller()
            logger.info("[AutopilotEngine] Storyteller agent loaded.")
        except Exception as e:
            logger.warning(f"[AutopilotEngine] Failed to load storyteller agent: {e}")
        
        logger.info(f"[AutopilotEngine] Initialized with {len(self._agents)} agents.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process complex multi-step tasks."""
        lower_query = query.lower()
        
        # Orchestrate multi-agent task
        if any(kw in lower_query for kw in ["orchestrate", "multi-agent", "coordinate"]):
            return await self.orchestrate(query, context)
        
        # Plan and execute
        if any(kw in lower_query for kw in ["plan", "execute", "workflow"]):
            return await self.plan_and_execute(query, context)
        
        # Agent delegation
        if any(kw in lower_query for kw in ["delegate", "assign", "route to"]):
            return await self.delegate_task(query, context)
        
        # Default: orchestrate
        return await self.orchestrate(query, context)

    async def orchestrate(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Orchestrate a complex task across multiple agents."""
        # Analyze task complexity
        complexity = self._analyze_complexity(query)
        
        if complexity == "simple":
            # Single agent task
            agent_type = self._select_agent(query)
            return await self._execute_agent(agent_type, query, context)
        
        # Multi-agent task
        subtasks = self._decompose_task(query)
        results = []
        
        for subtask in subtasks:
            agent_type = self._select_agent(subtask)
            result = await self._execute_agent(agent_type, subtask, context)
            results.append(f"### {subtask.title()}\n{result}")
        
        # Synthesize results
        synthesis = await self._synthesize_results(query, results)
        return synthesis

    async def plan_and_execute(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Plan steps and execute them."""
        # Generate plan
        plan = await self._generate_plan(query)
        
        # Execute each step
        execution_results = []
        for i, step in enumerate(plan, 1):
            result = await self._execute_agent("cognitive", step, context)
            execution_results.append(f"**Step {i}:** {step}\nResult: {result[:200]}...")
        
        return f"## Execution Plan\n\n{plan}\n\n## Results\n\n" + "\n\n".join(execution_results)

    async def delegate_task(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Delegate task to appropriate agent."""
        agent_type = self._select_agent(query)
        return await self._execute_agent(agent_type, query, context)

    def _analyze_complexity(self, query: str) -> str:
        """Analyze task complexity."""
        complexity_indicators = [
            "and then", "also", "additionally", "multiple", "several",
            "compare", "analyze", "synthesize", "comprehensive"
        ]
        
        if any(indicator in query.lower() for indicator in complexity_indicators):
            return "complex"
        return "simple"

    def _select_agent(self, query: str) -> str:
        """Select best agent for the task."""
        lower_query = query.lower()
        
        if any(kw in lower_query for kw in ["story", "narrative", "report", "data"]):
            return "storyteller"
        
        return "cognitive"

    def _decompose_task(self, query: str) -> list[str]:
        """Decompose complex task into subtasks."""
        # Simple decomposition based on conjunctions
        import re
        parts = re.split(r'\s+(?:and|also|additionally|then)\s+', query, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]

    async def _execute_agent(self, agent_type: str, query: str, context: dict[str, Any] | None) -> str:
        """Execute task with specified agent."""
        agent = self._agents.get(agent_type)
        
        if agent is None:
            return f"Agent '{agent_type}' not available."
        
        try:
            from crewai import Task, Crew, Process
            
            task = Task(
                description=f"Process: {query}",
                expected_output="Detailed response in Markdown format.",
                agent=agent
            )
            
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )
            
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            return f"Agent execution error: {e}"

    async def _generate_plan(self, query: str) -> list[str]:
        """Generate execution plan."""
        # Simple plan generation
        return [
            f"Analyze requirements for: {query}",
            f"Execute core logic for: {query}",
            f"Validate and report results for: {query}"
        ]

    async def _synthesize_results(self, query: str, results: list[str]) -> str:
        """Synthesize multiple results into coherent response."""
        combined = "\n\n".join(results)
        
        # Use LLM to synthesize
        if self._agents.get("cognitive"):
            try:
                from crewai import Task, Crew, Process
                
                task = Task(
                    description=f"Synthesize these results into a coherent response to: {query}\n\nResults:\n{combined}",
                    expected_output="Synthesized response in Markdown.",
                    agent=self._agents["cognitive"]
                )
                
                crew = Crew(
                    agents=[self._agents["cognitive"]],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False
                )
                
                result = crew.kickoff()
                return str(result)
            except Exception as e:
                logger.warning(f"Synthesis failed: {e}")
        
        return combined

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream autopilot execution."""
        result = await self.process(query, session_id, context)
        yield result

    async def shutdown(self) -> None:
        """Cleanup autopilot resources."""
        self._agents.clear()
        self._task_queue.clear()
