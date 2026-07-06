from typing import Any, Optional, Self
import webcolors
from pydantic import BaseModel, Field, ValidationError, model_validator


class HubModel(BaseModel):
    name: str = Field(min_length=1)
    x: int = Field(...)
    y: int = Field(...)
    metadata: Optional[list[str]] = Field(default=None, min_length=1)

    @model_validator(mode='after')
    def validade_hub(self) -> Self:
        valid_metadatas = ["zone", "color", "max_drones"]
        valid_zones = ["normal", "blocked", "restricted", "priority"]

        if self.metadata:
            for data in self.metadata:
                if "=" not in data:
                    raise ValueError("Metadata item should be in 'key=value' format")

                name, value = data.split("=", 1)
                name = name.replace("[", "")
                value = value.replace("]", "")
                if name not in valid_metadatas:
                    raise ValueError("zone, color and max_drones are the only valid metadata")

                if name == "zone" and value not in valid_zones:
                    raise ValueError("Error: normal, blocked, restricted and priority are the only valid zones")

                elif name == "color":
                    try:
                        webcolors.name_to_hex(value)
                    except ValueError as e:
                        raise ValueError(f"{value} is not a valid standard web color name")

                elif name == "max_drones":
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


# class Map(BaseModel):
#     drone_count: int = Field(ge=1)
#     start_hub = dict[str, Any]
#     end_hub = 


class MapParser:
    def __init__(self, filename: str) -> None:
        self.drone_count = 0
        self.filename = filename
        self.connections = []
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
            _, value = list(hub.items())[0]
            parts = value.strip().split(" ")
            try:
                name, x, y = parts[0:3]
            except Exception:
                print("Error: invalid hub format. Usage: <name> <x> <y> <metadata>")

            if len(parts) >= 4:
                metadata = parts[3:]
            elif len(parts) == 3:
                metadata = None

            try:
                self.hubs.append(HubModel(name=name, x=int(x), y=int(y), metadata=metadata))
            except ValueError as e:
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


if __name__ == "__main__":
    map_parser = MapParser("map.txt")
    map_parser.parse()
