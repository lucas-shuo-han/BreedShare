"""Run one simulation and return its per-round summaries."""
from typing import Dict, List

import numpy as np

from config.config import Config
from initializer.bootstrap import bootstrap
from simulation.game_loop import GameLoop
from simulation.metrics import CATEGORIES


def run(config: Config) -> List[Dict[str, float]]:
    return GameLoop(bootstrap(config)).run(config.rounds)


def steady_state(rows: List[Dict[str, float]], last: int = 20) -> Dict[str, float]:
    """Average of the last `last` rounds, once the population has settled."""
    tail = rows[-last:]
    return {k: float(np.mean([r[k] for r in tail])) for k in tail[0] if k != "round"}


__all__ = ["run", "steady_state", "CATEGORIES"]
