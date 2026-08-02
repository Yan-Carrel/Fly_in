"""This module is responsible for choosing appropriate path for each drone."""
from graph_pac import Graph
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
        self.drones_path: list[str] = []
        self.hub_states = {}
        self.link_states = {}
        self.hub_states[0] = {"start": drones_count}

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

    def compute_route(self, path: list[str]) -> tuple[dict, dict, list[str]]:
        """Simulate one drone's path turn-by-turn.

        Walks the raw path hop by hop, advancing a real-time
        turn counter that accounts for restricted-zone hubs
        costing an extra turn to enter. At each step, checks
        whether the destination hub and the link into it
        have free capacity; if not, the drone waits (recorded as an empty
        string in the result path) rather than moving. Hub occupancy is
        carried forward turn-to-turn and propagated into already-computed
        later turns whenever an earlier turn's state changes.

        Parameters
        ----------
        path : list[str]
            Ordered list of hub names representing one drone's route from
            start to goal.

        Returns
        -------
        tuple[dict, dict, list[str]]
            ``(hub_states, link_states, result_path)`` — per-turn hub
            occupancy, per-turn link usage, and the path with waiting turns
            represented as empty strings.
        """
        result_path = [path[0]]
        hub_states = copy.deepcopy(self.hub_states)
        link_states = copy.deepcopy(self.link_states)

        turn = 1
        i = 1

        while i < len(path):
            current_hub = self.graph.get_hub(path[i])
            previous_hub = self.graph.get_hub(path[i - 1])

            self._ensure_turn_exists(hub_states, link_states, turn)

            if self._can_advance(
                hub_states, link_states,
                    turn, previous_hub, current_hub):
                self._apply_move(
                    hub_states, link_states, turn,
                    previous_hub, current_hub)
                result_path.append(current_hub.name)
                i += 1
                turn += self._hop_cost(current_hub)
            else:
                result_path.append("")
                turn += 1

        return hub_states, link_states, result_path

    def _ensure_turn_exists(
        self, hub_states: dict,
        link_states: dict, turn: int
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
        self, hub_states: dict, link_states: dict,
        turn: int, previous_hub, current_hub
            ) -> bool:
        """Check free capacity in destination hub and the link int it."""
        drones_in_hub = hub_states[turn].get(current_hub.name, 0)
        link_load = link_states[turn].get(
            (previous_hub.name, current_hub.name), 0)

        max_drones = self.convert_to_int(
            current_hub.metadata.get("max_drones", 100))
        max_link_capacity = self.convert_to_int(
            self.graph.connection_capacities.get(
                (previous_hub.name, current_hub.name), 100)
        )

        return (
            drones_in_hub + 1 <= max_drones
            and link_load + 1 <= max_link_capacity)

    def _apply_move(
        self, hub_states: dict, link_states: dict,
        turn: int, previous_hub, current_hub
            ) -> None:
        """Record drone's arrival and departure from previous_hub."""
        hub_states[turn][current_hub.name] = hub_states[turn].get(
            current_hub.name, 0) + 1
        if hub_states[turn].get(previous_hub.name, 0) >= 1:
            hub_states[turn][previous_hub.name] -= 1

        link_states[turn][(previous_hub.name, current_hub.name)] = (
            link_states[turn].get(
                (previous_hub.name, current_hub.name), 0) + 1
        )

        for t in hub_states:
            if t > turn:
                hub_states[t][current_hub.name] = 1 + hub_states[t].get(
                    current_hub.name, 0)
                if hub_states[t].get(previous_hub.name, 0) >= 1:
                    hub_states[t][previous_hub.name] -= 1

    def _hop_cost(self, hub) -> int:
        """Compute costs on each hub to enter."""
        return 2 if hub.metadata.get("zone") == "restricted" else 1

    def best_path(self, drone: str, paths: list[list[str]]) -> list[str]:
        """Choose best and shortest path from many paths for a drone."""
        results = []
        for i in range(len(paths.copy())):
            results.append(self.compute_route(paths[i]))

        best_path = min(results, key=lambda p: self.get_path_cost(p[2]))

        self.drones_path.append(best_path[2])
        self.hub_states = best_path[0]
        self.link_states = best_path[1]
        return best_path[-1]

    def formatted_routes(self) -> dict[int, list[str]]:
        """Expand each drone's raw path into per-turn move strings.

        Walks every drone's path in ``self.drones_path`` and assigns each hop
        to a real simulation turn, staggering drones that start at different
        times and inserting an extra turn for restricted-zone hubs (which
        take two turns to enter instead of one).

        Each move is formatted as ``"D{n}-{hub}"`` for a normal, single-turn
        hop, or ``"D{n}-{start}-{dest}"`` for a restricted hop that spans two
        turns (the first turn records departure, the second the arrival).

        Returns
        -------
        dict[int, list[str]]
            Mapping of turn number to the list of move strings for every
            drone that acts during that turn.
        """
        drones_count = len(self.drones_path)
        max_len = len(max(self.drones_path, key=len))

        input_idx = [1] * drones_count
        pending_stay = [False] * drones_count
        current_hub = [None] * drones_count
        finished = [False] * drones_count

        drones_path_output: dict[int, list[str]] = {}
        output_turn = 0
        safety_cap = max_len * 2 + drones_count

        while not all(finished) and output_turn < safety_cap:
            output_turn += 1
            turn_moves = []

            for i in range(drones_count):
                if finished[i]:
                    continue
                if pending_stay[i]:
                    turn_moves.append(f"D{i + 1}-{current_hub[i]}")
                    pending_stay[i] = False
                    continue
                if input_idx[i] >= len(self.drones_path[i]):
                    finished[i] = True
                    continue

                destination = self.drones_path[i][input_idx[i]]
                input_idx[i] += 1

                if not destination:
                    continue
                metadata = next((
                    hub.metadata for hub in self.graph.hubs
                    if hub.name == destination), None
                    )
                if metadata and metadata.get("zone") == "restricted":
                    start = next(
                        (key for key, value in self.graph.connections.items()
                            if destination in value),
                        None,
                    )
                    turn_moves.append(f"D{i + 1}-{start}-{destination}")
                    current_hub[i] = destination
                    pending_stay[i] = True
                else:
                    turn_moves.append(f"D{i + 1}-{destination}")

            if turn_moves:
                drones_path_output[output_turn] = turn_moves

        return drones_path_output
    
    # def compute_hub_occupancy(
    #     self, drone_count: int,
    #     graph: "graph_pac.Graph",
    #         formatted_routes: dict[int, list[str]]) -> dict[int, dict[str, int]]:
    #     """Track position of each drone on each turn."""
    #     start_name = graph.start_hub.name
    #     drone_position = {i: start_name for i in range(1, drone_count + 1)}

    #     hub_states: dict[int, dict[str, int]] = {}
    #     hub_states[0] = {hub.name: 0 for hub in graph.hubs}
    #     hub_states[0][start_name] = drone_count

    #     for turn in sorted(formatted_routes.keys()):
    #         for move in formatted_routes[turn]:
    #             drone_id, *hops = move.split("-")
    #             drone_num = int(drone_id[1:])
    #             drone_position[drone_num] = hops[0]

    #         counts = {hub.name: 0 for hub in graph.hubs}
    #         for hub_name in drone_position.values():
    #             counts[hub_name] += 1
    #         hub_states[turn] = counts

    #     return hub_states

    def get_path_cost(self, path: list[str]) -> int:
        """Compute cost of path based on the total turns needed."""
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
