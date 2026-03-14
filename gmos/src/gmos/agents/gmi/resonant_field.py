"""
Resonant Field Block for GMI Resonant Field Framework.

Implements the 88-octave resonant substrate field per the mathematical specification:

    ξ_Φ ∈ ℝ^88
    
    k_n = k₀ * 2^n  (octave wave numbers)
    K = diag(k₀, ..., k₈₇)  (diagonal octave operator)

The field drift law:

    F_Φ(z) = -ν(b) * K² * ξ_Φ + R[ξ_Φ; ξ_coh] + B(ξ_action)
    
Components:
- Dissipation: -ν(b) * K² * ξ_Φ (preferentially damps high octaves)
- Resonant redistribution: R[ξ_Φ; ξ_coh] (transfers energy across octaves)
- Agent forcing: B(ξ_action) (injects action-driven excitation)

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable


class ResonantFieldBlock:
    """
    Resonant substrate field ξ_Φ ∈ ℝ^88.
    
    Each Φ_n represents amplitude/energy of octave n.
    
    Octave wave numbers: k_n = k₀ * 2^n
    
    This gives exponentially increasing frequencies across octaves,
    which means high octaves have much higher energy scales.
    """
    
    NUM_OCTAVES = 88
    
    def __init__(self, k0: float = 0.1):
        """
        Initialize the resonant field block.
        
        Args:
            k0: Base wave number (default: 0.1 to avoid numerical overflow at high octaves)
        """
        self.k0 = k0
        
        # Compute wave numbers for each octave: k_n = k0 * 2^(n/10)
        # Using slower scaling (power of 1/10) to keep numbers manageable across 88 octaves
        self.k = np.array([k0 * (2 ** (n/10)) for n in range(self.NUM_OCTAVES)])
        
        # Diagonal octave operator: K = diag(k₀², ..., k₈₇²)
        self.K_squared = np.diag(self.k ** 2)
        
        # Full K operator (for weighted operations)
        self.K = np.diag(self.k)
    
    def compute_field_energy(self, xi_Phi: Optional[np.ndarray] = None) -> float:
        """
        Compute field energy: E_field = 0.5 * |ξ_Φ|²
        
        Args:
            xi_Phi: Field state (uses internal if None)
            
        Returns:
            Field energy
        """
        if xi_Phi is None:
            return 0.0  # No state, no energy
        return 0.5 * np.sum(xi_Phi ** 2)
    
    def compute_weighted_energy(self, xi_Phi: np.ndarray) -> float:
        """
        Compute weighted field energy: E_field^K = 0.5 * |K * ξ_Φ|²
        
        Used for dissipation weighting - high octaves damp faster.
        
        Args:
            xi_Phi: Field state
            
        Returns:
            Weighted field energy
        """
        weighted = self.K @ xi_Phi
        return 0.5 * np.sum(weighted ** 2)
    
    def compute_octave_energy(self, xi_Phi: np.ndarray) -> np.ndarray:
        """
        Compute energy per octave.
        
        Args:
            xi_Phi: Field state
            
        Returns:
            Array of energies per octave (Φ_n²)
        """
        return xi_Phi ** 2
    
    def compute_dissipation(
        self, 
        xi_Phi: np.ndarray, 
        nu: float
    ) -> np.ndarray:
        """
        Compute dissipation term: -ν * K² * ξ_Φ
        
        This preferentially damps high octaves because k_n² grows exponentially.
        
        Args:
            xi_Phi: Current field state
            nu: Viscosity coefficient
            
        Returns:
            Dissipation vector
        """
        # K² @ ξ_Φ applies k_n² scaling to each octave
        return -nu * (self.K_squared @ xi_Phi)
    
    def compute_dissipation_gradient(self, xi_Phi: np.ndarray, nu: float) -> np.ndarray:
        """
        Compute gradient of dissipation term with respect to xi_Phi.
        
        d(-ν * K² * ξ_Φ)/dξ_Φ = -ν * K²
        
        Args:
            xi_Phi: Current field state
            nu: Viscosity coefficient
            
        Returns:
            Gradient matrix
        """
        return -nu * self.K_squared


@dataclass
class FieldDriftComponents:
    """
    Container for field drift components.
    
    F_Φ = dissipation + resonance + forcing
    """
    dissipation: np.ndarray
    resonance: np.ndarray
    forcing: np.ndarray
    
    @property
    def total(self) -> np.ndarray:
        """Total drift = sum of all components."""
        return self.dissipation + self.resonance + self.forcing


def compute_field_drift(
    xi_Phi: np.ndarray,
    xi_coh: np.ndarray,
    xi_action: np.ndarray,
    nu: float,
    field_block: ResonantFieldBlock,
    resonance_operator: Optional[Callable] = None,
    forcing_operator: Optional[Callable] = None
) -> FieldDriftComponents:
    """
    Compute full field drift.
    
    F_Φ(z) = -ν(b) * K² * ξ_Φ + R[ξ_Φ; ξ_coh] + B(ξ_action)
    
    Args:
        xi_Phi: Current field state
        xi_coh: Coherence state
        xi_action: Action intent
        nu: Viscosity coefficient
        field_block: ResonantFieldBlock instance
        resonance_operator: Function R[xi_Phi; xi_coh]
        forcing_operator: Function B(xi_action)
        
    Returns:
        FieldDriftComponents with all three parts
    """
    # Dissipation: -ν * K² * ξ_Phi
    dissipation = field_block.compute_dissipation(xi_Phi, nu)
    
    # Resonance: R[xi_Phi; xi_coh]
    if resonance_operator is not None:
        resonance = resonance_operator(xi_Phi, xi_coh)
    else:
        resonance = np.zeros(88)
    
    # Forcing: B(xi_action)
    if forcing_operator is not None:
        forcing = forcing_operator(xi_action)
    else:
        forcing = np.zeros(88)
    
    return FieldDriftComponents(
        dissipation=dissipation,
        resonance=resonance,
        forcing=forcing
    )


# =============================================================================
# Action forcing operator
# =============================================================================

class ActionForcingOperator:
    """
    Operator B: action space → field forcing.
    
    Injects action-driven excitation into the field.
    
    This is the "voice" side - the organism pushes back on the world
    through the resonant field.
    """
    
    def __init__(
        self,
        action_dim: int = 16,
        field_dim: int = 88,
        spectral_focus: str = "mid"  # "low", "mid", "high", "full"
    ):
        """
        Initialize action forcing operator.
        
        Args:
            action_dim: Dimension of action space
            field_dim: Dimension of field (88)
            spectral_focus: Which octaves get excited by actions
        """
        self.action_dim = action_dim
        self.field_dim = field_dim
        
        # Learnable mapping from action to field
        self.B = np.random.randn(field_dim, action_dim) * 0.01
        
        # Spectral focus mask
        if spectral_focus == "low":
            mask = np.zeros(field_dim)
            mask[:20] = 1.0
        elif spectral_focus == "mid":
            mask = np.zeros(field_dim)
            mask[20:60] = 1.0
        elif spectral_focus == "high":
            mask = np.zeros(field_dim)
            mask[60:] = 1.0
        else:  # "full"
            mask = np.ones(field_dim)
        
        self.spectral_mask = mask
    
    def __call__(self, xi_action: np.ndarray) -> np.ndarray:
        """
        Compute action forcing: B(action)
        
        Args:
            xi_action: Action intent vector
            
        Returns:
            Field forcing vector
        """
        # Project action to field space
        forcing = self.B @ xi_action
        
        # Apply spectral focus
        forcing = forcing * self.spectral_mask
        
        return forcing
    
    def compute_jacobian(self) -> np.ndarray:
        """
        Compute Jacobian d(B(action))/d(action) = B.
        
        Returns:
            Jacobian matrix
        """
        # Apply spectral mask to each column
        return self.B * self.spectral_mask[:, np.newaxis]


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing resonant field block...")
    
    # Create field block
    field_block = ResonantFieldBlock(k0=1.0)
    print(f"Number of octaves: {field_block.NUM_OCTAVES}")
    print(f"Wave numbers (first 5): {field_block.k[:5]}")
    print(f"Wave numbers (last 5): {field_block.k[-5:]}")
    
    # Test with random field state
    xi_Phi = np.random.randn(88) * 0.5
    print(f"\nField energy: {field_block.compute_field_energy(xi_Phi):.4f}")
    print(f"Weighted energy: {field_block.compute_weighted_energy(xi_Phi):.4f}")
    
    # Test dissipation
    nu = 0.1
    dissipation = field_block.compute_dissipation(xi_Phi, nu)
    print(f"\nDissipation norm: {np.linalg.norm(dissipation):.4f}")
    print(f"High octave dissipation (last 5): {dissipation[-5:]}")
    
    # Test action forcing
    action_op = ActionForcingOperator(action_dim=16, field_dim=88, spectral_focus="mid")
    xi_action = np.random.randn(16)
    forcing = action_op(xi_action)
    print(f"\nAction forcing norm: {np.linalg.norm(forcing):.4f}")
    print(f"Action forcing (first 10): {forcing[:10]}")
    
    # Test full drift computation
    xi_coh = np.array([0.0, 0.0, 1.0])
    drift = compute_field_drift(
        xi_Phi=xi_Phi,
        xi_coh=xi_coh,
        xi_action=xi_action,
        nu=nu,
        field_block=field_block,
        forcing_operator=action_op
    )
    print(f"\nTotal drift norm: {np.linalg.norm(drift.total):.4f}")
    print(f"  Dissipation: {np.linalg.norm(drift.dissipation):.4f}")
    print(f"  Resonance: {np.linalg.norm(drift.resonance):.4f}")
    print(f"  Forcing: {np.linalg.norm(drift.forcing):.4f}")
    
    print("\nAll tests passed!")
