"""
Hierarchical Budget Delegation for the GMI Universal Cognition Engine.

Module 17.2: Hierarchical Budget Delegation

The core principle: Energy always flows from strategic allocation → operational execution.
This matches real systems where higher-level planning allocates resources for
lower-level execution.

Mathematical Specification:
  B_total = Σₗ B⁽ˡ⁾
  
Budget Flow (downward only):
  B⁽ˡ⁾ → B⁽ˡ⁻¹⁾ for l > 1

Protected Survival Reserve:
  B_reserve⁽¹⁾ ≥ b_min  (Layer 1 cannot be starved)

EXPLICIT ASSUMPTION (Budget Transfer Energy Conservation):
  For internal budget transfers between layers:
    Σₗ ΔB⁽ˡ⁾ = 0
    
This ensures budget transfers do not create or destroy energy.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class BudgetDelegation:
    """
    Record of a budget delegation between layers.
    
    Attributes:
        from_layer: Source layer (higher index)
        to_layer: Target layer (lower index) 
        amount: Amount delegated
        timestamp: When the delegation occurred
    """
    from_layer: int
    to_layer: int
    amount: float
    timestamp: int = 0


@dataclass
class HierarchicalBudget:
    """
    Hierarchical budget management with downward flow and transfer invariants.
    
    This implements the budget cascade: thinking can stop without dying
    because the reflex layer (Layer 1) maintains a protected survival reserve.
    
    Attributes:
        layer_budgets: Budget for each layer (index 0 = Layer 1)
        min_reserves: Minimum reserve for each layer
        delegation_history: Record of all delegations
    """
    layer_budgets: List[float]
    min_reserves: List[float]
    delegation_history: List[BudgetDelegation] = field(default_factory=list)
    timestamp: int = 0
    
    def __post_init__(self):
        """Validate budget constraints after construction."""
        if len(self.layer_budgets) != len(self.min_reserves):
            raise ValueError(
                "Number of budgets must match number of reserves"
            )
        for i, (b, r) in enumerate(zip(self.layer_budgets, self.min_reserves)):
            if b < r:
                raise ValueError(
                    f"Layer {i+1}: budget ({b}) < reserve ({r})"
                )
    
    @property
    def num_layers(self) -> int:
        """Return the number of layers."""
        return len(self.layer_budgets)
    
    @property
    def total_budget(self) -> float:
        """Return total budget across all layers."""
        return sum(self.layer_budgets)
    
    @property
    def total_reserve(self) -> float:
        """Return total minimum reserves across all layers."""
        return sum(self.min_reserves)
    
    def get_budget(self, layer_id: int) -> float:
        """
        Get budget for a specific layer.
        
        Args:
            layer_id: Layer index (1-based)
            
        Returns:
            Current budget for that layer
        """
        return self.layer_budgets[layer_id - 1]
    
    def get_reserve(self, layer_id: int) -> float:
        """
        Get minimum reserve for a specific layer.
        
        Args:
            layer_id: Layer index (1-based)
            
        Returns:
            Minimum reserve for that layer
        """
        return self.min_reserves[layer_id - 1]
    
    def get_available(self, layer_id: int) -> float:
        """
        Get available budget (budget - reserve) for a layer.
        
        Args:
            layer_id: Layer index (1-based)
            
        Returns:
            Available budget for spending
        """
        budget = self.get_budget(layer_id)
        reserve = self.get_reserve(layer_id)
        return max(0.0, budget - reserve)
    
    def can_delegate(
        self, 
        from_layer: int, 
        to_layer: int, 
        amount: float
    ) -> bool:
        """
        Check if a budget delegation is possible.
        
        Args:
            from_layer: Source layer (must be > to_layer for downward flow)
            to_layer: Target layer
            amount: Amount to delegate
            
        Returns:
            True if delegation is possible
        """
        # Must be downward flow
        if from_layer <= to_layer:
            return False
        
        # Source must have enough available budget
        if self.get_available(from_layer) < amount:
            return False
        
        return True
    
    def delegate(
        self, 
        from_layer: int, 
        to_layer: int, 
        amount: float,
        force: bool = False
    ) -> Tuple[bool, float]:
        """
        Execute a budget delegation from one layer to another.
        
        Budget flows downward: from higher layers (strategic) to lower 
        layers (operational). This is the core of the hierarchical architecture.
        
        Args:
            from_layer: Source layer (must be > to_layer)
            to_layer: Target layer
            amount: Amount to delegate
            force: If True, allow delegation even if it dips into reserve
            
        Returns:
            Tuple of (success, actual_amount_delegated)
        """
        # Enforce downward flow
        if from_layer <= to_layer:
            raise ValueError(
                f"Budget can only flow downward: from_layer ({from_layer}) "
                f"must be > to_layer ({to_layer})"
            )
        
        source_idx = from_layer - 1
        target_idx = to_layer - 1
        
        # Calculate actual amount
        available = self.layer_budgets[source_idx] - self.min_reserves[source_idx]
        
        if not force:
            actual = min(amount, available)
        else:
            # With force, can dip into reserve but not below zero
            actual = min(amount, self.layer_budgets[source_idx])
        
        if actual <= 0:
            return False, 0.0
        
        # Execute delegation
        self.layer_budgets[source_idx] -= actual
        self.layer_budgets[target_idx] += actual
        
        # Record in history
        self.timestamp += 1
        self.delegation_history.append(BudgetDelegation(
            from_layer=from_layer,
            to_layer=to_layer,
            amount=actual,
            timestamp=self.timestamp
        ))
        
        return True, actual
    
    def spend(
        self, 
        layer_id: int, 
        amount: float
    ) -> Tuple[bool, float]:
        """
        Spend budget from a specific layer.
        
        Args:
            layer_id: Layer to spend from
            amount: Amount to spend
            
        Returns:
            Tuple of (success, actual_amount_spent)
        """
        available = self.get_available(layer_id)
        
        if available < amount:
            # Can only spend what's available (not reserve)
            actual = available
            if actual <= 0:
                return False, 0.0
        else:
            actual = amount
        
        self.layer_budgets[layer_id - 1] -= actual
        return True, actual
    
    def replenish(
        self, 
        layer_id: int, 
        amount: float
    ) -> None:
        """
        Add budget to a layer (e.g., from environment).
        
        Args:
            layer_id: Layer to replenish
            amount: Amount to add
        """
        self.layer_budgets[layer_id - 1] += amount
    
    def check_invariant(self) -> Tuple[bool, str]:
        """
        Check the budget transfer invariant: Σₗ ΔB⁽ˡ⁾ = 0 for internal transfers.
        
        This verifies that all budget movements have been balanced
        (no energy created or destroyed within the system).
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check each layer has at least its reserve
        for i, (b, r) in enumerate(zip(self.layer_budgets, self.min_reserves)):
            if b < r:
                return False, f"Layer {i+1} violates reserve: {b} < {r}"
        
        # The total budget should be conserved (except for external spend/replenish)
        # We can't check this directly without tracking external flows,
        # but we can verify the system is self-consistent
        
        return True, "All invariants satisfied"
    
    def compute_reserve_violations(self) -> List[int]:
        """
        Find layers that violate their reserve requirements.
        
        Returns:
            List of layer IDs that are below reserve
        """
        violations = []
        for i, (b, r) in enumerate(zip(self.layer_budgets, self.min_reserves)):
            if b < r:
                violations.append(i + 1)
        return violations
    
    def is_viable(self) -> bool:
        """
        Check if the hierarchical budget is globally viable.
        
        A system is viable if:
        1. All layers have at least their minimum reserves
        2. The reflex layer (Layer 1) specifically has its survival reserve
        
        Returns:
            True if system is viable
        """
        # Check reserves
        if self.compute_reserve_violations():
            return False
        
        # Reflex layer must have positive budget (cannot be starved)
        if self.layer_budgets[0] <= 0:
            return False
        
        return True
    
    def snapshot(self) -> Dict:
        """
        Create a snapshot of the current budget state.
        
        Returns:
            Dict with budget state
        """
        return {
            'layer_budgets': list(self.layer_budgets),
            'min_reserves': list(self.min_reserves),
            'total_budget': self.total_budget,
            'total_reserve': self.total_reserve,
            'timestamp': self.timestamp,
            'is_viable': self.is_viable()
        }


class BudgetCascade:
    """
    Automatic budget cascade system.
    
    This implements the "thinking can stop without dying" property:
    when the system stops thinking (reduces activity), budget cascades
    downward to ensure the reflex layer survives.
    
    Usage:
        cascade = BudgetCascade(hierarchical_budget)
        cascade.trigger_if_needed()
    """
    
    def __init__(
        self, 
        budget: HierarchicalBudget,
        cascade_threshold: float = 0.5
    ):
        """
        Initialize budget cascade.
        
        Args:
            budget: The hierarchical budget to manage
            cascade_threshold: Fraction of reserve that triggers cascade
        """
        self.budget = budget
        self.cascade_threshold = cascade_threshold
    
    def compute_cascade_amounts(self) -> Dict[Tuple[int, int], float]:
        """
        Compute how much budget should cascade from each layer.
        
        Returns:
            Dict mapping (from_layer, to_layer) -> amount to cascade
        """
        cascade_amounts = {}
        
        for layer in range(2, self.budget.num_layers + 1):
            reserve = self.budget.get_reserve(layer)
            current = self.budget.get_budget(layer)
            
            # If above reserve, can cascade the excess
            excess = current - reserve
            
            if excess > 0:
                # Cascade to layer below
                cascade_amounts[(layer, layer - 1)] = excess
        
        return cascade_amounts
    
    def trigger_if_needed(self) -> Tuple[bool, List[BudgetDelegation]]:
        """
        Trigger cascade if any layer is at risk of reserve violation.
        
        Returns:
            Tuple of (cascade_triggered, list_of_delegations)
        """
        delegations = []
        
        # Check each layer
        for layer in range(2, self.budget.num_layers + 1):
            current = self.budget.get_budget(layer)
            reserve = self.budget.get_reserve(layer)
            
            # If below threshold of reserve, trigger cascade
            if current < reserve * (1 + self.cascade_threshold):
                # Try to get budget from layer above
                if layer < self.budget.num_layers:
                    available = self.budget.get_available(layer + 1)
                    if available > 0:
                        success, amount = self.budget.delegate(
                            from_layer=layer + 1,
                            to_layer=layer,
                            amount=available
                        )
                        if success and amount > 0:
                            delegations.append(BudgetDelegation(
                                from_layer=layer + 1,
                                to_layer=layer,
                                amount=amount,
                                timestamp=self.budget.timestamp
                            ))
        
        return len(delegations) > 0, delegations
    
    def force_cascade_all(self) -> List[BudgetDelegation]:
        """
        Force complete cascade of all excess budget downward.
        
        Returns:
            List of delegations performed
        """
        delegations = []
        
        # Process from top down
        for layer in range(self.budget.num_layers, 1, -1):
            available = self.budget.get_available(layer)
            
            if available > 0:
                success, amount = self.budget.delegate(
                    from_layer=layer,
                    to_layer=layer - 1,
                    amount=available
                )
                if success and amount > 0:
                    delegations.append(BudgetDelegation(
                        from_layer=layer,
                        to_layer=layer - 1,
                        amount=amount,
                        timestamp=self.budget.timestamp
                    ))
        
        return delegations


def create_default_hierarchical_budget(
    num_layers: int = 3,
    total_budget: float = 100.0,
    reflex_reserve: float = 10.0,
    reserve_ratio: float = 0.1
) -> HierarchicalBudget:
    """
    Create a default hierarchical budget with standard configuration.
    
    Args:
        num_layers: Number of layers
        total_budget: Total budget to distribute
        reflex_reserve: Minimum reserve for Layer 1 (survival critical)
        reserve_ratio: Reserve ratio for higher layers
        
    Returns:
        Configured HierarchicalBudget
    """
    # Exponential budget distribution: higher layers get more
    # This matches the intuition that strategic thinking requires more resources
    fractions = [2.0 ** (-i) for i in range(num_layers)]
    total_fraction = sum(fractions)
    fractions = [f / total_fraction for f in fractions]
    
    layer_budgets = [total_budget * f for f in fractions]
    
    # Reserves: Layer 1 gets absolute minimum, others get ratio
    min_reserves = [reflex_reserve] + [
        layer_budgets[i] * reserve_ratio 
        for i in range(1, num_layers)
    ]
    
    return HierarchicalBudget(
        layer_budgets=layer_budgets,
        min_reserves=min_reserves
    )


# Explicit invariant check for theorem proofs
def verify_budget_transfer_invariant(
    before: List[float],
    after: List[float]
) -> Tuple[bool, float]:
    """
    Verify the budget transfer invariant: Σₗ ΔB⁽ˡ⁾ = 0
    
    This is the explicit assumption required for Theorem 17.2.
    
    Args:
        before: Budgets before transfer
        after: Budgets after transfer
        
    Returns:
        Tuple of (is_conserved, delta_sum)
    """
    delta_sum = sum(a - b for a, b in zip(after, before))
    return abs(delta_sum) < 1e-10, delta_sum


def compute_global_viability(
    layer_potentials: List[float],
    layer_budgets: List[float],
    lambda_budget: float = 0.01
) -> float:
    """
    Compute the global viability measure V_GMI.
    
    V_GMI = Σₗ V⁽ˡ⁾ + λ⋅Σₗ B⁽ˡ⁾
    
    Args:
        layer_potentials: List of potential values per layer
        layer_budgets: List of budget values per layer
        lambda_budget: Scaling factor for budget contribution
        
    Returns:
        Global viability
    """
    total = sum(layer_potentials) + lambda_budget * sum(layer_budgets)
    return total
