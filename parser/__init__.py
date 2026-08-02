"""Public interface for the parser package."""
from parser.models import MapModel, HubModel, ConnectionModel
from parser.parser import MapParser

__all__ = ["MapModel", "HubModel", "ConnectionModel", "MapParser"]
