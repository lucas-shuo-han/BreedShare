# initializer/bootstrap.py
from typing import List, Tuple, Set, Literal
import numpy as np
from numpy.typing import NDArray
import random
from world.world_generator import WorldGenerator
from world.world_state import WorldState
from core.base_agent import BaseAgent
from agents.female_agent import FemaleAgent
from agents.male_agent import MaleAgent
from strategies.belief_system import BeliefSystem
from simulation.orchestrator import Orchestrator
from config.config import GRID_SIZE, RESOURCE_LEVEL, AGGREGATION_LEVEL, INITIAL_FEMALE_COUNT, INITIAL_MALE_COUNT, HOME_RANGE_RADIUS


def bootstrap() -> Tuple[WorldState, List[FemaleAgent], List[MaleAgent], Orchestrator]:
    """
    Initialize simulation world, agents, nests, and orchestrator.
    
    Returns:
        Tuple containing: WorldState, List[FemaleAgent], List[MaleAgent], Orchestrator
    """
    # 1. Generate resource map and world state
    world_generator = WorldGenerator(GRID_SIZE, RESOURCE_LEVEL, AGGREGATION_LEVEL)
    resource_map: NDArray[np.float32] = world_generator.generate_resources()
    world_state = WorldState(resource_grid = resource_map)
    
    # 2. Spawn agents with initial positions (uniform random)
    female_agents = [agent for agent in _spawn_agents(INITIAL_FEMALE_COUNT, "female", world_state) if isinstance(agent, FemaleAgent)]
    male_agents = [agent for agent in _spawn_agents(INITIAL_MALE_COUNT, "male", world_state) if isinstance(agent, MaleAgent)]
    
    # 3. Allocate nests for female agents only
    _allocate_nests(female_agents, world_state, nest_radius=50, nests_per_agent=2)
    
    # 4. Initialize male nest assignments
    _initialize_male_nest_assignments(male_agents, world_state, nests_per_male=2, min_search_share=0.05)
    
    # 5. Initialize belief system and orchestrator
    belief_system = BeliefSystem()
    orchestrator = Orchestrator(world_state, belief_system)
    
    # 6. Bind strategies to all agents
    all_agents = female_agents + male_agents
    orchestrator.bind_all(all_agents)
    
    return world_state, female_agents, male_agents, orchestrator


def _spawn_agents(count: int, agent_type: Literal["female", "male"], world_state: WorldState) -> List[BaseAgent]:
    """
    Spawn agents with uniform random initial positions.
    
    Args:
        count: Number of agents to spawn
        agent_type: Agent type, must be "female" or "male"
        world_state: Current world state
        
    Returns:
        List of spawned agents
    """
    agents: List[BaseAgent] = []
    
    # Get next available ID from existing agents in world state
    next_agent_id = max(world_state.agents.keys()) + 1 if world_state.agents else 1
    
    for i in range(count): # type: ignore
        # Generate uniform random position within grid bounds
        x = random.randint(0, world_state.grid_size - 1)
        y = random.randint(0, world_state.grid_size - 1)
        position = (x, y)
        
        # Create agent based on type
        agent_id = next_agent_id + i
        if agent_type == "female":
            agent = FemaleAgent(id=agent_id, position=position)
        elif agent_type == "male":
            agent = MaleAgent(id=agent_id, position=position)
        else:
            raise ValueError(f"Invalid agent type: {agent_type}")
        
        agents.append(agent)
        world_state.agents[agent.id] = agent
    
    return agents


def _allocate_nests(agents: List[BaseAgent], world_state: WorldState, 
                   nest_radius: int, nests_per_agent: int) -> None:
    """
    Allocate nests for each female agent in the best resource locations within fixed radius.
    
    Args:
        agents: List of agents to allocate nests for
        world_state: Current world state
        nest_radius: Radius to search for nest locations
        nests_per_agent: Number of nests to allocate per agent
    """
    for agent in agents:
        # Get all cells within nest_radius from agent's position
        x, y = agent.position
        candidate_cells: List[Tuple[int, int]] = []
        
        # Generate all cells within nest_radius
        for dx in range(-nest_radius, nest_radius + 1):
            for dy in range(-nest_radius, nest_radius + 1):
                if dx * dx + dy * dy <= nest_radius * nest_radius:
                    cell_x = x + dx
                    cell_y = y + dy
                    if 0 <= cell_x < world_state.grid_size and 0 <= cell_y < world_state.grid_size:
                        candidate_cells.append((cell_x, cell_y))
        
        # Sort cells by resource density in descending order
        candidate_cells.sort(
            key=lambda cell: world_state.get_resource_density(cell),
            reverse=True
        )
        
        # Select top nests_per_agent cells for nests
        selected_cells = candidate_cells[:nests_per_agent]
        
        # Create nests for the agent
        for cell in selected_cells:
            # Calculate home range for this nest (10 grid units around nest)
            home_range: Set[Tuple[int, int]] = set()
            nest_x, nest_y = cell
            for dx in range(-HOME_RANGE_RADIUS, HOME_RANGE_RADIUS + 1):
                for dy in range(-HOME_RANGE_RADIUS, HOME_RANGE_RADIUS + 1):
                    hr_x = nest_x + dx
                    hr_y = nest_y + dy
                    if 0 <= hr_x < world_state.grid_size and 0 <= hr_y < world_state.grid_size:
                        home_range.add((hr_x, hr_y))
            
            # Create nest and associate with agent using WorldState's public method
            nest_id = world_state.create_nest_for_female(agent.id, cell)
            nest = world_state.nests[nest_id]
            nest.home_range_cells = home_range
            
            # Add nest ID to agent's nest list
            if isinstance(agent, FemaleAgent):
                agent.nest_ids.add(nest.id)


def _initialize_male_nest_assignments(male_agents: List[MaleAgent], 
                                     world_state: WorldState, 
                                     nests_per_male: int = 2, 
                                     min_search_share: float = 0.05) -> None:
    """
    Initialize male nest assignments with random raising share distribution.
    Each male gets nests_per_male nests with random raising share proportions summing to 1.
    """
    all_nests = list(world_state.nests.keys())
    if not all_nests:
        return

    for i, male in enumerate(male_agents): # type: ignore
        # Generate random search share between min and max
        search_share = random.uniform(min_search_share, 0.95)
        raising_share_available = 1.0 - search_share
        
        # Get random nests for this male
        male_nests = random.sample(all_nests, nests_per_male)
        
        # Generate random proportions that sum to 1
        weights = [random.random() for _ in range(nests_per_male)]
        total_weight = sum(weights)
        proportions = [w / total_weight for w in weights]
        
        # Assign nests and distribute raising shares proportionally
        for j, nest_id in enumerate(male_nests):
            male.assign_to_nest(nest_id, "alpha")
            raising_share = raising_share_available * proportions[j]
            
            nest = world_state.nests[nest_id]
            nest.male_raising_shares[male.id] = raising_share
            nest.add_male(male.id)

        
    
