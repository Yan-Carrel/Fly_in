import os
from dotenv import load_dotenv
import parser
import graph_pac
import webcolors
from algorithm import Solver


if __name__ == "__main__":
    load_dotenv()
    maps = os.getenv("MAPS").split(",")
    map_parser = parser.MapParser(f"maps/{maps[2]}")

    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 50)
    engine = graph_pac.Engine("black", visual)
    solver = Solver(graph)

    # print(graph.connections)
    # exit(1)

    engine.initialize_pygame()
    engine.run()
