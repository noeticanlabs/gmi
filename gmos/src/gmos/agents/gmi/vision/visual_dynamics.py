"""
Visual Dynamics for GMI Resonant Field Framework.

Implements the visual field dynamics per the mathematical specification:

    ∂_t V = -ν_vis(b) * K_vis * V + R_vis[V; ξ_coh] + I_ext + I_int

Where:
- K_vis = -α_Δ * Δ_x + α_n * K_n² (spatial-scale dissipation)
- R_vis: Cross-scale resonance
- I_ext: External visual forcing (world-imposed)
- I_int: Internal imagery forcing (imagination)

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from typing import Optional, Callable


class VisualDriftOperator:
    """
    Visual field dynamics operator.
    
    ∂_t V = -ν_vis(b) * K_vis * V + R_vis[V; ξ_coh] + I_ext + I_int
    
    Where:
    - K_vis = -α_Δ * Δ_x + α_n * K_n² (spatial-scale dissipation)
    - R_vis: Cross-scale resonance
    - I_ext: External visual forcing
    - I_int: Internal imagery forcing
    """
    
    def __init__(
        self,
        field_height: int = 32,
        field_width: int = 32,
        num_octaves: int = 88,
        alpha_delta: float = 0.1,   # Spatial smoothing
        alpha_n: float = 1.0,        # Octave damping
    ):
        """
        Initialize visual drift operator.
        
        Args:
            field_height: Spatial height
            field_width: Spatial width
            num_octaves: Number of octaves
            alpha_delta: Spatial Laplacian weight
            alpha_n: Octave damping weight
        """
        self.H = field_height
        self.W = field_width
        self.N = num_octaves
        self.alpha_delta = alpha_delta
        self.alpha_n = alpha_n
        
        # Wave numbers
        k0 = 1.0
        self.k = np.array([k0 * (2 ** n) for n in range(num_octaves)])
        
        # Spatial Laplacian kernel
        self._laplacian_kernel = np.array([
            [0.0, 1.0, 0.0],
            [1.0, -4.0, 1.0],
            [0.0, 1.0, 0.0]
        ])
    
    def compute_dissipation(
        self, 
        V: np.ndarray, 
        nu_vis: float
    ) -> np.ndarray:
        """
        Compute dissipation term: -ν * K_vis * V
        
        K_vis = -α_Δ * Δ_x + α_n * K_n²
        
        Args:
            V: Visual field
            nu_vis: Visual viscosity
            
        Returns:
            Dissipation vector
        """
        # Spatial Laplacian part
        laplacian = self._apply_spatial_laplacian(V)
        
        # Octave damping part
        octave_damping = self._apply_octave_damping(V)
        
        # Combined: -ν * (α_Δ * ΔV + α_n * K² * V)
        return -nu_vis * (self.alpha_delta * laplacian + self.alpha_n * octave_damping)
    
    def _apply_spatial_laplacian(self, V: np.ndarray) -> np.ndarray:
        """Apply spatial Laplacian to all octaves."""
        result = np.zeros_like(V)
        
        for n in range(self.N):
            V_slice = V[:, :, n]
            
            # Manual convolution with Laplacian kernel
            result[:, :, n] = (
                np.roll(V_slice, 1, axis=0) + 
                np.roll(V_slice, -1, axis=0) + 
                np.roll(V_slice, 1, axis=1) + 
                np.roll(V_slice, -1, axis=1) - 
                4 * V_slice
            )
        
        return result
    
    def _apply_octave_damping(self, V: np.ndarray) -> np.ndarray:
        """Apply octave-specific damping: K² * V."""
        result = np.zeros_like(V)
        
        for n in range(self.N):
            result[:, :, n] = self.k[n] ** 2 * V[:, :, n]
        
        return result
    
    def compute_drift(
        self,
        V: np.ndarray,
        nu_vis: float,
        resonance: Optional[np.ndarray] = None,
        external_forcing: Optional[np.ndarray] = None,
        internal_forcing: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute full visual drift.
        
        ∂_t V = dissipation + resonance + external + internal
        
        Args:
            V: Visual field
            nu_vis: Visual viscosity
            resonance: Cross-scale resonance term
            external_forcing: External forcing I_ext
            internal_forcing: Internal forcing I_int
            
        Returns:
            Visual drift
        """
        # Dissipation
        dissipation = self.compute_dissipation(V, nu_vis)
        
        # Resonance
        res = resonance if resonance is not None else np.zeros_like(V)
        
        # External forcing
        ext = external_forcing if external_forcing is not None else np.zeros_like(V)
        
        # Internal forcing
        int_forcing = internal_forcing if internal_forcing is not None else np.zeros_like(V)
        
        return dissipation + res + ext + int_forcing


class VisualCrossScaleResonance:
    """
    Cross-scale resonance for visual field.
    
    Similar to the triad resonance in the spectral field, but for spatial octaves.
    """
    
    def __init__(
        self,
        num_octaves: int = 88,
        coupling_strength: float = 0.1
    ):
        """
        Initialize cross-scale resonance.
        
        Args:
            num_octaves: Number of octaves
            coupling_strength: Coupling strength
        """
        self.N = num_octaves
        self.coupling = coupling_strength
    
    def __call__(self, V: np.ndarray, xi_coh: np.ndarray) -> np.ndarray:
        """
        Compute cross-scale resonance.
        
        Args:
            V: Visual field (H, W, N)
            xi_coh: Coherence state
            
        Returns:
            Resonance term of same shape as V
        """
        H, W, N = V.shape
        result = np.zeros_like(V)
        
        # Compute coherence factor
        coh_factor = self._compute_coherence_factor(xi_coh)
        
        # Transfer energy between adjacent octaves
        for n in range(N - 1):
            # Energy transfer from octave n to n+1
            energy_curr = V[:, :, n] ** 2
            energy_next = V[:, :, n + 1] ** 2
            
            # Transfer
            transfer = self.coupling * coh_factor * (energy_curr - energy_next)
            result[:, :, n] -= transfer
            result[:, :, n + 1] += transfer
        
        return result
    
    def _compute_coherence_factor(self, xi_coh: np.ndarray) -> float:
        """Compute coherence modulation factor."""
        if len(xi_coh) >= 3:
            z = xi_coh[2] if len(xi_coh) > 2 else 0.0
            return (1.0 + z) / 2.0
        return 0.5


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing visual dynamics operator...")
    
    # Create drift operator
    drift_op = VisualDriftOperator(
        field_height=32,
        field_width=32,
        num_octaves=88,
        alpha_delta=0.1,
        alpha_n=1.0
    )
    
    # Create test visual field
    np.random.seed(42)
    V = np.random.randn(32, 32, 88) * 0.1
    
    # Test dissipation
    nu_vis = 0.1
    dissipation = drift_op.compute_dissipation(V, nu_vis)
    print(f"Dissipation norm: {np.linalg.norm(dissipation):.4f}")
    
    # Test cross-scale resonance
    resonance_op = VisualCrossScaleResonance(num_octaves=88, coupling_strength=0.1)
    xi_coh = np.array([0.0, 0.0, 1.0])
    resonance = resonance_op(V, xi_coh)
    print(f"Resonance norm: {np.linalg.norm(resonance):.4f}")
    
    # Test full drift
    external_forcing = np.random.randn(32, 32, 88) * 0.01
    internal_forcing = np.random.randn(32, 32, 88) * 0.01
    
    drift = drift_op.compute_drift(
        V=V,
        nu_vis=nu_vis,
        resonance=resonance,
        external_forcing=external_forcing,
        internal_forcing=internal_forcing
    )
    print(f"Total drift norm: {np.linalg.norm(drift):.4f}")
    
    print("\nAll tests passed!")
