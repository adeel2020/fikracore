"""Operator Intent Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import AuthorityLevel, FCAPSCategory, RiskMode


class FCAPSClassification(BaseContract):
    primary: FCAPSCategory = FCAPSCategory.FAULT
    secondary: List[FCAPSCategory] = Field(default_factory=list)
    domain: str = "PS"
    confidence: float = 0.9
    clarification_required: bool = False


class IntentSpec(BaseContract):
    type: str = "INVESTIGATE_SERVICE_DEGRADATION"
    natural_language: str = ""
    subject: Dict[str, Any] = Field(default_factory=dict)
    scope: Dict[str, Any] = Field(default_factory=dict)
    objective: str = "identify probable causal driver"
    constraints: Dict[str, Any] = Field(default_factory=dict)
    requested_authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE
    risk_mode: RiskMode = RiskMode.ANALYZE_ONLY
    requested_by: str = "operator"
    fcaps: FCAPSClassification = Field(default_factory=FCAPSClassification)


class OperatorIntentContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "Intent"
    intent_id: str = Field(default_factory=lambda: f"INT-{int(datetime.now(timezone.utc).timestamp())}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    spec: IntentSpec = Field(default_factory=IntentSpec)
