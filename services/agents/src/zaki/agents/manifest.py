"""Agent Manifest model and utilities for Zaki v1."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, Union
from ..contracts.agent import AgentManifestContract


class ManifestLoader:
    """Loads and validates ODA Component-aligned Agent Manifests."""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> AgentManifestContract:
        return AgentManifestContract.model_validate(data)

    @staticmethod
    def from_yaml(content: Union[str, Path]) -> AgentManifestContract:
        if isinstance(content, Path):
            text = content.read_text(encoding="utf-8")
        else:
            text = content
        data = yaml.safe_load(text)
        return AgentManifestContract.model_validate(data)
