"""Calendar engine registry shell."""

from engine_stack.engines.base import RegistryBackedEngine

ENGINE_ID = "calendar"


class CalendarEngine(RegistryBackedEngine):
    def __init__(self) -> None:
        super().__init__(ENGINE_ID)


__all__ = ["CalendarEngine", "ENGINE_ID"]
