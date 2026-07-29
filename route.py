from graph_pac import Graph
from parser import HubModel
import copy


class Route:
    def __init__(self, graph: Graph, paths: list[list[str]], drones_count: int) -> None:
        self.graph = graph
        self.paths = paths
        self.drones_path: list[str] = []
        self.hub_states = {}
        self.link_states = {}
        self.hub_states[0] = {"start": drones_count}


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
        result_path = [path[0]]
        hub_states = copy.deepcopy(self.hub_states)
        link_states = copy.deepcopy(self.link_states)

        turn = 1
        i = 1

        while i < len(path):
            current_hub = self.graph.get_hub(path[i])
            previous_hub = self.graph.get_hub(path[i - 1])

            drones_in_hub = hub_states.get(turn, None)
            if not drones_in_hub:
                hub_states[turn] = {}
                hub_states[turn][current_hub.name] = 0

            link_state = link_states.get(turn, None)
            if not link_state:
                link_states[turn] = {}
                link_states[turn][(previous_hub.name, current_hub.name)] = 0
            link_state = link_states[turn].get((previous_hub.name, current_hub.name), 0)

            drones_in_hub = hub_states[turn].get(current_hub.name, 0)

            max_drones = self.convert_to_int(current_hub.metadata.get("max_drones", 100))
            if previous_hub:
                max_link_capacity = self.graph.connection_capacities.get((previous_hub.name, current_hub.name), 100)
                max_link_capacity = self.convert_to_int(max_link_capacity)
            else:
                max_link_capacity = 100

            full = (max_drones < drones_in_hub + 1
            or max_link_capacity < link_state + 1)

            if not full:
                hub_states[turn][current_hub.name] = drones_in_hub + 1
                link_states[turn][(previous_hub.name, current_hub.name)] = link_state + 1
                result_path.append(current_hub.name)
                i += 1
            else:
                result_path.append("")
                if previous_hub.name not in hub_states[turn - 1]:
                    hub_states[turn - 1][previous_hub.name] = 0

                hub_states[turn - 1][previous_hub.name] -= 1
    
            turn += 1

        return hub_states, link_states, result_path

    def best_path(self, drone: str, paths: list[list[str]]) -> list[str]:
        results = []
        for i in range(len(paths.copy())):
            results.append(self.compute_route(paths[i]))

        tup_results = []

        best_path = min(results, key=lambda p: self.get_path_cost(p[2]))

        self.drones_path.append(best_path[2])
        self.hub_states = best_path[0]
        self.link_states = best_path[1]
        return best_path[-1]

    def formatted_routes(self) -> list[str]:
        turns = len(max(self.drones_path, key=len))
        drones_count = len(self.drones_path)
        drones_path_output: dict[int, list[str]] = {}

        for turn in range(1, turns):
            for i in range(drones_count):
                if turn < len(self.drones_path[i]) and self.drones_path[i][turn]:
                    # try:
                    connections = self.graph.connections
                    destination = self.drones_path[i][turn]
                    metadata = next((hub.metadata for hub in self.graph.hubs if hub.name == destination), None)
                    if metadata and "zone" in metadata and metadata["zone"] == "restricted":
                        start = next((key for key, value in self.graph.connections.items() if destination in self.graph.connections[key]), next)
                        try:
                            drones_path_output[turn].append(f"D{i + 1}-{start}-{destination}")
                        except KeyError:
                            drones_path_output[turn] = []
                            drones_path_output[turn].append(f"D{i + 1}-{start}-{destination}")
                    else:
                        try:
                            drones_path_output[turn].append(f"D{i + 1}-{destination}")
                        except KeyError:
                            drones_path_output[turn] = []
                            drones_path_output[turn].append(f"D{i + 1}-{destination}")

        return drones_path_output

    def get_path_cost(self, path: list[str]) -> int:
        cost = 0
        for step in path:
            if not step:
                cost += 1
                continue
            zone = self.graph.get_hub(step).metadata.get("zone")
            if zone == "restricted":
                cost += 2
            elif zone in (None, "priority", "normal"):
                cost += 1
        return cost
