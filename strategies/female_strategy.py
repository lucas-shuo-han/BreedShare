"""Female decision: learned search share; the rest split across her own nests."""
from typing import Dict, List, Tuple

from agents.female_agent import FemaleAgent
from core.base_strategy import allocate_raising, blend
from core.fitness import delivered_care, female_counterfactual
from strategies.belief_system import BeliefSystem
from world.world_state import WorldState


class FemaleStrategy:
    def __init__(self, beliefs: BeliefSystem):
        self.beliefs = beliefs

    def candidate_nests(self, agent: FemaleAgent, world: WorldState) -> List[int]:
        return list(agent.nest_ids)

    def decide(self, agent: FemaleAgent, world: WorldState) -> Tuple[float, Dict[int, float]]:
        c = world.config
        search = self.beliefs.sample_search_share(agent.id)
        budget = 1.0 - search
        nests = self.candidate_nests(agent, world)

        def payoff(my_share: float, nest_id: int) -> float:
            others_total, others_male = self.beliefs.nest_belief(agent.id, nest_id)
            care = delivered_care(my_share, world.nest_distance(agent, nest_id), c)
            return female_counterfactual(care, others_total, others_male,
                                         world.nest_quality(nest_id), c)

        best = allocate_raising(nests, budget, payoff, c)
        return search, blend(agent.raising_shares, best, c.adjustment_rate, budget)
