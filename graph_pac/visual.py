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
        self.formatted_routes: Optional[list[str]] = None
        self.drone_count = 0
        self.hub_states = {}
        self.drone_position: dict[int, tuple[int, int]] = {}
        self.drone_t: dict[int, tuple[int, int]] = {}
        self.drone_target: dict[int, tuple[int, int]] = {}
        self.drone_move_duration: dict[int, int] = {}
        self.drone_finished_move: dict[int, int] = {}
        self.drone_turns_elapsed: dict[int, int] = {}
        self.nb_of_drone_moved: dict[int, int] = {}
        self.total_cost = 0
        self.average_turn = 0
        self.hub_states = {}

    def build_layout(self) -> None:
        if self.win_width is None or self.win_height is None:
            raise ValueError("Window size must be set before building the layout")

        self.layout = Layout(
            self.graph,
            self.win_width,
            self.win_height,
            self.margin,
        )

    def simulation_text(self, turn: int, turns: int, screen) -> None:
        self.display_text(f"Turns: {turn}/{turns}", (50, 10), "TL", "white", screen)
        self.display_text(f"Total drones: {self.drone_count}", (50, 30), "TL", "white", screen)
        self.display_text(f"Number of drones moved: {self.nb_of_drone_moved[turn]}", (50, 50), "TL", "white", screen)
        self.display_text(f"Total cost: {self.total_cost}", (50, 70), "TL", "white", screen)
        self.display_text(f"Average turn: {self.average_turn}", (50, 90), "TL", "white", screen)

    def display_text(self, text: str, pos: tuple[int, int], anchor: str, color: str, screen) -> None:
        text_surface = self.pygame_font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if anchor == "TL":
            text_rect.topleft = pos
        elif anchor == "MT":
            text_rect.midtop = pos
        elif anchor == "MB":
            text_rect.midbottom = pos

        screen.blit(text_surface, text_rect)

    def draw_hubs(self, turn: int, screen: "screen") -> None:
        if self.layout is None:
            raise ValueError("Layout has not been built")

        scale = self.layout.scale

        for hub in self.graph.hubs:
            center_x, center_y = self.layout.position((hub.x, hub.y))
            circle_radius = 6

            if "color" in hub.metadata:
                color = hub.metadata["color"]
                if color == "rainbow":
                    color = (255, 127, 80)
            else:
                color = "white"
            self.pygame.draw.circle(screen, color, (center_x, center_y), circle_radius, 0)

            self.display_text(hub.name, (center_x, center_y - circle_radius), "MB", "white", screen)
            max_drones = self.graph.get_hub(hub.name).metadata["max_drones"]
            try:
                drones_in_hub = self.hub_states[turn][hub.name]
            except KeyError:
                drones_in_hub = 0
            self.display_text(f"{drones_in_hub}/{max_drones}", (center_x + 10, center_y + circle_radius + 10), "MT", "white", screen)

    def draw_drones(self, screen, surface, turn: int, frames_per_turn: int, previous_frame: int, frame: int) -> None:
        turn_moves = self.formatted_routes[turn]
        elapsed = frame - previous_frame

        for i in range(1, self.drone_count + 1):
            if self.drone_finished_move[i]:
                next_move = next((move for move in turn_moves if f"D{i}" == move.split("-")[0]), None)
                if next_move:
                    parts = next_move.split("-")
                    self.drone_target[i] = self.graph.get_hub(parts[-1])
                    self.drone_move_duration[i] = 2 if len(parts) > 2 else 1
                    self.drone_turns_elapsed[i] = 0
                    self.drone_finished_move[i] = False

            target_hub = self.drone_target[i]
            duration = self.drone_move_duration[i]
            total_elapsed = self.drone_turns_elapsed[i] * frames_per_turn + elapsed
            self.drone_t[i] = min(total_elapsed / (frames_per_turn * duration), 1.0)

            target_position = self.layout.position((target_hub.x, target_hub.y))
            x = self.drone_position[i][0] + self.drone_t[i] * (target_position[0] - self.drone_position[i][0])
            y = self.drone_position[i][1] + self.drone_t[i] * (target_position[1] - self.drone_position[i][1])

            self.draw_drone((x, y), (20, 20), screen, surface)
            drones_in_hub = self.hub_states[turn][target_hub.name]
            if drones_in_hub == 1 and self.drone_t[i] < .9 or self.drone_t[i] > .1:
                self.display_text(f"D{i}", (x, y), "MB", "green", screen)
            elif target_hub.name not in [self.graph.end_hub.name, self.graph.start_hub.name]:
                self.display_text(f"{drones_in_hub} drones", (x, y), "MB", "green", screen)

    def draw_drone(self, pos: tuple[int, int], size: tuple[int, int], screen: "screen", surface) -> None:
        screen.blit(surface, pos)

    def draw_connections(self, screen: "screen") -> None:
        if self.layout is None:
            raise ValueError("Layout has not been built")

        drawn_lines = []
        for key in self.graph.connections:
            start_pos = self.layout.position(next((hub.x, hub.y) for hub in self.graph.hubs if hub.name == key))
            for end_pos in self.graph.connections[key]:
                target_pos = self.layout.position(next((hub.x, hub.y) for hub in self.graph.hubs if hub.name == end_pos))
                if sorted([start_pos, target_pos]) in drawn_lines:
                    continue

                target_hub = self.graph.get_hub(end_pos)
                color = "white"
                if "zone" in target_hub.metadata and target_hub.metadata["zone"] == "restricted":
                    color = "red"

                self.pygame.draw.line(screen, color, start_pos, target_pos, 1)
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
    
    def position(self, pos: tuple[int, int]) -> tuple[float, float]:
        x = pos[0] * self.scale + self.offset_x
        y = pos[1] * self.scale + self.offset_y
        return x, y
