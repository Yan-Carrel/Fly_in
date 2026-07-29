import os
from dotenv import load_dotenv
import parser
import graph_pac
import webcolors
from algorithm import Solver
from route import Route
from parser import HubModel


if __name__ == "__main__":
    load_dotenv()
    maps = os.getenv("MAPS").split(",")
    map_parser = parser.MapParser(f"maps/{maps[0]}")

    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 100)
    engine = graph_pac.Engine("black", visual)
    solver = Solver(graph)
    route = Route(graph, solver.get_all_paths(), map_parser.drone_count)

    paths = solver.get_all_paths()

    if paths != [[]]:
        for i in range(1, map_parser.drone_count + 1):
            route.best_path(f"D{i}", paths)

        visual.drone_count = map_parser.drone_count
        visual.formatted_routes = route.formatted_routes()
        for i in range(1, len(visual.formatted_routes)):
            print(visual.formatted_routes[i])
        # exit(1)

        engine.initialize_pygame()
        engine.run()
    else:
        print("Unable to find any valid path")
