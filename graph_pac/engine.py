import pygame
from pygame.locals import (QUIT)
from .graph_cls import Graph
from .visual import Visual


class Engine:
    def __init__(self, background_color: str, visual: Visual)  -> None:
        self.background_color = background_color
        self.running = True
        self.visual = visual

    def initialize_pygame(self) -> None:
        pygame.init()
        # pygame.font.init()
        monitor_info = pygame.display.Info()
        self.visual.win_width = monitor_info.current_w
        self.visual.win_height = monitor_info.current_h
        self.visual.build_layout()
        self.screen = pygame.display.set_mode((monitor_info.current_w, monitor_info.current_h), pygame.FULLSCREEN)
        self.visual.pygame = pygame
        self.visual.pygame_font = self.visual.pygame.font.SysFont("None", 20)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill(self.background_color)
            self.render()
            pygame.display.flip()
        pygame.quit()
    
    def render(self) -> None:
        self.visual.draw_hubs(self.screen)
        self.visual.draw_connections(self.screen)
