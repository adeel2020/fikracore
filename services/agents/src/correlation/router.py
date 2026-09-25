"""Discoverable incident registry and lifecycle HTTP API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .registry import IncidentRegistry

router = APIRouter(prefix="/api/incidents", tags=["incident-registry"])
_registry = IncidentRegistry()


class LifecycleRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=20)
    actor: str = Field(default="operator", max_length=100)
    reason: str | None = Field(default=None, max_length=1000)
    owner: str | None = Field(default=None, max_length=100)
    target_incident_ids: list[str] = Field(default_factory=list, max_length=20)


@router.get("")
def list_incidents(
    tenant_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    sync: bool = False,
) -> list[dict]:
    if sync:
        _registry.ensure_seeded()
    return _registry.list(tenant_id=tenant_id, status=status, limit=limit)


@router.get("/{incident_id:path}/audit")
def incident_audit(incident_id: str) -> list[dict]:
    try:
        return _registry.audit(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc


@router.post("/{incident_id:path}/lifecycle")
def lifecycle(incident_id: str, request: LifecycleRequest) -> dict:
    try:
        return _registry.transition(
            incident_id,
            request.action,
            actor=request.actor,
            reason=request.reason,
            owner=request.owner,
            payload={"target_incident_ids": request.target_incident_ids},
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{incident_id:path}")
def get_incident(incident_id: str) -> dict:
    try:
        return _registry.get(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc
