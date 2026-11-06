"""State shared by all birds. Agents hold state only; decisions live in strategies/."""
from typing import Dict, Tuple


class BaseAgent:
    sex: str = ""

    def __init__(self, id: int, position: Tuple[int, int]):
        self._id = id
        self._position = position
        # The allocation vector: search_share + sum(raising_shares.values()) == 1.
        self.search_share: float = 1.0
        self.raising_shares: Dict[int, float] = {}
        self.fitness: float = 0.0   # payoff in the last completed round

    @property
    def id(self) -> int:
        return self._id

    @property
    def position(self) -> Tuple[int, int]:
        """Home position: where the bird lives and measures distances from."""
        return self._position

    def move_to(self, position: Tuple[int, int]) -> None:
        self._position = position

    def set_allocation(self, search_share: float, raising_shares: Dict[int, float]) -> None:
        self.search_share = search_share
        self.raising_shares = {k: v for k, v in raising_shares.items() if v > 1e-9}

    def nests_cared_for(self, threshold: float) -> Dict[int, float]:
        return {k: v for k, v in self.raising_shares.items() if v >= threshold}
