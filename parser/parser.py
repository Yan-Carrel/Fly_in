from parser.models import HubModel, ConnectionModel, MapModel
from typing import Any, Optional
from pydantic import ValidationError


class MapParser:
    def __init__(self, filename: str) -> None:
        self.drone_count = 0
        self.filename = filename
        self.connections = []
        self.start_hub = None
        self.end_hub = None
        self.hubs = []

    def parse(self) -> MapModel:
        try:
            with open(self.filename, "r") as file:
                lines = file.read().splitlines()
        except FileNotFoundError as e:
            print(f"Error: {self.filename} was not found")
            return

        hubs = []
        connections = []

        for line in lines:
            if not line or line.startswith("#"):
                continue
            if line.startswith("nb_drones:"):
                self.drone_count = int(line.split(':')[1])
            elif line.startswith("connection"):
                connections.append(line.split(':')[1].strip())
            elif "hub" in line:
                key, value = line.split(':')
                hubs.append({key:value})

        self.parse_hub(hubs)
        self.parse_connections(connections)

        try:
            _map = MapModel(
                drone_count = self.drone_count,
                start_hub=self.start_hub,
                end_hub=self.end_hub,
                hubs=self.hubs,
                connections=self.connections
                )
            return _map
        except ValidationError as e:
            print(e.errors()[0]['msg'])
            exit(1)


    def parse_hub(self, hubs) -> None:
        for hub in hubs:
            hub_type, value = list(hub.items())[0]
            parts = value.strip().split(" ")
            try:
                name, x, y = parts[0:3]
            except Exception:
                print("Error: invalid hub format. Usage: <name> <x> <y> <metadata>")
                continue

            metadata: dict[str, Any] = {}
            if len(parts) >= 4:
                metadata_list = parts[3:]
                for meta in metadata_list:
                    try:
                        meta_key, meta_value = meta.replace("[", "").replace("]", "").split('=')
                    except ValueError:
                        print("Error: metadata should be in 'key=value' format")
                        exit(1)
                    metadata[meta_key] = meta_value
            elif len(parts) == 3:
                metadata = None

            try:
                new_hub = HubModel(name=name, x=int(x), y=int(y), metadata=metadata)
                self.hubs.append(new_hub)
                if hub_type == "start_hub":
                    self.start_hub = new_hub
                elif hub_type == "end_hub":
                    self.end_hub = new_hub
            except ValidationError as e:
                print(e.errors()[0]['msg'])
                exit(1)


    def parse_connections(self, connections) -> None:
        for connection in connections:
            connec_parts = connection.strip().split(" ")

            if len(connec_parts) == 1:
                connec_metadata = None
            elif len(connec_parts) == 2:
                raw_metadata = connec_parts[1].replace("[", "").replace("]", "")

                if "=" not in raw_metadata:
                    print(f"Error: Invalid metadata format '{raw_metadata}'")
                    exit(1)

                try:
                    key, value = raw_metadata.split("=")
                except Exception:
                    print(f"Error: Invalid metadata format for {connec_parts[0]}")
                    exit(1)

                try:
                    connec_metadata = int(value)
                except ValueError:
                    print(f"Error: max_link_capacity must be a positive integer for {connec_parts[0]}")
                    exit(1)
            else:
                print(f"Error: invalid connection format '{connection}'")
                exit(1)

            try:
                self.connections.append(ConnectionModel(connection=connec_parts[0], metadata=connec_metadata))
            except ValueError as e:
                print(e.errors()[0]['msg'])
                exit(1)

