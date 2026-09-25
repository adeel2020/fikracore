"""FikraCore Run Client for Zaki v1."""

from __future__ import annotations

from typing import Any, Dict, Optional
from .adapter import FikraCoreAdapter, default_fikracore_adapter


class FikraCoreRunClient:
    """Convenience client accessing live investigation execution runs."""

    def __init__(self, adapter: Optional[FikraCoreAdapter] = None) -> None:
        self.adapter = adapter or default_fikracore_adapter

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        return self.adapter.get_state(run_id)

    def get_ranked_hypotheses(self, run_id: str):
        return self.adapter.get_ranked_hypotheses(run_id)

    def get_gaps(self, run_id: str):
        return self.adapter.get_knowledge_gaps(run_id)


default_run_client = FikraCoreRunClient()
