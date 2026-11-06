"""Builds the initial world: landscape, birds, nests, beliefs."""
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from agents.female_agent import FemaleAgent
from agents.male_agent import MaleAgent
from config.config import Config
from core.fitness import delivered_care
from simulation.orchestrator import Orchestrator
from strategies.belief_system import BeliefSystem
from world.world_state import WorldState


@dataclass
class Simulation:
    config: Config
    rng: np.random.Generator
    world: WorldState
    females: List[FemaleAgent]
    males: List[MaleAgent]
    beliefs: BeliefSystem
    orchestrator: Orchestrator


def bootstrap(config: Config) -> Simulation:
    rng = np.random.default_rng(config.seed)
    world = WorldState(config, rng)
    beliefs = BeliefSystem(config, rng)

    def random_cell() -> Tuple[int, int]:
        return int(rng.integers(config.grid_size)), int(rng.integers(config.grid_size))

    def initial_search() -> float:
        return float(rng.uniform(config.min_search_share, 0.5))

    agent_id = 0
    females: List[FemaleAgent] = []
    for _ in range(config.n_females):
        female = FemaleAgent(agent_id, random_cell())
        agent_id += 1
        nest_id = world.create_nest(female.id, _settle(world, female.position, config.settle_radius))
        female.nest_ids.append(nest_id)
        female.move_to(world.nests[nest_id].position)
        s = initial_search()
        female.set_allocation(s, {nest_id: 1.0 - s})
        world.add_agent(female)
        females.append(female)

    males: List[MaleAgent] = []
    for _ in range(config.n_males):
        male = MaleAgent(agent_id, random_cell())
        agent_id += 1
        reachable = sorted(world.nests_within(male.position, config.neighbourhood_radius),
                           key=lambda k: world.distance(male.position, world.nests[k].position))[:2]
        if reachable:
            s = initial_search()
            weights = rng.random(len(reachable))
            weights = weights / weights.sum() * (1.0 - s)
            male.set_allocation(s, dict(zip(reachable, weights.tolist())))
        else:
            male.set_allocation(1.0, {})
        world.add_agent(male)
        males.append(male)

    # The starting allocations act as "last round" for every nest.
    for agent in world.agents.values():
        for nest_id, share in agent.raising_shares.items():
            care = delivered_care(share, world.nest_distance(agent, nest_id), config)
            if care > 0:
                world.nests[nest_id].shares[agent.id] = care

    # Beliefs: each bird starts with its own search share as prior and knows
    # the nests it is already caring for.
    for agent in world.agents.values():
        beliefs.init_agent(agent.id, agent.search_share)
        for nest_id in agent.raising_shares:
            beliefs.observe_nest(agent.id, world.nests[nest_id])

    return Simulation(config, rng, world, females, males, beliefs, Orchestrator(beliefs))


def _settle(world: WorldState, start: Tuple[int, int], radius: int) -> Tuple[int, int]:
    """Females contract toward good habitat: the best free cell within `radius`."""
    x0, y0 = start
    taken = {n.position for n in world.nests.values()}
    best, best_value = start, -1.0
    for x in range(max(0, x0 - radius), min(world.grid_size, x0 + radius + 1)):
        for y in range(max(0, y0 - radius), min(world.grid_size, y0 + radius + 1)):
            if (x - x0) ** 2 + (y - y0) ** 2 > radius ** 2 or (x, y) in taken:
                continue
            value = world.habitat[x, y] + 1e-3 * world.resource_grid[x, y]
            if value > best_value:
                best, best_value = (x, y), value
    return best
