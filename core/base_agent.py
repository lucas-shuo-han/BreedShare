# core/base_agent.py
from abc import ABC, abstractmethod
from typing import Tuple

# TODO: search should reveal more information about every agent in the nest to do Bayesian updating


class BaseAgent(ABC):
    """
    Abstract base class for all bird agents in the mating system simulation.
    Defines the minimal interface that all agents must implement.
    """

    def __init__(self, id: int, position: Tuple[int, int]):
        """
        Initialize base agent with immutable ID and mutable position.
        
        Args:
            id: Unique integer identifier for this bird
            position: Current (x, y) grid coordinates as a tuple
        """
        self._id = id
        self._position = position
        self.search_share: float = 1  # agent can only choose to search other nests or feed nestlings
    
    @abstractmethod
    def step(self) -> None:
        """Execute one simulation step (to be implemented by subclasses)."""
        pass

    @property
    def id(self) -> int:
        """Return the unique identifier for this agent."""
        return self._id
    
    @property
    def position(self) -> Tuple[int, int]:
        """Return the current (x, y) grid coordinates of this agent."""
        return self._position
    
    def move_to(self, new_position: Tuple[int, int]) -> None:
        """
        Update the agent's position.
        
        Args:
            new_position: New (x, y) grid coordinates
        """
        self._position = new_position

