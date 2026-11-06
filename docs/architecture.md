# Code Architecture

The code is split into four layers. Each layer only depends on the ones above it in this list.

| Layer | Folder | Responsibility |
|---|---|---|
| World | `world/` | Resource landscape, nests, search and foraging |
| Agents | `agents/`, `core/base_agent.py` | State only: home position, allocation vector, last payoff |
| Strategies | `strategies/`, `core/base_strategy.py` | Decide the allocation; hold beliefs |
| Simulation | `simulation/`, `initializer/` | Build the initial state, run rounds, measure mating systems |

Keeping decisions out of the agent classes means a strategy can be replaced (for example, by a learned rule) by changing one line in `simulation/orchestrator.py`.

All parameters are fields of one frozen `Config` (`config/config.py`). Every function receives the config it should use, so experiments can run many configurations side by side without editing globals.

## Files

```
config/config.py             Config dataclass: every parameter, with its default
main.py                      Run one simulation and print the mating system per round

world/world_generator.py     Gamma-Poisson landscape: persistent habitat + daily resources
world/world_state.py         Nests and birds; search success; foraging with depletion

core/base_agent.py           Allocation vector (search_share + raising_shares), home, fitness
core/base_strategy.py        Greedy marginal-utility allocation; blending with last round
core/fitness.py              Delivered care, expected resources, fledgling curve, payoffs

agents/nest.py               One female's nest: who invested how much, what was gathered
agents/female_agent.py       Female: owns nest(s)
agents/male_agent.py         Male: no nest of his own

strategies/belief_system.py  Beta belief on search share; per-nest beliefs about others' care
strategies/female_strategy.py
strategies/male_strategy.py

initializer/bootstrap.py     Landscape, settling, initial allocations and beliefs
simulation/orchestrator.py   Which strategy each sex uses
simulation/game_loop.py      One round: decide → shuffle → search/raise → payoffs → learn
simulation/metrics.py        Classify each female's mating system; round summary
simulation/run.py            run(config) and steady_state(rows)

experiments/run_experiments.py  All sweeps and figures in docs/results.md
tests/test_model.py             Invariants from docs/model.md
```

## One round in code

`GameLoop.run_round()`:

1. `nest.begin_round()` for every nest; the population-average investment becomes the prior for unobserved nests.
2. Each agent's strategy returns `(search_share, raising_shares)`; `agent.set_allocation` stores it.
3. One `search` action per agent and one `raise` action per (agent, nest) are shuffled with the run's RNG.
4. `raise`: `delivered_care` subtracts the travel cost, `WorldState.forage` takes resources from the nest's next ring of cells, and the nest records the care. `search`: `WorldState.search` decides, nest by nest, whether the agent learns that nest's composition.
5. `nest.end_round()`; payoffs from `core/fitness.py`.
6. Agents update beliefs about the nests they saw, then learn search share from same-sex neighbours.
7. `summarize_round` classifies females; resources regenerate.

## Conventions

- One `numpy.random.Generator` per run, seeded from `Config.seed`; the same config gives the same result.
- `python main.py --log` writes each decision to `breed_share_debug.log`.
- `python -m pytest` runs the tests.
