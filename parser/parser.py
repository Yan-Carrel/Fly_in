class MapParser:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.hubs = []
        self.connections = {}
        self.graph

    def parse(self) -> None:
        with open(self.filename, "r") as file:
            lines = file.read().splitlines()

        for line in lines:
            if line.startswith("nb_drones:"):
                self.drone_count = int(line.split(':')[1])
            # elif not line.startswith("#"):
                


if __name__ == "__main__":
    map_parser = MapParser("map.txt")
    print(map_parser.parse())

# Responsibilities:

# open file
# iterate through lines
# determine line type
# create objects
# return a complete graph