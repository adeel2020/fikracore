"""FastAPI Capability Router for FikraCore (§57, §68, §69, §89).

Provides unified REST endpoints for CLI, Simulator UI, Zaki Copilot, and external consumers:
- Capabilities metadata & execution
- Scenarios resolution & registry
- Grounded Zaki chat using shared structured state
- Knowledge inventory & audit trail
"""

from __future__ import annotations

from typing import Any, Optional, Dict, List, Literal
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..capabilities import (
    default_capability_registry,
    ExecutionContext,
    RolePermission,
    build_shared_state_from_presentation,
)
from ..investigation.contracts import StandardPresentationModel
from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver
from ..presentation.zaki_bridge import ZakiBridge
from ..services.storytelling import StorytellingService
from ..simulator.simulation_manager import simulation_manager

router = APIRouter(prefix="/api/v1/fikracore", tags=["FikraCore Unified Capabilities"])

_ZAKI_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}


class ExecuteCapabilityRequest(BaseModel):
    caller_id: str = "operator-01"
    caller_role: RolePermission = RolePermission.OPERATOR
    session_id: str = "default-session"
    mode: str = "INVESTIGATION"
    step: int = 1
    input_data: dict[str, Any] = Field(default_factory=dict)


class ZakiChatRequest(BaseModel):
    query: str | None = None
    message: str | None = None
    scenario: str = "SCN-001"
    scenario_id: str | None = None
    workspace: str = "investigate"
    simulation_stage: str | None = None
    response_level: str = "engineer"
    selected_domain: str | None = None
    selected_service: str | None = None
    selected_entity_id: str | None = None
    selected_hypothesis_id: str | None = None
    selected_gap_id: str | None = None
    selected_evidence_id: str | None = None
    selected_pathway_id: str | None = None
    selected_connection_id: str | None = None
    knowledge_source: str | None = None
    mode: str = "INVESTIGATION"  # INVESTIGATION or DEMO
    step: int = 1
    run_id: str | None = None
    revision: int | None = None
    selected_context: dict[str, Any] | None = None


class CreateSimulationRequest(BaseModel):
    scenario_id: str = "SCN-001"
    speed: float = 1.0
    mode: str = "live"


class ResolveScenarioRunRequest(BaseModel):
    speed: float = 1.0
    mode: str = "live"
    fresh: bool = True


class TriggerActionRequest(BaseModel):
    action_id: str


class CreateOperationalRunRequest(BaseModel):
    source_mode: Literal["SIMULATION", "LIVE_INTENT"] = "SIMULATION"
    scenario_id: Optional[str] = "SCN-001"
    intent_id: Optional[str] = None
    speed: float = 1.0


class LiveEvidenceIngestRequest(BaseModel):
    evidence: dict[str, Any]
    caller_role: str = "operator"



WORKSPACE_NAMES = ("investigate", "discover", "learn", "predict", "knowledge", "lab", "benchmarks")


def _derive_capabilities(stage: str, tags: list[str] | None = None) -> dict[str, bool]:
    """Derive workspace availability from existing registry metadata."""
    stage_norm = (stage or "H1").upper()
    tags = tags or []
    is_h2_plus = stage_norm in {"H2", "H3", "H4"}
    is_h3_plus = stage_norm in {"H3", "H4"}
    is_h4 = stage_norm == "H4"
    model_insufficient = "model_insufficient" in tags
    return {
        "investigate": True,
        "discover": is_h2_plus,
        "learn": is_h3_plus and not model_insufficient,
        "predict": is_h4,
        "knowledge": True,
        "lab": True,
        "benchmarks": True,
    }


def _derive_domains(tags: list[str] | None = None) -> list[str]:
    domain_map = {
        "transport": "Transport",
        "mobile_core": "Mobile Core",
        "packet_core": "Packet Core",
        "core": "Core",
        "ran": "RAN",
        "ims": "IMS",
        "bss": "BSS",
        "oss": "OSS",
        "database": "Database",
        "dns": "DNS",
        "security": "Security",
        "signaling": "Signaling",
    }
    return list(dict.fromkeys(domain_map[tag] for tag in (tags or []) if tag in domain_map))


def _derive_services(tags: list[str] | None = None) -> list[str]:
    service_map = {
        "4g": "4G LTE Data",
        "5g": "5G Core",
        "volte": "VoLTE",
        "routing": "IP Routing",
        "charging": "Charging",
        "subscriber": "Subscriber Data",
        "tcp": "TCP Data",
        "mtu": "SGi Transport",
    }
    return list(dict.fromkeys(service_map[tag] for tag in (tags or []) if tag in service_map))


def _derive_difficulty(tags: list[str] | None = None) -> str:
    for tag in tags or []:
        if isinstance(tag, str) and tag.upper().startswith("L") and tag[1:].isdigit():
            return tag.upper()
    return "L3"


def _nested_string(source: Any, *keys: str) -> str | None:
    current = source
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, str) and current.strip() else None


def _resolve_storyteller_incident_id(
    *,
    scenario_id: str,
    selected_context: dict[str, Any] | None,
    model: StandardPresentationModel | None,
    state: dict[str, Any] | None,
) -> str | None:
    """Resolve a public Storyteller incident for Zaki without reading hidden truth."""
    selected_context = selected_context or {}
    metadata = selected_context.get("metadata") if isinstance(selected_context.get("metadata"), dict) else {}
    explicit = (
        selected_context.get("incident_id")
        or selected_context.get("storyteller_incident_id")
        or metadata.get("incident_id")
        or metadata.get("storyteller_incident_id")
        or _nested_string(state, "storyteller", "incident_id")
        or _nested_string(state, "scenario", "incident_id")
        or _nested_string(state, "scenario", "storyteller_incident_id")
        or _nested_string(model.scenario if model else None, "incident_id")
        or _nested_string(model.scenario if model else None, "storyteller_incident_id")
    )
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    searchable = " ".join(
        str(value)
        for value in [
            scenario_id,
            _nested_string(state, "scenario", "id"),
            _nested_string(state, "scenario", "display_name"),
            _nested_string(state, "scenario", "title"),
            _nested_string(model.scenario if model else None, "id"),
            _nested_string(model.scenario if model else None, "display_name"),
            _nested_string(model.scenario if model else None, "title"),
        ]
        if value
    ).lower()
    if any(token in searchable for token in ("sgi", "throughput", "packet discard", "nat", "pgw")):
        return "incidents/mobile-core/sgi-throughput-drop"
    if any(token in searchable for token in ("attach", "s1-mme", "lte")):
        return "incidents/mobile-core/lte-attach-54db6ef325fbf758"
    if any(token in searchable for token in ("amf", "registration", "ue-registration")):
        return "mobile-core/incidents/amf-overload-2026-08-09"
    return None


def _build_zaki_storyteller_payload(
    *,
    scenario_id: str,
    selected_context: dict[str, Any] | None,
    model: StandardPresentationModel | None,
    state: dict[str, Any] | None,
    query: str,
    session_id: str | None,
) -> dict[str, Any] | None:
    incident_id = _resolve_storyteller_incident_id(
        scenario_id=scenario_id,
        selected_context=selected_context,
        model=model,
        state=state,
    )
    if not incident_id:
        return None
    try:
        return StorytellingService().build_payload(
            incident_id,
            message=query or f"Create an executive summary for {incident_id}.",
            session_id=session_id,
            intent="executive",
        )
    except Exception:
        return None


def _scenario_contract(record: Any) -> dict[str, Any]:
    base = record.model_dump(mode="json")
    tags = base.get("tags") or []
    stage = base.get("stage", "H1")
    from ..simulator.scenario_catalog import concept_for_stage
    concept = base.get("concept") or concept_for_stage(stage)
    base.update({
        "stage": stage,
        "concept": concept,
        "scenario_type": base.get("scenario_type", "INCIDENT"),
        "capabilities": _derive_capabilities(stage, tags),
        "domains": base.get("domains") or _derive_domains(tags),
        "services": base.get("services") or _derive_services(tags),
        "difficulty": base.get("difficulty") or _derive_difficulty(tags),
        "status": "READY" if base.get("demo_enabled", True) else "AVAILABLE",
        "source": base.get("source", "scenario-catalog"),
    })
    return base


@router.get("/capabilities")
def list_capabilities() -> dict[str, Any]:
    """List all registered capabilities and their operational metadata."""
    caps = []
    for c in default_capability_registry.list_all():
        caps.append({
            "name": c.name,
            "description": c.description,
            "permissions": [p.value for p in c.permissions],
            "supports_cli": c.supports_cli,
            "supports_ui": c.supports_ui,
            "supports_zaki": c.supports_zaki,
            "supports_demo": c.supports_demo,
            "supports_api": c.supports_api,
            "read_only": c.read_only,
        })
    return {"status": "SUCCESS", "total_capabilities": len(caps), "capabilities": caps}


@router.post("/capabilities/{capability_name}/execute")
def execute_capability(capability_name: str, req: ExecuteCapabilityRequest) -> dict[str, Any]:
    """Execute a capability through the unified capability registry."""
    ctx = ExecutionContext(
        caller_id=req.caller_id,
        caller_role=req.caller_role,
        session_id=req.session_id,
        mode=req.mode,
        current_step=req.step,
    )
    result = default_capability_registry.execute(capability_name, req.input_data, ctx)
    if not result.success:
        if result.error_code == "PERMISSION_DENIED":
            raise HTTPException(status_code=403, detail=result.errors)
        elif result.error_code in ("CAPABILITY_NOT_FOUND", "SCENARIO_NOT_FOUND", "UNIT_NOT_FOUND"):
            raise HTTPException(status_code=404, detail=result.errors)
        else:
            raise HTTPException(status_code=400, detail=result.errors)
    return result.model_dump(mode="json")


@router.get("/scenarios")
def list_scenarios(
    stage: Optional[str] = Query(None, description="Filter by stage: H1, H2, H3, H4"),
    concept: Optional[str] = Query(None, description="Filter by concept: Understand, Discover, Learn, Anticipate"),
) -> dict[str, Any]:
    """List all registered simulator scenarios across stages and conceptual capabilities."""
    from ..simulator.scenario_catalog import scenario_catalog

    if concept:
        records = scenario_catalog.filter_by_concept(concept)
    elif stage:
        records = scenario_catalog.filter_by_stage(stage)
    else:
        records = scenario_catalog.all()

    scenarios = []
    for r in records:
        scenarios.append({
            "id": r.id,
            "display_name": r.display_name,
            "stage": r.stage,
            "concept": r.concept,
            "scenario_type": r.scenario_type,
            "description": r.description,
            "aliases": r.aliases,
            "tags": r.tags,
            "domains": r.domains or _derive_domains(r.tags),
            "services": r.services or _derive_services(r.tags),
            "difficulty": r.difficulty or _derive_difficulty(r.tags),
            "status": r.status,
            "source": r.source,
            "demo_enabled": r.demo_enabled,
            "capabilities": _derive_capabilities(r.stage, r.tags),
        })
    return {"status": "SUCCESS", "total_scenarios": len(scenarios), "scenarios": scenarios}


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    """Resolve and return specific scenario details."""
    resolver = ScenarioResolver(get_default_h4_registry())
    rec, candidates, err = resolver.resolve_or_disambiguate(scenario_id)
    if not rec:
        if candidates:
            raise HTTPException(status_code=300, detail={"message": err, "candidates": [c.model_dump(mode="json") for c in candidates]})
        raise HTTPException(status_code=404, detail=err or f"Scenario '{scenario_id}' not found.")
    return {"status": "SUCCESS", "scenario": _scenario_contract(rec)}


@router.get("/scenarios/{scenario_id}/capabilities")
def get_scenario_capabilities(scenario_id: str) -> dict[str, Any]:
    """Return workspace availability for a scenario."""
    resolver = ScenarioResolver(get_default_h4_registry())
    rec, candidates, err = resolver.resolve_or_disambiguate(scenario_id)
    if not rec:
        if candidates:
            raise HTTPException(status_code=300, detail={"message": err, "candidates": [_scenario_contract(c) for c in candidates]})
        raise HTTPException(status_code=404, detail=err or f"Scenario '{scenario_id}' not found.")
    contract = _scenario_contract(rec)
    return {
        "status": "SUCCESS",
        "scenario_id": rec.id,
        "capabilities": contract["capabilities"],
        "available_workspaces": [name for name, enabled in contract["capabilities"].items() if enabled],
    }


class ScenarioYamlUpdateRequest(BaseModel):
    content: str


@router.get("/scenarios/{scenario_id}/yaml")
def get_scenario_yaml_endpoint(scenario_id: str) -> dict[str, Any]:
    """Retrieve raw YAML definition and source path for a scenario."""
    from ..simulator.scenario_catalog import scenario_catalog
    try:
        content, filename, is_read_only = scenario_catalog.get_yaml(scenario_id)
        return {
            "status": "SUCCESS",
            "scenario_id": scenario_id,
            "filename": filename,
            "content": content,
            "read_only": is_read_only,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/scenarios/{scenario_id}/yaml")
def update_scenario_yaml_endpoint(scenario_id: str, request: ScenarioYamlUpdateRequest) -> dict[str, Any]:
    """Validate and persist updated YAML definition for a scenario."""
    from ..simulator.scenario_catalog import scenario_catalog
    ok, msg = scenario_catalog.save_yaml(scenario_id, request.content)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "status": "SUCCESS",
        "scenario_id": scenario_id,
        "message": msg,
    }


@router.get("/scenarios/{scenario_id}/topology")
def get_scenario_topology(scenario_id: str) -> dict[str, Any]:
    """Retrieve structured 6-domain topology for the scenario."""
    state = simulation_manager.get_state(scenario_id)
    return {"status": "SUCCESS", "scenario_id": scenario_id, "topology": state["topology"]}


@router.get("/scenarios/{scenario_id}/state")
def get_scenario_state(scenario_id: str) -> dict[str, Any]:
    """Retrieve full structured simulation state for the scenario."""
    return simulation_manager.get_state(scenario_id)


@router.post("/scenarios/{scenario_id}/run")
def resolve_scenario_run(scenario_id: str, req: ResolveScenarioRunRequest) -> dict[str, Any]:
    """Start a clean run for the selected scenario, or resolve the active run when requested."""
    resolver = ScenarioResolver(get_default_h4_registry())
    rec, candidates, err = resolver.resolve_or_disambiguate(scenario_id)
    if not rec:
        if candidates:
            raise HTTPException(status_code=300, detail={"message": err, "candidates": [_scenario_contract(c) for c in candidates]})
        raise HTTPException(status_code=404, detail=err or f"Scenario '{scenario_id}' not found.")
    if req.fresh:
        run = simulation_manager.start_clean_run_for_scenario(rec.id, speed=req.speed, mode=req.mode)
    else:
        run = simulation_manager.resolve_run_for_scenario(rec.id, speed=req.speed, mode=req.mode)
    return {
        "status": "SUCCESS",
        "scenario_id": run.scenario_id,
        "run_id": run.run_id,
        "simulation_status": run.status,
        "speed": run.speed,
        "started_at": run.started_at,
    }


@router.post("/simulations")
def start_simulation(req: CreateSimulationRequest) -> dict[str, Any]:
    """Start or initialize a simulation run."""
    run = simulation_manager.create_run(scenario_id=req.scenario_id, speed=req.speed, mode=req.mode)
    return {
        "status": "SUCCESS",
        "run_id": run.run_id,
        "scenario_id": run.scenario_id,
        "simulation_status": run.status,
        "speed": run.speed,
        "started_at": run.started_at,
    }


@router.get("/simulations/{run_id}")
def get_simulation(run_id: str) -> dict[str, Any]:
    """Get active simulation run details and state."""
    run = simulation_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation run '{run_id}' not found.")
    return simulation_manager.get_state(scenario_id=run.scenario_id, run_id=run_id)


@router.get("/simulations/{run_id}/state")
def get_simulation_state(run_id: str) -> dict[str, Any]:
    """Get authoritative run-bound simulation snapshot."""
    run = simulation_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation run '{run_id}' not found.")
    return simulation_manager.get_state(scenario_id=run.scenario_id, run_id=run_id)


@router.get("/runs/{run_id}/snapshot")
def get_run_snapshot(run_id: str) -> dict[str, Any]:
    """Canonical authoritative run-bound snapshot for Step 5 & 5.2."""
    return get_simulation_state(run_id)


@router.get("/runs/{run_id}/events")
def get_run_events(run_id: str) -> dict[str, Any]:
    """Get events for unified operational run."""
    state = simulation_manager.get_state(run_id=run_id)
    return {"status": "SUCCESS", "run_id": run_id, "events": state["events"]}


@router.get("/live/intents")
def list_live_intents() -> dict[str, Any]:
    """Retrieve backend-configured live intents (§8, §48)."""
    from ..simulator.live_reasoning import live_intent_registry
    intents = [item.model_dump() for item in live_intent_registry.list_intents()]
    return {"status": "SUCCESS", "total_intents": len(intents), "intents": intents}


@router.post("/live/intents/{intent_id}/activate")
def activate_live_intent(intent_id: str, req: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Activate or attach to an operational run from a live intent violation (§9, §10)."""
    correlation_hint = (req or {}).get("correlation_hint") if req else None
    run, decision = simulation_manager.attach_or_create_live_run(intent_id, correlation_hint=correlation_hint)
    return {
        "status": "SUCCESS",
        "decision": decision.decision,
        "run_id": run.run_id,
        "matched_run_id": decision.matched_run_id,
        "confidence": decision.confidence,
        "reasons": decision.reasons,
        "source_mode": run.source_mode,
        "intent_id": run.intent_id,
        "run_status": run.status,
        "revision": run.snapshot_version,
        "sequence": run.sequence,
    }


@router.post("/runs")
def create_operational_run(req: CreateOperationalRunRequest) -> dict[str, Any]:
    """Unified operational run creation endpoint (§37, §38, §39)."""
    if req.source_mode == "LIVE_INTENT":
        intent_id = req.intent_id or "INTENT-APN-001"
        run, decision = simulation_manager.attach_or_create_live_run(intent_id)
    else:
        scenario_id = req.scenario_id or "SCN-001"
        run = simulation_manager.create_run(scenario_id=scenario_id, speed=req.speed)
    return {
        "status": "SUCCESS",
        "run_id": run.run_id,
        "source_mode": run.source_mode,
        "scenario_id": run.scenario_id,
        "intent_id": run.intent_id,
        "run_status": run.status,
        "revision": run.snapshot_version,
        "sequence": run.sequence,
    }


@router.post("/runs/{run_id}/evidence")
def ingest_run_evidence(run_id: str, req: LiveEvidenceIngestRequest) -> dict[str, Any]:
    """Admit operational evidence into run with provenance, deduplication, and authorization (§13, §42)."""
    admission = simulation_manager.admit_live_evidence(
        run_id=run_id,
        raw_evidence=req.evidence,
        caller_role=req.caller_role,
    )
    return {
        "status": "SUCCESS",
        "run_id": run_id,
        "admission": admission.model_dump(),
    }



@router.post("/simulations/{run_id}/pause")
def pause_simulation(run_id: str) -> dict[str, Any]:
    """Pause an active simulation."""
    run = simulation_manager.pause_run(run_id)
    return {"status": "SUCCESS", "run_id": run_id, "simulation_status": run.status}


@router.post("/simulations/{run_id}/resume")
def resume_simulation(run_id: str) -> dict[str, Any]:
    """Resume a paused simulation."""
    run = simulation_manager.resume_run(run_id)
    return {"status": "SUCCESS", "run_id": run_id, "simulation_status": run.status}


@router.post("/simulations/{run_id}/advance")
def advance_simulation_stage(run_id: str) -> dict[str, Any]:
    """Advance the active simulation to the next stage."""
    run = simulation_manager.advance_stage(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Simulation run '{run_id}' not found.")
    return {"status": "SUCCESS", "run_id": run_id, "simulation_status": run.status, "stage_index": run.stage_index}


@router.post("/simulations/{run_id}/stop")
def stop_simulation(run_id: str) -> dict[str, Any]:
    """Stop/end a simulation run."""
    run = simulation_manager.stop_run(run_id)
    return {"status": "SUCCESS", "run_id": run_id, "simulation_status": run.status}


@router.post("/simulations/{run_id}/replay")
def replay_simulation(run_id: str) -> dict[str, Any]:
    """Replay simulation from time zero."""
    run = simulation_manager.replay_run(run_id)
    return {"status": "SUCCESS", "run_id": run_id, "simulation_status": run.status}


@router.get("/simulations/{run_id}/events")
def get_simulation_events(run_id: str) -> dict[str, Any]:
    """Get unified live event stream."""
    state = simulation_manager.get_state(run_id=run_id)
    return {"status": "SUCCESS", "run_id": run_id, "events": state["events"]}


@router.get("/simulations/{run_id}/hypotheses")
def get_simulation_hypotheses(run_id: str) -> dict[str, Any]:
    """Get ranked hypotheses with supports/against/missing evidence."""
    state = simulation_manager.get_state(run_id=run_id)
    return {"status": "SUCCESS", "run_id": run_id, "hypotheses": state["hypotheses"]}


@router.get("/simulations/{run_id}/impact")
def get_simulation_impact(run_id: str) -> dict[str, Any]:
    """Get service impact and blast radius."""
    state = simulation_manager.get_state(run_id=run_id)
    return {"status": "SUCCESS", "run_id": run_id, "impact": state["impact"]}


@router.get("/simulations/{run_id}/knowledge-gaps")
def get_simulation_knowledge_gaps(run_id: str) -> dict[str, Any]:
    """Get identified knowledge gaps."""
    state = simulation_manager.get_state(run_id=run_id)
    return {"status": "SUCCESS", "run_id": run_id, "knowledge_gaps": state["knowledge_gaps"]}


@router.get("/simulations/{run_id}/next-best-evidence")
def get_simulation_next_best_evidence(run_id: str) -> dict[str, Any]:
    """Get next-best-evidence actions."""
    state = simulation_manager.get_state(run_id=run_id)
    return {"status": "SUCCESS", "run_id": run_id, "next_best_actions": state["next_best_actions"]}


@router.get("/simulations/{run_id}/trace")
def get_simulation_trace(
    run_id: str,
    level: str = "verbose",
    stage: str | None = None,
    component: str | None = None,
    entity: str | None = None,
    hypothesis: str | None = None,
    type: str | None = None,
) -> dict[str, Any]:
    """Return the reasoning trace with stage/component/entity/hypothesis filters."""
    state = simulation_manager.get_state(run_id=run_id)
    records = [dict(r) for r in state.get("reasoning_trace", [])]
    if stage:
        records = [r for r in records if r.get("stage", "").upper() == stage.upper()]
    if component:
        records = [r for r in records if r.get("component", "").lower() == component.lower()]
    if entity:
        records = [r for r in records if entity in r.get("entity_ids", [])]
    if hypothesis:
        records = [r for r in records if r.get("hypothesis_id") == hypothesis]
    if type:
        records = [r for r in records if r.get("event_type", "").lower() == type.lower()]
    if level == "summary":
        records = [r for r in records if r.get("event_type") in {"stage_transition", "knowledge_gap_detected", "learning_candidate_created", "recommendation_generated"}]
    return {"status": "SUCCESS", "run_id": run_id, "level": level, "records": records}


@router.get("/simulations/{run_id}/live")
async def stream_live_simulation(run_id: str):
    """Server-Sent Events (SSE) live stream of simulation updates."""
    return StreamingResponse(
        simulation_manager.stream_live_events(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/simulations/{run_id}/actions")
def execute_simulation_action(run_id: str, req: TriggerActionRequest) -> dict[str, Any]:
    """Trigger a next-best-evidence intelligence action."""
    return simulation_manager.execute_action(run_id, req.action_id)


@router.post("/investigate")
def investigate(req: ExecuteCapabilityRequest) -> dict[str, Any]:
    """Shortcut endpoint executing investigate capability."""
    return execute_capability("investigate", req)


@router.post("/discover")
def discover(req: ExecuteCapabilityRequest) -> dict[str, Any]:
    """Shortcut endpoint executing discover capability."""
    return execute_capability("discover", req)


@router.post("/learn")
def learn(req: ExecuteCapabilityRequest) -> dict[str, Any]:
    """Shortcut endpoint executing learn capability."""
    return execute_capability("learn", req)


@router.post("/predict")
def predict(req: ExecuteCapabilityRequest) -> dict[str, Any]:
    """Shortcut endpoint executing predict capability."""
    return execute_capability("predict", req)


@router.get("/knowledge/inventory")
def get_knowledge_inventory() -> dict[str, Any]:
    """Retrieve live telecombrain knowledge inventory."""
    ctx = ExecutionContext(caller_role=RolePermission.OPERATOR)
    result = default_capability_registry.execute("inspect", {"target": "knowledge"}, ctx)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.errors)
    return result.model_dump(mode="json")


@router.post("/zaki/chat")
def zaki_chat(req: ZakiChatRequest) -> dict[str, Any]:
    """Chat with Mark / Zaki copilot grounded in shared state."""
    query_text = req.query or req.message or ""
    scenario_id = req.scenario_id or req.scenario
    ctx = ExecutionContext(mode=req.mode, current_step=req.step)
    state: dict[str, Any] | None = None
    run = None
    if req.run_id:
        run = simulation_manager.get_run(req.run_id)
        if run:
            scenario_id = run.scenario_id
            if req.revision is not None:
                if req.revision < run.snapshot_version:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Stale revision (STALE_REVISION): requested {req.revision} < current {run.snapshot_version}",
                    )
                if req.revision > run.snapshot_version:
                    raise HTTPException(
                        status_code=409,
                        detail=f"INVALID_REVISION: requested {req.revision} > current {run.snapshot_version}",
                    )
        state = simulation_manager.get_state(scenario_id=scenario_id, run_id=req.run_id)
        scenario_id = state.get("scenario_id", scenario_id)

    # Context extraction from selected_context if present
    selected_context = req.selected_context or {}
    c_type = str(selected_context.get("type") or selected_context.get("context_type") or "").lower()
    c_id = selected_context.get("id") or selected_context.get("context_id")

    sel_hyp_id = req.selected_hypothesis_id or selected_context.get("hypothesis_id") or (c_id if c_type == "hypothesis" else None)
    sel_stage = req.simulation_stage or selected_context.get("stage") or (c_id if c_type == "stage" else None)
    sel_gap_id = req.selected_gap_id or selected_context.get("gap_id") or (c_id if c_type in {"gap", "knowledge_gap"} else None)
    sel_ev_id = req.selected_evidence_id or selected_context.get("evidence_id") or (c_id if c_type == "evidence" else None)
    sel_pw_id = req.selected_pathway_id or selected_context.get("pathway_id") or (c_id if c_type == "pathway" else None)
    sel_conn_id = req.selected_connection_id or selected_context.get("connection_id") or (c_id if c_type == "connection" else None)
    sel_dom_id = req.selected_domain or selected_context.get("domain_id") or (c_id if c_type in {"domain", "domain_attribution"} else None)

    # Explanation caching key (§35)
    cache_rev = run.snapshot_version if run else (req.revision or 1)
    cache_key = (
        req.run_id or scenario_id,
        cache_rev,
        req.workspace or "investigate",
        c_type,
        str(c_id or ""),
        req.selected_entity_id or "",
        (req.response_level or "engineer").lower(),
        query_text.strip().lower(),
    )
    if cache_key in _ZAKI_CACHE:
        return _ZAKI_CACHE[cache_key]

    # Generate presentation model only when no authoritative run snapshot is selected.
    pres_res = None if state else default_capability_registry.execute("present", {"scenario": scenario_id, "mode": req.mode, "step": req.step}, ctx)
    if pres_res and pres_res.success:
        model = StandardPresentationModel.model_validate(pres_res.data)
    else:
        state = state or simulation_manager.get_state(scenario_id=scenario_id, run_id=req.run_id)
        visible_entities = []
        for domain in state.get("topology", {}).get("domains", []):
            for entity in domain.get("entities", []):
                visible_entities.append({
                    "canonical_id": entity.get("id"),
                    "display_name": entity.get("display_name"),
                    "domain": domain.get("name"),
                    "state": entity.get("state"),
                })
        gap_boundary = visible_entities[0] if visible_entities else {}
        model = StandardPresentationModel(
            scenario=state.get("scenario", {"id": scenario_id}),
            impact=state.get("impact", {}),
            timeline=state.get("events", []),
            topology={
                "visible_entities": visible_entities,
                "visible_relationships": state.get("topology", {}).get("causal_path", []),
                "highlighted_path": [
                    edge.get("from")
                    for edge in state.get("topology", {}).get("causal_path", [])
                    if edge.get("from")
                ],
                "gap_boundary": gap_boundary,
            },
            reasoning={
                "hypotheses": state.get("hypotheses", []),
                "terminal_state": "MODEL_INSUFFICIENT" if state.get("knowledge_gaps") else "PARTIALLY_EXPLAINED",
                "knowledge_gaps": state.get("knowledge_gaps", []),
                "unexplained_residual": state.get("knowledge_gaps", []),
            },
            next_best_evidence=state.get("next_best_actions", []),
            candidate_knowledge=[],
            validation={"state": "PENDING"},
            presentation={"active_mode": req.mode, "current_step": req.step},
            learning=state.get("learning"),
            resilience={},
        )
    shared_state = build_shared_state_from_presentation(model, capability_name="present")

    bridge = ZakiBridge()
    zaki_context = bridge.build_context(model, mode=req.mode, step=req.step)
    ui_context = {
        "workspace": req.workspace,
        "run_id": req.run_id,
        "simulation_stage": sel_stage,
        "response_level": req.response_level,
        "selected_domain": sel_dom_id,
        "selected_service": req.selected_service,
        "selected_entity_id": req.selected_entity_id,
        "selected_hypothesis_id": sel_hyp_id,
        "selected_gap_id": sel_gap_id,
        "selected_evidence_id": sel_ev_id,
        "selected_pathway_id": sel_pw_id,
        "selected_connection_id": sel_conn_id,
        "selected_context": selected_context,
        "knowledge_source": req.knowledge_source,
        "revision": run.snapshot_version if run else (req.revision or 1),
        "is_replay": getattr(run, "is_replay", False) if run else False,
        "replay_position": getattr(run, "replay_position", 0) if run else 0,
        "simulation_state": state,
    }
    answer = bridge.answer_query(query_text, zaki_context, ui_context=ui_context)

    raw_answer_str = answer.get("response", "") if isinstance(answer, dict) else str(answer)
    grounded_in = answer.get("grounded_in", {}) if isinstance(answer, dict) else {}
    uncertainty = answer.get("uncertainty", []) if isinstance(answer, dict) else []
    suggested_actions = answer.get("suggested_actions", []) if isinstance(answer, dict) else []
    selected_context_v2 = selected_context if isinstance(selected_context, dict) else {}
    copilot_state = "REPLAY" if ui_context.get("is_replay") else (
        "NEEDS_EVIDENCE" if state and (state.get("waiting_for") or state.get("blocking_reason") or state.get("stage_status") == "BLOCKED")
        else "VALIDATION_REQUIRED" if model.validation.get("state") == "PENDING"
        else "RECOMMENDATION_READY" if str(sel_stage or model.scenario.get("stage") or "").upper() == "ACTION"
        else "REASONING" if req.run_id or state
        else "IDLE"
    )
    sections_v2 = answer.get("sections") if isinstance(answer, dict) and answer.get("sections") else [
        {"title": "What Happened", "content": raw_answer_str},
        {
            "title": "What Happens Next",
            "content": suggested_actions[0].get("display_name", "Continue with the next governed action from the active workspace.") if suggested_actions else "Continue with the next governed action from the active workspace.",
        },
    ]
    entities_v2 = answer.get("entities") if isinstance(answer, dict) and answer.get("entities") else (
        [
            {
                "id": selected_context_v2.get("context_id") or selected_context_v2.get("id"),
                "display_name": selected_context_v2.get("display_name", "Selected context"),
                "entity_type": selected_context_v2.get("context_type") or selected_context_v2.get("type", "ENTITY"),
                "visual_role": "FOCUS",
            }
        ] if selected_context_v2 else []
    )
    storyteller_payload = _build_zaki_storyteller_payload(
        scenario_id=scenario_id,
        selected_context=selected_context_v2 or selected_context,
        model=model,
        state=state,
        query=query_text,
        session_id=req.run_id,
    )
    zaki_v2 = {
        "answer": raw_answer_str,
        "run_id": req.run_id,
        "revision": run.snapshot_version if run else (req.revision or 1),
        "source_mode": getattr(run, "source_mode", "SIMULATION") if run else "SIMULATION",
        "copilot_state": copilot_state,
        "response_level": (req.response_level or "engineer").upper(),
        "selected_context": selected_context_v2 or None,
        "sections": sections_v2,
        "entities": entities_v2,
        "grounded_in": grounded_in,
        "uncertainty": uncertainty,
        "suggested_actions": suggested_actions,
        "storyteller": storyteller_payload,
    }

    ret_payload = {
        "status": "SUCCESS",
        "scenario_id": scenario_id,
        "run_id": req.run_id,
        "source_mode": getattr(run, "source_mode", "SIMULATION") if run else "SIMULATION",
        "intent_id": getattr(run, "intent_id", None) if run else None,
        "revision": run.snapshot_version if run else (req.revision or 1),
        "workspace": req.workspace,
        "response_level": (req.response_level or "engineer").lower(),
        "mode": req.mode,
        "step": req.step,
        "query": query_text,
        "answer": raw_answer_str,
        "response": answer,
        "grounded_in": grounded_in,
        "uncertainty": uncertainty,
        "suggested_actions": suggested_actions,
        "entities": answer.get("entities", []) if isinstance(answer, dict) else [],
        "zaki_v2": zaki_v2,
        "shared_state": shared_state.model_dump(mode="json"),
    }
    _ZAKI_CACHE[cache_key] = ret_payload
    return ret_payload


@router.get("/audit")
def get_audit_trail() -> dict[str, Any]:
    """Retrieve audit log of capability executions."""
    return {"status": "SUCCESS", "audit_trail": default_capability_registry.get_audit_trail()}
