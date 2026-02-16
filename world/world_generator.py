# world/world_generator.py
import numpy as np
from numpy.typing import NDArray

class WorldGenerator:
    """
    WorldGenerator class for generating the world. 500 * 500 gridline with discrete resource level.
    """
    def __init__(self, grid_size: int, resource_level: float, aggregation: float):
        """
        Initialize the WorldGenerator class.
        :param grid_size: grid size for the world, unchanged
        :param resource_level: resource level, between 0 and 1
        :param aggregation: aggregation level, between 0 and 1
        """
        self.grid_size = grid_size
        self.resource_level = resource_level
        self.aggregation = aggregation

        # calculate negative binomial distribution parameters
        self.n = int(max(1.0, 10.0 / self.aggregation)) if self.aggregation > 0 else 100 # to capture the effect of aggregation
        self.p = self.n / (self.n + self.resource_level) # to make sure mean is equal to resource_level

    def generate_resources(self) -> NDArray[np.float32]:
        """
        Generate resources for the world.
        :return: a 2D numpy array of resources
        """
        raw_grid: NDArray[np.int64] = np.random.negative_binomial(
            n=self.n,
            p=self.p,
            size=(self.grid_size, self.grid_size)
        )
        
        normalized_grid: NDArray[np.float32] = (
            raw_grid.astype(np.float32) / np.sum(raw_grid)
        ) * (self.grid_size ** 2)

        return normalized_grid.astype(np.float32)
