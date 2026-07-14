"""
Unified CrewAI Manager — rag_agent.py

Crew 1 — QnACrew:
    Single-agent crew optimised for fast, conversational responses.
    Equipped with a RAG query system tool to query databases and vector stores.
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crewai.utilities.streaming import (
    StreamChunk,
    TaskInfo,
    create_async_chunk_generator,
    create_streaming_state,
    signal_end,
    signal_error,
)
from crewai.types.streaming import CrewStreamingOutput
from sqlalchemy.orm import Session as SASession

from backend.database.db import SessionLocal
from backend.database.models import ChatSession, ChatMessage
from backend.config import settings
from backend.rag.services.qna import RAGQueryEngine

logger = logging.getLogger("agent.rag_agent")

# ====================================================================
# CREWAI TOOLS — used by the RAG/QnA agent
_rag_engine_instance = None

def get_rag_engine():
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGQueryEngine()
    return _rag_engine_instance

@tool("query_rag_system")
def query_rag_system(query: str) -> str:
    """Query the RAG knowledge base system to retrieve structured data tables,
    rejection reasons, countries, metrics, or document context details.
    Pass the user's raw question directly as the query input.
    Also returns available chart options (chart pills) when the user asks about charts.
    """
    engine = get_rag_engine()
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            with ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(engine.aquery(query)))
                result = future.result()
        else:
            result = asyncio.run(engine.aquery(query))

        chart_options = result.get("chart_options")
        chart_hint = result.get("chart_hint")
        pre_selected = result.get("pre_selected_dom_id")

        lines = []
        rag_retrievals = result.get("rag_retrievals", "")
        answer = result.get("answer", "No response from RAG system.")

        if rag_retrievals:
            lines.append(rag_retrievals)
            lines.append("")
            lines.append("final answer:")
            lines.append(answer)
        else:
            lines.append(f"ANSWER: {answer}")

        if chart_options:
            lines.append("\nAVAILABLE CHARTS:")
            for c in chart_options:
                marker = " [PRE-SELECTED]" if c["dom_id"] == pre_selected else ""
                lines.append(f"  - {c['name']} (id: {c['dom_id']}){marker}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error querying RAG system in tool: {e}", exc_info=True)
        return f"Error querying RAG system: {str(e)}"


# ====================================================================
# CREW 1 — RAG/QnA Crew (lightweight, single-agent)
# ====================================================================
def _create_rag_agent(streaming: bool = False) -> Agent:
    """Conversational Data Analyst — fast, concise, uses RAG tool."""
    llm = LLM(
        model=settings.openai_model,
        base_url=settings.openai_api_base,
        api_key=settings.openai_api_key or "ollama",
        stream=streaming
    )
    return Agent(
        role="QnA Assistant",
        goal=(
            "Answer the user's question using ONLY the output from your query_rag_system tool. "
            "ALWAYS call the tool first. Return the tool output verbatim — do not add, rephrase, or evaluate it."
        ),
        backstory=(
            """You are a pass-through assistant. You call the query_rag_system tool with the user's question
            and return exactly what the tool says. You never fabricate, rephrase, or add extra commentary.
            If the tool says it cannot answer, you repeat that verbatim."""
        ),
        verbose=False,
        tools=[query_rag_system],
        llm=llm,
        max_retry_limit=1,
        allow_code_execution=False,
    )


async def execute_qna(query: str, session_id: str) -> str:
    """Run the RAG Crew and return the final answer string.
    For chart/graph queries, bypasses the agent and returns the full RAG result as JSON.
    """
    engine = get_rag_engine()
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            with ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(engine.aquery(query)))
                rag_result = future.result()
        else:
            rag_result = await engine.aquery(query)
    except Exception as e:
        return json.dumps({"answer": f"Error: {e}"})

    if rag_result.get("chart_options"):
        return json.dumps(rag_result)

    agent = _create_rag_agent(streaming=False)

    task = Task(
        description=(
            f"Call the query_rag_system tool with the user's question and return its output exactly."
            f"USER QUESTION:\n{query}"
        ),
        expected_output=(
            "The exact output from the query_rag_system tool. "
            "Do not add, rephrase, or format the tool's response."
        ),
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        reasoning=False
    )

    result = await crew.kickoff_async()
    return str(result)


async def stream_qna(
    query: str, session_id: str
) -> AsyncIterator[StreamChunk]:
    """Stream the RAG Crew execution as an async iterator of StreamChunks."""
    agent = _create_rag_agent(streaming=True)

    task = Task(
        description=(
            f"Call the query_rag_system tool with the user's question and return its output exactly."
            f"USER QUESTION:\n{query}"
        ),
        expected_output=(
            "The exact output from the query_rag_system tool. "
            "Do not add, rephrase, or format the tool's response."
        ),
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        reasoning=False,
    )

    task_info: TaskInfo = {
        "index": 0,
        "name": "qna_answer",
        "id": "qna",
        "agent_role": "QnA Assistant",
        "agent_id": "rag_agent",
    }
    result_holder: list[str] = []
    output_holder: list[CrewStreamingOutput] = []

    state = create_streaming_state(
        current_task_info=task_info,
        result_holder=result_holder,
        use_async=True,
    )

    async def run_and_signal():
        try:
            res = await crew.kickoff_async()
            result_holder.append(res)
            return res
        except Exception as e:
            signal_error(state, e, is_async=True)
            raise
        finally:
            signal_end(state, is_async=True)

    async for chunk in create_async_chunk_generator(
        state=state,
        run_coro=run_and_signal,
        output_holder=output_holder,
    ):
        yield chunk


# ====================================================================
# CREW 2 — Storyteller Crew (heavy multi-agent, MOCKED for now)
# ====================================================================
async def execute_storyteller(query: str, task_id: str) -> None:
    """Placeholder for the heavy Storyteller Crew."""
    print(f"[StorytellerCrew] Task {task_id} started — query: {query!r}")
    await asyncio.sleep(5)
    print(
        f"[StorytellerCrew] Task {task_id} completed — "
        f" would have produced a multi-agent report."
    )
