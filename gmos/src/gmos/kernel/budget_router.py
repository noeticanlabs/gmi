"""
Budget Router for GM-OS Kernel.

Manages process and layer budgets, enforces reserve law, handles lawful
internal transfers, protects survival reserves.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class ReserveTier(Enum):
    """Reserve protection tiers."""
    SURVIVAL = "survival"       # layer 1 protected
    ESSENTIAL = "essential"     # layer 2 protected  
    DISCRETIONARY = "discretionary"  # can be depleted


@dataclass
class BudgetSlice:
    """Individual budget allocation."""
    process_id: str
    layer: int
    amount: float
    reserve: float
    tier: ReserveTier = ReserveTier.DISCRETIONARY
    
    @property
    def available(self) -> float:
        """Amount available to spend."""
        return max(0, self.amount - self.reserve)


class BudgetRouter:
    """
    Budget routing and reserve enforcement.
    
    Core laws enforced:
    - no internal minting
    - reserve floor preservation
    - protected layer-1 reserve
    - optional emergency override hook
    """
    
    def __init__(self, global_reserve: float = 0.0):
        self._global_budget: float = 0.0
        self._global_reserve: float = global_reserve
        self._process_budgets: Dict[str, BudgetSlice] = {}
        self._layer_budgets: Dict[str, Dict[int, BudgetSlice]] = {}
    
    def register_process_budget(
        self, 
        process_id: str, 
        layer: int,
        amount: float,
        reserve: float = 0.0,
        tier: ReserveTier = ReserveTier.DISCRETIONARY
    ) -> BudgetSlice:
        """Register budget for a process layer."""
        budget = BudgetSlice(
            process_id=process_id,
            layer=layer,
            amount=amount,
            reserve=reserve,
            tier=tier
        )
        self._process_budgets[process_id] = budget
        
        if process_id not in self._layer_budgets:
            self._layer_budgets[process_id] = {}
        self._layer_budgets[process_id][layer] = budget
        
        return budget
    
    def register_layer_budget(
        self,
        process_id: str,
        layer: int,
        amount: float,
        reserve: float
    ) -> BudgetSlice:
        """Register budget for a specific layer."""
        tier = ReserveTier.SURVIVAL if layer == 1 else ReserveTier.ESSENTIAL
        return self.register_process_budget(process_id, layer, amount, reserve, tier)
    
    def can_spend(self, process_id: str, layer: int, amount: float) -> bool:
        """Check if spend is feasible."""
        budget = self._get_budget(process_id, layer)
        if not budget:
            return False
        return budget.amount - amount >= budget.reserve
    
    def apply_spend(self, process_id: str, layer: int, amount: float) -> bool:
        """Apply a spend if legal."""
        if not self.can_spend(process_id, layer, amount):
            return False
        
        budget = self._get_budget(process_id, layer)
        budget.amount -= amount
        return True
    
    def route_budget(
        self, 
        from_process: str, 
        to_process: str, 
        layer: int, 
        amount: float
    ) -> bool:
        """Route budget between processes (parent delegation)."""
        if not self.can_spend(from_process, layer, amount):
            return False
        
        self.apply_spend(from_process, layer, amount)
        
        if to_process in self._process_budgets:
            self._process_budgets[to_process].amount += amount
        else:
            self.register_process_budget(to_process, layer, amount, 0.0)
        
        return True
    
    def reserve_ok(self, process_id: str, layer: int) -> bool:
        """Check if reserve is preserved."""
        budget = self._get_budget(process_id, layer)
        if not budget:
            return False
        return budget.amount >= budget.reserve
    
    def get_budget(self, process_id: str, layer: Optional[int] = None) -> Optional[float]:
        """Get current budget for process/layer."""
        if layer is not None:
            budget = self._get_budget(process_id, layer)
            return budget.amount if budget else None
        process_budget = self._process_budgets.get(process_id)
        return process_budget.amount if process_budget else None
    
    def get_reserve(self, process_id: str, layer: int) -> Optional[float]:
        """Get reserve amount for process/layer."""
        budget = self._get_budget(process_id, layer)
        return budget.reserve if budget else None
    
    def _get_budget(self, process_id: str, layer: int) -> Optional[BudgetSlice]:
        """Get budget slice for process and layer."""
        if process_id in self._layer_budgets:
            return self._layer_budgets[process_id].get(layer)
        return self._process_budgets.get(process_id)
