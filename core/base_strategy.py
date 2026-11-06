"""Shared decision machinery: greedy marginal-utility allocation (docs/model.md §5.2)."""
from typing import Callable, Dict, List

from config.config import Config

# payoff(my_share, nest_id) -> expected payoff from that nest
PayoffFn = Callable[[float, int], float]


def allocate_raising(nests: List[int], budget: float, payoff: PayoffFn, c: Config) -> Dict[int, float]:
    """Split `budget` across `nests` in `allocation_steps` equal increments.
    Each increment goes to the nest with the highest marginal utility
        MU_k = [F(r_k + delta) - F(r_k)] / delta
    at its current allocation. This approximates equalising marginal returns
    without assuming F is differentiable."""
    shares = {k: 0.0 for k in nests}
    if not nests or budget <= 0:
        return shares
    step = budget / c.allocation_steps
    d = c.marginal_delta
    for n_left in range(c.allocation_steps, 0, -1):
        def mu(k: int) -> float:
            # Local slope, plus the best average slope over the next j steps.
            # The look-ahead stops the optimiser ignoring a nest whose payoff
            # starts flat (travel overhead, or the low end of the S-curve).
            base = payoff(shares[k], k)
            best = (payoff(shares[k] + d, k) - base) / d
            for j in range(1, n_left + 1):
                best = max(best, (payoff(shares[k] + j * step, k) - base) / (j * step))
            return best
        best_nest = max(nests, key=mu)
        shares[best_nest] += step
    return shares


def blend(old: Dict[int, float], new: Dict[int, float], rate: float, budget: float) -> Dict[int, float]:
    """Move part of the way from last round's allocation to the new best response,
    then rescale so the raising shares sum exactly to `budget`."""
    keys = set(old) | set(new)
    mixed = {k: (1 - rate) * old.get(k, 0.0) + rate * new.get(k, 0.0) for k in keys}
    total = sum(mixed.values())
    if total <= 0:
        return {k: budget / len(new) for k in new} if new else {}
    return {k: v * budget / total for k, v in mixed.items() if v > 1e-9}
