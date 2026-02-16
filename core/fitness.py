# core/fitness.py
import agents.nest as nest
import math
from typing import Tuple, Set, Optional
from world.world_state import WorldState
from config.config import RESOURCE_EXTRACTION_RATE, HOME_RANGE_RADIUS, LOGISTIC_K, LOGISTIC_A, LOGISTIC_R

def calculate_female_fitness(nest: nest.Nest, world_state: WorldState) -> float:
    """
    Calculate the fitness of a female agent in a nest.
    
    Args:
        nest: The nest where the female agent is located
        world_state: The current world state
        
    Returns:
        The fitness of the female agent
    """
    # payoff is just the number of surviving fledglings
    return resource_to_fledglings(nest.get_total_resources(world_state))

def calculate_male_fitness(nest: nest.Nest, male_id: int, world_state: WorldState) -> float:
    """
    Calculate the fitness of a male agent in a nest.
    
    Args:
        nest: The nest where the male agent is located
        male_id: The ID of the male agent
        world_state: The current world state
        
    Returns:
        The fitness of the male agent
    """
    # payoff is just the number of surviving fledglings multiplied buy the male's raising_share contribution share.
    total_male_share = nest.get_male_raising_share()
    
    # Handle case where total male share is zero to avoid division by zero
    if total_male_share == 0:
        return 0.0
    
    paternity_share = nest.male_raising_share(male_id) / total_male_share
    return resource_to_fledglings(nest.get_total_resources(world_state)) * paternity_share

def resource_to_fledglings(total_resources: float) -> float:
    """
    Convert total resources to the number of expected surviving fledglings.
    
    Args:
        total_resources: The total resources available for the nest.
        
    Returns:
        The number of expected surviving fledglings
    """
    return LOGISTIC_K / (1 + LOGISTIC_A * math.exp(- total_resources * LOGISTIC_R))


def mine_resources(world_state: WorldState, nest_id: int, raising_share: float) -> float:
    """
    Main function to mine resources based on raising_share.
    
    Args:
        world_state: The current world state
        nest_id: The ID of the nest to mine for
        raising_share: The raising share (0.0-1.0)
        
    Returns:
        The amount of resources mined
    """
    nest = world_state.nests[nest_id]
    
    # Step 1: Determine exploration area
    home_range = determine_exploration_area(world_state, nest.position, raising_share)
    
    # Step 2: Select target patch with maximum resource density
    target_pos = select_target_patch(world_state, home_range)
    
    # Step 3: Extract resources if target found
    if target_pos:
        extracted = extract_resources(world_state, target_pos)
        nest.add_resources(extracted)
        return extracted
    return 0.0


def determine_exploration_area(world_state: WorldState, nest_position: Tuple[int, int], raising_share: float) -> Set[Tuple[int, int]]:
    """
    Determine exploration area based on raising_share and home range radius.
    
    Args:
        world_state: The current world state
        nest_position: The position of the nest
        raising_share: The raising share (0.0-1.0)
        
    Returns:
        Set of cells in the exploration area
    """
    # Calculate effective exploration radius based on raising_share
    # The more resources invested in raising (higher raising_share), the larger the exploration area
    base_radius = HOME_RANGE_RADIUS * raising_share  # Continuous value radius
    effective_radius = int(base_radius)  # Convert to integer grid cells
    
    # Ensure minimum exploration area: even with very small raising_share, the agent
    # will still explore at least a 1-cell radius (the immediate surrounding area)
    effective_radius = max(effective_radius, 1)
    
    x, y = nest_position
    home_range: set[Tuple[int, int]] = set()
    
    # Add all cells within effective radius
    for dx in range(-effective_radius, effective_radius + 1):
        for dy in range(-effective_radius, effective_radius + 1):
            if dx*dx + dy*dy <= effective_radius*effective_radius:
                cell_x, cell_y = x + dx, y + dy
                if 0 <= cell_x < world_state.grid_size and 0 <= cell_y < world_state.grid_size:
                    home_range.add((cell_x, cell_y))
    
    return home_range


def select_target_patch(world_state: WorldState, home_range: Set[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    """
    Select the target patch with maximum resource density in the exploration area.
    
    Args:
        world_state: The current world state
        home_range: The set of cells in the exploration area
        
    Returns:
        The position of the target patch, or None if no valid cells
    """
    if not home_range or world_state.resource_grid is None:
        return None
    
    # Find cell with maximum resource density
    max_density = -1.0
    target_pos = None
    
    for cell in home_range:
        density = world_state.get_resource_density(cell)
        if density > max_density:
            max_density = density
            target_pos = cell
    
    return target_pos if max_density > 0.0 else None


def extract_resources(world_state: WorldState, position: Tuple[int, int]) -> float:
    """
    Extract resources from the specified position at a fixed rate.
    
    Args:
        world_state: The current world state
        position: The position to extract resources from
        
    Returns:
        The amount of resources extracted
    """
    if world_state.resource_grid is None:
        return 0.0
    
    density = world_state.get_resource_density(position)
    return density * RESOURCE_EXTRACTION_RATE


def calculate_female_fitness_counterfactual(
    my_raise: float,
    others_raise: float,
    nest_position: Tuple[int, int],
    world_state: WorldState
) -> float:
    """
    Pure function to calculate counterfactual fitness for female agents.
    
    Args:
        my_raise: This agent's hypothetical investment
        others_raise: Belief about total investment from other agents
        nest_position: Position of the nest
        world_state: Read-only world state for resource queries
        
    Returns:
        Fitness value in the counterfactual scenario
    """
    total_investment = my_raise + others_raise
    
    # Calculate exploration area based on total investment
    home_range = determine_exploration_area(world_state, nest_position, total_investment)
    
    # Find target patch with maximum resource density
    target_pos = select_target_patch(world_state, home_range)
    
    # Extract resources if target found
    total_resources = 0.0
    if target_pos:
        total_resources = extract_resources(world_state, target_pos)
    
    # Convert resources to fledglings using logistic function
    return resource_to_fledglings(total_resources)


def calculate_male_fitness_counterfactual(
    my_raise: float,
    others_raise: float,
    nest_position: Tuple[int, int],
    world_state: WorldState
) -> float:
    """
    Pure function to calculate counterfactual fitness for male agents.
    
    Args:
        my_raise: This agent's hypothetical investment
        others_raise: Belief about total investment from other male agents
        nest_position: Position of the nest
        world_state: Read-only world state for resource queries
        
    Returns:
        Fitness value in the counterfactual scenario
    """
    # Male payoff is proportional to his share of total male investment
    total_male_investment = my_raise + others_raise
    
    if total_male_investment == 0:
        return 0.0
    
    paternity_share = my_raise / total_male_investment
    
    # Calculate total resources available to the nest
    total_investment = total_male_investment  # Female's share is handled in others_raise
    home_range = determine_exploration_area(world_state, nest_position, total_investment)
    target_pos = select_target_patch(world_state, home_range)
    
    total_resources = 0.0
    if target_pos:
        total_resources = extract_resources(world_state, target_pos)
    
    # Convert resources to fledglings and multiply by paternity share
    return resource_to_fledglings(total_resources) * paternity_share
