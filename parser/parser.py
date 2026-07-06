from typing import Any, Optional, Self
import webcolors
from pydantic import BaseModel, Field, ValidationError, model_validator


class HubModel(BaseModel):
    name: str = Field(min_length=1)
    x: int = Field(...)
    y: int = Field(...)
    metadata: Optional[dict[str, Any]] = Field(default=None)

    @model_validator(mode='after')
    def validade_hub(self) -> Self:
        valid_metadatas = ["zone", "color", "max_drones"]
        valid_zones = ["normal", "blocked", "restricted", "priority"]

        if self.metadata:
            for key, value in self.metadata.items():
                if key not in valid_metadatas:
                    raise ValueError("zone, color and max_drones are the only valid metadata")

                if key == "zone" and value not in valid_zones:
                    raise ValueError("Error: normal, blocked, restricted and priority are the only valid zones")

                elif key == "color":
                    try:
                        webcolors.name_to_hex(value)
                    except ValueError as e:
                        raise ValueError(f"{value} is not a valid standard web color name")

                elif key == "max_drones":
                    try:
                        max_drones = int(value)
                    except Exception:
                        raise ValueError("Error: invalid max_drones value")
                    if max_drones <= 0:
                        raise ValueError("Error: max_drones can't be negative or equal to 0.")   
        return self


class ConnectionModel(BaseModel):
    connection: str = Field(min_length=1)
    metadata: Optional[int]= Field(default=None)

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        if "-" not in self.connection:
            raise ValueError("Error: Invalid format. Usage: <name1>-<name2> <metadata>")
        if self.metadata is not None and self.metadata <= 0:
            raise ValueError("Error: Metadata 'max_link_capacity' must be a positive integer")

        try:
            name1, name2 = self.connection.split("-")
        except Exception as e:
            raise ValueError(f"Error invalid format: {e}")
        if not name1 or not name2 or name1 == name2:
           raise ValueError(f"Error: Invalid connection '{self.connection}'")
        return self


class MapModel(BaseModel):
    drone_count: int
    start_hub: HubModel
    end_hub: HubModel
    hubs: list[HubModel] = Field(...)
    connections: list[ConnectionModel]

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        for connection in self.connections:
            name1, name2 = connection.connection.split("-")
            if not any(name1 == hub.name for hub in self.hubs):
                raise ValueError(f"Hub with name '{name1}' is not recognized")
            if not any(name2 == hub.name for hub in self.hubs):
                raise ValueError(f"Hub with name '{name2}' is not recognized")
        return self


class MapParser:
    def __init__(self, filename: str) -> None:
        self.drone_count = 0
        self.filename = filename
        self.connections = []
        self.start_hub = None
        self.end_hub = None
        self.hubs = []

    def parse(self) -> None:
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

        try:
            _map = MapModel(
                drone_count = self.drone_count,
                start_hub=self.start_hub,
                end_hub=self.end_hub,
                hubs=self.hubs,
                connections=self.connections
                )
        except ValidationError as e:
            print(e.errors()[0]['msg'])
            exit(1)


if __name__ == "__main__":
    map_parser = MapParser("map.txt")
    map_parser.parse()
