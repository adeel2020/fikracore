"""Metadata DB connector shell."""

from connectors.base import RegistryBackedConnector

CONNECTOR_ID = "metadata_db"


class MetadataDbConnector(RegistryBackedConnector):
    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)


__all__ = ["CONNECTOR_ID", "MetadataDbConnector"]
