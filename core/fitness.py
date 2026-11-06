"""From resources to fledglings, and from fledglings to payoffs (docs/model.md §7)."""
import math

from agents.nest import Nest
from config.config import Config


def fledglings(resources: float, c: Config) -> float:
    """Logistic curve: K / (1 + exp(-r (R - R0)))."""
    z = -c.fledgling_steepness * (resources - c.fledgling_midpoint)
    return c.max_fledglings / (1.0 + math.exp(min(z, 700.0)))


def expected_resources(total_effort: float, quality: float, c: Config) -> float:
    """What a bird expects a nest to gather with this total effort: rho x quality x area.
    Ignores depletion by neighbours, which the bird cannot foresee."""
    effort = min(max(total_effort, 0.0), c.max_nest_effort)
    area = math.pi * c.territory_radius ** 2 * effort
    return c.extraction_rate * quality * area


def delivered_care(share: float, distance: float, c: Config) -> float:
    """Raising share that actually reaches a nest after the trip from home.
    Each nest costs `travel_cost` per neighbourhood_radius of distance, so
    caring for many or far-away nests wastes budget."""
    return max(0.0, share - c.travel_cost * distance / c.neighbourhood_radius)


# --- realised payoffs ---------------------------------------------------------
def female_payoff(nest: Nest, c: Config) -> float:
    return fledglings(nest.resources, c)


def paternity_share(nest: Nest, male_id: int) -> float:
    """Key simplifying assumption: paternity follows care among the nest's males."""
    total = nest.total_male_share
    return nest.shares.get(male_id, 0.0) / total if total > 0 else 0.0


def male_payoff(nest: Nest, male_id: int, c: Config) -> float:
    return paternity_share(nest, male_id) * fledglings(nest.resources, c)


# --- counterfactual payoffs used when deciding ----------------------------------
def female_counterfactual(my_share: float, others_total: float, others_male: float,
                          quality: float, c: Config) -> float:
    return fledglings(expected_resources(my_share + others_total, quality, c), c)


def male_counterfactual(my_share: float, others_total: float, others_male: float,
                        quality: float, c: Config) -> float:
    if my_share <= 0.0:
        return 0.0
    paternity = my_share / (my_share + others_male)
    return paternity * fledglings(expected_resources(my_share + others_total, quality, c), c)
