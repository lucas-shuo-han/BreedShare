# Application Scenarios for the Energy-Budget Allocation Framework

This document outlines three high‑compatibility application domains for our energy‑budget allocation framework. The core abstraction—individuals with a fixed budget that must be split between *exploration* (search) and *exploitation* (raising share), embedded in a spatially heterogeneous environment with information asymmetry and social learning—can be naturally mapped to diverse fields. Each scenario preserves the model’s mathematical core while offering new research questions.

---

## 1. Labor Market Model (Producers & Consumers)

### Scenario Description
A labor market where workers (employees) allocate their time between searching for new job opportunities and working for current employers. Firms provide jobs and pay wages based on a worker’s contribution. Workers face spatial frictions (commuting costs) and incomplete information about actual job conditions; they learn through personal exploration and by observing peers. Firms compete for labour, and the spatial distribution of industries shapes employment patterns.

### Role Mapping
| Original Model      | Labor Market Model                |
|---------------------|-----------------------------------|
| Female              | Firm (employer)                   |
| Male                | Worker (employee)                 |
| Nest                | Job position / workplace          |
| Resource            | Wage package / firm’s capital     |
| Raising share       | Time invested in a specific job   |
| Search share        | Time spent job‑hunting / exploring|
| Search cost λ       | Difficulty of obtaining true wage information |
| Extraction rate ρ   | Worker’s productivity             |
| Fitness             | Worker’s total income / firm’s output |

### Key Variable Correspondence
- **Worker’s budget**: Total time = 1, constraint `search_share + ∑raising_share = 1`.
- **Firm output**: Depends on total worker input and the firm’s own resources (location, capital); logistic function models diminishing returns.
- **Wage**: Distributed proportionally to each worker’s raising share (male payoff analogy).
- **Spatial information**: Firms are located on a grid; `query_nest_composition` models the costly discovery of true job attributes.
- **Social learning**: Workers observe the job choices and incomes of others, updating beliefs via Bayesian inference.

### Potential Research Questions
- How does the spatial clustering of industries affect commuting patterns and wage inequality?
- What is the impact of labour‑market transparency (λ) on job mobility and equilibrium unemployment?
- Can worker heterogeneity (skill levels) lead to occupational segregation?
- How do firms compete for labour in a spatial landscape, and what urban forms emerge?

### Comparison with Original Model
- **Same**: Budget constraint, spatial resources, information asymmetry, social learning.
- **Different**: Fitness must be split into worker income and firm profit; firms may actively adjust their offers (e.g., raise wages) to attract workers, whereas original females are passive recipients.

---

## 2. Residential Choice & Commuting Model

### Scenario Description
Urban residents decide how to allocate their time between commuting/exploring new neighbourhoods and staying in a particular residential/work area. Different zones offer varying levels of employment density, public services, and amenities. Residents have imperfect information about zone quality and learn by exploration and by observing neighbours. The resulting spatial distribution of residents determines urban form and segregation.

### Role Mapping
| Original Model      | Residential Choice Model          |
|---------------------|-----------------------------------|
| Female              | Urban zone (employment centre, district) |
| Male                | Resident (household)              |
| Nest                | Specific zone (e.g., business district) |
| Resource            | Zone’s job density, services, housing quality |
| Raising share       | Time spent in a zone (working, living) |
| Search share        | Time spent commuting / exploring new zones |
| Search cost λ       | Difficulty of obtaining reliable zone information |
| Extraction rate ρ   | Efficiency of converting zone resources into utility (e.g., commuting speed) |
| Fitness             | Resident’s total utility (income, satisfaction) |

### Key Variable Correspondence
- **Resident’s budget**: Total daily time = 1, constraint `commuting/exploring + time in zones = 1`.
- **Zone resources**: Generated via negative binomial distribution to create heterogeneous spatial patches.
- **Utility function**: Logistic transform of zone resources, capturing congestion effects (diminishing returns).
- **Information**: Residents learn zone quality through costly search (`query_nest_composition`) or by observing neighbours’ choices and outcomes.
- **Social learning**: Residents update beliefs about zone attractiveness based on observed peers’ utilities.

### Potential Research Questions
- How does the spatial distribution of jobs (monocentric vs. polycentric) shape commuting times and residential sorting?
- Can high information costs (λ) lock residents into suboptimal neighbourhoods?
- How do income groups self‑segregate, and what policies might reduce segregation?
- What is the effect of transport improvements (lower λ) on urban sprawl and equity?

### Comparison with Original Model
- **Same**: Budget allocation, spatial heterogeneity, information costs, social learning.
- **Different**: Residents can simultaneously interact with multiple zones (e.g., work in one, live in another), requiring a multi‑nest participation mechanism not present in the original mating context.

---

## 3. Cloud Computing Resource Scheduling Model

### Scenario Description
Distributed computing nodes (servers, VMs) must allocate computational resources among multiple tasks while also discovering new tasks that appear in the system. Each node balances execution of current tasks (raising share) with exploring for new tasks (search share). Tasks yield rewards (e.g., credits) distributed proportionally to each node’s contribution. Nodes operate under incomplete information about task demands and learn by observing neighbours.

### Role Mapping
| Original Model      | Cloud Scheduling Model            |
|---------------------|-----------------------------------|
| Female              | Task instance (job)               |
| Male                | Computing node                    |
| Nest                | Task queue / virtual machine      |
| Resource            | Required CPU, memory, bandwidth   |
| Raising share       | Computational resources allocated to a task |
| Search share        | Overhead for task discovery / load balancing |
| Search cost λ       | Difficulty of assessing a task’s true requirements |
| Extraction rate ρ   | Node’s processing efficiency (FLOPS) |
| Fitness             | Total reward earned by node / task completion |

### Key Variable Correspondence
- **Node budget**: Total computational capacity = 1, constraint `search overhead + ∑raising shares = 1`.
- **Task resource needs**: May vary over time; modelled as spatial “resource hotspots” on a grid.
- **Completion function**: Task completion follows a logistic curve with total input (diminishing returns).
- **Reward distribution**: Proportionally to each node’s raising share (male payoff analogy).
- **Information**: Nodes learn about true task demands through active probing (`query_nest_composition`) and by observing allocations of neighbours.
- **Social learning**: Nodes update beliefs about optimal task‑mix based on observed neighbours’ rewards.

### Potential Research Questions
- How do different task distributions (CPU‑ vs. I/O‑intensive) affect node scheduling strategies?
- What is the impact of information latency (λ) on load balancing in distributed systems?
- Can node heterogeneity (different processing speeds) lead to systemic resource misallocation?
- Does social learning among nodes improve overall cluster efficiency?

### Comparison with Original Model
- **Same**: Budget constraint, spatial representation of tasks, information costs, social learning.
- **Different**: Nodes may cooperate (e.g., task migration), whereas original males are primarily competitors. Cooperation mechanisms could be introduced.

---

## Summary

All three scenarios retain the core mathematical structure of the original model—budget‑constrained agents choosing between exploration and exploitation in a spatially heterogeneous environment with costly information and social learning. Minimal changes to the codebase (redefining fitness functions and agent interactions) would allow rapid prototyping in each domain. The labour market model is the most direct mapping and offers the richest set of immediately testable hypotheses, making it the recommended first extension.