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
        self.screen = pygame.display.set_mode([1080, 720])

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill(self.background_color)
            self.render(pygame)
            pygame.display.flip()
        pygame.quit()
    
    def render(self, pygame: "pygame") -> None:
        self.visual.draw_hubs(pygame, self.screen)
