# BreedShare — Model Description

This document describes what the model assumes and why. Passages marked as design rationale are the arguments behind each modelling choice; equations match the code in this repository, and `tests/test_model.py` checks them. What the model produces is in [results.md](results.md); how the code is organised is in [architecture.md](architecture.md); what is not yet done is in [ROADMAP.md](../ROADMAP.md).

---

## 1. Purpose

The model explores how the spatiotemporal distribution of resources drives the dynamic evolution of mating systems, for example:

- Emergence conditions of polyandry/polygyny mating systems
- Optimal strategies for time/energy budget allocation between males and females
- Game mechanisms formed by dynamic territory adjustments

**Abstraction over realism.** Our objective is to identify the minimal set of biologically meaningful parameters that govern mating system dynamics, rather than replicate the full complexity of avian behavior. By prioritizing higher-level abstraction—reducing parameter space, accelerating simulation, and enhancing explainability—we sacrifice granular realism to amplify intuitive understanding and cross-species generalizability. This approach acknowledges that some implementation details may appear abstract and counterintuitive, but the gains in computational tractability and theoretical clarity justify the architectural investment.

The reference system is the dunnock (*Prunella modularis*), whose variable mating system (monogamy, polyandry, polygyny and polygynandry within one population) is documented by Davies and colleagues.

---

## 2. Core abstraction: energy as the single currency

Our model reframes mating system dynamics as a problem of **temporal and energetic resource allocation**. Both sexes face a fundamental constraint: time and effort invested in one activity (e.g., guarding a nest, searching for additional mates) cannot be allocated elsewhere. Strategic decisions such as "accept beta male" or "abandon nest" are not primitive actions but **surface-level manifestations** of underlying **breedshare profiles**—vectors describing how an individual distributes its finite energetic budget across competing reproductive tasks.

Every individual satisfies the budget constraint:

$$
\text{search\_share} + \sum_{k \in \text{nests}} \text{raising\_share}_k = 1
$$

**search_share** is investment in exploring unknown mates and territories; **raising_share** is investment in consolidating current reproductive units. Abandonment corresponds to raising_shareₖ = 0, while defending and accepting mates are reflected in the relative proportion of raising_share between individuals, without being modelled separately.

**Female behaviours, reduced to the allocation vector**

| Behaviour | How it appears in the allocation |
|---|---|
| Accept / reject a beta male | Whether the males' total raising_share in her nest goes from 0 to positive, and whether her own share adjusts |
| Abandon vs. stay | Whether her raising_share for that nest is 0 or positive |
| Single vs. multi-nest breeding | Whether the vector has one or several positive elements |
| Territory size | A nest's foraging range grows with the total raising_share it receives — more energy covers a larger range |

**Male behaviours, reduced to the allocation vector**

| Behaviour | How it appears in the allocation |
|---|---|
| Join / leave a nest | His raising_share for that nest goes from 0 to positive, or back |
| Parental care intensity | The value of his raising_share for that nest |
| Disruptive competition | Not yet implemented; could be modelled as negative contributions |

Because every behaviour draws on the same budget, trade-offs between behaviours follow from the constraint instead of being encoded one by one.

---

## 3. Environment

### 3.1 Resource landscape

The world is a 200 × 200 grid. Resources follow a gamma–Poisson process, the standard construction of the negative binomial (NB):

- Each 10 × 10 **patch** has a persistent habitat quality $q \sim \text{Gamma}(k, 1/k)$ with mean 1. The shape $k = (1-a)/a$ comes from the aggregation level $a$: small $a$ gives nearly equal patches, large $a$ a few rich patches in a poor matrix.
- Each round, each cell's resources are drawn fresh as $\text{Poisson}(q \cdot \bar{R})$, where $\bar{R}$ is the resource level.

A cell's daily value is therefore NB-distributed with mean $\bar{R}$, and $\bar{R}$ and $a$ control abundance and aggregation independently.

**Design rationale — why the negative binomial.** Prior research identifies two primary drivers of mating system evolution: total resource abundance and spatial aggregation of resources. The negative binomial directly parameterizes both with two interpretable variables (mean and aggregation level), replacing four arbitrary patch parameters with a mathematically tractable alternative.

This simplification does not sacrifice realism: the original patch model was already an approximation of heterogeneous micro-habitats. The negative binomial provides a first-principles statistical representation of aggregation, eliminating nested approximations while preserving the capacity to generate biologically plausible landscapes. The cell-based model itself still reflects aggregation, is more computationally efficient, and approaches a continuous landscape as the grid size grows.

A potential objection is that territories containing many cells might approximate a normal distribution by the Central Limit Theorem. This is unlikely for three reasons:

1. Mating system evolution depends on population-level aggregation, captured by the negative binomial's higher moments.
2. Individual fitness is determined by territory size, not within-territory patchiness.
3. The Central Limit Theorem's assumptions are not met: cells in the same patch share one quality value, so they are not independent, and a territory's total keeps the patch-level variance.

Resources are regenerated around the same patch qualities at the end of every round. Habitat quality is persistent, so a bird knows how good the area around a nest is; the day's exact yield is not known in advance.

### 3.2 Initial positions

Individuals start at uniformly random positions. Each female then settles her nest on the best-habitat cell within 10 cells of her start; a male's start is his home, from which he reaches nests within the neighbourhood radius (50 cells).

**Design rationale.** Random initial positions conform to the territory establishment mechanism of resident species—spring territories are local adjustments based on winter home ranges rather than migration (Birkhead 1981), and observations show individuals forming stable groups around fixed resource points (Bishton 1986). The model's core mechanism is resource-driven dynamic territory adjustment (Davies & Lundberg 1984). The intended behaviour is that random starting positions converge after the first rounds—females contracting toward high-density patches, males competing to merge—so the initial error is removed by the dynamics. Random initialisation also provides heterogeneity, and therefore something to learn from.

---

## 4. Information: a two-tier structure

The cognitive architecture of wild animals imposes severe constraints on information processing: they cannot engage in infinite recursive reasoning about conspecifics' strategic responses, nor can they instantaneously survey entire landscapes. The model uses a parsimonious two-tier structure.

**Free information — where the nests are.** Agents know all nest locations, not as a literal panopticon but as a tractable abstraction of the information conveyed by territorial song, movement patterns, and spatial memory accumulated over weeks of ranging. Dunnocks can detect singing males and active nests within hundreds of meters without dedicated search effort, yet remain ignorant of the internal composition of these nests.

**Costly information — who is in them.** Knowing a nest's internal state (its male and female roster and their investment) requires search. The probability of success decays with distance and grows with search investment:

$$
p_i = 1 - \exp\left(-\lambda \cdot \frac{\text{search\_share}}{d_i}\right)
$$

λ is the search efficiency constant, standing for vegetation density and predation risk: low λ means costly search and a tendency to stay; high λ means cheap search and a tendency to explore. Distance $d_i$ is measured in units of the neighbourhood radius.

**As implemented.** Each round, a male makes one search attempt on every reachable nest he is not already caring for. (Females care only for their own nest, so in this version their search share buys nothing; see ROADMAP.) A success reveals that nest's composition at the end of the round: how much the female and each male invested. A bird always knows the nests it cares for, because it is there. For a nest it has never observed, it assumes the population-average investment (coarse, free information); for a nest observed earlier, it keeps its last observation, which may be out of date. This is what search buys: accurate beliefs about where care is needed.

**Hypothesis to test.** If λ is raised—analogous to supplemental feeding—optimal search_share should decline, female ranges contract, and the mating system shift toward monogamy and polygyny, as in the food-supplementation experiment of Davies & Lundberg (1984). Low λ should produce expansive female ranges and frequent polyandry. The simulation's answer is in [results.md](results.md#3-cost-of-information).

---

## 5. Decisions

Each round an individual makes two decisions: how much to search (search_share) and how to split the rest across nests (raising_share).

### 5.1 Search share: social learning as Bayesian updating

**Design rationale — from impossible to achievable.** Directly modeling how individuals optimally decide search_share is an impossible task—it requires comparing the cross-period potential payoff of exploring new nests with the direct payoff of staying at the current nest, and estimating the delayed value of information: a dynamic programming problem beyond current cognitive science understanding. Since we as modelers cannot explicitly solve this optimization, birds are even less likely to possess such hyper-rationality.

However, birds **do engage in social learning**—they observe neighbor strategies and payoffs, imitating successful behaviors (Birkhead 1981). This real mechanism is isomorphic with the structure of a **Bayesian update**: neighbor strategies are the evidence, the individual's own current strategy is the prior, and the posterior is next round's strategy. Update intensity increases with neighbor advantage and decreases with accumulated experience, without additional parameters.

**As implemented.** The belief about the best search_share is a Beta distribution, with the bird's own starting share as the prior. Each round, a bird observes the (search_share, fitness) pairs of same-sex neighbours within the neighbourhood radius, itself included, and adds the weighted search shares to the Beta parameters:

$$
\alpha' = \alpha + \sum_j w_j s_j, \qquad \beta' = \beta + \sum_j w_j (1 - s_j), \qquad w_j \propto e^{\gamma z_j}
$$

where $s_j$ is neighbour $j$'s search_share and $z_j$ its fitness standardised within the neighbourhood, so neighbours doing better than average count for more. $\gamma$ (`imitation_strength`, default 2) sets how strongly; 0 means copying the plain average. Next round's search_share is the posterior mean $\alpha'/(\alpha'+\beta')$ plus a little noise (sd 0.05), bounded to [0.05, 0.95]; the noise keeps variation for learning to act on.

Two choices refine the plain update. Weights use standardised fitness, because with raw fitness, differences in habitat swamp differences in strategy and learning barely moves. And pseudo-counts $\alpha+\beta$ are capped at 10, so old evidence fades instead of freezing the belief.

### 5.2 Raising share: natural selection as an implicit optimiser

Given search share $s$ and a belief $\hat{o}_k$ about how much everyone else invests in nest $k$, the individual solves

$$
\max_{\{r_k\}} \sum_{k} \mathcal{F}(r_k + \hat{o}_k, \mathbf{p}_k) \quad \text{s.t.} \quad \sum_k r_k = 1 - s,\; r_k \ge 0
$$

**Design rationale.** We assume individuals can solve this problem through marginal utility equalisation. The biological justification is **natural selection programming**—the evolutionary process itself performs gradient descent in strategy space over millions of years, and retained decision rules approximate optimal response functions. Individuals need not differentiate in their brains; their behavioral patterns are already encoded as heuristics that are "approximately optimal given beliefs".

This assumption is admittedly Panglossian. It avoids compounding errors by overlaying a second layer of behavioral-rule approximation on an already approximated utility function. It also makes the model **interpretable**: one can argue that "given the belief, this strategy is the optimal response", which is the minimum rationality requirement of game theory.

**As implemented — greedy marginal allocation.** The budget $B = 1 - s$ is split into $N$ equal increments ($N$ = `ALLOCATION_STEPS`, default 20). Each increment goes to the nest with the highest numerical marginal utility

$$
\text{MU}_k(r_k) = \frac{\mathcal{F}(r_k + \hat{o}_k + \Delta) - \mathcal{F}(r_k + \hat{o}_k)}{\Delta}
$$

Numerical differentiation avoids assuming the fitness function is differentiable. Because a nest's payoff can start flat (a travel overhead, or the low end of the S-curve), the marginal utility also looks ahead: it is the best average return over the next $j$ increments, for any $j$ up to the remaining budget. A plain one-step rule would never start investing in such a nest.

For a male, nest $k$'s payoff is his paternity share times its expected fledglings (§7), with $\hat{o}_k$ split into everyone else's care and other males' care. For a female, it is the nest's expected fledglings.

**Site fidelity.** Birds do not relocate all at once: each round an individual moves half-way (`adjustment_rate` = 0.5) from last round's raising shares toward the new best response. Without this, all males would answer the same out-of-date beliefs together and stampede between nests.

---

## 6. Scheduling: shuffled order and population-level beliefs

The fundamental challenge in modeling strategic interactions among mating animals is the intractable recursion of predicting others' responses—Player A's optimal move depends on Player B's anticipated reaction, which depends on A's reaction to B's reaction, and so on. Such higher-order reasoning is computationally prohibitive and biologically implausible.

We resolve this with a **sequential decision framework**: within each round, all actions are randomly shuffled. The shuffling is not merely a computational convenience but a representation of natural asynchrony—birds cannot synchronize reproductive decisions nor observe real-time updates from all conspecifics.

In the code the order matters through depletion: a nest's foraging range can overlap a neighbour's, and whoever forages first takes the shared cells.

The key point is that **agents cannot know their position in the queue**. Rather than forecasting the contingent moves of specific rivals—futile when any neighbor may have already acted or may yet act—agents form beliefs about **population-level frequencies**. An alpha male does not ask "Will rival A chase the beta?" but "What is the probability that a randomly selected neighbouring male would chase?" This keeps each agent's decision a best response to a belief, rather than a fixed point of mutual best responses.

**One round:**

1. Every agent decides its search_share and raising_share vector from the current snapshot and its beliefs. Decisions are cached.
2. All (agent, nest) actions are shuffled.
3. Actions run in that order: **search** tries to learn reachable nests' composition; **raise** forages for a nest.
4. Payoffs are paid, beliefs about observed nests are updated, search shares are learned from neighbours, and resources regenerate.

---

## 7. Payoffs: from energy to fledglings

**Step 0 — travel.** Care has to reach the nest. A bird's raising share $r_k$ for nest $k$ arrives as

$$
c_k = \max\left(0,\; r_k - \tau \cdot \frac{d_k}{D}\right)
$$

where $d_k$ is the distance from home, $D$ the neighbourhood radius and $\tau$ the travel cost (0.2). Each extra nest therefore costs a fixed overhead, so spreading thinly over many nests wastes budget. Females live at their nest and pay nothing.

**Step 1 — resource extraction.** A nest's foraging range is a disc whose radius grows with the total care $E_k$ it receives, $T\sqrt{E_k}$, so its area is proportional to care ($T$ = 6 cells). Each delivered unit of care extends the disc by a ring and takes a fraction ρ (0.5) of every cell in that ring. Taken resources leave the grid, so overlapping ranges compete. When deciding, a bird expects $\hat{R}_k(E) = \rho\, q_k\, \pi T^2 E$ from the habitat quality $q_k$ around the nest; it cannot foresee depletion by neighbours.

**Step 2 — logistic conversion.** A nest's total resources $R_k$ map to expected surviving fledglings:

$$
\text{fledglings}_k = \frac{K}{1 + e^{-r (R_k - R_0)}}
$$

$K$ (5) is the maximum number of fledglings, $r$ (0.1) the conversion efficiency, and $R_0$ (40) the resources that give half of $K$. In average habitat at the default resource level, a female alone (about three quarters of her budget) raises about 0.7 fledglings, and her nest needs roughly 0.6 more units of care from males to pass $K/2$. The S-shape encodes diminishing returns once resources saturate, very low output when investment is low, and a smooth curve for the optimiser (cf. Davies 1986).

**Step 3 — payoff allocation.**

$$
\text{payoff}_{\text{female}} = \sum_{k \in \text{her nests}} \text{fledglings}_k
$$

$$
\text{payoff}_{\text{male}} = \sum_k \frac{c_{\text{male},k}}{\sum_{m \in \text{males of } k} c_{m,k}} \times \text{fledglings}_k
$$

**Key simplifying assumption:** paternity among a nest's males is allocated in proportion to their delivered care. In dunnocks, males do adjust care to their mating access (Davies et al. 1992), but care and paternity are not identical; this assumption is the one most in need of defence. An egg-laying cost for females is part of the design but not yet in the code.

---

## 8. Parameters

All parameters are fields of `Config` in `config/config.py`. Main defaults:

| Parameter | Meaning | Default |
|---|---|---|
| `grid_size`, `patch_size` | World side; habitat patch side (cells) | 200, 10 |
| `resource_level` | Mean resource per cell | 0.5 |
| `aggregation_level` | Patch inequality (0 = even) | 0.3 |
| `n_females` / `n_males` | Population | 30 / 30 |
| `search_efficiency` | λ in the search formula | 1.0 |
| `neighbourhood_radius` | D: reach for nests and for social learning (cells) | 50 |
| `min_search_share`, `max_search_share` | Bounds on search_share | 0.05, 0.95 |
| `territory_radius` | T: foraging radius at total care 1 (cells) | 6 |
| `extraction_rate` | ρ | 0.5 |
| `travel_cost` | τ: share lost per visit to a nest at distance D | 0.2 |
| `max_fledglings`, `fledgling_midpoint`, `fledgling_steepness` | K, R₀, r | 5, 40, 0.1 |
| `allocation_steps` | Increments in the greedy allocation | 20 |
| `adjustment_rate` | Site fidelity: step toward best response | 0.5 |
| `imitation_strength`, `learning_memory`, `learning_noise` | Social learning | 2, 10, 0.05 |
| `care_threshold` | Care counted as a partnership in the statistics | 0.1 |
| `rounds`, `seed` | Run length; random seed | 60, 42 |

## 9. References

- Birkhead, T. R. (1981). Territory establishment and social learning in birds.
- Bishton, G. (1986). Spatial distribution of individuals around resource points.
- Davies, N. B. & Lundberg, A. (1984). Food distribution and a variable mating system in the dunnock, *Prunella modularis*. *Journal of Animal Ecology*, 53, 895–912.
- Davies, N. B. (1986). Reproductive success of dunnocks in a variable mating system. *Journal of Animal Ecology*, 55.
- Davies, N. B., Hatchwell, B. J., Robson, T. & Burke, T. (1992). Paternity and parental effort in dunnocks, *Prunella modularis*. *Animal Behaviour*, 43, 729–745.

*Full citations for Birkhead (1981) and Bishton (1986) to be completed.*
