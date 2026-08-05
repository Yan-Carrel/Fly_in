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
            print("Error: no map filename provided")
            sys.exit(0)

        self.drone_count = 0
        self.max_nb_of_drone = 50
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
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("nb_drones: "):
                try:
                    self.drone_count = int(line.split(':')[1])
                except ValueError:
                    print(f"Error, invalid line format: '{line}'.\n")
                    sys.exit(0)
            elif line.startswith("connection: "):
                hub_line = line.split(':')[1].strip()
                connections.append(hub_line)
            elif (
                    line.startswith("hub: ") or
                    line.startswith("start_hub: ") or
                    line.startswith("end_hub: ")):
                key, value = line.split(':')
                hubs.append({key: value})

            else:
                print(f"Error, invalid line format: '{line}'")
                sys.exit(0)

        if self.drone_count > self.max_nb_of_drone:
            print(
                "Error, the maximum number of drones"
                f" is {self.max_nb_of_drone}")
            sys.exit(0)
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
            if len(parts) < 3:
                print(
                    f"Error: invalid hub format for '{hub}'. "
                    "Usage: <name> <x> <y> <metadata>")
                sys.exit(0)
            try:
                name, x_raw, y_raw = parts[0:3]
            except Exception:
                print(
                    "Error: invalid hub format. "
                    "Usage: <name> <x> <y> <metadata>")
                sys.exit(0)

            try:
                x = int(x_raw)
                y = int(y_raw)
            except ValueError:
                print(
                    "Error, x and/or y are missings or invalids: "
                    f"'{" ".join(parts)}'")
                sys.exit(0)

            if x > 30 or x < -30 or y > 30 or y < -30:
                print("Error, x and y coordinates might exceed the limits")
                sys.exit(0)

            metadata: dict[str, Any] = {}
            if len(parts) >= 4:
                metadata_list = parts[3:]
                if '[' not in parts[3] or ']' not in parts[-1]:
                    print(
                        "Error, metadata should be inside square brackets: "
                        f"'{" ".join(parts[3:])}'"
                        )
                    sys.exit(0)

                for meta in metadata_list:
                    try:
                        meta_key, meta_value = meta.replace(
                            "[", "").replace("]", "").split('=')
                    except ValueError:
                        print(
                            "Error: metadata should be in 'key=value' format")
                        sys.exit(0)
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
                    name=name, x=x, y=y, metadata=metadata)
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
                raw_metadata = connec_parts[1]
                if '[' not in raw_metadata or ']' not in raw_metadata:

                    print(
                        "Error, metadata should be in 'key=value'"
                        f" format: {connec_parts}")
                    sys.exit(0)
                raw_metadata = raw_metadata.replace(
                    "[", "").replace("]", "")

                if raw_metadata.split("=")[0] != "max_link_capacity":
                    print(
                        "Error, 'max_link_capacity' is the only valid metadata"
                        f" for connection: '{connection}'"
                        )
                    sys.exit(0)

                if "=" not in raw_metadata:
                    sys.exit(
                        f"Error: Invalid metadata format '{raw_metadata}'")

                try:
                    key, value = raw_metadata.split("=")
                except Exception:
                    print(
                        "Error: Invalid metadata"
                        f"format for {connec_parts[0]}")
                    sys.exit(0)
                try:
                    connec_metadata = int(value)
                except ValueError:
                    print(
                        "Error: max_link_capacity must be a "
                        f"positive integer for {connec_parts[0]}")
                    sys.exit(0)
            else:
                print(f"Error: invalid connection format '{connection}'")
                sys.exit(0)

            try:
                self.connections.append(
                    ConnectionModel(
                        connection=connec_parts[0], metadata=connec_metadata))
            except ValidationError as e:
                print(f"{e.errors()[0]['msg']}\nInput:'{connection}'")
                sys.exit(0)
