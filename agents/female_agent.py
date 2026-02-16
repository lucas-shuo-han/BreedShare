# agents/female_agent.py
from typing import Tuple, Set
from core.base_agent import BaseAgent

class FemaleAgent(BaseAgent):
    """
    Female bird agent with home range and nest state management.
    Encapsulates state only - all decision logic is in FemaleStrategy.
    Can be queried from outside
    """

    def __init__(
            self,
            id: int,
            position: Tuple[int, int],
            initial_male_count: int = 0
    ):
        """
        Initialize female agent.
        
        Args:
            bird_id: Unique integer identifier
            position: Current (x, y) coordinates
            home_range: Set of grid cells defining territory (no resource data stored).
            initial_male_count: Number of males currently in nest (default 0)
        """
        super().__init__(id, position)
        self.nest_ids: Set[int] = set()
        self._male_count = initial_male_count
        # TODO: home_range is not used in core simulation logic, consider removing or integrating
        self.home_range: Set[Tuple[int, int]] = set()

    def get_home_range(self) -> Set[Tuple[int, int]]:
        """Return female home range cells."""
        return self.home_range.copy()  # Return copy to prevent external mutation
    
    def get_male_count(self) -> int:
        """
        Direct query of males in nest. 
        NOTE: Strategy layer will enforce search costs if needed.
        """
        return self._male_count

    def add_male_to_nest(self) -> None:
        """Increment male count when a male joins the nest."""
        self._male_count += 1
    
    def remove_male_from_nest(self) -> None:
        """Decrement male count when a male leaves the nest."""
        if self._male_count > 0:
            self._male_count -= 1

    def step(self) -> None:
        """
        Execute one simulation step.
        NOTE: Strategy layer will handle movement and mating decisions.
        """
        pass