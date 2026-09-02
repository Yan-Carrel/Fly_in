"""Entry point for the drone routing simulation.

Parses a map file, computes optimal drone paths with capacity and
timing constraints, and runs the pygame visualization.
"""
import os
import sys
import argparse
from dotenv import load_dotenv
import parser
import graph_pac
from algorithm import Solver
from route import Route


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    """Parse map selection and developer-only animation options."""
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("map_argument", nargs="?")
    argument_parser.add_argument(
        "--frames-per-turn", type=int, default=600,
        help="Number of animation frames used for each simulation turn.",
    )
    argument_parser.add_argument(
        "--show-all", "--show_all", action="store_true",
        help="Show all hub and connection labels at startup.",
    )
    return argument_parser.parse_args(arguments)


if __name__ == "__main__":
    try:
        load_dotenv()
        command_line = parse_arguments(sys.argv[1:])
        map_argument = command_line.map_argument
        if map_argument and map_argument.startswith("MAP="):
            map_argument = map_argument.removeprefix("MAP=")
        map_filename = map_argument or os.getenv("MAP")
        if not map_filename:
            print("Error: map not found. Please choose a filename in .env")
            sys.exit(0)
        map_parser = parser.MapParser(map_filename)

        graph = graph_pac.Graph(map_parser.parse())
        visual = graph_pac.Visual(graph, 80, 120)
        background = os.getenv("BACKGROUND")
        engine = graph_pac.Engine(background, visual)

        solver = Solver(graph)
        paths = solver.get_all_paths()

        if paths != [[]]:
            route = Route(graph, paths, map_parser.drone_count)

            if command_line.frames_per_turn <= 0:
                raise ValueError("--frames-per-turn must be positive")
            engine.frames_per_turn = command_line.frames_per_turn

            for i in range(1, map_parser.drone_count + 1):
                route.best_path(f"D{i}", paths)

            visual.drone_count = map_parser.drone_count
            visual.formatted_routes = route.formatted_routes()
            visual.hub_states = route.hub_states
            visual.link_states = route.link_states
            visual.total_cost = route.total_cost()
            visual.average_turn = route.average_turn()
            visual.display_all_labels = command_line.show_all

            engine.initialize_pygame()
            engine.run()
        else:
            print("Unable to find any valid path")
    except Exception as e:
        print(e)
