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
        self.frame = 0
        self.previous_frame = 0
        self.frames_per_turn = 300
        self.turn = 1

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

        for i in range(self.visual.drone_count + 1):
            start_hub = self.visual.graph.get_hub("start")
            self.visual.drone_position[i] = self.visual.layout.position((start_hub.x, start_hub.y))
            self.visual.drone_t[i] = 0
            self.visual.drone_target[i] = self.visual.graph.get_hub("start")

        self.visual.pygame = pygame
        self.visual.pygame_font = self.visual.pygame.font.SysFont("None", 20)
        self.drone_img = self.visual.pygame.image.load("drone.png")
        self.small_img = pygame.transform.scale(self.drone_img, (20, 20))


    def run(self):
        previous_frame = 0
        frame = 0
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_ESCAPE:
                        self.running = False

            self.frame += 1

            self.screen.fill(self.background_color)
            self.render()
            pygame.display.flip()
        pygame.quit()
    
    def render(self) -> None:
        self.visual.draw_hubs(self.screen)
        self.visual.draw_connections(self.screen)

        if self.frame == self.previous_frame + self.frames_per_turn:
            if self.turn < len(self.visual.formatted_routes):
                self.previous_frame = self.frame
                self.turn += 1
                for i in range(1, self.visual.drone_count + 1):
                    self.visual.drone_t[i] = 0
                    self.visual.drone_position[i] = self.visual.layout.position(
                        (self.visual.drone_target[i].x, self.visual.drone_target[i].y)
                    )

        self.visual.draw_drones(self.screen, self.small_img, self.turn, self.frames_per_turn, self.previous_frame, self.frame)
