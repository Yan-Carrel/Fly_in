import pygame
from pygame.locals import (QUIT)


class Visual:
    def __init__(self, win_x: int, win_y: int, background_color: str, graph: "Graph", margin: int)  -> None:
        self.graph = graph
        self.connections = graph.connections
        self.margin = margin
        self.map_x, self.map_y = self.map_size(margin)
        self.offset = self.add_offset()
        self.win_x, self.win_y = (win_x, win_y)
        self.tile = self.tile_size()
        self.background_color = background_color
        self.running = True

    def initialize_pygame(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode([self.win_x, self.win_y])
    
    def add_offset(self) -> None:
        neg_x_values = min(self.graph.hubs, key=lambda hub: hub.x).x
        neg_y_values = min(self.graph.hubs, key=lambda hub: hub.y).y
        offset_x = 0
        offset_y = 0

        if neg_x_values >= 0:
            offset_x = 0
        else:
            offset_x = neg_x_values * (-1)

        if neg_y_values >= 0:
            offset_y = 0
        else:
            offset_y = neg_y_values * (-1)

        for hub in self.graph.hubs:
            hub.x += offset_x
            hub.y += offset_y

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill(self.background_color)
            self.draw_connections()
            self.draw_hubs()
            pygame.display.flip()
        pygame.quit()

    def map_size(self, margin: int) -> tuple[int, int]:
        min_x = min(self.graph.hubs, key=lambda h: h.x).x
        min_y = min(self.graph.hubs, key=lambda h: h.y).y
        max_x = max(self.graph.hubs, key=lambda h: h.x).x
        max_y = max(self.graph.hubs, key=lambda h: h.y).y

        map_width = max_x - min_x
        map_height = max_y - min_y

        return (map_width, map_height)
    
    def tile_size(self) -> None:
        usable_width = self.win_x
        usable_height = self.win_y
        tile_x = usable_width // self.map_x
        tile_y = usable_height // self.map_y

        return min(tile_x, tile_y)
    
    def draw_hubs(self) -> None:
        for hub in self.graph.hubs:
            if "color" in hub.metadata:
                color = hub.metadata["color"]
            else:
                color = "white"
            center_x, center_y = self.hub_position(hub.x, hub.y)
            radius = max(1, self.tile // 3)
            pygame.draw.circle(self.screen, color, (center_x, center_y), radius, 0)

    def draw_connections(self) -> None:
        drawn_edges: set[tuple[str, str]] = set()

        for name, neighbors in self.graph.connections.items():
            start_hub = next(hub for hub in self.graph.hubs if hub.name == name)
            start_pos = self.hub_position(start_hub.x, start_hub.y)

            for target in self.graph.connections[name]:
                edge = tuple(sorted((name, target)))
                if edge in drawn_edges:
                    continue

                target_hub = next(hub for hub in self.graph.hubs if hub.name == target)
                target_pos = self.hub_position(target_hub.x, target_hub.y)
                pygame.draw.line(self.screen, "white", start_pos, target_pos, 2)
                drawn_edges.add(edge)

    def hub_position(self, x: int, y: int) -> tuple[int, int]:
        return (x * self.tile, y * self.tile)
