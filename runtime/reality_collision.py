"""
Reality Collision for the GMI Universal Cognition Engine.

Module 15.4-15.5: The Reality Collision and Prediction Error

Handles:
- Reality response from environment
- Prediction error computation
- Structural scarring (curvature update)
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np

from runtime.policy_selection import CommitmentReceipt, Branch


@dataclass
class RealityResponse:
    """
    Response from the environment after action execution.
    
    Contains:
    - external_receipt_id: External validation receipt
    - actual_gain: G_actual from environment
    - validated: Whether the response was validated
    """
    external_receipt_id: str
    actual_gain: float
    validated: bool = True
    
    # Additional metadata
    timestamp: float = field(default_factory=time.time)
    environment_type: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps({
            'external_receipt_id': self.external_receipt_id,
            'actual_gain': round(self.actual_gain, 6),
            'validated': self.validated,
            'timestamp': self.timestamp,
            'environment_type': self.environment_type,
            'metadata': self.metadata
        }, sort_keys=True)
    
    def hash(self) -> str:
        return hashlib.sha256(self.to_json().encode()).hexdigest()


@dataclass
class CollisionResult:
    """
    Result of processing a reality collision.
    
    Contains:
    - prediction_error: Δ_err = |Γ(B*) - G_actual|
    - curvature_update: How much curvature changed
    - metadata: Additional info
    """
    prediction_error: float
    curvature_update: float
    
    # Details
    expected_gain: float
    actual_gain: float
    state_hash: str
    branch_id: str
    timestamp: float = field(default_factory=time.time)
    
    @property
    def over_prediction(self) -> bool:
        """Did we overestimate gain?"""
        return self.expected_gain > self.actual_gain
    
    @property
    def under_prediction(self) -> bool:
        """Did we underestimate gain?"""
        return self.expected_gain < self.actual_gain


class RealityCollision:
    """
    Handles the reality collision event.
    
    Process:
    1. Receive reality response from environment
    2. Compare to expected gain from commitment
    3. Compute prediction error
    4. Update passive structural memory (curvature/scar)
    
    The prediction error acts as a forcing term on curvature:
    ∂_t C(x, t) ∝ Δ_err - βC + D_C ΔC
    """
    
    def __init__(self, memory_manifold: Optional[Any] = None):
        """
        Initialize reality collision handler.
        
        Args:
            memory_manifold: Optional MemoryManifold for curvature updates
        """
        self.memory = memory_manifold
        self.collision_history: list = []
        
        # Scarring parameters
        self.scar_beta = 0.1  # Decay rate
        self.scar_strength = 1.0  # How much error affects curvature
    
    def process(
        self,
        commitment: CommitmentReceipt,
        response: RealityResponse,
        state_position: Optional[np.ndarray] = None
    ) -> CollisionResult:
        """
        Process reality response and update structural memory.
        
        Args:
            commitment: The commitment receipt
            response: Response from environment
            state_position: Current state position for curvature update
            
        Returns:
            CollisionResult
        """
        # Compute prediction error
        prediction_error = abs(
            commitment.expected_gain - response.actual_gain
        )
        
        # Update curvature if memory available
        curvature_update = 0.0
        if self.memory is not None and state_position is not None:
            curvature_update = self._update_curvature(
                state_position, 
                prediction_error
            )
        
        # Create result
        result = CollisionResult(
            prediction_error=prediction_error,
            curvature_update=curvature_update,
            expected_gain=commitment.expected_gain,
            actual_gain=response.actual_gain,
            state_hash=commitment.state_hash_before,
            branch_id=commitment.selected_branch_id
        )
        
        # Record
        self.collision_history.append(result)
        
        return result
    
    def _update_curvature(
        self, 
        position: np.ndarray, 
        error: float
    ) -> float:
        """
        Update passive structural memory (curvature/scar).
        
        ∂_t C(x, t) ∝ Δ_err - βC + D_C ΔC
        
        When prediction fails, the manifold "scars" - increasing resistance
        in that region of state space.
        """
        if self.memory is None:
            return 0.0
        
        # Apply scar at this position
        # Error increases curvature (makes region harder to traverse)
        scar_magnitude = self.scar_strength * error
        
        # Write scar to memory
        self.memory.write_scar(position, scar_magnitude)
        
        # Apply decay to existing scars
        # (This would be done in memory.step() normally)
        
        return scar_magnitude
    
    def get_prediction_accuracy(self) -> Dict[str, float]:
        """
        Get statistics on prediction accuracy.
        
        Returns:
            Dict with accuracy metrics
        """
        if not self.collision_history:
            return {'message': 'No collisions recorded'}
        
        errors = [c.prediction_error for c in self.collision_history]
        over = sum(1 for c in self.collision_history if c.over_prediction)
        under = sum(1 for c in self.collision_history if c.under_prediction)
        
        return {
            'total_collisions': len(self.collision_history),
            'avg_error': sum(errors) / len(errors),
            'max_error': max(errors),
            'min_error': min(errors),
            'over_predictions': over,
            'under_predictions': under,
            'accuracy_rate': (len(errors) - max(over, under)) / len(errors)
        }
    
    def get_recent_scarring(self, n: int = 5) -> list:
        """Get n most recent scarring events."""
        return self.collision_history[-n:]


@dataclass
class CycleBudgetChange:
    """
    Result of computing the full metabolic cycle budget change.
    
    Theorem 15.1: Δb_cycle = G_actual - D_phys(u*) - C_commit - Σ Σ(B_i)
    """
    actual_gain: float
    physical_cost: float
    commitment_cost: float
    total_branch_cost: float
    
    @property
    def net_change(self) -> float:
        """Δb_cycle"""
        return (
            self.actual_gain 
            - self.physical_cost 
            - self.commitment_cost 
            - self.total_branch_cost
        )
    
    @property
    def is_profitable(self) -> bool:
        """Did we make net progress?"""
        return self.net_change > 0
    
    def __repr__(self) -> str:
        return (
            f"CycleBudgetChange("
            f"gain={self.actual_gain:.2f}, "
            f"cost={self.physical_cost + self.commitment_cost + self.total_branch_cost:.2f}, "
            f"net={self.net_change:+.2f})"
        )


def compute_cycle_budget(
    response: RealityResponse,
    physical_cost: float,
    commitment_cost: float,
    total_branch_cost: float
) -> CycleBudgetChange:
    """
    Compute the full metabolic cycle budget change.
    
    Theorem 15.1: The Full Metabolic Cycle Identity
    
    Δb_cycle = G_actual - D_phys(u*) - C_commit - Σ Σ(B_i)
    
    Args:
        response: Reality response with actual gain
        physical_cost: Cost of physical action
        commitment_cost: Cost of writing commitment receipt
        total_branch_cost: Total simulation cost of all branches
        
    Returns:
        CycleBudgetChange
    """
    return CycleBudgetChange(
        actual_gain=response.actual_gain,
        physical_cost=physical_cost,
        commitment_cost=commitment_cost,
        total_branch_cost=total_branch_cost
    )
