from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agenticaiops_shared.guardrails import check_guardrail_standalone

from .complaint.analyst import complaint_analyst

logger = logging.getLogger("complaint.router")
router = APIRouter(prefix="/api/complaint", tags=["complaint"])


class ComplaintRequest(BaseModel):
    complaint_text: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None
    user_role: str = "Customer_Ops"


class ComplaintResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/analyze")
async def analyze(req: ComplaintRequest) -> ComplaintResponse:
    rejection = check_guardrail_standalone(req.complaint_text, agent_role="Complaint Analyst", agent_goal="Analyze telecom complaints")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)
    try:
        reply = complaint_analyst.analyze(
            raw_complaint=req.complaint_text,
            user_role=req.user_role,
            session_id=req.session_id,
        )
        return ComplaintResponse(session_id=req.session_id or "default", reply=reply)
    except Exception as e:
        logger.error("Complaint analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/analyze/stream")
async def analyze_stream(req: ComplaintRequest) -> StreamingResponse:
    rejection = check_guardrail_standalone(req.complaint_text, agent_role="Complaint Analyst", agent_goal="Analyze telecom complaints")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)

    async def event_stream() -> AsyncIterator[str]:
        yield "event: status\ndata: " + json.dumps({"agent": "complaint", "task": "analyzing"}) + "\n\n"
        try:
            async for chunk in complaint_analyst.stream_analyze(
                raw_complaint=req.complaint_text,
                user_role=req.user_role,
                session_id=req.session_id,
            ):
                if hasattr(chunk, "content") and chunk.content:
                    yield "event: token\ndata: " + json.dumps({"content": chunk.content, "agent": "complaint"}) + "\n\n"
            yield "event: done\ndata: " + json.dumps({"session_id": req.session_id or "default"}) + "\n\n"
        except Exception as e:
            yield "event: error\ndata: " + json.dumps({"message": str(e)}) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
