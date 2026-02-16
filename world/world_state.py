# world/world_state.py
from typing import Dict, Tuple, Any, Optional, List
import math
import numpy as np
from numpy.typing import NDArray
import random
from config.config import RESOURCE_LEVEL, AGGREGATION_LEVEL, SEARCH_COST, GRID_SIZE
from agents.nest import Nest
from core.base_agent import BaseAgent
from world.world_generator import WorldGenerator

class WorldState:
    """Environment state management center.
    
    Responsibilities:
    1. Manage nest creation and ID allocation
    2. Manage resource map state
    3. Provide resource query interfaces
    4. Record agent action results
    5. Provide nest-related query interfaces
    """
    
    def __init__(self, nests: Optional[Dict[int, Nest]] = None, agents: Optional[Dict[int, BaseAgent]] = None,
                 resource_grid: Optional[NDArray[np.float32]] = None):
        self._next_nest_id = 0
        self.nests: Dict[int, Nest] = nests if nests is not None else {}
        self.agents: Dict[int, BaseAgent] = agents if agents is not None else {}
        
        # spatial resource grid (supports spatial resource queries)
        self.resource_grid: Optional[NDArray[np.float32]] = resource_grid
        self.grid_size: int = resource_grid.shape[0] if resource_grid is not None else 0
    
    def create_nest_for_female(self, female_id: int, position: Tuple[int, int]) -> int:
        """
        Create nest for female (allows multiple nests per female).
        
        Args:
            female_id: ID of the female agent that owns the nest
            position: (x, y) grid coordinates where nest is located
            
        Returns:
            Newly created nest ID
        """
        nest_id = self._next_nest_id
        nest = Nest(
            id=nest_id,
            female_id=female_id,
            position=position
        )
        self.nests[nest_id] = nest
        self._next_nest_id += 1
        return nest_id
    
    def get_nest_locations(self) -> List[Tuple[int, int]]:
        """
        Get all nest locations in the environment.
        
        Returns:
            List of (x, y) coordinates for all nests
        """
        return [nest.position for nest in self.nests.values()]
    
    def get_resource_density(self, position: Tuple[int, int]) -> float:
        """
        Get resource density at a specific position.
        
        Args:
            position: (x, y) grid coordinates to query
            
        Returns:
            Resource density at the specified position
        """
        if self.resource_grid is None:
            return 0.0
        
        x, y = position
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return float(self.resource_grid[x, y])
        return 0.0
    
    def compute_distance(self, cell1: Tuple[int, int], cell2: Tuple[int, int]) -> float:
        """
        Compute Euclidean distance between two cells.
        """
        dx = cell1[0] - cell2[0]
        dy = cell1[1] - cell2[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def get_agents_in_radius(self, position: Tuple[int, int], radius: int) -> List[BaseAgent]:
        """
        Get all agents within a specified radius of a given position.
        
        Args:
            position: (x, y) grid coordinates to query
            radius: Maximum distance from position to include agents
            
        Returns:
            List of BaseAgent objects within the specified radius
        """
        agents_in_radius = []
        
        for agent in self.agents.values():
            distance = self.compute_distance(position, agent.position)
            if distance <= radius:
                agents_in_radius.append(agent)
        
        return agents_in_radius
    
    def get_all_nests_basic(self) -> Dict[int, Tuple[int, int]]:
        """Return basic nest information (ID and position)."""
        return {nest_id: nest.position for nest_id, nest in self.nests.items()}
    
    def get_nest_details(self, nest_id: int) -> Dict[str, Any]:
        """
        Return complete nest information.
        """
        nest = self.nests[nest_id]
        return {
            'nest_id': nest.id,
            'female_id': nest.female_id,
            'male_ids': nest.get_male_ids,  # Get the property value (no parentheses needed)
            'position': nest.position
        }
    
    def get_agent_by_id(self, agent_id: int) -> BaseAgent:
        """Get agent object by ID."""
        return self.agents[agent_id]

    def query_nest_composition(self, agent_id: int, nest_id: int, search_share: float) -> Optional[Dict[str, Any]]:
        """
        Probabilistic query of nest internal composition based on distance and search share.
        
        Args:
            agent_id: The ID of the agent performing the search
            nest_id: The ID of the nest to query
            search_share: The agent's search investment (0.0 to 1.0)
            
        Returns:
            Dictionary containing nest details if search is successful, else None
        """
        # Get agent and nest objects
        agent = self.agents[agent_id]
        nest = self.nests[nest_id]
        
        # Compute distance between agent and nest
        d = self.compute_distance(agent.position, nest.position)
        
        # If agent is at the nest, it automatically knows the nest information
        if d == 0.0:
            return {
                'nest_id': nest.id,
                'female_id': nest.female_id,
                'male_ids': nest.get_male_ids,  # Get the property value (no parentheses needed)
                'position': nest.position,
                'female_raising_share': nest.female_raising_share,
                'male_raising_shares': nest.male_raising_shares
            }
        
        # Core magic formula: discovery probability
        p = 1 - math.exp(- SEARCH_COST * search_share / d)
        
        # Return results based on probability
        if random.random() < p:
            # Search successful, return all nest information
            return {
                'nest_id': nest.id,
                'female_id': nest.female_id,
                'male_ids': nest.get_male_ids,  # Get the property value (no parentheses needed)
                'position': nest.position,
                'female_raising_share': nest.female_raising_share,
                'male_raising_shares': nest.male_raising_shares
            }
        else:
            # Failed to find detailed nest information
            return None
    
    def reset_resources(self) -> None:
        """
        Reset world resources using WorldGenerator.
        
        This method regenerates resources after each round according to the technical documentation.
        """
        if self.grid_size <= 0:
            return
        
        # Use WorldGenerator to generate new resources with the same parameters as initialization
        world_generator = WorldGenerator(GRID_SIZE, RESOURCE_LEVEL, AGGREGATION_LEVEL)
        self.resource_grid = world_generator.generate_resources()
    
    def clear_all_nest_resources(self) -> None:
        """
        Clear all accumulated resources from nests.
        
        This method resets the resource counters for all nests.
        """
        for nest in self.nests.values():
            nest.reset_resources()
