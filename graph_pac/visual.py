"""Rendering layer for the drone simulation."""
from types import ModuleType
from typing import Optional

import pygame

from parser import HubModel
from .graph_cls import Graph


class Visual:
    """Class responsible for all display-related tasks."""

    def __init__(
        self, graph: Graph,
        target_min_gap: int,
        margin: int,
            ) -> None:
        """Set up layout parameters and initialize class.

        Parameters
        ----------
        graph : Graph
            The map graph (hubs and connections) to render.
        target_min_gap : int
            Minimum pixel gap to maintain between rendered targets/labels.
        margin : int
            Pixel margin around the drawing canvas.
        """
        self.target_min_gap = target_min_gap
        self.graph = graph
        self.margin = margin
        self.win_width: Optional[int] = None
        self.win_height: Optional[int] = None
        self.layout: Optional[Layout] = None
        self.pygame: Optional[ModuleType] = None
        self.pygame_font: Optional[pygame.font.Font] = None
        self.formatted_routes: Optional[dict[int, list[str]]] = None
        self.drone_count = 0
        self.hub_states: dict[int, dict[str, int]] = {}
        self.drone_position: dict[int, tuple[float, float]] = {}
        self.drone_t: dict[int, float] = {}
        self.drone_target: dict[int, HubModel] = {}
        self.drone_move_duration: dict[int, int] = {}
        self.drone_finished_move: dict[int, bool] = {}
        self.drone_turns_elapsed: dict[int, int] = {}
        self.nb_of_drone_moved: dict[int, int] = {}
        self.total_cost = 0
        self.average_turn = 0.0
        self.display_all_labels = False
        self.draw_labels = [
            self.graph.start_hub.name, self.graph.end_hub.name]

    def _require_layout(self) -> "Layout":
        """Return the built layout, or raise if it isn't ready yet."""
        if self.layout is None:
            raise ValueError("Layout has not been built")
        return self.layout

    def _require_pygame(self) -> ModuleType:
        """Return the pygame module, or raise if it hasn't been attached."""
        if self.pygame is None:
            raise ValueError("pygame has not been attached to Visual")
        return self.pygame

    def _require_font(self) -> pygame.font.Font:
        """Return the font, or raise if it hasn't been initialized."""
        if self.pygame_font is None:
            raise ValueError("Font has not been initialized")
        return self.pygame_font

    def _require_routes(self) -> dict[int, list[str]]:
        """Return formatted_routes, or raise if it hasn't been set."""
        if self.formatted_routes is None:
            raise ValueError("formatted_routes has not been set")
        return self.formatted_routes

    def build_layout(self) -> None:
        """Instantiate and compute the layout that will be used."""
        if self.win_width is None or self.win_height is None:
            raise ValueError(
                "Window size must be set before building the layout")

        self.layout = Layout(
            self.graph,
            self.win_width,
            self.win_height,
            self.margin,
        )

    def simulation_text(
        self, turn: int, turns: int,
        screen: pygame.Surface
            ) -> None:
        """Responsible for displaying statistics and metrics."""
        pg = self._require_pygame()
        self.display_text(
            "Simulation", (50, 10),
            "TL", "white", screen)
        pg.draw.line(
            screen,
            (255, 255, 255),
            (40, 27),
            (830, 27),
            2
        )

        self.display_text(
            "Key inputs", (750, 10),
            "TL", "white", screen)
        self.display_text(
            "Escape - Quit", (750, 30),
            "TL", "white", screen)
        self.display_text(
            "T - Toggle display labels", (750, 50),
            "TL", "white", screen)

        self.display_text(
            "Performance", (400, 10),
            "TL", "white", screen)
        self.display_text(
            f"Turns: {turn}/{turns}", (50, 30),
            "TL", "white", screen)
        self.display_text(
            f"Number of drones moved: {self.nb_of_drone_moved[turn]}",
            (50, 50), "TL", "white", screen)
        self.display_text(
            f"Total drones: {self.drone_count}",
            (50, 70), "TL", "white", screen)
        self.display_text(
            f"Total cost: {self.total_cost}",
            (400, 30), "TL", "white", screen)
        self.display_text(
            f"Average turn: {self.average_turn}",
            (400, 50), "TL", "white", screen)

    def display_text(
        self, text: str, pos: tuple[float, float],
        anchor: str, color: str, screen: pygame.Surface
            ) -> None:
        """Responsible for displaying text at (x, y) coordinates."""
        font = self._require_font()
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        int_pos = (int(pos[0]), int(pos[1]))

        if anchor == "TL":
            text_rect.topleft = int_pos
        elif anchor == "MT":
            text_rect.midtop = int_pos
        elif anchor == "MB":
            text_rect.midbottom = int_pos

        screen.blit(text_surface, text_rect)

    def draw_hubs(
        self, mouse_pos: tuple[int, int],
        turn: int, screen: pygame.Surface
            ) -> None:
        """Draw every hub as a circle and label with name and occupancy."""
        layout = self._require_layout()
        pg = self._require_pygame()

        for hub in self.graph.hubs:
            center_x, center_y = layout.position((hub.x, hub.y))
            circle_radius = 6
            ver_dst = (mouse_pos[1] - center_y) ** 2
            hor_dst = (mouse_pos[0] - center_x) ** 2
            distance_squared = hor_dst + ver_dst
            radius_squared = circle_radius ** 2

            pg.draw.circle(
                screen, self._hub_color(hub),
                (center_x, center_y), circle_radius, 0)
            if (
                hub.name in self.draw_labels or self.display_all_labels or
                distance_squared <= radius_squared
                    ):
                self.display_text(
                    hub.name, (center_x, center_y - circle_radius),
                    "MB", "white", screen)

            self.display_text(
                self._occupancy_label(hub, turn),
                (center_x + 10, center_y + circle_radius + 10),
                "MT", "white", screen)

    def _hub_color(self, hub: HubModel) -> str | tuple[int, int, int]:
        """Return the hub's display color, resolving 'rainbow' color issue."""
        metadata = hub.metadata or {}
        color = metadata.get("color", "white")
        return (255, 127, 80) if color == "rainbow" else color

    def _occupancy_label(self, hub: HubModel, turn: int) -> str:
        """Return a 'current/max' occupancy string at the given turn."""
        metadata = hub.metadata or {}
        max_drones = metadata.get("max_drones", "?")
        drones_in_hub = self.hub_states.get(turn, {}).get(hub.name, 0)
        return f"{drones_in_hub}/{max_drones}"

    def draw_drones(
        self, screen: pygame.Surface, surface: pygame.Surface, turn: int,
        frames_per_turn: int, previous_frame: int, frame: int
            ) -> None:
        """Draw every drone at its current interpolated position.

        For each drone, checks whether it needs a new target (only once its
        previous move has finished), then linearly interpolates its position
        between where it started and its current target hub, using
        ``drone_t[i]`` as the interpolation fraction (0 = still at origin,
        1 = arrived). Also labels each drone with its id, or with an
        occupancy count if it shares a hub with other drones.
        """
        turn_moves = self._require_routes()[turn]
        elapsed = frame - previous_frame

        for i in range(1, self.drone_count + 1):
            if self.drone_finished_move[i]:
                self._assign_next_move(i, turn_moves)

            self._advance_interpolation(i, elapsed, frames_per_turn)
            x, y = self._interpolated_position(i)

            self.draw_drone((x, y), (20, 20), screen, surface)
            self._label_drone(i, turn, x, y, screen)

    def _assign_next_move(self, drone_id: int, turn_moves: list[str]) -> None:
        """Look up this drone's move for the current turn and track it."""
        next_move = next(
            (
                move for move in turn_moves if (
                    f"D{drone_id}" == move.split("-")[0])
                    ), None
                )
        if not next_move:
            return

        parts = next_move.split("-")
        self.drone_target[drone_id] = self.graph.get_hub(parts[-1])
        self.drone_move_duration[drone_id] = 2 if len(parts) > 2 else 1
        self.drone_turns_elapsed[drone_id] = 0
        self.drone_finished_move[drone_id] = False

    def _advance_interpolation(
        self, drone_id: int, elapsed: int,
        frames_per_turn: int
            ) -> None:
        """Update position relative to its current move this drone is."""
        duration = self.drone_move_duration[drone_id]
        turns_elapsed = self.drone_turns_elapsed[drone_id]
        total_elapsed = turns_elapsed * frames_per_turn + elapsed
        self.drone_t[drone_id] = min(
            total_elapsed / (frames_per_turn * duration), 1.0
            )

    def _interpolated_position(self, drone_id: int) -> tuple[float, float]:
        """Compute current (x, y) between origin and target hub."""
        layout = self._require_layout()
        target_hub = self.drone_target[drone_id]
        target_position = layout.position((target_hub.x, target_hub.y))
        start_x, start_y = self.drone_position[drone_id]
        t = self.drone_t[drone_id]

        x = start_x + t * (target_position[0] - start_x)
        y = start_y + t * (target_position[1] - start_y)
        return x, y

    def _label_drone(
        self, drone_id: int, turn: int, x: float,
        y: float, screen: pygame.Surface
            ) -> None:
        """Draw the drone's id."""
        is_settled = self.drone_finished_move[drone_id]
        current_hub = self.drone_target[drone_id]
        drones_in_hub = self.hub_states[turn].get(current_hub.name, 0)

        if not is_settled or drones_in_hub == 1:
            self.display_text(
                f"D{drone_id}", (x, y), "MB", "green", screen)

    def draw_drone(
        self, pos: tuple[float, float],
        size: tuple[int, int], screen: pygame.Surface,
        surface: pygame.Surface
            ) -> None:
        """Display the image of a drone at (x, y) coordinates."""
        screen.blit(surface, pos)

    def draw_connections(self, screen: pygame.Surface) -> None:
        """Draw the connections between hubs."""
        layout = self._require_layout()
        pg = self._require_pygame()

        drawn_lines = []
        for key in self.graph.connections:
            start_pos = layout.position(next(
                (hub.x, hub.y) for hub in self.graph.hubs
                if hub.name == key))
            for end_pos in self.graph.connections[key]:
                target_pos = layout.position(next(
                    (hub.x, hub.y) for hub in self.graph.hubs
                    if hub.name == end_pos))
                if sorted([start_pos, target_pos]) in drawn_lines:
                    continue

                target_hub = self.graph.get_hub(end_pos)
                metadata = target_hub.metadata or {}
                color = "red" if metadata.get("zone") == "restricted" \
                    else "white"

                pg.draw.line(screen, color, start_pos, target_pos, 1)
                drawn_lines.append(sorted([start_pos, target_pos]))


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
        if min_y != 0:
            offset_y -= min_y * self.scale

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
        """Convert x, y coordinates by adding computed scale and offsets."""
        x = pos[0] * self.scale + self.offset_x
        y = pos[1] * self.scale + self.offset_y
        return x, y
