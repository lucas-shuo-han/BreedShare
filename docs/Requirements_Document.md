# BreedShare - Requirements Document

---

## 1. Project Overview and Goals

### 1.1 Project Core Goal (Technical Version)

**Objective**: Build a discrete Agent Based Model (ABM) that simulates individuals maximizing fitness through search and resource investment decisions under limited energy budgets.

**Deliverable**: A Python package containing a configurable simulator that outputs per-round individual fitness and nest state data.

### 1.2 Core Modeling Philosophy

**Project Philosophy: Abstraction over Realism for Generalizable Insights**

Our objective is to identify the minimal set of biologically meaningful parameters that govern mating system dynamics, rather than replicate the full complexity of avian behavior. By prioritizing higher-level abstraction—reducing parameter space, accelerating simulation, and enhancing explainability—we sacrifice granular realism to amplify intuitive understanding and cross-species generalizability. This approach acknowledges that some implementation details may appear abstract and counterintuitive, but the gains in computational tractability and theoretical clarity justify the architectural investment.

This philosophy extends to code design: readability and maintainability are non-negotiable. We enforce PEP 8 standards rigorously and employ comprehensive type hinting not as stylistic flourish, but as a contract that makes the model's assumptions explicit and the codebase navigable for future collaborators. The effort required to write such disciplined code is repaid in debuggability and extensibility, ensuring the model remains a living tool rather than a fragile prototype.

### 1.3 Research Questions and Model Capabilities

The model explores how the spatiotemporal distribution of resources drives the dynamic evolution of mating systems, for example:

- Emergence conditions of polyandry/polygyny mating systems
- Optimal strategies for time/energy budget allocation between males and females
- Game mechanisms formed by dynamic territory adjustments

---

## 2. Functional Requirements

### 2.1 World Layer: Environment Generation and Information Structure

#### 2.1.1 Resource Map Generation (world_generator.py)

**Requirement**: Generate a 500×500 resource grid using Negative Binomial (NB) distribution, parameterizing both total resource abundance and spatial aggregation.

**Refactor: Replace Patch Model with Negative Binomial Distribution**

Prior research identifies two primary drivers of mating system evolution: total resource abundance and spatial aggregation of resources. This refactor adopts the negative binomial distribution because it directly parameterizes both with two interpretable variables (mean and aggregation level), replacing four arbitrary patch parameters with a mathematically tractable alternative.

Critically, this simplification does not sacrifice realism: the original patch model was already an approximation of heterogeneous micro-habitats. The negative binomial provides a first-principles statistical representation of aggregation, eliminating nested approximations while preserving the capacity to generate biologically plausible landscapes.

**Defense for Concrete Model**: Because the concrete model itself reflects some sort of aggregation. It is more computationally efficient, and it can model continuous ones when increasing grid_size.

A potential consideration is whether territories containing many patches might approximate a normal distribution by the Central Limit Theorem. This is unlikely for three reasons:
1. Mating system evolution depends on population-level aggregation, captured by the negative binomial's higher moments
2. Individual fitness is determined by territory size, not within-territory patchiness
3. The Central Limit Theorem's assumptions are not met, as patches are not independent random variables because of the NB parameterization.

**Implementation Design**: `world_generator.py` generates a 500×500 base grid, with large-scale simulations capable of further expansion. During decision-making, use local statistical proxies instead of per-cell calculations to balance precision with computational efficiency.

**Configuration Parameters**: Uses `GRID_SIZE`, `RESOURCE_LEVEL`, and `AGGREGATION_LEVEL` from `config/config.py`.

#### 2.1.2 World State Management (world_state.py)

**Requirement**: Serve as the environment state registry and global state query center, following the "data service layer" principle to provide all agents with a single source of environmental information.

**Core Responsibilities**:
- **Nest Lifecycle Management**: Create and destroy nests, maintain `nests: Dict[int, Nest]` registry
  - `create_nest_for_female(female_id, position, home_range_cells)`: Create nest for female agent, supporting multiple nests per female
- **Read-only Resource Map Access**: Provide `get_resource_value(position)` or `get_resource_density(position)` query interface
- **Spatial Information Queries**: Calculate distances between individuals, get lists of nearby nests
- **Probabilistic Information Queries**: Calculate discovery probability of nest composition based on distance and search_share
- **State Consistency Guarantee**: Ensure all agents see identical environmental snapshots at the same time step

**Tiered Information Acquisition Model: Information Structure Under Bounded Rationality**

**A Tiered Information Model for Bounded Rationality in Mating Systems**

The cognitive architecture of wild animals imposes severe constraints on information processing: they cannot engage in infinite recursive reasoning about conspecifics' strategic responses, nor can they instantaneously survey entire landscapes. Our model addresses this through a parsimonious two-tiered information structure that mirrors biological reality while maintaining computational tractability.

At the foundational level, we assume agents possess **global awareness of nest locations**—not as a literal panopticon, but as a tractable abstraction of the pervasive information conveyed by territorial song, movement patterns, and spatial memory accumulated over weeks of ranging. This free information reflects the empirical observation that Dunnocks can detect singing males and active nests within hundreds of meters without dedicated search effort, yet remain ignorant of the internal composition of these nests.

The critical innovation lies in making **detailed knowledge costly**. The probability of discovering a nest's internal state—its male and female roster, dominance hierarchies, and reproductive status—scales as an exponential decay function of distance and search investment.

**Search Success Probability Function**:
$$
p_i = 1 - \exp\left(-\lambda \cdot \frac{\text{search\_share}}{d_i}\right)
$$

**Biological Significance of λ**: Search efficiency constant, corresponding to vegetation density and predation risk.
- Low λ → High search cost → Tendency to stay
- High λ → Low search cost → Tendency to explore

**Empirical Validation**: When simulating high food abundance (increasing λ via supplemental feeding), optimal search_share declines, female ranges contract, and the mating system shifts toward monogamy and polygyny, precisely matching the experimental manipulation in Davies & Lundberg (1984). Conversely, low λ values generate expansive female ranges and frequent polyandry, capturing the natural variation observed across habitat types.

**Implementation Design**: `world_state.py` provides the following query interfaces:
- `get_nest_locations()` or `get_all_nests_basic()`: Obtain all nest coordinates at no cost
- `query_nest_composition(agent_id, nest_id, search_share)`: Probabilistically query nest internal state, returns `Optional[NestDetails]`
- `get_agents_in_radius(position, radius)`: Get agents within specified radius

This architecture elegantly sidesteps the infinite recursion problem that plagues classical game-theoretic models. By making information probabilistic rather than contingent on specific rivals' unobservable strategies, agents need not ask "If I search, how will opponent X respond?" but instead "What is the expected value of searching given population-level frequencies?"

### 2.2 Agent Layer: State Entities

#### 2.2.1 Nest Entity (agents/nest.py)

**Requirement**: Nest exists as an independent entity carrying core data.

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

**Additional Properties**:
- `home_range_cells`: Set of home range cells, accessed through `get_home_range` method
- `resource_cache`: Current step's available resource cache

**Implementation Design**: `agents/nest.py` does not depend on any strategy module and can be independently managed by WorldState. Female birds can simultaneously own multiple nests, maintaining associations through `FemaleAgent.nest_ids` set/list.

Note: `home_range_radius` is only used for explanatory output and can be dynamically calculated in the reporter, not stored in Nest.

#### 2.2.2 Female Agent (agents/female_agent.py)

**Requirement**: Manage female agent state and mechanical behaviors.

**Core Attributes**:
- `nest_ids`: Set/list of currently associated nests
- `memory`: Dict[int, Any] - Memory recording other individuals' actions and previous round fitness as belief

**Methods**:
- `add_male_to_nest()`: Manage males in nest
- Search functionality provided through WorldState's `query_nest_composition` method

#### 2.2.3 Male Agent (agents/male_agent.py)

**Requirement**: Manage male agent state and allocation status.

**Core Attributes**:
- `nest_ids`: Set of nests currently providing raising_share
- `nest_roles`: Alpha/beta allocation for multi-nest management
- `memory`: Dict[int, Any] - Memory recording other individuals' actions and previous round fitness as belief

**Methods**:
- `assign_to_nest()`: Assign to multiple nests
- Search functionality provided through WorldState's `query_nest_composition` method

#### 2.2.4 Base Agent (agents/base_agent.py)

**Requirement**: Define base attributes and methods for all agents.

**Core Attributes**:
- `id`: Unique identifier
- `position`: Tuple[int, int] - Current position
- `search_share`: float - Initial search share (default 1)

**Abstract Methods**:
- `step()`: To be implemented by specific agent classes

**Implementation Design**: Agent classes contain only state attributes and mechanical behaviors. All decision interfaces are implemented by Strategy classes, called through `self.strategy.decide_search_share()`.

### 2.3 Strategy Layer: Decision Logic

#### 2.3.1 Core Decision Framework: Energy Budget Abstraction

**Core Model Architecture: Energy Allocation as the Fundamental Currency**

Our model reframes mating system dynamics as a problem of **temporal and energetic resource allocation**. Both sexes face a fundamental constraint: time and effort invested in one activity (e.g., guarding a nest, searching for additional mates) cannot be allocated elsewhere. Strategic decisions such as "accept beta male" or "abandon nest" are not primitive actions but **surface-level manifestations** of underlying **breedshare profiles**—vectors describing how an individual distributes its finite energetic budget across competing reproductive tasks.

All strategies satisfy the budget constraint:
$$
\text{search\_share} + \sum_{k \in \text{nests}} \text{raising\_share}_k = 1.0
$$

Where **search_share** quantifies investment in exploring unknown mates and territories, and **raising_share** quantifies investment in consolidating current reproductive units. Abandonment corresponds to raising_shareₖ=0, while defend and accept mate behaviors are automatically reflected through the relative proportion of raising_share between individuals, without independent modeling.

**Female Strategy Reduction (4 categories)**:
1. **Accept/Reject Beta Male**: Reflected in whether the sum of male raising_share in the nest changes from 0 to positive, and whether female's own raising_share adjusts accordingly
2. **Abandon vs. Stay**: Directly reflected in whether the raising_share value allocated to this nest is 0 or positive
3. **Single Nest vs. Multi-Nest Breeding**: Reflected in whether raising_share vector is single-element or multi-element
4. **Territory Size Adjustment**: home_range radius itself is a function of raising_share—more energy allows guarding larger geographic range

**Male Strategy Reduction (3 categories)**:
1. **Join/Leave Nest**: Individual raising_share changes from 0 to positive (join) or vice versa (leave)
2. **Parental Care Intensity Adjustment**: Directly reflected in the numerical value of raising_share for this nest
3. **Disruptive Competitive Behavior**: Not yet implemented, can be modeled by adjusting raising_share to positive/negative values

**Revolutionary Advantages of This Abstraction**:
1. **Computational Brute Force Aesthetics**: Compress 10 discrete behavioral strategies and 30+ parameter conditional trees into 1 continuous variable, achieving exponential computational savings
2. **Fidelity Paradox**: Captures "energy limitation" as the primary biological constraint, automatic correct trade-offs between behaviors without manual encoding of interactions, actually improving fidelity
3. **Universality Promise**: Applicable to any reproductive organism with time/energy constraints, transcending the single species of wren
4. **Zero-Cost Extensibility**: Currently all individuals have energy budget=1.0, future addition of individual heterogeneity only requires changing to `agent.energy_budget`, strategy code needs no refactoring

#### 2.3.2 Mating Game Formal Definition

**[Core Definition]** This chapter defines the project's mathematical foundation—the complete formal structure of the breed share game. This game is the single source of truth for all subsequent simulation and theoretical derivation.

According to game theory, any solvable game must explicitly define four elements and equilibrium concepts:

**Players**: Female/male individuals instantiated by the Agent layer (energy budget, perception radius as exogenous parameters).

**Strategy Variables**: All surface behaviors reduce to a single continuous variable—the **raising_share** vector.

**Payoff Calculation (Three-Step Scoring Rule)**:
1. **Resource Extraction**: Aggregate all inputs for nest k, $\sum \text{raising\_share}_k$, calculate actual acquired resource amount $R_{\text{total},k}$
2. **Logistic Conversion**:
   $$
   \text{fledglings}_k = \frac{K}{1 + \exp\{-r \cdot (R_{\text{total},k} - R_0)\}}
   $$
3. **Payoff Allocation**:
   - Female: $\sum \text{fledglings}_k$
   - Male: $\sum \text{fledglings}_k$ allocated paternity by investment proportion

**Information Structure (Two-Tier Bounded Channel)**:
- **Free Information**: Global nest locations (passive perception)
- **Paid Information**: Neighboring nest internal composition and individual strategies (active search, success rate exponentially decaying), individuals only build beliefs about population behavior frequencies

These four elements define the individual strategy selection problem: **selecting raising_share to maximize expected payoff under information constraints**.

#### 2.3.3 Stage 1: Search_share Evolution Dynamics

**Search_share Bayesian Update Framework**

The model models cross-round evolution of search_share as **random initialization + single-step Bayesian update**:
$$
\text{search\_share}_{t+1} = \text{BayesianUpdate}\left(\text{search\_share}_t \mid \text{social\_learning\_evidence}_t\right)
$$

Where:
- **Prior**: Current round's search_share value, representing individual's existing belief about optimal strategy
- **Likelihood**: Constructed from **social learning evidence**, i.e., statistical distribution of search_share from high-payoff neighboring agents
- **Posterior**: Next round's search_share, automatically contracting toward successful experience through Bayesian rule

**Modeling Motivation: From Impossible to Achievable**

Directly modeling how individuals optimally decide search_share is an impossible task—this requires comparing **cross-period potential payoff of exploring new nests** with **direct payoff of staying at current nest**, and also estimating the delayed value of information acquisition, belonging to dynamic programming problems beyond current cognitive science understanding. Since we as modelers cannot explicitly solve this optimization, birds are even less likely to possess such hyper-rationality.

However, birds **do engage in social learning**—they observe neighbor strategies and payoffs, imitating successful behaviors (Birkhead 1981). This real mechanism happens to be perfectly isomorphic with the mathematical structure of **Bayesian update**: using neighbor strategies as likelihood evidence, own current strategy as prior, completing strategy adjustment through posterior calculation. Update intensity automatically increases with neighbor advantage and decreases with own experience accumulation, without additional parameters.

Random initialization captures heterogeneity in birds and also provides possible learning objects.

**Search Share Decision and Bayesian Update Mechanism - Detailed Process**:

1. **Initial Setup**: Each agent's `search_share` is randomly generated as a fixed value at initialization, updated through social learning in subsequent rounds.

2. **Social Learning and Bayesian Update**:
   - At the end of each round, agents collect same-sex individuals' `search_share` and corresponding `fitness` data through `belief_system`
   - These data update agent's belief about `search_share` through Bayesian update:
     - **Likelihood**: Based on observed same-sex individuals' `search_share` and `fitness` data
     - **Prior**: Agent's current belief about `search_share`
     - **Posterior**: Combining likelihood and prior, updating agent's belief about `search_share`
   - Updated belief influences agent's `search_share` decision in next round

3. **Data Collection**: After each round's search, agents submit observed same-sex individuals' `search_share` and `fitness` data to `belief_system`

4. **Bayesian Update Process**:
   - Calculate observed same-sex individuals' average `search_share` and average `fitness`
   - Use these averages as likelihood, combine with agent's current prior belief, calculate posterior belief
   - Updated posterior belief serves as next round's prior belief

5. **Decision Adjustment**: Agent adjusts next round's `search_share` decision based on updated belief, either by directly sampling posterior distribution or adjusting based on posterior distribution mean

#### 2.3.4 Stage 2: Raising_share Allocation Optimization

**Optimization Problem Formalization**

Given search_share, agents need to allocate remaining energy among available nests, transforming into standard **expected utility maximization problem**:
$$
\max_{\{\text{raising\_share}_k\}} \sum_{k} \text{payoff}_k \quad \text{s.t.} \sum \text{raising\_share}_k = 1 - \text{search\_share}
$$

In the context of known belief $\hat{o}_k$ (expected total investment from others in nest k), female agent solves the following constrained optimization problem:

**Objective Function**:
$$
\max_{\{r_k\}} \sum_{k \in \text{owned\_nests}} \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k)
$$

**Constraints**:
$$
\sum_k r_k = 1 - s, \quad r_k \geq 0
$$

Where $\mathcal{F}(\cdot)$ is the expected fitness function, $s$ is search_share, $r_k$ is the raising_share to be decided.

**Modeling Choice: Natural Selection as Implicit Optimizer**

We directly assume individuals can solve this problem through marginal utility equalization or Lagrange multiplier method. The biological justification lies in **natural selection programming**—the evolutionary process itself performs gradient descent in strategy space over millions of years, and retained decision rules necessarily approximate optimal response functions. Individuals need not explicitly differentiate in their brains; their behavioral patterns are already encoded as heuristics that are "approximately optimal given beliefs".

This assumption, while Panglossian optimism, avoids introducing compound errors by overlaying a second layer of behavioral rule approximation on an already approximated logistic utility function. More importantly, this assumption gives the model **interpretability**: it can be clearly argued that "given the belief, this strategy is the optimal response", meeting the minimum requirements of game theory for rationality assumptions.

**Marginal Expected Utility Calculation**

Using numerical differentiation method to calculate marginal utility, avoiding differentiability assumptions about the fitness function:

$$
\text{MU}_k(r_k) = \frac{\mathcal{F}(r_k + \hat{o}_k + \Delta, \mathbf{p}_k) - \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k)}{\Delta}
$$

Where $\Delta$ is the configuration parameter `marginal_delta`.

**Greedy Iterative Allocation Algorithm**

Discretize total budget $B = 1 - s$ into $N$ equal parts ($N$ from configuration parameter `allocation_steps`), approaching optimal solution through iterative allocation:

**Initialization**: For all nests $k$, set initial allocation $r_k^{(0)} = 0$

**Iteration Process**: For $t = 1$ to $N$:
1. Calculate marginal utility $\text{MU}_k$ for each nest based on current allocation $r_k^{(t-1)}$
2. Select nest $k^* = \arg\max_k \text{MU}_k$ with maximum marginal utility
3. Update allocation: $r_{k^*}^{(t)} = r_{k^*}^{(t-1)} + \delta$, other nests remain unchanged

**Normalization**: After iteration completes:
$$
r_k^{\text{final}} = r_k^{(N)} \times \frac{B}{\sum_j r_j^{(N)}}
$$

Ensuring strict satisfaction of budget constraints and elimination of floating-point error accumulation.

**Parameter Requirements**: Default iteration steps $N$ is 20, step size $\delta = B/N$ must satisfy $\delta \leq 0.05$ to ensure approximation accuracy.

#### 2.3.5 Belief System (belief_system.py)

**Requirement**: Implement Bayesian updates for search share and raising share belief management.

**Core Functions**:

1. **Search-Share Decision Support**
   - After each round of search, record observed same-sex individuals' `(search_share, fitness)` pairs
   - Use descriptive statistics to obtain average performance of same-sex individuals this round as likelihood; use agent's previous round belief about search_share as prior
   - Execute naive Bayes update, producing posterior belief for agent to directly sample or take expectation when deciding own `search_share` the next day

2. **Raising-Share Behavior Prediction**
   - After each round of search, record observed "target nest - occupant" `(nest_id, agent_id, raising_share(in this nest))` triples
   - Calculate average `raising_share` by sex group (descriptive statistics) as likelihood; use agent's previous round belief about others' investment in each nest as prior
   - Execute naive Bayes update, producing posterior belief, obtaining probability distribution of "other individuals' expected investment in nests I care about", as exogenous input for own `raising_share` Lagrange optimization the next day

**Belief System Interface Specification**:
- `get_search_belief(agent_id) → float`: Return agent's point estimate (posterior mean) of optimal search_share
- `get_raising_belief(agent_id, nest_id) → float`: Return agent's point estimate of expected total investment $\hat{o}_k$ in nest_id
- `submit_search_observation()`: Submit search observation data
- `update_search_beliefs()`: Execute belief update

Both updates are stored independently, normalized independently, all completed within belief_system; external strategy layer only obtains normalized probability through `get_belief(agent_id, behavior_class)`, without perceiving update details.

Belief update operations must be uniformly executed by `belief_system.update_beliefs()` at the end of each round; strategy layer must not directly modify belief system internal state, ensuring decoupling of observation data and decision logic.

#### 2.3.6 Payoff Functions and Paternity Allocation

**Three-Layer Mapping from Investment to Reproductive Output**

**Layer 1: Resource Extraction** - Mapping from total_raising_share to total_resource

Formula: For nest k, aggregate all participants' total investment $\sum \text{raising\_share}_k$ and home range resource matrix, calculate actual acquired resource amount $R_{\text{total},k}$ through extraction cost function.

**Layer 2: Logistic Conversion** - Mapping from total_resource to fledglings

Formula: Map $R_{\text{total},k}$ to expected number of surviving offspring:
$$
\text{fledglings}_k = \frac{K}{1 + \exp\{-r \cdot (R_{\text{total},k} - R_0)\}}
$$

Parameters: K (half-saturation constant), r (conversion efficiency), R₀ (resource threshold).

**Justification**: S-shaped curve embodies:
1. **Diminishing marginal utility**: Return on investment decreases when resources saturate
2. **Base mortality**: Positive output below R₀, corresponding to natural loss of nest without investment
3. **Differentiability**: Smooth function avoids optimization traps, retains biological plausibility (Davies 1986 Fig.3)

**Layer 3: Payoff Allocation** - Mapping from fledglings to payoff

Formulas:
- Female: $\text{payoff}_{\text{female}} = \sum_{k \in \text{her\_nests}} \text{fledglings}_k - c_{\text{egg}}$
- Male: $\text{payoff}_{\text{male}} = \sum_k \left( \frac{\text{raising\_share}_{\text{male},k}}{\sum \text{raising\_share}_k} \times \text{fledglings}_k \right)$

**Key Simplification Assumption**: Paternity allocated proportionally by raising_share. Need to cite Davies 1992 or other paternity allocation literature, and prepare defensive arguments.

**Male Payoff**:
$$
\text{payoff}_{\text{male}} = \left( \frac{\text{raising\_share}_{\text{male}}}{\sum \text{raising\_share}_{\text{male}}} \right) \times \text{surviving\_fledglings}
$$

**Female Payoff**:
$$
\text{payoff}_{\text{female}} = \sum_{k \in \text{her\_nests}} \text{surviving\_fledglings}_k - c_{\text{egg}}
$$

Where $c_{\text{egg}}$ is egg-laying cost (can be set to 0 and marked as arguable point). This design allows females to allocate raising_share among multiple nests, achieving polyandry/polygyny continuum.

### 2.4 Simulation Layer: Execution Flow

#### 2.4.1 Main Loop (game_loop.py)

**Responsibility**: Manage daily asynchronous action iteration, execute `random.shuffle()` each round to randomize action order.

**Initialization**: Randomly generate initial positions of female and male individuals in the world (uniform distribution).

**Process**: Each round, all individuals act once in shuffled order.

**Biological Plausibility**: Random initialization positions conform to the territory establishment mechanism of resident wren species—spring territories are local adjustments based on winter home ranges rather than migration (Birkhead 1981), and actual observations show individuals forming stable groups around fixed resource points (Bishton 1986). The model's core mechanism is resource-driven dynamic territory adjustment (Davies & Lundberg 1984). Random initial positions converge to observationally consistent state after first round iteration (females contracting toward high-density patches, males competing to merge), with initial errors naturally eliminated by dynamic process. This simplification conforms to the model's "minimum assumption" principle and does not affect accuracy of emergent behaviors like mating systems.

**Sequential Decision Framework: Modeling Bounded Rationality Without Infinite Recursion**

The fundamental challenge in modeling strategic interactions among mating animals lies in the intractable recursion of predicting others' responses—an infinite regress where Player A's optimal move depends on Player B's anticipated reaction, which in turn depends on A's reaction to B's reaction, and so on. Such higher-order reasoning is computationally prohibitive and biologically implausible, as wild Dunnocks lack the cognitive architecture for recursive mind-reading.

We resolve this impasse by adopting a **sequential decision framework** within each round: all agents are randomly shuffled to generate a decision order. This shuffling is not merely a computational convenience but a realistic representation of natural asynchrony, where birds cannot synchronize reproductive decisions nor observe real-time updates from all conspecifics.

The critical innovation is that **agents cannot know their position in the decision queue**. This veil of ignorance fundamentally transforms the prediction problem: rather than forecasting the contingent moves of specific rivals—a futile endeavor when any given neighbor may have already acted or may yet act—agents must instead form beliefs about **population-level frequencies**. An alpha male does not ask "Will rival A chase the beta?" but instead "What is the probability that a randomly-selected neighboring male would chase?"

This aggregate-level belief formation is naturally computed through **Bayesian updating** on local observations, where each agent tracks the frequency of actions among its immediate neighbors and updates its prior using a simple beta-binomial model. The limited sample size inherent in local perception (each bird only observes 5-10 neighbors) is mitigated by two mechanisms:
- **Temporal smoothing**: Beliefs decay slowly across rounds to reflect memory
- **Social learning**: Agents incorporate neighbors' beliefs at a discount factor, effectively pooling observations across the population

This framework yields three crucial advantages:
1. **Biologically**: Reflects **bounded rationality**—agents rely on heuristic rules derived from descriptive statistics rather than forward-looking rationality
2. **Computationally**: Reduces complexity from O(N!) to O(N) per round
3. **Theoretically**: Sidesteps infinite regress of best-response functions and problematic multiplicity of Nash equilibria

**Daily Strategy and Action Flow**:

1. At the start of each round, game_loop calls WorldState to get current world snapshot (resource distribution and all agent positions)
2. Iterate through each agent:
   - Agent decides this round's strategy based on snapshot and own knowledge base: search_share and raising_share vector for each nest
   - Decision results written to local cache, no changes this round
3. Generate action list:
   - Collect all (agent, nest) combinations with raising_share > 0 from cache
   - Execute random shuffle on this list to get random action sequence
4. Execute actions in shuffled order for each (agent, nest) based on strategy decided in step 2:
   - **Search**: Obtain nest information by calling WorldState.query_nest_composition method, add search results to agent's knowledge base (belief_system), and update agent's search_share
   - **Raise**: Call mining function in fitness.py through strategy
     - First determine individual's explorable area based on raising_share
     - Select patch with maximum resource amount in explorable area
     - Extract resources from corresponding resource patch at fixed ratio ρ
     - Extraction amount immediately deducted from WorldState and accumulated to target Nest's acquired resource record
5. After extraction completes, game_loop notifies WorldState to complete this round's resource reset (negative binomial), and clears all nests' acquired resource records

#### 2.4.2 Orchestrator (orchestrator.py)

**Responsibility**: Runtime binding of Agent and Strategy, executing `decide_search_share()` and `decide_raising_allocation()`, synchronizing updates to Nest and Agent states.

**Key Operations**: Ensure strong consistency between `Nest.male_ids` and `FemaleAgent.male_count`.

**Design Advantages: Agent-Strategy Decoupling**:

1. **Strategy Pluggability**: `orchestrator` dynamically binds Agent and Strategy, enabling horizontal comparison of different decision algorithms (e.g., Bayesian vs. reinforcement learning) without modifying Agent code, achieving "hot-swappable" experimental design.

2. **State Consistency Guarantee**: Centrally manage all cross-entity state updates (e.g., `Nest.male_ids` and `FemaleAgent.male_count`), transforming distributed operations into atomic transactions, eliminating race conditions.

3. **Testability**: Strategy designed as pure function interface `decide(...)->allocation`, given same input must produce same output. Unit tests can bypass Agent instances, directly verifying decision logic with mock data, achieving separation-of-concerns test coverage.

4. **Parallelization Friendly**: Stateless Strategy can be shared by multiple same-type Agents, avoiding memory duplication overhead; pure function characteristics allow decision computation batch parallelization without write conflicts, crucial for large-scale simulation.

5. **Cognitive Fidelity**: Real animals' decision rules can switch with experience. Separation architecture supports future introduction of fitness threshold-based strategy elimination mechanisms, making "strategy selection" itself an evolvable endogenous variable.

**Lifecycle**:
- Instantiated once by bootstrap, survives entire simulation
- Internally maintains daily "Agent → Strategy instance" mapping table; can rebind before first decision each day, read-only rest of time

**Daily Binding**:
- Provide `bind_one(agent)` interface:
  - If agent already has mapping and strategy type unchanged, return original strategy directly
  - If strategy type switches, instantiate new Strategy and replace old mapping
- Provide `bind_all(agent_list)` batch binding for game_loop to call once before daily decisions

**Runtime Invocation**:
- Provide `get_strategy(agent)` for game_loop to quickly obtain agent's strategy object when iterating agents
- Does not provide any numerical calculation, share normalization, or resource deduction logic; these completed by Strategy layer and WorldState direct interaction

**State Isolation**:
- Orchestrator itself does not save Agent or Strategy internal state, only holds mapping relationships
- Strategy instance internal parameters (beliefs, memory, etc.) managed by Strategy layer itself, Orchestrator only forwards calls

#### 2.4.3 Entry Point (main.py)

**Responsibility**: Read config.py parameters, initialize WorldGenerator to create resource map, instantiate Agents and Strategies, start simulation loop.

**Code Example**:
```python
def main():
    world_state, female_agents, male_agents, orchestrator = bootstrap()
    game_loop = GameLoop(world_state, female_agents, male_agents, orchestrator)
    simulation_results = game_loop.run(num_days)
```

### 2.5 Fitness Functions: Mapping Resources to Offspring Survival

#### 2.5.1 Resource Extraction Model

**Requirement**: Implement resource extraction and fitness calculation functions.

**Input**: `total_breedshare` and resource matrix around nest
**Output**: Actual acquired resource amount
**Rule**: The farther from nest center, the higher the extraction cost (cost increases linearly or exponentially per outer expansion ring)

**Three-Step Resource Extraction Calculation**:
1. **Determine Exploration Area**: Circular area centered at nest_position with home_range_radius as radius
2. **Select Target Patch**: Select grid cell with maximum resource value in exploration area
   target_pos = argmax_{pos in range} world_state.get_resource_density(pos)
3. **Extract by Ratio**: Actual extraction = rho × current resource value of that patch
   extracted = rho × get_resource_density(target_pos)
4. **Update World State**: Immediately deduct resources from that patch

**Implementation Design**: `core/fitness.py` implements `mine_resources()` or `extract_resources()` function, cost coefficient from config.yaml or config.py.

**Resource Extraction Rate**: ρ (rho) - Fixed proportion for resource extraction, default value to be confirmed (mentioned as 0.33 or 0.3 in different documents).

#### 2.5.2 Logistic Conversion

Actual acquired resource amount maps to expected surviving offspring through logistic function:
$$
\text{fledglings} = \frac{K}{1 + e^{-r(R - R_0)}}
$$

Where K is half-saturation constant, R is actual resource amount, r is conversion efficiency, R₀ is resource threshold.

**Biological Plausibility**: Diminishing marginal utility characteristics reflect resource saturation and density-dependent effects, "leakage" at very low investment corresponds to base mortality rate, consistent with field data.

#### 2.5.3 Payoff Calculation Implementation

- **Female**: Sum of fledglings from all participating nests (configurable whether to deduct egg-laying cost constant)
- **Male**: Paternity proportion × fledglings

**Counterfactual Fitness**: Provide `calculate_female_fitness_counterfactual` and `calculate_male_fitness_counterfactual` methods to evaluate impact of resource allocation.

---

## 3. Non-Functional Requirements

### 3.1 Engineering Implementation Constraints

- All function signatures must use type annotations
- All parameters must come from config.yaml or config.py, no hard-coding allowed
- No new parameters allowed in code
- Enforce PEP 8 standards rigorously
- Comprehensive type hinting as contract to make model assumptions explicit
- Codebase must be navigable for future collaborators
- Model must remain a living tool rather than a fragile prototype

### 3.2 Performance Requirements

- Large-scale simulations feasible on standard hardware
- Computational complexity reduced from O(N!) to O(N) per round
- Stateless Strategy allows batch parallelization without write conflicts
- Pure function characteristics enable decision computation parallelization

### 3.3 Extensibility Requirements

- Strategy modules can be hot-swapped without modifying Agent code
- Future refinements (sex-specific detection abilities, habitat-dependent λ values) can be integrated without rearchitecting core model
- Support for future introduction of fitness threshold-based strategy elimination mechanisms
- Alternative optimization criteria (risk aversion, kin selection) can be substituted without redesigning core architecture

### 3.4 Testability Requirements

- Strategy designed as pure function interface
- Unit tests can bypass Agent instances, directly verify decision logic with mock data
- Separation of concerns in test coverage

---

## 4. Configuration Parameters

### 4.1 Required Configuration Parameters (config.py)

**Global Parameters**:
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| RANDOM_SEED | Random seed | 42 |
| GRID_SIZE | Grid size | 500 |
| initial_female_count | Initial female count | 20 |
| initial_male_count | Initial male count | 20 |
| simulation_rounds | Simulation rounds | 5 |

**World Parameters**:
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| RESOURCE_LEVEL | Resource level | 100 |
| AGGREGATION_LEVEL | Aggregation level | 5 |

**Search Parameters**:
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| SEARCH_COST | Search efficiency constant λ | 0.5 |

**Fitness Calculation Parameters**:
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| LOGISTIC_K | Logistic function maximum | 10 |
| LOGISTIC_R | Logistic function growth rate | 0.1 |
| LOGISTIC_A | Logistic function parameter | 100 |

**Extraction Parameters**:
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| RESOURCE_EXTRACTION_RATE | Resource extraction rate ρ | 0.3 |

**Allocation Parameters**:
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| ALLOCATION_STEPS | Greedy iteration steps | 20 |
| MARGINAL_DELTA | Marginal utility calculation step | 0.01 |
| HOME_RANGE_RADIUS | Home range radius | 3 |

### 4.2 Pending Technical Issues and Parameter System

**Algorithm Selection Matrix**:
| Issue | Option A | Option B | Option C |
|-------|----------|----------|----------|
| **Extraction Cost Curve** | Linear increasing | Exponential increasing | Step fixed |
| **Breedshare Allocation Algorithm** | Greedy iteration | Lagrange analytical | Randomized trial-and-error |
| **Belief Update Frequency** | Update every round | Update every 3 rounds | Update only during social learning |
| **Micro-step Quantity** | Fixed 10 steps/round | Adaptive | Variable configuration |

---

## 5. Future Enhancement Paths

**Strategy Expansion** (currently hard-coded in initial version):
- **Risk Aversion**: Introduce variance penalty term in payoff function
- **Kin Selection**: Adjust payoff weights to reflect kinship relationships
- **Individual Heterogeneity**: Let K or r vary between individuals, reflecting quality differences

**System Expansion Directions**:
1. **Strategy Expansion**: Support more types of strategies, such as genetic algorithm-based strategies
2. **Environmental Complexity**: Increase environmental dynamics, such as seasonal resource variation, resource redistribution
3. **Agent Behavior**: Expand agent behavior patterns, such as territory defense, mate choice, etc.
4. **Visualization**: Add real-time visualization functionality to display simulation process
5. **Performance Optimization**: Optimize simulation performance, support larger scale agents and longer duration simulations

---

## 6. Biological Justifications and References

### 6.1 Key Biological References

- **Birkhead 1981**: Wren territory establishment mechanism, social learning in birds
- **Bishton 1986**: Individuals forming stable groups around fixed resource points
- **Davies & Lundberg 1984**: Resource-driven dynamic territory adjustment, experimental manipulation of food abundance
- **Davies 1986**: Logistic conversion biological plausibility (Fig.3)
- **Davies 1992**: Paternity allocation literature (to be cited for key simplification assumption)

### 6.2 Key Modeling Assumptions

1. **Energy Budget Constraint**: All individuals have energy budget = 1.0 (can be extended to `agent.energy_budget` for individual heterogeneity)
2. **Paternity Proportional to Raising Share**: Key simplification requiring defensive argumentation
3. **Egg-laying Cost**: Configurable (can be set to 0 and marked as arguable point)
4. **Initial Position Randomization**: Converges to observationally consistent state after first round iteration
5. **Sequential Decision Framework**: Agents cannot know their position in decision queue
6. **Bounded Rationality**: Agents rely on heuristic rules rather than forward-looking rationality

---

## 7. Implementation Phases

### Phase 1: Foundation (Implemented by Developer)
- Implement game_loop.py main loop framework (without specific extraction logic)
- Implement Nest and Agent data classes
- Implement world_generator and basic query interfaces, including query_nest_composition method
- Implement belief_system skeleton (empty functions)

### Phase 2: Core Logic (Joint Review)
- Implement orchestrator and strategy core logic after confirming all algorithm details
- Implement fitness.py resource extraction and calculation functions
- Implement female_strategy.py and male_strategy.py decision logic


