from graph_pac import Graph
from parser import HubModel
from collections import deque


class Solver:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def find_path(self, start: HubModel) -> list[str]:
        visited = set()
        visited.add(start)
        queue = deque([start])
        path = {}

        while queue:
            current = queue.popleft()
            if current not in visited:
                visited.add(current)
                for neighbor in get_neighbors():
                    if neighbor not in visited:
                        queue.append(neighbor)


    def get_neighbors(self, hub: HubModel, visited: list[str]) -> list[HubModel]:
        connections = self.graph.connections[hub.name]

        return [name for name in connections if name not in visited]
