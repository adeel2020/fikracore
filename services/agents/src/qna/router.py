from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agenticaiops_shared.schemas import ChatRequest, ChatResponse, Telemetry
from agenticaiops_shared.guardrails import check_guardrail_standalone

from .rag_agent import execute_qna, stream_qna

logger = logging.getLogger("qna.router")
router = APIRouter(prefix="/api/qna", tags=["qna"])


class QnAResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/ask")
async def ask(req: ChatRequest) -> QnAResponse:
    rejection = check_guardrail_standalone(req.message, agent_role="QnA Agent", agent_goal="Answer telecom and network operations queries")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)
    try:
        reply = await execute_qna(req.message, req.session_id or "default")
        return QnAResponse(session_id=req.session_id or "default", reply=reply)
    except Exception as e:
        logger.error("QnA execution failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/ask/stream")
async def ask_stream(req: ChatRequest) -> StreamingResponse:
    rejection = check_guardrail_standalone(req.message, agent_role="QnA Agent", agent_goal="Answer telecom and network operations queries")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)

    async def event_stream() -> AsyncIterator[str]:
        yield "event: status\ndata: " + json.dumps({"agent": "qna", "task": "processing"}) + "\n\n"
        try:
            async for chunk in stream_qna(req.message, req.session_id or "default"):
                if hasattr(chunk, "content") and chunk.content:
                    yield "event: token\ndata: " + json.dumps({"content": chunk.content, "agent": "qna"}) + "\n\n"
            yield "event: done\ndata: " + json.dumps({"session_id": req.session_id or "default"}) + "\n\n"
        except Exception as e:
            yield "event: error\ndata: " + json.dumps({"message": str(e)}) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
