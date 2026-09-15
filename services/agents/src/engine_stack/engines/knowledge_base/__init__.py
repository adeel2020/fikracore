"""Knowledge Base engine registry shell."""

from engine_stack.engines.base import RegistryBackedEngine

ENGINE_ID = "knowledge_base"


class KnowledgeBaseEngine(RegistryBackedEngine):
    def __init__(self) -> None:
        super().__init__(ENGINE_ID)


__all__ = ["ENGINE_ID", "KnowledgeBaseEngine"]
