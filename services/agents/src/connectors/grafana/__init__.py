"""Grafana connector shell."""

from connectors.base import RegistryBackedConnector

CONNECTOR_ID = "grafana"


class GrafanaConnector(RegistryBackedConnector):
    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)


__all__ = ["CONNECTOR_ID", "GrafanaConnector"]
