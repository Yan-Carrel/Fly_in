"""Schedule drone movements while respecting hub and link capacities."""
from graph_pac import Graph
from parser import HubModel
import copy


class Route:
    """Compute turn-by-turn schedules for a fleet of drones."""

    def __init__(
        self, graph: Graph,
        paths: list[list[str]],
        drones_count: int
            ) -> None:
        """Initialize scheduling state for the supplied graph and paths."""
        self.graph = graph
        self.paths = paths
        self.drones_path: list[list[str]] = []
        self.hub_states: dict[int, dict[str, int]] = {}
        self.link_states: dict[int, dict[tuple[str, str], int]] = {}
        self.hub_states[0] = {graph.start_hub.name: drones_count}
        self.drones_count = drones_count

    def convert_to_int(self, value: object) -> int:
        """Convert values that might be a string instead of integers."""
        if value is None:
            return 1
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 1
        if isinstance(value, int):
            return value
        return 1

    def compute_route(
        self, path: list[str]
            ) -> tuple[
                dict[int, dict[str, int]],
                dict[int, dict[tuple[str, str], int]],
                list[str]]:
        """Schedule one path and return states plus its raw route."""
        raw_path = [path[0]]
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
                i += 1
                turn += hop_cost
            else:
                if i > 1:
                    incoming_hub = self.graph.get_hub(path[i - 2])
                    self._occupy_link(
                        link_states, turn, incoming_hub.name,
                        previous_hub.name)
                raw_path.append("")
                turn += 1

            self._normalize_hub_states(hub_states)
        return hub_states, link_states, raw_path

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
        """Return whether the destination and incoming link have capacity."""
        drones_in_hub = hub_states[arrival_turn].get(current_hub.name, 0)
        link_load = link_states[turn].get(
            (previous_hub.name, current_hub.name), 0)

        current_metadata = current_hub.metadata or {}
        max_drones = self.convert_to_int(
            current_metadata.get("max_drones", 1))
        max_link_capacity = self.convert_to_int(
            self.graph.connection_capacities.get(
                (previous_hub.name, current_hub.name), 1)
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
        """Record departure and arrival for a drone's hub movement."""
        if hub_states[turn].get(previous_hub.name, 0) >= 1:
            hub_states[turn][previous_hub.name] -= 1

        hub_states[arrival_turn][current_hub.name] = hub_states[
            arrival_turn].get(current_hub.name, 0) + 1

        for link_turn in range(turn, arrival_turn + 1):
            self._occupy_link(
                link_states, link_turn, previous_hub.name, current_hub.name)

        for t in hub_states:
            if t > turn:
                if hub_states[t].get(previous_hub.name, 0) >= 1:
                    hub_states[t][previous_hub.name] -= 1
            if t > arrival_turn:
                hub_states[t][current_hub.name] = 1 + hub_states[t].get(
                    current_hub.name, 0)

    def _occupy_link(
        self, link_states: dict[int, dict[tuple[str, str], int]],
        turn: int, previous_name: str, current_name: str
            ) -> None:
        """Record a drone occupying a link during a simulation turn."""
        self._ensure_link_turn_exists(link_states, turn)
        link = (previous_name, current_name)
        link_states[turn][link] = link_states[turn].get(link, 0) + 1

    def _ensure_link_turn_exists(
        self, link_states: dict[int, dict[tuple[str, str], int]],
        turn: int
            ) -> None:
        """Create a link snapshot when occupancy is extended to a turn."""
        if turn not in link_states:
            link_states[turn] = {}

    def _hop_cost(self, hub: HubModel) -> int:
        """Return the number of turns required to enter ``hub``."""
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
            results.append(self.compute_route(path))

        best_path = min(
            results,
            key=lambda p: (
                self.get_path_cost(p[2]),
                -self._priority_hub_count(p[2]),
            ),
        )

        self.drones_path.append(best_path[2])
        self.hub_states = best_path[0]
        self.link_states = best_path[1]
        return best_path[2]

    def formatted_routes(self) -> dict[int, list[str]]:
        """Format raw drone paths as turn-indexed movement strings."""
        if not self.drones_path:
            return {}
        turn_routes: dict[int, list[str]] = {}
        for drone_index, drone_path in enumerate(self.drones_path):
            turn_offset = 0
            for path_index in range(1, len(drone_path)):
                destination = drone_path[path_index]
                if not destination:
                    continue

                turn = path_index + turn_offset
                previous = next(
                    (drone_path[index]
                     for index in range(path_index - 1, -1, -1)
                     if drone_path[index]),
                    drone_path[0],
                )
                metadata = self.graph.get_hub(destination).metadata or {}
                if metadata.get("zone") == "restricted":
                    turn_routes.setdefault(turn, []).append(
                        f"D{drone_index + 1}-{previous}-{destination}")
                    turn_routes.setdefault(turn + 1, []).append(
                        f"D{drone_index + 1}-{destination}")
                    turn_offset += 1
                else:
                    turn_routes.setdefault(turn, []).append(
                        f"D{drone_index + 1}-{destination}")
        return turn_routes

    def build_turn_routes(self) -> dict[int, list[str]]:
        """Backward-compatible alias for :meth:`formatted_routes`."""
        return self.formatted_routes()

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

    def total_cost(self) -> int:
        """Return the sum of turns used by all scheduled drones."""
        return sum(len(path) - 1 for path in self.drones_path)

    def average_turn(self) -> float:
        """Return the average turn on which drones reach the goal."""
        if not self.drones_path:
            return 0.0
        return self.total_cost() / len(self.drones_path)
