"""
JARVIS RAG Engine - Retrieval Augmented Generation
Intelligent document retrieval and context-aware responses using OpenAI.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.rag")


class RAGEngine:
    """MARK RAG superpower - retrieve, augment, generate with OpenAI."""

    def __init__(self, config):
        self.config = config
        self._retriever = None
        self._llm = None

    async def initialize(self) -> None:
        """Initialize RAG pipeline."""
        try:
            from rag.services.retriever import ConcurrentRetriever
            self._retriever = ConcurrentRetriever()
            logger.info("[RAGEngine] Retriever loaded.")
        except Exception:
            logger.info("[RAGEngine] Specialized RAG retriever not available; using OpenAI directly.")
        
        try:
            from openai import OpenAI
            self._llm = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base if self.config.api_base != "https://api.openai.com/v1" else None,
            )
        except Exception as e:
            logger.warning(f"[RAGEngine] LLM init failed: {e}")
        
        logger.info("[RAGEngine] Initialized with OpenAI.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process RAG queries with MARK Incident Manager persona."""
        try:
            context_docs = await self.retrieve(query)
            response = await self.generate(query, context_docs)
            return response
        except Exception as e:
            return f"MARK operations error: {e}"

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Retrieve relevant documents."""
        if self._retriever:
            try:
                nodes = await self._retriever.retrieve(query)
                return [
                    {"content": node.node.get_content(), "score": node.score}
                    for node in nodes[:top_k]
                ]
            except Exception as e:
                logger.info(f"Retrieval info: {e}")
        return []

    async def generate(self, query: str, context_docs: list[dict]) -> str:
        """Generate response with retrieved context using OpenAI."""
        if not self._llm:
            return "MARK OpenAI client is not initialized."

        system_prompt = (
            "You are MARK, the Telecom Incident Manager for AgenticAIOPs. "
            "You provide sharp, commanding, precise incident operations guidance, "
            "focusing on MTTR reduction, RCA, blast radius, correlation, and automated healing."
        )

        if context_docs:
            context_text = "\n\n".join([
                f"[Evidence {i+1}] {doc['content'][:500]}"
                for i, doc in enumerate(context_docs)
            ])
            system_prompt += f"\n\nOperational Context:\n{context_text}"

        try:
            response = self._llm.chat.completions.create(
                model=self.config.model or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content or "No response generated."
        except Exception as e:
            return f"MARK LLM Generation error: {e}"

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream RAG responses."""
        result = await self.process(query, session_id, context)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', result)
        for sentence in sentences:
            yield sentence + " "

    async def shutdown(self) -> None:
        """Cleanup RAG resources."""
        self._retriever = None
        self._llm = None
