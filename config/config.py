"""All model parameters in one place.

Every run is described by one immutable `Config`. Experiments create variants
with `dataclasses.replace(DEFAULT, resource_level=0.8)` instead of editing
module constants, so many configurations can run in the same process.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # --- Run -------------------------------------------------------------
    seed: int = 42
    rounds: int = 60                  # breeding rounds per run

    # --- World (see docs/model.md §3) -------------------------------------
    grid_size: int = 200              # world is grid_size x grid_size cells
    resource_level: float = 0.5       # mean resource per cell (abundance)
    aggregation_level: float = 0.3    # 0 = even habitat, ->1 = few rich patches
    patch_size: int = 10              # side length of one habitat patch, in cells

    # --- Population --------------------------------------------------------
    n_females: int = 30
    n_males: int = 30
    settle_radius: int = 10           # females place their nest on the best cell this close

    # --- Information and search (§4) --------------------------------------
    search_efficiency: float = 1.0    # lambda: higher = cheaper information
    neighbourhood_radius: float = 50.0  # nests a bird can reach; peers it learns from
    min_search_share: float = 0.05
    max_search_share: float = 0.95

    # --- Raising and resources (§7) ---------------------------------------
    territory_radius: float = 6.0     # foraging radius of a nest with total effort 1
    max_nest_effort: float = 4.0      # range stops growing beyond this total effort
    extraction_rate: float = 0.5      # rho: fraction of a cell taken when foraged
    travel_cost: float = 0.2          # share lost per visit to a nest one neighbourhood_radius away

    # --- Fledgling curve ---------------------------------------------------
    max_fledglings: float = 5.0       # K
    fledgling_midpoint: float = 40.0  # R0: resources giving K/2 fledglings
    fledgling_steepness: float = 0.1  # r

    # --- Decisions (§5) ----------------------------------------------------
    allocation_steps: int = 20        # increments in the greedy raising allocation
    marginal_delta: float = 0.01      # step for numerical marginal utility
    adjustment_rate: float = 0.5      # fraction of the way to the best response per round
    learning_memory: float = 10.0     # cap on Beta pseudo-counts (older evidence fades)
    learning_noise: float = 0.05      # sd of noise when an individual adopts a search share
    imitation_strength: float = 2.0   # how strongly better-off neighbours are favoured (0 = copy the average)

    # --- Classification ----------------------------------------------------
    care_threshold: float = 0.1       # raising share counted as "caring for" a nest


DEFAULT = Config()
