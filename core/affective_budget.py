"""
Affective Budget Law for the GMI Universal Cognition Engine.

Module 16.2: Affective Thermodynamic Pricing

χ-modulated thermodynamic pricing:
Ḃ = -D_phys - μ_I(χ)||O_I||² - μ_L(χ)||O_L||² - μ_E(χ)||O_E||² + G_env

Policies:
- ∂μ_I/∂χ > 0: Imagination expensive under threat
- ∂μ_L/∂χ < 0: Logic cheaper under threat
"""

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np


@dataclass
class AffectiveBudgetLaw:
    """
    χ-modulated thermodynamic budget law.
    
    The mode field χ directly deforms the thermodynamic cost of utilizing
    the epistemic operators.
    
    As χ increases (more threatened):
    - Imagination (O_I) becomes MORE expensive
    - Logic (O_L) becomes CHEAPER
    - Emotion (O_E) becomes MORE expensive
    """
    # Base cost coefficients
    base_mu_imagination: float = 1.0
    base_mu_logic: float = 0.8
    base_mu_emotion: float = 0.5
    
    # Base branch admissibility threshold
    base_lambda_branch: float = 1.0
    
    # χ parameter
    chi: float = 0.5
    
    def __post_init__(self):
        self.chi = np.clip(self.chi, 0.0, 1.0)
    
    @property
    def mu_imagination(self) -> float:
        """
        Imagination cost coefficient.
        
        ∂μ_I/∂χ > 0: Increases with threat
        """
        return self.base_mu_imagination * (1.0 + self.chi * 2.0)
    
    @property
    def mu_logic(self) -> float:
        """
        Logic cost coefficient.
        
        ∂μ_L/∂χ < 0: Decreases with threat
        """
        return self.base_mu_logic * (1.0 - self.chi * 0.5)
    
    @property
    def mu_emotion(self) -> float:
        """
        Emotion/salience cost coefficient.
        
        Increases with threat
        """
        return self.base_mu_emotion * (1.0 + self.chi * 1.5)
    
    @property
    def lambda_branch(self) -> float:
        """
        Branch admissibility threshold.
        
        ∂λ_B/∂χ > 0: Higher threshold under threat
        Requires higher expected ROI to justify branch
        """
        return self.base_lambda_branch * (1.0 + self.chi)
    
    def cost_imagination(self, magnitude: float) -> float:
        """
        Cost of imagination operation.
        
        Args:
            magnitude: Size/complexity of imagination
            
        Returns:
            Cost in budget units
        """
        return self.mu_imagination * (magnitude ** 2)
    
    def cost_logic(self, magnitude: float) -> float:
        """
        Cost of logic/pruning operation.
        
        Args:
            magnitude: Complexity of logic check
            
        Returns:
            Cost in budget units
        """
        return self.mu_logic * (magnitude ** 2)
    
    def cost_emotion(self, magnitude: float) -> float:
        """
        Cost of emotion/salience operation.
        
        Args:
            magnitude: Complexity of emotion processing
            
        Returns:
            Cost in budget units
        """
        return self.mu_emotion * (magnitude ** 2)
    
    def branch_admissible(
        self, 
        expected_gain: float, 
        branch_cost: float
    ) -> bool:
        """
        Check if branch is admissible under current threat level.
        
        Args:
            expected_gain: Γ(B_i)
            branch_cost: Σ(B_i)
            
        Returns:
            True if admissible
        """
        if branch_cost <= 0:
            return expected_gain > 0
        
        # Higher threshold under threat
        return expected_gain >= self.lambda_branch * branch_cost
    
    def max_branches(self, budget: float, min_cost: float = 1.0) -> int:
        """
        Maximum number of branches possible under budget.
        
        Args:
            budget: Available budget
            min_cost: Minimum cost per branch
            
        Returns:
            Maximum branches
        """
        # At least imagination cost
        cost_per = self.cost_imagination(min_cost)
        if cost_per <= 0:
            return float('inf')
        return int(budget / cost_per)
    
    def set_chi(self, chi: float) -> 'AffectiveBudgetLaw':
        """
        Set χ and return self for chaining.
        
        Args:
            chi: New χ value
            
        Returns:
            Self
        """
        self.chi = np.clip(chi, 0.0, 1.0)
        return self
    
    def get_cost_summary(self) -> dict:
        """Get summary of current costs."""
        return {
            'chi': self.chi,
            'mu_imagination': self.mu_imagination,
            'mu_logic': self.mu_logic,
            'mu_emotion': self.mu_emotion,
            'lambda_branch': self.lambda_branch,
            'affective_mode': self._get_mode_name()
        }
    
    def _get_mode_name(self) -> str:
        """Get current affective mode name."""
        if self.chi < 0.2:
            return "safe"
        elif self.chi < 0.4:
            return "flow"
        elif self.chi < 0.6:
            return "neutral"
        elif self.chi < 0.8:
            return "caution"
        else:
            return "defensive"


class AffectiveBudgetCalculator:
    """
    Helper to compute total budget changes with affective modulation.
    """
    
    def __init__(self, chi: float = 0.5):
        self.law = AffectiveBudgetLaw(chi=chi)
    
    def compute_budget_change(
        self,
        physical_cost: float,
        imagination_magnitude: float,
        logic_magnitude: float,
        emotion_magnitude: float,
        external_gain: float = 0.0
    ) -> float:
        """
        Compute total budget change over a cycle.
        
        Ḃ = -D_phys - μ_I||O_I||² - μ_L||O_L||² - μ_E||O_E||² + G_env
        
        Args:
            physical_cost: D_phys
            imagination_magnitude: ||O_I||
            logic_magnitude: ||O_L||
            emotion_magnitude: ||O_E||
            external_gain: G_env
            
        Returns:
            Net budget change
        """
        imagination_cost = self.law.cost_imagination(imagination_magnitude)
        logic_cost = self.law.cost_logic(logic_magnitude)
        emotion_cost = self.law.cost_emotion(emotion_magnitude)
        
        return (
            external_gain 
            - physical_cost 
            - imagination_cost 
            - logic_cost 
            - emotion_cost
        )
    
    def can_afford_branch(
        self,
        budget: float,
        expected_gain: float,
        branch_magnitude: float
    ) -> tuple[bool, float]:
        """
        Check if budget can afford opening a branch.
        
        Args:
            budget: Current budget
            expected_gain: Expected gain from branch
            branch_magnitude: Complexity of branch
            
        Returns:
            (can_afford, cost)
        """
        cost = self.law.cost_imagination(branch_magnitude)
        
        if budget < cost:
            return False, cost
        
        # Check admissibility
        admissible = self.law.branch_admissible(expected_gain, cost)
        
        return admissible, cost
