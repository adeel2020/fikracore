import json
import time
import asyncio

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from crewai.events import BaseEventListener, LLMStreamChunkEvent

from backend.agent.memory import MemoryStore
from backend.agent.rag_agent import execute_qna, stream_qna
from backend.agent.data_storyteller_agent import (
    run_storyteller,
)
from backend.agent.primary_agent import execute_primary_agent, stream_primary_agent
from backend.config import settings
from backend.core.orchestrator import get_route
from backend.database.db import get_db, init_db
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    HealthResponse,
    Telemetry,
    TelemetryResponse,
)

load_dotenv()

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")

router = APIRouter(prefix="/api/qna", tags=["agentic-qna"])

def _parse_complaint_structured_event(text: str) -> dict | None:
    if "__STRUCTURED_EVENT__" not in text:
        return None
    try:
        start_marker = "__STRUCTURED_EVENT__"
        end_marker = "__END_STRUCTURED_EVENT__"
        start_idx = text.find(start_marker)
        end_idx = text.find(end_marker)
        if start_idx == -1:
            return None
        
        block = text[start_idx + len(start_marker):]
        if end_idx != -1:
            block = text[start_idx + len(start_marker):end_idx]
        
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        result = {}
        current_list_key = None
        for line in lines:
            if line.startswith("- ") and current_list_key:
                val = line[2:].strip()
                result[current_list_key].append(val)
            elif ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val == "":
                    result[key] = []
                    current_list_key = key
                else:
                    result[key] = val
                    current_list_key = None
            else:
                current_list_key = None
        return result
    except Exception as e:
        print(f"Error parsing structured event: {e}")
        return None


def _build_telemetry(session, latency_ms: int) -> Telemetry:
    from datetime import datetime
    from backend.database.db import SessionLocal
    from backend.database.models import SessionTelemetry

    db = getattr(session, "_db", None)
    if db is not None:
        records = db.query(SessionTelemetry).filter(SessionTelemetry.session_id == session.session_id).all()
    else:
        with SessionLocal() as local_db:
            records = local_db.query(SessionTelemetry).filter(SessionTelemetry.session_id == session.session_id).all()

    if records:
        accumulated_prompt = sum(r.prompt_tokens for r in records)
        accumulated_completion = sum(r.completion_tokens for r in records)
        accumulated_total = sum(r.total_tokens for r in records)
        accumulated_cost = sum(r.estimated_cost_usd for r in records)
        
        # Sort by creation time to get the latest record stats for latency and throughput
        latest_record = sorted(records, key=lambda r: r.created_at or datetime.min, reverse=True)[0]
        latest_latency_ms = latest_record.latency_ms
        latest_tps = latest_record.throughput_tps
    else:
        accumulated_prompt = 0
        accumulated_completion = 0
        accumulated_total = session.total_tokens()
        accumulated_cost = accumulated_total * 0.000005
        latest_latency_ms = latency_ms
        
        # Calculate tokens consumed (estimate last exchange)
        tokens_consumed = 0
        if len(session.messages) >= 2:
            last_user_msg = session.messages[-2].content if len(session.messages) >= 2 else ""
            last_assistant_msg = session.messages[-1].content if len(session.messages) >= 1 else ""
            tokens_consumed = (len(last_user_msg) + len(last_assistant_msg)) // 4
            
        latest_tps = 0.0
        if latency_ms > 0 and tokens_consumed > 0:
            latest_tps = (tokens_consumed / latency_ms) * 1000

    # Apply the 50,000 token cap and corresponding $0.25 cost cap
    capped_total_tokens = min(accumulated_total, 50000)
    capped_completion_tokens = min(accumulated_completion, 50000)
    capped_cost = min(accumulated_cost, 0.25)
    
    # Scale memory percentage based on the 50,000 token cap
    memory_pct = min(100, int((capped_total_tokens / 50000) * 100))

    return Telemetry(
        memory_pct=memory_pct,
        token_cache_pct=session.token_cache_pct(),
        context_window="50K",
        latency_ms=latest_latency_ms,
        message_count=len(session.messages),
        estimated_tokens=capped_total_tokens,
        tokens_consumed=capped_completion_tokens,
        token_cost=max(capped_cost, 0.0),
        tokens_per_second=max(latest_tps, 0.0),
    )


def _is_valid_trace_query(query: str) -> bool:
    import re
    q = query.strip()
    if q.startswith("/"):
        return True
    if re.search(r"\b[\w\.-]+\.pcap(?:ng)?\b", q, re.IGNORECASE):
        return True
    return False


def _is_matching_agent(agent_role: str, target_agent: str) -> bool:
    if agent_role == target_agent:
        return True
    cognitive_roles = {"Cognitive Operation & Customer Center", "Core Mobile Network Data Analyst"}
    if agent_role in cognitive_roles and target_agent in cognitive_roles:
        return True
    return False


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    mode = "openai" if settings.openai_api_key else "mock"
    return HealthResponse(status="ok", agent_mode=mode)


@router.get("/telemetry/{session_id}", response_model=TelemetryResponse)
async def get_telemetry(session_id: str, db: Session = Depends(get_db)) -> TelemetryResponse:
    memory_store = MemoryStore(db)
    session = memory_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    from datetime import datetime
    from backend.database.models import SessionTelemetry
    tel_records = db.query(SessionTelemetry).filter(SessionTelemetry.session_id == session_id).all()
    
    if tel_records:
        accumulated_prompt = sum(r.prompt_tokens for r in tel_records)
        accumulated_completion = sum(r.completion_tokens for r in tel_records)
        accumulated_total = sum(r.total_tokens for r in tel_records)
        accumulated_cost = sum(r.estimated_cost_usd for r in tel_records)
        
        # Sort by creation time to get the latest record stats for latency and throughput
        latest_record = sorted(tel_records, key=lambda r: r.created_at or datetime.min, reverse=True)[0]
        latest_latency_ms = latest_record.latency_ms
        latest_tps = latest_record.throughput_tps
        
        # Apply the 50,000 token cap and corresponding $0.25 cost cap
        capped_total_tokens = min(accumulated_total, 50000)
        capped_completion_tokens = min(accumulated_completion, 50000)
        capped_cost = min(accumulated_cost, 0.25)
        
        # Scale memory percentage based on the 50,000 token cap
        memory_pct = min(100, int((capped_total_tokens / 50000) * 100))

        return TelemetryResponse(
            session_id=session_id,
            telemetry=Telemetry(
                memory_pct=memory_pct,
                token_cache_pct=session.token_cache_pct(),
                context_window="50K",
                latency_ms=latest_latency_ms,
                message_count=len(session.messages),
                estimated_tokens=capped_total_tokens,
                tokens_consumed=capped_completion_tokens,
                token_cost=max(capped_cost, 0.0),
                tokens_per_second=latest_tps,
            )
        )

    return TelemetryResponse(
        session_id=session_id,
        telemetry=_build_telemetry(session, latency_ms=0),
    )


@router.post("/mobile-core-analyst", response_model=ChatResponse)
async def mobile_core_analyst_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    memory_store = MemoryStore(db)
    session = memory_store.get_or_create(request.session_id)
    session.add("user", request.message.strip())

    msg_strip = request.message.strip()
    is_skill = msg_strip.startswith("/")

    if not is_skill:
        from backend.agent.complaint_analyst import complaint_analyst
        redirect_message = complaint_analyst.validate_and_route_query(msg_strip)
        if redirect_message:
            session.add("assistant", redirect_message)
            
            from backend.database.models import SessionTelemetry
            telemetry_record = SessionTelemetry(
                session_id=request.session_id,
                agent_name="System Validator",
                prompt_tokens=max(len(request.message) // 4, 1),
                completion_tokens=max(len(redirect_message) // 4, 1),
                total_tokens=max(len(request.message) // 4, 1) + max(len(redirect_message) // 4, 1),
                latency_ms=0,
                throughput_tps=0.0,
                estimated_cost_usd=0.0
            )
            db.add(telemetry_record)
            db.commit()
            
            return ChatResponse(
                session_id=session.session_id,
                reply=redirect_message,
                messages=session.messages,
                telemetry=_build_telemetry(session, latency_ms=0),
            )

    if is_skill:
        from backend.agent.skill_manager import SkillManager
        manager = SkillManager()
        parts = msg_strip.split()
        skill_name = parts[0][1:]
        arguments = parts[1:]
        
        start = time.perf_counter()
        reply, agent_role = await manager.execute_skill(skill_name, arguments)
        latency_ms = int((time.perf_counter() - start) * 1000)
    else:
        from backend.agent.complaint_analyst import complaint_analyst
        start = time.perf_counter()
        reply = await asyncio.to_thread(complaint_analyst.analyze, request.message.strip())
        latency_ms = int((time.perf_counter() - start) * 1000)
        agent_role = "Customer Complaint Analyst"

    session.add("assistant", reply)

    if agent_role == "Customer Complaint Analyst":
        structured_data = _parse_complaint_structured_event(reply)
        if structured_data:
            from backend.database.models import ComplaintTelemetry, get_dubai_now
            from backend.agent.complaint_analyst import _resolve_team
            import random

            now = get_dubai_now()
            date_str = now.strftime("%Y%m%d")
            db_is_unique = False
            while not db_is_unique:
                random_num = random.randint(10000, 99999)
                complaint_num = f"INC-{date_str}-{random_num}"
                exists = db.query(ComplaintTelemetry).filter_by(complaint_number=complaint_num).first()
                if not exists:
                    db_is_unique = True

            assignment_target = structured_data.get("assignment_target", "")
            team_info = _resolve_team(assignment_target)
            assignment_queue = team_info.get("queue") if team_info else None

            complaint_rec = ComplaintTelemetry(
                session_id=request.session_id,
                complaint_number=complaint_num,
                issue_summary=structured_data.get("issue_summary", ""),
                assignment_target=assignment_target,
                assignment_queue=assignment_queue,
                reassignment_category=structured_data.get("reassignment_category", ""),
                resolution_category=structured_data.get("resolution_category", ""),
                raw_complaint=request.message.strip(),
            )
            db.add(complaint_rec)

    prompt_tokens = max(len(request.message) // 4, 1)
    completion_tokens = max(len(reply) // 4, 1)
    total_tokens = prompt_tokens + completion_tokens
    throughput_tps = round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0
    estimated_cost_usd = round(total_tokens * 0.000005, 6)

    from backend.database.models import SessionTelemetry
    telemetry_record = SessionTelemetry(
        session_id=request.session_id,
        agent_name=agent_role,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        throughput_tps=throughput_tps,
        estimated_cost_usd=estimated_cost_usd
    )
    db.add(telemetry_record)
    db.commit()

    return ChatResponse(
        session_id=session.session_id,
        reply=reply,
        messages=session.messages,
        telemetry=_build_telemetry(session, latency_ms=latency_ms),
    )


# Global registry to track active streams for mid-query reconnection/hydration on refresh
active_streams: dict[str, dict] = {}

@router.post("/mobile-core-analyst/stream")
async def customer_complaint_analyst_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream the Customer Complaint Analyst agent response chunk-by-chunk"""
    session_id = request.session_id
    msg_strip = request.message.strip()
    is_skill = msg_strip.startswith("/")

    if is_skill:
        from backend.agent.skill_manager import SkillManager
        manager = SkillManager()
        parts = msg_strip.split()
        skill_name = parts[0][1:]
        skill_agent_role = "Senior Telecom Signaling Analyst"
        skill_item = manager.get_skill(skill_name)
        if skill_item:
            skill_agent_role = skill_item.role
        target_agent = skill_agent_role
    else:
        target_agent = "Customer Complaint Analyst"

    # Clean up previously completed streams from memory when starting or reconnecting
    if session_id in active_streams and active_streams[session_id].get("done", False):
        active_streams.pop(session_id, None)

    # Reconnect to an ongoing stream if it exists
    if session_id in active_streams:
        print(f"[Stream Reconnect] Reconnecting client to active stream for session: {session_id}")
        queue = active_streams[session_id]["queue"]
    else:
        # Save query to database and prepare new stream
        memory_store = MemoryStore(db)
        session = memory_store.get_or_create(session_id)
        session.add("user", msg_strip)

        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        active_streams[session_id] = {
            "queue": queue,
            "accumulated_chunks": [],
            "done": False,
        }

        # Spawn independent background thread/task to execute crew task
        async def run_crew_task():
            start_time = time.perf_counter()
            full_reply_parts = []
            try:
                if is_skill:
                    from backend.agent.skill_manager import SkillManager
                    manager = SkillManager()
                    parts = msg_strip.split()
                    skill_name = parts[0][1:]
                    arguments = parts[1:]
                    
                    reply, agent_role = await manager.execute_skill(skill_name, arguments)
                    
                    chunk_obj = (f"__AGENT__:{agent_role}\n", agent_role)
                    active_streams[session_id]["accumulated_chunks"].append(chunk_obj)
                    loop.call_soon_threadsafe(queue.put_nowait, chunk_obj)
                    
                    chunk_size = 64
                    for i in range(0, len(reply), chunk_size):
                        chunk = reply[i:i+chunk_size]
                        chunk_obj = (chunk, agent_role)
                        active_streams[session_id]["accumulated_chunks"].append(chunk_obj)
                        loop.call_soon_threadsafe(queue.put_nowait, chunk_obj)
                else:
                    from backend.agent.complaint_analyst import complaint_analyst
                    user_role = request.user_role or "Customer_Ops"
                    async for chunk in complaint_analyst.stream_analyze(msg_strip, user_role=user_role, session_id=session_id):
                        chunk_obj = (chunk.content, chunk.agent_role)
                        active_streams[session_id]["accumulated_chunks"].append(chunk_obj)
                        loop.call_soon_threadsafe(queue.put_nowait, chunk_obj)
                
                # Signal end of queue
                loop.call_soon_threadsafe(queue.put_nowait, None)

                # Reassemble full reply
                for chunk_text, agent_role in active_streams[session_id]["accumulated_chunks"]:
                    if (agent_role == target_agent or agent_role == "System Validator") and chunk_text:
                        if not chunk_text.startswith("__AGENT__"):
                            full_reply_parts.append(chunk_text)

                full_reply = "".join(full_reply_parts)
                if not full_reply:
                    full_reply = "I do not know the answer"

                # Persist answer and telemetry directly to SQLite inside background task
                from backend.database.db import SessionLocal
                from backend.database.models import ChatMessage as ChatMessageModel, SessionTelemetry
                
                with SessionLocal() as local_db:
                    msg_record = ChatMessageModel(
                        session_id=session_id,
                        role="assistant",
                        content=full_reply
                    )
                    local_db.add(msg_record)
                    
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    prompt_tokens = max(len(msg_strip) // 4, 1)
                    completion_tokens = max(len(full_reply) // 4, 1)
                    total_tokens = prompt_tokens + completion_tokens
                    throughput_tps = round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0
                    estimated_cost_usd = round(total_tokens * 0.000005, 6)
                    
                    telemetry_record = SessionTelemetry(
                        session_id=session_id,
                        agent_name=target_agent,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        latency_ms=latency_ms,
                        throughput_tps=throughput_tps,
                        estimated_cost_usd=estimated_cost_usd
                    )
                    local_db.add(telemetry_record)

                    if target_agent == "Customer Complaint Analyst":
                        structured_data = _parse_complaint_structured_event(full_reply)
                        if structured_data:
                            from backend.database.models import ComplaintTelemetry, get_dubai_now
                            from backend.agent.complaint_analyst import _resolve_team
                            import random

                            now = get_dubai_now()
                            date_str = now.strftime("%Y%m%d")
                            db_is_unique = False
                            while not db_is_unique:
                                random_num = random.randint(10000, 99999)
                                complaint_num = f"INC-{date_str}-{random_num}"
                                exists = local_db.query(ComplaintTelemetry).filter_by(complaint_number=complaint_num).first()
                                if not exists:
                                    db_is_unique = True

                            assignment_target = structured_data.get("assignment_target", "")
                            team_info = _resolve_team(assignment_target)
                            assignment_queue = team_info.get("queue") if team_info else None

                            complaint_rec = ComplaintTelemetry(
                                session_id=session_id,
                                complaint_number=complaint_num,
                                issue_summary=structured_data.get("issue_summary", ""),
                                assignment_target=assignment_target,
                                assignment_queue=assignment_queue,
                                reassignment_category=structured_data.get("reassignment_category", ""),
                                resolution_category=structured_data.get("resolution_category", ""),
                                raw_complaint=msg_strip,
                            )
                            local_db.add(complaint_rec)

                    local_db.commit()

                # Sync in-memory store
                memory_store = MemoryStore(db)
                session = memory_store.get_or_create(session_id)
                session.messages.append(ChatMessage(role="assistant", content=full_reply))

            except Exception as e:
                print(f"[SSE] Background task failed: {e}")
                loop.call_soon_threadsafe(queue.put_nowait, e)
            finally:
                if session_id in active_streams:
                    active_streams[session_id]["done"] = True

        asyncio.create_task(run_crew_task())

    # Yield redirect if validation failed
    if not is_skill:
        from backend.agent.complaint_analyst import complaint_analyst
        redirect_message = complaint_analyst.validate_and_route_query(msg_strip)
        if redirect_message:
            async def _validation_failed_generator():
                yield "__AGENT__:System Validator\n"
                yield redirect_message
                
                from backend.database.db import SessionLocal
                from backend.database.models import ChatMessage as ChatMessageModel, SessionTelemetry
                with SessionLocal() as local_db:
                    msg_record = ChatMessageModel(
                        session_id=session_id,
                        role="assistant",
                        content=redirect_message
                    )
                    local_db.add(msg_record)
                    
                    telemetry_record = SessionTelemetry(
                        session_id=session_id,
                        agent_name="System Validator",
                        prompt_tokens=max(len(msg_strip) // 4, 1),
                        completion_tokens=max(len(redirect_message) // 4, 1),
                        total_tokens=max(len(msg_strip) // 4, 1) + max(len(redirect_message) // 4, 1),
                        latency_ms=0,
                        throughput_tps=0.0,
                        estimated_cost_usd=0.0
                    )
                    local_db.add(telemetry_record)
                    local_db.commit()
                
                memory_store = MemoryStore(db)
                session = memory_store.get_or_create(session_id)
                session.messages.append(ChatMessage(role="assistant", content=redirect_message))
                active_streams.pop(session_id, None)

            return StreamingResponse(
                _validation_failed_generator(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

    # Event generator that catches up the client and streams new chunks in real-time
    last_agent_role = None

    async def _event_generator():
        nonlocal last_agent_role
        try:
            # 1. Stream all accumulated history first (catch up)
            for chunk_text, agent_role in list(active_streams[session_id]["accumulated_chunks"]):
                if agent_role != last_agent_role:
                    last_agent_role = agent_role
                    yield f"__AGENT__:{agent_role}\n"
                
                if (agent_role == target_agent or agent_role == "System Validator") and chunk_text:
                    if not chunk_text.startswith("__AGENT__"):
                        yield chunk_text

            # 2. If task was already completed, stop here
            if active_streams[session_id]["done"]:
                return

            # 3. Stream real-time events as they arrive in the queue
            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item

                chunk_text, agent_role = item

                if agent_role != last_agent_role:
                    last_agent_role = agent_role
                    yield f"__AGENT__:{agent_role}\n"

                if (agent_role == target_agent or agent_role == "System Validator") and chunk_text:
                    if not chunk_text.startswith("__AGENT__"):
                        yield chunk_text

        except asyncio.CancelledError:
            # Client disconnected mid-query again; ignore to allow background task to complete safely.
            pass
        except Exception as exc:
            print(f"[SSE] Streaming error: {exc}")
            yield f"\nError: {exc}"

    return StreamingResponse(
        _event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    memory_store = MemoryStore(db)
    session = memory_store.get_or_create(request.session_id)
    session.add("user", request.message.strip())

    msg_strip = request.message.strip()
    is_skill = msg_strip.startswith("/")

    route = get_route(request.message, session_id=request.session_id, db=db)

    if route in ("signaling_workflow", "skill_workflow"):
        if not _is_valid_trace_query(request.message):
            skill_agent_role = "Senior Telecom Signaling Analyst"
            from backend.agent.skill_manager import SkillManager
            manager = SkillManager()
            parts = msg_strip.split()
            skill_name = parts[0][1:] if parts[0].startswith("/") else "trace-analyzer"
            skill_item = manager.get_skill(skill_name)
            if skill_item:
                skill_agent_role = skill_item.role

            reply = (
                f"I am the {skill_agent_role}. I can only assist with analyzing and "
                f"troubleshooting core mobile network signaling PCAP trace files. "
                f"Please provide a PCAP or PCAPNG trace file to analyze (e.g., using `/trace-analyzer [file]`)."
            )
            session.add("assistant", reply)

            from backend.database.models import SessionTelemetry
            telemetry_record = SessionTelemetry(
                session_id=request.session_id,
                agent_name=skill_agent_role,
                prompt_tokens=max(len(request.message) // 4, 1),
                completion_tokens=max(len(reply) // 4, 1),
                total_tokens=max(len(request.message) // 4, 1) + max(len(reply) // 4, 1),
                latency_ms=0,
                throughput_tps=0.0,
                estimated_cost_usd=0.0
            )
            db.add(telemetry_record)
            db.commit()

            return ChatResponse(
                session_id=session.session_id,
                reply=reply,
                messages=session.messages,
                telemetry=_build_telemetry(session, latency_ms=0),
            )

    if not is_skill and route == "cognitive_workflow":
        from backend.agent.complaint_analyst import complaint_analyst
        redirect_message = complaint_analyst.validate_and_route_query(msg_strip)
        if redirect_message:
            session.add("assistant", redirect_message)
            
            from backend.database.models import SessionTelemetry
            telemetry_record = SessionTelemetry(
                session_id=request.session_id,
                agent_name="System Validator",
                prompt_tokens=max(len(request.message) // 4, 1),
                completion_tokens=max(len(redirect_message) // 4, 1),
                total_tokens=max(len(request.message) // 4, 1) + max(len(redirect_message) // 4, 1),
                latency_ms=0,
                throughput_tps=0.0,
                estimated_cost_usd=0.0
            )
            db.add(telemetry_record)
            db.commit()
            
            return ChatResponse(
                session_id=session.session_id,
                reply=redirect_message,
                messages=session.messages,
                telemetry=_build_telemetry(session, latency_ms=0),
            )
    if route == "storyteller_workflow":
        start = time.perf_counter()
        from functools import partial
        user_message = session.messages[-1].content if session.messages else request.message
        hist = []
        for m in session.messages[:-1]:
            if m.role == "user":
                hist.append({"q": m.content})
            else:
                hist.append({"a": m.content})
        reply = await asyncio.to_thread(partial(run_storyteller, user_message, history=hist))
        latency_ms = int((time.perf_counter() - start) * 1000)

        session.add("assistant", reply)

        prompt_tokens = max(len(request.message) // 4, 1)
        completion_tokens = max(len(reply) // 4, 1)
        total_tokens = prompt_tokens + completion_tokens
        throughput_tps = round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0
        estimated_cost_usd = round(total_tokens * 0.000005, 6)
        
        from backend.database.models import SessionTelemetry
        telemetry_record = SessionTelemetry(
            session_id=request.session_id,
            agent_name="Data Storyteller",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            throughput_tps=throughput_tps,
            estimated_cost_usd=estimated_cost_usd
        )
        db.add(telemetry_record)
        db.commit()

        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            messages=session.messages,
            telemetry=_build_telemetry(session, latency_ms=latency_ms),
        )

    if route == "cognitive_workflow":
        start = time.perf_counter()
        reply = await execute_primary_agent(query=request.message, session_id=session.session_id)
        latency_ms = int((time.perf_counter() - start) * 1000)

        session.add("assistant", reply)

        prompt_tokens = max(len(request.message) // 4, 1)
        completion_tokens = max(len(reply) // 4, 1)
        total_tokens = prompt_tokens + completion_tokens
        throughput_tps = round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0
        estimated_cost_usd = round(total_tokens * 0.000005, 6)

        from backend.database.models import SessionTelemetry
        telemetry_record = SessionTelemetry(
            session_id=request.session_id,
            agent_name="Cognitive Operation & Customer Center",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            throughput_tps=throughput_tps,
            estimated_cost_usd=estimated_cost_usd
        )
        db.add(telemetry_record)
        db.commit()

        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            messages=session.messages,
            telemetry=_build_telemetry(session, latency_ms=latency_ms),
        )

    if route in ("signaling_workflow", "skill_workflow"):
        from backend.agent.skill_manager import SkillManager
        manager = SkillManager()
        
        msg_strip = request.message.strip()
        parts = msg_strip.split()
        skill_name = parts[0][1:] if parts[0].startswith("/") else "trace-analyzer"
        arguments = parts[1:]
        
        start = time.perf_counter()
        reply, agent_name = await manager.execute_skill(skill_name, arguments)
        latency_ms = int((time.perf_counter() - start) * 1000)

        session.add("assistant", reply)

        prompt_tokens = max(len(request.message) // 4, 1)
        completion_tokens = max(len(reply) // 4, 1)
        total_tokens = prompt_tokens + completion_tokens
        throughput_tps = round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0
        estimated_cost_usd = round(total_tokens * 0.000005, 6)

        from backend.database.models import SessionTelemetry
        telemetry_record = SessionTelemetry(
            session_id=request.session_id,
            agent_name=agent_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            throughput_tps=throughput_tps,
            estimated_cost_usd=estimated_cost_usd
        )
        db.add(telemetry_record)
        db.commit()

        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            messages=session.messages,
            telemetry=_build_telemetry(session, latency_ms=latency_ms),
        )

    start = time.perf_counter()
    reply = await execute_qna(query=request.message, session_id=session.session_id)
    latency_ms = int((time.perf_counter() - start) * 1000)

    session.add("assistant", reply)

    prompt_tokens = max(len(request.message) // 4, 1)
    completion_tokens = max(len(reply) // 4, 1)
    total_tokens = prompt_tokens + completion_tokens
    throughput_tps = round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0
    estimated_cost_usd = round(total_tokens * 0.000005, 6)
    
    from backend.database.models import SessionTelemetry
    telemetry_record = SessionTelemetry(
        session_id=request.session_id,
        agent_name="QnA Assistant",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        throughput_tps=throughput_tps,
        estimated_cost_usd=estimated_cost_usd
    )
    db.add(telemetry_record)
    db.commit()

    return ChatResponse(
        session_id=session.session_id,
        reply=reply,
        messages=session.messages,
        telemetry=_build_telemetry(session, latency_ms=latency_ms),
    )


active_session_tasks: dict[str, asyncio.Task] = {}
active_session_queues: dict[str, list[asyncio.Queue]] = {}

# ------------------------------------------------------------------
# Plain text streaming endpoint
# ------------------------------------------------------------------
@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream the agent response as plain text chunks directly,
    matching the StreamingTest.py approach.
    """
    memory_store = MemoryStore(db)
    session = memory_store.get_or_create(request.session_id)
    session.add("user", request.message.strip())

    msg_strip = request.message.strip()
    is_skill = msg_strip.startswith("/")

    route = get_route(request.message, session_id=request.session_id, db=db)

    if route in ("signaling_workflow", "skill_workflow"):
        if not _is_valid_trace_query(request.message):
            skill_agent_role = "Senior Telecom Signaling Analyst"
            from backend.agent.skill_manager import SkillManager
            manager = SkillManager()
            parts = msg_strip.split()
            skill_name = parts[0][1:] if parts[0].startswith("/") else "trace-analyzer"
            skill_item = manager.get_skill(skill_name)
            if skill_item:
                skill_agent_role = skill_item.role

            redirect_message = (
                f"I am the {skill_agent_role}. I can only assist with analyzing and "
                f"troubleshooting core mobile network signaling PCAP trace files. "
                f"Please provide a PCAP or PCAPNG trace file to analyze (e.g., using `/trace-analyzer [file]`)."
            )

            async def _signaling_validation_failed_generator():
                yield f"__AGENT__:{skill_agent_role}\n"
                yield redirect_message
                
                # Persist assistant response and telemetry to db
                from backend.database.db import SessionLocal
                from backend.database.models import ChatMessage as ChatMessageModel, SessionTelemetry
                with SessionLocal() as local_db:
                    msg_record = ChatMessageModel(
                        session_id=request.session_id,
                        role="assistant",
                        content=redirect_message
                    )
                    local_db.add(msg_record)
                    
                    telemetry_record = SessionTelemetry(
                        session_id=request.session_id,
                        agent_name=skill_agent_role,
                        prompt_tokens=max(len(request.message) // 4, 1),
                        completion_tokens=max(len(redirect_message) // 4, 1),
                        total_tokens=max(len(request.message) // 4, 1) + max(len(redirect_message) // 4, 1),
                        latency_ms=0,
                        throughput_tps=0.0,
                        estimated_cost_usd=0.0
                    )
                    local_db.add(telemetry_record)
                    local_db.commit()
                session.messages.append(ChatMessage(role="assistant", content=redirect_message))

            return StreamingResponse(
                _signaling_validation_failed_generator(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection-type": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

    if not is_skill and route == "cognitive_workflow":
        from backend.agent.complaint_analyst import complaint_analyst
        redirect_message = complaint_analyst.validate_and_route_query(msg_strip)
        if redirect_message:
            async def _validation_failed_generator():
                yield "__AGENT__:System Validator\n"
                yield redirect_message
                
                # Persist assistant response and telemetry to db
                from backend.database.db import SessionLocal
                from backend.database.models import ChatMessage as ChatMessageModel, SessionTelemetry
                with SessionLocal() as local_db:
                    msg_record = ChatMessageModel(
                        session_id=request.session_id,
                        role="assistant",
                        content=redirect_message
                    )
                    local_db.add(msg_record)
                    
                    telemetry_record = SessionTelemetry(
                        session_id=request.session_id,
                        agent_name="System Validator",
                        prompt_tokens=max(len(request.message) // 4, 1),
                        completion_tokens=max(len(redirect_message) // 4, 1),
                        total_tokens=max(len(request.message) // 4, 1) + max(len(redirect_message) // 4, 1),
                        latency_ms=0,
                        throughput_tps=0.0,
                        estimated_cost_usd=0.0
                    )
                    local_db.add(telemetry_record)
                    local_db.commit()
                session.messages.append(ChatMessage(role="assistant", content=redirect_message))

            return StreamingResponse(
                _validation_failed_generator(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

    async def _event_generator():
        start_time = time.perf_counter()
        full_reply_parts: list[str] = []

        try:
            queue = asyncio.Queue()
            queues_list = active_session_queues.setdefault(request.session_id, [])
            queues_list.append(queue)
            
            loop = asyncio.get_running_loop()

            class MyStreamListener(BaseEventListener):
                def setup_listeners(self, crewai_event_bus):
                    @crewai_event_bus.on(LLMStreamChunkEvent)
                    def on_llm_stream_chunk(source, event):
                        chunk = event.chunk
                        print(chunk, end="", flush=True)
                        for q in active_session_queues.get(request.session_id, []):
                            loop.call_soon_threadsafe(
                                q.put_nowait,
                                (chunk, event.agent_role)
                            )
                    self.handler = on_llm_stream_chunk
                    self.bus = crewai_event_bus

            # Resolve skill dynamic target role if this is a skill/signaling command
            skill_agent_role = "Senior Telecom Signaling Analyst"
            if route in ("signaling_workflow", "skill_workflow"):
                from backend.agent.skill_manager import SkillManager
                manager = SkillManager()
                msg_strip = request.message.strip()
                parts = msg_strip.split()
                skill_name = parts[0][1:] if parts[0].startswith("/") else "trace-analyzer"
                skill_item = manager.get_skill(skill_name)
                if skill_item:
                    skill_agent_role = skill_item.role

            listener = MyStreamListener()
            target_agent = "Data Storyteller" if route == "storyteller_workflow" else (
                skill_agent_role if route in ("signaling_workflow", "skill_workflow") else (
                    "Cognitive Operation & Customer Center" if route == "cognitive_workflow" else "QnA Assistant"
                )
            )
            last_agent_role = None

            async def run_crew_task():
                try:
                    if route == "storyteller_workflow":
                        from functools import partial
                        user_message = session.messages[-1].content if session.messages else request.message
                        hist = []
                        for m in session.messages[:-1]:
                            if m.role == "user":
                                hist.append({"q": m.content})
                            else:
                                hist.append({"a": m.content})
                        reply = await asyncio.to_thread(partial(run_storyteller, user_message, history=hist))
                        for q in active_session_queues.get(request.session_id, []):
                            loop.call_soon_threadsafe(
                                q.put_nowait,
                                ("__AGENT__:Data Storyteller\n", "Data Storyteller")
                            )
                        chunk_size = 64
                        for i in range(0, len(reply), chunk_size):
                            chunk = reply[i:i+chunk_size]
                            for q in active_session_queues.get(request.session_id, []):
                                loop.call_soon_threadsafe(
                                    q.put_nowait,
                                    (chunk, "Data Storyteller")
                                )
                            await asyncio.sleep(0.015)
                    elif route == "cognitive_workflow":
                        async for _ in stream_primary_agent(query=request.message, session_id=session.session_id):
                            pass
                    elif route in ("signaling_workflow", "skill_workflow"):
                        from backend.agent.skill_manager import SkillManager
                        manager = SkillManager()
                        
                        msg_strip = request.message.strip()
                        parts = msg_strip.split()
                        skill_name = parts[0][1:] if parts[0].startswith("/") else "trace-analyzer"
                        arguments = parts[1:]
                        
                        # Execute the skill
                        reply, agent_role = await manager.execute_skill(skill_name, arguments)
                        
                        # Yield the agent role first
                        for q in active_session_queues.get(request.session_id, []):
                            loop.call_soon_threadsafe(
                                q.put_nowait,
                                (f"__AGENT__:{agent_role}\n", agent_role)
                            )
                        
                        # Stream the result chunk by chunk
                        chunk_size = 64
                        for i in range(0, len(reply), chunk_size):
                            chunk = reply[i:i+chunk_size]
                            for q in active_session_queues.get(request.session_id, []):
                                loop.call_soon_threadsafe(
                                    q.put_nowait,
                                    (chunk, agent_role)
                                )
                            await asyncio.sleep(0.015)
                    else:
                        from backend.agent.rag_agent import get_rag_engine
                        rag_engine = get_rag_engine()
                        import json
                        try:
                            rag_result = await rag_engine.aquery(request.message)
                        except Exception:
                            rag_result = None

                        if rag_result and rag_result.get("chart_options"):
                            # Chart query — send as JSON for frontend pill rendering
                            reply = json.dumps(rag_result)
                        elif rag_result:
                            # Non-chart query — send rag_retrievals before final answer marker
                            answer = rag_result.get("answer", "No response from RAG system.")
                            rag_retrievals = rag_result.get("rag_retrievals", "")
                            if rag_retrievals:
                                reply = f"{rag_retrievals}\n\nfinal answer:\n{answer}"
                            else:
                                reply = answer
                        else:
                            reply = "Error querying RAG system."

                        for q in active_session_queues.get(request.session_id, []):
                            loop.call_soon_threadsafe(q.put_nowait, ("__AGENT__:QnA Assistant\n", "QnA Assistant"))
                        chunk_size = 64
                        for i in range(0, len(reply), chunk_size):
                            chunk = reply[i:i+chunk_size]
                            for q in active_session_queues.get(request.session_id, []):
                                loop.call_soon_threadsafe(q.put_nowait, (chunk, "QnA Assistant"))
                            await asyncio.sleep(0.015)
                    
                    for q in active_session_queues.get(request.session_id, []):
                        loop.call_soon_threadsafe(q.put_nowait, None)
                except Exception as e:
                    print(f"[SSE] Crew kickoff task failed: {e}")
                    for q in active_session_queues.get(request.session_id, []):
                        loop.call_soon_threadsafe(q.put_nowait, e)

            # Get or start background crew task
            existing_task = active_session_tasks.get(request.session_id)
            if existing_task and not existing_task.done():
                print(f"[SSE] Reconnecting to existing crew task for session {request.session_id}")
                crew_task = existing_task
            else:
                print(f"[SSE] Starting new crew task for session {request.session_id}")
                crew_task = asyncio.create_task(run_crew_task())
                active_session_tasks[request.session_id] = crew_task

            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item

                chunk_text, agent_role = item

                # Yield agent name marker when active agent changes
                if agent_role != last_agent_role:
                    last_agent_role = agent_role
                    yield f"__AGENT__:{agent_role}\n"

                # Yield text chunks only for the target agent or System Validator
                if (_is_matching_agent(agent_role, target_agent) or agent_role == "System Validator") and chunk_text:
                    if not chunk_text.startswith("__AGENT__"):
                        full_reply_parts.append(chunk_text)
                        yield chunk_text

            # Crew finished — persist to memory and database
            full_reply = "".join(full_reply_parts)
            
            # Since the original FastAPI request-scoped session `db` is closed when streaming begins,
            # we open a fresh local session to safely persist the assistant message & telemetry.
            from backend.database.db import SessionLocal
            from backend.database.models import ChatMessage as ChatMessageModel, SessionTelemetry
            
            with SessionLocal() as local_db:
                # 1. Persist the assistant response message
                msg_record = ChatMessageModel(
                    session_id=request.session_id,
                    role="assistant",
                    content=full_reply
                )
                local_db.add(msg_record)
                
                # 2. Persist the telemetry record
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                prompt_tokens = max(len(request.message) // 4, 1)
                completion_tokens = max(len(full_reply) // 4, 1)
                total_tokens = prompt_tokens + completion_tokens
                throughput_tps = round((completion_tokens / (latency_ms / 1000.0)), 2) if latency_ms > 0 else 0.0
                estimated_cost_usd = round(total_tokens * 0.000005, 6)
                
                telemetry_record = SessionTelemetry(
                    session_id=request.session_id,
                    agent_name=target_agent,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    throughput_tps=throughput_tps,
                    estimated_cost_usd=estimated_cost_usd
                )
                local_db.add(telemetry_record)
                
                # Commit both records safely
                local_db.commit()

            # Append to request-scoped session list
            session.messages.append(ChatMessage(role="assistant", content=full_reply))

        except Exception as exc:
            print(f"[SSE] Streaming error: {exc}")
            yield f"\nError: {exc}"
        finally:
            try:
                if request.session_id in active_session_queues:
                    if queue in active_session_queues[request.session_id]:
                        active_session_queues[request.session_id].remove(queue)
                    if not active_session_queues[request.session_id]:
                        del active_session_queues[request.session_id]
            except Exception as e:
                print(f"[SSE] Failed to remove queue from session registry: {e}")

            if request.session_id not in active_session_queues:
                try:
                    if 'crew_task' in locals() and not crew_task.done():
                        crew_task.cancel()
                        print("[SSE] Cancelled background crew task successfully since no clients are connected.")
                except Exception as e:
                    print(f"[SSE] Failed to cancel background crew task: {e}")
                if request.session_id in active_session_tasks:
                    del active_session_tasks[request.session_id]

            try:
                from crewai.events import crewai_event_bus
                handlers = crewai_event_bus._sync_handlers.get(LLMStreamChunkEvent, frozenset())
                crewai_event_bus._sync_handlers[LLMStreamChunkEvent] = frozenset(
                    h for h in handlers if h != listener.handler
                )
                print("[SSE] Cleaned up event bus listener successfully.")
            except Exception as e:
                print(f"[SSE] Failed to clean up event bus listener: {e}")

    return StreamingResponse(
        _event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/skills", response_model=None)
async def get_skills() -> list:
    from backend.agent.skill_manager import SkillManager
    return SkillManager().get_skills_list()


@router.get("/complaints/telemetry", response_model=None)
async def get_complaints_telemetry(db: Session = Depends(get_db)):
    from backend.database.models import ComplaintTelemetry
    records = db.query(ComplaintTelemetry).order_by(ComplaintTelemetry.time_reported.desc()).all()
    return [r.to_dict() for r in records]

