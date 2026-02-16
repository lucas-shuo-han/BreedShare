# core/base_strategy.py
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING, Callable, List
from config.config import ALLOCATION_STEPS, MARGINAL_DELTA


# TODO: this is hard to comprehend
# TODO: agent can choose whether its raising share to a certain nest is counted as positive or negative???
if TYPE_CHECKING:
    from world.world_state import WorldState
    from strategies.belief_system import BeliefSystem

class BaseStrategy(ABC):
    """
    Abstract base for all decision strategies.
    
    Contract: Subclasses must implement allocate_shares to determine
    how an agent splits its effort between search and raising activities.
    """
    
    def __init__(self, belief_system: 'BeliefSystem'):
        """
        Initialize strategy with belief system reference.
        
        Args:
            belief_system: The belief system instance for Bayesian updating
        """
        self.belief_system = belief_system
    
    @abstractmethod
    def allocate_shares(self, agent_id: int, world_state: 'WorldState') -> Dict[str, Any]:
        """
        Core decision: Allocate 1.0 unit of effort across search and nests.
        
        Returns:
            {
                "raising_shares": {nest_id: share} (raising share for each nest),
                "search_share": float (≥ min_search_share)
            }
        """
        pass
    
    def get_search_belief(self, agent_id: int) -> float:
        """
        Get normalized search share belief from belief system.
        
        Args:
            agent_id: The agent's ID
            
        Returns:
            The posterior mean search share belief
        """
        belief = self.belief_system.get_belief(agent_id, 'search')
        return belief
    
    def get_raising_belief(self, agent_id: int, nest_id: int) -> float:
        """
        Get normalized raising share belief from belief system.
        
        Args:
            agent_id: The agent's ID
            nest_id: The nest ID
            
        Returns:
            The posterior mean raising share belief
        """
        belief = self.belief_system.get_belief(agent_id, 'raising', nest_id=nest_id)
        return belief
    
    def submit_search_observation(self, agent_id: int, observed_agent_id: int, 
                                 search_share: float, fitness: float) -> None:
        """
        Submit an observation of a peer's search_share and fitness for social learning.
        
        Args:
            agent_id: The observing agent's ID
            observed_agent_id: The observed agent's ID
            search_share: The observed agent's search_share
            fitness: The observed agent's fitness
        """
        self.belief_system.submit_search_observation(agent_id, observed_agent_id, search_share, fitness)
    
    def update_beliefs(self, agent_id: int) -> None:
        """
        Update all beliefs for the agent.
        
        Args:
            agent_id: The agent's ID
        """
        self.belief_system.update_search_beliefs(agent_id)
        self.belief_system.update_raising_beliefs(agent_id)
    
    def _allocate_raising_shares(self, 
                                agent_id: int, 
                                available_nests: List[int], 
                                total_raising_share: float, 
                                belief_func: Callable[[int], float], 
                                fitness_func: Callable[[float, float, tuple, 'WorldState'], float], 
                                world_state: 'WorldState') -> Dict[int, float]:
        """
        General greedy iterative allocation algorithm for raising shares.
        
        Args:
            agent_id: The agent's ID
            available_nests: List of nest IDs available to the agent
            total_raising_share: Total raising share to allocate across nests
            belief_func: Function to get beliefs about others' raising shares for a nest
            fitness_func: Counterfactual fitness calculation function
            world_state: Current world state
            
        Returns:
            Dictionary mapping nest IDs to allocated raising shares
        """
        num_nests = len(available_nests)
        
        # Initialize allocation for all nests to 0
        raising_shares = {nest_id: 0.0 for nest_id in available_nests}
        
        # Calculate step size: total_raising_share / number of allocation steps
        step_size = total_raising_share / ALLOCATION_STEPS
        
        # Get beliefs about others' raising shares in each nest
        others_total = {nest_id: belief_func(nest_id) for nest_id in available_nests}
        
        # Iterate for the specified number of steps
        for _ in range(ALLOCATION_STEPS):
            # Calculate marginal utility for each nest
            marginal_utilities = {}
            
            for nest_id in available_nests:
                # Get current allocation for this nest
                current_allocation = raising_shares[nest_id]
                
                # Get nest information
                nest = world_state.nests[nest_id]
                nest_position = nest.position
                
                # Get others' total raising share for this nest from beliefs
                others_raising = others_total.get(nest_id, 0.0)
                
                # Calculate base fitness using counterfactual function
                base_fitness: float = fitness_func(
                    my_raise=current_allocation,
                    others_raise=others_raising,
                    nest_position=nest_position,
                    world_state=world_state
                )
                
                # Calculate fitness with increment using counterfactual function
                increment_fitness = fitness_func(
                    my_raise=current_allocation + MARGINAL_DELTA,
                    others_raise=others_raising,
                    nest_position=nest_position,
                    world_state=world_state
                )
                
                # Calculate marginal utility using numerical differentiation
                if MARGINAL_DELTA > 0:
                    marginal_utility = (increment_fitness - base_fitness) / MARGINAL_DELTA
                else:
                    marginal_utility = 0.0
                
                marginal_utilities[nest_id] = marginal_utility
            
            # Find the nest with the highest marginal utility
            if marginal_utilities:
                best_nest_id = max(marginal_utilities, key=marginal_utilities.get)
                
                # Add a step of raising share to this nest
                raising_shares[best_nest_id] += step_size
        
        # Step 3: Normalize to ensure strict budget constraint
        actual_total = sum(raising_shares.values())
        if actual_total > 0:
            scaling_factor = total_raising_share / actual_total
            raising_shares = {nest_id: share * scaling_factor for nest_id, share in raising_shares.items()}
        else:
            # Fallback to equal distribution if all marginal utilities are zero
            share_per_nest = total_raising_share / num_nests
            raising_shares = {nest_id: share_per_nest for nest_id in available_nests}
        
        return raising_shares