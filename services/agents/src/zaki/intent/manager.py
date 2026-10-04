"""Operator Intent Manager for Zaki v1."""

from __future__ import annotations

from typing import Dict, List, Optional
from .normalizer import IntentNormalizer
from ..contracts.intent import OperatorIntentContract
from ..enums import AuthorityLevel, RiskMode


class IntentManager:
    """Manages operator intents lifecycle and normalization."""

    def __init__(self, normalizer: Optional[IntentNormalizer] = None) -> None:
        self.normalizer = normalizer or IntentNormalizer()
        self._intents: Dict[str, OperatorIntentContract] = {}

    def capture_intent(
        self,
        query: str,
        requested_by: str = "operator",
        authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
        risk_mode: RiskMode = RiskMode.ANALYZE_ONLY,
    ) -> OperatorIntentContract:
        intent = self.normalizer.normalize(
            query=query,
            requested_by=requested_by,
            requested_authority=authority,
            risk_mode=risk_mode,
        )
        self._intents[intent.intent_id] = intent
        return intent

    def get_intent(self, intent_id: str) -> Optional[OperatorIntentContract]:
        return self._intents.get(intent_id)

    def list_intents(self) -> List[OperatorIntentContract]:
        return list(self._intents.values())


default_intent_manager = IntentManager()
