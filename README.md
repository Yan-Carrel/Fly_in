*This project has been created as part of the 42 curriculum by yaandria.*

# Fly-in

Fly-in is a Python simulation that routes a fleet of drones from a shared
start zone to a shared end zone across a network of connected zones, while
respecting per-zone and per-connection capacity limits, zone-type movement
costs, and turn-by-turn scheduling constraints. The simulation is rendered
live with a pygame-based visualization.

## Description

Given a map file describing zones ("hubs") and the connections between
them, Fly-in computes, for every drone, a path from the unique start hub to
the unique end hub, then schedules all drones' movements turn by turn so
that:

- No hub is ever occupied by more drones than its `max_drones` capacity
  (except the start and end hubs, which have no such restriction).
- No connection ever carries more simultaneous traversals than its
  `max_link_capacity`.
- `restricted` zones cost two turns to enter instead of one, and a drone
  committed to entering one cannot wait mid-transit — it must arrive on
  the very next turn.
- `blocked` zones can never be entered or passed through.
- The whole fleet reaches the end hub in as few total simulation turns as
  possible.

The result is displayed both as a turn-by-turn textual log and as an
animated graphical simulation.

## Map format

Fly-in reads and validates a text map describing the drone network. Blank lines are ignored, and any line beginning with `#` is treated as a comment.

Each map specifies:

- The number of drones.
- A single start hub and a single end hub.
- Intermediate hubs.
- Directed connections between hubs.
- Optional metadata for both hubs and connections.

A valid map file looks like this:

```text
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

### Comments

Any line beginning with `#` is ignored by the parser and can be used to document the map.

### Hub definitions

Hubs are declared using one of the following keywords:

```text
start_hub: <name> <x> <y> [metadata]
hub: <name> <x> <y> [metadata]
end_hub: <name> <x> <y> [metadata]
```

where:

- `<name>` is the unique hub identifier.
- `<x>` and `<y>` are the hub coordinates used by the visualization.
- `[metadata]` is optional and may contain:
  - `color`
  - `zone` (`normal`, `priority`, `restricted`, or `blocked`)
  - `max_drones`

If no `zone` is specified, the hub is considered `normal`.

### Connections

Connections are declared as:

```text
connection: <from>-<to> [metadata]
```

For example:

```text
connection: start-waypoint1
connection: waypoint1-waypoint2 [max_link_capacity=2]
connection: waypoint2-goal [max_link_capacity=3]
```

Connection metadata is optional. Currently, the supported metadata is:

- `max_link_capacity` — the maximum number of drones allowed to traverse the connection during the same simulation turn.

During parsing, Fly-in validates the entire map before the simulation starts, ensuring that hub names are unique, connections reference existing hubs, metadata values are valid, and the overall map is structurally consistent.

#### Default values

If metadata is omitted, the parser applies the following defaults:

- **Hubs**
  - `zone = normal`
  - `max_drones = 1`
  - For `start_hub` and `end_hub`, if `max_drones` is not specified, it defaults to the total number of drones (`nb_drones`).

- **Connections**
  - `max_link_capacity = 1`

## Project structure

```
fly_in/
├── graph_pac/          # Graph model, rendering, and the pygame engine
│   ├── engine.py        # Main loop, turn/frame timing
│   ├── graph_cls.py      # Graph built from the parsed map
│   └── visual.py         # Hub/drone/connection rendering, Layout
├── parser/              # Map file parsing and validation
│   ├── models.py         # Pydantic models: HubModel, ConnectionModel, MapModel
│   └── parser.py         # Reads and validates a map file into a MapModel
├── maps/                # Sample maps, grouped by difficulty
│   ├── easy/
│   ├── medium/
│   ├── hard/
│   └── challenger/
├── algorithm.py          # Solver: BFS pathfinding across multiple routes
├── route.py              # Turn-by-turn scheduling, capacity checks, formatting
├── fly_in.py             # Entry point
├── drone.png             # Drone sprite used by the visualization
├── .env / env.example    # Runtime configuration (window size, colors, ...)
├── requirements.txt
└── Makefile
```

## Instructions

### Requirements

- Python 3.10 or later
- Dependencies listed in `requirements.txt` (notably `pygame`, `pydantic`,
  `python-dotenv`, `webcolors`)

### Setup

Copy the example environment file and adjust it to your needs:

```bash
cp env.example .env
```

Relevant variables:

| Variable | Purpose |
|----------|---------|
| `MAP` | Default map file used when no map is provided. |
| `FULLSCREEN` | `TRUE` to run in fullscreen mode, `FALSE` to use a windowed display. |
| `FRAMES_PER_TURN` | Number of animation frames used to display a single simulation turn. |
| `BACKGROUND` | Background color of the visualization (any valid web color name). |

### Makefile targets

```bash
make install      # install dependencies
make run          # run the simulation on the default/configured map
make debug        # run under pdb
make lint         # flake8 . and mypy with the required flags
make lint-strict  # flake8 . and mypy --strict
make clean        # remove __pycache__, .mypy_cache, etc.
```

### Running against a specific map

The simulation must be run through `make run`, passing the map file via the
`MAP` variable:

```bash
make run MAP=maps/medium/01_dead_end_trap.txt
```

If `MAP` is omitted, the map defined by `MAP` in `.env` is used instead.

## Expected output

When the simulation starts, it prints the drones' movements turn by turn in the terminal while simultaneously displaying the animated `pygame` visualization.

For example, running the **Easy 01 – Linear path** map produces the following movement log:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line represents one simulation turn, and each movement is formatted as:

```text
D<id>-<destination>
```

or, when entering a restricted zone:

```text
D<id>-<origin>-<destination>
```

The second format indicates that the drone has started traversing a **restricted** zone, which requires **two simulation turns** to complete. During this transit the drone cannot stop or wait until it reaches the destination hub.

In the graphical visualization:

- **Colored circles** represent hubs.
- **Red connections** indicate that the destination hub is a **restricted** zone (a two-turn movement).
- Drone sprites move smoothly between hubs according to the movement cost.
- Hub labels display the current number of drones occupying each hub.
- A statistics overlay shows the current turn and other simulation metrics.

## Controls

| Key | Action |
|-----|--------|
| `Esc` | Exit the simulation. |

## Algorithm choices and implementation strategy

**Parsing.** `parser/parser.py` reads the map file line by line, builds raw
hub/connection dictionaries, then hands them to Pydantic models
(`parser/models.py`) for structural and semantic validation — unique names,
valid zone types, positive capacities, and metadata consistency (e.g. the
start/end hub's `max_drones` must equal the drone count). Invalid maps exit
with a clear error message rather than crashing.

**Graph representation.** `graph_pac/graph_cls.py` turns the validated map
into an adjacency-list graph (`dict[str, list[str]]`) plus a lookup table of
per-connection capacities, with no external graph library involved, per the
project constraints.

**Pathfinding.** `algorithm.py`'s `Solver` finds the main shortest path from
`start` to the end hub using breadth-first search, skipping `blocked` zones
entirely. To give the scheduler alternative routes to spread drones across
(rather than funneling every drone down the single shortest path), the
solver additionally identifies every junction (a hub with more than one
outgoing connection) and computes one extra BFS path per still-unexplored
branch at each junction — forcing the search away from already-claimed
branches so that every distinct path through the graph is represented.

**Turn-by-turn scheduling.** `route.py`'s `Route` class is the core of the
simulation:

- `compute_route` walks a single drone's raw path hop by hop, maintaining a
  real turn counter. At each hop it checks whether the destination hub and
  the connection leading to it both have free capacity for that turn; if
  not, the drone waits (recorded as an empty step) rather than moving.
  Occupancy is tracked per turn and carried forward (and propagated into
  already-computed later turns) so that a hub's occupancy count is always
  consistent regardless of which drone's turn is being computed.
- Entering a `restricted` zone advances the turn counter by two instead of
  one, matching the two-turn cost of that zone type; the two-part move
  string (`Di-from-to`) generated by `formatted_routes` records this as an
  uninterruptible transit — the drone cannot idle mid-connection.
- `best_path` computes every candidate path for a drone and keeps the one
  with the lowest cost (`get_path_cost`, which sums per-hop turn cost).
- `formatted_routes` expands every drone's chosen path into the turn-by-turn
  move strings required by the output format (`Di-hub` or `Di-from-to`),
  staggering drones so that later drones' departures don't corrupt earlier
  drones' already-computed schedules.
- `compute_hub_occupancy` derives, for every turn, exactly how many drones
  currently occupy each hub — recomputed from each drone's tracked current
  position rather than accumulated via increment/decrement, which keeps hub
  counts self-consistent (no drift, no negative counts) across the whole
  simulation.

**Complexity and performance notes.** Each candidate path is simulated
independently in `compute_route` (O(path length) per candidate, with a
constant-size capacity check per hop), and `best_path` compares candidates
by their computed turn cost. Paths are computed once per drone and reused
for the rest of the simulation (via `formatted_routes`/`hub_states`) rather
than recomputed every turn, keeping the animation loop itself O(drone
count) per rendered frame.

## Visual representation

The simulation renders live with `pygame`, driven by `graph_pac/engine.py`
(timing/turn advancement) and `graph_pac/visual.py` (drawing):

- **Hubs** are drawn as colored circles (color taken from the map's
  metadata, with a `rainbow` special case), labeled with their name and a
  live `current/max` occupancy count for the active turn.
- **Connections** are drawn as lines between hubs, colored red when they
  lead into a `restricted` zone, to make movement-cost zones visually
  obvious at a glance.
- **Drones** are drawn as sprites that move with a smooth linear
  interpolation between their origin and current target hub, spread across
  the correct number of frames for the move's real turn cost (one turn for
  a normal/priority hop, two for a restricted one), so an entering
  restricted zone visibly takes twice as long to traverse. Each drone is
  labeled with its ID while alone, or with a shared "N drones" occupancy
  label once it settles into a hub shared with others, avoiding label
  clutter when many drones converge.
- **Statistics overlay** shows the current turn out of the total, number of
  drones currently moving, total accumulated path cost, and the average
  turn at which drones reach the goal — giving an at-a-glance read on how
  efficient the computed schedule is, alongside the turn-by-turn textual
  log printed to the terminal.

Together, the colored zone/connection cues and the smooth per-turn-cost
drone animation make it easy to see which routing decisions (restricted
detours, capacity waits, junction diversity) are driving the total turn
count for a given map.

## Benchmark results

Measured simulation turns against the subject's reference targets, using the
provided sample maps:

| Difficulty | Map                         | Target   | Result |
|------------|------------------------------|----------|--------|
| Easy       | 01 – Linear path             | ≤ 6      | 4      |
| Easy       | 02 – Simple fork             | ≤ 6      | 5      |
| Easy       | 03 – Basic capacity          | ≤ 8      | 6      |
| Medium     | 01 – Dead end trap           | ≤ 15     | 8      |
| Medium     | 02 – Circular loop           | ≤ 20     | 16     |
| Medium     | 03 – Priority puzzle         | ≤ 12     | 7      |
| Hard       | 01 – Maze nightmare          | ≤ 45     | 14     |
| Hard       | 02 – Capacity hell           | ≤ 60     | 18     |
| Hard       | 03 – Ultimate challenge      | ≤ 35     | 26     |
| Challenger | 01 – The Impossible Dream    | 45 (ref.)| 43     |

All required maps meet their reference target, and the optional Challenger
map beats the reference record of 45 turns.

## Resources

- [Python `typing` module documentation](https://docs.python.org/3/library/typing.html)
- [Pydantic documentation](https://docs.pydantic.dev/latest/)
- [pygame documentation](https://www.pygame.org/docs/)
- [mypy documentation](https://mypy.readthedocs.io/en/stable/)
- [flake8 documentation](https://flake8.pycqa.org/en/latest/)
- Breadth-first search, as a general graph-traversal reference (standard
  algorithms textbook material, no specific library used per the project's
  constraints)

### AI usage

AI was used throughout development as a debugging and
learning tool, not as a code generator for whole features from scratch.
Specifically, it was used to:

- Enhance code design and approaches.
- Get further explanations about some mypy errors.
- Explain trade-offs (e.g. how restricted-zone timing interacts with the
  turn scheduler).
