"""This module is responsible for choosing appropriate path for each drone."""
from graph_pac import Graph
from parser import HubModel
import copy


class Route:
    """Class responsible for computing routes."""

    def __init__(
        self, graph: Graph,
        paths: list[list[str]],
        drones_count: int
            ) -> None:
        """Initialize the Route class."""
        self.graph = graph
        self.paths = paths
        self.drones_path: list[list[str]] = []
        self.hub_states: dict[int, dict[str, int]] = {}
        self.link_states: dict[int, dict[tuple[str, str], int]] = {}
        self.hub_states[0] = {"start": drones_count}
        self.drones_count = drones_count

    def convert_to_int(self, value: object) -> int:
        """Convert values that might be a string instead of integers."""
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

    def compute_route(
        self, drone: str, path: list[str]
            ) -> tuple[
                dict[int, dict[str, int]],
                dict[int, dict[tuple[str, str], int]],
                list[str],
                list[str]]:
        """Compute and format drone path, update hubs and links occupency."""
        raw_path = [path[0]]
        formatted_path = [f"{drone}-{path[0]}"]
        hub_states = copy.deepcopy(self.hub_states)
        link_states = copy.deepcopy(self.link_states)

        turn = 1
        i = 1

        while i < len(path):
            current_hub = self.graph.get_hub(path[i])
            previous_hub = self.graph.get_hub(path[i - 1])
            hop_cost = self._hop_cost(current_hub)
            arrival_turn = turn + hop_cost - 1

            for current_turn in range(turn, arrival_turn + 1):
                self._ensure_turn_exists(
                    hub_states, link_states, current_turn)

            if self._can_advance(
                hub_states, link_states, turn, arrival_turn,
                    previous_hub, current_hub):
                self._apply_move(
                    hub_states, link_states, turn, arrival_turn,
                    previous_hub, current_hub)
                raw_path.append(current_hub.name)

                if hop_cost == 2:
                    formatted_path.append(
                        f"{drone}-{previous_hub.name}-{current_hub.name}")
                    formatted_path.append(f"{drone}-{current_hub.name}")
                else:
                    formatted_path.append(f"{drone}-{current_hub.name}")

                i += 1
                turn += hop_cost
            else:
                raw_path.append("")
                formatted_path.append("")
                turn += 1

            self._normalize_hub_states(hub_states)
        return hub_states, link_states, raw_path, formatted_path

    def _ensure_turn_exists(
        self, hub_states: dict[int, dict[str, int]],
        link_states: dict[int, dict[tuple[str, str], int]], turn: int
            ) -> None:
        """Seed this turn's hub occupancy from the most recent turn."""
        if turn not in hub_states:
            prior_turns = [t for t in hub_states if t <= turn - 1]
            baseline = max(prior_turns) if prior_turns else None
            hub_states[turn] = (
                dict(hub_states[baseline]) if baseline is not None else {})
        if turn not in link_states:
            link_states[turn] = {}

    def _can_advance(
        self, hub_states: dict[int, dict[str, int]],
        link_states: dict[int, dict[tuple[str, str], int]],
        turn: int, arrival_turn: int,
        previous_hub: HubModel, current_hub: HubModel
            ) -> bool:
        """Check free capacity in destination hub and the link int it."""
        drones_in_hub = hub_states[arrival_turn].get(current_hub.name, 0)
        link_load = link_states[turn].get(
            (previous_hub.name, current_hub.name), 0)

        current_metadata = current_hub.metadata or {}
        max_drones = self.convert_to_int(
            current_metadata.get("max_drones", 100))
        max_link_capacity = self.convert_to_int(
            self.graph.connection_capacities.get(
                (previous_hub.name, current_hub.name), 100)
        )

        return bool(
            drones_in_hub + 1 <= max_drones
            and link_load + 1 <= max_link_capacity)

    def _apply_move(
        self, hub_states: dict[int, dict[str, int]],
        link_states: dict[int, dict[tuple[str, str], int]],
        turn: int, arrival_turn: int, previous_hub: HubModel,
        current_hub: HubModel
            ) -> None:
        """Record drone's arrival and departure from previous_hub."""
        hub_states[arrival_turn][current_hub.name] = hub_states[
            arrival_turn].get(
            current_hub.name, 0) + 1
        if hub_states[arrival_turn].get(previous_hub.name, 0) >= 1:
            hub_states[arrival_turn][previous_hub.name] -= 1

        link_states[turn][(previous_hub.name, current_hub.name)] = (
            link_states[turn].get(
                (previous_hub.name, current_hub.name), 0) + 1
        )

        for t in hub_states:
            if t > arrival_turn:
                hub_states[t][current_hub.name] = 1 + hub_states[t].get(
                    current_hub.name, 0)
                if hub_states[t].get(previous_hub.name, 0) >= 1:
                    hub_states[t][previous_hub.name] -= 1

    def _hop_cost(self, hub: HubModel) -> int:
        """Compute costs on each hub to enter."""
        metadata = hub.metadata or {}
        return 2 if metadata.get("zone") == "restricted" else 1

    def _normalize_hub_states(
        self, hub_states: dict[int, dict[str, int]]
            ) -> None:
        """Fill missing hub counts so each turn has a complete snapshot."""
        known_hubs = [hub.name for hub in self.graph.hubs]
        carried_state: dict[str, int] = {}

        for turn in sorted(hub_states):
            current_state = hub_states[turn]
            for hub_name in known_hubs:
                if hub_name not in current_state:
                    current_state[hub_name] = carried_state.get(hub_name, 0)
            carried_state = dict(current_state)

    def best_path(self, drone: str, paths: list[list[str]]) -> list[str]:
        """Choose the shortest path, favoring priority-zone hubs on ties."""
        results = []
        for path in paths:
            results.append(self.compute_route(drone, path))

        best_path = min(
            results,
            key=lambda p: (
                self.get_path_cost(p[2]),
                -self._priority_hub_count(p[2]),
            ),
        )

        self.drones_path.append(best_path[3])
        self.hub_states = best_path[0]
        self.link_states = best_path[1]
        return best_path[3]

    def build_turn_routes(self) -> dict[int, list[str]]:
        """Pivot per-drone formatted paths into turn-indexed move lists."""
        if not self.drones_path:
            return {}
        max_len = max(len(p) for p in self.drones_path)
        turn_routes: dict[int, list[str]] = {}
        for turn in range(max_len):
            moves = [
                drone_path[turn]
                for drone_path in self.drones_path
                if turn < len(drone_path) and drone_path[turn]
            ]
            turn_routes[turn] = moves
        return turn_routes

    def get_path_cost(self, path: list[str]) -> int:
        """Compute cost of path based on the total turns needed."""
        cost = 0
        for step in path:
            if not step:
                cost += 1
                continue
            metadata = self.graph.get_hub(step).metadata or {}
            zone = metadata.get("zone")
            if zone == "restricted":
                cost += 2
            elif zone in (None, "priority", "normal"):
                cost += 1
        return cost

    def _priority_hub_count(self, path: list[str]) -> int:
        """Count how many hubs in a path are marked as priority."""
        count = 0
        for step in path:
            if not step:
                continue
            metadata = self.graph.get_hub(step).metadata or {}
            if metadata.get("zone") == "priority":
                count += 1
        return count
