"""Module responsible for parsing by reading map file."""
from parser.models import HubModel, ConnectionModel, MapModel
from typing import Any
from pydantic import ValidationError
import sys


class MapParser:
    """Class that hold all parsing functions."""

    def __init__(self, filename: str | None) -> None:
        """Initialize the class with all needed elements."""
        if filename is None:
            sys.exit("Error: no map filename provided")

        self.drone_count = 0
        self.filename: str = filename
        self.connections: list[ConnectionModel] = []
        self.hubs: list[HubModel] = []

    def parse(self) -> MapModel:
        """Act as a function responsible for parsing all datas from map."""
        try:
            with open(self.filename, "r") as file:
                lines = file.read().splitlines()
        except FileNotFoundError:
            sys.exit(f"Error: map '{self.filename}' was not found")

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
                hubs.append({key: value})

        self.parse_hub(hubs)
        self.parse_connections(connections)

        try:
            _map = MapModel(
                drone_count=self.drone_count,
                start_hub=self.start_hub,
                end_hub=self.end_hub,
                hubs=self.hubs,
                connections=self.connections
                )
            return _map
        except ValidationError as e:
            sys.exit(e.errors()[0]['msg'])

    def parse_hub(self, hubs: list[dict[str, str]]) -> None:
        """Parse name, x and y coordinates and metadata."""
        for hub in hubs:
            hub_type, value = list(hub.items())[0]
            parts = value.strip().split(" ")
            try:
                name, x, y = parts[0:3]
            except Exception:
                sys.exit(
                    "Error: invalid hub format. "
                    "Usage: <name> <x> <y> <metadata>")
                continue

            metadata: dict[str, Any] = {}
            if len(parts) >= 4:
                metadata_list = parts[3:]
                for meta in metadata_list:
                    try:
                        meta_key, meta_value = meta.replace(
                            "[", "").replace("]", "").split('=')
                    except ValueError:
                        sys.exit(
                            "Error: metadata should be in 'key=value' format")
                    metadata[meta_key] = meta_value

            if hub_type == "start_hub" or hub_type == "end_hub":
                max_drones = metadata.get("max_drones", None)
                if not max_drones:
                    metadata["max_drones"] = self.drone_count
                elif int(max_drones) != self.drone_count:
                    sys.exit(
                        "Error, the 'max_drones' value should be equal to "
                        "the total number of drones in "
                        "starting and ending hubs.")
            elif len(parts) == 3:
                metadata = {"max_drones": 1}

            try:
                new_hub = HubModel(
                    name=name, x=int(x), y=int(y), metadata=metadata)
                self.hubs.append(new_hub)
                if hub_type == "start_hub":
                    self.start_hub = new_hub
                elif hub_type == "end_hub":
                    self.end_hub = new_hub
            except ValidationError as e:
                sys.exit(e.errors()[0]['msg'])

    def parse_connections(self, connections: list[str]) -> None:
        """Parse connections, get and check formats.

        Loop, format, and verify each value and get.
        """
        for connection in connections:
            connec_parts = connection.strip().split(" ")

            if len(connec_parts) == 1:
                connec_metadata = 1
            elif len(connec_parts) == 2:
                raw_metadata = connec_parts[1].replace(
                    "[", "").replace("]", "")

                if "=" not in raw_metadata:
                    sys.exit(
                        f"Error: Invalid metadata format '{raw_metadata}'")

                try:
                    key, value = raw_metadata.split("=")
                except Exception:
                    sys.exit(
                        "Error: Invalid metadata"
                        f"format for {connec_parts[0]}")

                try:
                    connec_metadata = int(value)
                except ValueError:
                    sys.exit(
                        "Error: max_link_capacity must be a "
                        f"positive integer for {connec_parts[0]}")
            else:
                sys.exit(f"Error: invalid connection format '{connection}'")

            try:
                self.connections.append(
                    ConnectionModel(
                        connection=connec_parts[0], metadata=connec_metadata))
            except ValidationError as e:
                print(e.errors()[0]['msg'])
                sys.exit(1)
