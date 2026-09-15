"""
Primary Agent File: Antigravity.
A powerful agentic AI coding assistant designed to coordinate, plan, execute, and verify tasks.
Matches the Primary Agent's persona, planning mode, skill execution, and downstream task flow.
"""
from __future__ import annotations

import os
import subprocess
import asyncio
import time
from collections.abc import AsyncIterator
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

from agenticaiops_shared.config import settings
from qna.skill_manager import SkillManager
from agenticaiops_shared.memory import SessionMemory

# Resolve workspace root dynamically
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ==========================================
# ADVANCED ORCHESTRATION TOOLS FOR ANTIGRAVITY
# ==========================================

@tool("view_file_tool")
def view_file_tool(file_path: str) -> str:
    """Read the contents of a file within the workspace.
    Pass the relative or absolute path of the file you wish to view.
    """
    full_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, file_path))
    if not full_path.startswith(WORKSPACE_ROOT):
        return f"Error: Access denied. Path '{file_path}' is outside the workspace."
    
    if not os.path.exists(full_path):
        return f"Error: File not found at '{file_path}'."
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read(20000)  # Read up to 20k chars
            if len(content) >= 20000:
                content += "\n... [TRUNCATED due to size]"
            return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool("write_to_file_tool")
def write_to_file_tool(file_path: str, content: str) -> str:
    """Create or overwrite a file in the workspace with the specified content.
    Provide the relative or absolute path and the complete text content.
    """
    full_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, file_path))
    if not full_path.startswith(WORKSPACE_ROOT):
        return f"Error: Access denied. Path '{file_path}' is outside the workspace."
    
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: File successfully written to '{file_path}'."
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool("run_shell_command_tool")
def run_shell_command_tool(command: str) -> str:
    """Execute a terminal/shell command within the workspace.
    This can be used to run scripts, compile code, run tests, or execute system checks.
    """
    try:
        # Run safely in workspace directory
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=WORKSPACE_ROOT,
            timeout=30 # Safety timeout
        )
        output = f"Exit Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}"
        if result.stderr:
            output += f"\n\nSTDERR:\n{result.stderr}"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

@tool("execute_skill_tool")
def execute_skill_tool(skill_name: str, arguments: str) -> str:
    """Dynamically invoke a workspace skill (like /trace-analyzer) with optional arguments.
    Provide the name of the skill (e.g. 'trace-analyzer') and a space-separated arguments string.
    """
    manager = SkillManager()
    parsed_args = arguments.split() if arguments else []
    
    # Run the skill asynchronously in executor to prevent blocking
    async def run():
        res, role = await manager.execute_skill(skill_name, parsed_args)
        return f"[{role} Output]:\n{res}"
        
    try:
        return asyncio.run(run())
    except Exception as e:
        return f"Error executing skill '{skill_name}': {str(e)}"

# ==========================================
# ANTIGRAVITY AGENT CREATION
# ==========================================

def _create_antigravity_agent(streaming: bool = False) -> Agent:
    llm = LLM(model=settings.openai_model, base_url=settings.openai_api_base, api_key=settings.openai_api_key or "ollama", stream=streaming)
    return Agent(
        role="Core Mobile Network Data Analyst",
        goal=(
            "Coordinate, plan, execute system diagnostics, run tests, analyze core mobile network signaling (SIP, M2UA, M3UA), "
            "manage workspace files, and orchestrate capabilities/skills. Follow the primary agent's rigorous planning loop."
        ),
        backstory=(
            """You are Cognitive Operation & Customer Center, a powerful agentic Core Mobile Network Data Analyst. 
            You excel at system orchestration, planning, diagnostics, analyzing mobile network architectures, parsing telecommunication signaling traces, and extending platform capabilities.
            
            IMPORTANT: While you run system diagnostics, explain architecture, read/manage files, and write test/operational scripts, you DO NOT write or generate raw application-level source code or software development files from scratch.
            
            When confronted with any task:
            1. First research the directories, file constraints, and mobile core network parameters.
            2. If the task is complex, formulate a structured 'implementation_plan.md' and request review.
            3. Track step-by-step progress using a 'task.md' checklist.
            4. Execute diagnostic runs, file adjustments, shell commands, or custom skills (using your execute_skill_tool).
            5. Verify all actions through validation steps, documenting findings in 'walkthrough.md'.
            Ground every action in safety and high quality. Never use placeholders."""
        ),
        verbose=True,
        tools=[view_file_tool, write_to_file_tool, run_shell_command_tool, execute_skill_tool],
        llm=llm
    )

# ==========================================
# EXECUTION & STREAMING HANDLERS
# ==========================================

async def execute_primary_agent(query: str, session_id: str) -> str:
    """Run the Cognitive Operation & Customer Center Agent and return the final response."""
    agent = _create_antigravity_agent(streaming=False)
    
    task = Task(
        description=(
            f"Process the user's request. Maintain the standard Cognitive workflow.\n"
            f"USER REQUEST: {query}\n"
            f"Session ID: {session_id}"
        ),
        expected_output="A polished, precise, and verified technical response in Markdown format.",
        agent=agent
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    result = await crew.kickoff_async()
    return str(result)

async def stream_primary_agent(query: str, session_id: str) -> AsyncIterator[StreamChunk]:
    """Stream the Cognitive Operation & Customer Center Agent execution chunk-by-chunk."""
    agent = _create_antigravity_agent(streaming=True)
    
    task = Task(
        description=(
            f"Process the user's request using the standard Cognitive workflow.\n"
            f"USER REQUEST: {query}\n"
            f"Session ID: {session_id}"
        ),
        expected_output="A polished, precise technical response in Markdown format.",
        agent=agent
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    task_info: TaskInfo = {
        "index": 0,
        "name": "cognitive_operator_execution",
        "id": "cognitive_operator",
        "agent_role": "Cognitive Operation & Customer Center",
        "agent_id": "cognitive_operator_agent",
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
