"""Pydantic models used to validate maps, hubs, and connections."""
from typing import Any, Optional, Self
from pydantic import BaseModel, Field, model_validator


class HubModel(BaseModel):
    """Validated hub definition with coordinates and optional metadata."""

    name: str = Field(min_length=1)
    x: int = Field(...)
    y: int = Field(...)
    metadata: Optional[dict[str, Any]] = Field(default=None)

    @model_validator(mode='after')
    def validade_hub(self) -> Self:
        """Validate hub metadata and apply the default capacity."""
        valid_metadatas = ["zone", "color", "max_drones"]
        valid_zones = ["normal", "blocked", "restricted", "priority"]

        if self.metadata:
            if "max_drones" not in self.metadata:
                self.metadata["max_drones"] = 1
            for key, value in self.metadata.items():
                if key not in valid_metadatas:
                    raise ValueError(
                        "zone, color and max_drones are"
                        " the only valid metadata"
                        )

                if key == "zone" and value not in valid_zones:
                    raise ValueError(
                        "Error: normal, blocked, "
                        "restricted and priority are the only valid zones"
                        )

                elif key == "color":
                    if not isinstance(value, str) or not value or \
                            any(character.isspace() for character in value):
                        raise ValueError(
                            "Error: color must be a non-empty single-word "
                            "value"
                        )

                elif key == "max_drones":
                    try:
                        max_drones = int(value)
                    except Exception:
                        raise ValueError("Error: invalid max_drones value")
                    if max_drones <= 0:
                        raise ValueError(
                            "Error: max_drones "
                            "can't be negative or equal to 0."
                            )
        else:
            self.metadata = {"max_drones": 1}
        return self


class ConnectionModel(BaseModel):
    """Validated connection with its maximum traversal capacity."""

    connection: str = Field(min_length=1)
    metadata: Optional[int] = Field(default=1)

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        """Validate the connection format and positive capacity."""
        if "-" not in self.connection:
            raise ValueError(
                "Error: Invalid format. Usage: "
                "connection: <name1>-<name2> <metadata>"
                )
        if self.metadata is not None and self.metadata <= 0:
            raise ValueError(
                "Error: Metadata 'max_link_capacity' "
                "must be a positive integer"
                )

        try:
            name1, name2 = self.connection.split("-")
        except Exception as e:
            raise ValueError(f"Error invalid format: {e}")
        if not name1 or not name2 or name1 == name2:
            raise ValueError(f"Error: Invalid connection '{self.connection}'")
        return self


class MapModel(BaseModel):
    """Validated map containing hubs, connections, and drone count."""

    drone_count: int = Field(ge=1)
    start_hub: HubModel = Field(...)
    end_hub: HubModel = Field(...)
    hubs: list[HubModel] = Field(...)
    connections: list[ConnectionModel] = Field(...)

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        """Ensure every connection refers to a declared hub."""
        for connection in self.connections:
            name1, name2 = connection.connection.split("-")
            if not any(name1 == hub.name for hub in self.hubs):
                raise ValueError(f"Hub with name '{name1}' is not recognized")
            if not any(name2 == hub.name for hub in self.hubs):
                raise ValueError(f"Hub with name '{name2}' is not recognized")
        return self
