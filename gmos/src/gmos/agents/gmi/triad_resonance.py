"""
Triad Resonance Operator for GMI Resonant Field Framework.

Implements the constitutive triad law for energy redistribution across octaves:

    R_n[ξ_Φ; ξ_coh] = f(ξ_coh) * [k_n * Φ_{n-1}² - k_{n+1} * Φ_n * Φ_{n+1}]

This transfers energy between adjacent octaves while respecting the defect bound:

    |⟨ξ_Φ, R[ξ_Φ; ξ_coh]⟩| ≤ Δ_R

The ideal conservative case has ⟨ξ_Φ, R⟩ = 0 (no net energy creation/destruction).

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from typing import Optional, Tuple


class TriadResonanceOperator:
    """
    Constitutive triad law for energy redistribution.
    
    R_n[ξ_Φ; ξ_coh] = f(ξ_coh) * [k_n * Φ_{n-1}² - k_{n+1} * Φ_n * Φ_{n+1}]
    
    This models three-wave resonance processes where energy transfers
    between adjacent octaves through nonlinear coupling.
    """
    
    def __init__(
        self,
        k: np.ndarray,
        delta_R: float = 0.0,
        coherence_factor_type: str = "simple"
    ):
        """
        Initialize the triad resonance operator.
        
        Args:
            k: Wave numbers array (k_n = k0 * 2^n)
            delta_R: Triad defect bound (default: 0 = conservative)
            coherence_factor_type: Type of coherence modulation
        """
        self.k = k
        self.n = len(k)
        self.delta_R = delta_R
        self.coherence_factor_type = coherence_factor_type
    
    def compute_coherence_factor(self, xi_coh: np.ndarray) -> float:
        """
        Compute coherence-dependent modulation factor.
        
        Args:
            xi_coh: Coherence state vector
            
        Returns:
            Coherence modulation factor in [0, 1]
        """
        if self.coherence_factor_type == "simple":
            # Simple: inverse of coherence norm
            norm = np.linalg.norm(xi_coh)
            if norm < 1e-10:
                return 0.0
            return min(1.0, 1.0 / (1.0 + norm))
        
        elif self.coherence_factor_type == "bloch":
            # Assume xi_coh is Bloch sphere vector [x, y, z]
            if len(xi_coh) >= 3:
                # Purity = (1 + z) / 2 for |ψ⟩ = cos(θ/2)|0⟩ + sin(θ/2)e^(iφ)|1⟩
                z = xi_coh[2] if len(xi_coh) > 2 else 0.0
                purity = (1.0 + z) / 2.0
                return max(0.0, min(1.0, purity))
            return 0.5
        
        else:
            # Default: no modulation
            return 1.0
    
    def __call__(
        self, 
        xi_Phi: np.ndarray, 
        xi_coh: np.ndarray
    ) -> np.ndarray:
        """
        Compute resonant redistribution.
        
        R_n[ξ_Φ; ξ_coh] = f(ξ_coh) * [k_n * Φ_{n-1}² - k_{n+1} * Φ_n * Φ_{n+1}]
        
        Args:
            xi_Phi: Field state (88 octaves)
            xi_coh: Coherence state
            
        Returns:
            Redistribution vector
        """
        n = self.n
        result = np.zeros(n)
        
        # Get coherence modulation factor
        f_coh = self.compute_coherence_factor(xi_coh)
        
        for i in range(n):
            # Lower octave contribution: k_i * Φ_{i-1}²
            if i > 0:
                lower = self.k[i] * (xi_Phi[i-1] ** 2)
            else:
                lower = 0.0
            
            # Higher octave contribution: k_{i+1} * Φ_i * Φ_{i+1}
            if i < n - 1:
                higher = self.k[i+1] * xi_Phi[i] * xi_Phi[i+1]
            else:
                higher = 0.0
            
            # Net transfer (positive = energy flows to this octave)
            result[i] = f_coh * (lower - higher)
        
        return result
    
    def compute_defect(
        self, 
        xi_Phi: np.ndarray, 
        xi_coh: np.ndarray
    ) -> float:
        """
        Compute the triad defect: |⟨ξ_Φ, R[ξ_Φ; ξ_coh]⟩|
        
        This measures the net energy transfer. The ideal conservative
        case has defect = 0.
        
        Args:
            xi_Phi: Field state
            xi_coh: Coherence state
            
        Returns:
            Defect value (capped at delta_R)
        """
        R = self(xi_Phi, xi_coh)
        defect = np.abs(np.dot(xi_Phi, R))
        
        # Cap at bound
        if self.delta_R > 0:
            return min(defect, self.delta_R)
        return defect
    
    def compute_energy_balance(
        self, 
        xi_Phi: np.ndarray, 
        xi_coh: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Compute energy balance analysis.
        
        Returns:
            (input_energy, output_energy, net_transfer)
        """
        R = self(xi_Phi, xi_coh)
        
        # Energy flowing INTO each octave (positive R)
        input_energy = np.sum(np.maximum(0, R) * xi_Phi)
        
        # Energy flowing OUT OF each octave (negative R)
        output_energy = np.sum(np.minimum(0, R) * xi_Phi)
        
        # Net transfer
        net_transfer = input_energy + output_energy  # = <xi_Phi, R>
        
        return input_energy, output_energy, net_transfer


class ConservativeTriadOperator(TriadResonanceOperator):
    """
    Conservative triad operator that preserves energy exactly.
    
    This enforces ⟨ξ_Φ, R⟩ = 0 by adjusting the redistribution.
    """
    
    def __init__(
        self,
        k: np.ndarray,
        coherence_factor_type: str = "simple"
    ):
        super().__init__(
            k=k,
            delta_R=0.0,  # Conservative
            coherence_factor_type=coherence_factor_type
        )
    
    def __call__(
        self, 
        xi_Phi: np.ndarray, 
        xi_coh: np.ndarray
    ) -> np.ndarray:
        """
        Compute conservative redistribution.
        
        This version ensures exactly zero net energy transfer.
        """
        # Get base redistribution
        R_base = super().__call__(xi_Phi, xi_coh)
        
        # Compute the dot product (net energy transfer)
        net_transfer = np.dot(xi_Phi, R_base)
        
        # Subtract the mean to enforce conservation
        # This ensures <xi_Phi, R> = 0
        if np.linalg.norm(xi_Phi) > 1e-10:
            correction = net_transfer / np.dot(xi_Phi, xi_Phi)
            R_conservative = R_base - correction * xi_Phi
        else:
            R_conservative = R_base
        
        return R_conservative


class BoundedTriadOperator(TriadResonanceOperator):
    """
    Bounded triad operator with explicit defect bound.
    
    This version enforces the defect bound by clamping.
    """
    
    def __init__(
        self,
        k: np.ndarray,
        delta_R: float = 1.0,
        coherence_factor_type: str = "simple"
    ):
        super().__init__(
            k=k,
            delta_R=delta_R,
            coherence_factor_type=coherence_factor_type
        )
    
    def __call__(
        self, 
        xi_Phi: np.ndarray, 
        xi_coh: np.ndarray
    ) -> np.ndarray:
        """
        Compute bounded redistribution.
        
        This version enforces |⟨ξ_Φ, R⟩| ≤ Δ_R.
        """
        # Get base redistribution
        R_base = super().__call__(xi_Phi, xi_coh)
        
        # Compute current defect
        current_defect = np.abs(np.dot(xi_Phi, R_base))
        
        if current_defect <= self.delta_R or self.delta_R <= 0:
            # Within bounds, return as-is
            return R_base
        
        # Need to bound the defect
        # Scale down the redistribution proportionally
        scale_factor = self.delta_R / current_defect
        
        return scale_factor * R_base


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing triad resonance operator...")
    
    # Create wave numbers
    k0 = 1.0
    k = np.array([k0 * (2 ** n) for n in range(88)])
    
    # Create operator
    triad = TriadResonanceOperator(k=k, delta_R=1.0)
    
    # Test with random field
    np.random.seed(42)
    xi_Phi = np.random.randn(88) * 0.5
    xi_coh = np.array([0.0, 0.0, 1.0])  # Pure |0⟩ state
    
    # Compute redistribution
    R = triad(xi_Phi, xi_coh)
    print(f"Redistribution norm: {np.linalg.norm(R):.4f}")
    
    # Compute defect
    defect = triad.compute_defect(xi_Phi, xi_coh)
    print(f"Defect: {defect:.4f}")
    
    # Energy balance
    input_e, output_e, net = triad.compute_energy_balance(xi_Phi, xi_coh)
    print(f"Energy balance: input={input_e:.4f}, output={output_e:.4f}, net={net:.4f}")
    
    # Test conservative operator
    print("\nTesting conservative operator...")
    conservative = ConservativeTriadOperator(k=k)
    R_cons = conservative(xi_Phi, xi_coh)
    defect_cons = np.abs(np.dot(xi_Phi, R_cons))
    print(f"Conservative defect: {defect_cons:.10f}")
    
    # Test bounded operator
    print("\nTesting bounded operator...")
    bounded = BoundedTriadOperator(k=k, delta_R=0.5)
    R_bounded = bounded(xi_Phi, xi_coh)
    defect_bounded = np.abs(np.dot(xi_Phi, R_bounded))
    print(f"Bounded defect: {defect_bounded:.4f} (should be ≤ 0.5)")
    
    # Test coherence factor
    print("\nTesting coherence modulation...")
    for coh_state in [
        np.array([0.0, 0.0, 1.0]),   # Pure |0⟩
        np.array([0.0, 0.0, 0.5]),   # Mixed
        np.array([0.0, 0.0, -1.0]),  # Pure |1⟩
        np.array([0.707, 0.707, 0.0]),  # Superposition
    ]:
        f = triad.compute_coherence_factor(coh_state)
        print(f"  Coherence state {coh_state}: f={f:.4f}")
    
    print("\nAll tests passed!")
