"""Vector DB connector shell."""

from connectors.base import RegistryBackedConnector

CONNECTOR_ID = "vector_db"


class VectorDbConnector(RegistryBackedConnector):
    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)


__all__ = ["CONNECTOR_ID", "VectorDbConnector"]
