"""Checks that the code does what docs/model.md says. Run with: python -m pytest"""
import math
import os
import sys
from dataclasses import replace

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.female_agent import FemaleAgent
from agents.male_agent import MaleAgent
from config.config import DEFAULT
from core.base_strategy import allocate_raising, blend
from core.fitness import delivered_care, expected_resources, fledglings, male_counterfactual
from initializer.bootstrap import bootstrap
from simulation.game_loop import GameLoop
from simulation.metrics import classify_females
from simulation.run import run
from strategies.belief_system import BeliefSystem
from world.world_state import WorldState

SMALL = replace(DEFAULT, grid_size=100, n_females=12, n_males=12, rounds=5)


# --- budget constraint --------------------------------------------------------------
def test_every_allocation_sums_to_one():
    sim = bootstrap(SMALL)
    loop = GameLoop(sim)
    for _ in range(5):
        loop.run_round()
        for agent in sim.world.agents.values():
            total = agent.search_share + sum(agent.raising_shares.values())
            assert total == pytest.approx(1.0, abs=1e-9)
            assert all(v >= 0 for v in agent.raising_shares.values())
            assert SMALL.min_search_share <= agent.search_share <= 1.0


def test_blend_keeps_budget():
    out = blend({1: 0.6, 2: 0.2}, {2: 0.5, 3: 0.4}, 0.5, 0.9)
    assert sum(out.values()) == pytest.approx(0.9)


# --- greedy allocation -----------------------------------------------------------------
def test_allocation_spends_whole_budget_and_prefers_better_nest():
    payoff = lambda x, k: (2.0 if k == "rich" else 1.0) * math.sqrt(x)
    shares = allocate_raising(["rich", "poor"], 0.8, payoff, DEFAULT)
    assert sum(shares.values()) == pytest.approx(0.8)
    # Equal marginal returns for 2*sqrt(x) vs sqrt(x) put 4/5 of the budget on "rich".
    assert shares["rich"] == pytest.approx(0.64, abs=0.05)


def test_allocation_handles_travel_overhead():
    # Four identical far nests; each visit loses 0.2 of budget on the way.
    c = replace(DEFAULT, travel_cost=0.2)
    payoff = lambda x, k: male_counterfactual(delivered_care(x, 50.0, c), 0.8, 0.0, 0.5, c)
    shares = allocate_raising([1, 2, 3, 4], 0.8, payoff, c)
    got = sum(payoff(v, k) for k, v in shares.items())
    best_even_split = max(n * payoff(0.8 / n, 0) for n in (1, 2, 3, 4))
    assert got >= 0.97 * best_even_split
    # Spreading over all four would waste the whole budget on travel.
    assert sum(1 for v in shares.values() if v > 0) < 4


# --- payoffs ---------------------------------------------------------------------------
def test_fledgling_curve():
    assert fledglings(DEFAULT.fledgling_midpoint, DEFAULT) == pytest.approx(DEFAULT.max_fledglings / 2)
    values = [fledglings(r, DEFAULT) for r in range(0, 200, 10)]
    assert all(b > a for a, b in zip(values, values[1:]))
    assert values[-1] < DEFAULT.max_fledglings


def test_expected_resources_linear_then_capped():
    a = expected_resources(1.0, 0.5, DEFAULT)
    assert expected_resources(2.0, 0.5, DEFAULT) == pytest.approx(2 * a)
    assert expected_resources(100.0, 0.5, DEFAULT) == expected_resources(DEFAULT.max_nest_effort, 0.5, DEFAULT)


def test_paternity_follows_care():
    c = DEFAULT
    alone = male_counterfactual(0.5, 0.8, 0.0, 0.5, c)
    shared = male_counterfactual(0.5, 1.3, 0.5, 0.5, c)   # same nest effort, one rival of equal care
    assert shared == pytest.approx(0.5 * fledglings(expected_resources(1.8, 0.5, c), c))
    assert alone > 0


# --- world ------------------------------------------------------------------------------
def test_foraging_moves_resources_from_grid_to_nest():
    rng = np.random.default_rng(0)
    world = WorldState(SMALL, rng)
    nest_id = world.create_nest(0, (50, 50))
    before = world.resource_grid.sum()
    got = world.forage(nest_id, 0.7) + world.forage(nest_id, 0.5)
    world.nests[nest_id].effort = 1.2
    assert got > 0
    assert world.resource_grid.sum() == pytest.approx(before - got)


def test_second_forager_on_same_ring_gets_nothing_new():
    rng = np.random.default_rng(0)
    world = WorldState(SMALL, rng)
    k = world.create_nest(0, (50, 50))
    first = world.forage(k, 1.0)
    # Without advancing the nest's effort, the same ring is foraged again from the depleted grid.
    again = world.forage(k, 1.0)
    assert again == pytest.approx(first * (1 - SMALL.extraction_rate), rel=1e-6)


def test_search_probability():
    world = WorldState(SMALL, np.random.default_rng(0))
    assert world.search_success_probability(0.0, 0.1) == 1.0
    near = world.search_success_probability(10.0, 0.2)
    far = world.search_success_probability(40.0, 0.2)
    more = world.search_success_probability(40.0, 0.6)
    assert 0 < far < near < 1 and far < more


def test_resource_level_sets_mean():
    for level in (0.3, 1.2):
        world = WorldState(replace(SMALL, resource_level=level, aggregation_level=0.0), np.random.default_rng(1))
        assert world.resource_grid.mean() == pytest.approx(level, rel=0.02)


def test_aggregation_increases_spread():
    spread = []
    for agg in (0.1, 0.8):
        world = WorldState(replace(DEFAULT, aggregation_level=agg), np.random.default_rng(1))
        spread.append(world.habitat.std() / world.habitat.mean())
    assert spread[1] > spread[0]


# --- learning -----------------------------------------------------------------------------
def test_search_learning_moves_toward_successful_neighbours():
    beliefs = BeliefSystem(DEFAULT, np.random.default_rng(0))
    beliefs.init_agent(0, 0.5)
    for _ in range(30):
        beliefs.learn_search(0, [(0.1, 5.0), (0.9, 1.0), (0.5, 3.0)])
    assert beliefs.search_mean(0) < 0.3


# --- classification --------------------------------------------------------------------------
def _world_with(shares):
    """shares: {nest_id: {male_id: share}}; female i owns nest i."""
    world = WorldState(SMALL, np.random.default_rng(0))
    for k, males in shares.items():
        f = FemaleAgent(100 + k, (10 * k, 10))
        world.add_agent(f)
        f.nest_ids.append(world.create_nest(f.id, f.position))
        world.nests[k].shares = {f.id: 0.9, **males}
    for m in {m for males in shares.values() for m in males}:
        world.add_agent(MaleAgent(m, (0, 0)))
    return world


def test_classification():
    world = _world_with({
        0: {},                       # unmated
        1: {1: 0.8},                 # monogamy
        2: {2: 0.4}, 3: {2: 0.4},    # polygyny (male 2 has two females)
        4: {4: 0.5, 5: 0.4},         # polyandry
        5: {6: 0.5, 7: 0.3}, 6: {7: 0.3},  # polygynandry at 5 (male 7 also cares for 6)
        7: {8: 0.05},                # below threshold: unmated
    })
    got = classify_females(world)
    assert [got[100 + k] for k in range(8)] == [
        "unmated", "monogamy", "polygyny", "polygyny", "polyandry", "polygynandry", "polygyny", "unmated"]


# --- reproducibility -----------------------------------------------------------------------
def test_same_seed_same_result():
    assert run(SMALL) == run(SMALL)
    assert run(SMALL) != run(replace(SMALL, seed=SMALL.seed + 1))
