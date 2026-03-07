"""
Memory Budget Costs for the GMI Memory System.

Prices all memory operations thermodynamically.
The anti-raccoon law: no free recall, no free imagination, no self-issued reward.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class MemoryBudgetLaw:
    """
    Full budget law with memory operations.
    
    B_{k+1} = B_k - Σ_phys - Σ_R - Σ_W - Σ_P - Σ_K + G_env
    
    All costs are nonnegative. All internal epistemic operations
    carry strict minimum toll (anti-raccoon law).
    
    Cost formula for each operation:
    Σ = μ * |operation|² + σ
    
    Where:
    - μ (mu): Quadratic cost coefficient
    - |operation|: Magnitude of the operation (e.g., vector length)
    - σ (sigma): Minimum toll (ensures finite operations under finite budget)
    """
    # Quadratic cost coefficients
    mu_read: float = 1.0
    mu_write: float = 1.2
    mu_replay: float = 1.5
    mu_compare: float = 0.8
    mu_prune: float = 1.0
    
    # Minimum tolls (ensures bounded operations)
    sigma_read: float = 0.3
    sigma_write: float = 0.5
    sigma_replay: float = 0.8
    sigma_compare: float = 0.2
    sigma_prune: float = 0.4
    
    def cost_read(self, operation_magnitude: float) -> float:
        """
        Compute cost of a read operation.
        
        Args:
            operation_magnitude: Size of data being read
            
        Returns:
            Cost in budget units
        """
        return self.mu_read * (operation_magnitude ** 2) + self.sigma_read
    
    def cost_write(self, operation_magnitude: float) -> float:
        """
        Compute cost of a write operation.
        
        Args:
            operation_magnitude: Size of data being written
            
        Returns:
            Cost in budget units
        """
        return self.mu_write * (operation_magnitude ** 2) + self.sigma_write
    
    def cost_replay(self, operation_magnitude: float) -> float:
        """
        Compute cost of a replay operation.
        
        Replay is more expensive than read because it reconstructs
        internal geometry, not just metadata.
        
        Args:
            operation_magnitude: Size of data being reconstructed
            
        Returns:
            Cost in budget units
        """
        return self.mu_replay * (operation_magnitude ** 2) + self.sigma_replay
    
    def cost_compare(self, operation_magnitude: float) -> float:
        """
        Compute cost of a compare operation.
        
        Args:
            operation_magnitude: Size of data being compared
            
        Returns:
            Cost in budget units
        """
        return self.mu_compare * (operation_magnitude ** 2) + self.sigma_compare
    
    def cost_prune(self, operation_magnitude: float) -> float:
        """
        Compute cost of a prune/consolidation operation.
        
        Args:
            operation_magnitude: Amount of data being consolidated
            
        Returns:
            Cost in budget units
        """
        return self.mu_prune * (operation_magnitude ** 2) + self.sigma_prune
    
    def can_afford(self, budget: float, operation_magnitude: float, op_type: str) -> bool:
        """
        Check if budget can afford an operation.
        
        Args:
            budget: Current budget
            operation_magnitude: Size of operation
            op_type: Type of operation ("read", "write", "replay", "compare", "prune")
            
        Returns:
            True if budget can afford the operation
        """
        cost_map = {
            "read": self.cost_read,
            "write": self.cost_write,
            "replay": self.cost_replay,
            "compare": self.cost_compare,
            "prune": self.cost_prune
        }
        
        cost_fn = cost_map.get(op_type.lower())
        if cost_fn is None:
            return False
        
        return budget >= cost_fn(operation_magnitude)
    
    def max_operations(self, budget: float, op_type: str) -> int:
        """
        Compute maximum number of operations possible under budget.
        
        Uses quadratic cost formula:
        budget >= μ * n * |op|² + n * σ
        
        Solving for n:
        n <= budget / (μ * |op|² + σ)
        
        Args:
            budget: Available budget
            op_type: Type of operation
            
        Returns:
            Maximum number of operations
        """
        # Default magnitude
        magnitude = 1.0
        
        if op_type.lower() == "read":
            denom = self.mu_read * (magnitude ** 2) + self.sigma_read
        elif op_type.lower() == "write":
            denom = self.mu_write * (magnitude ** 2) + self.sigma_write
        elif op_type.lower() == "replay":
            denom = self.mu_replay * (magnitude ** 2) + self.sigma_replay
        elif op_type.lower() == "compare":
            denom = self.mu_compare * (magnitude ** 2) + self.sigma_compare
        elif op_type.lower() == "prune":
            denom = self.mu_prune * (magnitude ** 2) + self.sigma_prune
        else:
            return 0
        
        if denom <= 0:
            return float('inf')
        
        return int(budget / denom)
    
    def budget_summary(self, budget: float) -> Dict[str, int]:
        """
        Get summary of available operations under budget.
        
        Args:
            budget: Available budget
            
        Returns:
            Dict of operation type to max count
        """
        return {
            "read": self.max_operations(budget, "read"),
            "write": self.max_operations(budget, "write"),
            "replay": self.max_operations(budget, "replay"),
            "compare": self.max_operations(budget, "compare"),
            "prune": self.max_operations(budget, "prune")
        }


# Global budget law instance
_global_budget_law: MemoryBudgetLaw = None


def get_budget_law() -> MemoryBudgetLaw:
    """Get or create the global memory budget law."""
    global _global_budget_law
    if _global_budget_law is None:
        _global_budget_law = MemoryBudgetLaw()
    return _global_budget_law


def set_budget_law(law: MemoryBudgetLaw) -> None:
    """Set the global memory budget law."""
    global _global_budget_law
    _global_budget_law = law
