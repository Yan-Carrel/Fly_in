import pygame
from typing import Optional
from parser import HubModel
from .graph_cls import Graph


class Visual:
    def __init__(
        self, graph: Graph,
        target_min_gap: int,
        margin: int,
        ) -> None:
        self.target_min_gap = target_min_gap
        self.graph = graph
        self.margin = margin
        self.win_width = None
        self.win_height = None
        self.layout: Optional[Layout] = None
        self.pygame: Optional[pygame] = None
        self.pygame_font: Optional[pygame.font.SysFont] = None

    def build_layout(self) -> None:
        if self.win_width is None or self.win_height is None:
            raise ValueError("Window size must be set before building the layout")

        self.layout = Layout(
            self.graph,
            self.win_width,
            self.win_height,
            self.margin,
        )
    
    def draw_hubs(self, screen: "screen") -> None:
        if self.layout is None:
            raise ValueError("Layout has not been built")

        scale = self.layout.scale

        for hub in self.graph.hubs:
            center_x, center_y = self.layout.hub_position(hub)
            circle_radius = 6

            if "color" in hub.metadata:
                color = hub.metadata["color"]
                if color == "rainbow":
                    color = (255, 127, 80)
            else:
                color = "white"
            self.pygame.draw.circle(screen, color, (center_x, center_y), circle_radius, 0)

            added_labels = []
            text_surface = self.pygame_font.render(hub.name, True, "white")
            text_rect = text_surface.get_rect()
            text_rect.midbottom = (center_x, center_y - circle_radius)
            screen.blit(text_surface, text_rect)

    def draw_connections(self, screen: "screen") -> None:
        if self.layout is None:
            raise ValueError("Layout has not been built")

        drawn_lines = []
        for key in self.graph.connections:
            start_pos = self.layout.hub_position(next(hub for hub in self.graph.hubs if hub.name == key))
            for end_pos in self.graph.connections[key]:
                target_pos = self.layout.hub_position(next(hub for hub in self.graph.hubs if hub.name == end_pos))
                if sorted([start_pos, target_pos]) in drawn_lines:
                    continue
                self.pygame.draw.line(screen, "white", start_pos, target_pos, 1)
                drawn_lines.append(sorted([start_pos, target_pos]))


class Layout:
    def __init__(self, graph: Graph, win_width: int, win_height: int, margin: int) -> None:
        self.graph = graph
        self.win_width = win_width
        self.win_height = win_height
        self.margin = margin
        self.scale = self.compute_scale()
        self.offset_x, self.offset_y = self.offset()

    def map_bounds(self) -> tuple[int, int, int, int]:
        hubs = self.graph.hubs
        min_x = min(hubs, key=lambda hub: hub.x).x
        min_y = min(hubs, key=lambda hub: hub.y).y
        max_x = max(hubs, key=lambda hub: hub.x).x
        max_y = max(hubs, key=lambda hub: hub.y).y

        return (max_x, min_x, max_y, min_y)

    def canvas_size(self) -> tuple[int, int]:
        return (
            self.win_width - (self.margin * 2),
            self.win_height - (self.margin * 2)
            )

    def offset(self) -> tuple[int, int]:
        graph_width, graph_height = self.graph_size()
        offset_x = (self.win_width - graph_width) / 2
        offset_y = (self.win_height - graph_height) / 2

        max_x, min_x, max_y, min_y = self.map_bounds()

        if min_x != 0:
            offset_x -= min_x * self.scale
        if min_y != 0:
            offset_y -= min_y * self.scale

        return offset_x, offset_y

    def compute_scale(self) -> None:
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

    def graph_size(self) -> None:
        max_x, min_x, max_y, min_y = self.map_bounds()
        scale = self.compute_scale()

        graph_width = (max_x - min_x) * scale
        graph_height = (max_y - min_y) * scale

        return graph_width, graph_height
    
    def hub_position(self, hub: HubModel) -> tuple[int, int]:
        x = hub.x * self.scale + self.offset_x
        y = hub.y * self.scale + self.offset_y
        return x, y
