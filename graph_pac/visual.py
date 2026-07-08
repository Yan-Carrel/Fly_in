import pygame
from pygame.locals import (QUIT)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph_pac.graph_cls import Graph


class Visual:
    def __init__(self, win_x: int, win_y: int, background_color: str, hubs: list["Graph"], margin: int)  -> None:
        self.hubs = hubs
        self.margin = margin
        self.map_x, self.map_y = self.map_size(hubs, margin)
        self.win_x, self.win_y = (win_x, win_y)
        self.tile = self.tile_size()
        self.background_color = background_color
        self.running = True

    def initialize_pygame(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode([self.win_x, self.win_y])

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill("black")
            self.draw_hubs()
            pygame.display.flip()
        pygame.quit()

    def map_size(self, hubs: list["Graph"], margin: int) -> tuple[int, int]:
        min_x = min(hubs, key=lambda h: h.x).x
        min_y = min(hubs, key=lambda h: h.y).y
        max_x = max(hubs, key=lambda h: h.x).x
        max_y = max(hubs, key=lambda h: h.y).y

        map_width = max_x - min_x
        map_height = max_y - min_y

        return (map_width, map_height)
    
    def tile_size(self) -> None:
        usable_width = self.win_x - (self.margin * 2)
        usable_height = self.win_y - (self.margin * 2)
        tile_x = usable_width // self.map_x
        tile_y = usable_height // self.map_y

        return min(tile_x, tile_y)
    
    def draw_hubs(self) -> None:
        for hub in self.hubs:
            center_x = hub.x * self.tile + self.margin
            center_y = hub.y * self.tile + self.margin
            radius = max(1, self.tile // 3)
            pygame.draw.circle(self.screen, "white", (center_x, center_y), radius, 0)

    # def draw_connections(
    #     color: str, start_por: tuple[int, int],
    #     end_pos: tuple(int, int), width: int,
    #     connections: graph_pac.mode.ConnectionModel
    #         ) -> None:
