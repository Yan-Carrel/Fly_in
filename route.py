from graph_pac import Graph
from parser import HubModel


class Route:
    def __init__(self, graph: Graph, paths: list[list[str]]) -> None:
        self.graph = graph
        self.paths = paths
        self.drones_path: [tuple, list[str]] = []

    def convert_to_int(self, value: object) -> int:
        if value is None:
            return 100
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 100
        if isinstance(value, int):
            return value
        return 100

    def compute_route(self, path: list[str]) -> list[str]:
        drones_paths = [tup[1] for tup in self.drones_path]
        result_path = path.copy()

        for t in range(1, len(result_path)):

            current_hub = self.graph.get_hub(result_path[t])
            previous_hub = self.graph.get_hub(path[t - 1])

            drones_in_hub = int(self.count_drones_in_hub(drones_paths, current_hub, t))
            max_drones = self.convert_to_int(current_hub.metadata.get("max_drones", 100))
            if previous_hub:
                max_link_capacity = self.graph.connection_capacities.get((previous_hub.name, current_hub.name), 100)
                max_link_capacity = self.convert_to_int(max_link_capacity)
            else:
                max_link_capacity = 100

            if (
                drones_in_hub + 1 > max_drones or
                    drones_in_hub + 1 > max_link_capacity):
                result_path.insert(t, "")

        self.drones_path.append(result_path)
        return result_path

    def count_drones_in_hub(self, paths: list[list[str]], hub: HubModel, i: int) -> int:
        count = 0
        for path in paths:
            if i < len(path) and path[i] == hub.name:
                count += 1
        return count
    
    def best_path(self, drone: str, paths: list[list[str]]) -> list[str]:
        results = []
        for path in paths:
            results.append(self.compute_route(path))
        best_path = min(results, key=lambda p: self.get_path_cost(p))
        self.drones_path.append((drone, best_path))
        return best_path


    def get_path_cost(self, path: list[str]) -> int:
        cost = 0
        for step in path:
            if not step:
                continue
            zone = self.graph.get_hub(step).metadata.get("zone")
            if zone == "restricted":
                cost += 2
            elif zone in (None, "priority", "normal"):
                cost += 1
        return cost
