import parser
import graph_pac
import webcolors


if __name__ == "__main__":
    map_parser = parser.MapParser("map.txt")
    
    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(1080, 720, "black", graph, 200)

    visual.initialize_pygame()
    visual.run()

