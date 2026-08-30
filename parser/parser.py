"""Module responsible for parsing by reading map file."""
from parser.models import HubModel, ConnectionModel, MapModel
from typing import Any, NoReturn
from pydantic import ValidationError
from collections import Counter
import sys


class MapParser:
    """Class that hold all parsing functions."""

    def __init__(self, filename: str | None) -> None:
        """Initialize the class with all needed elements."""
        if filename is None:
            print("Error: no map filename provided")
            sys.exit(0)

        self.drone_count = 0
        self.filename: str = filename
        self.connections: list[ConnectionModel] = []
        self.hubs: list[HubModel] = []
        self.start_hub: HubModel | None = None
        self.end_hub: HubModel | None = None

    def _fail(self, message: str, line_no: int | None = None) -> NoReturn:
        """Print an error message, optionally annotated with a line number."""
        if line_no is None:
            print(message)
        else:
            print(f"Error on line {line_no}: {message}")
        sys.exit(0)

    def parse(self) -> MapModel:
        """Act as a function responsible for parsing all datas from map."""
        try:
            with open(self.filename, "r") as file:
                lines = file.read().splitlines()
        except FileNotFoundError:
            self._fail(f"Error: map '{self.filename}' was not found")

        hubs: list[tuple[int, str, str]] = []
        connections: list[tuple[int, str]] = []
        self.start_hub = None
        self.end_hub = None

        found_nb_drones = False
        for line_no, line in enumerate(lines, start=1):
            if "  " in line:
                self._fail(f"Error, too many spaces in line: {line}", line_no)
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("nb_drones: "):
                found_nb_drones = True
                try:
                    self.drone_count = int(line.split(':')[1])
                except ValueError:
                    self._fail(
                        f"Error, invalid line format: '{line}'.\n", line_no)
            elif line.startswith("connection: ") and found_nb_drones:
                hub_line = line.split(':')[1].strip()
                connections.append((line_no, hub_line))
            elif (
                    line.startswith("hub: ") or
                    line.startswith("start_hub: ") or
                    line.startswith("end_hub: ")) and found_nb_drones:
                key, value = line.split(':')
                hubs.append((line_no, key, value))

            else:
                if not found_nb_drones:
                    self._fail(f"Error, the first configuration must"
                    " be 'nb_drones'")
                else:
                    self._fail(f"Error, invalid line format: '{line}'", line_no)

        self.parse_hub(hubs)
        self.parse_connections(connections)

        hub_names = {hub.name for hub in self.hubs}
        for line_no, connection in connections:
            name1, name2 = connection.split(" ")[0].split("-")
            if name1 not in hub_names:
                self._fail(
                    f"Hub with name '{name1}' is not recognized",
                    line_no)
            if name2 not in hub_names:
                self._fail(
                    f"Hub with name '{name2}' is not recognized",
                    line_no)

        if self.start_hub is None:
            self._fail("Error: missing start_hub definition")
        if self.end_hub is None:
            self._fail("Error: missing end_hub definition")

        assert self.start_hub is not None
        assert self.end_hub is not None

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
            self._fail(e.errors()[0]['msg'])

    def parse_hub(self, hubs: list[tuple[int, str, str]]) -> None:
        """Parse name, x and y coordinates and metadata."""
        for line_no, hub_type, value in hubs:
            parts = value.strip().split()
            if len(parts) < 3:
                self._fail(
                    f"Error: invalid hub format for '{value}'. "
                    "Usage: <type>: <name> <x> <y> <metadata>,"
                    "start_hub, end_hub and hub are the only valid types",
                    line_no)
            try:
                name, x_raw, y_raw = parts[0:3]
            except Exception:
                self._fail(
                    f"Error: invalid hub format for '{value}'. "
                    "Usage: <type>: <name> <x> <y> <metadata>,"
                    "start_hub, end_hub and hub are the only valid types",
                    line_no)

            try:
                x = int(x_raw)
                y = int(y_raw)
            except ValueError:
                self._fail(
                    "Error, x and/or y are missings or invalids: "
                    f"'{' '.join(parts)}'", line_no)

            if x > 30 or x < -30 or y > 30 or y < -30:
                self._fail(
                    "Error, x and y coordinates might exceed the limits",
                    line_no)
            metadata: dict[str, Any] = {}
            if len(parts) >= 4:
                metadata_text = " ".join(parts[3:])
                if (
                    not metadata_text.startswith("[")
                    or not metadata_text.endswith("]")
                        ):
                    self._fail(
                        "Error, invalid metadata: "
                        f"'{metadata_text}'",
                        line_no)
                count = Counter(metadata_text)
                if (
                    count["zone="] > 1 or count["max_link_capacity="] > 1
                    or count["color="] > 1 or count["maxdrones="] > 1
                        ):
                    self._fail(
                        "Error, cannot define the same metadata"
                        f" twice: {metadata_text}",
                        line_no)

                metadata_items = metadata_text[1:-1].split()
                meta_keys = []
                for meta in metadata_items:
                    try:
                        meta_key, meta_value = meta.split('=', 1)
                    except ValueError:
                        self._fail(
                            "Error: metadata should be in 'key=value' format",
                            line_no)
                    if meta_key in meta_keys:
                        self._fail(
                            "Error, cannot define the same "
                            f"metadata twice: {meta_key}",
                            line_no)
                    meta_keys.append(meta_key)
                    metadata[meta_key] = meta_value

            if hub_type == "start_hub" or hub_type == "end_hub":
                max_drones = metadata.get("max_drones", None)
                if not max_drones:
                    metadata["max_drones"] = self.drone_count
                elif int(max_drones) < self.drone_count:
                    self._fail(
                        "Error, the 'max_drones' value can't be less "
                        "than the total number of drones in "
                        "starting and ending hubs.",
                        line_no)
            elif len(parts) == 3:
                metadata = {"max_drones": 1}

            if any(existing_hub.name == name for existing_hub in self.hubs):
                self._fail(f"Error: hub '{name}' is already defined", line_no)

            try:
                new_hub = HubModel(
                    name=name, x=x, y=y, metadata=metadata)
                self.hubs.append(new_hub)
                if hub_type == "start_hub":
                    if self.start_hub is not None:
                        self._fail(
                            "Error: multiple start_hub definitions", line_no)
                    self.start_hub = new_hub
                elif hub_type == "end_hub":
                    if self.end_hub is not None:
                        self._fail(
                            "Error: multiple end_hub definitions", line_no)
                    self.end_hub = new_hub
                if any(
                    [
                        True for h in self.hubs if new_hub.x == h.x and
                        new_hub.y == h.y and h != new_hub]
                            ):
                    self._fail(
                        "Error, two different hubs "
                        "cannot have the same coordinates",
                        line_no)
            except ValidationError as e:
                self._fail(e.errors()[0]['msg'], line_no)

    def parse_connections(self, connections: list[tuple[int, str]]) -> None:
        """Parse connections, get and check formats.

        Loop, format, and verify each value and get.
        """
        connections_found = []
        for line_no, connection in connections:
            connec_parts = connection.strip().split()

            if sorted(connec_parts[0].split("-")) in connections_found:
                self._fail(
                    f"Error, connection '{connec_parts[0]}' already exists."
                )
            else:
                connections_found.append(sorted(connec_parts[0].split("-")))

            if len(connec_parts) == 1:
                connec_metadata = 1
            elif len(connec_parts) == 2:
                raw_metadata = connec_parts[1]
                if (
                    not raw_metadata.startswith("[")
                    or not raw_metadata.endswith("]")
                        ):

                    self._fail(
                        "Error, metadata should be in 'key=value'"
                        f" format: {connec_parts}",
                        line_no)
                raw_metadata = raw_metadata[1:-1]

                if raw_metadata.split("=", 1)[0] != "max_link_capacity":
                    self._fail(
                        "Error, 'max_link_capacity' is the only valid metadata"
                        f" for connection: '{connection}'", line_no)

                if "=" not in raw_metadata:
                    self._fail(
                        f"Error: Invalid metadata format '{raw_metadata}'",
                        line_no)

                try:
                    key, value = raw_metadata.split("=", 1)
                except Exception:
                    self._fail(
                        "Error: Invalid metadata"
                        f"format for {connec_parts[0]}",
                        line_no)
                try:
                    connec_metadata = int(value)
                except ValueError:
                    self._fail(
                        "Error: max_link_capacity must be a "
                        f"positive integer for {connec_parts[0]}",
                        line_no)
            else:
                self._fail(
                    f"Error: invalid connection format '{connection}'",
                    line_no)

            try:
                self.connections.append(
                    ConnectionModel(
                        connection=connec_parts[0], metadata=connec_metadata))
            except ValidationError as e:
                self._fail(
                    f"{e.errors()[0]['msg']}\nInput:'{connection}'",
                    line_no)
