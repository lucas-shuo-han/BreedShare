# simulation/game_loop.py
import random
import logging
from typing import List, Dict, Tuple, Any, cast
from world.world_state import WorldState
from core.base_agent import BaseAgent
from agents.female_agent import FemaleAgent
from agents.male_agent import MaleAgent
from agents.nest import Nest
from simulation.orchestrator import Orchestrator
from strategies.female_strategy import FemaleStrategy
from strategies.male_strategy import MaleStrategy
from core.fitness import mine_resources
from analysis.mating_system_analyzer import MatingSystemAnalyzer

# Set up logging for strategy decisions
logging.basicConfig(
    filename='mating_system_debug.log',
    level=logging.INFO,  # Set to INFO to capture strategy decisions
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'  # Overwrite log file each time
)


def handle_male_joining_nest(male: MaleAgent, nest_id: int, role: str, 
                                world_state: WorldState, 
                                females: Dict[int, FemaleAgent]):
    """Ensure state consistency when a male joins a nest."""
    
    # 1. Update male's own role
    male.assign_to_nest(nest_id, role)
    
    # 2. Update nest object
    nest = world_state.nests[nest_id]
    nest.add_male(male.id)
    
    # 3. Update female's male count (find female through nest)
    if nest.female_id is not None:
        female = females[nest.female_id]
        female.add_male_to_nest()


class GameLoop:
    """
    GameLoop: Manages the daily strategy and action flow.
    
    Responsibilities:
    1. Daily world snapshot acquisition
    2. Agent strategy decision processing
    3. Action list generation and execution
    4. Resource extraction and nest resource accumulation
    5. World state resource reset after each round
    """
    
    def __init__(self, world_state: WorldState, female_agents: List[FemaleAgent], 
                 male_agents: List[MaleAgent], orchestrator: Orchestrator):
        """
        Initialize GameLoop with simulation components.
        
        Args:
            world_state: Current world state
            female_agents: List of all female agents
            male_agents: List of all male agents
            orchestrator: Strategy orchestration manager
        """
        self.world_state = world_state
        self.female_agents = female_agents
        self.male_agents = male_agents
        self.orchestrator = orchestrator
        
        # Convert agent lists to dictionaries for quick access
        self._female_dict = {agent.id: agent for agent in female_agents}
        self._male_dict = {agent.id: agent for agent in male_agents}
        self._all_agents = female_agents + male_agents
        
        # Daily strategy cache: Agent ID -> Strategy decisions
        self._daily_strategy_cache: Dict[int, Dict[str, Any]] = {}
        
        # Mating system analyzer for daily statistics
        self.mating_system_analyzer = MatingSystemAnalyzer()
    
    def run(self, num_days: int) -> Dict[str, Any]:
        """
        Run the simulation for the specified number of days.
        
        Args:
            num_days: Number of days to run the simulation
            
        Returns:
            Simulation results summary
        """
        results: Dict[str, Any] = {
            'days_completed': 0,
            'daily_nest_resources': [],
            'agent_fitness': {},
            'mating_system_analyzer': self.mating_system_analyzer
        }
        
        for day in range(num_days):
            print(f"Day {day + 1} of {num_days}...")
            
            # Run one day of simulation
            daily_results = self._run_one_day()
            
            # Record daily results
            results['daily_nest_resources'].append(daily_results['nest_resources'])
            
            # Record mating system statistics for this day
            self.mating_system_analyzer.record_daily_statistics(day, self.world_state, self.male_agents)
            
            # Increment completed days
            results['days_completed'] += 1
        
        return results
    
    def _run_one_day(self) -> Dict[str, Any]:
        """
        Run a single day of the simulation.
        
        Returns:
            Dictionary containing daily simulation results
        """
        # 1. Get current world snapshot from WorldState
        world_snapshot = self._get_world_snapshot()
        
        # 2. Bind strategies for all agents at the start of the day
        self.orchestrator.bind_all(cast(List[BaseAgent], self._all_agents))
        
        # 3. Iterate through each agent to get their strategies
        self._collect_agent_strategies(world_snapshot)
        
        # 4. Generate action list from strategies
        action_list = self._generate_action_list()
        
        # 5. Shuffle action list for random execution order
        random.shuffle(action_list)
        
        # 6. Execute actions in random order
        nest_resources = self._execute_actions(action_list)
        
        # 7. Reset world state resources after each round
        self._reset_world_resources()
        
        return {'nest_resources': nest_resources}
    
    def _get_world_snapshot(self) -> Dict[str, Any]:
        """
        Get world snapshot from WorldState.
        
        Returns:
            Dictionary containing resource distribution and all agent positions
        """
        return {
            'resource_distribution': self.world_state.resource_grid,
            'agent_positions': {
                agent.id: agent.position for agent in self._all_agents
            },
            'nest_locations': self.world_state.get_nest_locations()
        }
    
    def _collect_agent_strategies(self, world_snapshot: Dict[str, Any]) -> None:
        """
        Collect strategies from all agents.
        
        Args:
            world_snapshot: Current world snapshot
        """
        import logging
        
        self._daily_strategy_cache.clear()
        
        for agent in self._all_agents:
            # Get strategy from orchestrator
            strategy = self.orchestrator.get_strategy(agent)
            
            if strategy is None:
                continue
            
            # Get agent's strategy decisions for this round
            if isinstance(agent, FemaleAgent) or isinstance(agent, MaleAgent):
                # Get allocation from strategy
                allocation = strategy.allocate_shares(agent.id, self.world_state)
                
                # Cache the strategy decisions
                self._daily_strategy_cache[agent.id] = {
                    'search_share': allocation.get('search_share', 0.0),
                    'raising_shares': allocation.get('raising_shares', {})
                }
                
                # Log strategy decisions
                agent_type = "Female" if isinstance(agent, FemaleAgent) else "Male"
                logging.info(f"{agent_type} Agent {agent.id} - search_share: {allocation.get('search_share', 0.0):.3f}, raising_shares: {allocation.get('raising_shares', {})}")
            else:
                continue
    
    def _generate_action_list(self) -> List[Tuple[str, BaseAgent, int, float]]:
        """
        Generate action list from search_share and raising_share > 0.
        
        Returns:
            List of tuples (ActionType, Agent, Nest ID, share)
            ActionType can be 'search' or 'raise'
        """
        action_list = []
        
        for agent_id, strategy in self._daily_strategy_cache.items():
            agent = self._female_dict.get(agent_id) or self._male_dict.get(agent_id)
            
            if agent is None:
                continue
            
            # Get search share for this agent
            search_share = strategy['search_share']
            
            # Get raising shares for this agent
            raising_shares = strategy['raising_shares']
            
            # Add search action if search_share > 0
            if search_share > 0:
                # For search, we'll add it for all nests the agent is involved with
                for nest_id, raising_share in raising_shares.items():
                    if raising_share > 0:
                        action_list.append(('search', agent, nest_id, search_share))
            
            # Add raise actions for raising_share > 0
            for nest_id, raising_share in raising_shares.items():
                if raising_share > 0:
                    action_list.append(('raise', agent, nest_id, raising_share))
        
        return action_list
    
    def _execute_actions(self, action_list: List[Tuple[str, BaseAgent, int, float]]) -> Dict[int, float]:
        """
        Execute actions in random order.
        
        Args:
            action_list: List of actions to execute
            
        Returns:
            Dictionary containing accumulated resources for each nest
        """
        nest_resources = {}
        
        for action_type, agent, nest_id, share in action_list:
            if action_type == 'search':
                # Execute search action
                self._execute_search(agent, nest_id, share)
            elif action_type == 'raise':
                # Execute raise action
                resource_amount = self._execute_raise(agent, nest_id, share)
                
                # Accumulate nest resources
                if nest_id in nest_resources:
                    nest_resources[nest_id] += resource_amount
                else:
                    nest_resources[nest_id] = resource_amount
                
                # If this is a male agent with positive raising share, ensure state consistency
                if isinstance(agent, MaleAgent) and share > 0:
                    # Determine role based on raising share (simplified)
                    # TODO: Implement alpha and beta role distinction based on raising share or other factors
                    role = "alpha"  # Default role for now, could be more complex
                    handle_male_joining_nest(agent, nest_id, role, self.world_state, self._female_dict)
                    # Update male_raising_shares in the nest
                    nest = self.world_state.nests[nest_id]
                    nest.male_raising_shares[agent.id] = share
        
        return nest_resources
    
    def _execute_search(self, agent: BaseAgent, nest_id: int, search_share: float) -> None:
        """
        Execute search action for an agent.
        
        Args:
            agent: Agent performing the search
            nest_id: Nest ID being searched
            raising_share: Raising share for this nest
        """
        # Get search share from agent's strategy
        strategy = self._daily_strategy_cache[agent.id]
        search_share = strategy['search_share']
        
        if search_share > 0:
            # Move agent to the nest location before searching
            nest = self.world_state.nests[nest_id]
            agent.move_to(nest.position)
            
            # Query nest composition using WorldState
            nest_details = self.world_state.query_nest_composition(
                agent_id=agent.id,
                nest_id=nest_id,
                search_share=search_share
            )
            
            # Add search results to agent's knowledge base (belief_system)
            # Note: Belief update functionality is currently handled in the strategy's allocate_shares method
            # and through the submit_observation methods, not directly from nest_details
    
    def _execute_raise(self, agent: BaseAgent, nest_id: int, raising_share: float) -> float:
        """
        Execute raise action for an agent.
        
        Args:
            agent: Agent performing the raising
            nest_id: Nest ID being raised
            raising_share: Raising share for this nest
            
        Returns:
            Amount of resources extracted and added to the nest
        """
        # Move agent to the nest location before raising
        nest = self.world_state.nests[nest_id]
        agent.move_to(nest.position)
        
        # Call mine_resources from fitness.py to handle resource extraction
        extracted_resources = mine_resources(
            world_state=self.world_state,
            nest_id=nest_id,
            raising_share=raising_share
        )
        
        return extracted_resources
    
    def _reset_world_resources(self) -> None:
        """
        Reset world state resources after each round.
        
        This method regenerates resources using the negative binomial distribution
        as mentioned in the technical documentation.
        """
        # Reset world resources using negative binomial distribution
        self.world_state.reset_resources()
        
        # Clear all accumulated resources from nests
        self.world_state.clear_all_nest_resources()
