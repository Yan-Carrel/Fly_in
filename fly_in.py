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


if __name__ == "__main__":
    load_dotenv()
    args = sys.argv
    map_filename = args[1] if len(args) == 2 else os.getenv("MAP")
    if not map_filename:
        print("Error: map not found. Please choose a filename in .env")
        sys.exit(0)
    map_parser = parser.MapParser(map_filename)

    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 100)
    background = os.getenv("BACKGROUND")
    engine = graph_pac.Engine(background, visual)

    solver = Solver(graph)
    route = Route(graph, solver.get_all_paths(), map_parser.drone_count)

    engine.frames_per_turn = int(os.getenv("FRAMES_PER_TURN") or "600")
    paths = solver.get_all_paths()

    if paths != [[]]:
        for i in range(1, map_parser.drone_count + 1):
            route.best_path(f"D{i}", paths)

        visual.drone_count = map_parser.drone_count
        visual.formatted_routes = route.formatted_routes()
        visual.hub_states = route.compute_hub_occupancy(
            map_parser.drone_count, graph, visual.formatted_routes
            )

        for i in range(1, len(visual.formatted_routes) + 1):
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
