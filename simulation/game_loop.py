"""One breeding round (docs/model.md §6):

1. Every bird decides its allocation from what it currently believes.
2. All actions — one search per bird, one raise per (bird, nest) — are shuffled.
3. Actions run in that order. Raising forages around the nest and depletes the
   grid; searching may reveal a nest's composition.
4. Payoffs are paid, beliefs are updated, and resources regenerate.
"""
import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import numpy as np

from core.base_agent import BaseAgent
from core.fitness import delivered_care, female_payoff, male_payoff
from initializer.bootstrap import Simulation
from simulation.metrics import summarize_round

log = logging.getLogger("breedshare")

Action = Tuple[str, BaseAgent, int, float]


class GameLoop:
    def __init__(self, sim: Simulation):
        self.sim = sim
        self.round = 0

    def run(self, rounds: int) -> List[Dict[str, float]]:
        return [self.run_round() for _ in range(rounds)]

    def run_round(self) -> Dict[str, float]:
        sim, world, beliefs = self.sim, self.sim.world, self.sim.beliefs
        agents = list(world.agents.values())
        self.round += 1

        for nest in world.nests.values():
            nest.begin_round()

        # Free, coarse information: the population-average investment per nest
        # stands in for nests a bird has never observed.
        beliefs.prior_total = float(np.mean([n.total_share for n in world.nests.values()]))
        beliefs.prior_male = float(np.mean([n.total_male_share for n in world.nests.values()]))

        # 1. Decide (all from the same snapshot, so order does not matter here).
        for agent in agents:
            search, raising = sim.orchestrator.strategy_for(agent).decide(agent, world)
            agent.set_allocation(search, raising)
            log.info("round %d %s %d search=%.3f raising=%s", self.round, agent.sex, agent.id,
                     search, {k: round(v, 3) for k, v in agent.raising_shares.items()})

        # 2. Shuffle.
        actions: List[Action] = []
        for agent in agents:
            actions.append(("search", agent, -1, agent.search_share))
            actions.extend(("raise", agent, k, x) for k, x in agent.raising_shares.items())
        order = sim.rng.permutation(len(actions))

        # 3. Execute.
        observed: Dict[int, Set[int]] = defaultdict(set)
        for i in order:
            kind, agent, nest_id, share = actions[i]
            if kind == "raise":
                care = delivered_care(share, world.nest_distance(agent, nest_id), sim.config)
                harvested = world.forage(nest_id, care)
                world.nests[nest_id].record(agent.id, care, harvested)
                observed[agent.id].add(nest_id)   # being at the nest reveals it
            else:
                for k in sim.orchestrator.strategy_for(agent).candidate_nests(agent, world):
                    if k not in agent.raising_shares and world.search(agent, k):
                        observed[agent.id].add(k)

        for nest in world.nests.values():
            nest.end_round()

        # 4. Payoffs.
        c = sim.config
        for agent in agents:
            if agent.sex == "female":
                agent.fitness = sum(female_payoff(world.nests[k], c) for k in agent.nest_ids)
            else:
                agent.fitness = sum(male_payoff(world.nests[k], agent.id, c) for k in agent.raising_shares)

        # Beliefs about nests: what each bird saw this round.
        for agent_id, nest_ids in observed.items():
            for k in nest_ids:
                beliefs.observe_nest(agent_id, world.nests[k])

        # Social learning of search share from same-sex neighbours (self included).
        peers = {a.id: [(p.search_share, p.fitness)
                        for p in world.agents_within(a.position, c.neighbourhood_radius, a.sex)]
                 for a in agents}
        for agent_id, obs in peers.items():
            beliefs.learn_search(agent_id, obs)

        summary = summarize_round(world)
        summary["round"] = self.round
        world.regenerate_resources()
        return summary
