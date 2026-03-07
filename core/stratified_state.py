"""
Stratified Mind Manifold for the GMI Universal Cognition Engine.

Module 17: Stratified Mind Architecture

The core insight is that minds must stratify to survive:
- Fast, cheap control loops under slow, expensive supervisory loops
- Biology: reflex arcs vs cortical planning
- Engineering: CPU pipeline stages, control loops in aircraft
- Physics: local PDE solvers under global constraint solvers

Mathematical Specification:
  Z = (Z⁽¹⁾, ..., Z⁽ᴸ⁾)
  
With coupling maps:
  Φ⁽ˡ→ˡ⁻¹⁾: budget delegation (downward flow)
  Ψ⁽ˡ⁻¹→ˡ⁾: information abstraction / receipt roll-up (upward flow)

Each layer l has:
  - z⁽ˡ⁾(t) = (x⁽ˡ⁾(t), b⁽ˡ⁾(t))
  - Δt⁽ˡ⁾: characteristic timescale (Δt⁽¹⁾ ≪ Δt⁽²⁾ ≪ ... ≪ Δt⁽ᴸ⁾)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Callable, Any
import numpy as np
import hashlib
import json


@dataclass
class LayerConfig:
    """
    Configuration for a single layer in the stratified manifold.
    
    Attributes:
        layer_id: Index of this layer (1 = reflex, L = strategic)
        timescale: Characteristic timestep Δt⁽ˡ⁾
        branch_allowed: Whether branching/speculation is allowed at this layer
        min_operator_cost: Minimum cost for any operator at this layer
        reserve_ratio: Fraction of layer budget that must be preserved
    """
    layer_id: int
    timescale: float
    branch_allowed: bool
    min_operator_cost: float
    reserve_ratio: float = 0.1  # 10% of layer budget is reserve


@dataclass
class LayerState:
    """
    State of a single layer in the stratified manifold.
    
    z⁽ˡ⁾(t) = (x⁽ˡ⁾(t), b⁽ˡ⁾(t))
    
    Attributes:
        x: Continuous cognitive coordinates in PhaseLoom space
        b: Thermodynamic budget for this layer
        curvature: Memory-augmented curvature (from MemoryManifold)
    """
    x: np.ndarray
    b: float
    curvature: float = 0.0
    
    def copy(self) -> 'LayerState':
        """Create a deep copy of this layer state."""
        return LayerState(
            x=self.x.copy(),
            b=float(self.b),
            curvature=float(self.curvature)
        )


class LayerCoupling(Protocol):
    """
    Protocol for inter-layer coupling maps.
    
    Φ⁽ˡ→ˡ⁻¹⁾: Budget delegation (downward flow)
    Ψ⁽ˡ⁻¹→ˡ⁾: Information abstraction (upward flow)
    """
    
    def delegate_budget(self, from_layer: int, to_layer: int, amount: float) -> float:
        """
        Delegate budget from layer l to layer l-1.
        
        Args:
            from_layer: Source layer index
            to_layer: Target layer index  
            amount: Amount to delegate
            
        Returns:
            Actual amount delegated (may be less than requested)
        """
        ...
    
    def abstract_information(self, from_layer: int, to_layer: int, data: Dict) -> Dict:
        """
        Abstract information from layer l-1 to layer l.
        
        Args:
            from_layer: Source layer (lower)
            to_layer: Target layer (higher)
            data: Information to abstract
            
        Returns:
            Abstracted information
        """
        ...


@dataclass
class StratifiedState:
    """
    The full stratified mind manifold state.
    
    Z = (Z⁽¹⁾, ..., Z⁽ᴸ⁾)
    
    This represents a fibered hierarchy of cognitive states, where:
    - Layer 1 (reflex): Fast, cheap, no branching
    - Layer 2 (working): Medium speed, local problem solving
    - Layer L (strategic): Slow, expensive, identity/goal formation
    
    Attributes:
        layers: List of layer states (index 0 = Layer 1)
        layer_configs: Configuration for each layer
        coupling_history: Record of budget delegations and abstractions
    """
    layers: List[LayerState]
    layer_configs: Dict[int, LayerConfig]
    coupling_history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the stratified state after construction."""
        if not self.layers:
            raise ValueError("StratifiedState must have at least one layer")
        if len(self.layers) != len(self.layer_configs):
            raise ValueError(
                f"Number of layers ({len(self.layers)}) must match "
                f"number of layer configs ({len(self.layer_configs)})"
            )
    
    @property
    def num_layers(self) -> int:
        """Return the number of layers in the stratified manifold."""
        return len(self.layers)
    
    @property
    def total_budget(self) -> float:
        """Return the total budget across all layers."""
        return sum(layer.b for layer in self.layers)
    
    def get_layer(self, layer_id: int) -> LayerState:
        """
        Get the state of a specific layer.
        
        Args:
            layer_id: Index of the layer (1-based, as in mathematical notation)
            
        Returns:
            The state of the specified layer
        """
        if layer_id < 1 or layer_id > self.num_layers:
            raise ValueError(
                f"Layer {layer_id} out of range [1, {self.num_layers}]"
            )
        return self.layers[layer_id - 1]
    
    def get_config(self, layer_id: int) -> LayerConfig:
        """
        Get the configuration for a specific layer.
        
        Args:
            layer_id: Index of the layer (1-based)
            
        Returns:
            The configuration for the specified layer
        """
        if layer_id not in self.layer_configs:
            raise ValueError(f"No configuration for layer {layer_id}")
        return self.layer_configs[layer_id]
    
    def delegate_budget(
        self, 
        from_layer: int, 
        to_layer: int, 
        amount: float
    ) -> bool:
        """
        Delegate budget from one layer to another (downward flow only).
        
        Budget can only flow from higher layers (larger index) to lower 
        layers (smaller index). This enforces the hierarchical structure.
        
        Args:
            from_layer: Source layer (must be > to_layer for downward flow)
            to_layer: Target layer (must be < from_layer)
            amount: Amount to delegate
            
        Returns:
            True if delegation succeeded, False otherwise
        """
        # Enforce downward flow: can only delegate from higher to lower
        if from_layer <= to_layer:
            raise ValueError(
                f"Budget can only flow downward: from_layer ({from_layer}) "
                f"must be > to_layer ({to_layer})"
            )
        
        source = self.get_layer(from_layer)
        target = self.get_layer(to_layer)
        
        # Check if source has enough budget
        source_config = self.get_config(from_layer)
        min_reserve = source.b * source_config.reserve_ratio
        
        if source.b - amount < min_reserve:
            # Cannot delegate - would violate reserve
            return False
        
        # Execute delegation
        source.b -= amount
        target.b += amount
        
        # Record in history
        self.coupling_history.append({
            'type': 'budget_delegation',
            'from_layer': from_layer,
            'to_layer': to_layer,
            'amount': amount,
        })
        
        return True
    
    def compute_potential(
        self, 
        potential_fn: Callable[[np.ndarray], float],
        layer_potentials: Optional[Dict[int, float]] = None
    ) -> float:
        """
        Compute the total GMI potential across all layers.
        
        Args:
            potential_fn: Base potential function V(x)
            layer_potentials: Optional dict of layer-specific potential adjustments
            
        Returns:
            Total potential across all layers
        """
        total = 0.0
        
        for i, layer in enumerate(self.layers):
            # Base potential from coordinates
            V_layer = potential_fn(layer.x)
            
            # Add curvature (memory penalty)
            V_layer += layer.curvature
            
            # Add layer-specific adjustments
            if layer_potentials and (i + 1) in layer_potentials:
                V_layer += layer_potentials[i + 1]
            
            total += V_layer
            
        return total
    
    def compute_viability(self) -> float:
        """
        Compute the global viability measure V_GMI.
        
        V_GMI = Σₗ V⁽ˡ⁾ + λ⋅Σₗ B⁽ˡ⁾
        
        Where λ is a scaling factor balancing potential energy and budget.
        """
        lambda_budget = 0.01  # Scaling factor
        
        total = 0.0
        for layer in self.layers:
            # Simple quadratic potential
            V_layer = np.sum(layer.x ** 2)
            total += V_layer + lambda_budget * layer.b
            
        return total
    
    def hash_state(self) -> str:
        """
        Compute a deterministic hash of the stratified state.
        
        Returns:
            SHA-256 hash as hexadecimal string
        """
        state_data = {
            'layers': [
                {
                    'x': layer.x.tolist(),
                    'b': float(layer.b),
                    'curvature': float(layer.curvature)
                }
                for layer in self.layers
            ]
        }
        
        json_str = json.dumps(state_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()


def create_default_stratified_state(
    num_layers: int = 3,
    dimension: int = 10,
    initial_budget: float = 100.0,
    timescale_ratio: float = 10.0
) -> StratifiedState:
    """
    Create a default stratified state with standard configuration.
    
    Args:
        num_layers: Number of layers (default 3: reflex, working, strategic)
        dimension: Dimension of each layer's coordinate space
        initial_budget: Initial total budget (distributed across layers)
        timescale_ratio: Ratio between adjacent layer timescales
        
    Returns:
        Configured StratifiedState
    """
    # Distribute budget exponentially: higher layers get more
    # This matches the intuition that strategic thinking is expensive
    layer_budgets = []
    remaining_budget = initial_budget
    
    for i in range(num_layers):
        # Exponential distribution: layer L gets 2^(-(L-1)) fraction
        fraction = 2.0 ** (-i)
        layer_budget = remaining_budget * fraction
        layer_budgets.append(layer_budget)
        remaining_budget -= layer_budget
    
    # Handle any rounding errors
    layer_budgets[-1] += remaining_budget
    
    # Create layer states
    layers = [
        LayerState(
            x=np.zeros(dimension),  # Start at origin
            b=budget
        )
        for budget in layer_budgets
    ]
    
    # Create layer configurations
    # Layer 1: reflex - fast, no branching
    # Layer 2: working - medium, branching allowed
    # Layer L: strategic - slow, full reflection
    layer_configs = {}
    timescale = 1.0
    
    for i in range(1, num_layers + 1):
        layer_configs[i] = LayerConfig(
            layer_id=i,
            timescale=timescale,
            branch_allowed=(i > 1),  # No branching at layer 1
            min_operator_cost=0.1 * (2 ** (i - 1)),  # Exponential cost scaling
            reserve_ratio=0.1
        )
        timescale *= timescale_ratio
    
    return StratifiedState(
        layers=layers,
        layer_configs=layer_configs
    )


def create_reflex_layer(dimension: int, budget: float) -> LayerState:
    """
    Create a Layer 1 (reflex) state - the fast, cheap control loop.
    
    This is the survival-critical layer that must never be starved.
    
    Args:
        dimension: Coordinate dimension
        budget: Initial budget
        
    Returns:
        LayerState for reflex layer
    """
    return LayerState(
        x=np.zeros(dimension),
        b=budget,
        curvature=0.0
    )


def create_strategic_layer(dimension: int, budget: float) -> LayerState:
    """
    Create a Layer L (strategic) state - the slow, expensive supervisor.
    
    This layer handles identity formation, goal planning, and reflection.
    
    Args:
        dimension: Coordinate dimension  
        budget: Initial budget (typically higher than reflex)
        
    Returns:
        LayerState for strategic layer
    """
    return LayerState(
        x=np.zeros(dimension),
        b=budget,
        curvature=0.0
    )


# Protocol for layer coupling implementations
class CouplingMaps:
    """
    Default implementation of the layer coupling maps.
    
    Φ⁽ˡ→ˡ⁻¹⁾: Budget delegation (downward flow)
    Ψ⁽ˡ⁻¹→ˡ⁾: Information abstraction (upward flow)
    """
    
    def __init__(self, abstraction_fn: Optional[Callable] = None):
        """
        Initialize coupling maps.
        
        Args:
            abstraction_fn: Optional custom abstraction function
        """
        self.abstraction_fn = abstraction_fn or self._default_abstraction
    
    def _default_abstraction(self, data: Dict) -> Dict:
        """
        Default information abstraction: summarize and compress.
        
        Args:
            data: Raw data from lower layer
            
        Returns:
            Abstracted summary
        """
        # Simple abstraction: just keep statistics
        abstracted = {}
        
        for key, value in data.items():
            if isinstance(value, (list, np.ndarray)):
                abstracted[f"{key}_mean"] = float(np.mean(value))
                abstracted[f"{key}_std"] = float(np.std(value))
            else:
                abstracted[key] = value
                
        return abstracted
    
    def delegate_budget(
        self, 
        from_state: LayerState, 
        to_state: LayerState, 
        amount: float,
        from_reserve_ratio: float = 0.1
    ) -> float:
        """
        Delegate budget from one layer state to another.
        
        Args:
            from_state: Source layer state
            to_state: Target layer state
            amount: Requested amount
            from_reserve_ratio: Fraction that must remain in source
            
        Returns:
            Actual amount delegated
        """
        min_reserve = from_state.b * from_reserve_ratio
        available = from_state.b - min_reserve
        
        actual = min(amount, available)
        
        if actual > 0:
            from_state.b -= actual
            to_state.b += actual
            
        return actual
    
    def abstract_receipts(
        self, 
        receipts: List[Dict], 
        target_layer: int
    ) -> Dict:
        """
        Abstract a batch of receipts from lower layer to upper layer.
        
        This implements the receipt roll-up: micro-receipts at Layer 1
        are composed into slabs and verified macroscopically.
        
        Args:
            receipts: List of receipts from lower layer
            target_layer: Target layer for abstraction
            
        Returns:
            Abstracted receipt summary
        """
        if not receipts:
            return {}
            
        # Aggregate statistics
        total_spend = sum(r.get('spend', 0) for r in receipts)
        total_defect = sum(r.get('defect', 0) for r in receipts)
        
        # Apply abstraction function
        summary = {
            'num_receipts': len(receipts),
            'total_spend': total_spend,
            'total_defect': total_defect,
            'target_layer': target_layer
        }
        
        # Layer-specific abstraction
        if target_layer >= 2:
            # Higher layers get more abstract summaries
            summary.update(self.abstraction_fn({'receipts': receipts}))
            
        return summary
