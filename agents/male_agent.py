# agents/male_agent.py
from typing import Tuple, Dict, Optional, Set
from core.base_agent import BaseAgent

class MaleAgent(BaseAgent):
    """
    Male bird agent with id, position and nest_roles.
    Encapsulates state only - all decision logic is in MaleStrategy.
    Can be queried from outside
    """
    
    def __init__(
            self,
            id: int,
            position: Tuple[int, int],
            nest_roles: Optional[Dict[int, str]] = None
    ):
        """
        Initialize male agent.
        
        Args:
            id: Unique integer identifier
            position: Current (x, y) coordinates
            nest_roles: Dict mapping nest_id to role ("alpha"/"beta").
                       None or empty dict indicates unpaired/roaming status.
                       Keys with role "none" should be omitted to save memory.
        """
        super().__init__(id, position)
        self._nest_roles = {k: v for k, v in (nest_roles or {}).items() 
                   if v in ["alpha", "beta"]}

    @property
    def nest_roles(self) -> Dict[int, str]:
        """Read-only access to nest roles."""
        return self._nest_roles.copy()  # Return copy to prevent external mutation
    
    @property
    def nest_ids(self) -> Set[int]:
        """Return set of nest IDs where male currently provides raising_share."""
        return set(self._nest_roles.keys())
    
    def get_nest_role(self, nest_id: int) -> Optional[str]:
        """
        Get role of agent in specified nest.
        
        Args:
            nest_id: ID of nest to query
            
        Returns:
            Role string ("alpha"/"beta") if agent is paired, else None
        """
        return self._nest_roles.get(nest_id)
    
    def is_assigned(self) -> bool:
        """Check if male is currently assigned to any nest."""
        return len(self._nest_roles) > 0

    def assign_to_nest(self, nest_id: int, role: str) -> None:
        """
        Assign male to a nest with specified role.
        
        Args:
            nest_id: Unique identifier of the nest (represents breeding unit).
                     One female can have multiple nests (replacement clutches),
                     but one nest corresponds to exactly one female.
            role: "alpha" (primary paternity) or "beta" (subordinate/auxiliary paternity).
                  Should not be "none" - omit key instead.
        
        NOTE: Strategy layer must also update female's male_count for consistency.
              Roles are refreshed each time step based on spatial overlap,
              conflict outcomes, and female acceptance.
        """
        if role not in ["alpha", "beta"]:
            raise ValueError(f"Role must be 'alpha' or 'beta', got '{role}'")
        
        self._nest_roles[nest_id] = role
        
    def unassign_from_nest(self, nest_id: int) -> None:
        """
        Remove male from specified nest.
        
        NOTE: Strategy layer must also update female's male_count for consistency.
        """
        self._nest_roles.pop(nest_id, None)

    def unassign_from_all_nests(self) -> None:
        """Remove from all nests when the male becomes unpaired."""
        self._nest_roles.clear()

    def step(self) -> None:
        """
        Execute one simulation step.
        
        NOTE: Strategy layer will handle movement and mating decisions.
              This method is intentionally empty - behavior is delegated.
        """
        pass
