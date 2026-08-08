"""Pygame engine that drives the turn-based drone simulation loop."""
import os
import sys
import pygame
from .visual import Visual


class Engine:
    """Own the pygame window, main loop, and turn/frame timing.

    Coordinates when a simulation turn advances (based on elapsed frames),
    delegating all drawing and per-drone state to the attached ``Visual``
    instance.
    """

    def __init__(
        self,
        background_color: str | tuple[int, int, int] | None, visual: Visual
            ) -> None:
        """Store the background color and the ``Visual`` to render each frame.

        Parameters
        ----------
        background_color : str | tuple[int, int, int] | None
            Color name for the window background, ``"rainbow"`` for a
            fixed accent color, or ``None`` to fall back to a default.
        visual : Visual
            The visual layer responsible for drawing hubs, connections,
            and drones.
        """
        if background_color is None:
            background_color = "black"

        self.background_color: str | tuple[int, int, int] = background_color
        if self.background_color == "rainbow":
            self.background_color = (255, 127, 80)
        self.running = True
        self.visual = visual
        self.frame = 0
        self.previous_frame = 0
        self.frames_per_turn = 600
        self.turn = 1

    def initialize_pygame(self) -> None:
        """Set up the pygame window, drone assets, and per-drone initial state.

        Reads window dimensions from the environment (falling back to the
        monitor's full resolution/fullscreen mode if unset or invalid),
        builds the layout, seeds every drone's starting position at the
        start hub, and precomputes how many drones move on each turn.
        """
        pygame.init()
        monitor_info = pygame.display.Info()

        desktop_width = monitor_info.current_w
        desktop_height = monitor_info.current_h

        fullscreen = os.getenv("FULLSCREEN", "FALSE").upper() == "TRUE"

        if fullscreen:
            width = desktop_width
            height = desktop_height

            self.visual.win_width = width
            self.visual.win_height = height
            self.visual.build_layout()

            self.screen = pygame.display.set_mode(
                (width, height),
                pygame.FULLSCREEN
            )
        else:
            width = int(desktop_width * 0.7)
            height = int(desktop_height * 0.7)

            self.visual.win_width = width
            self.visual.win_height = height
            self.visual.build_layout()

            self.screen = pygame.display.set_mode((width, height))

        layout = self.visual.layout
        assert layout is not None

        for i in range(self.visual.drone_count + 1):
            start_hub = self.visual.graph.get_hub("start")
            self.visual.drone_position[i] = layout.position(
                (start_hub.x, start_hub.y))
            self.visual.drone_t[i] = 0.0
            self.visual.drone_target[i] = start_hub
            self.visual.drone_move_duration[i] = 1
            self.visual.drone_finished_move[i] = True
            self.visual.drone_turns_elapsed[i] = 0

        routes = self.visual.formatted_routes
        assert routes is not None
        for turn, moves in routes.items():
            self.visual.nb_of_drone_moved[turn] = len(moves)

        self.visual.pygame = pygame
        self.visual.pygame_font = pygame.font.SysFont("None", 20)
        try:
            self.drone_img = pygame.image.load("drone.png")
        except FileNotFoundError:
            print("Error, drone.img file not found.")
            sys.exit(0)
        self.small_img = pygame.transform.scale(self.drone_img, (20, 20))

    def run(self) -> None:
        """Run the main event/render loop until the window is closed."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_t:
                        if self.visual.display_all_labels:
                            self.visual.display_all_labels = False
                        else:
                            self.visual.display_all_labels = True
            mouse_pos = pygame.mouse.get_pos()

            routes = self.visual.formatted_routes
            assert routes is not None
            if self.frame == 1:
                print(" ".join(routes[self.turn]))
            self.frame += 1

            self.screen.fill(self.background_color)
            self.render(mouse_pos)
            pygame.display.flip()
        pygame.quit()

    def render(self, mouse_pos: tuple[int, int]) -> None:
        """Advance the turn if enough frames have elapsed, then draw frame.

        Turn advancement ticks forward any drones mid multi-turn move and
        finalizes their position once their move duration is reached,
        before incrementing ``self.turn``. Drawing always happens every
        frame regardless of whether a turn boundary was crossed.
        """
        if self.frame == self.previous_frame + self.frames_per_turn:
            self.previous_frame = self.frame

            visual = self.visual
            layout = visual.layout
            assert layout is not None
            routes = visual.formatted_routes
            assert routes is not None

            for i in range(1, visual.drone_count + 1):
                if visual.drone_finished_move[i]:
                    continue

                visual.drone_turns_elapsed[i] += 1
                elapsed = visual.drone_turns_elapsed[i]
                duration = visual.drone_move_duration[i]

                if elapsed < duration:
                    continue

                visual.drone_finished_move[i] = True
                target_hub = visual.drone_target[i]
                visual.drone_position[i] = layout.position(
                    (target_hub.x, target_hub.y)
                )

            if self.turn < len(routes):
                self.turn += 1
                print(" ".join(routes[self.turn]))

        routes = self.visual.formatted_routes
        assert routes is not None
        win_width = self.visual.win_width
        win_height = self.visual.win_height
        assert win_width is not None
        assert win_height is not None

        self.visual.draw_hubs(mouse_pos, self.turn, self.screen)
        self.visual.draw_connections(self.screen)
        self.visual.draw_drones(
            self.screen, self.small_img, self.turn,
            self.frames_per_turn, self.previous_frame, self.frame)
        pygame.draw.rect(
            self.screen,
            (28, 32, 38),
            (0, 0, win_width, 90))
        pygame.draw.line(
            self.screen,
            (90, 90, 90),
            (0, 90),
            (win_width, 90),
            2
        )
        self.visual.simulation_text(
            self.turn, len(routes), self.screen)
