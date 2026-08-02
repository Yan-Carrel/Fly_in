"""Entry point for the drone routing simulation.

Parses a map file, computes optimal drone paths with capacity and
timing constraints, and runs the pygame visualization.
"""
import os
import sys
from dotenv import load_dotenv
import parser
import graph_pac
from algorithm import Solver
from route import Route


def compute_hub_occupancy(
    drone_count: int,
    graph: "graph_pac.Graph",
        formatted_routes: dict[int, list[str]]) -> dict[int, dict[str, int]]:
    """Track position of each drone on each turn."""
    start_name = graph.start_hub.name
    drone_position = {i: start_name for i in range(1, drone_count + 1)}

    hub_states: dict[int, dict[str, int]] = {}
    hub_states[0] = {hub.name: 0 for hub in graph.hubs}
    hub_states[0][start_name] = drone_count

    for turn in sorted(formatted_routes.keys()):
        for move in formatted_routes[turn]:
            drone_id, *hops = move.split("-")
            drone_num = int(drone_id[1:])
            drone_position[drone_num] = hops[0]

        counts = {hub.name: 0 for hub in graph.hubs}
        for hub_name in drone_position.values():
            counts[hub_name] += 1
        hub_states[turn] = counts

    return hub_states


if __name__ == "__main__":
    load_dotenv()
    try:
        map_parser = parser.MapParser(os.getenv("MAP"))
    except AttributeError:
        sys.exit("Error, map not found. Please choose a filename in .env")

    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 100)
    try:
        background = os.getenv("BACKGROUND")
        engine = graph_pac.Engine(background, visual)
    except ValueError:
        engine = graph_pac.Engine("darkblue", visual)

    solver = Solver(graph)
    route = Route(graph, solver.get_all_paths(), map_parser.drone_count)

    engine.frames_per_turn = int(os.getenv("FRAMES_PER_TURN"))
    paths = solver.get_all_paths()

    if paths != [[]]:
        for i in range(1, map_parser.drone_count + 1):
            route.best_path(f"D{i}", paths)

        visual.drone_count = map_parser.drone_count
        visual.formatted_routes = route.formatted_routes()
        visual.hub_states = compute_hub_occupancy(
            map_parser.drone_count, graph, visual.formatted_routes
            )

        for i in range(1, len(visual.formatted_routes) + 1):
            print(" ".join(visual.formatted_routes[i]))
            visual.total_cost += len(visual.formatted_routes[i])
            if any(
                graph.end_hub.name in element
                for element in visual.formatted_routes[i]
            ):
                visual.average_turn += i
        visual.average_turn /= map_parser.drone_count

        engine.initialize_pygame()
        engine.run()
    else:
        print("Unable to find any valid path")
