"""Minimal Zaki orchestrator: creates Task context, calls FikraCoreAdapter, records runtime state and audit."""
from .adapter import FikraCoreAdapter
from .runtime_state import RuntimeState
from .audit import AuditLog
from pathlib import Path
import time


class ZakiOrchestrator:
    def __init__(self, provider, resolver=None, step_callback=None, storage_dir: str | None = None):
        self.provider = provider
        self.adapter = FikraCoreAdapter(provider, resolver=resolver, step_callback=step_callback)
        self.step_callback = step_callback
        self.storage_dir = Path(storage_dir) if storage_dir else Path(".zaki")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _state_path(self, run_id: str) -> str:
        return str(self.storage_dir / f"runtime_{run_id}.json")

    def _audit_path(self, run_id: str) -> str:
        return str(self.storage_dir / f"audit_{run_id}.jsonl")

    def start_investigation(self, generated_input, operational_root, revision: int = 0):
        """Start an investigation with revision fencing, persistent audit, and streaming callbacks.

        - Saves runtime state to `.zaki/runtime_{run_id}.json`
        - Appends audit records to `.zaki/audit_{run_id}.jsonl`
        - Streams investigator callbacks to `step_callback` if provided
        """
        run_id = generated_input.run_id
        state_path = self._state_path(run_id)
        audit_path = self._audit_path(run_id)

        # Load existing state and enforce revision fencing
        try:
            existing = RuntimeState.load(state_path)
            if revision < existing.revision:
                raise RuntimeError(f"Stale revision {revision} < existing {existing.revision}")
            state = existing
        except FileNotFoundError:
            state = RuntimeState(run_id=run_id)
            state.set_path(state_path)

        # bump revision and persist
        state.revision = max(state.revision, revision) + 1
        state._persist()

        audit = AuditLog(audit_path)
        audit.append({"event": "zaki:start", "run_id": run_id, "ts": time.time(), "revision": state.revision})

        def cb(event_type: str, data: dict):
            # stream to provided callback
            if self.step_callback:
                try:
                    self.step_callback(event_type, data)
                except Exception:
                    pass
            # record minimal audit event
            audit.append({"event": event_type, "ts": time.time(), "data": data})
            state.record_event({"event": event_type, "ts": time.time()})

        result = self.adapter.start_investigation(generated_input, operational_root, step_callback=cb)

        state.terminal_state = result.terminal_state.value
        state.record_event({"terminal": state.terminal_state, "ts": time.time()})
        audit.append({"event": "zaki:complete", "run_id": run_id, "terminal": state.terminal_state, "ts": time.time()})

        # write execution trace into storage_dir for easy retrieval
        try:
            trace_path = self.storage_dir / f"execution_trace_{run_id}.json"
            latest_path = self.storage_dir / "execution_trace_latest.json"
            # model_dump if pydantic model, else fallback to __dict__
            data = result.model_dump(mode="json") if hasattr(result, "model_dump") else getattr(result, "__dict__", {})
            # atomic write
            import json
            tmp = trace_path.with_suffix(trace_path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            tmp.replace(trace_path)

            # also update latest copy
            tmp2 = latest_path.with_suffix(latest_path.suffix + ".tmp")
            with open(tmp2, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            tmp2.replace(latest_path)
        except Exception:
            pass

        return result
