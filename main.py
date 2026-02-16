# main.py
# Entry point for the simulation system
import os
from initializer.bootstrap import bootstrap
from simulation.game_loop import GameLoop
from analysis.reporter import Reporter
from config.config import LOOP_ROUND


def main():
    """
    Main function to run the simulation.
    
    Steps:
    1. Initialize simulation environment using bootstrap
    2. Run game loop for the specified number of days
    3. Generate and output simulation results report
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
    
    # 5. Generate and output report
    print("Generating simulation report...")
    reporter = Reporter(world_state,
                        {agent.id: agent for agent in female_agents},
                        {agent.id: agent for agent in male_agents},
                        orchestrator)
    report_path = os.path.join('results', 'simulation_report.pdf')
    reporter.generate_report(simulation_results, report_path)
    
    print(f"Simulation completed successfully!")


if __name__ == "__main__":
    main()
