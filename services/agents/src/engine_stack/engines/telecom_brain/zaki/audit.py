"""Append-only audit helper for Zaki runs (in-memory)."""
from typing import List
from pathlib import Path
import json


class AuditLog:
    def __init__(self, path: str | Path | None = None):
        self._events: List[dict] = []
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                # load existing events (jsonl)
                with open(self.path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        try:
                            self._events.append(json.loads(line))
                        except Exception:
                            continue

    def append(self, event: dict):
        self._events.append(event)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, default=str) + "\n")

    def all(self):
        return list(self._events)
