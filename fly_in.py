import parser
import graph


if __name__ == "__main__":
    map_parser = parser.MapParser("map.txt")
    
    graph = graph.Graph(map_parser.parse())
    # graph.build_graph(_map)
    # print(type(_map.hubs))
