"""Module responsible for solving and finding paths."""
from collections import deque
from graph_pac import Graph
from parser import HubModel


class Solver:
    """Class that find single valid path or few valid paths."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the 'Solver' class."""
        self.graph = graph
        self.start = next(
            hub for hub in self.graph.hubs if hub.name == "start")
        self.paths: list[str] = []

    def find_path(self, start: HubModel, visited: set[str]) -> list[str]:
        """Find path be reading graph and using BFS algorithm."""
        goal = getattr(self.graph, "end_hub", None)
        if goal is None:
            goal = next(
                (hub for hub in self.graph.hubs if hub.name == "goal"), None)
        if goal is None:
            return []

        queue = deque([start])
        visited.add(start.name)
        previous: dict[str, str | None] = {start.name: None}

        while queue:
            current = queue.popleft()

            if current.name == goal.name:
                break

            for neighbor_hub in self.get_neighbors(current, visited):
                visited.add(neighbor_hub.name)
                previous[neighbor_hub.name] = current.name
                queue.append(neighbor_hub)

        if goal.name not in previous:
            return []

        path: list[str] = []
        current_name: str | None = goal.name
        while current_name is not None:
            path.append(current_name)
            current_name = previous[current_name]

        path.reverse()
        return path

    def get_neighbors(
        self, hub: HubModel, visited: set[str]
            ) -> list[HubModel]:
        """Get hubs connected to hub by reading connections in graph."""
        connections = self.graph.connections.get(hub.name, [])
        neighbors = [
            candidate
            for candidate in self.graph.hubs
            if candidate.name in connections and candidate.name not in visited
        ]

        result: list[HubModel] = []
        for neighbor in neighbors:
            metadata = neighbor.metadata
            if (
                metadata and "zone" in metadata
                    and metadata["zone"] == "blocked"):
                pass
            else:
                result.append(neighbor)

        return result

    def get_all_paths(self) -> list[list[str]]:
        """Find all available paths that can be used to reach goal."""
        main_path = self.find_path(self.start, set())
        junctions = self.get_junctions()
        paths: list[list[str]] = []
        paths.append(main_path)

        for junction in junctions:
            junction_children = self.graph.connections[junction]
            used_children = {
                c for c in junction_children
                if any(c in path for path in paths)}
            unused_children = [
                c for c in junction_children if c not in used_children]

            for child in unused_children:
                visited = used_children | (set(unused_children) - {child})
                path = self.find_path(self.start, visited)
                if path:
                    paths.append(path)

        return paths

    def get_junctions(self) -> list[str]:
        """Find all junctions or hubs that are connected to many hubs."""
        result = []
        for hub in self.graph.hubs:
            connections = self.graph.connections.get(hub.name, [])

            if len(connections) > 1:
                result.append(hub.name)

        return result
