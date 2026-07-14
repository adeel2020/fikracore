"""
JARVIS Code Engine - Code Generation & Debugging
Writes, reviews, debugs, and refactors code across the workspace.
"""

from __future__ import annotations

import os
import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.code")

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class CodeEngine:
    """JARVIS code superpower - write, debug, refactor code."""

    def __init__(self, config):
        self.config = config
        self._llm = None

    async def initialize(self) -> None:
        """Initialize code generation models."""
        try:
            from openai import OpenAI
            self._llm = OpenAI(
                api_key=self.config.api_key or "ollama",
                base_url=self.config.api_base,
            )
            logger.info("[CodeEngine] LLM initialized.")
        except Exception as e:
            logger.warning(f"[CodeEngine] LLM init failed: {e}")
        
        logger.info("[CodeEngine] Initialized.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process code-related queries."""
        lower_query = query.lower()
        
        # Code generation
        if any(kw in lower_query for kw in ["write", "create", "generate", "implement"]):
            return await self.generate_code(query, context)
        
        # Code debugging
        if any(kw in lower_query for kw in ["debug", "fix", "error", "bug"]):
            return await self.debug_code(query, context)
        
        # Code review
        if any(kw in lower_query for kw in ["review", "check", "improve"]):
            return await self.review_code(query, context)
        
        # Refactoring
        if any(kw in lower_query for kw in ["refactor", "optimize", "clean"]):
            return await self.refactor_code(query, context)
        
        # File operations
        if "read file" in lower_query or "show file" in lower_query:
            file_path = context.get("file_path") if context else None
            if file_path:
                return await self.read_file(file_path)
        
        if "write file" in lower_query or "save file" in lower_query:
            file_path = context.get("file_path") if context else None
            content = context.get("content") if context else None
            if file_path and content:
                return await self.write_file(file_path, content)
        
        return await self.generate_code(query, context)

    async def generate_code(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Generate code based on natural language request."""
        system_prompt = """You are JARVIS, an expert code generation assistant.
Generate clean, production-ready code with:
- Type hints and docstrings
- Error handling
- Follow project conventions
- Include imports
- Add brief inline comments for complex logic

Output format: Return ONLY the code in a markdown code block with the appropriate language tag."""
        
        try:
            response = self._llm.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Code generation error: {e}"

    async def debug_code(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Debug code issues."""
        code = context.get("code") if context else ""
        error = context.get("error") if context else ""
        
        system_prompt = """You are JARVIS, an expert debugger.
Analyze the code and error, identify the root cause, and provide a fix.
Output: The fixed code with explanation of what was wrong."""
        
        user_msg = f"Query: {query}\nCode: {code}\nError: {error}"
        
        try:
            response = self._llm.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.2,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Debug analysis error: {e}"

    async def review_code(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Review code for issues and improvements."""
        code = context.get("code") if context else ""
        
        system_prompt = """You are JARVIS, an expert code reviewer.
Review the code for:
- Bugs and potential issues
- Security vulnerabilities
- Performance optimizations
- Code style and best practices
- Architecture improvements

Provide actionable feedback with specific line references."""
        
        try:
            response = self._llm.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Review this code:\n{code}"}
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Code review error: {e}"

    async def refactor_code(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Refactor and optimize code."""
        code = context.get("code") if context else ""
        
        system_prompt = """You are JARVIS, an expert code refactoring assistant.
Refactor the code for:
- Better readability
- Performance optimization
- SOLID principles
- DRY (Don't Repeat Yourself)
- Clean architecture

Output the refactored code with explanation of changes."""
        
        try:
            response = self._llm.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Refactor: {query}\nCode:\n{code}"}
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Refactoring error: {e}"

    async def read_file(self, file_path: str) -> str:
        """Read file contents."""
        full_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, file_path))
        if not full_path.startswith(WORKSPACE_ROOT):
            return "Access denied: Path outside workspace."
        
        if not os.path.exists(full_path):
            return f"File not found: {file_path}"
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read(50000)
            return f"**{file_path}**:\n```\n{content}\n```"
        except Exception as e:
            return f"Error reading file: {e}"

    async def write_file(self, file_path: str, content: str) -> str:
        """Write content to file."""
        full_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, file_path))
        if not full_path.startswith(WORKSPACE_ROOT):
            return "Access denied: Path outside workspace."
        
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File written successfully: {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream code generation."""
        result = await self.process(query, session_id, context)
        # Yield in code chunks for streaming effect
        lines = result.split("\n")
        current_chunk = []
        for line in lines:
            current_chunk.append(line)
            if len(current_chunk) >= 5:
                yield "\n".join(current_chunk)
                current_chunk = []
        if current_chunk:
            yield "\n".join(current_chunk)

    async def shutdown(self) -> None:
        """Cleanup code engine resources."""
        self._llm = None
