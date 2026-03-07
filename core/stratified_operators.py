"""
Stratified Operator Access for the GMI Universal Cognition Engine.

Module 17.3: Stratified Operator Access

The core constraint: Layer 1 (reflex) has no branching, higher layers allow branching.
This prevents combinatorial explosion at the fast (reflex) timescale.

Mathematical Specification:
  Layer 1 (Reflex):
    O_I = ∅  (no branching allowed)
    μ⁽¹⁾: minimum operator cost
  
  Layer l ≥ 2 (Reflective):
    O_I unrestricted
    μ⁽ˡ⁺¹⁾ ≫ μ⁽ˡ⁾  (exponential cost scaling)

EXPLICIT ASSUMPTION (Branch Evaluation Cost):
  σ_branch > 0
  
Branch evaluation itself consumes budget. Without this assumption,
the system could open arbitrarily many speculative nodes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
import numpy as np
from enum import Enum


class OperatorType(Enum):
    """Types of cognitive operators."""
    EXPLORE = "explore"      # Novelty search
    INFER = "infer"         # Gradient descent
    BRANCH = "branch"       # Speculative branching
    PRUNE = "prune"         # Hypothesis elimination
    ABSTRACT = "abstract"   # Information abstraction
    COMMIT = "commit"       # Policy commitment


@dataclass
class OperatorCost:
    """
    Cost structure for an operator.
    
    Attributes:
        sigma: Energy cost of computation
        kappa: Allowed defect budget (inequality violation tolerance)
        min_budget: Minimum budget required to use this operator
    """
    sigma: float
    kappa: float = 0.0
    min_budget: float = 0.0


@dataclass
class LayerOperatorConfig:
    """
    Configuration of operators allowed at a specific layer.
    
    Attributes:
        layer_id: Layer index (1 = reflex, L = strategic)
        allowed_operators: Set of operator types allowed at this layer
        min_operator_cost: Minimum sigma for any operator at this layer
        branch_cost_multiplier: Multiplier for branch cost at this layer
        max_branches: Maximum number of simultaneous branches
    """
    layer_id: int
    allowed_operators: Set[OperatorType]
    min_operator_cost: float
    branch_cost_multiplier: float = 1.0
    max_branches: int = 10


class BranchPricing:
    """
    Pricing mechanism for speculative branching.
    
    This implements the critical constraint that prevents combinatorial
    explosion: branch evaluation itself must consume budget (σ_branch > 0).
    
    Without this, the system could spawn infinite speculative branches
    since there's no cost to creating them.
    """
    
    def __init__(
        self,
        base_branch_cost: float = 1.0,
        exponential_scaling: float = 2.0,
        min_branch_cost: float = 0.1
    ):
        """
        Initialize branch pricing.
        
        Args:
            base_branch_cost: Base cost for a single branch
            exponential_scaling: How quickly branch costs scale with depth
            min_branch_cost: Minimum cost for any branch
        """
        self.base_branch_cost = base_branch_cost
        self.exponential_scaling = exponential_scaling
        self.min_branch_cost = min_branch_cost
    
    def compute_branch_cost(
        self,
        num_branches: int,
        branch_depth: int = 1
    ) -> float:
        """
        Compute the cost of opening N branches.
        
        EXPLICIT ASSUMPTION: σ_branch > 0
        
        This ensures branching has a positive cost, preventing
        infinite speculation.
        
        Args:
            num_branches: Number of branches to open
            branch_depth: Current depth of branching (higher = more expensive)
            
        Returns:
            Total cost of branching
        """
        # Cost scales exponentially with both count and depth
        depth_factor = self.exponential_scaling ** (branch_depth - 1)
        
        # Per-branch cost
        per_branch = max(
            self.min_branch_cost, 
            self.base_branch_cost * depth_factor
        )
        
        return num_branches * per_branch
    
    def compute_roi_threshold(
        self,
        num_branches: int,
        branch_depth: int = 1,
        expected_improvement: float = 0.0
    ) -> float:
        """
        Compute the minimum ROI required to justify branching.
        
        Args:
            num_branches: Number of branches being considered
            branch_depth: Current depth
            expected_improvement: Expected potential improvement
            
        Returns:
            Minimum ROI ratio required
        """
        cost = self.compute_branch_cost(num_branches, branch_depth)
        
        if cost <= 0:
            return 0.0
        
        if expected_improvement <= 0:
            return float('inf')  # Never branch if no improvement
        
        return cost / expected_improvement


class LayerOperatorRegistry:
    """
    Registry of operators restricted by layer.
    
    This implements the "combinatorial firewall":
    - Layer 1: No branching operators allowed
    - Layer l >= 2: Branching allowed with exponential pricing
    """
    
    # Class-level defaults for each layer type
    LAYER_CONFIGS: Dict[int, LayerOperatorConfig] = {
        1: LayerOperatorConfig(
            layer_id=1,
            allowed_operators={OperatorType.EXPLORE, OperatorType.INFER, OperatorType.PRUNE},
            min_operator_cost=0.1,
            branch_cost_multiplier=1.0,
            max_branches=0  # No branching at layer 1!
        ),
        2: LayerOperatorConfig(
            layer_id=2,
            allowed_operators={OperatorType.EXPLORE, OperatorType.INFER, OperatorType.BRANCH, 
                            OperatorType.PRUNE, OperatorType.ABSTRACT},
            min_operator_cost=0.2,
            branch_cost_multiplier=2.0,
            max_branches=5
        ),
    }
    
    def __init__(
        self,
        custom_configs: Optional[Dict[int, LayerOperatorConfig]] = None,
        branch_pricing: Optional[BranchPricing] = None
    ):
        """
        Initialize the registry.
        
        Args:
            custom_configs: Override layer configs
            branch_pricing: Branch pricing mechanism
        """
        # Start with defaults
        self.configs = dict(self.LAYER_CONFIGS)
        
        # Apply custom configs
        if custom_configs:
            self.configs.update(custom_configs)
        
        # Branch pricing
        self.branch_pricing = branch_pricing or BranchPricing()
    
    def get_config(self, layer_id: int) -> LayerOperatorConfig:
        """
        Get operator config for a layer.
        
        Args:
            layer_id: Layer index
            
        Returns:
            Configuration for that layer
        """
        if layer_id not in self.configs:
            # Auto-generate for higher layers (exponential scaling)
            base_config = self.configs[2]
            scale_factor = 2.0 ** (layer_id - 2)
            
            return LayerOperatorConfig(
                layer_id=layer_id,
                allowed_operators=base_config.allowed_operators | {OperatorType.COMMIT},
                min_operator_cost=base_config.min_operator_cost * scale_factor,
                branch_cost_multiplier=base_config.branch_cost_multiplier * scale_factor,
                max_branches=base_config.max_branches * 2
            )
        
        return self.configs[layer_id]
    
    def is_operator_allowed(
        self, 
        layer_id: int, 
        operator: OperatorType
    ) -> bool:
        """
        Check if an operator is allowed at a given layer.
        
        Args:
            layer_id: Layer to check
            operator: Operator type
            
        Returns:
            True if allowed
        """
        config = self.get_config(layer_id)
        return operator in config.allowed_operators
    
    def can_branch(self, layer_id: int) -> bool:
        """
        Check if branching is allowed at a layer.
        
        This is the critical check that prevents combinatorial explosion
        at Layer 1.
        
        Args:
            layer_id: Layer to check
            
        Returns:
            True if branching allowed
        """
        config = self.get_config(layer_id)
        return config.max_branches > 0
    
    def get_branch_cost(
        self,
        layer_id: int,
        num_branches: int,
        branch_depth: int = 1
    ) -> float:
        """
        Get the cost of branching at a layer.
        
        EXPLICIT: Returns σ_branch > 0
        
        Args:
            layer_id: Layer requesting branches
            num_branches: Number of branches
            branch_depth: Current branch depth
            
        Returns:
            Cost (guaranteed > 0)
        """
        if not self.can_branch(layer_id):
            return float('inf')  # Cannot branch at this layer
        
        config = self.get_config(layer_id)
        
        # Compute base cost
        base_cost = self.branch_pricing.compute_branch_cost(
            num_branches, 
            branch_depth
        )
        
        # Apply layer-specific multiplier
        return base_cost * config.branch_cost_multiplier
    
    def check_branch_admissible(
        self,
        layer_id: int,
        num_branches: int,
        available_budget: float,
        expected_improvement: float = 0.0
    ) -> Tuple[bool, str]:
        """
        Check if branching is admissible at a layer.
        
        Branching is admissible if:
        1. Branching is allowed at this layer
        2. The layer has enough budget
        3. Expected ROI exceeds threshold
        
        Args:
            layer_id: Layer requesting branches
            num_branches: Number of branches
            available_budget: Budget available at this layer
            expected_improvement: Expected potential improvement
            
        Returns:
            Tuple of (is_admissible, reason)
        """
        config = self.get_config(layer_id)
        
        # Check 1: Is branching allowed?
        if not self.can_branch(layer_id):
            return False, f"Layer {layer_id} does not allow branching"
        
        # Check 2: Is there enough budget?
        if num_branches > config.max_branches:
            return False, f"Exceeds max branches ({config.max_branches})"
        
        # Check 3: Can afford the cost?
        branch_cost = self.get_branch_cost(layer_id, num_branches)
        
        if branch_cost > available_budget:
            return False, f"Insufficient budget: need {branch_cost}, have {available_budget}"
        
        # Check 4: ROI threshold
        if expected_improvement > 0:
            roi = expected_improvement / branch_cost
            min_roi = self.branch_pricing.compute_roi_threshold(
                num_branches, 1, expected_improvement
            )
            
            if roi < min_roi:
                return False, f"ROI {roi} below threshold {min_roi}"
        
        return True, "Admissible"


@dataclass
class StratifiedOperator:
    """
    An operator annotated with layer information.
    
    This allows the system to track which layer an operation
    belongs to, enabling proper routing and cost accounting.
    """
    op_type: OperatorType
    layer_id: int
    sigma: float  # Energy cost
    kappa: float = 0.0  # Defect allowance
    pi_func: Optional[Callable] = None  # Transition function
    
    def __post_init__(self):
        """Validate the operator."""
        if self.sigma < 0:
            raise ValueError(f"Operator sigma must be non-negative, got {self.sigma}")
        if self.layer_id < 1:
            raise ValueError(f"Layer ID must be >= 1, got {self.layer_id}")


def create_layer_operators(
    layer_id: int,
    dimension: int,
    registry: Optional[LayerOperatorRegistry] = None
) -> List[StratifiedOperator]:
    """
    Create standard operators for a layer.
    
    Args:
        layer_id: Layer to create operators for
        dimension: State dimension
        registry: Operator registry (uses default if None)
        
    Returns:
        List of available operators
    """
    registry = registry or LayerOperatorRegistry()
    config = registry.get_config(layer_id)
    
    operators = []
    
    # EXPLORE: Random perturbation
    if OperatorType.EXPLORE in config.allowed_operators:
        sigma = max(config.min_operator_cost, 1.0)
        operators.append(StratifiedOperator(
            op_type=OperatorType.EXPLORE,
            layer_id=layer_id,
            sigma=sigma,
            kappa=sigma * 2,  # Higher defect tolerance for exploration
            pi_func=lambda x: x + np.random.uniform(0.5, 1.5, size=len(x))
        ))
    
    # INFER: Gradient descent
    if OperatorType.INFER in config.allowed_operators:
        sigma = config.min_operator_cost
        operators.append(StratifiedOperator(
            op_type=OperatorType.INFER,
            layer_id=layer_id,
            sigma=sigma,
            kappa=sigma * 0.5,  # Low defect tolerance for inference
            pi_func=lambda x: x - 0.1 * x
        ))
    
    # BRANCH: Speculative branching (only at layer >= 2)
    if OperatorType.BRANCH in config.allowed_operators:
        branch_cost = registry.get_branch_cost(layer_id, 1)
        operators.append(StratifiedOperator(
            op_type=OperatorType.BRANCH,
            layer_id=layer_id,
            sigma=branch_cost,  # This is σ_branch > 0
            kappa=0.0,
            pi_func=None  # Branching doesn't have a simple transition
        ))
    
    return operators


def verify_no_branching_at_layer_1(operators: List[StratifiedOperator]) -> bool:
    """
    Verify that Layer 1 has no branching operators.
    
    This is a critical invariant for the stratified architecture.
    
    Args:
        operators: List of operators to check
        
    Returns:
        True if invariant is satisfied
    """
    for op in operators:
        if op.layer_id == 1 and op.op_type == OperatorType.BRANCH:
            return False
    return True


def compute_exponential_cost_scaling(
    base_cost: float,
    layer: int,
    scaling_factor: float = 2.0
) -> float:
    """
    Compute exponential cost scaling between layers.
    
    μ⁽ˡ⁺¹⁾ ≫ μ⁽ˡ⁾
    
    This ensures higher-order reflection is rare.
    
    Args:
        base_cost: Cost at layer 1
        layer: Target layer
        scaling_factor: Exponential scaling factor
        
    Returns:
        Cost at the target layer
    """
    return base_cost * (scaling_factor ** (layer - 1))
