from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agenticaiops_shared.guardrails import check_guardrail_standalone

from .services.qna import long_term_memory_query_engine

logger = logging.getLogger("rag.router")
router = APIRouter(prefix="/api/rag", tags=["rag"])


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None


class RAGSearchResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[str] = []


class RAGIngestRequest(BaseModel):
    file_path: str = Field("", description="Path to file or directory to ingest")
    collection_name: str = Field("default", description="Target collection for ingestion")


@router.post("/search")
async def search(req: RAGSearchRequest) -> RAGSearchResponse:
    rejection = check_guardrail_standalone(req.query, agent_role="RAG Engine", agent_goal="Retrieve and synthesize information from documents")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)
    try:
        result = await long_term_memory_query_engine.aquery(req.query, [])
        sources = []
        for node in result.get("source_nodes", []):
            text = getattr(node, "text", str(node))[:100] if node else ""
            sources.append(text)
        return RAGSearchResponse(
            session_id=req.session_id or "default",
            answer=result.get("answer", ""),
            sources=sources,
        )
    except Exception as e:
        logger.error("RAG search failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/ingest/list")
async def list_ingested():
    try:
        from .pipelines.ingestion import get_docstore
        docstore = get_docstore()
        docs = []
        for doc_id, node in docstore.docs.items():
            docs.append({
                "id": doc_id,
                "text": node.text[:200] if hasattr(node, "text") else str(node)[:200],
            })
        return {"total_docs": len(docs), "documents": docs[:100]}
    except Exception as e:
        logger.warning("Docstore not available: %s", e)
        return {"total_docs": 0, "documents": [], "note": "Docstore not initialized. Ingest documents first."}
