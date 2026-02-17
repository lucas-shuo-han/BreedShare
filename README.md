# Breed Share

Agent-based model simulating mating system dynamics via energy allocation strategies.

## Core Idea

This model abstracts all reproductive behaviors as allocations of a finite energy budget between **search** (exploring for mates/territories) and **raising** (investing in nest care). By tracking how individuals optimize this trade-off under varying resource distributions, the model explores how spatiotemporal resource patterns drive the evolution of mating systems—from monogamy to polyandry and polygyny.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/lucas-shuo-han/BreedShare.git

# Install dependencies
pip install numpy
# Dependencies: numpy

# Configure simulation parameters in config/config.py
# Then run the simulation
python main.py
```

## Configuration

All simulation parameters are defined in `config/config.py`. Key parameter groups include:

| Group | Key Parameters |
|-------|----------------|
| **World Generation** | `GRID_SIZE` (500), `RESOURCE_LEVEL` (100), `AGGREGATION_LEVEL` (5) |
| **Agent Counts** | `initial_female_count` (20), `initial_male_count` (20) |
| **Search Behavior** | `SEARCH_COST` (λ, search efficiency constant) |
| **Fitness Calculation** | `LOGISTIC_K` (10), `LOGISTIC_R` (0.1), `LOGISTIC_A` (100) |
| **Resource Extraction** | `RESOURCE_EXTRACTION_RATE` (ρ, extraction rate, 0.3) |
| **Allocation Algorithm** | `ALLOCATION_STEPS` (20), `MARGINAL_DELTA` (0.01) |

See the full documentation for detailed parameter descriptions and valid ranges.

## Basic Usage

Run a simulation with default parameters:

```bash
python main.py
```

The simulation will:
1. Generate a 500×500 resource landscape using negative binomial distribution
2. Initialize female and male agents with random positions
3. Run the specified number of rounds (default: 5)
4. Output per-round fitness data and nest state statistics

## Output

The simulation produces:

- **Daily nest resources**: Resource accumulation per nest per round
- **Agent fitness**: Individual payoff calculations for males and females
- **Mating system statistics**: Nest composition, resource allocation patterns, fitness distributions
- **Debug logs**: Strategy decisions and system states are logged to `breed_share_debug.log`

### Debug Logging (Pluggable Component)

The debug logging module is a pluggable code component located in `simulation/game_loop.py`. It records:
- Agent strategy decisions (search_share and raising_shares)
- System state changes
- Runtime information for debugging and analysis

**Features:**
- Default log file: `breed_share_debug.log`
- Log level: INFO and above
- Format: timestamp - log level - message

**Future Extensions:**
- The log data can be used for visualization and analysis
- Integrate with machine learning and genetic algorithm training
- Generate statistical reports and visualizations by parsing log files

## Documentation

For comprehensive details, consult the documentation in the `docs/` folder:

- **`Requirements_Document.md`**: Full project requirements, modeling philosophy, functional specifications, and biological justifications
- **`Technical_Document.md`**: Technical architecture, module details, implementation notes, algorithms, and mathematical formulations

## Project Structure

```
├── agents/
│   ├── __init__.py
│   ├── female_agent.py      # Female agent state
│   ├── male_agent.py        # Male agent state
│   └── nest.py              # Nest data class
├── config/
│   ├── __init__.py
│   └── config.py            # All simulation parameters
├── core/
│   ├── __init__.py
│   ├── base_agent.py        # Agent base class
│   ├── base_strategy.py     # Strategy abstract base class
│   └── fitness.py           # Fitness calculation functions
├── docs/
│   ├── Requirements_Document.md
│   └── Technical_Document.md
├── initializer/
│   ├── __init__.py
│   └── bootstrap.py         # System initialization
├── simulation/
│   ├── __init__.py
│   ├── game_loop.py         # Main simulation loop
│   └── orchestrator.py      # Agent-strategy binding
├── strategies/
│   ├── __init__.py
│   ├── belief_system.py     # Bayesian belief updates
│   ├── female_strategy.py   # Female decision logic
│   └── male_strategy.py     # Male decision logic
├── test/
│   └── test_home_range.py
├── world/
│   ├── __init__.py
│   ├── world_generator.py   # Resource map generation
│   └── world_state.py       # Environment state management
├── .gitignore
├── README.md
├── TODO.md
└── main.py                  # Entry point
```

## License

This project is released under the MIT License. See LICENSE for details.

## Citation

If you use this model in your research, please cite:

```
Breed Share. (2024). Agent-based simulation of mating 
system dynamics via energy allocation strategies. 
GitHub: <repository-url>
```

Key references used in model development:
- Birkhead (1981) - Territory establishment and social learning
- Davies & Lundberg (1984) - Resource-driven territory dynamics
- Davies (1986) - Parental investment and fitness functions
- Bishton (1986) - Spatial distribution patterns

