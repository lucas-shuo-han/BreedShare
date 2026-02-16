# strategies/belief_system.py
from typing import Dict, Any
from collections import defaultdict
import numpy as np
from config.config import (
    SEARCH_BELIEF_PRIOR_ALPHA,
    SEARCH_BELIEF_PRIOR_BETA,
    SEARCH_BELIEF_INITIAL_MEAN,
    RAISING_BELIEF_INITIAL_MEAN
)


class BeliefSystem:
    """
    Belief system that implements Bayesian updating for agent decision-making.
    
    Two main functions:
    1. Search-Share decision support: Updates beliefs about optimal search_share based on observed peers
    2. Raising-Share behavior prediction: Predicts others' raising_share contributions to nests
    
    Both updates are stored and normalized independently within the system.
    Simplified version: Only tracks mean values (no variance) for risk-neutral agents.
    """
    
    def __init__(self):
        # Search share belief data
        self.search_beliefs: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            "observations": [],  # List of (search_share, fitness) tuples
            "posterior_mean": SEARCH_BELIEF_INITIAL_MEAN,  # Initial posterior mean from config
        })
        
        # Raising share belief data
        self.raising_beliefs: Dict[int, Dict[int, Dict[str, Any]]] = defaultdict(lambda: defaultdict(lambda: {
            "observations": [],  # List of (agent_id, raising_share) tuples
            "expected_total_investment": RAISING_BELIEF_INITIAL_MEAN,  # Expected total investment from all others
        }))
    
    def submit_search_observation(self, agent_id: int, observed_agent_id: int, 
                                 search_share: float, fitness: float) -> None:
        """
        Submit an observation of a peer's search_share and fitness for social learning.
        
        Args:
            agent_id: The observing agent's ID
            observed_agent_id: The observed agent's ID
            search_share: The observed agent's search_share
            fitness: The observed agent's fitness
        """
        self.search_beliefs[agent_id]["observations"].append((search_share, fitness))
    
    def submit_raising_observation(self, agent_id: int, nest_id: int, 
                                  observed_agent_id: int, raising_share: float, fitness: float) -> None:
        """
        Submit an observation of a peer's raising_share contribution to a nest.
        
        Args:
            agent_id: The observing agent's ID
            nest_id: The nest ID
            observed_agent_id: The observed agent's ID
            raising_share: The observed agent's raising_share for the nest
            fitness: The observed agent's fitness (for fitness-weighted updates)
        """
        self.raising_beliefs[agent_id][nest_id]["observations"].append((observed_agent_id, raising_share, fitness))
    
    def update_search_beliefs(self, agent_id: int) -> None:
        """
        Perform Bayesian update on search_share beliefs based on collected observations.
        Implements true Bayesian updating using fitness-weighted likelihood.
        
        Args:
            agent_id: The agent whose beliefs to update
        """
        beliefs = self.search_beliefs[agent_id]
        observations = beliefs["observations"]
        
        if not observations:
            # No new observations, keep current beliefs
            return
        
        # Step 1: Extract search_shares and fitness values from observations
        search_shares = np.array([obs[0] for obs in observations])
        fitnesses = np.array([obs[1] for obs in observations])
        
        # Step 2: Calculate weights based on fitness (high fitness = higher weight)
        total_fitness = np.sum(fitnesses)
        if total_fitness > 0:
            weights = fitnesses / total_fitness
        else:
            # If no fitness difference, use equal weights
            weights = np.ones(len(fitnesses)) / len(fitnesses)
        
        # Step 3: Implement true Bayesian update using Beta-Binomial conjugate prior
        # Convert posterior mean to alpha and beta parameters
        prior_mean = beliefs["posterior_mean"]
        prior_variance = 0.01  # Assume small variance for simplicity
        prior_alpha = prior_mean * (prior_mean * (1 - prior_mean) / prior_variance - 1)
        prior_beta = (1 - prior_mean) * (prior_mean * (1 - prior_mean) / prior_variance - 1)
        
        # Ensure alpha and beta are positive
        prior_alpha = max(prior_alpha, SEARCH_BELIEF_PRIOR_ALPHA)
        prior_beta = max(prior_beta, SEARCH_BELIEF_PRIOR_BETA)
        
        # Update using weighted observations
        weighted_alpha_update = np.sum(weights * search_shares)
        weighted_beta_update = np.sum(weights * (1 - search_shares))
        
        posterior_alpha = prior_alpha + weighted_alpha_update
        posterior_beta = prior_beta + weighted_beta_update
        
        # Calculate new posterior mean
        posterior_mean = posterior_alpha / (posterior_alpha + posterior_beta)
        
        # Step 4: Update beliefs
        beliefs["posterior_mean"] = posterior_mean
        
        # Clear observations for next round
        beliefs["observations"] = []
    
    def update_raising_beliefs(self, agent_id: int) -> None:
        """
        Perform Bayesian update on raising_share beliefs based on collected observations.
        Implements proper Bayesian updating with fitness weights and calculates total expected investment.
        
        Args:
            agent_id: The agent whose beliefs to update
        """
        agent_raising_beliefs = self.raising_beliefs[agent_id]
        
        for nest_id, beliefs in agent_raising_beliefs.items(): # type: ignore
            observations = beliefs["observations"]
            
            if not observations:
                continue
            
            # Step 1: Extract raising shares and fitness values
            raising_shares = np.array([obs[1] for obs in observations])
            fitnesses = np.array([obs[2] for obs in observations])
            
            # Step 2: Calculate weights based on fitness (high fitness = higher weight)
            total_fitness = np.sum(fitnesses)
            if total_fitness > 0:
                weights = fitnesses / total_fitness
            else:
                # If no fitness difference, use equal weights
                weights = np.ones(len(fitnesses)) / len(fitnesses)
            
            # Step 3: Calculate total observed investment weighted by fitness
            weighted_observed_investment = np.sum(weights * raising_shares)
            
            # Step 4: Apply Bayesian update
            # Use previous expected total as prior
            prior_total = beliefs["expected_total_investment"]
            
            # Weight by number of observations (more observations = more weight on new data)
            n_obs = len(observations)
            expected_total_investment = (prior_total + n_obs * weighted_observed_investment) / (1 + n_obs)
            
            # Step 5: Update beliefs with expected total investment
            beliefs["expected_total_investment"] = expected_total_investment
            
            # Clear observations for next round
            beliefs["observations"] = []
    
    def get_search_belief(self, agent_id: int) -> float:
        """
        Get normalized belief for search_share (only mean for risk-neutral agents).
        
        Args:
            agent_id: The agent whose beliefs to retrieve
            
        Returns:
            Posterior mean as a float value
        """
        beliefs = self.search_beliefs[agent_id]
        return beliefs["posterior_mean"]
    
    def get_raising_belief(self, agent_id: int, nest_id: int) -> float:
        """
        Get normalized belief for raising_share for a specific nest.
        Returns the expected total investment from other individuals to nest k.
        
        Args:
            agent_id: The agent whose beliefs to retrieve
            nest_id: The nest ID
            
        Returns:
            Expected total investment from other individuals as a float value
        """
        beliefs = self.raising_beliefs[agent_id][nest_id]
        return beliefs["expected_total_investment"]
    
    def get_belief(self, agent_id: int, behavior_class: str, **kwargs: Any) -> float:
        """
        Unified interface to get normalized belief for agent behavior (only mean for risk-neutral agents).
        
        Args:
            agent_id: The agent whose beliefs to retrieve
            behavior_class: Type of behavior to get beliefs for ('search' or 'raising')
            **kwargs: Additional parameters (nest_id for raising behavior)
            
        Returns:
            Posterior mean as a float value
            
        Raises:
            ValueError: If behavior_class is not 'search' or 'raising'
        """
        if behavior_class == 'search':
            return self.get_search_belief(agent_id)
        elif behavior_class == 'raising':
            nest_id = kwargs.get('nest_id')
            if nest_id is None:
                raise ValueError("nest_id is required for raising behavior beliefs")
            return self.get_raising_belief(agent_id, nest_id)
        else:
            raise ValueError(f"Invalid behavior_class: {behavior_class}. Must be 'search' or 'raising'")
    
    def update_all_beliefs(self) -> None:
        """
        Update beliefs for all agents. Called at the end of each round.
        """
        # Update search beliefs for all agents
        for agent_id in self.search_beliefs:
            self.update_search_beliefs(agent_id)
        
        # Update raising beliefs for all agents
        for agent_id in self.raising_beliefs:
            self.update_raising_beliefs(agent_id)
