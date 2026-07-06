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

                name, value = data.split("=")
                if name not in valid_metadatas:
                    raise ValueError("zone, color and max_drones are the only valid metadata")

                if name == "zone" and value not in valid_zones:
                    raise ValueError("Error, normal, blocked, restricted and priority are the only valid zones")

                elif name == "color":
                    try:
                        webcolors.name_to_hex(value)
                    except ValueError as e:
                        raise ValueError(f"{value} is not a valid standard web color name")

                elif name == "max_drones":
                    try:
                        max_drones = int(value)
                    except Exception:
                        raise ValueError("Error, invalid max_drones value")
                    if max_drones < 0:
                        raise ValueError("Error, max_drones can't be negative")   

        return self

# class ValidData(BaseModel):
#     drone_count: int = Field(ge=1)
#     start_hub = dict[str, Any]


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
            print(f"Error, {self.filename} was not found")
            return

        for line in lines:
            if not line or line.startswith("#"):
                continue
            if line.startswith("nb_drones:"):
                self.drone_count = int(line.split(':')[1])
            elif line.startswith("connection"):
                self.connections.append(line.split(':')[1])
            elif "hub" in line:
                key, value = line.split(':')                  
                self.hubs.append({key:value})

        for item in self.hubs:
            raw_string = list(item.values())[0]
            parts = [p.strip() for p in raw_string.split(",")]

            if len(parts) < 3:
                print(f"Error: Invalid hub format for string: '{raw_string}'")
                continue

            name = parts[0]
            x = int(parts[1])
            y = int(parts[2])

            metadata = parts[3:] if len(parts) > 3 else None

            try:
                hub_object = HubModel(name=name, x=x, y=y, metadata=metadata)
                print(f"Successfully validated hub: {hub_object.name}")
                
            except (ValidationError, ValueError) as e:
                print(f"Validation failed for hub '{name}':")
                print(e)


        # print(self.hubs)


if __name__ == "__main__":
    map_parser = MapParser("map.txt")
    map_parser.parse()

# Responsibilities:

# open file
# iterate through lines
# determine line type
# create objects
# return a complete graph