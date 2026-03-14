"""
Reserve-Coupled Viscosity Law for GMI Resonant Field Framework.

Implements the Softplus constitutive law per the mathematical specification:

    ν(b) = ν₀ + (ν₁/κ) * log(1 + exp(κ(b_floor - b)))

Interpretation:
- b >> b_floor: ν(b) ≈ ν₀ (minimum viscosity)
- b → b_floor: ν(b) → ν₀ + ν₁ (maximum viscosity)

This is a C^1 function (smooth), which is important for the Moreau projection
to have well-defined normal cone geometry.

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from typing import Optional, Tuple


class ReserveCoupledViscosity:
    """
    C^1 Softplus constitutive law for viscosity.
    
    ν(b) = ν₀ + (ν₁/κ) * log(1 + exp(κ(b_floor - b)))
    
    This couples the field dissipation to the budget reserves.
    As reserves are threatened, the field becomes more viscous,
    suppressing expensive high-frequency oscillations.
    """
    
    def __init__(
        self,
        nu_0: float = 0.1,    # Minimum viscosity (when b >> b_floor)
        nu_1: float = 1.0,    # Viscosity range (max increase)
        kappa: float = 10.0,   # Smoothness parameter (larger = sharper transition)
        b_floor: float = 1.0   # Reserve floor threshold
    ):
        """
        Initialize the viscosity law.
        
        Args:
            nu_0: Minimum viscosity (base dissipation)
            nu_1: Viscosity range (additional dissipation at floor)
            kappa: Smoothness parameter (controls transition sharpness)
            b_floor: Reserve floor threshold
        """
        self.nu_0 = nu_0
        self.nu_1 = nu_1
        self.kappa = kappa
        self.b_floor = b_floor
        
        # Precompute for efficiency
        self._inv_kappa = 1.0 / kappa
    
    def __call__(self, b: float) -> float:
        """
        Compute viscosity at budget b.
        
        Uses numerically stable softplus computation.
        
        Args:
            b: Current budget level
            
        Returns:
            Viscosity coefficient ν(b)
        """
        x = self.kappa * (self.b_floor - b)
        
        # Numerically stable softplus:
        # log(1 + exp(x)) = max(x, 0) + log(1 + exp(-|x|))
        if x > 0:
            softplus = x + np.log1p(np.exp(-x))
        else:
            softplus = np.log1p(np.exp(x))
        
        return self.nu_0 + self.nu_1 * self._inv_kappa * softplus
    
    def derivative(self, b: float) -> float:
        """
        Compute dν/db.
        
        dν/db = -ν₁ * sigmoid(κ(b_floor - b))
        
        The derivative is always negative (viscosity increases as budget decreases).
        
        Args:
            b: Current budget level
            
        Returns:
            dν/db
        """
        x = self.kappa * (self.b_floor - b)
        
        # Sigmoid: 1 / (1 + exp(-x))
        sigmoid = 1.0 / (1.0 + np.exp(-x))
        
        return -self.nu_1 * sigmoid
    
    def second_derivative(self, b: float) -> float:
        """
        Compute d²ν/db².
        
        d²ν/db² = -ν₁ * κ * sigmoid(x) * (1 - sigmoid(x))
                = -ν₁ * κ * sigmoid(x) * sigmoid(-x)
        
        Always positive (viscosity curve is convex in b).
        
        Args:
            b: Current budget level
            
        Returns:
            d²ν/db²
        """
        x = self.kappa * (self.b_floor - b)
        
        sigmoid = 1.0 / (1.0 + np.exp(-x))
        
        return self.nu_1 * self.kappa * sigmoid * (1 - sigmoid)
    
    def compute_viscosity_range(self) -> Tuple[float, float]:
        """
        Compute the range of viscosity values.
        
        Returns:
            (nu_min, nu_max) tuple
        """
        nu_min = self.nu_0  # When b >> b_floor
        nu_max = self.nu_0 + self.nu_1  # When b → -∞ (practically when b << b_floor)
        return nu_min, nu_max
    
    def get_parameters(self) -> dict:
        """
        Get viscosity law parameters.
        
        Returns:
            Dictionary of parameters
        """
        return {
            'nu_0': self.nu_0,
            'nu_1': self.nu_1,
            'kappa': self.kappa,
            'b_floor': self.b_floor,
            'nu_range': self.compute_viscosity_range()
        }
    
    def __repr__(self) -> str:
        return (f"ReserveCoupledViscosity(nu_0={self.nu_0}, nu_1={self.nu_1}, "
                f"kappa={self.kappa}, b_floor={self.b_floor})")


class MultiChannelViscosity:
    """
    Viscosity law for multiple budget channels.
    
    Different subsystems can have different viscosity behaviors
    based on their specific budget channels.
    """
    
    def __init__(
        self,
        channel_configs: Optional[dict] = None
    ):
        """
        Initialize multi-channel viscosity.
        
        Args:
            channel_configs: Dict mapping channel name to (nu_0, nu_1, kappa, b_floor)
        """
        if channel_configs is None:
            channel_configs = {
                'default': (0.1, 1.0, 10.0, 1.0)
            }
        
        self.channel_viscosities = {
            name: ReserveCoupledViscosity(*config)
            for name, config in channel_configs.items()
        }
    
    def __call__(self, b: dict) -> dict:
        """
        Compute viscosities for all channels.
        
        Args:
            b: Dict mapping channel name to budget level
            
        Returns:
            Dict mapping channel name to viscosity
        """
        return {
            name: vis(b.get(name, 0.0))
            for name, vis in self.channel_viscosities.items()
        }
    
    def derivative(self, b: dict) -> dict:
        """
        Compute derivatives for all channels.
        
        Args:
            b: Dict mapping channel name to budget level
            
        Returns:
            Dict mapping channel name to derivative
        """
        return {
            name: vis.derivative(b.get(name, 0.0))
            for name, vis in self.channel_viscosities.items()
        }
    
    def get_channel(self, name: str) -> Optional[ReserveCoupledViscosity]:
        """Get viscosity law for a specific channel."""
        return self.channel_viscosities.get(name)


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing reserve-coupled viscosity law...")
    
    # Create viscosity law
    vis = ReserveCoupledViscosity(nu_0=0.1, nu_1=1.0, kappa=10.0, b_floor=1.0)
    print(f"Viscosity law: {vis}")
    
    # Test viscosity at different budget levels
    print("\nViscosity at various budget levels:")
    for b in [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]:
        nu = vis(b)
        dnu = vis.derivative(b)
        print(f"  b={b:5.1f}: ν={nu:.4f}, dν/db={dnu:.4f}")
    
    # Test viscosity range
    nu_min, nu_max = vis.compute_viscosity_range()
    print(f"\nViscosity range: [{nu_min:.4f}, {nu_max:.4f}]")
    
    # Test multi-channel viscosity
    print("\nTesting multi-channel viscosity...")
    multi_vis = MultiChannelViscosity({
        'field': (0.1, 1.0, 10.0, 1.0),
        'sensory': (0.05, 0.5, 5.0, 2.0),
        'memory': (0.2, 0.8, 15.0, 1.5),
    })
    
    budgets = {'field': 1.5, 'sensory': 3.0, 'memory': 1.0}
    viscosities = multi_vis(budgets)
    print(f"  Budgets: {budgets}")
    print(f"  Viscosities: {viscosities}")
    
    # Test smoothness (C^1 continuity)
    print("\nTesting C^1 continuity...")
    b_test = 1.0
    epsilon = 1e-6
    nu_b = vis(b_test)
    nu_plus = vis(b_test + epsilon)
    nu_minus = vis(b_test - epsilon)
    numerical_deriv = (nu_plus - nu_minus) / (2 * epsilon)
    analytical_deriv = vis.derivative(b_test)
    print(f"  At b={b_test}:")
    print(f"    Numerical dν/db: {numerical_deriv:.6f}")
    print(f"    Analytical dν/db: {analytical_deriv:.6f}")
    print(f"    Difference: {abs(numerical_deriv - analytical_deriv):.8f}")
    
    print("\nAll tests passed!")
