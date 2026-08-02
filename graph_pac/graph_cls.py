"""Graph representation of a parsed map: hubs and their connections."""
from parser import MapModel, HubModel


class Graph:
    """Build a graph from previously parsed graph."""

    def __init__(self, _map: MapModel) -> None:
        """Initialize the graph with hubs and connections."""
        self.start_hub = _map.start_hub
        self.end_hub = _map.end_hub
        self.hubs = _map.hubs
        self.connections: dict[str, list[str]] = {}
        self.connection_capacities: dict[tuple[str, str], int] = {}
        self.build_connections(_map)

    def build_connections(self, _map: MapModel) -> None:
        """Connect hubs between them by using a dict."""
        for connection in _map.connections:
            name1, name2 = connection.connection.split("-")
            if name1 not in self.connections:
                self.connections[name1] = []
            if name2 not in self.connections[name1]:
                self.connections[name1].append(name2)
            capacity = connection.metadata
            self.connection_capacities[(name1, name2)] = (
                capacity if capacity is not None else 100)

    def get_hub(self, name: str) -> HubModel:
        """Return a hub by searching by name."""
        return next(hub for hub in self.hubs if hub.name == name)
