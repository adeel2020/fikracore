"""Codex Engineering engine registry shell."""

from engine_stack.engines.base import RegistryBackedEngine

ENGINE_ID = "codex_engineering"


class CodexEngineeringEngine(RegistryBackedEngine):
    def __init__(self) -> None:
        super().__init__(ENGINE_ID)


__all__ = ["CodexEngineeringEngine", "ENGINE_ID"]
