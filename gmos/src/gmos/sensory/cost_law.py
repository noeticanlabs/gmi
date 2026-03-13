"""
Observation Cost Law for Dual-Use Sensory Substrate.

Per spec §9: Observation must cost something, otherwise the organism
can Zeno-poll the universe.

Mathematical definition:
    Σ_obs(s) = α_obs + β_obs * Sal(s) + γ_obs * BW(s)

With constraint: Σ_obs(s) > 0 for every non-null percept

Budget enforcement (within one macro-step):
    ∑ Σ_obs(s_j) ≤ b_t

This implements the "no free polling" principle in hard form.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


@dataclass
class CostCoefficients:
    """
    Coefficients for the observation cost law.
    
    Per spec §9:
    - α_obs: Base observation cost (must be > 0)
    - β_obs: Salience scaling factor
    - γ_obs: Bandwidth cost factor
    """
    alpha: float = 0.001   # Base cost per observation
    beta: float = 0.002    # Salience weight
    gamma: float = 0.001   # Bandwidth weight
    
    def __post_init__(self):
        """Ensure base cost is positive."""
        if self.alpha <= 0:
            raise ValueError(f"Base cost α must be positive, got {self.alpha}")


class ObservationCostLaw:
    """
    Implements the observation cost law per spec §9.
    
    The cost law ensures:
    1. Every observation costs something (Σ > 0)
    2. Salience influences cost (more salient = more expensive)
    3. Bandwidth influences cost (larger percepts = more expensive)
    4. Budget enforcement prevents infinite polling
    
    Mathematical form:
        Σ_obs(s) = α + β * Sal(s) + γ * BW(s)
    
    Usage:
        cost_law = ObservationCostLaw()
        cost = cost_law.compute_cost(percept)
        is_valid = cost_law.check_budget(budget, [p1, p2, p3])
    """
    
    def __init__(
        self,
        coefficients: Optional[CostCoefficients] = None,
        min_cost: float = 1e-6
    ):
        """
        Initialize the cost law.
        
        Args:
            coefficients: Cost law coefficients (uses defaults if None)
            min_cost: Minimum allowed cost (for numerical stability)
        """
        self.coefficients = coefficients or CostCoefficients()
        self.min_cost = min_cost
    
    def compute_cost(
        self,
        salience: float,
        bandwidth: float = 0.0,
        base_override: Optional[float] = None
    ) -> float:
        """
        Compute observation cost for a single percept.
        
        Formula: Σ_obs(s) = α + β * Sal(s) + γ * BW(s)
        
        Args:
            salience: Salience score [0, 1]
            bandwidth: Percept bandwidth/size (e.g., token count)
            base_override: Optional base cost override
            
        Returns:
            Observation cost (always > 0)
        """
        alpha = base_override if base_override is not None else self.coefficients.alpha
        beta = self.coefficients.beta
        gamma = self.coefficients.gamma
        
        cost = alpha + beta * salience + gamma * bandwidth
        
        # Ensure positive cost (per spec constraint)
        return max(cost, self.min_cost)
    
    def compute_costs(
        self,
        percepts: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Compute costs for multiple percepts.
        
        Args:
            percepts: List of percept dictionaries with 'salience' and optional 'bandwidth'
            
        Returns:
            List of observation costs
        """
        costs = []
        for percept in percepts:
            salience = percept.get("salience", 0.0)
            bandwidth = percept.get("bandwidth", 0.0)
            cost = self.compute_cost(salience, bandwidth)
            costs.append(cost)
        return costs
    
    def check_budget(
        self,
        budget: float,
        percepts: List[Dict[str, Any]],
        reserved_budget: float = 0.0
    ) -> Tuple[bool, float, List[float]]:
        """
        Check if a set of observations fits within budget.
        
        Per spec §9: ∑ Σ_obs(s_j) ≤ b_t
        
        Args:
            budget: Available budget b_t
            percepts: List of percepts to observe
            reserved_budget: Budget already reserved for other operations
            
        Returns:
            (fits_in_budget, total_cost, individual_costs)
        """
        available = budget - reserved_budget
        if available < 0:
            return False, 0.0, []
        
        costs = self.compute_costs(percepts)
        total_cost = sum(costs)
        
        fits = total_cost <= available
        return fits, total_cost, costs
    
    def select_observations(
        self,
        budget: float,
        percepts: List[Dict[str, Any]],
        reserved_budget: float = 0.0
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """
        Greedily select observations that fit within budget.
        
        Selects percepts in order of salience (highest first) until
        budget is exhausted.
        
        Args:
            budget: Available budget
            percepts: Available percepts (must have 'salience' field)
            reserved_budget: Budget already reserved
            
        Returns:
            (selected_percepts, costs)
        """
        available = budget - reserved_budget
        if available <= 0:
            return [], []
        
        # Sort by salience (descending)
        sorted_percepts = sorted(
            percepts,
            key=lambda p: p.get("salience", 0.0),
            reverse=True
        )
        
        selected = []
        costs = []
        total = 0.0
        
        for percept in sorted_percepts:
            cost = self.compute_cost(
                percept.get("salience", 0.0),
                percept.get("bandwidth", 0.0)
            )
            
            if total + cost <= available:
                selected.append(percept)
                costs.append(cost)
                total += cost
            else:
                break
        
        return selected, costs
    
    def compute_marginal_cost(
        self,
        current_total: float,
        new_salience: float,
        new_bandwidth: float = 0.0,
        max_budget: float = 1.0
    ) -> Tuple[float, bool]:
        """
        Compute the marginal cost of adding a new observation.
        
        Args:
            current_total: Current total observation cost
            new_salience: Salience of new percept
            new_bandwidth: Bandwidth of new percept
            max_budget: Maximum allowed budget
            
        Returns:
            (marginal_cost, would_exceed_budget)
        """
        cost = self.compute_cost(new_salience, new_bandwidth)
        would_exceed = (current_total + cost) > max_budget
        return cost, would_exceed
    
    def budget_absorption(
        self,
        budget: float,
        percept: Dict[str, Any]
    ) -> Tuple[float, float]:
        """
        Apply budget absorption rule at boundary.
        
        When budget is zero (b=0), positive spend is blocked.
        This is the global budget absorption rule from RCFA.
        
        Args:
            budget: Current budget (may be 0)
            percept: Percept to observe
            
        Returns:
            (actual_cost, effective_spend)
        """
        # Compute raw cost
        cost = self.compute_cost(
            percept.get("salience", 0.0),
            percept.get("bandwidth", 0.0)
        )
        
        # Apply absorption: if budget is 0, no spend allowed
        if budget <= 0:
            return 0.0, 0.0
        
        # Cannot spend more than available
        effective = min(cost, budget)
        
        return cost, effective


class CostLawValidator:
    """
    Validates cost law properties.
    
    Ensures the cost law satisfies spec requirements:
    1. Σ > 0 for all percepts
    2. Budget enforcement works correctly
    """
    
    def __init__(self, cost_law: ObservationCostLaw):
        self.cost_law = cost_law
    
    def validate_cost_positivity(self) -> Tuple[bool, str]:
        """
        Validate that Σ_obs(s) > 0 for all possible inputs.
        """
        test_cases = [
            (0.0, 0.0),   # Zero salience, zero bandwidth
            (1.0, 0.0),   # Max salience, zero bandwidth
            (0.0, 1.0),   # Zero salience, max bandwidth
            (1.0, 1.0),   # Max salience, max bandwidth
        ]
        
        for salience, bandwidth in test_cases:
            cost = self.cost_law.compute_cost(salience, bandwidth)
            if cost <= 0:
                return False, f"Cost must be positive, got {cost} for salience={salience}, bandwidth={bandwidth}"
        
        return True, "All costs are positive"
    
    def validate_budget_enforcement(
        self,
        budget: float,
        percepts: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Validate that budget enforcement prevents overspending.
        """
        fits, total, _ = self.cost_law.check_budget(budget, percepts)
        
        if not fits and total > budget:
            return False, f"Budget violation: total {total} exceeds budget {budget}"
        
        return True, "Budget enforcement works"
    
    def validate_absorption(
        self,
        budget: float,
        percept: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate that absorption rule blocks spend at b=0.
        """
        _, effective = self.cost_law.budget_absorption(budget, percept)
        
        if budget <= 0 and effective > 0:
            return False, f"Absorption violated: budget={budget}, effective={effective}"
        
        return True, "Absorption rule enforced"


# === Exports ===

__all__ = [
    "CostCoefficients",
    "ObservationCostLaw",
    "CostLawValidator",
]
