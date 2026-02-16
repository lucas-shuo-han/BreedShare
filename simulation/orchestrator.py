# simulation/orchestrator.py
from typing import List, Dict, Optional, Type

from world.world_state import WorldState
from core.base_agent import BaseAgent
from agents.female_agent import FemaleAgent
from agents.male_agent import MaleAgent
from strategies.belief_system import BeliefSystem
from strategies.female_strategy import FemaleStrategy
from strategies.male_strategy import MaleStrategy


class Orchestrator:
    """
    Orchestrator: Coordinate agents with their strategies.
    
    Responsibilities:
    1. Lifecycle management: Created once by bootstrap, exists for entire simulation duration
    2. Daily binding: Manages agent-strategy mappings that can be re-bound before daily decisions
    3. Runtime access: Provides quick access to agent strategies during simulation execution
    4. State isolation: Only maintains mappings, doesn't store agent/strategy internal states
    """
    
    def __init__(self, world_state: WorldState, belief_system: BeliefSystem):
        """
        Initialize Orchestrator with world state and belief system.
        
        Args:
            world_state: Current world state
            belief_system: Belief system instance for agent decision-making
        """
        self.world_state = world_state
        self.belief_system = belief_system
        
        # Strategy mappings: Agent ID -> Strategy instance
        self._agent_strategy_map: Dict[int, object] = {}
        
        # Strategy type tracking: Agent ID -> Strategy class type
        self._agent_strategy_type_map: Dict[int, Type[object]] = {}
    
    def bind_one(self, agent: BaseAgent) -> object:
        """
        Bind a strategy to a single agent.
        
        If the agent already has a strategy mapping and the strategy type hasn't changed,
        returns the existing strategy. If the strategy type has changed, instantiates
        a new strategy and replaces the old mapping.
        
        Args:
            agent: The agent to bind a strategy to
            
        Returns:
            The strategy object for the agent
        """
        agent_id = agent.id
        
        # Determine the appropriate strategy type for the agent
        if isinstance(agent, FemaleAgent):
            strategy_type = FemaleStrategy
        elif isinstance(agent, MaleAgent):
            strategy_type = MaleStrategy
        else:
            raise ValueError(f"Unsupported agent type: {type(agent).__name__}")
        
        # Check if agent already has a strategy mapping
        if agent_id in self._agent_strategy_map:
            current_strategy = self._agent_strategy_map[agent_id]
            current_strategy_type = self._agent_strategy_type_map[agent_id]
            
            # If strategy type hasn't changed, return existing strategy
            if current_strategy_type == strategy_type:
                return current_strategy
            
        # Either no existing mapping or strategy type changed
        # Create new strategy and update mappings
        new_strategy = strategy_type(self.belief_system)
        self._agent_strategy_map[agent_id] = new_strategy
        self._agent_strategy_type_map[agent_id] = strategy_type
        
        return new_strategy
    
    def bind_all(self, agent_list: List[BaseAgent]) -> None:
        """
        Batch bind strategies to all agents in the list.
        
        This method is typically called by game_loop before daily decisions.
        
        Args:
            agent_list: List of agents to bind strategies to
        """
        for agent in agent_list:
            self.bind_one(agent)
    
    def get_strategy(self, agent: BaseAgent) -> Optional[object]:
        """
        Get the strategy object for a given agent.
        
        This method is used by game_loop to quickly retrieve the current day's strategy object
        when iterating through agents.
        
        Args:
            agent: The agent to get the strategy for
            
        Returns:
            The strategy object for the agent, or None if not found
        """
        return self._agent_strategy_map.get(agent.id)