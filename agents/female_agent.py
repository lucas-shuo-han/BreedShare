from typing import List, Tuple

from core.base_agent import BaseAgent


class FemaleAgent(BaseAgent):
    """A female owns her nest(s). Males choose which nests to help raise."""
    sex = "female"

    def __init__(self, id: int, position: Tuple[int, int]):
        super().__init__(id, position)
        self.nest_ids: List[int] = []
