import os
from dotenv import load_dotenv
import parser
import graph_pac
import webcolors
from algorithm import Solver
from route import Route


if __name__ == "__main__":
    load_dotenv()
    maps = os.getenv("MAPS").split(",")
    map_parser = parser.MapParser(f"maps/{maps[9]}")

    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 50)
    engine = graph_pac.Engine("black", visual)
    solver = Solver(graph)
    route = Route(graph, solver.get_all_paths())

    paths = solver.get_all_paths()

    for i in range(1, map_parser.drone_count + 1):
        print(route.best_path(f"D{i}", paths))

    engine.initialize_pygame()
    engine.run()
