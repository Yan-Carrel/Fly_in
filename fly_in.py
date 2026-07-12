import parser
import graph_pac
import webcolors


if __name__ == "__main__":
    map_parser = parser.MapParser("map.txt")
    
    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(graph, 80, 50)
    engine = graph_pac.Engine("black", visual)

    engine.initialize_pygame()
    engine.run()

