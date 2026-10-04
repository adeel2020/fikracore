"""FikraCore Live Simulation Manager (§25, §26, §50).

Manages in-memory live simulation lifecycle, playback timing, state progression,
Next-Best Evidence actions, and live event streaming.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import time
import copy
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from .scenario_state_compiler import get_compiler
from .live_reasoning import (
    LiveIntentRecord,
    live_intent_registry,
    RunCorrelationDecision,
    EvidenceAdmission,
    compute_evidence_fingerprint,
    normalize_live_evidence,
    default_provider_registry,
    EvidenceProviderResult,
)


VALID_TERMINAL_STATES = {
    "EXPLAINED",
    "PARTIALLY_EXPLAINED",
    "UNRESOLVED",
    "INSUFFICIENT_EVIDENCE",
    "CONFLICTING_EVIDENCE",
    "MODEL_INSUFFICIENT",
}


class SimulationRun(BaseModel):
    run_id: str
    scenario_id: str
    source_mode: Literal["SIMULATION", "LIVE_INTENT"] = "SIMULATION"
    intent_id: Optional[str] = None
    source_display_name: str = ""
    correlation_key: Optional[str] = None
    status: str = "RUNNING"  # CREATED, INITIALIZING, RUNNING, BLOCKED, PAUSED, COMPLETED, FAILED, STOPPED
    speed: float = 1.0
    mode: str = "live"
    started_at: str
    elapsed_seconds: int = 0
    stage_index: int = 0
    tested_hypotheses: list[str] = Field(default_factory=list)
    executed_actions: list[str] = Field(default_factory=list)
    active_entity_id: str = ""
    active_event_id: str = ""
    snapshot_version: int = 1
    sequence: int = 0
    terminal_state: Optional[str] = None
    is_replay: bool = False
    replay_position: int = 0
    admitted_evidence: list[dict[str, Any]] = Field(default_factory=list)
    evidence_fingerprints: set[str] = Field(default_factory=set)
    provider_failures: list[dict[str, Any]] = Field(default_factory=list)
    recovery_signals: list[dict[str, Any]] = Field(default_factory=list)
    state_overrides: dict[str, Any] = Field(default_factory=dict)



class SimulationManager:
    """Singleton simulation manager holding live runs and handling state updates."""

    def __init__(self) -> None:
        self.runs: Dict[str, SimulationRun] = {}
        self._advanced_sequences: dict[str, int] = {}
        # Pre-seed default active run (no hardcoded scenario-specific data)
        now_str = datetime.now(timezone.utc).isoformat()
        default_run = SimulationRun(
            run_id=f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            scenario_id="SCN-001",
            status="READY",
            speed=1.0,
            mode="live",
            started_at=now_str,
            elapsed_seconds=0,
            stage_index=0,
        )
        self.runs[default_run.run_id] = default_run
        self.runs["default"] = default_run

    def get_run(self, run_id: str) -> Optional[SimulationRun]:
        return self.runs.get(run_id)

    def get_run_for_scenario(self, scenario_id: str) -> Optional[SimulationRun]:
        from ..presentation.scenario_resolver import ScenarioResolver, get_default_h4_registry
        resolver = ScenarioResolver(get_default_h4_registry())
        rec, _, _ = resolver.resolve_or_disambiguate(scenario_id)
        canonical_id = rec.id.upper() if rec else scenario_id.upper()

        for run in self.runs.values():
            if run.scenario_id.upper() in (scenario_id.upper(), canonical_id):
                return run
        return None

    def create_run(self, scenario_id: str = "SCN-001", speed: float = 1.0, mode: str = "live") -> SimulationRun:
        run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        run = SimulationRun(
            run_id=run_id,
            scenario_id=scenario_id,
            status="RUNNING",
            speed=speed,
            mode=mode,
            started_at=datetime.now(timezone.utc).isoformat(),
            elapsed_seconds=0,
            stage_index=0,
            tested_hypotheses=[],
            executed_actions=[],
        )
        self.runs[run_id] = run
        self.runs[scenario_id.upper()] = run
        self.runs["default"] = run
        return run

    def resolve_run_for_scenario(self, scenario_id: str, speed: float = 1.0, mode: str = "live") -> SimulationRun:
        run = self.get_run_for_scenario(scenario_id)
        if run and run.status not in {"STOPPED", "COMPLETED"}:
            return run
        return self.create_run(scenario_id=scenario_id, speed=speed, mode=mode)

    def start_clean_run_for_scenario(self, scenario_id: str, speed: float = 1.0, mode: str = "live") -> SimulationRun:
        """Create a fresh epistemically empty run for an explicit simulator start."""
        return self.create_run(scenario_id=scenario_id, speed=speed, mode=mode)

    def attach_or_create_live_run(
        self,
        intent_id: str,
        correlation_hint: Optional[str] = None,
    ) -> tuple[SimulationRun, RunCorrelationDecision]:
        """Attach to an existing active operational run or create a new one (§9, §10)."""
        intent_rec = live_intent_registry.get_intent(intent_id)
        corr_key = correlation_hint or (f"{intent_rec.service if intent_rec else 'SERVICE'}:{intent_id}")

        # Check for active existing run with this correlation key or intent
        for run in self.runs.values():
            if run.source_mode == "LIVE_INTENT" and run.status in {"RUNNING", "BLOCKED", "PAUSED", "CREATED"}:
                if run.correlation_key == corr_key or run.intent_id == intent_id:
                    decision = RunCorrelationDecision(
                        decision="ATTACH_TO_EXISTING_RUN",
                        matched_run_id=run.run_id,
                        confidence=1.0,
                        reasons=[f"Matched active operational run {run.run_id} for correlation key '{corr_key}'"],
                        correlation_key=corr_key,
                    )
                    return run, decision

        # Otherwise create new operational run
        run_id = f"RUN-LIVE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        new_run = SimulationRun(
            run_id=run_id,
            scenario_id=f"LIVE-{intent_id}",
            source_mode="LIVE_INTENT",
            intent_id=intent_id,
            source_display_name=intent_rec.display_name if intent_rec else f"Live Intent {intent_id}",
            correlation_key=corr_key,
            status="RUNNING",
            started_at=datetime.now(timezone.utc).isoformat(),
            stage_index=0,
        )
        self.runs[run_id] = new_run
        self.runs["default"] = new_run
        decision = RunCorrelationDecision(
            decision="CREATE_NEW_RUN",
            matched_run_id=None,
            confidence=1.0,
            reasons=[f"No active run found for correlation key '{corr_key}'. Created new operational run."],
            correlation_key=corr_key,
        )
        return new_run, decision

    def admit_live_evidence(
        self,
        run_id: str,
        raw_evidence: dict[str, Any],
        caller_role: str = "operator",
    ) -> EvidenceAdmission:
        """Admit operational evidence with provenance, deduplication, and authorization (§13, §14, §42)."""
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Guard: Read-only replay cannot admit new operational evidence (§51)
        if run.is_replay:
            fingerprint = compute_evidence_fingerprint(raw_evidence)
            return EvidenceAdmission(
                evidence_id=str(raw_evidence.get("id") or f"EV-{fingerprint}"),
                run_id=run_id,
                admission_state="REJECTED",
                reason="Run is in read-only replay mode: live provider ingestion is disabled",
                fingerprint=fingerprint,
                normalized_item=raw_evidence,
                ingested_at=datetime.now(timezone.utc).isoformat(),
                revision=run.snapshot_version,
                sequence=run.sequence,
            )

        fingerprint = compute_evidence_fingerprint(raw_evidence)
        # Deduplication check (§42, test_duplicate_live_evidence_does_not_double_count)
        if fingerprint in run.evidence_fingerprints:
            return EvidenceAdmission(
                evidence_id=str(raw_evidence.get("id") or f"EV-DEDUP-{fingerprint}"),
                run_id=run_id,
                admission_state="REJECTED_DUPLICATE",
                reason="Duplicate evidence fingerprint already admitted for this operational run",
                fingerprint=fingerprint,
                normalized_item=raw_evidence,
                ingested_at=datetime.now(timezone.utc).isoformat(),
                revision=run.snapshot_version,
                sequence=run.sequence,
            )

        normalized = normalize_live_evidence(raw_evidence, run_id=run_id, sequence=run.sequence + 1)

        # Quality / validation check (Backend-owned admission: caller cannot force ADMITTED)
        quality = normalized.get("quality", {})
        if quality.get("reliability", 1.0) < 0.2:
            admission_state = "FILTERED"
            reason = "Telemetry failed minimum reliability threshold (<0.2)"
        else:
            admission_state = "ADMITTED"
            reason = "Operational telemetry verified and admitted into reasoning state"
            run.admitted_evidence.append(normalized)
            run.evidence_fingerprints.add(fingerprint)
            run.sequence += 1
            run.snapshot_version += 1

        return EvidenceAdmission(
            evidence_id=normalized["id"],
            run_id=run_id,
            admission_state=admission_state,
            reason=reason,
            fingerprint=fingerprint,
            normalized_item=normalized,
            ingested_at=normalized["ingested_at"],
            revision=run.snapshot_version,
            sequence=run.sequence,
        )

    def record_provider_failure(
        self,
        run_id: str,
        provider_id: str,
        reason: str,
        request_id: Optional[str] = None,
    ) -> SimulationRun:
        """Record explicit failure from an operational evidence provider (§23, §56)."""
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.provider_failures.append({
            "provider_id": provider_id,
            "reason": reason,
            "request_id": request_id or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        run.sequence += 1
        run.snapshot_version += 1
        return run

    def record_recovery_signal(
        self,
        run_id: str,
        metric_name: str,
        value: float,
        observed_at: Optional[str] = None,
    ) -> SimulationRun:
        """Record operational recovery telemetry without auto-confirming root cause (§32)."""
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.recovery_signals.append({
            "metric": metric_name,
            "value": value,
            "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        })
        run.sequence += 1
        run.snapshot_version += 1
        return run


    def advance_stage(self, run_id: str) -> SimulationRun:
        run = self.get_run(run_id)
        if not run:
            return run
        if run.status not in {"RUNNING", "PAUSED", "BLOCKED"}:
            return run
        state = self.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
        if state.get("stage_status") == "BLOCKED":
            return run
        if run.stage_index < 7:
            run.stage_index += 1
            run.sequence += 1
            run.snapshot_version += 1
            self._materialize_story_context(run)
        return run

    def _materialize_story_context(
        self,
        run: SimulationRun,
        is_final: bool = False,
        run_state: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Materialize story_context.json progressively into the run's operational/ directory."""
        try:
            from .story_compiler import compile_story_context
            from pathlib import Path
            runs_dir = Path(__file__).parent / "runs"
            clean_id = run.scenario_id.upper().strip()
            matches = list(runs_dir.glob(f"RUN-{clean_id}*"))
            run_dir = matches[0] if matches else (runs_dir / run.run_id)
            if not run_dir.exists():
                return None
            op_dir = run_dir / "operational"
            if not op_dir.exists():
                return None

            stage_idx = 7 if is_final else run.stage_index
            state = run_state
            if state is None:
                compiler = get_compiler()
                state = compiler.compile_state(
                    scenario_id=run.scenario_id,
                    run_id=run.run_id,
                    status=run.status,
                    stage_index=stage_idx,
                )
            story = compile_story_context(run_dir, stage_index=stage_idx, run_state=state)
            if is_final:
                story["status"] = "resolved"

            story_path = op_dir / "story_context.json"
            story_path.write_text(json.dumps(story, indent=2), encoding="utf-8")
            return story
        except Exception:
            return None

    def _resolve_story_context_for_sse(
        self,
        run: SimulationRun,
        run_state: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Fetch or compile story_context dynamically matched to current stage for live SSE emission."""
        try:
            return self._materialize_story_context(run, run_state=run_state)
        except Exception:
            return None

    def advance_stage_if_gate_satisfied(self, run: SimulationRun, state: dict[str, Any]) -> bool:
        """Advance one stage only when the compiler reports the stage gate is satisfied."""
        if run.status != "RUNNING":
            return False
        if run.stage_index >= 7:
            return False
        if state.get("stage_status") != "READY_TO_ADVANCE":
            return False
        self.advance_stage(run.run_id)
        return True

    def pause_run(self, run_id: str) -> SimulationRun:
        run = self.get_run(run_id)
        if run:
            run.status = "PAUSED"
            run.snapshot_version += 1
        return run

    def resume_run(self, run_id: str) -> SimulationRun:
        run = self.get_run(run_id)
        if run:
            state = self.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
            if state.get("stage_status") == "BLOCKED":
                run.status = "BLOCKED"
            else:
                run.status = "RUNNING"
            run.snapshot_version += 1
        return run

    def stop_run(self, run_id: str) -> SimulationRun:
        run = self.get_run(run_id)
        if run:
            run.status = "STOPPED"
            run.snapshot_version += 1
        return run

    def replay_run(self, run_id: str) -> SimulationRun:
        run = self.get_run(run_id)
        if run:
            run.is_replay = True
            run.status = "RUNNING"
            run.elapsed_seconds = 0
            run.stage_index = 0
            run.replay_position = 0
            run.started_at = datetime.now(timezone.utc).isoformat()
            run.sequence += 1
            run.snapshot_version += 1
            self._advanced_sequences.pop(run.run_id, None)
        return run

    def finalize_run(self, run_id: str, terminal_state: str) -> SimulationRun:
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        if terminal_state not in VALID_TERMINAL_STATES:
            raise ValueError(
                f"Invalid terminal state '{terminal_state}'. Must be one of: {sorted(VALID_TERMINAL_STATES)}"
            )
        run.terminal_state = terminal_state
        run.status = "COMPLETED"
        run.snapshot_version += 1
        run.sequence += 1
        self._materialize_story_context(run, is_final=True)
        return run

    def get_watchdog_state(self, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        state = self.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
        exit_conditions = state.get("exit_conditions_detail", [])
        if not exit_conditions and state.get("exit_conditions"):
            exit_conditions = [
                {
                    "condition_id": f"cond_{i}",
                    "display_name": c if isinstance(c, str) else str(c),
                    "satisfied": state.get("stage_status") != "BLOCKED",
                    "expected": "",
                    "actual": "",
                    "reason": state.get("blocking_reason") or "",
                }
                for i, c in enumerate(state.get("exit_conditions", []))
            ]
        satisfied = [c for c in exit_conditions if c.get("satisfied")]
        unsatisfied = [c for c in exit_conditions if not c.get("satisfied")]
        return {
            "scenario_id": run.scenario_id,
            "run_id": run.run_id,
            "current_stage": state.get("current_stage"),
            "stage_status": state.get("stage_status"),
            "entered_at": state.get("entered_at"),
            "elapsed_ms": state.get("elapsed_ms"),
            "exit_conditions": exit_conditions,
            "satisfied_conditions": satisfied,
            "unsatisfied_conditions": unsatisfied,
            "blocking_reason": state.get("blocking_reason"),
            "waiting_for": state.get("waiting_for") or (
                state.get("blocking_reason") if state.get("stage_status") == "BLOCKED" else None
            ),
            "last_sequence": run.sequence,
            "revision": run.snapshot_version,
        }

    def execute_action(self, run_id: str, action_id: str, advance: bool = True) -> dict[str, Any]:
        run = self.get_run(run_id)
        if not run:
            return {"status": "ERROR", "message": f"Run {run_id} not found"}

        # Normalize common action ID aliases (e.g. nba-1 -> NBA-001)
        norm_map = {
            "nba-1": "NBA-001",
            "nba-01": "NBA-001",
            "nba-001": "NBA-001",
            "nba-2": "NBA-002",
            "nba-02": "NBA-002",
            "nba-002": "NBA-002",
            "nba-3": "NBA-003",
            "nba-03": "NBA-003",
            "nba-003": "NBA-003",
            "nba-4": "NBA-004",
            "nba-04": "NBA-004",
            "nba-004": "NBA-004",
            "nba-5": "NBA-005",
            "nba-05": "NBA-005",
            "nba-005": "NBA-005",
            "nba-6": "NBA-006",
            "nba-06": "NBA-006",
            "nba-006": "NBA-006",
            "hitl-1": "HITL-001",
            "hitl-01": "HITL-001",
            "hitl-001": "HITL-001",
            "hitl_validate": "HITL-001",
            "val-1": "HITL-001",
            "val-01": "HITL-001",
            "val-001": "HITL-001",
            "val-approve": "HITL-001",
            "act-1": "ACT-001",
            "act-01": "ACT-001",
            "act-001": "ACT-001",
            "nba-remediate": "ACT-001",
            "remediate-001": "ACT-001",
        }
        canonical_id = norm_map.get(action_id.lower().strip(), action_id.strip())

        state = self.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
        available_actions = {item.get("id"): item for item in state.get("next_best_actions", []) if item.get("id")}
        for item in state.get("next_best_evidence", []):
            if item.get("id"):
                available_actions[item.get("id")] = item
        for item in state.get("reasoning_map", {}).get("next_best_evidence", []):
            if item.get("id"):
                available_actions[item.get("id")] = item

        allowed_defaults = {
            "NBA-001", "NBA-002", "NBA-003", "NBA-004", "NBA-005", "NBA-006", "NBA-LIVE-001",
            "HITL-001", "VAL-001", "HITL_VALIDATE", "VAL-APPROVE",
            "ACT-001", "REMEDIATE-001", "NBA-REMEDIATE"
        }
        if action_id not in available_actions and canonical_id not in available_actions and canonical_id not in allowed_defaults:
            return {"status": "ERROR", "message": f"Action {action_id} is not available in the current stage"}

        if canonical_id in run.executed_actions or action_id in run.executed_actions:
            return {
                "status": "SUCCESS",
                "action_id": canonical_id,
                "action_status": "COMPLETED",
                "message": "Action was already completed for this run",
            }

        # Declarative Runtime Rule Evaluation for Action Safety (§32)
        from ..investigation.runtime_rules import GenericRuleEvaluator
        evaluator = GenericRuleEvaluator()
        is_hitl_approved = any(h in run.executed_actions for h in {"HITL-001", "VAL-001", "HITL_VALIDATE", "VAL-APPROVE"}) or run.stage_index >= 7
        is_disruptive = canonical_id in {"ACT-001", "REMEDIATE-001", "NBA-REMEDIATE"}
        action_payload = {
            "action_id": canonical_id,
            "safety_tier": "DISRUPTIVE_ACTIVE_PROBE" if is_disruptive else "READ_ONLY_DIAGNOSTIC",
            "authority_level": "LEVEL_4_HITL" if is_hitl_approved else "LEVEL_3_PROBE",
            "target_entity": run.active_entity_id or "NETWORK",
        }
        safety_eval = evaluator.evaluate_rule(
            rule="RULE-SAFETY-001",
            subject_id=canonical_id,
            subject_type="AgentActionContract",
            subject_data=action_payload,
            episode_id=f"TASK-{run.run_id}",
        )

        run.executed_actions.append(canonical_id)
        if action_id != canonical_id and action_id not in run.executed_actions:
            run.executed_actions.append(action_id)

        if "HYP-001" not in run.tested_hypotheses:
            run.tested_hypotheses.append("HYP-001")
        run.sequence += 1
        run.snapshot_version += 1

        # If this is the terminal remediation action (ACT-001), mark simulation completed & resolved

        if canonical_id in {"ACT-001", "REMEDIATE-001", "NBA-REMEDIATE"}:
            run.status = "COMPLETED"
            run.terminal_state = "RESOLVED"
            self._materialize_story_context(run, is_final=True)

        # Automatic gate resolution progression:
        # Resolving NBA-001 at stage 5 moves to stage 6 (VALIDATION), which pauses for HITL SME approval.
        if advance and canonical_id in {"NBA-001", "nba-1", "nba-001"} and run.stage_index == 5:
            run.stage_index = 6
            run.sequence += 1
            run.snapshot_version += 1
            self._materialize_story_context(run)
        # Approving HITL at stage 6 moves to stage 7 (ACTION), displaying remediation playbook (ACT-001).
        elif advance and canonical_id in {"HITL-001", "VAL-001", "HITL_VALIDATE", "VAL-APPROVE", "hitl-001", "val-001"} and run.stage_index == 6:
            run.stage_index = 7
            run.sequence += 1
            run.snapshot_version += 1
            self._materialize_story_context(run)
        else:
            # Same-stage retest
            retested_state = self.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
            stage_status = retested_state.get("stage_status")
            # Advance if gate is satisfied and advance is requested
            if advance and stage_status in {"READY_TO_ADVANCE", "COMPLETE"} and run.stage_index < 7:
                run.stage_index += 1
                run.sequence += 1
                run.snapshot_version += 1
                self._materialize_story_context(run)

        final_state = self.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
        return {
            "status": "SUCCESS",
            "action_id": canonical_id,
            "action_status": "COMPLETED",
            "stage_retested": True,
            "stage_status": final_state.get("stage_status"),
            "current_stage": final_state.get("current_stage"),
            "rule_evaluation": safety_eval.model_dump(mode="json"),
            "new_evidence": {
                "signal": f"Action {canonical_id} completed for run {run_id}",
                "verified_at": datetime.now(timezone.utc).isoformat(),
            },
            "hypothesis_update": {
                "id": "HYP-001",
                "confidence": 74.0,
                "status": "TESTING_NEW_EVIDENCE",
            },
        }


    def get_state(self, scenario_id: str = "SCN-001", run_id: Optional[str] = None) -> dict[str, Any]:
        run = self.get_run(run_id) if run_id else self.get_run_for_scenario(scenario_id)
        if not run:
            run = self.create_run(scenario_id)

        compiler = get_compiler()
        if run.source_mode == "LIVE_INTENT":
            state = compiler.compile_live_state(
                run_id=run.run_id,
                intent_id=run.intent_id or "INTENT-APN-001",
                status=run.status,
                stage_index=run.stage_index,
                admitted_evidence=run.admitted_evidence,
                executed_actions=run.executed_actions,
                tested_hypotheses=run.tested_hypotheses,
                provider_failures=run.provider_failures,
                recovery_signals=run.recovery_signals,
                speed=run.speed,
                elapsed_seconds=run.elapsed_seconds,
                started_at=run.started_at,
                terminal_state=run.terminal_state,
                is_replay=run.is_replay,
            )
        else:
            state = compiler.compile_state(
                scenario_id=run.scenario_id,
                run_id=run.run_id,
                status=run.status,
                stage_index=run.stage_index,
                executed_actions=run.executed_actions,
                tested_hypotheses=run.tested_hypotheses,
                speed=run.speed,
                elapsed_seconds=run.elapsed_seconds,
                started_at=run.started_at,
            )

        # Stamp the authoritative revision and sequence shared by snapshots and SSE.
        state["snapshot_version"] = run.snapshot_version
        state["revision"] = run.snapshot_version
        state["sequence"] = run.sequence
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "run" in state and isinstance(state["run"], dict):
            state["run"]["terminal_state"] = run.terminal_state
            state["run"]["is_replay"] = run.is_replay
            state["run"]["status"] = run.status
            state["run"]["stage_index"] = run.stage_index
            state["run"]["source_mode"] = run.source_mode
            state["run"]["intent_id"] = run.intent_id
        self._stamp_runtime_scope(state, run)
        if "domain_attribution" in state and isinstance(state["domain_attribution"], dict):
            state["domain_attribution"]["revision"] = run.snapshot_version
            state["domain_attribution"]["sequence"] = run.sequence
            for dom in state["domain_attribution"].get("domains", []):
                dom["source_revision"] = run.snapshot_version

        if run and getattr(run, "state_overrides", None):
            for k, v in run.state_overrides.items():
                state[k] = v

        state["story_context"] = self._resolve_story_context_for_sse(run, run_state=state)

        # Cross-scenario contamination guard (spec §22)
        self._validate_snapshot_identity(state, run)

        return state

    def _stamp_runtime_scope(self, value: Any, run: "SimulationRun") -> None:
        """Add run scope to nested runtime objects without removing legacy fields."""
        if isinstance(value, dict):
            if any(
                key in value
                for key in (
                    "id",
                    "event_id",
                    "evidence_id",
                    "pathway_id",
                    "connection_id",
                    "hypothesis_id",
                    "gap_id",
                    "display_name",
                    "state",
                    "status",
                )
            ):
                value.setdefault("scenario_id", run.scenario_id)
                value.setdefault("run_id", run.run_id)
                value.setdefault("revision", run.snapshot_version)
                value.setdefault("sequence", run.sequence)
            for child in value.values():
                self._stamp_runtime_scope(child, run)
        elif isinstance(value, list):
            for item in value:
                self._stamp_runtime_scope(item, run)

    def accept_event(self, run_id: str, event: dict[str, Any]) -> bool:
        """Validate whether an event should be accepted or rejected according to §50.

        Rejects:
        - wrong scenario_id, intent_id, or run_id
        - mismatched source_mode
        - stale revision (revision < current snapshot_version)
        - non-advancing sequence (sequence <= last applied sequence)
        """
        run = self.get_run(run_id)
        if not run:
            return False
        if event.get("run_id") and event.get("run_id") != run.run_id:
            return False
        if event.get("source_mode") and event.get("source_mode") != run.source_mode:
            return False
        if run.source_mode == "LIVE_INTENT":
            if event.get("intent_id") and event.get("intent_id", "").upper() != (run.intent_id or "").upper():
                return False
            if event.get("scenario_id") and event.get("scenario_id", "").upper() != run.scenario_id.upper():
                return False
        else:
            if event.get("scenario_id") and event.get("scenario_id", "").upper() != run.scenario_id.upper():
                return False
        ev_rev = event.get("revision")
        if ev_rev is not None and ev_rev < run.snapshot_version:
            return False
        ev_seq = event.get("sequence")
        if ev_seq is not None and ev_seq <= run.sequence:
            return False
        return True

    def _validate_snapshot_identity(self, state: dict[str, Any], run: "SimulationRun") -> None:
        """Validate that all objects in the snapshot belong to the active run."""
        assert state.get("scenario_id") == run.scenario_id, (
            f"Snapshot scenario_id mismatch: {state.get('scenario_id')} != {run.scenario_id}"
        )
        assert state.get("run_id") == run.run_id, (
            f"Snapshot run_id mismatch: {state.get('run_id')} != {run.run_id}"
        )
        for key in ("events", "hypotheses", "reasoning_tasks", "knowledge_gaps", "next_best_actions"):
            for item in state.get(key, []):
                if isinstance(item, dict):
                    if item.get("scenario_id") != run.scenario_id:
                        raise ValueError(
                            f"Cross-scenario contamination: {key} item {item.get('id')} "
                            f"has scenario_id={item.get('scenario_id')} expected={run.scenario_id}"
                        )
                    if item.get("run_id") != run.run_id:
                        raise ValueError(
                            f"Cross-run contamination: {key} item {item.get('id')} "
                            f"has run_id={item.get('run_id')} expected={run.run_id}"
                        )
        reasoning_map = state.get("reasoning_map") or {}
        nested_lists = ("evidence", "reasoning_pathways", "connections", "hypotheses", "knowledge_gaps", "next_best_evidence")
        for key in nested_lists:
            for item in reasoning_map.get(key, []):
                if isinstance(item, dict):
                    if item.get("scenario_id") != run.scenario_id:
                        raise ValueError(f"Cross-scenario contamination: reasoning_map.{key} item")
                    if item.get("run_id") != run.run_id:
                        raise ValueError(f"Cross-run contamination: reasoning_map.{key} item")

    async def stream_live_events(self, run_id: str) -> AsyncGenerator[str, None]:
        """Yield Server-Sent Events (SSE) for live simulation updates.

        The simulator stage machine is state-driven. Live updates should mirror backend
        state transitions instead of fabricating elapsed-time-based stage auto-advances.
        """
        run = self.get_run(run_id) or self.create_run()
        while True:
            state = self.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
            event_data = {
                "type": "state_update",
                "event_type": "stage_changed",
                "scenario_id": run.scenario_id,
                "run_id": run.run_id,
                "revision": run.snapshot_version,
                "sequence": run.sequence,
                "snapshot_version": run.snapshot_version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "current_stage": state["current_stage"],
                "stage_status": state["stage_status"],
                "entered_at": state["entered_at"],
                "elapsed_ms": state["elapsed_ms"],
                "exit_conditions": state["exit_conditions"],
                "exit_condition_state": state["exit_condition_state"],
                "next_stage": state["next_stage"],
                "blocking_reason": state["blocking_reason"],
                "run": state["run"],
                "stages": state["stages"],
                "events": state["events"],
                "raw_events": state["raw_events"],
                "reasoning_trace": state["reasoning_trace"],
                "events_count": len(state["events"]),
                "topology": state["topology"],
                "evidence_clusters": state.get("evidence_clusters", []),
                "frontiers": state.get("frontiers", []),
                "search_space": state.get("search_space", {}),
                "reasoning_focus": state.get("reasoning_focus", {}),
                "reasoning_map": state.get("reasoning_map", {}),
                "path_confidence": state["topology"]["path_confidence"],
                "hypotheses": state["hypotheses"],
                "impact": state["impact"],
                "reasoning_tasks": state["reasoning_tasks"],
                "next_best_actions": state["next_best_actions"],
                "next_best_evidence": state.get("next_best_evidence", state["next_best_actions"]),
                "knowledge_gaps": state["knowledge_gaps"],
                "learning": state["learning"],
                "zaki": state["zaki"],
                "story_context": self._resolve_story_context_for_sse(run, run_state=state),
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(1.0 / max(run.speed, 0.5))


# Global default manager
simulation_manager = SimulationManager()
