import parser
import graph_pac
import webcolors


if __name__ == "__main__":
    map_parser = parser.MapParser("map.txt")
    
    graph = graph_pac.Graph(map_parser.parse())
    visual = graph_pac.Visual(500, 500, "black", graph.hubs, 50)

    visual.initialize_pygame()
    # visual.draw_hubs()
    visual.run()

