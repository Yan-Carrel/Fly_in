import parser
import graph_pac
import webcolors
from algorithm import Solver


if __name__ == "__main__":
    map_parser = parser.MapParser("map.txt")

    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 50)
    engine = graph_pac.Engine("black", visual)
    solver = Solver(graph)

    print(solver.get_neighbors(graph.hubs[1]))
    exit(1)

    engine.initialize_pygame()
    engine.run()
