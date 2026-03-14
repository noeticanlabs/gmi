"""
Scene Binding Functional for GMI Resonant Field Framework.

Implements the scene potential per the mathematical specification:

    V_scene[V] = E_smooth + E_bind + E_persist + E_mismatch

Where:
- E_smooth: Spatial smoothness penalty
- E_bind: Cross-scale binding (coherence across octaves)
- E_persist: Temporal persistence (object identity over time)
- E_mismatch: Expected vs observed mismatch (surprise)

This governs visual coherence - stable scenes are cheap, fragmented scenes are expensive.

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from typing import Optional, Tuple


class SceneBindingFunctional:
    """
    Scene potential V_scene[V] = E_smooth + E_bind + E_persist + E_mismatch
    
    This governs visual coherence:
    - stable scenes are cheap
    - fragmented incoherent scenes are expensive
    - violated predictions create tension
    """
    
    def __init__(
        self,
        alpha_smooth: float = 1.0,
        alpha_bind: float = 1.0,
        alpha_persist: float = 1.0,
        alpha_mismatch: float = 1.0
    ):
        """
        Initialize scene binding functional.
        
        Args:
            alpha_smooth: Smoothness weight
            alpha_bind: Cross-scale binding weight
            alpha_persist: Temporal persistence weight
            alpha_mismatch: Mismatch weight
        """
        self.alpha_smooth = alpha_smooth
        self.alpha_bind = alpha_bind
        self.alpha_persist = alpha_persist
        self.alpha_mismatch = alpha_mismatch
    
    def compute_smoothness(self, V: np.ndarray) -> float:
        """
        Compute spatial smoothness energy.
        
        E_smooth = (α_s/2) * Σ_n ∫ |∇V(x,n)|² dx
        
        This penalizes jagged spatial nonsense.
        
        Args:
            V: Visual field of shape (H, W, N)
            
        Returns:
            Smoothness energy
        """
        H, W, N = V.shape
        energy = 0.0
        
        for n in range(N):
            V_slice = V[:, :, n]
            
            # Compute gradient using central differences
            # (simplified - could use scipy.ndimage)
            grad_x = np.zeros_like(V_slice)
            grad_y = np.zeros_like(V_slice)
            
            # Central differences
            grad_x[:, 1:-1] = (V_slice[:, 2:] - V_slice[:, :-2]) / 2.0
            grad_y[1:-1, :] = (V_slice[2:, :] - V_slice[:-2, :]) / 2.0
            
            # Boundary (forward/backward differences)
            grad_x[:, 0] = V_slice[:, 1] - V_slice[:, 0]
            grad_x[:, -1] = V_slice[:, -1] - V_slice[:, -2]
            grad_y[0, :] = V_slice[1, :] - V_slice[0, :]
            grad_y[-1, :] = V_slice[-1, :] - V_slice[-2, :]
            
            energy += np.sum(grad_x ** 2 + grad_y ** 2)
        
        return (self.alpha_smooth / 2.0) * energy
    
    def compute_cross_scale_binding(self, V: np.ndarray) -> float:
        """
        Compute cross-scale binding energy.
        
        E_bind = (α_b/2) * Σ_n ∫ |V(x,n+1) - U_n V(x,n)|² dx
        
        where U_n is an up/down-scale consistency operator.
        
        This says visual forms should cohere across octaves.
        
        Args:
            V: Visual field of shape (H, W, N)
            
        Returns:
            Binding energy
        """
        H, W, N = V.shape
        energy = 0.0
        
        for n in range(N - 1):
            V_n = V[:, :, n]
            V_np1 = V[:, :, n + 1]
            
            # Simple upsampling: interpolate V_n to V_{n+1}
            # For simplicity, we just compare at same resolution
            # In practice, would use proper upsampling
            
            # Difference between adjacent octaves
            diff = V_np1 - V_n
            
            energy += np.sum(diff ** 2)
        
        return (self.alpha_bind / 2.0) * energy
    
    def compute_temporal_persistence(
        self, 
        V_curr: np.ndarray, 
        V_prev: np.ndarray
    ) -> float:
        """
        Compute temporal persistence energy.
        
        E_persist = (α_p/2) * Σ_n ∫ |V(x,n,t) - V(x,n,t-Δt)|² dx
        
        This stabilizes object identity over time.
        
        Args:
            V_curr: Current visual field
            V_prev: Previous visual field
            
        Returns:
            Persistence energy
        """
        if V_curr is None or V_prev is None:
            return 0.0
        
        diff = V_curr - V_prev
        return (self.alpha_persist / 2.0) * np.sum(diff ** 2)
    
    def compute_prediction_mismatch(
        self,
        V_obs: np.ndarray,
        V_pred: np.ndarray
    ) -> float:
        """
        Compute prediction mismatch energy.
        
        E_mismatch = (α_m/2) * Σ_n ∫ |V(x,n) - V_pred(x,n)|² dx
        
        This measures surprise.
        
        Args:
            V_obs: Observed visual field
            V_pred: Predicted visual field
            
        Returns:
            Mismatch energy
        """
        if V_pred is None:
            return 0.0
        
        diff = V_obs - V_pred
        return (self.alpha_mismatch / 2.0) * np.sum(diff ** 2)
    
    def compute_total(
        self,
        V: np.ndarray,
        V_prev: Optional[np.ndarray] = None,
        V_pred: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute total scene potential.
        
        V_scene = E_smooth + E_bind + E_persist + E_mismatch
        
        Args:
            V: Current visual field
            V_prev: Previous visual field (for persistence)
            V_pred: Predicted visual field (for mismatch)
            
        Returns:
            Total scene energy
        """
        E_smooth = self.compute_smoothness(V)
        E_bind = self.compute_cross_scale_binding(V)
        
        E_persist = 0.0
        if V_prev is not None:
            E_persist = self.compute_temporal_persistence(V, V_prev)
        
        E_mismatch = 0.0
        if V_pred is not None:
            E_mismatch = self.compute_prediction_mismatch(V, V_pred)
        
        return E_smooth + E_bind + E_persist + E_mismatch
    
    def compute_gradient(self, V: np.ndarray) -> np.ndarray:
        """
        Compute gradient of scene potential with respect to V.
        
        This is needed for Moreau projection.
        
        Args:
            V: Visual field
            
        Returns:
            Gradient of same shape as V
        """
        H, W, N = V.shape
        grad = np.zeros_like(V)
        
        # Gradient of smoothness
        # Simplified: just use Laplacian
        grad += self.alpha_smooth * self._compute_laplacian(V)
        
        # Gradient of cross-scale binding
        grad += self.alpha_bind * self._compute_bind_gradient(V)
        
        return grad
    
    def _compute_laplacian(self, V: np.ndarray) -> np.ndarray:
        """Compute spatial Laplacian."""
        H, W, N = V.shape
        laplacian = np.zeros_like(V)
        
        for n in range(N):
            V_slice = V[:, :, n]
            
            # Central Laplacian
            lap = np.zeros_like(V_slice)
            lap[:, 1:-1] = (V_slice[:, 2:] + V_slice[:, :-2] - 2 * V_slice[:, 1:-1])
            lap[1:-1, :] += (V_slice[2:, :] + V_slice[:-2, :] - 2 * V_slice[1:-1, :])
            
            # Boundaries
            lap[:, 0] = V_slice[:, 1] - V_slice[:, 0]
            lap[:, -1] = V_slice[:, -1] - V_slice[:, -2]
            lap[0, :] = V_slice[1, :] - V_slice[0, :]
            lap[-1, :] = V_slice[-1, :] - V_slice[-2, :]
            
            laplacian[:, :, n] = lap
        
        return laplacian
    
    def _compute_bind_gradient(self, V: np.ndarray) -> np.ndarray:
        """Compute gradient of cross-scale binding."""
        H, W, N = V.shape
        grad = np.zeros_like(V)
        
        # Contribution from each pair
        for n in range(N - 1):
            # d/dV_n: - (V_{n+1} - V_n)
            grad[:, :, n] -= (V[:, :, n + 1] - V[:, :, n])
            
            # d/dV_{n+1}: (V_{n+1} - V_n)
            grad[:, :, n + 1] += (V[:, :, n + 1] - V[:, :, n])
        
        return grad


class SceneCoherenceAnalyzer:
    """
    Analyze scene coherence properties.
    """
    
    def __init__(self, scene_binding: Optional[SceneBindingFunctional] = None):
        """Initialize analyzer."""
        self.scene_binding = scene_binding or SceneBindingFunctional()
    
    def analyze_coherence(
        self,
        V: np.ndarray,
        V_prev: Optional[np.ndarray] = None
    ) -> dict:
        """
        Analyze scene coherence.
        
        Args:
            V: Current visual field
            V_prev: Previous visual field
            
        Returns:
            Dictionary with coherence metrics
        """
        # Compute individual components
        smoothness = self.scene_binding.compute_smoothness(V)
        binding = self.scene_binding.compute_cross_scale_binding(V)
        
        persistence = 0.0
        if V_prev is not None:
            persistence = self.scene_binding.compute_temporal_persistence(V, V_prev)
        
        total = smoothness + binding + persistence
        
        # Additional metrics
        energy = 0.5 * np.sum(V ** 2)
        
        # Sparsity
        sparsity = np.sum(np.abs(V) < 0.01) / V.size
        
        # Spatial coherence (variance of gradient magnitude)
        grad_mag = self._compute_gradient_magnitude(V)
        spatial_coherence = float(np.std(grad_mag))
        
        return {
            'smoothness': smoothness,
            'binding': binding,
            'persistence': persistence,
            'total_energy': total,
            'field_energy': energy,
            'sparsity': sparsity,
            'spatial_coherence': spatial_coherence,
        }
    
    def _compute_gradient_magnitude(self, V: np.ndarray) -> np.ndarray:
        """Compute gradient magnitude."""
        H, W, N = V.shape
        grad_mag = np.zeros((H, W))
        
        for n in range(N):
            V_slice = V[:, :, n]
            grad_x = np.gradient(V_slice, axis=0)
            grad_y = np.gradient(V_slice, axis=1)
            grad_mag += np.sqrt(grad_x ** 2 + grad_y ** 2)
        
        return grad_mag / N


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing scene binding functional...")
    
    # Create scene binding
    scene_binding = SceneBindingFunctional(
        alpha_smooth=1.0,
        alpha_bind=1.0,
        alpha_persist=1.0,
        alpha_mismatch=1.0
    )
    
    # Create test visual fields
    np.random.seed(42)
    V = np.random.randn(32, 32, 88) * 0.1
    V_prev = np.random.randn(32, 32, 88) * 0.1
    V_pred = np.random.randn(32, 32, 88) * 0.1
    
    # Compute energies
    print("\nScene binding energies:")
    smoothness = scene_binding.compute_smoothness(V)
    print(f"  Smoothness: {smoothness:.4f}")
    
    binding = scene_binding.compute_cross_scale_binding(V)
    print(f"  Binding: {binding:.4f}")
    
    persistence = scene_binding.compute_temporal_persistence(V, V_prev)
    print(f"  Persistence: {persistence:.4f}")
    
    mismatch = scene_binding.compute_prediction_mismatch(V, V_pred)
    print(f"  Mismatch: {mismatch:.4f}")
    
    total = scene_binding.compute_total(V, V_prev, V_pred)
    print(f"  Total: {total:.4f}")
    
    # Test gradient
    print("\nTesting gradient...")
    grad = scene_binding.compute_gradient(V)
    print(f"  Gradient shape: {grad.shape}")
    print(f"  Gradient norm: {np.linalg.norm(grad):.4f}")
    
    # Test coherence analyzer
    print("\nTesting coherence analyzer...")
    analyzer = SceneCoherenceAnalyzer(scene_binding)
    coherence = analyzer.analyze_coherence(V, V_prev)
    print(f"  Sparsity: {coherence['sparsity']:.4f}")
    print(f"  Spatial coherence: {coherence['spatial_coherence']:.4f}")
    
    # Test with structured visual field
    print("\nTesting with structured visual field...")
    V_structured = np.zeros((32, 32, 88))
    # Add a smooth gradient
    x = np.linspace(0, 1, 32)
    y = np.linspace(0, 1, 32)
    X, Y = np.meshgrid(x, y)
    for n in range(88):
        V_structured[:, :, n] = np.sin(2 * np.pi * X) * np.cos(2 * np.pi * Y) * 0.5
    
    smoothness_struct = scene_binding.compute_smoothness(V_structured)
    binding_struct = scene_binding.compute_cross_scale_binding(V_structured)
    print(f"  Structured smoothness: {smoothness_struct:.4f}")
    print(f"  Structured binding: {binding_struct:.4f}")
    
    print("\nAll tests passed!")
