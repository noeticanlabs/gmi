"""
Thermodynamic Cost Tracker for GM-OS Self-Repair System.

Tracks thermodynamic costs of repair and reconfiguration per Self-Repair Model Section 14:

Continuous cost: W_repair (hidden dissipation / stabilization work)
Discrete cost: κ_repair (projection/coarse-graining loss)

These map to receipt-level Spend and Defect via the hidden-fiber envelope logic.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum
import time


class CostType(Enum):
    """Types of thermodynamic costs."""
    CONTINUOUS = "continuous"    # W_repair - dissipation
    DISCRETE = "discrete"       # κ_repair - projection loss
    SPEND = "spend"             # Budget expenditure
    DEFECT = "defect"            # Uncertainty/information loss


@dataclass
class ThermodynamicCost:
    """Thermodynamic cost of an operation."""
    cost_type: CostType
    
    # Components
    recomputation_cost: float = 0.0      # Work to rebuild structure
    entropy_reduction: float = 0.0        # Order restored
    boundary_coherence: float = 0.0        # Lawful continuity
    projection_loss: float = 0.0          # Detail destroyed
    compression_loss: float = 0.0         # Branch discard
    
    # Totals
    continuous_total: float = 0.0   # W_repair
    discrete_total: float = 0.0      # κ_repair
    
    # Metadata
    operation: str = ""
    timestamp: float = field(default_factory=time.time)
    
    @property
    def total(self) -> float:
        """Total thermodynamic cost."""
        return self.continuous_total + self.discrete_total


@dataclass
class CostBudget:
    """Budget for thermodynamic costs."""
    total_budget: float = 100.0
    spent: float = 0.0
    reserve: float = 10.0
    
    @property
    def remaining(self) -> float:
        return self.total_budget - self.spent - self.reserve
    
    @property
    def utilization(self) -> float:
        return self.spent / max(0.001, self.total_budget)


class ThermodynamicCostTracker:
    """
    Tracks thermodynamic costs of repair and reconfiguration.
    
    Per Self-Repair Model Section 14:
    
    Repair consumes budget because it:
    - Recomputes lost local structure
    - Reduces entropy in corrupted subsystems
    - Restores lawful boundary coherence
    - Discards damaged branches by paying projection loss
    - Rewrites memory anchors
    
    These appear as Spend and Defect in receipts.
    """
    
    def __init__(self, total_budget: float = 100.0, reserve: float = 10.0):
        """
        Initialize tracker.
        
        Args:
            total_budget: Total thermodynamic budget
            reserve: Protected reserve
        """
        self.budget = CostBudget(total_budget=total_budget, reserve=reserve)
        self._cost_history: List[ThermodynamicCost] = []
        self._max_history = 1000
        
        # Aggregates
        self._total_continuous = 0.0
        self._total_discrete = 0.0
    
    def compute_repair_cost(
        self,
        operation: str,
        curvature_delta: float = 0.0,
        tension_delta: float = 0.0,
        state_size_delta: float = 0.0,
        branches_pruned: int = 0
    ) -> ThermodynamicCost:
        """
        Compute thermodynamic cost of repair.
        
        Args:
            operation: Type of repair operation
            curvature_delta: Change in curvature (positive = more damage)
            tension_delta: Change in tension (positive = more damage)
            state_size_delta: Change in state size
            branches_pruned: Number of branches discarded
            
        Returns:
            ThermodynamicCost with computed components
        """
        cost = ThermodynamicCost(cost_type=CostType.CONTINUOUS, operation=operation)
        
        # Continuous costs (W_repair)
        # Entropy reduction from healing
        cost.entropy_reduction = max(0, tension_delta) * 0.5
        
        # Recomputation cost proportional to damage fixed
        cost.recomputation_cost = max(0, -curvature_delta) * 1.0 + max(0, -tension_delta) * 0.5
        
        # Boundary coherence restoration
        cost.boundary_coherence = max(0, -state_size_delta) * 0.3
        
        cost.continuous_total = (
            cost.recomputation_cost +
            cost.entropy_reduction +
            cost.boundary_coherence
        )
        
        # Discrete costs (κ_repair)
        # Projection loss from discarding branches
        cost.projection_loss = branches_pruned * 2.0
        
        # Compression loss from summarization
        cost.compression_loss = max(0, state_size_delta) * 0.5
        
        cost.discrete_total = (
            cost.projection_loss +
            cost.compression_loss
        )
        
        return cost
    
    def compute_reconfiguration_cost(
        self,
        from_mode: str,
        to_mode: str,
        features_disabled: int = 0,
        memory_compressed: float = 0.0
    ) -> ThermodynamicCost:
        """
        Compute cost of geometry reconfiguration.
        
        Per Adaptive Reconfiguration Model Section 11:
        
        Contraction causes damage-like effects:
        - Pruning destroys branches
        - Summarization loses detail
        - Narrow instruments increase uncertainty
        """
        cost = ThermodynamicCost(cost_type=CostType.CONTINUOUS, operation=f"{from_mode}->{to_mode}")
        
        # Continuous costs
        cost.recomputation_cost = features_disabled * 1.0
        cost.entropy_reduction = memory_compressed * 0.2
        cost.boundary_coherence = 0.5  # Restructuring cost
        
        cost.continuous_total = (
            cost.recomputation_cost +
            cost.entropy_reduction +
            cost.boundary_coherence
        )
        
        # Discrete costs
        cost.projection_loss = features_disabled * 3.0
        cost.compression_loss = memory_compressed * 1.0
        
        cost.discrete_total = (
            cost.projection_loss +
            cost.compression_loss
        )
        
        return cost
    
    def spend(self, cost: ThermodynamicCost) -> bool:
        """
        Apply a thermodynamic cost to the budget.
        
        Args:
            cost: Cost to apply
            
        Returns:
            True if cost was applied (budget sufficient)
        """
        total = cost.total
        
        if total > self.budget.remaining:
            return False
        
        self.budget.spent += total
        self._total_continuous += cost.continuous_total
        self.budget.spent += cost.discrete_total
        self._total_discrete += cost.discrete_total
        
        self._cost_history.append(cost)
        if len(self._cost_history) > self._max_history:
            self._cost_history = self._cost_history[-self._max_history:]
        
        return True
    
    def can_afford(self, cost: ThermodynamicCost) -> bool:
        """Check if cost can be afforded."""
        return cost.total <= self.budget.remaining
    
    def get_statistics(self) -> Dict:
        """Get cost statistics."""
        return {
            "budget": {
                "total": self.budget.total_budget,
                "spent": self.budget.spent,
                "remaining": self.budget.remaining,
                "utilization": self.budget.utilization
            },
            "totals": {
                "continuous": self._total_continuous,
                "discrete": self._total_discrete,
                "combined": self._total_continuous + self._total_discrete
            },
            "history_count": len(self._cost_history)
        }
    
    def get_recent_costs(self, limit: int = 10) -> List[ThermodynamicCost]:
        """Get recent costs."""
        return self._cost_history[-limit:]
    
    def reset(self) -> None:
        """Reset tracker."""
        self.budget.spent = 0.0
        self._total_continuous = 0.0
        self._total_discrete = 0.0
        self._cost_history.clear()


def create_cost_tracker(
    total_budget: float = 100.0,
    reserve: float = 10.0
) -> ThermodynamicCostTracker:
    """
    Factory to create thermodynamic cost tracker.
    
    Args:
        total_budget: Total budget
        reserve: Protected reserve
        
    Returns:
        Configured ThermodynamicCostTracker
    """
    return ThermodynamicCostTracker(
        total_budget=total_budget,
        reserve=reserve
    )
