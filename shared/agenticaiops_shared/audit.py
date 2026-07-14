from __future__ import annotations

import json
import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session as SASession

from agenticaiops_shared.database.db import SessionLocal
from agenticaiops_shared.database.models import AuditLog

logger = logging.getLogger(__name__)

SECURITY_EVENT_PATTERNS: dict[str, list[str]] = {
    "auth_failure": ["/api/auth/", "401", "403"],
    "injection_attempt": ["sql", "exec(", "eval(", "drop table"],
    "path_traversal": ["../", "..\\", "/etc/"],
    "rate_limit_exceeded": ["429"],
    "secret_exposure": ["password=", "secret=", "api_key="],
}


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, exclude_paths: set[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or {"/health", "/metrics", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        start = time.perf_counter()

        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8", errors="replace")[:200] if body_bytes else ""

        response = await call_next(request)

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        security_event = self._detect_security_event(request.method, request.url.path, body_str, response.status_code)

        user_id = request.headers.get("X-User-Id", "")
        user_role = request.headers.get("X-User-Role", "")
        session_id = request.headers.get("X-Session-Id", "")

        audit_entry = AuditLog(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=elapsed_ms,
            user_id=user_id or None,
            user_role=user_role or None,
            session_id=session_id or None,
            agent_name=self._resolve_agent(request.url.path),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500] or None,
            request_body_preview=body_str[:200] or None,
            response_size_bytes=int(response.headers.get("content-length", 0)) or None,
            security_event=security_event,
            iso_control="A.8.15",
        )

        try:
            db: SASession = SessionLocal()
            db.add(audit_entry)
            db.commit()
        except Exception as e:
            logger.warning("Audit log write failed: %s", e)
        finally:
            try:
                db.close()
            except Exception:
                pass

        if security_event:
            logger.warning(
                "SECURITY_EVENT=%s method=%s path=%s status=%d ip=%s",
                security_event, request.method, request.url.path, response.status_code,
                request.client.host if request.client else "unknown",
            )

        return response

    def _resolve_agent(self, path: str) -> str | None:
        for prefix, agent in [
            ("/api/qna", "qna"),
            ("/api/complaint", "complaint"),
            ("/api/storyteller", "storyteller"),
            ("/api/rag", "rag"),
            ("/api/jarvis", "jarvis"),
            ("/api/auth", "auth"),
        ]:
            if path.startswith(prefix):
                return agent
        return None

    def _detect_security_event(self, method: str, path: str, body: str, status: int) -> str | None:
        combined = f"{method} {path} {body} {status}"
        if status in (401, 403) and path.startswith("/api/auth"):
            return "auth_failure"
        for event, patterns in SECURITY_EVENT_PATTERNS.items():
            if event == "auth_failure":
                continue
            for pat in patterns:
                if pat.lower() in combined.lower():
                    return event
        return None
