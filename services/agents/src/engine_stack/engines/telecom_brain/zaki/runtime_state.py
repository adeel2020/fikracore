"""Simple in-memory runtime state for a Zaki orchestrated run."""
from dataclasses import dataclass, field, asdict
from typing import List
from pathlib import Path
import json


@dataclass
class RuntimeState:
    run_id: str
    revision: int = 0
    sequence: int = 0
    terminal_state: str | None = None
    audit: List[dict] = field(default_factory=list)
    _path: str | None = None

    def record_event(self, event: dict):
        self.audit.append(event)
        self.sequence += 1
        self._persist()

    def _persist(self):
        if not self._path:
            return
        p = Path(self._path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, default=str, indent=2)
        tmp.replace(p)

    @classmethod
    def load(cls, path: str):
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        inst = cls(**{k: v for k, v in data.items() if k != "_path"})
        inst._path = path
        return inst

    def set_path(self, path: str):
        self._path = path
        self._persist()
