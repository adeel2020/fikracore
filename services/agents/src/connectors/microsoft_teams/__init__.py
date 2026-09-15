"""Microsoft Teams connector shell."""

from connectors.base import RegistryBackedConnector

CONNECTOR_ID = "microsoft_teams"


class MicrosoftTeamsConnector(RegistryBackedConnector):
    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)


__all__ = ["CONNECTOR_ID", "MicrosoftTeamsConnector"]
