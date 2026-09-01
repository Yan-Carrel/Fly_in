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
        self.scale = self.compute_scale()
        self.offset_x, self.offset_y = self.offset()

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

        max_x, min_x, max_y, min_y = self.map_bounds()

        if min_x != 0:
            offset_x -= min_x * self.scale
        offset_y += max_y * self.scale

        return offset_x, offset_y

    def compute_scale(self) -> float:
        """Compute appropriate scale to help the screen to fit the window."""
        max_x, min_x, max_y, min_y = self.map_bounds()
        canvas_width, canvas_height = self.canvas_size()

        try:
            scale_a = canvas_width / (max_x - min_x)
        except ZeroDivisionError:
            scale_a = canvas_width
        try:
            scale_b = canvas_height / (max_y - min_y)
        except ZeroDivisionError:
            scale_b = canvas_height

        return min(scale_a, scale_b)

    def graph_size(self) -> tuple[float, float]:
        """Return the size of the graph."""
        max_x, min_x, max_y, min_y = self.map_bounds()
        scale = self.compute_scale()

        graph_width = (max_x - min_x) * scale
        graph_height = (max_y - min_y) * scale

        return graph_width, graph_height

    def position(self, pos: tuple[int, int]) -> tuple[float, float]:
        """Convert map coordinates with positive Y pointing upward."""
        x = pos[0] * self.scale + self.offset_x
        y = -pos[1] * self.scale + self.offset_y
        return x, y
