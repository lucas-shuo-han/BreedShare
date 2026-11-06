"""Resource landscape.

Resources follow a gamma-Poisson (negative binomial) process:

* A persistent **habitat quality** field is drawn once per run. Each patch of
  `patch_size` x `patch_size` cells gets a gamma-distributed quality with mean 1;
  `aggregation_level` sets how unequal patches are.
* Each round, the **resources** in every cell are drawn fresh as
  Poisson(quality x resource_level), so a cell's daily value is negative
  binomial and neighbouring cells are correlated through their shared patch.
"""
import numpy as np
from numpy.typing import NDArray

from config.config import Config

# Resources are counted in units of 1/RESOURCE_GRAIN so the Poisson draw is not too coarse.
RESOURCE_GRAIN = 10.0


class WorldGenerator:
    def __init__(self, config: Config, rng: np.random.Generator):
        self.config = config
        self.rng = rng

    def generate_habitat(self) -> NDArray[np.float64]:
        """Mean resource per cell, fixed for the whole run."""
        c = self.config
        n_patches = int(np.ceil(c.grid_size / c.patch_size))
        a = min(max(c.aggregation_level, 0.0), 0.99)
        if a == 0.0:
            quality = np.ones((n_patches, n_patches))
        else:
            shape = (1.0 - a) / a  # gamma shape k; smaller k = more aggregated
            quality = self.rng.gamma(shape, 1.0 / shape, size=(n_patches, n_patches))
        habitat = np.kron(quality, np.ones((c.patch_size, c.patch_size)))
        return habitat[: c.grid_size, : c.grid_size] * c.resource_level

    def generate_resources(self, habitat: NDArray[np.float64]) -> NDArray[np.float64]:
        """One round's resources, drawn around the habitat means."""
        counts = self.rng.poisson(habitat * RESOURCE_GRAIN)
        return counts.astype(np.float64) / RESOURCE_GRAIN
