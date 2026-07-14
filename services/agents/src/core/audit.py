from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session as SASession
from sqlalchemy import desc

from agenticaiops_shared.database.db import get_db
from agenticaiops_shared.database.models import AuditLog

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs")
async def get_audit_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    security_event: str | None = Query(None),
    agent: str | None = Query(None),
    user_id: str | None = Query(None),
    db: SASession = Depends(get_db),
):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Missing token")

    query = db.query(AuditLog)
    if security_event:
        query = query.filter(AuditLog.security_event == security_event)
    if agent:
        query = query.filter(AuditLog.agent_name == agent)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    total = query.count()
    logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "logs": [log.to_dict() for log in logs],
    }


@router.get("/security-events")
async def get_security_events(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    db: SASession = Depends(get_db),
):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Missing token")

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.security_event.isnot(None))
        .order_by(desc(AuditLog.timestamp))
        .limit(limit)
        .all()
    )
    return {
        "total": len(logs),
        "logs": [log.to_dict() for log in logs],
    }
