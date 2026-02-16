# Wren Mating System Modeling Project - Technical Document (Final)

---

## 1. Technical Architecture

### 1.1 Layered Generative Architecture

This project adopts a layered generative architecture, with construction sequence following the logical chain from environment to individuals to interactions:

**Layer 1: World Environment Generation**
- `world_generator.py`: Creates 500×500 resource map based on negative binomial distribution, parameterizing total resource amount and spatial aggregation
- `world_state.py`: Serves as environment state registry center, managing all Nest entities and global information query interfaces

**Layer 2: Agent State Entities**
- `agents/nest.py`: Exists as core independent entity, carrying location, home_range, and male/female participants
- `agents/female_agent.py` and `male_agent.py`: Only implement state attributes and mechanical behavior methods (e.g., search functionality), contain no decision logic

**Layer 3: Strategy Decision Logic**
- `strategies/belief_system.py`: Maintains population behavior frequency statistics, supports Bayesian updates
- `strategies/female_strategy.py` and `male_strategy.py`: Implement `decide_search_share()` and `decide_raising_allocation()` interfaces, transforming biological constraints into optimization problems

**Layer 4: Simulation Execution Coordination**
- `simulation/game_loop.py`: Manages daily micro-step iteration and Shuffle mechanism
- `simulation/orchestrator.py`: Serves as runtime binding layer, dynamically associating Agents with Strategies, ensuring state consistency

**Layer 5: Analysis Output**
- `analysis/reporter.py` or `analysis/mating_system_analyzer.py`: Collects simulation data and generates statistical summaries and visualizations

This architecture achieves 100% external configuration of parameters through `config/config.yaml` or `config/config.py`, with all inter-layer interfaces using type annotations as contracts.

### 1.2 Project Directory Structure

**Version 1 Structure (from technical_documentation.md)**:
```
project/
├── config/
│   └── config.yaml          # All parameters must be defined here, no hard-coding
├── core/
│   ├── base_agent.py        # Define Agent base class
│   ├── base_strategy.py     # Define Strategy abstract base class
│   └── fitness.py           # Fitness calculation pure functions
├── agents/
│   ├── nest.py              # Nest data class
│   ├── female_agent.py      # FemaleAgent data class
│   └── male_agent.py        # MaleAgent data class
├── strategies/
│   ├── belief_system.py     # Belief update implementation
│   ├── female_strategy.py   # Female decision implementation
│   └── male_strategy.py     # Male decision implementation
├── simulation/
│   ├── game_loop.py         # Main loop: shuffle -> execute
│   └── orchestrator.py      # Agent-Strategy binding and state sync
├── world/
│   ├── world_generator.py   # Resource map generator
│   └── world_state.py       # Environment state manager
├── analysis/
│   └── reporter.py          # Result summary
└── initializer/
    └── bootstrap.py         # System initialization
```

**Version 2 Structure (from technical_documentation_new.md)**:
```
CurrentVersion/
├── config/
│   └── config.py            # All configuration parameter definitions
├── core/
│   ├── base_agent.py        # Agent base class definition
│   ├── base_strategy.py     # Strategy abstract base class
│   └── fitness.py           # Fitness calculation functions
├── agents/
│   ├── nest.py              # Nest data class
│   ├── female_agent.py      # FemaleAgent class
│   └── male_agent.py        # MaleAgent class
├── strategies/
│   ├── belief_system.py     # Belief update system
│   ├── female_strategy.py   # Female decision implementation
│   └── male_strategy.py     # Male decision implementation
├── simulation/
│   ├── game_loop.py         # Main loop implementation
│   └── orchestrator.py      # Agent-Strategy binding and state sync
├── world/
│   ├── world_generator.py   # Resource map generator
│   └── world_state.py       # Environment state manager
├── analysis/
│   └── mating_system_analyzer.py  # Mating system analyzer
├── initializer/
│   └── bootstrap.py         # System initialization
├── main.py                  # Program entry
└── docs/
    └── technical_documentation_new.md  # Technical implementation document
```

**Note**: Different versions show variations in configuration file format (config.yaml vs config.py) and analysis module naming (reporter.py vs mating_system_analyzer.py). [Note: conflicting information from versions, please verify]

---

## 2. Core Module Implementation Details

### 2.1 Program Entry and Initialization

#### 2.1.1 main.py

**Responsibility**: Program entry point, responsible for launching the entire simulation system.

**Functions**:
- **Read Configuration File**: Load all parameters from `config.yaml` or use `config.py` definitions
- **Initialize System**: Call initialization function in `initializer/bootstrap.py` to obtain initial state (including world, Agent list, and Orchestrator)
- **Start Simulation Loop**: Pass initialized state to `simulation/game_loop.py` to begin day-by-day simulation advancement
- **Generate Report**: After simulation ends, call `analysis/reporter.py` or report generation function to generate result report

**Key Points**:
- `main.py` does not directly participate in any specific initialization logic, only responsible for calling and passing control
- It is the "commander" of the entire program, ensuring modules start in sequence

**Code Example**:
```python
def main():
    world_state, female_agents, male_agents, orchestrator = bootstrap()
    game_loop = GameLoop(world_state, female_agents, male_agents, orchestrator)
    simulation_results = game_loop.run(num_days)
    reporter.generate_report(simulation_results, report_path)
```

#### 2.1.2 initializer/bootstrap.py

**Responsibility**: Responsible for building complete initial state before simulation starts, generating all necessary objects and initial configurations.

**Functions**:
- **Generate World**: Call `world/world_generator.py` to generate resource map, initialize `world/world_state.py`
- **Generate Agents**: Randomly generate female and male Agents according to configuration parameters, assign initial positions
- **Initialize Nests**: Assign initial nests to each Agent (2 nests per female and male in one version). Nest locations selected based on resource map and fixed sampling radius (50 grid units) at points with maximum resources
- **Initialize Beliefs**: Set initial parameters for each Agent's belief system (initial frequency values hard-coded in code in one version, not configuration)
- **Return Initial State**: Return a 4-tuple containing `WorldState`, `FemaleAgent` list, `MaleAgent` list, and `Orchestrator`

**Key Points**:
- Initialization process does not involve any strategy decisions (`Strategy`). Strategy decisions are runtime behaviors, dynamically bound and executed by `Orchestrator` during simulation
- Initial beliefs are static, based on prior parameters in configuration file, not dependent on any dynamic observations
- Instantiate empty shell Orchestrator (at this point only holds world and agent list, no strategy binding)
- Return assembled WorldState, Agent list, and Orchestrator to caller, then exit, no longer participating in subsequent simulation process

**Code Example**:
```python
def bootstrap() -> Tuple[WorldState, List[FemaleAgent], List[MaleAgent], Orchestrator]:
    world_generator = WorldGenerator(GRID_SIZE, RESOURCE_LEVEL, AGGREGATION_LEVEL)
    resource_map = world_generator.generate_resources()
    world_state = WorldState(resource_grid=resource_map)
    female_agents = _spawn_agents(...)  # Generate female agents
    male_agents = _spawn_agents(...)    # Generate male agents
    _allocate_nests(female_agents, world_state, ...)  # Allocate nests
    _initialize_male_nest_assignments(male_agents, ...)  # Initialize male nest assignments
    orchestrator.bind_all(all_agents)  # Bind all agent strategies
    return world_state, female_agents, male_agents, orchestrator
```

### 2.2 World Generation and State Management

#### 2.2.1 world_generator.py

**Responsibility**: Generate resource grid using negative binomial distribution to ensure randomness and configurability of resource distribution.

**Functions**:
- **Parameterized Generation**: Control resource distribution through `GRID_SIZE`, `RESOURCE_LEVEL` (or `mean_resource`), and `AGGREGATION_LEVEL` (or `aggregation_index`)
- **Normalization Processing**: Ensure generated resource grid total resource amount matches grid size

**Implementation Details**:
- Generate 500×500 base grid, large-scale simulations can further expand
- During decision-making, use local statistical proxies instead of per-cell calculations to balance precision with computational power

**Code Example**:
```python
def generate_resources(self) -> NDArray[np.float32]:
    raw_grid = np.random.negative_binomial(n=self.n, p=self.p, size=(self.grid_size, self.grid_size))
    normalized_grid = (raw_grid.astype(np.float32) / np.sum(raw_grid)) * (self.grid_size ** 2)
    return normalized_grid.astype(np.float32)
```

#### 2.2.2 world_state.py

**Responsibility**: Manage simulation environment, including resource grid, nests, and agent states.

**Functions**:
- **Environment Queries**: Provide `get_resource_density`, `query_nest_composition` and other methods to query environment state
- **Resource Management**: Responsible for resource reset and update
- **Nest Management**: Provide nest creation, resource addition, and clearing functions

**Core Responsibilities**:
- **Nest Lifecycle Management**: Create and destroy nests, maintain `nests: Dict[int, Nest]` registry
  - `create_nest_for_female(female_id: int, position: Tuple[int, int]) -> int`: Create nest for female agent, supporting multiple nests per female
- **Read-only Resource Map Access**: Provide `get_resource_value(position)` or `get_resource_density(position)` query interface
- **Spatial Information Queries**: Calculate distances between individuals, get lists of nearby nests
- **Probabilistic Information Queries**: Calculate discovery probability of nest composition based on distance and search_share
- **State Consistency Guarantee**: Ensure all agents see identical environmental snapshots at the same time step

**Required Interface Implementations**:
```python
def create_nest_for_female(female_id: int, position: Tuple[int, int]) -> int: pass
def get_nest_locations() -> List[Tuple[int, int]]: pass
def query_nest_composition(agent_id: int, nest_id: int, search_share: float) -> Optional[NestDetails]: pass
def get_resource_density(position: Tuple[int, int]) -> float: pass
def get_agents_in_radius(position: Tuple[int, int], radius: int) -> List[Agent]: pass
```

**Search Success Probability Function**:
$$
p_i = 1 - \exp\left(-\lambda \cdot \frac{\text{search\_share}}{d_i}\right)
$$

Where:
- $\lambda$ is search efficiency constant (SEARCH_COST configuration parameter)
- $d_i$ is distance between agent and target nest

**Tiered Information Model**:
- **Free Information**: Global nest locations (passive perception) through `get_nest_locations()` or `get_all_nests_basic()`
- **Paid Information**: Neighboring nest internal composition and individual strategies (active search, success rate exponentially decaying) through `query_nest_composition(agent_id, nest_id, search_share)`

### 2.3 Agent Class Design

#### 2.3.1 base_agent.py

**Responsibility**: Define base attributes and methods for all agents.

**Core Attributes**:
- `_id`: Unique identifier
- `_position`: Tuple[int, int] - Current position
- `search_share`: float - Search share (initial value 1)

**Abstract Methods**:
- `step()`: To be implemented by specific agent classes

**Properties**:
- `id`: Return self._id
- `position`: Return self._position

**Code Example**:
```python
class BaseAgent(ABC):
    def __init__(self, id: int, position: Tuple[int, int]):
        self._id = id
        self._position = position
        self.search_share: float = 1  # Initial search share
    
    @abstractmethod
    def step(self) -> None: pass
    
    @property
    def id(self) -> int: return self._id
    
    @property
    def position(self) -> Tuple[int, int]: return self._position
```

#### 2.3.2 Nest Class (agents/nest.py)

**Required Fields**:
```python
@dataclass
class Nest:
    id: int
    position: Tuple[int, int]  # Grid coordinates
    female_id: Optional[int]
    _male_ids: Set[int]  # Private variable storing male individual ID set
    female_raising_share: float = 0.0
    male_raising_shares: Dict[int, float]  # {male_id: share}
    resources_acquired: float = 0.0  # Acquired resource amount
    expected_viable_fledgling: float = 0.0  # Expected number of viable offspring
```

**Access Methods**:
- Access male IDs through `get_male_ids` property, returning a copy to prevent external modification
- Manage males in nest through `add_male()` and `remove_male()` methods

**Additional Properties** (from different versions):
- `home_range_cells`: Set of home range cells, accessed through `get_home_range` method
- `resource_cache`: Current step's available resource cache

**Note**: `home_range_radius` is only used for explanatory output and can be dynamically calculated in the reporter, not stored in Nest.

#### 2.3.3 FemaleAgent (agents/female_agent.py)

**Core Attributes**:
- `nest_ids`: Set[int] - Currently associated nests (one version uses list, another uses set)
- `memory`: Dict[int, Any] - Memory recording other individuals' actions and previous round fitness as belief

**Methods**:
- `add_male_to_nest()`: Manage males in nest
- Search functionality provided through WorldState's `query_nest_composition` method

**Note**: Different versions show `nest_ids` as either Set[int] or List[int]. [Note: conflicting information from versions, please verify]

#### 2.3.4 MaleAgent (agents/male_agent.py)

**Core Attributes**:
- `nest_ids`: Set[int] - Nests currently providing raising_share
- `nest_roles`: Alpha/beta allocation for multi-nest management
- `memory`: Dict[int, Any] - Memory recording other individuals' actions and previous round fitness as belief

**Methods**:
- `assign_to_nest()`: Assign to multiple nests
- Search functionality provided through WorldState's `query_nest_composition` method

### 2.4 Strategy Implementation

#### 2.4.1 belief_system.py

**Responsibility**: Implement Bayesian updates for search share and raising share belief management.

**Core Functions**:

1. **Search Beliefs**:
   - Manage `search_beliefs`, including posterior mean and observation data
   - `get_search_belief(agent_id) → float`: Return agent's point estimate (posterior mean) of optimal search_share

2. **Raising Beliefs**:
   - Manage `raising_beliefs`, predicting other individuals' investment in nests
   - `get_raising_belief(agent_id, nest_id) → float`: Return agent's point estimate of expected total investment in nest_id

3. **Belief Update**:
   - `submit_search_observation()`: Submit search observation data
   - `update_search_beliefs()`: Execute belief update
   - `update_beliefs()`: Unified execution of belief updates at end of each round

**Descriptive Statistics + Naive Bayes Update**:

1. **Search-Share Decision Support**:
   - After each round of search, record observed same-sex individuals' `(search_share, fitness)` pairs
   - Use descriptive statistics to obtain average performance of same-sex individuals this round as likelihood; use agent's previous round belief about search_share as prior
   - Execute naive Bayes update, producing posterior belief

2. **Raising-Share Behavior Prediction**:
   - After each round of search, record observed "target nest - occupant" `(nest_id, agent_id, raising_share)` triples
   - Calculate average `raising_share` by sex group as likelihood; use agent's previous round belief as prior
   - Execute naive Bayes update, producing posterior belief

Both updates are stored independently, normalized independently, all completed within belief_system; external strategy layer only obtains normalized probability through `get_belief(agent_id, behavior_class)`.

#### 2.4.2 base_strategy.py

**Responsibility**: Define strategy abstract base class, implement core algorithm for raising share allocation.

**Core Method**:
```python
def _allocate_raising_shares(self, agent_id, available_nests, total_raising_share, belief_func, fitness_func, world_state) -> Dict[int, float]:
    raising_shares = {nest_id: 0.0 for nest_id in available_nests}
    step_size = total_raising_share / ALLOCATION_STEPS
    for _ in range(ALLOCATION_STEPS):
        marginal_utilities = {nest_id: calculate_marginal_utility(...) for nest_id in available_nests}
        best_nest_id = max(marginal_utilities, key=marginal_utilities.get)
        raising_shares[best_nest_id] += step_size
    # Normalize to ensure budget constraint
    return raising_shares
```

#### 2.4.3 female_strategy.py & male_strategy.py

**Responsibility**: Implement sex-specific allocation logic.

**Female Strategy**:
- Handle nest ownership and raising share allocation for owned nests
- `decide_search_share()`: Evaluate current nest quality vs. expected value of searching
- `decide_raising_allocation()`: Allocate raising shares among owned nests

**Male Strategy**:
- Handle allocation across multiple nests and raising shares
- `decide_search_share()`: Determine search investment
- `decide_raising_allocation()`: Allocate raising shares across participated nests

**Search Share Decision Process**:
1. **Initial Setup**: Each agent's `search_share` randomly generated as fixed value at initialization
2. **Social Learning and Bayesian Update**:
   - Collect same-sex individuals' `search_share` and `fitness` data
   - Use Bayesian update with likelihood (observed data) and prior (current belief) to produce posterior
   - Adjust next round's `search_share` based on updated belief

**Raising Share Allocation Optimization**:

**Optimization Problem**:
$$
\max_{\{r_k\}} \sum_{k \in \text{owned\_nests}} \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k) \quad \text{s.t.} \sum_k r_k = 1 - s, \quad r_k \geq 0
$$

**Marginal Utility Calculation**:
$$
\text{MU}_k(r_k) = \frac{\mathcal{F}(r_k + \hat{o}_k + \Delta, \mathbf{p}_k) - \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k)}{\Delta}
$$

**Greedy Iterative Algorithm**:
1. Initialize all nest allocations to 0
2. For each iteration step:
   - Calculate marginal utility for each nest
   - Allocate to nest with maximum marginal utility
3. Normalize final allocation to satisfy budget constraint

### 2.5 Simulation Main Loop and Orchestrator

#### 2.5.1 game_loop.py

**Responsibility**: Manage daily simulation flow, including strategy decisions, action execution, and resource reset.

**Core Methods**:
- **Daily Iteration**: Advance simulation day by day, execute `_run_one_day` method
- **Strategy Collection**: Collect all agents' strategy decisions
- **Action Execution**: Generate and execute action list (search and raise)
- **Resource Reset**: Reset world resources and nest resources at end of each day

**Daily Simulation Flow**:
1. **Get World Snapshot**: Get current world state, including resource distribution and agent positions
2. **Strategy Binding**: Call `orchestrator.bind_all()` to bind strategies for all agents
3. **Collect Agent Strategies**: Each agent decides `search_share` and `raising_shares` for each nest
   - Decision results cached, no changes this round
4. **Generate Action List**:
   - Collect all (agent, nest) combinations with `raising_share > 0`
   - Randomly shuffle action sequence
5. **Execute Actions**:
   - **Search**: Call `WorldState.query_nest_composition` to get nest info, update agent's belief system
   - **Raise**: Call `mine_resources` to extract resources, add to nest resource cache
6. **Reset World Resources**: Use negative binomial distribution to regenerate world resources, clear all nests' resource records

**Code Example**:
```python
def _run_one_day(self) -> Dict[str, Any]:
    # 1. Get current world snapshot
    world_snapshot = self._get_world_snapshot()
    
    # 2. Bind strategies for all agents
    self.orchestrator.bind_all(cast(List[BaseAgent], self._all_agents))
    
    # 3. Collect agent strategies
    self._collect_agent_strategies(world_snapshot)
    
    # 4. Generate action list
    action_list = self._generate_action_list()
    
    # 5. Execute actions randomly
    nest_resources = self._execute_actions(action_list)
    
    # 6. Reset world resources
    self._reset_world_resources()
    
    return {'nest_resources': nest_resources}
```

#### 2.5.2 orchestrator.py

**Responsibility**: Bind agents with strategies, manage strategy lifecycle.

**Core Methods**:
- **Strategy Binding**:
  - `bind_one(agent)`: Bind strategy for single agent
  - `bind_all(agent_list)`: Batch bind strategies
- **Strategy Access**:
  - `get_strategy(agent)`: Get agent's strategy at runtime
- **State Isolation**: Only maintain mapping relationships, do not store agent or strategy internal state

**Lifecycle**:
- Instantiated once by bootstrap, survives entire simulation
- Internally maintains daily "Agent → Strategy instance" mapping table

**Daily Binding**:
- If agent already has mapping and strategy type unchanged, return original strategy
- If strategy type switches, instantiate new Strategy and replace old mapping

### 2.6 Fitness Calculation (fitness.py)

**Responsibility**: Implement resource extraction and fitness calculation functions.

**Core Functions**:

#### 2.6.1 Resource Extraction (mine_resources)

**Three-Step Resource Extraction**:
1. **Determine Exploration Area**: Circular area centered at nest position with home_range_radius as radius
   ```python
   home_range = determine_exploration_area(world_state, nest.position, raising_share)
   ```
2. **Select Target Patch**: Select grid cell with maximum resource density in exploration area
   ```python
   target_pos = select_target_patch(world_state, home_range)
   ```
3. **Extract by Ratio**: Extract resources at fixed ratio ρ
   ```python
   if target_pos:
       extracted = extract_resources(world_state, target_pos)
       nest.add_resources(extracted)
       return extracted
   return 0.0
   ```

**Extraction Formula**:
- Actual extraction = rho × current resource value of patch
- Extraction amount immediately deducted from WorldState
- Accumulated to target Nest's acquired resource record

**Resource Extraction Rate**: ρ (rho) - Fixed proportion for resource extraction

#### 2.6.2 Fitness Calculation

**Logistic Conversion**:
$$
\text{fledglings} = \frac{K}{1 + \exp\{-r \cdot (R_{\text{total}} - R_0)\}}
$$

Where:
- K: Half-saturation constant (logistic_K)
- r: Conversion efficiency (logistic_r)
- R₀: Resource threshold (logistic_A or R_0)
- R_total: Actual acquired resource amount

**Payoff Calculation**:
- **Female**: $\text{payoff}_{\text{female}} = \sum_{k \in \text{her\_nests}} \text{fledglings}_k - c_{\text{egg}}$
- **Male**: $\text{payoff}_{\text{male}} = \sum_k \left( \frac{\text{raising\_share}_{\text{male},k}}{\sum \text{raising\_share}_k} \times \text{fledglings}_k \right)$

**Counterfactual Fitness**:
- `calculate_female_fitness_counterfactual()`: Evaluate impact of resource allocation for females
- `calculate_male_fitness_counterfactual()`: Evaluate impact of resource allocation for males

---

## 3. Core Algorithms and Mechanisms

### 3.1 Raising Share Allocation Optimization Mechanism

#### 3.1.1 Optimization Problem Formalization

In the context of known belief $\hat{o}_k$ (expected total investment from others in nest k), agent solves:

**Objective Function**:
$$
\max_{\{r_k\}} \sum_{k \in \text{owned\_nests}} \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k)
$$

**Constraints**:
$$
\sum_k r_k = 1 - s, \quad r_k \geq 0
$$

Where:
- $\mathcal{F}(\cdot)$: Expected fitness function
- $s$: search_share
- $r_k$: raising_share to be decided
- $\hat{o}_k$: Belief about others' investment
- $\mathbf{p}_k$: Nest position

#### 3.1.2 Marginal Expected Utility Calculation

Using numerical differentiation:
$$
\text{MU}_k(r_k) = \frac{\mathcal{F}(r_k + \hat{o}_k + \Delta, \mathbf{p}_k) - \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k)}{\Delta}
$$

Where $\Delta$ is configuration parameter `marginal_delta` (default 0.01).

#### 3.1.3 Greedy Iterative Allocation Algorithm

**Initialization**: For all nests $k$, set $r_k^{(0)} = 0$

**Iteration Process**: For $t = 1$ to $N$ (ALLOCATION_STEPS, default 20):
1. Calculate marginal utility $\text{MU}_k$ for each nest based on current allocation $r_k^{(t-1)}$
2. Select nest $k^* = \arg\max_k \text{MU}_k$ with maximum marginal utility
3. Update allocation: $r_{k^*}^{(t)} = r_{k^*}^{(t-1)} + \delta$, other nests remain unchanged
   Where $\delta = B/N$, $B = 1 - s$

**Normalization**:
$$
r_k^{\text{final}} = r_k^{(N)} \times \frac{B}{\sum_j r_j^{(N)}}
$$

**Parameter Requirements**:
- Iteration steps $N$: Default 20
- Step size $\delta = B/N$ must satisfy $\delta \leq 0.05$ to ensure approximation accuracy

### 3.2 Bayesian Update Mechanism

#### 3.2.1 Search Share Update

**Formula**:
$$
\text{search\_share}_{t+1} = \text{BayesianUpdate}\left(\text{search\_share}_t \mid \text{social\_learning\_evidence}_t\right)
$$

**Process**:
1. **Data Collection**: Collect same-sex individuals' `(search_share, fitness)` pairs
2. **Bayesian Update**:
   - **Likelihood**: Based on observed same-sex individuals' average `search_share` and `fitness`
   - **Prior**: Current belief about `search_share`
   - **Posterior**: Combining likelihood and prior
3. **Decision Adjustment**: Adjust next round's `search_share` based on updated belief

#### 3.2.2 Raising Share Belief Update

**Process**:
1. Record observed "target nest - occupant" `(nest_id, agent_id, raising_share)` triples
2. Calculate average `raising_share` by sex group as likelihood
3. Use agent's previous round belief as prior
4. Execute naive Bayes update to produce posterior belief

### 3.3 Sequential Decision Framework

**Core Innovation**: Agents cannot know their position in the decision queue.

**Process**:
1. All agents randomly shuffled to generate decision order each round
2. Agents form beliefs about **population-level frequencies** rather than specific rivals' moves
3. Bayesian updating on local observations using beta-binomial model
4. Limited sample size mitigated by temporal smoothing and social learning

**Advantages**:
- **Biological**: Reflects bounded rationality
- **Computational**: Reduces complexity from O(N!) to O(N) per round
- **Theoretical**: Sidesteps infinite regress and Nash equilibrium multiplicity

---

## 4. Configuration Parameters

### 4.1 Configuration Parameters Table

All configuration parameters defined in `config/config.yaml` or `config/config.py`:

| Parameter | Description | Default Value | Source |
|-----------|-------------|---------------|--------|
| RANDOM_SEED | Random seed | 42 | technical_documentation_new.md |
| grid_size / GRID_SIZE | Grid size | 500 | All versions |
| initial_female_count | Initial female count | 20 | technical_documentation.md |
| initial_male_count | Initial male count | 20 | technical_documentation.md |
| simulation_rounds | Simulation rounds | 5 | technical_documentation.md |
| world.grid_size | Grid size (world section) | 500 | technical_documentation.md |
| world.resource_level | Resource level | 0.5 | technical_documentation.md |
| world.aggregation_level | Aggregation level | 0.3 | technical_documentation.md |
| RESOURCE_LEVEL | Resource level | 100 | technical_documentation_new.md |
| AGGREGATION_LEVEL | Aggregation level | 5 | technical_documentation_new.md |
| SEARCH_COST / search_cost | Search efficiency constant λ | 0.5 | technical_documentation.md |
| raising_success.logistic_K | Logistic function maximum | 1.0 | technical_documentation.md |
| raising_success.logistic_r | Logistic function growth rate | 0.5 | technical_documentation.md |
| raising_success.logistic_A | Logistic function parameter | 1e-6 | technical_documentation.md |
| LOGISTIC_K | Logistic function maximum | 10 | technical_documentation_new.md |
| LOGISTIC_R | Logistic function growth rate | 0.1 | technical_documentation_new.md |
| LOGISTIC_A | Logistic function parameter | 100 | technical_documentation_new.md |
| resource_extraction_rho | Resource extraction rate ρ | 0.33 | technical_documentation.md |
| RESOURCE_EXTRACTION_RATE | Resource extraction rate | 0.3 | technical_documentation_new.md |
| HOME_RANGE_RADIUS | Home range radius | 3 | technical_documentation_new.md |
| ALLOCATION_STEPS / allocation_steps | Greedy iteration steps | 20 | All versions |
| MARGINAL_DELTA / marginal_delta | Marginal utility step | 0.01 | All versions |

**Note**: There are significant differences in default values between versions for several parameters:
- RESOURCE_LEVEL: 0.5 vs 100
- AGGREGATION_LEVEL: 0.3 vs 5
- LOGISTIC_K: 1.0 vs 10
- LOGISTIC_R: 0.5 vs 0.1
- LOGISTIC_A: 1e-6 vs 100
- resource_extraction_rho: 0.33 vs 0.3

[Note: conflicting information from versions, please verify]

### 4.2 Configuration File Format

**YAML Format (config.yaml)**:
```yaml
# Global parameters
grid_size: 500
initial_female_count: 20
initial_male_count: 20
simulation_rounds: 5

# World parameters
world:
  grid_size: 500
  resource_level: 0.5
  aggregation_level: 0.3

# Search parameters
SEARCH_COST: 0.5

# Fitness calculation parameters
raising_success:
  logistic_K: 1.0
  logistic_r: 0.5
  logistic_A: 1e-6

# Extraction parameters
resource_extraction_rho: 0.33
```

**Python Format (config.py)**:
```python
RANDOM_SEED = 42
GRID_SIZE = 500
RESOURCE_LEVEL = 100
AGGREGATION_LEVEL = 5
RESOURCE_EXTRACTION_RATE = 0.3
HOME_RANGE_RADIUS = 3
ALLOCATION_STEPS = 20
MARGINAL_DELTA = 0.01
LOGISTIC_K = 10
LOGISTIC_A = 100
LOGISTIC_R = 0.1
```

[Note: conflicting information from versions, please verify which format to use]

---

## 5. Initialization and Simulation Flow

### 5.1 Initialization Flow

1. **World Generation**: Use `world_generator.py` to generate resource grid, initialize `world_state.py`
2. **Agent Generation**: Randomly generate female and male agents, assign initial positions (uniform distribution)
3. **Nest Allocation**: Allocate initial nests for each agent:
   - Select locations with maximum resources within fixed sampling radius (50 grid units)
   - One version allocates 2 nests per female and male
4. **Belief Initialization**: Set initial parameters for each agent's belief system
5. **Strategy Binding**: Bind corresponding strategies for all agents

### 5.2 Daily Simulation Flow

1. **Get World Snapshot**: Get current world state, including resource distribution and agent positions
2. **Strategy Decision**:
   - Agents decide `search_share` and `raising_shares` for each nest based on current world state and belief system
   - Decision results cached, no changes this round
3. **Action List Generation**:
   - Collect all (agent, nest) combinations with `raising_share > 0`
   - Randomly shuffle action sequence
4. **Action Execution**:
   - **Search**: Call `WorldState.query_nest_composition` to get nest info, update agent's belief system
   - **Raise**: Call `mine_resources` to extract resources, add to nest resource cache
5. **Resource Reset**: Use negative binomial distribution to regenerate world resources, clear all nests' resource records

---

## 6. Output and Analysis

### 6.1 Simulation Output

- **Daily Nest Resources**: Record daily resource accumulation for each nest
- **Agent Fitness**: Calculate and record fitness for each agent
- **Mating System Statistics**: Record daily mating system statistics

### 6.2 Data Analysis

**analysis/reporter.py** or **analysis/mating_system_analyzer.py**:
- **Nest Composition**: Analyze female and male composition of each nest
- **Resource Allocation**: Analyze resource allocation among different nests and agents
- **Fitness Distribution**: Analyze distribution and trends of agent fitness

---

## 7. Engineering Constraints

### 7.1 Code Quality Requirements

- All function signatures must use type annotations
- All parameters must come from config.yaml or config.py
- No hard-coding of parameters allowed
- No new parameters allowed in code
- Enforce PEP 8 standards rigorously
- Comprehensive type hinting as contract to make model assumptions explicit

### 7.2 Performance Considerations

- Computational complexity: O(N) per round (reduced from O(N!))
- Stateless Strategy allows batch parallelization
- Pure function characteristics enable decision computation parallelization without write conflicts
- Large-scale simulations feasible on standard hardware

### 7.3 Design Principles

- **Agent-Strategy Decoupling**: Strategy can be hot-swapped without modifying Agent code
- **State Consistency**: Centralized management of cross-entity state updates
- **Testability**: Strategy designed as pure function interface
- **Extensibility**: Future refinements can be integrated without rearchitecting core model

---

## 8. Extension and Improvement Directions

1. **Strategy Expansion**: Support more types of strategies, such as genetic algorithm-based strategies
2. **Environmental Complexity**: Increase environmental dynamics, such as seasonal resource variation
3. **Agent Behavior**: Expand agent behavior patterns, such as territory defense, mate choice, etc.
4. **Visualization**: Add real-time visualization functionality to display simulation process
5. **Performance Optimization**: Optimize simulation performance, support larger scale agents and longer duration simulations
6. **Risk Aversion**: Introduce variance penalty term in payoff function
7. **Kin Selection**: Adjust payoff weights to reflect kinship relationships
8. **Individual Heterogeneity**: Let K or r vary between individuals, reflecting quality differences

---

## 9. Mathematical Formulas Reference

### 9.1 Search Success Probability
$$
p_i = 1 - \exp\left(-\lambda \cdot \frac{\text{search\_share}}{d_i}\right)
$$

### 9.2 Budget Constraint
$$
\text{search\_share} + \sum_{k \in \text{nests}} \text{raising\_share}_k = 1.0
$$

### 9.3 Logistic Conversion
$$
\text{fledglings}_k = \frac{K}{1 + \exp\{-r \cdot (R_{\text{total},k} - R_0)\}}
$$

### 9.4 Female Payoff
$$
\text{payoff}_{\text{female}} = \sum_{k \in \text{her\_nests}} \text{fledglings}_k - c_{\text{egg}}
$$

### 9.5 Male Payoff
$$
\text{payoff}_{\text{male}} = \sum_k \left( \frac{\text{raising\_share}_{\text{male},k}}{\sum \text{raising\_share}_k} \times \text{fledglings}_k \right)
$$

### 9.6 Marginal Utility
$$
\text{MU}_k(r_k) = \frac{\mathcal{F}(r_k + \hat{o}_k + \Delta, \mathbf{p}_k) - \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k)}{\Delta}
$$

### 9.7 Bayesian Update
$$
\text{search\_share}_{t+1} = \text{BayesianUpdate}\left(\text{search\_share}_t \mid \text{social\_learning\_evidence}_t\right)
$$

---

*Document compiled from: demand_text.md, demand_text_latest.md, demand_text_ttb.md, raw_ideas.md, technical_documentation.md, technical_documentation_new.md*
