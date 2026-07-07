import parser


if __name__ == "__main__":
    map_parser = parser.MapParser("map.txt")
    _map = map_parser.parse()
    print(_map)