"""
Operating Cost Calculator for GM-OS Adaptive Reconfiguration System.

Computes the metabolic cost of current operating geometry per Adaptive Reconfiguration Model Section 6:

    C_op(Γ) = C_idle(Γ) + C_memory(Γ) + C_inference(Γ) + C_projection(Γ) + C_coord(Γ)

This determines whether the current geometry is affordable given available budget.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum

from gmos.kernel.reconfiguration import GeometryMode, ModeConfig, MODE_CONFIGS


@dataclass
class CostComponents:
    """Individual cost components."""
    idle: float = 0.0
    memory: float = 0.0
    inference: float = 0.0
    projection: float = 0.0
    coord: float = 0.0
    
    @property
    def total(self) -> float:
        """Total operating cost."""
        return self.idle + self.memory + self.inference + self.projection + self.coord


@dataclass
class OperatingBudget:
    """Available operating budget."""
    total_budget: float = 100.0
    reserve_floor: float = 10.0
    
    @property
    def available(self) -> float:
        """Budget available for operations."""
        return max(0.0, self.total_budget - self.reserve_floor)


class OperatingCostCalculator:
    """
    Calculates operating cost for different geometry modes.
    
    Per Adaptive Reconfiguration Model Section 6:
    A configuration is affordable only if:
    
        C_op(Γ) <= B_p - B_reserve
    """
    
    def __init__(
        self,
        base_idle_cost: float = 1.0,
        base_memory_cost: float = 2.0,
        base_inference_cost: float = 3.0,
        base_projection_cost: float = 2.0,
        base_coord_cost: float = 1.5
    ):
        """
        Args:
            base_*_cost: Base cost per tick for each component
        """
        self.base_costs = {
            'idle': base_idle_cost,
            'memory': base_memory_cost,
            'inference': base_inference_cost,
            'projection': base_projection_cost,
            'coord': base_coord_cost,
        }
    
    def calculate_cost(
        self,
        mode: GeometryMode,
        modifiers: Optional[Dict[str, float]] = None
    ) -> CostComponents:
        """
        Calculate operating cost for a geometry mode.
        
        Args:
            mode: Geometry mode
            modifiers: Optional custom cost multipliers
            
        Returns:
            CostComponents with individual and total costs
        """
        config = MODE_CONFIGS.get(mode, MODE_CONFIGS[GeometryMode.FULL])
        
        # Apply mode-specific multipliers
        multipliers = modifiers if modifiers is not None else {}
        
        return CostComponents(
            idle=self.base_costs['idle'] * config.idle_cost_mult * multipliers.get('idle', 1.0),
            memory=self.base_costs['memory'] * config.memory_cost_mult * multipliers.get('memory', 1.0),
            inference=self.base_costs['inference'] * config.inference_cost_mult * multipliers.get('inference', 1.0),
            projection=self.base_costs['projection'] * config.projection_cost_mult * multipliers.get('projection', 1.0),
            coord=self.base_costs['coord'] * config.coord_cost_mult * multipliers.get('coord', 1.0),
        )
    
    def is_affordable(
        self,
        mode: GeometryMode,
        budget: OperatingBudget,
        modifiers: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Check if a geometry mode is affordable given budget.
        
        Per Adaptive Reconfiguration Model Section 13.1:
        
            C_op(Γ) <= B - B_reserve
        """
        cost = self.calculate_cost(mode, modifiers)
        return cost.total <= budget.available
    
    def get_affordable_modes(
        self,
        budget: OperatingBudget,
        min_mode: GeometryMode = GeometryMode.TORPOR
    ) -> List[GeometryMode]:
        """
        Get list of affordable geometry modes.
        
        Args:
            budget: Available budget
            min_mode: Minimum mode to consider (e.g., don't go below SURVIVAL)
            
        Returns:
            List of affordable modes, ordered from highest to lowest
        """
        modes = []
        for mode in [GeometryMode.FULL, GeometryMode.EFFICIENCY, 
                     GeometryMode.DEFENSIVE, GeometryMode.SURVIVAL, GeometryMode.TORPOR]:
            if self.is_affordable(mode, budget):
                modes.append(mode)
            if mode == min_mode:
                break
        
        return modes
    
    def get_minimum_affordable_mode(
        self,
        budget: OperatingBudget
    ) -> Optional[GeometryMode]:
        """
        Get the lowest geometry mode that is still affordable.
        
        Returns:
            Minimum affordable mode, or None if even torpor is too expensive
        """
        affordable = self.get_affordable_modes(budget, min_mode=GeometryMode.TORPOR)
        return affordable[-1] if affordable else None
    
    def compute_cost_reduction(
        self,
        from_mode: GeometryMode,
        to_mode: GeometryMode
    ) -> float:
        """
        Compute cost reduction from transitioning modes.
        
        Args:
            from_mode: Current mode
            to_mode: Target mode
            
        Returns:
            Cost reduction (positive = savings)
        """
        cost_from = self.calculate_cost(from_mode)
        cost_to = self.calculate_cost(to_mode)
        return cost_from.total - cost_to.total
    
    def get_cost_summary(self, mode: GeometryMode) -> Dict[str, float]:
        """
        Get cost summary for a mode.
        
        Returns:
            Dictionary with cost breakdown
        """
        cost = self.calculate_cost(mode)
        config = MODE_CONFIGS[mode]
        
        return {
            "mode": mode.value,
            "description": config.description,
            "idle": cost.idle,
            "memory": cost.memory,
            "inference": cost.inference,
            "projection": cost.projection,
            "coord": cost.coord,
            "total": cost.total,
            "idle_mult": config.idle_cost_mult,
            "memory_mult": config.memory_cost_mult,
            "inference_mult": config.inference_cost_mult,
            "projection_mult": config.projection_cost_mult,
            "coord_mult": config.coord_cost_mult,
        }


# Default calculator instance
_default_calculator: Optional[OperatingCostCalculator] = None


def get_default_calculator() -> OperatingCostCalculator:
    """Get or create default cost calculator."""
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = OperatingCostCalculator()
    return _default_calculator


def calculate_operating_cost(mode: GeometryMode) -> float:
    """
    Convenience function to calculate operating cost.
    
    Args:
        mode: Geometry mode
        
    Returns:
        Total operating cost per tick
    """
    calculator = get_default_calculator()
    return calculator.calculate_cost(mode).total


def is_mode_affordable(mode: GeometryMode, budget: float, reserve: float = 10.0) -> bool:
    """
    Convenience function to check if mode is affordable.
    
    Args:
        mode: Geometry mode
        budget: Total budget
        reserve: Reserve floor
        
    Returns:
        True if affordable
    """
    calculator = get_default_calculator()
    operating_budget = OperatingBudget(total_budget=budget, reserve_floor=reserve)
    return calculator.is_affordable(mode, operating_budget)
