import pygame
from pygame.locals import (
    QUIT,
    K_ESCAPE
    )
from .graph_cls import Graph
from .visual import Visual
import os


class Engine:
    def __init__(self, background_color: str, visual: Visual)  -> None:
        self.background_color = background_color
        if self.background_color == "rainbow":
            self.background_color = (255, 127, 80)
        self.running = True
        self.visual = visual

    def initialize_pygame(self) -> None:
        pygame.init()
        monitor_info = pygame.display.Info()

        try:
            self.visual.win_width = int(os.getenv("WINDOW_WIDTH"))
            self.visual.win_height = int(os.getenv("WINDOW_HEIGHT"))
            self.visual.build_layout()
            self.screen = pygame.display.set_mode([self.visual.win_width, self.visual.win_height])
        except Exception:
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
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_ESCAPE:
                        self.running = False

            self.screen.fill(self.background_color)
            self.render()
            pygame.display.flip()
        pygame.quit()
    
    def render(self) -> None:
        self.visual.draw_hubs(self.screen)
        self.visual.draw_connections(self.screen)
