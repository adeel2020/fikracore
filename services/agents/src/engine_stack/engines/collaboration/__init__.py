"""Collaboration engine registry shell."""

from engine_stack.engines.base import RegistryBackedEngine

ENGINE_ID = "collaboration"


class CollaborationEngine(RegistryBackedEngine):
    def __init__(self) -> None:
        super().__init__(ENGINE_ID)


__all__ = ["CollaborationEngine", "ENGINE_ID"]
