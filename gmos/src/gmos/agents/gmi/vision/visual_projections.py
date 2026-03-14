"""
Visual Projections for GMI Resonant Field Framework.

Implements the visual I/O operators per the mathematical specification:

Eye operator (vision ingress):
    P_eye: V → ξ_sens_vis
    
Internal imagery (imagination):
    I_int = G_imag(ξ_mem, ξ_task, ξ_affect, ξ_policy, ξ_coh)
    
Visual egress (display):
    G_vis_out: (ξ_scene, ξ_task, ξ_affect, ξ_shell) → V_out

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from typing import Optional, Tuple


class EyeOperator:
    """
    Visual sensory projection: P_eye: V → ξ_sens_vis
    
    The eyes are NOT a direct peek at reality. They are a lawful projection
    from the visual field into the sensory manifold.
    
    Per spec §10: This is the eye-version of the ear operator, but now
    the sensory projection acts on a spatial field, not a mere octave vector.
    """
    
    def __init__(
        self,
        field_height: int = 32,
        field_width: int = 32,
        num_octaves: int = 88,
        sensory_dim: int = 32
    ):
        """
        Initialize eye operator.
        
        Args:
            field_height: Visual field height
            field_width: Visual field width
            num_octaves: Number of octaves
            sensory_dim: Output sensory dimension
        """
        self.H = field_height
        self.W = field_width
        self.N = num_octaves
        self.sensory_dim = sensory_dim
        
        # Learnable projection from visual field to sensory
        field_dim = field_height * field_width * num_octaves
        self.P_eye = np.random.randn(sensory_dim, field_dim) * 0.01
    
    def __call__(
        self, 
        V: np.ndarray,
        ctx_modulation: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Project visual field to sensory manifold.
        
        P_eye: V → ξ_sens_vis
        
        Args:
            V: Visual field (H, W, N)
            ctx_modulation: Optional context modulation
            
        Returns:
            Sensory projection
        """
        # Flatten visual field
        V_flat = V.flatten()
        
        # Project to sensory
        sensory = self.P_eye @ V_flat
        
        # Add context modulation if provided
        if ctx_modulation is not None:
            sensory = sensory + ctx_modulation
        
        return sensory
    
    def compute_bound(self) -> float:
        """
        Get operator norm bound.
        
        Returns:
            Operator norm
        """
        return np.linalg.norm(self.P_eye, ord=2)


class ImageryOperator:
    """
    Internal imagery operator: G_imag
    
    This generates internal visual thought without external input.
    
    Internal vision is defined as:
        I_ext ≈ 0, I_int ≠ 0
        
    This allows:
    - recalling a face
    - simulating a route
    - imagining the unseen side of an object
    - planning a path through a maze
    """
    
    def __init__(
        self,
        field_height: int = 32,
        field_width: int = 32,
        num_octaves: int = 88,
        mem_dim: int = 16,
        task_dim: int = 16,
        affect_dim: int = 8,
        policy_dim: int = 16,
        coh_dim: int = 3
    ):
        """
        Initialize imagery operator.
        
        Args:
            field_height: Visual field height
            field_width: Visual field width
            num_octaves: Number of octaves
            mem_dim: Memory dimension
            task_dim: Task dimension
            affect_dim: Affect dimension
            policy_dim: Policy dimension
            coh_dim: Coherence dimension
        """
        self.H = field_height
        self.W = field_width
        self.N = num_octaves
        
        # Total input dimension
        input_dim = mem_dim + task_dim + affect_dim + policy_dim + coh_dim
        
        # Learnable mappings for different octave bands
        # Low octaves: global structure from memory
        self.W_mem = np.random.randn(field_height * field_width * 10, mem_dim) * 0.01
        
        # Mid octaves: task-relevant patterns
        self.W_task = np.random.randn(field_height * field_width * 30, task_dim) * 0.01
        
        # High octaves: detail from affect
        self.W_affect = np.random.randn(field_height * field_width * 48, affect_dim) * 0.01
        
        # Policy and coherence modulation
        self.W_policy = np.random.randn(input_dim, 1) * 0.01
    
    def __call__(
        self,
        xi_mem: np.ndarray,
        xi_task: np.ndarray,
        xi_affect: np.ndarray,
        xi_policy: np.ndarray,
        xi_coh: np.ndarray
    ) -> np.ndarray:
        """
        Generate internal visual imagery.
        
        I_int = G_imag(mem, task, affect, policy, coh)
        
        Args:
            xi_mem: Memory state
            xi_task: Task state
            xi_affect: Affective state
            xi_policy: Policy state
            xi_coh: Coherence state
            
        Returns:
            Visual field (H, W, N)
        """
        H, W, N = self.H, self.W, self.N
        
        # Initialize output
        V_int = np.zeros((H, W, N))
        
        # Memory contribution (low octaves)
        if len(xi_mem) > 0:
            mem_flat = self.W_mem @ xi_mem
            V_int[:, :, :10] = mem_flat.reshape(H, W, 10)
        
        # Task contribution (mid octaves)
        if len(xi_task) > 0:
            task_flat = self.W_task @ xi_task
            V_int[:, :, 10:40] = task_flat.reshape(H, W, 30)
        
        # Affect contribution (high octaves)
        if len(xi_affect) > 0:
            affect_flat = self.W_affect @ xi_affect
            V_int[:, :, 40:] = affect_flat.reshape(H, W, 48)
        
        # Policy modulation - compute a scalar from all inputs
        combined = np.concatenate([xi_mem, xi_task, xi_affect, xi_policy, xi_coh])
        policy_mod = np.sum(combined) / len(combined)  # Simple average
        V_int = V_int * (1.0 + policy_mod)
        
        return V_int
    
    def compute_imagery_cost(self, V_int: np.ndarray) -> float:
        """
        Compute the metabolic cost of internal imagery.
        
        Rich internal imagery should consume budget.
        
        Args:
            V_int: Generated visual field
            
        Returns:
            Imagery cost
        """
        # Energy of generated imagery
        energy = 0.5 * np.sum(V_int ** 2)
        
        return energy


class VisualEgressOperator:
    """
    Visual egress operator: G_vis_out
    
    This generates outward visual expression (display, rendering, etc.)
    
    This is the visual analogue of the voice.
    """
    
    def __init__(
        self,
        field_height: int = 32,
        field_width: int = 32,
        num_octaves: int = 88,
        scene_dim: int = 64,
        task_dim: int = 16,
        affect_dim: int = 8,
        shell_dim: int = 16
    ):
        """
        Initialize visual egress operator.
        
        Args:
            field_height: Visual field height
            field_width: Visual field width
            num_octaves: Number of octaves
            scene_dim: Scene representation dimension
            task_dim: Task dimension
            affect_dim: Affect dimension
            shell_dim: Shell dimension
        """
        self.H = field_height
        self.W = field_width
        self.N = num_octaves
        
        # Input dimension
        input_dim = scene_dim + task_dim + affect_dim + shell_dim
        
        # Learnable generator
        field_dim = field_height * field_width * num_octaves
        self.W_generator = np.random.randn(field_dim, input_dim) * 0.01
    
    def __call__(
        self,
        xi_scene: np.ndarray,
        xi_task: np.ndarray,
        xi_affect: np.ndarray,
        xi_shell: np.ndarray
    ) -> np.ndarray:
        """
        Generate visual output.
        
        G_vis_out: (scene, task, affect, shell) → V_out
        
        Args:
            xi_scene: Scene representation
            xi_task: Task state
            xi_affect: Affective state
            xi_shell: Shell state
            
        Returns:
            Visual output field (H, W, N)
        """
        # Combine inputs
        combined = np.concatenate([
            xi_scene[:min(len(xi_scene), 64)],  # Truncate scene to expected dim
            xi_task,
            xi_affect,
            xi_shell
        ])
        
        # Pad if needed
        if len(combined) < 64 + 16 + 8 + 16:
            combined = np.pad(combined, (0, 64 + 16 + 8 + 16 - len(combined)))
        
        # Generate visual field
        V_flat = self.W_generator @ combined
        V_out = V_flat.reshape(self.H, self.W, self.N)
        
        return V_out
    
    def compute_egress_cost(self, V_out: np.ndarray) -> float:
        """
        Compute the cost of visual expression.
        
        Args:
            V_out: Output visual field
            
        Returns:
            Egress cost
        """
        # Energy of output
        energy = 0.5 * np.sum(V_out ** 2)
        
        # Complexity cost (high frequency content)
        diffs = np.diff(V_out, axis=2)
        complexity = np.sum(diffs ** 2)
        
        return energy + 0.1 * complexity


class VisualBudgetCost:
    """
    Visual contribution to budget.
    
    Σ_vis = λ₁ * E_vis + λ₂ * E_bind + λ₃ * E_persist + λ₄ * E_mismatch
    
    This prevents infinite hallucinated megapixel cathedrals from blooming for free.
    """
    
    def __init__(
        self,
        lambda_field: float = 1.0,
        lambda_binding: float = 1.0,
        lambda_persist: float = 1.0,
        lambda_mismatch: float = 1.0
    ):
        """Initialize visual budget cost."""
        self.lambda_field = lambda_field
        self.lambda_binding = lambda_binding
        self.lambda_persist = lambda_persist
        self.lambda_mismatch = lambda_mismatch
    
    def compute_cost(
        self,
        V: np.ndarray,
        scene_binding,
        V_prev: Optional[np.ndarray] = None,
        V_pred: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute visual budget cost.
        
        Args:
            V: Current visual field
            scene_binding: SceneBindingFunctional instance
            V_prev: Previous visual field
            V_pred: Predicted visual field
            
        Returns:
            Total cost
        """
        # Field energy
        E_field = 0.5 * np.sum(V ** 2)
        
        # Binding
        E_bind = scene_binding.compute_cross_scale_binding(V)
        
        # Persistence
        E_persist = 0.0
        if V_prev is not None:
            E_persist = scene_binding.compute_temporal_persistence(V, V_prev)
        
        # Mismatch
        E_mismatch = 0.0
        if V_pred is not None:
            E_mismatch = scene_binding.compute_prediction_mismatch(V, V_pred)
        
        return (
            self.lambda_field * E_field +
            self.lambda_binding * E_bind +
            self.lambda_persist * E_persist +
            self.lambda_mismatch * E_mismatch
        )


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing visual projections...")
    
    # Test eye operator
    print("\nTesting eye operator...")
    eye = EyeOperator(field_height=32, field_width=32, num_octaves=88, sensory_dim=32)
    V = np.random.randn(32, 32, 88) * 0.1
    sensory = eye(V)
    print(f"  Input shape: {V.shape}")
    print(f"  Output shape: {sensory.shape}")
    print(f"  Operator bound: {eye.compute_bound():.4f}")
    
    # Test imagery operator
    print("\nTesting imagery operator...")
    imagery = ImageryOperator(
        field_height=32, field_width=32, num_octaves=88,
        mem_dim=16, task_dim=16, affect_dim=8, policy_dim=16, coh_dim=3
    )
    
    xi_mem = np.random.randn(16) * 0.5
    xi_task = np.random.randn(16) * 0.5
    xi_affect = np.random.randn(8) * 0.3
    xi_policy = np.random.randn(16) * 0.2
    xi_coh = np.array([0.0, 0.0, 1.0])
    
    V_int = imagery(xi_mem, xi_task, xi_affect, xi_policy, xi_coh)
    print(f"  Imagery output shape: {V_int.shape}")
    print(f"  Imagery cost: {imagery.compute_imagery_cost(V_int):.4f}")
    
    # Test visual egress
    print("\nTesting visual egress...")
    egress = VisualEgressOperator(field_height=32, field_width=32, num_octaves=88)
    
    xi_scene = np.random.randn(64)
    xi_shell = np.random.randn(16)
    
    V_out = egress(xi_scene, xi_task, xi_affect, xi_shell)
    print(f"  Egress output shape: {V_out.shape}")
    print(f"  Egress cost: {egress.compute_egress_cost(V_out):.4f}")
    
    # Test visual budget cost
    print("\nTesting visual budget cost...")
    from gmos.agents.gmi.vision.scene_binding import SceneBindingFunctional
    
    scene_binding = SceneBindingFunctional()
    budget_cost = VisualBudgetCost()
    
    cost = budget_cost.compute_cost(V, scene_binding)
    print(f"  Budget cost: {cost:.4f}")
    
    print("\nAll tests passed!")
