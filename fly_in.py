import os
from dotenv import load_dotenv
import parser
import graph_pac
import webcolors
from algorithm import Solver


if __name__ == "__main__":
    load_dotenv()
    maps = os.getenv("MAPS").split(",")
    map_parser = parser.MapParser(f"maps/{maps[0]}")

    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 50)
    engine = graph_pac.Engine("black", visual)
    solver = Solver(graph)

    # start = next(hub for hub in graph.hubs if hub.name == "start")
    # print(solver.find_path(start, {"maze_b2"}))

    # solver.get_all_paths()

    for path in solver.get_all_paths():
        print(path)

    engine.initialize_pygame()
    engine.run()
