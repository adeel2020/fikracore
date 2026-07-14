"""
JARVIS RAG Engine - Retrieval Augmented Generation
Intelligent document retrieval and context-aware responses.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.rag")


class RAGEngine:
    """JARVIS RAG superpower - retrieve, augment, generate."""

    def __init__(self, config):
        self.config = config
        self._retriever = None
        self._llm = None

    async def initialize(self) -> None:
        """Initialize RAG pipeline."""
        try:
            # Try to load existing RAG infrastructure
            from ..rag.services.retriever import ConcurrentRetriever
            self._retriever = ConcurrentRetriever()
            logger.info("[RAGEngine] Retriever loaded.")
        except ImportError:
            logger.warning("[RAGEngine] RAG retriever not available.")
        
        try:
            from openai import OpenAI
            self._llm = OpenAI(
                api_key=self.config.api_key or "ollama",
                base_url=self.config.api_base,
            )
        except Exception as e:
            logger.warning(f"[RAGEngine] LLM init failed: {e}")
        
        logger.info("[RAGEngine] Initialized.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process RAG queries."""
        try:
            # Retrieve relevant context
            context_docs = await self.retrieve(query)
            
            # Generate response with context
            response = await self.generate(query, context_docs)
            
            return response
        except Exception as e:
            return f"RAG processing error: {e}"

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
                logger.warning(f"Retrieval failed: {e}")
        
        return []

    async def generate(self, query: str, context_docs: list[dict]) -> str:
        """Generate response with retrieved context."""
        if not context_docs:
            # No context available, use LLM directly
            if self._llm:
                response = self._llm.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "You are JARVIS, a helpful AI assistant."},
                        {"role": "user", "content": query}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )
                return response.choices[0].message.content
            return "I don't have enough context to answer that question."
        
        # Build context from retrieved docs
        context_text = "\n\n".join([
            f"[Doc {i+1}] {doc['content'][:500]}"
            for i, doc in enumerate(context_docs)
        ])
        
        system_prompt = """You are JARVIS, an intelligent AI assistant.
Answer the user's question based on the provided context.
If the context doesn't contain the answer, say so and provide what you know.

Context:
{context}
"""
        
        try:
            response = self._llm.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context_text)},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Generation error: {e}"

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream RAG responses."""
        result = await self.process(query, session_id, context)
        # Yield sentence by sentence
        import re
        sentences = re.split(r'(?<=[.!?])\s+', result)
        for sentence in sentences:
            yield sentence + " "

    async def shutdown(self) -> None:
        """Cleanup RAG resources."""
        self._retriever = None
        self._llm = None
