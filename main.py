# main.py
# Entry point for the simulation system
from initializer.bootstrap import bootstrap
from simulation.game_loop import GameLoop
from config.config import LOOP_ROUND


def main():
    """
    Main function to run the simulation.
    
    Steps:
    1. Initialize simulation environment using bootstrap
    2. Run game loop for the specified number of days
    """
    # Configuration is now loaded from config/config.py - THE SOURCE OF TRUTH
    print("Loading configuration from config/config.py...")
    
    # 1. Initialize simulation environment
    print("Initializing simulation environment...")
    world_state, female_agents, male_agents, orchestrator = bootstrap()
    
    # 2. Run game loop
    num_days = LOOP_ROUND
    print(f"Starting simulation for {num_days} days...")
    game_loop = GameLoop(world_state, female_agents, male_agents, orchestrator)
    simulation_results = game_loop.run(num_days)
    
    print(f"Simulation completed successfully!")


if __name__ == "__main__":
    main()
