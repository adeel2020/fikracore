"""Automation engine registry shell."""

from engine_stack.engines.base import RegistryBackedEngine

ENGINE_ID = "automation"


class AutomationEngine(RegistryBackedEngine):
    def __init__(self) -> None:
        super().__init__(ENGINE_ID)


__all__ = ["AutomationEngine", "ENGINE_ID"]
