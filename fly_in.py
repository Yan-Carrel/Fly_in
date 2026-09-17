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
    try:
        load_dotenv()
        map_argument = None
        arguments = sys.argv[1:]
        show_all = False
        for argument in arguments:
            # if not argument.startswith("MAP="):
            #     raise ValueError(
            #         "invalid argument; use MAP=<map_file>"
            #     )
            if argument == "show_all":
                show_all = True
            if map_argument is not None and argument.startswith("MAP="):
                raise ValueError("only one MAP argument is allowed")
            if argument.startswith("MAP="):
                map_argument = argument.removeprefix("MAP=") or None
        map_filename = map_argument or os.getenv("MAP")
        if not map_filename:
            print("Error: map not found. Please choose a filename in .env")
            sys.exit(0)
        map_parser = parser.MapParser(map_filename)

        graph = graph_pac.Graph(map_parser.parse())
        visual = graph_pac.Visual(graph, 80, 120)
        visual.display_all_labels = show_all
        visual.display_connection_occupancy = True
        background = os.getenv("BACKGROUND")
        engine = graph_pac.Engine(background, visual)

        solver = Solver(graph)
        paths = solver.get_all_paths()

        if paths != [[]]:
            route = Route(graph, paths, map_parser.drone_count)

            for i in range(1, map_parser.drone_count + 1):
                route.best_path(f"D{i}", paths)

            visual.drone_count = map_parser.drone_count
            visual.formatted_routes = route.formatted_routes()
            visual.hub_states = route.hub_states
            visual.link_states = route.link_states
            visual.total_cost = route.total_cost()
            visual.average_turn = route.average_turn()

            engine.initialize_pygame()
            engine.run()
        else:
            print("Unable to find any valid path")
    except (Exception, KeyboardInterrupt) as e:
        print(e)
