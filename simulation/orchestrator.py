"""Binds each agent to a strategy object. Swapping a strategy class here is the
only change needed to try a different decision rule."""
from typing import Dict, Union

from core.base_agent import BaseAgent
from strategies.belief_system import BeliefSystem
from strategies.female_strategy import FemaleStrategy
from strategies.male_strategy import MaleStrategy

Strategy = Union[FemaleStrategy, MaleStrategy]


class Orchestrator:
    def __init__(self, beliefs: BeliefSystem):
        self.beliefs = beliefs
        self._by_sex: Dict[str, Strategy] = {
            "female": FemaleStrategy(beliefs),
            "male": MaleStrategy(beliefs),
        }

    def strategy_for(self, agent: BaseAgent) -> Strategy:
        return self._by_sex[agent.sex]
