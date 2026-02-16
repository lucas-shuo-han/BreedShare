# strategies/female_strategy.py
import random
from typing import Dict, Any
from core.base_strategy import BaseStrategy
from world.world_state import WorldState
from config.config import MIN_SEARCH_SHARE, ALLOCATION_STEPS, MARGINAL_DELTA
from core.fitness import calculate_female_fitness, calculate_female_fitness_counterfactual

class FemaleStrategy(BaseStrategy):
    """
    Female strategy: Take other agent's action as given, and maximize the utility(fitness) function.
    
    Decision logic:
    - If owns 0 nests: search_share = 1.0
    - Use Bayesian updating based on observed peers' search_share and fitness
    - This is essentially an fitness maximation problem with constraint total raising share equals 1 - search share, with the utility(fitness) function being wrapped logistic function
    - Enforce min_search_share floor
    """
    
    def __init__(self, belief_system: Any):
        """
        Initialize female strategy with belief system.
        
        Args:
            belief_system: The belief system instance for Bayesian updating
        """
        super().__init__(belief_system)
    
    def allocate_shares(self, agent_id: int, world_state: WorldState) -> Dict[str, Any]:
        """
        Allocate raising shares across female's nests using Bayesian updated search_share.
        
        Args:
            agent_id: The agent's ID
            world_state: The current world state
            
        Returns:
            Dictionary containing search_share and raising_shares
        """
        female = world_state.get_agent_by_id(agent_id)
        
        # Validate agent type
        if not hasattr(female, 'nest_ids'):
            raise ValueError(f"Agent {agent_id} is not a female agent")
        
        owned_nests: list[int] = list(female.nest_ids)  # type: ignore
        num_nests = len(owned_nests)
        
        # Base case: no nests - create a new nest
        if num_nests == 0:
            # Create a new nest at the female's current position
            new_nest_id = world_state.create_nest_for_female(
                female_id=agent_id,
                position=female.position
            )
            # Add the new nest to the female's owned nests
            female.nest_ids.add(new_nest_id)  # type: ignore
            # Update owned_nests list and num_nests count
            owned_nests = [new_nest_id]
            num_nests = 1
            # Set search_share to minimum since we just created a nest
            search_share = MIN_SEARCH_SHARE
        else:
            # Get Bayesian updated search share belief
            search_share = self.get_search_belief(agent_id)
            # Enforce minimum search share
            search_share = max(search_share, MIN_SEARCH_SHARE)
        

        # Calculate raising share per nest using optimization
        total_raising_share = 1.0 - search_share
        
        # Use the general allocation algorithm from BaseStrategy
        raising_shares = self._allocate_raising_shares(
            agent_id=agent_id,
            available_nests=owned_nests,
            total_raising_share=total_raising_share,
            belief_func=lambda nest_id: self.get_raising_belief(agent_id, nest_id),
            fitness_func=calculate_female_fitness_counterfactual,
            world_state=world_state
        )
        
        # Submit observations of other female agents' search_share and fitness for social learning
        self._submit_female_observations(agent_id, world_state)
        
        return {
            "search_share": search_share,
            "raising_shares": raising_shares
        }
    
    def _submit_female_observations(self, agent_id: int, world_state: WorldState) -> None:
        """
        Submit observations of other female agents' search_share and fitness for social learning.
        
        Args:
            agent_id: The observing agent's ID
            world_state: The current world state
        """
        # Get all other female agents
        female_agents = [agent for agent in world_state.agents.values() 
                        if hasattr(agent, 'nest_ids') and agent.id != agent_id]
        
        for observed_agent in female_agents:
            # For simplicity, we'll assume the observed agent's current search_share is stored somewhere
            # In a real implementation, this would be retrieved from the agent's history
            # For now, we'll use a random value similar to the current implementation
            # TODO: Store and retrieve actual search_share from agent's history
            observed_search_share = random.uniform(MIN_SEARCH_SHARE, 1.0)
            
            # Calculate fitness for the observed agent
            total_fitness = 0.0
            for nest_id in getattr(observed_agent, 'nest_ids', []):
                if nest_id in world_state.nests:
                    nest = world_state.nests[nest_id]
                    total_fitness += calculate_female_fitness(nest, world_state)
            
            # Submit observation to belief system
            self.submit_search_observation(agent_id, observed_agent.id, observed_search_share, total_fitness)
        
        # Update beliefs based on collected observations
        self.update_beliefs(agent_id)