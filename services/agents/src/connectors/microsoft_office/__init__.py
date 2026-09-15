"""Microsoft Office connector shell."""

from connectors.base import RegistryBackedConnector

CONNECTOR_ID = "microsoft_office"


class MicrosoftOfficeConnector(RegistryBackedConnector):
    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)


__all__ = ["CONNECTOR_ID", "MicrosoftOfficeConnector"]
