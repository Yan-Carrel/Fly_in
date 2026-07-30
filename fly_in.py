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
    engine = graph_pac.Engine("darkblue", visual)
    solver = Solver(graph)
    route = Route(graph, solver.get_all_paths(), map_parser.drone_count)

    paths = solver.get_all_paths()

    if paths != [[]]:
        for i in range(1, map_parser.drone_count + 1):
            route.best_path(f"D{i}", paths)

        visual.drone_count = map_parser.drone_count
        visual.formatted_routes = route.formatted_routes()
        visual.hub_states = route.hub_states
        print(route.hub_states)

        for i in range(1, len(visual.formatted_routes) + 1):
            print(" ".join(visual.formatted_routes[i]))
            visual.total_cost += len(visual.formatted_routes[i])
            if any(graph.end_hub.name in element for element in visual.formatted_routes[i]):
                    visual.average_turn += i
        visual.average_turn /= map_parser.drone_count

        engine.initialize_pygame()
        engine.run()
    else:
        print("Unable to find any valid path")
