from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agenticaiops_shared.schemas import ChatRequest, ChatResponse, Telemetry, TelemetryResponse, ChatMessage
from agenticaiops_shared.guardrails import check_guardrail_standalone
from agenticaiops_shared.memory import MemoryStore
from agenticaiops_shared.database import get_db, SessionTelemetry, ComplaintTelemetry
from agenticaiops_shared.database.db import SessionLocal
from agenticaiops_shared.database.models import ChatMessage as ChatMessageModel

from qna.rag_agent import execute_qna, stream_qna, get_rag_engine
from qna.agent import execute_primary_agent, stream_primary_agent
from qna.skill_manager import SkillManager

logger = logging.getLogger("qna.router")
router = APIRouter(prefix="/api/qna", tags=["qna"])


def _strip_react(text: str) -> str:
    idx = -1
    for m in re.finditer(r"(?:Final\s*Answer\s*):\s*", text, re.IGNORECASE):
        idx = m.end()
    if idx >= 0:
        return text[idx:].strip()
    return text.strip()


def _build_telemetry(session, latency_ms: int) -> Telemetry:
    return Telemetry(
        memory_pct=0,
        token_cache_pct=session.token_cache_pct() if hasattr(session, "token_cache_pct") else 0,
        context_window="50K",
        latency_ms=latency_ms,
        message_count=len(session.messages),
        estimated_tokens=0,
        tokens_consumed=0,
        token_cost=0.0,
        tokens_per_second=0.0,
    )


def _route_by_agent(agent: str | None, message: str = "") -> str:
    raw_message = (message or "").strip()
    if raw_message.startswith("/") or raw_message.lower().startswith("trace-analyzer"):
        return "skill_workflow"

    if not agent:
        return "qna_workflow"
    mapping = {
        "Data Storyteller": "storyteller_workflow",
        "QnA Assistant": "qna_workflow",
        "Cognitive Operation & Customer Center": "cognitive_workflow",
        "Mobile Core Analyst": "cognitive_workflow",
        "Complaint Analyst": "cognitive_workflow",
        "Senior Telecom Signaling Analyst": "skill_workflow",
        "Telecom Signaling Analyst": "skill_workflow",
        "Telecom Signaling Specialist": "skill_workflow",
        "Signaling": "skill_workflow",
        "Skill Workflow": "skill_workflow",
        "Signaling Workflow": "skill_workflow",
    }
    return mapping.get(agent, "qna_workflow")


async def _stream_agent_chunks(
    query: str,
    session_id: str,
    route: str,
) -> AsyncIterator[tuple[str, str]]:
    """Yield (chunk_text, agent_role) tuples for the given route."""
    if route == "storyteller_workflow":
        try:
            from storyteller.agent import run_storyteller
        except ImportError:
            yield ("Storyteller agent not available", "Data Storyteller")
            return
        yield ("__AGENT__:Data Storyteller\n", "Data Storyteller")
        reply = await run_storyteller(query)
        for i in range(0, len(reply), 64):
            yield (reply[i:i+64], "Data Storyteller")
    elif route == "cognitive_workflow":
        from complaint.complaint.analyst import complaint_analyst
        redirect = complaint_analyst.validate_and_route_query(query)
        if redirect:
            yield ("__AGENT__:System Validator\n", "System Validator")
            yield (redirect, "System Validator")
            return
        yield ("__AGENT__:Cognitive Operation & Customer Center\n", "Cognitive Operation & Customer Center")
        async for chunk in stream_primary_agent(query=query, session_id=session_id):
            if chunk.content:
                yield (chunk.content, "Cognitive Operation & Customer Center")
    elif route in ("skill_workflow", "signaling_workflow"):
        manager = SkillManager()
        parts = query.strip().split()
        if parts:
            first_part = parts[0]
            if first_part.startswith("/"):
                skill_name = first_part[1:]
                arguments = parts[1:]
            elif first_part.lower() in ("trace-analyzer", "trace_analyzer"):
                skill_name = "trace-analyzer"
                arguments = parts[1:]
            else:
                skill_name = "trace-analyzer"
                pcap_arg = next((p for p in parts if p.endswith((".pcap", ".pcapng"))), None)
                arguments = [pcap_arg] if pcap_arg else parts
        else:
            skill_name = "trace-analyzer"
            arguments = []
        reply, agent_role = await manager.execute_skill(skill_name, arguments)
        yield (f"__AGENT__:{agent_role}\n", agent_role)
        for i in range(0, len(reply), 64):
            yield (reply[i:i+64], agent_role)
    else:
        yield ("__AGENT__:QnA Assistant\n", "QnA Assistant")
        engine = get_rag_engine()
        rag_result = await engine.aquery(query)
        if rag_result.get("chart_options"):
            reply = json.dumps(rag_result)
        else:
            answer = rag_result.get("answer", "No response from RAG system.")
            rag_retrievals = rag_result.get("rag_retrievals", "")
            if rag_retrievals:
                reply = f"{rag_retrievals}\n\nfinal answer:\n{answer}"
            else:
                reply = f"final answer:\n{answer}"
        for i in range(0, len(reply), 64):
            yield (reply[i:i+64], "QnA Assistant")


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


@router.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    memory_store = MemoryStore(db)
    session = memory_store.get_or_create(req.session_id)
    session.add("user", req.message.strip())

    route = _route_by_agent(req.agent, req.message)
    start = time.perf_counter()
    full_reply = ""
    raw_parts: list[str] = []
    agent_role = "Assistant"
    async for chunk_text, role in _stream_agent_chunks(req.message.strip(), req.session_id or "default", route):
        if not chunk_text.startswith("__AGENT__"):
            raw_parts.append(chunk_text)
        if not chunk_text.startswith("__AGENT__"):
            agent_role = role

    raw_reply = "".join(raw_parts)
    full_reply = _strip_react(raw_reply) or raw_reply
    if not full_reply:
        full_reply = "I do not know the answer"

    latency_ms = int((time.perf_counter() - start) * 1000)

    session.add("assistant", raw_reply)
    prompt_tokens = max(len(req.message) // 4, 1)
    completion_tokens = max(len(full_reply) // 4, 1)
    db.add(SessionTelemetry(
        session_id=req.session_id,
        agent_name=agent_role,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        latency_ms=latency_ms,
        throughput_tps=round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0,
        estimated_cost_usd=round((prompt_tokens + completion_tokens) * 0.000005, 6),
    ))
    db.commit()

    return ChatResponse(
        session_id=session.session_id,
        reply=full_reply,
        messages=session.messages,
        telemetry=_build_telemetry(session, latency_ms=latency_ms),
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    route = _route_by_agent(req.agent, req.message)

    async def _event_generator():
        local_db = SessionLocal()
        try:
            start_time = time.perf_counter()
            full_reply_parts: list[str] = []

            memory_store = MemoryStore(local_db)
            session = memory_store.get_or_create(req.session_id)
            session.add("user", req.message.strip())

            last_agent_role = "Assistant"
            async for chunk_text, role in _stream_agent_chunks(req.message.strip(), req.session_id or "default", route):
                yield chunk_text
                if not chunk_text.startswith("__AGENT__"):
                    full_reply_parts.append(chunk_text)
                last_agent_role = role

            raw_reply = "".join(full_reply_parts)
            if not raw_reply:
                raw_reply = "I do not know the answer"

            session.add("assistant", raw_reply)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            full_reply = _strip_react(raw_reply) or raw_reply
            prompt_tokens = max(len(req.message) // 4, 1)
            completion_tokens = max(len(full_reply) // 4, 1)
            local_db.add(SessionTelemetry(
                session_id=req.session_id,
                agent_name=last_agent_role,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=latency_ms,
                throughput_tps=round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0,
                estimated_cost_usd=round((prompt_tokens + completion_tokens) * 0.000005, 6),
            ))
            local_db.commit()
        except Exception as exc:
            logger.error("chat/stream error: %s", exc)
            yield f"\nError: {exc}"
        finally:
            local_db.close()

    return StreamingResponse(
        _event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/mobile-core-analyst")
async def mobile_core_analyst(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    memory_store = MemoryStore(db)
    session = memory_store.get_or_create(req.session_id)
    session.add("user", req.message.strip())

    from complaint.complaint.analyst import complaint_analyst
    redirect = complaint_analyst.validate_and_route_query(req.message.strip())
    if redirect:
        session.add("assistant", redirect)
        db.add(SessionTelemetry(
            session_id=req.session_id,
            agent_name="System Validator",
            prompt_tokens=max(len(req.message) // 4, 1),
            completion_tokens=max(len(redirect) // 4, 1),
            total_tokens=max(len(req.message) // 4, 1) + max(len(redirect) // 4, 1),
            latency_ms=0,
            throughput_tps=0.0,
            estimated_cost_usd=0.0,
        ))
        db.commit()
        return ChatResponse(
            session_id=session.session_id,
            reply=redirect,
            messages=session.messages,
            telemetry=_build_telemetry(session, latency_ms=0),
        )

    start = time.perf_counter()
    reply = complaint_analyst.analyze(req.message.strip(), user_role=req.user_role or "Customer_Ops", session_id=req.session_id)
    latency_ms = int((time.perf_counter() - start) * 1000)

    session.add("assistant", reply)
    prompt_tokens = max(len(req.message) // 4, 1)
    completion_tokens = max(len(reply) // 4, 1)
    db.add(SessionTelemetry(
        session_id=req.session_id,
        agent_name="Customer Complaint Analyst",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        latency_ms=latency_ms,
        throughput_tps=round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0,
        estimated_cost_usd=round((prompt_tokens + completion_tokens) * 0.000005, 6),
    ))
    db.commit()

    return ChatResponse(
        session_id=session.session_id,
        reply=reply,
        messages=session.messages,
        telemetry=_build_telemetry(session, latency_ms=latency_ms),
    )


@router.post("/mobile-core-analyst/stream")
async def mobile_core_analyst_stream(req: ChatRequest) -> StreamingResponse:
    from complaint.complaint.analyst import complaint_analyst
    redirect = complaint_analyst.validate_and_route_query(req.message.strip())
    if redirect:
        async def _validation_failed():
            yield "__AGENT__:System Validator\n"
            yield redirect
        return StreamingResponse(
            _validation_failed(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    async def _event_generator():
        local_db = SessionLocal()
        try:
            start_time = time.perf_counter()
            full_reply_parts: list[str] = []

            memory_store = MemoryStore(local_db)
            session = memory_store.get_or_create(req.session_id)
            session.add("user", req.message.strip())

            yield "__AGENT__:Customer Complaint Analyst\n"
            async for chunk in complaint_analyst.stream_analyze(req.message.strip(), user_role=req.user_role or "Customer_Ops", session_id=req.session_id):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
                    full_reply_parts.append(chunk.content)

            full_reply = "".join(full_reply_parts)
            session.add("assistant", full_reply)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            prompt_tokens = max(len(req.message) // 4, 1)
            completion_tokens = max(len(full_reply) // 4, 1)
            local_db.add(SessionTelemetry(
                session_id=req.session_id,
                agent_name="Customer Complaint Analyst",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=latency_ms,
                throughput_tps=round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0,
                estimated_cost_usd=round((prompt_tokens + completion_tokens) * 0.000005, 6),
            ))
            local_db.commit()
        except Exception as exc:
            logger.error("mobile-core-analyst/stream error: %s", exc)
            yield f"\nError: {exc}"
        finally:
            local_db.close()

    return StreamingResponse(
        _event_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/telemetry/{session_id}")
async def get_telemetry(session_id: str, db: Session = Depends(get_db)):
    memory_store = MemoryStore(db)
    session = memory_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    from datetime import datetime
    tel_records = db.query(SessionTelemetry).filter(SessionTelemetry.session_id == session_id).all()

    if tel_records:
        accumulated_total = sum(r.total_tokens for r in tel_records)
        accumulated_completion = sum(r.completion_tokens for r in tel_records)
        accumulated_cost = sum(r.estimated_cost_usd for r in tel_records)
        latest_record = sorted(tel_records, key=lambda r: r.created_at or datetime.min, reverse=True)[0]

        capped_total_tokens = min(accumulated_total, 50000)
        capped_cost = min(accumulated_cost, 0.25)
        memory_pct = min(100, int((capped_total_tokens / 50000) * 100))

        return TelemetryResponse(
            session_id=session_id,
            telemetry=Telemetry(
                memory_pct=memory_pct,
                token_cache_pct=session.token_cache_pct(),
                context_window="50K",
                latency_ms=latest_record.latency_ms,
                message_count=len(session.messages),
                estimated_tokens=capped_total_tokens,
                tokens_consumed=min(accumulated_completion, 50000),
                token_cost=max(capped_cost, 0.0),
                tokens_per_second=latest_record.throughput_tps,
            ),
        )

    return TelemetryResponse(
        session_id=session_id,
        telemetry=Telemetry(
            memory_pct=0,
            token_cache_pct=0.0,
            context_window="50K",
            latency_ms=0,
            message_count=0,
            estimated_tokens=0,
            tokens_consumed=0,
            token_cost=0.0,
            tokens_per_second=0.0,
        ),
    )


@router.get("/complaints/telemetry")
async def get_complaints_telemetry(db: Session = Depends(get_db)):
    records = db.query(ComplaintTelemetry).order_by(ComplaintTelemetry.time_reported.desc()).all()
    return [r.to_dict() for r in records]
