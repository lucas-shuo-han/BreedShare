# agents/nest.py
from typing import Dict, Set, Tuple, Optional

# Use string forward reference to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from world.world_state import WorldState

# TODO: the nest class looks tedious. I wonder if there is some way to pack similar attributes together.
# TODO: modify the home_range_cells to better accommodate the home range of the female.
class Nest:
    """Single breeding nest owned by one female."""
    
    def __init__(self, id: int, female_id: Optional[int], position: Tuple[int, int]):
        """
        Args:
            id: Nest unique ID (exposed to agents)
            female_id: The sole owner of this nest (None if no female assigned)
            position: (x, y) grid coordinates where nest is located
            home_range_cells: Set of (x, y) grid coordinates that define the nest's home range
        """
        self.id = id
        self.female_id = female_id
        self.position = position
        # TODO: home_range_cells is not used in core simulation logic, only for reporting. Consider removing or integrating
        self.home_range_cells: Set[Tuple[int, int]] = set()
        self.resource_cache: float = 0.0  # Current step's available resources

        # Males in the current nest
        self._male_ids: Set[int] = set()
        
        # Raising shares (breedshares) - determined by strategy layer
        # Key: male_id, Value: raising share (must sum to ≤ 1.0 across all males)
        self.male_raising_shares: Dict[int, float] = {}
        self.female_raising_share: float = 0.0
    
    @property
    def get_male_ids(self) -> Set[int]:
        return self._male_ids.copy()
    
    def add_male(self, male_id: int) -> None:
        if male_id not in self._male_ids:
            self._male_ids.add(male_id)
    
    def remove_male(self, male_id: int) -> None:
        self._male_ids.discard(male_id)

    def male_raising_share(self, male_id: int) -> float:
        """
        Get the raising share for a specific male.
        Called by: calculate_male_fitness()
        """
        return self.male_raising_shares.get(male_id, 0.0)
    
    def get_male_raising_share(self) -> float:
        """
        Get the total raising share of all males.
        Called by: calculate_male_fitness()
        """
        return sum(self.male_raising_shares.values())
    
    def get_total_raising_share(self) -> float:
        """
        Get the total raising share of all individuals (female + males).
        Called by: calculate_male_fitness()
        """
        return self.female_raising_share + self.get_male_raising_share()
    
    def get_home_range(self) -> Set[Tuple[int, int]]:
        """Return nest home range cells."""
        return self.home_range_cells.copy()  # Return copy to prevent external mutation
    
    def get_total_resources(self, world_state: 'WorldState') -> float:
        """
        Calculate total resources in the nest's home range by summing
        resources from world state's resource grid.
        Called by: calculate_female_fitness()
        
        Args:
            world_state: The current world state containing the resource grid
            
        Returns:
            Total resources in the nest's home range
        """
        total_resources = 0.0
        
        # Sum resources from all cells in the home range
        for cell in self.home_range_cells:
            total_resources += world_state.get_resource_density(cell)
        
        return total_resources
    
    def add_resources(self, amount: float) -> None:
        """
        Add resources to the nest's resource cache.
        Called by: mine_resources()
        
        Args:
            amount: The amount of resources to add
        """
        self.resource_cache += amount
    
    def reset_resources(self) -> None:
        """
        Reset the nest's resource cache to zero.
        Called by: world_state.clear_all_nest_resources()
        """
        self.resource_cache = 0.0

