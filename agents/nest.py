"""A nest: one female's breeding unit, cared for by her and any number of males."""
from typing import Dict, Tuple


class Nest:
    def __init__(self, id: int, female_id: int, position: Tuple[int, int]):
        self.id = id
        self.female_id = female_id
        self.position = position

        # Raising shares in the last completed round: agent_id -> share.
        # This is what other birds can learn by searching.
        self.shares: Dict[int, float] = {}

        # Bookkeeping for the round in progress.
        self._pending: Dict[int, float] = {}
        self.effort: float = 0.0       # total raising share applied so far this round
        self.resources: float = 0.0    # resources gathered so far this round

    # --- round lifecycle ---------------------------------------------------
    def begin_round(self) -> None:
        self._pending = {}
        self.effort = 0.0
        self.resources = 0.0

    def record(self, agent_id: int, share: float, harvested: float) -> None:
        self._pending[agent_id] = self._pending.get(agent_id, 0.0) + share
        self.effort += share
        self.resources += harvested

    def end_round(self) -> None:
        self.shares = self._pending

    # --- queries -------------------------------------------------------------
    @property
    def female_share(self) -> float:
        return self.shares.get(self.female_id, 0.0)

    @property
    def male_shares(self) -> Dict[int, float]:
        return {a: s for a, s in self.shares.items() if a != self.female_id}

    @property
    def total_male_share(self) -> float:
        return sum(self.male_shares.values())

    @property
    def total_share(self) -> float:
        return sum(self.shares.values())
