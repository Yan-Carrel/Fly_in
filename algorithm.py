"""Find valid routes through the parsed drone network."""
from collections import deque
from graph_pac import Graph
from parser import HubModel


class Solver:
    """Find a primary route and alternatives through graph junctions."""

    def __init__(self, graph: Graph) -> None:
        """Initialize a solver for the supplied graph."""
        self.graph = graph
        self.start = next(
            hub for hub in self.graph.hubs
            if hub.name == graph.start_hub.name)
        self.paths: list[str] = []

    def find_path(self, start: HubModel, visited: set[str]) -> list[str]:
        """Find a path from ``start`` to the graph's end hub using BFS."""
        goal = getattr(self.graph, "end_hub", None)
        if goal is None:
            goal = next(
                (hub for hub in self.graph.hubs
                    if hub.name == self.graph.end_hub.name), None)
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
        """Return unvisited, allowed hubs directly reachable from ``hub``."""
        connections = self.graph.connections.get(hub.name, [])
        neighbors = [
            neighbor
            for neighbor in self.graph.hubs
            if neighbor.name in connections and neighbor.name not in visited
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
        """Find the main route and alternatives through available junctions."""
        main_path = self.find_path(self.start, set())
        junctions = self.get_junctions()
        paths: list[list[str]] = []
        paths.append(main_path)

        for junction in junctions:
            junction_children = self.graph.connections[junction]
            junction_path = next(
                (path for path in paths if junction in path), [])
            if not junction_path:
                continue
            junction_index = junction_path.index(junction)
            parent = (
                junction_path[junction_index - 1]
                if junction_index > 0 else None
            )
            for child in junction_children:
                excluded_children = {
                    candidate for candidate in junction_children
                    if candidate != child and candidate != parent
                }
                path = self.find_path(self.start, excluded_children)
                if path and path not in paths:
                    paths.append(path)

        return paths

    def get_junctions(self) -> list[str]:
        """Return hubs with more than one outgoing connection."""
        result = []
        for hub in self.graph.hubs:
            connections = self.graph.connections.get(hub.name, [])

            if len(connections) > 1:
                result.append(hub.name)

        return result
