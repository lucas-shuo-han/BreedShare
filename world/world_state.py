"""The world: resource grid, nests, birds, and the two physical processes
that act on them — search (costly information) and foraging (depletion)."""
import math
from typing import Dict, List, Tuple

import numpy as np
from numpy.typing import NDArray

from agents.nest import Nest
from config.config import Config
from core.base_agent import BaseAgent
from world.world_generator import WorldGenerator


class WorldState:
    def __init__(self, config: Config, rng: np.random.Generator):
        self.config = config
        self.rng = rng
        self.generator = WorldGenerator(config, rng)
        self.habitat: NDArray[np.float64] = self.generator.generate_habitat()
        self.resource_grid: NDArray[np.float64] = self.generator.generate_resources(self.habitat)
        self.grid_size = config.grid_size

        self.nests: Dict[int, Nest] = {}
        self.agents: Dict[int, BaseAgent] = {}
        self._next_nest_id = 0

        # Per-nest foraging window: (row slice, col slice, distance array).
        self._windows: Dict[int, Tuple[slice, slice, NDArray[np.float64]]] = {}
        self._quality: Dict[int, float] = {}

    # --- set-up --------------------------------------------------------------
    def add_agent(self, agent: BaseAgent) -> None:
        self.agents[agent.id] = agent

    def create_nest(self, female_id: int, position: Tuple[int, int]) -> int:
        nest_id = self._next_nest_id
        self._next_nest_id += 1
        self.nests[nest_id] = Nest(nest_id, female_id, position)
        self._build_window(nest_id)
        return nest_id

    def _build_window(self, nest_id: int) -> None:
        c = self.config
        x, y = self.nests[nest_id].position
        reach = c.territory_radius * math.sqrt(c.max_nest_effort)
        r = int(math.ceil(reach))
        rows = slice(max(0, x - r), min(self.grid_size, x + r + 1))
        cols = slice(max(0, y - r), min(self.grid_size, y + r + 1))
        xs = np.arange(rows.start, rows.stop)[:, None] - x
        ys = np.arange(cols.start, cols.stop)[None, :] - y
        dist = np.sqrt(xs ** 2 + ys ** 2)
        self._windows[nest_id] = (rows, cols, dist)
        # Habitat quality a bird can expect around this nest (mean resource per cell
        # within the full foraging range). Habitat is persistent, so this is known.
        self._quality[nest_id] = float(self.habitat[rows, cols][dist <= reach].mean())

    # --- queries -------------------------------------------------------------
    @staticmethod
    def distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def nests_within(self, position: Tuple[int, int], radius: float) -> List[int]:
        return [k for k, n in self.nests.items() if self.distance(position, n.position) <= radius]

    def agents_within(self, position: Tuple[int, int], radius: float, sex: str) -> List[BaseAgent]:
        return [a for a in self.agents.values()
                if a.sex == sex and self.distance(position, a.position) <= radius]

    def nest_distance(self, agent: BaseAgent, nest_id: int) -> float:
        return self.distance(agent.position, self.nests[nest_id].position)

    def nest_quality(self, nest_id: int) -> float:
        return self._quality[nest_id]

    # --- search: costly information (§4) ---------------------------------------
    def search_success_probability(self, distance: float, search_share: float) -> float:
        """p = 1 - exp(-lambda * search_share / d), with d in units of the neighbourhood radius."""
        if distance <= 0.0:
            return 1.0
        d = distance / self.config.neighbourhood_radius
        return 1.0 - math.exp(-self.config.search_efficiency * search_share / d)

    def search(self, agent: BaseAgent, nest_id: int) -> bool:
        d = self.distance(agent.position, self.nests[nest_id].position)
        return bool(self.rng.random() < self.search_success_probability(d, agent.search_share))

    # --- foraging: depletion (§7) ------------------------------------------------
    def forage(self, nest_id: int, share: float) -> float:
        """Apply `share` more effort to a nest. The nest's foraging range grows from
        radius T*sqrt(E) to T*sqrt(E + share); the bird takes a fraction rho of every
        cell in the new ring. Taken resources leave the grid, so overlapping nests
        compete and the order of actions matters."""
        c = self.config
        nest = self.nests[nest_id]
        e0 = min(nest.effort, c.max_nest_effort)
        e1 = min(nest.effort + share, c.max_nest_effort)
        if e1 <= e0:
            return 0.0
        r0 = c.territory_radius * math.sqrt(e0)
        r1 = c.territory_radius * math.sqrt(e1)
        rows, cols, dist = self._windows[nest_id]
        ring = (dist < r1) & (dist >= r0)
        block = self.resource_grid[rows, cols]
        taken = block[ring] * c.extraction_rate
        block[ring] -= taken
        return float(taken.sum())

    def regenerate_resources(self) -> None:
        self.resource_grid = self.generator.generate_resources(self.habitat)
