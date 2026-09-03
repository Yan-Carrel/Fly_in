"""Coordinate and sizing calculations for the graph visualization."""

from .graph_cls import Graph


class Layout:
    """Compute layout that will be used in Visual class."""

    def __init__(
        self, graph: Graph, win_width: int,
        win_height: int, margin: int
            ) -> None:
        """Initialize with all informations needed."""
        self.graph = graph
        self.win_width = win_width
        self.win_height = win_height
        self.margin = margin
        self.x_ranks = self._coordinate_ranks("x")
        self.y_ranks = self._coordinate_ranks("y")
        self.scale_x, self.scale_y = self.compute_scale()
        self.offset_x, self.offset_y = self.offset()

    def _coordinate_ranks(self, coordinate: str) -> dict[int, int]:
        """Map each distinct coordinate to its sorted zero-based rank."""
        values = sorted({getattr(hub, coordinate) for hub in self.graph.hubs})
        return {value: rank for rank, value in enumerate(values)}

    def map_bounds(self) -> tuple[int, int, int, int]:
        """Return the (x, y) values related to the map bounds."""
        hubs = self.graph.hubs
        min_x = min(hubs, key=lambda hub: hub.x).x
        min_y = min(hubs, key=lambda hub: hub.y).y
        max_x = max(hubs, key=lambda hub: hub.x).x
        max_y = max(hubs, key=lambda hub: hub.y).y

        return (max_x, min_x, max_y, min_y)

    def canvas_size(self) -> tuple[int, int]:
        """Get the size of the canvas after adding margins."""
        return (
            self.win_width - (self.margin * 2),
            self.win_height - (self.margin * 2)
            )

    def offset(self) -> tuple[float, float]:
        """Return the offsets that will be applied to center coordinates."""
        graph_width, graph_height = self.graph_size()
        offset_x = (self.win_width - graph_width) / 2
        offset_y = (self.win_height - graph_height) / 2

        return offset_x, offset_y

    def compute_scale(self) -> tuple[float, float]:
        """Compute appropriate scale to help the screen to fit the window."""
        canvas_width, canvas_height = self.canvas_size()
        x_span = len(self.x_ranks) - 1
        y_span = len(self.y_ranks) - 1

        scale_a = canvas_width / x_span if x_span else 0
        scale_b = canvas_height / y_span if y_span else 0

        return scale_a, scale_b

    def graph_size(self) -> tuple[float, float]:
        """Return the size of the graph."""
        scale = self.compute_scale()

        x_span = len(self.x_ranks) - 1
        y_span = len(self.y_ranks) - 1
        graph_width = x_span * scale[0]
        graph_height = y_span * scale[1]

        return graph_width, graph_height

    def position(self, pos: tuple[int, int]) -> tuple[float, float]:
        """Convert normalized coordinates with positive Y pointing upward."""
        x = self.x_ranks[pos[0]] * self.scale_x + self.offset_x
        y = -self.y_ranks[pos[1]] * self.scale_y + self.offset_y
        return x, y
