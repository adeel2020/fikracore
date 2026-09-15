from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from agenticaiops_shared.database.db import get_db
from agenticaiops_shared.database.models import ChatSession, ChatMessage, get_dubai_timestamp

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db), limit: int = 50):
    try:
        sessions = db.query(ChatSession).order_by(
            desc(ChatSession.last_accessed)
        ).limit(limit).all()

        result = []
        for s in sessions:
            user_msg = next((m.content for m in sorted(s.messages, key=lambda msg: msg.id) if m.role == "user"), None)
            preview = "No messages"
            if user_msg:
                preview = user_msg[:60] + ("..." if len(user_msg) > 60 else "")

            result.append({
                "session_id": s.session_id,
                "created_at": get_dubai_timestamp(s.created_at),
                "last_accessed": get_dubai_timestamp(s.last_accessed),
                "message_count": len(s.messages),
                "preview": preview,
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()

        if not session:
            return {
                "session_id": session_id,
                "created_at": None,
                "message_count": 0,
                "messages": [],
            }

        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

        from agenticaiops_shared.database.models import SessionTelemetry
        telemetry_records = db.query(SessionTelemetry).filter(
            SessionTelemetry.session_id == session_id
        ).order_by(SessionTelemetry.created_at).all()

        assistant_msgs = [m for m in messages if m.role == "assistant"]
        tel_map = {}

        def map_agent_to_persona(agent_name: str | None) -> str | None:
            if not agent_name:
                return None
            mapping = {
                # route name aliases (for backward compat with old telemetry)
                "qna_workflow": "QnA Assistant",
                "cognitive_workflow": "Cognitive Operation & Customer Center",
                "storyteller_workflow": "Data Storyteller",
                "skill_workflow": "Senior Telecom Signaling Analyst",
                "signaling_workflow": "Senior Telecom Signaling Analyst",
                # agent name aliases (for backward compat with old telemetry)
                "Core Mobile Network Data Analyst": "Cognitive Operation & Customer Center",
                "Conversational Subject Matter Expert": "QnA Assistant",
                "Customer Complaint Analyst": "Mobile Core Analyst",
                "Senior Telecom Signaling Analyst": "Senior Telecom Signaling Analyst",
                "Telecom Signaling Analyst": "Senior Telecom Signaling Analyst",
                "Telecom Signaling Specialist": "Senior Telecom Signaling Analyst",
            }
            return mapping.get(agent_name, agent_name or "Assistant")

        for idx, m in enumerate(assistant_msgs):
            if idx < len(telemetry_records):
                t = telemetry_records[idx]
                tel_map[m.id] = {
                    "tokens_consumed": t.completion_tokens,
                    "tokens_per_second": t.throughput_tps,
                    "latency_ms": t.latency_ms,
                    "persona": map_agent_to_persona(t.agent_name),
                }

        return {
            "session_id": session_id,
            "created_at": get_dubai_timestamp(session.created_at),
            "message_count": len(messages),
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": get_dubai_timestamp(m.created_at),
                    "tokens_consumed": tel_map.get(m.id, {}).get("tokens_consumed"),
                    "tokens_per_second": tel_map.get(m.id, {}).get("tokens_per_second"),
                    "latency_ms": tel_map.get(m.id, {}).get("latency_ms"),
                    "persona": tel_map.get(m.id, {}).get("persona"),
                }
                for m in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()

        if not session:
            return {"message": f"Session {session_id} not found or already deleted"}

        from agenticaiops_shared.database.models import ChatMessage as ChatMessageModel, SessionTelemetry

        db.query(ChatMessageModel).filter(ChatMessageModel.session_id == session_id).delete(synchronize_session=False)
        db.query(SessionTelemetry).filter(SessionTelemetry.session_id == session_id).delete(synchronize_session=False)
        db.delete(session)
        db.commit()

        return {"message": f"Session {session_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
