from parser import MapModel, ConnectionModel, HubModel


class Graph:
    def __init__(self, _map):
        self.hubs = _map.hubs
        self.connections = {}
        self.build_connections(_map)

    def build_connections(self, _map: MapModel) -> dict:
        for connection in _map.connections:
            name1, name2 = connection.connection.split("-")
            if name1 not in self.connections:
                self.connections[name1] = []
            if name2 not in list(self.connections.keys()):
                self.connections[name2] = []
            if name2 not in self.connections[name1]:
                self.connections[name1].append(name2)
                self.connections[name2].append(name1)

    def get_hub(name: str) ->  HubModel:
        return next(hub for hub in self.hubs if hub.name == name)
