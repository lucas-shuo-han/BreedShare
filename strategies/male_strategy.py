"""Male decision: learned search share; the rest split across reachable nests
as a best response to his beliefs about who else is investing there."""
from typing import Dict, List, Tuple

from agents.male_agent import MaleAgent
from core.base_strategy import allocate_raising, blend
from core.fitness import delivered_care, male_counterfactual
from strategies.belief_system import BeliefSystem
from world.world_state import WorldState


class MaleStrategy:
    def __init__(self, beliefs: BeliefSystem):
        self.beliefs = beliefs

    def candidate_nests(self, agent: MaleAgent, world: WorldState) -> List[int]:
        """Nest locations are free information: every nest within reach is a candidate."""
        return world.nests_within(agent.position, world.config.neighbourhood_radius)

    def decide(self, agent: MaleAgent, world: WorldState) -> Tuple[float, Dict[int, float]]:
        c = world.config
        nests = self.candidate_nests(agent, world)
        if not nests:
            return 1.0, {}
        search = self.beliefs.sample_search_share(agent.id)
        budget = 1.0 - search

        def payoff(my_share: float, nest_id: int) -> float:
            others_total, others_male = self.beliefs.nest_belief(agent.id, nest_id)
            care = delivered_care(my_share, world.nest_distance(agent, nest_id), c)
            return male_counterfactual(care, others_total, others_male,
                                       world.nest_quality(nest_id), c)

        best = allocate_raising(nests, budget, payoff, c)
        return search, blend(agent.raising_shares, best, c.adjustment_rate, budget)
