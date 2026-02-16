# strategies/male_strategy.py
import random
from typing import Dict, Any
from core.base_strategy import BaseStrategy
from world.world_state import WorldState
from config.config import MIN_SEARCH_SHARE, ALLOCATION_STEPS, MARGINAL_DELTA
from core.fitness import calculate_male_fitness, calculate_male_fitness_counterfactual

class MaleStrategy(BaseStrategy):
    """
    Male strategy: Take other agent's action as given, and maximize the utility(fitness) function.
    
    Decision logic:
    - If owns 0 nests: search_share = 1.0
    - Use Bayesian updating based on observed peers' search_share and fitness
    - This is essentially an fitness maximation problem with constraint total raising share equals 1 - search share, with the utility(fitness) function being wrapped logistic function
    """
    
    def __init__(self, belief_system: Any):
        """
        Initialize male strategy with belief system.
        
        Args:
            belief_system: The belief system instance for Bayesian updating
        """
        super().__init__(belief_system)
    
    def allocate_shares(self, agent_id: int, world_state: WorldState) -> Dict[str, Any]:
        """
        Allocate raising shares across male's assigned nests using Bayesian updated search_share.
        
        Args:
            agent_id: The agent's ID
            world_state: The current world state
            
        Returns:
            Dictionary containing search_share and raising_shares
        """
        male = world_state.get_agent_by_id(agent_id)
        
        # Validate agent type
        if not hasattr(male, 'nest_roles'):
            raise ValueError(f"Agent {agent_id} is not a male agent")
        
        # Get all nests the male has searched or is assigned to
        # Currently, we'll include all nests since search history isn't tracked yet
        assigned_nests = list(getattr(male, 'nest_roles', {}).keys())
        all_nests = list(world_state.nests.keys())
        
        # Male can go to any nest he has searched or is assigned to
        # For now, include all nests as search history isn't implemented
        available_nests = list(set(assigned_nests + all_nests))
        num_nests = len(available_nests)
        
        # Base case: no assigned nests
        if num_nests == 0:
            return {
                "search_share": 1.0,
                "raising_shares": {}
            }
        
        # Get Bayesian updated search share belief
        search_share = self.get_search_belief(agent_id)
        
        # TODO: Enforcing minimum search share should be removed or changed to be different from female
        search_share = max(search_share, MIN_SEARCH_SHARE)
        
        # Calculate raising share per nest using optimization
        total_raising_share = 1.0 - search_share
        
        # Use the general allocation algorithm from BaseStrategy
        raising_shares = self._allocate_raising_shares(
            agent_id=agent_id,
            available_nests=available_nests,
            total_raising_share=total_raising_share,
            belief_func=lambda nest_id: self.get_raising_belief(agent_id, nest_id),
            fitness_func=calculate_male_fitness_counterfactual,
            world_state=world_state
        )
        
        # Submit observations of other male agents' search_share and fitness for social learning
        self._submit_male_observations(agent_id, world_state)
        
        return {
            "search_share": search_share,
            "raising_shares": raising_shares
        }
    
    def _submit_male_observations(self, agent_id: int, world_state: WorldState) -> None:
        """
        Submit observations of other male agents' search_share and fitness for social learning.
        
        Args:
            agent_id: The observing agent's ID
            world_state: The current world state
        """
        # Get all other male agents
        male_agents = [agent for agent in world_state.agents.values() 
                      if hasattr(agent, 'nest_roles') and agent.id != agent_id]
        
        for observed_agent in male_agents:
            # For simplicity, we'll assume the observed agent's current search_share is stored somewhere
            # In a real implementation, this would be retrieved from the agent's history
            # For now, we'll use a random value similar to the current implementation
            # TODO: Store and retrieve actual search_share from agent's history
            observed_search_share = random.uniform(MIN_SEARCH_SHARE, 1.0)
            
            # Calculate fitness for the observed agent
            total_fitness = 0.0
            for nest_id in getattr(observed_agent, 'nest_roles', {}).keys():
                if nest_id in world_state.nests:
                    nest = world_state.nests[nest_id]
                    total_fitness += calculate_male_fitness(nest, observed_agent.id, world_state)
            
            # Submit observation to belief system
            self.submit_search_observation(agent_id, observed_agent.id, observed_search_share, total_fitness)
        
        # Update beliefs based on collected observations
        self.update_beliefs(agent_id)