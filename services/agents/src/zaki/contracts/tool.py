"""Tool Contract for Zaki v1 Tool Gateway."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import AuthorityLevel, ToolInterface, ToolType


class ToolMetadata(BaseContract):
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""


class ToolSpec(BaseContract):
    type: ToolType = ToolType.READ
    interface: ToolInterface = ToolInterface.INTERNAL
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    required_authority: AuthorityLevel = AuthorityLevel.LEVEL_0_OBSERVE
    risk_level: str = "LOW"
    rate_limit: int = 100
    timeout_seconds: float = 30.0


class ToolContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "Tool"
    metadata: ToolMetadata
    spec: ToolSpec
