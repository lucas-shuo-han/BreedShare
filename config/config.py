# config.py
# Configuration constants for the simulation - THE SOURCE OF TRUTH

# Global parameters
RANDOM_SEED = 42  # Random seed for reproducibility

# World parameters (for world/world_generator.py)
GRID_SIZE = 500  # grid size for the world, unchanged
RESOURCE_LEVEL = 0.5  # resource level, between 0 and 1, higher means more resource
AGGREGATION_LEVEL = 0.3  # aggregation level, between 0 and 1, higher means more aggregation

# Agent parameters
INITIAL_FEMALE_COUNT = 30  # initial number of female agents
INITIAL_MALE_COUNT = 30  # initial number of male agents

# Search parameters (for core/base_agent.py)
SEARCH_COST = 0.3  # search cost, between 0 and 1, higher means more cost
MIN_SEARCH_SHARE = 0.05  # Minimum search share that agents can allocate
MAX_SEARCH_RADIUS = 50.0  # Maximum search radius baseline value

# Resource mining parameters
RESOURCE_EXTRACTION_RATE = 0.3  # rho - extraction rate per mining action
HOME_RANGE_RADIUS = 3  # Radius of home range for resource exploration

# Reproductive success parameters (logistic function) - for raising fledglings
LOGISTIC_K = 10.0  # Maximum number of viable fledglings
LOGISTIC_A = 1e-6  # Initial level of logistic function
LOGISTIC_R = 0.1   # Conversion efficiency of resources

# Simulation parameters
LOOP_ROUND = 10  # number of days to run the simulation

# Raising share allocation parameters (for greedy iterative allocation algorithm)
MARGINAL_DELTA = 0.01  # Step size for numerical differentiation (marginal utility calculation)
ALLOCATION_STEPS = 20  # Number of steps for greedy iterative allocation algorithm

# Belief system parameters
SEARCH_BELIEF_PRIOR_ALPHA = 1.0
SEARCH_BELIEF_PRIOR_BETA = 9.0
SEARCH_BELIEF_INITIAL_MEAN = 0.1
RAISING_BELIEF_INITIAL_MEAN = 0.45