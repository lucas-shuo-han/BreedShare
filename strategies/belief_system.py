"""What each bird believes (docs/model.md §5).

* Search belief: a Beta distribution over the best search_share, updated by
  fitness-weighted social learning from same-sex neighbours.
* Nest beliefs: for each nest, how much everyone else (and every other male)
  invests there. Learned only by observation — being at the nest, or a
  successful search. Unobserved nests fall back to the population average.
"""
from typing import Dict, List, Tuple

import numpy as np

from agents.nest import Nest
from config.config import Config


class BeliefSystem:
    def __init__(self, config: Config, rng: np.random.Generator):
        self.config = config
        self.rng = rng
        self._search: Dict[int, List[float]] = {}                       # agent -> [alpha, beta]
        self._nests: Dict[int, Dict[int, Tuple[float, float]]] = {}     # agent -> nest -> (others_total, others_male)
        # Population-level prior for nests never observed (free, coarse information).
        self.prior_total: float = 1.0
        self.prior_male: float = 0.5

    # --- search share ------------------------------------------------------------
    def init_agent(self, agent_id: int, search_share: float) -> None:
        n = self.config.learning_memory / 2
        self._search[agent_id] = [search_share * n, (1 - search_share) * n]
        self._nests.setdefault(agent_id, {})

    def search_mean(self, agent_id: int) -> float:
        a, b = self._search[agent_id]
        return a / (a + b)

    def learn_search(self, agent_id: int, peers: List[Tuple[float, float]]) -> None:
        """alpha += sum w_j s_j, beta += sum w_j (1 - s_j).
        Weights favour neighbours doing better than average:
            w_j proportional to exp(imitation_strength * z_j),
        where z_j is j's fitness standardised within the neighbourhood.
        Pseudo-counts are capped at `learning_memory`, so old evidence slowly fades."""
        if not peers:
            return
        s = np.array([p[0] for p in peers])
        f = np.array([p[1] for p in peers])
        sd = f.std()
        z = (f - f.mean()) / sd if sd > 1e-12 else np.zeros(len(f))
        w = np.exp(self.config.imitation_strength * z)
        w = w / w.sum()
        belief = self._search[agent_id]
        belief[0] += float(np.sum(w * s))
        belief[1] += float(np.sum(w * (1 - s)))
        total = belief[0] + belief[1]
        if total > self.config.learning_memory:
            scale = self.config.learning_memory / total
            belief[0] *= scale
            belief[1] *= scale

    def sample_search_share(self, agent_id: int) -> float:
        """The share actually used this round: the posterior mean plus a little noise."""
        c = self.config
        s = self.search_mean(agent_id) + self.rng.normal(0.0, c.learning_noise)
        return float(np.clip(s, c.min_search_share, c.max_search_share))

    # --- other birds' investment in a nest -------------------------------------------
    def observe_nest(self, agent_id: int, nest: Nest) -> None:
        mine = nest.shares.get(agent_id, 0.0)
        others_total = nest.total_share - mine
        others_male = nest.total_male_share - (mine if agent_id != nest.female_id else 0.0)
        self._nests[agent_id][nest.id] = (others_total, others_male)

    def nest_belief(self, agent_id: int, nest_id: int) -> Tuple[float, float]:
        return self._nests[agent_id].get(nest_id, (self.prior_total, self.prior_male))

    def knows(self, agent_id: int, nest_id: int) -> bool:
        return nest_id in self._nests[agent_id]
