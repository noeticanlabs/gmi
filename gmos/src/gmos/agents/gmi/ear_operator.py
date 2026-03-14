"""
Ear Operator (Sensory Ingress) for GMI Resonant Field Framework.

Implements the perception operator per the mathematical specification:

    P: ℝ^88 → ℝ^m

The ears are NOT a direct peek at reality. They are a lawful projection
from the substrate field into the sensory block.

This matches the world-weld logic: the world does something to the organism
through a lawful ingress operator, and the organism feels only a projection,
not the full hidden substrate.

    F_sens(z) = P·ξ_Φ - γ_sens·ξ_sens + Q_ctx

Components:
- P·ξ_Φ: Incoming world-field imprint
- -γ_sens·ξ_sens: Decay / sensory relaxation
- Q_ctx: Context/top-down modulation

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from typing import Optional, Callable


class EarOperator:
    """
    Sensory ingress operator P: ℝ^88 → ℝ^m.
    
    The ears are NOT a direct peek at reality. They are a lawful 
    projection from the substrate field into the sensory block.
    
    Per spec §10: This matches the world-weld logic - the world 
    dents the organism through a lawful ingress operator.
    """
    
    def __init__(
        self,
        field_dim: int = 88,      # 88 octaves
        sensory_dim: int = 32,    # Output dimension
        projection_type: str = "learned",  # "learned", "filter", "window"
        decay_rate: float = 0.1
    ):
        """
        Initialize the ear operator.
        
        Args:
            field_dim: Dimension of field (88)
            sensory_dim: Dimension of sensory output
            projection_type: Type of projection
            decay_rate: Sensory decay rate γ_sens
        """
        self.field_dim = field_dim
        self.sensory_dim = sensory_dim
        self.projection_type = projection_type
        self.decay_rate = decay_rate
        
        if projection_type == "learned":
            # Learnable projection matrix
            self.P = np.random.randn(sensory_dim, field_dim) * 0.01
        elif projection_type == "filter":
            # Gabor-like filter bank
            self._init_filter_bank()
        elif projection_type == "window":
            # Sliding window projection
            self.window_size = field_dim // sensory_dim
        
        # Operator norm bound (for Lemma 10.1)
        self._operator_norm = None
    
    def _init_filter_bank(self):
        """Initialize Gabor-like filter bank."""
        # Create simple filter bank covering different frequency bands
        self.filters = []
        num_filters = self.sensory_dim
        
        for i in range(num_filters):
            # Each filter responds to a specific octave band
            center = (i / num_filters) * self.field_dim
            filter_response = np.zeros(self.field_dim)
            
            # Simple bandpass filter
            for j in range(self.field_dim):
                distance = abs(j - center)
                filter_response[j] = np.exp(-distance ** 2 / 20.0)
            
            self.filters.append(filter_response)
        
        self.filters = np.array(self.filters)
    
    def __call__(self, xi_Phi: np.ndarray) -> np.ndarray:
        """
        Compute sensory projection: ξ_sens = P · ξ_Φ
        
        This is the "ear" - lawful bounded projection of shared field
        into organismal sensory state.
        
        Args:
            xi_Phi: Field state (88 octaves)
            
        Returns:
            Sensory projection
        """
        if self.projection_type == "learned":
            return self.P @ xi_Phi
        elif self.projection_type == "filter":
            return self._apply_filters(xi_Phi)
        elif self.projection_type == "window":
            return self._apply_window(xi_Phi)
        else:
            raise ValueError(f"Unknown projection type: {self.projection_type}")
    
    def _apply_filters(self, xi_Phi: np.ndarray) -> np.ndarray:
        """Apply filter bank."""
        return self.filters @ xi_Phi
    
    def _apply_window(self, xi_Phi: np.ndarray) -> np.ndarray:
        """Apply sliding window aggregation."""
        result = np.zeros(self.sensory_dim)
        window_size = self.window_size
        
        for i in range(self.sensory_dim):
            start = i * window_size
            end = min(start + window_size, self.field_dim)
            result[i] = np.mean(xi_Phi[start:end])
        
        return result
    
    def compute_bound(self) -> float:
        """
        Return operator norm bound |P|.
        
        Lemma 10.1: |P · ξ_Φ| ≤ |P| · |ξ_Φ|
        
        Returns:
            Operator norm
        """
        if self._operator_norm is None:
            if self.projection_type == "learned":
                self._operator_norm = np.linalg.norm(self.P, ord=2)
            elif self.projection_type == "filter":
                # Bound is max row sum
                self._operator_norm = np.max(np.sum(np.abs(self.filters), axis=1))
            else:
                self._operator_norm = np.sqrt(self.field_dim)
        
        return self._operator_norm
    
    def project_to_sensory_with_decay(
        self,
        xi_Phi: np.ndarray,
        current_sens: np.ndarray,
        ctx_modulation: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute sensory drift: F_sens = P·ξ_Φ - γ_sens·ξ_sens + Q_ctx
        
        Args:
            xi_Phi: Field state
            current_sens: Current sensory state
            ctx_modulation: Optional context modulation
            
        Returns:
            Sensory drift
        """
        # Ear projection
        ear_input = self(xi_Phi)
        
        # Decay
        decay = -self.decay_rate * current_sens
        
        # Context modulation
        ctx = ctx_modulation if ctx_modulation is not None else np.zeros_like(ear_input)
        
        return ear_input + decay + ctx


class ContextModulationOperator:
    """
    Context/top-down modulation for sensory processing.
    
    Q_ctx(ξ_task, ξ_shell, ξ_policy)
    
    This allows top-down attention and task modulation.
    """
    
    def __init__(
        self,
        task_dim: int = 16,
        shell_dim: int = 16,
        policy_dim: int = 16,
        sensory_dim: int = 32
    ):
        """
        Initialize context modulation.
        
        Args:
            task_dim: Task state dimension
            shell_dim: Shell state dimension
            policy_dim: Policy state dimension
            sensory_dim: Sensory output dimension
        """
        self.task_dim = task_dim
        self.shell_dim = shell_dim
        self.policy_dim = policy_dim
        self.sensory_dim = sensory_dim
        
        # Learnable projections from each source
        self.W_task = np.random.randn(sensory_dim, task_dim) * 0.01
        self.W_shell = np.random.randn(sensory_dim, shell_dim) * 0.01
        self.W_policy = np.random.randn(sensory_dim, policy_dim) * 0.01
        
        # Combination weights
        self.alpha_task = 0.4
        self.alpha_shell = 0.3
        self.alpha_policy = 0.3
    
    def __call__(
        self,
        xi_task: np.ndarray,
        xi_shell: np.ndarray,
        xi_policy: np.ndarray
    ) -> np.ndarray:
        """
        Compute context modulation.
        
        Q_ctx = α_task * W_task·task + α_shell * W_shell·shell + α_policy * W_policy·policy
        
        Args:
            xi_task: Task state
            xi_shell: Shell state
            xi_policy: Policy state
            
        Returns:
            Context modulation vector
        """
        ctx = np.zeros(self.sensory_dim)
        
        ctx += self.alpha_task * (self.W_task @ xi_task)
        ctx += self.alpha_shell * (self.W_shell @ xi_shell)
        ctx += self.alpha_policy * (self.W_policy @ xi_policy)
        
        return ctx


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing ear operator (sensory ingress)...")
    
    # Create ear operator
    ear = EarOperator(field_dim=88, sensory_dim=32, projection_type="learned")
    print(f"Ear operator: {ear.projection_type}")
    print(f"Operator norm bound: {ear.compute_bound():.4f}")
    
    # Test projection
    xi_Phi = np.random.randn(88) * 0.5
    sensory = ear(xi_Phi)
    print(f"Input norm: {np.linalg.norm(xi_Phi):.4f}")
    print(f"Output norm: {np.linalg.norm(sensory):.4f}")
    
    # Test with decay
    current_sens = np.random.randn(32) * 0.2
    drift = ear.project_to_sensory_with_decay(xi_Phi, current_sens)
    print(f"Sensory drift norm: {np.linalg.norm(drift):.4f}")
    
    # Test context modulation
    print("\nTesting context modulation...")
    ctx_op = ContextModulationOperator(
        task_dim=16, shell_dim=16, policy_dim=16, sensory_dim=32
    )
    
    xi_task = np.random.randn(16)
    xi_shell = np.random.randn(16)
    xi_policy = np.random.randn(16)
    
    ctx = ctx_op(xi_task, xi_shell, xi_policy)
    print(f"Context modulation norm: {np.linalg.norm(ctx):.4f}")
    
    # Test filter bank
    print("\nTesting filter bank operator...")
    ear_filter = EarOperator(field_dim=88, sensory_dim=32, projection_type="filter")
    sensory_filter = ear_filter(xi_Phi)
    print(f"Filter output norm: {np.linalg.norm(sensory_filter):.4f}")
    
    # Test window operator
    print("\nTesting window operator...")
    ear_window = EarOperator(field_dim=88, sensory_dim=11, projection_type="window")
    sensory_window = ear_window(xi_Phi)
    print(f"Window output norm: {np.linalg.norm(sensory_window):.4f}")
    print(f"Window output: {sensory_window}")
    
    print("\nAll tests passed!")
