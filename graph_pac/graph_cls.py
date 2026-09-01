"""Graph representation of a parsed map: hubs and their connections."""
from parser import MapModel, HubModel


class Graph:
    """Represent validated hubs and bidirectional connection capacities."""

    def __init__(self, _map: MapModel) -> None:
        """Build graph indexes from a validated map model."""
        self.start_hub = _map.start_hub
        self.end_hub = _map.end_hub
        self.hubs = _map.hubs
        self.connections: dict[str, list[str]] = {}
        self.connection_capacities: dict[tuple[str, str], int] = {}
        self.build_connections(_map)

    def build_connections(self, _map: MapModel) -> None:
        """Build adjacency and capacity indexes from map connections."""
        for connection in _map.connections:
            name1, name2 = connection.connection.split("-")
            if name1 not in self.connections:
                self.connections[name1] = []
            if name2 not in self.connections[name1]:
                self.connections[name1].append(name2)
            capacity = connection.metadata
            self.connection_capacities[(name1, name2)] = (
                capacity if capacity is not None else 100)
            if name2 not in self.connections:
                self.connections[name2] = []
            if name1 not in self.connections[name2]:
                self.connections[name2].append(name1)
            self.connection_capacities[(name2, name1)] = (
                capacity if capacity is not None else 100)

    def get_hub(self, name: str) -> HubModel:
        """Return the hub identified by ``name``."""
        return next(hub for hub in self.hubs if hub.name == name)
