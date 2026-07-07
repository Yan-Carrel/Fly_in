import webcolors
from typing import Any, Optional, Self
from pydantic import BaseModel, Field, model_validator


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
    drone_count: int = Field(...)
    start_hub: HubModel = Field(...)
    end_hub: HubModel = Field(...)
    hubs: list[HubModel] = Field(...)
    connections: list[ConnectionModel] = Field(...)

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        for connection in self.connections:
            name1, name2 = connection.connection.split("-")
            if not any(name1 == hub.name for hub in self.hubs):
                raise ValueError(f"Hub with name '{name1}' is not recognized")
            if not any(name2 == hub.name for hub in self.hubs):
                raise ValueError(f"Hub with name '{name2}' is not recognized")
        return self
