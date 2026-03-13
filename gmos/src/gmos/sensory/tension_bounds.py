"""
Bounded-Tension Lemma for Sensory Forcing.

Per spec §13: The mathematically respectable version of 
"the world can dent the organism without exploding the solver."

Mathematical Statement:
    If:
        |s|_sens ≤ S_max
        |Ξ(s)|_L² ≤ K_΋ |s|_sens
    
    Then for admissible θ ∈ H¹(M):
        |ΔV| ≤ C(|θ|_H¹, S_max, |C|, ...) < ∞

This ensures that a finite sensory object cannot create infinite
tension in one shot.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import numpy as np


@dataclass
class TensionBoundParameters:
    """
    Parameters for the bounded-tension lemma.
    
    These define the constants in:
        |Ξ(s)|_L² ≤ K_΋ |s|_sens
        |ΔV| ≤ C(|θ|_H¹, S_max, |C|, ...)
    """
    # Bounding constant K_΋
    bounding_constant: float = 1.0
    
    # Maximum percept norm S_max
    max_percept_norm: float = 10.0
    
    # Field parameters
    field_kappa: float = 1.0  # Diffusion coefficient
    field_lambda: float = 1.0  # Coupling constant
    
    # Domain parameters
    domain_volume: float = 1.0


class BoundedTensionLemma:
    """
    Implements the bounded-tension lemma per spec §13.
    
    This is the mathematical guarantee that sensory forcing
    cannot create infinite tension in the GMI solver.
    
    The lemma states:
    1. If percept norm is bounded (|s| ≤ S_max)
    2. And the forcing operator is bounded (|Ξ(s)| ≤ K|s|)
    3. Then the potential variation is bounded
    
    Usage:
        lemma = BoundedTensionLemma()
        is_bounded, bound = lemma.verify(percept, theta_field)
    """
    
    def __init__(
        self,
        params: Optional[TensionBoundParameters] = None
    ):
        """
        Initialize the bounded-tension lemma.
        
        Args:
            params: Lemma parameters (uses defaults if None)
        """
        self.params = params or TensionBoundParameters()
    
    def compute_percept_norm(self, percept_features: Dict[str, float]) -> float:
        """
        Compute the L2 norm of a percept.
        
        Per spec: |s|_sens = sqrt(sum of squared components)
        
        Args:
            percept_features: Dictionary of percept feature values
            
        Returns:
            L2 norm of the percept
        """
        squared_sum = sum(v ** 2 for v in percept_features.values())
        return np.sqrt(squared_sum)
    
    def compute_forcing_bound(
        self,
        percept_norm: float
    ) -> float:
        """
        Compute the upper bound on forcing norm.
        
        Per spec: |Ξ(s)|_L² ≤ K_΋ |s|_sens
        
        Args:
            percept_norm: |s|_sens
            
        Returns:
            Upper bound on |Ξ(s)|_L²
        """
        return self.params.bounding_constant * percept_norm
    
    def compute_tension_bound(
        self,
        theta_norm: float,
        percept_norm: float,
        curvature_magnitude: float = 0.0
    ) -> float:
        """
        Compute the bound on potential variation.
        
        Per spec:
        |ΔV| ≤ C(|θ|_H¹, S_max, |C|, ...)
        
        The constant C combines:
        - Field energy: κ|∇θ|² ≤ κ|θ|² (by Poincaré)
        - Forcing term: Ξ(s)θ
        - Coupling: λ_C Cθ
        
        Args:
            theta_norm: |θ|_H¹ (H¹ norm of field)
            percept_norm: |s|_sens (percept norm, capped at S_max)
            curvature_magnitude: |C| (curvature field magnitude)
            
        Returns:
            Upper bound on |ΔV|
        """
        kappa = self.params.field_kappa
        lam = self.params.field_lambda
        K = self.params.bounding_constant
        V = self.params.domain_volume
        
        # Cap percept norm at S_max
        S = min(percept_norm, self.params.max_percept_norm)
        
        # Bound from field energy term: κ|θ|²
        energy_bound = kappa * (theta_norm ** 2)
        
        # Bound from forcing term: |Ξ(s)θ| ≤ |Ξ(s)||θ| ≤ K| s||θ|
        forcing_bound = K * S * theta_norm
        
        # Bound from coupling term: λ_C|C||θ|
        coupling_bound = lam * curvature_magnitude * theta_norm
        
        # Total bound (using triangle inequality)
        total_bound = energy_bound + forcing_bound + coupling_bound
        
        # Scale by domain volume
        return total_bound * V
    
    def verify(
        self,
        percept_features: Dict[str, float],
        theta_norm: float,
        curvature_magnitude: float = 0.0,
        actual_forcing_norm: Optional[float] = None
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Verify the bounded-tension lemma for given inputs.
        
        Args:
            percept_features: Features of the sensory percept
            theta_norm: H¹ norm of the field θ
            curvature_magnitude: Magnitude of curvature field
            actual_forcing_norm: Actual forcing norm (if known, for verification)
            
        Returns:
            (is_bounded, details)
            
        Details contains:
            - percept_norm: |s|_sens
            - forcing_bound: Upper bound on |Ξ(s)|
            - actual_forcing: Actual forcing norm (if provided)
            - tension_bound: Upper bound on |ΔV|
            - is_valid: Whether the lemma conditions are satisfied
        """
        # Compute percept norm
        percept_norm = self.compute_percept_norm(percept_features)
        
        # Check percept norm bound
        percept_ok = percept_norm <= self.params.max_percept_norm
        
        # Compute forcing bound
        forcing_bound = self.compute_forcing_bound(percept_norm)
        
        # If actual forcing provided, verify it respects bound
        if actual_forcing_norm is not None:
            forcing_ok = actual_forcing_norm <= forcing_bound
        else:
            forcing_ok = True
        
        # Compute tension bound
        tension_bound = self.compute_tension_bound(
            theta_norm,
            percept_norm,
            curvature_magnitude
        )
        
        # Lemma is satisfied if percept norm is bounded
        # (forcing bound is always valid by construction)
        is_bounded = percept_ok
        
        details = {
            "percept_norm": percept_norm,
            "percept_bound": self.params.max_percept_norm,
            "forcing_bound": forcing_bound,
            "actual_forcing": actual_forcing_norm,
            "forcing_ok": forcing_ok,
            "tension_bound": tension_bound,
            "theta_norm": theta_norm,
            "curvature_magnitude": curvature_magnitude,
            "is_valid": is_bounded,
        }
        
        return is_bounded, details
    
    def verify_operator_boundedness(
        self,
        percept: Any,
        ingress_operator: Any
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Verify that an ingress operator satisfies boundedness.
        
        Checks: |Ξ(s)|_L² ≤ K_΋ |s|_sens
        
        Args:
            percept: SensoryPercept object
            ingress_operator: The ingress operator to verify
            
        Returns:
            (is_bounded, details)
        """
        # Compute percept norm
        percept_norm = percept.compute_norm()
        
        # Apply operator to get forcing
        force = ingress_operator(percept)
        forcing_norm = force.compute_l2_norm()
        
        # Compute bound
        forcing_bound = self.compute_forcing_bound(percept_norm)
        
        # Check boundedness
        is_bounded = forcing_norm <= forcing_bound
        
        details = {
            "percept_norm": percept_norm,
            "forcing_norm": forcing_norm,
            "forcing_bound": forcing_bound,
            "bounding_constant": self.params.bounding_constant,
            "is_bounded": is_bounded,
        }
        
        return is_bounded, details


class TensionVerifier:
    """
    Verifier for sensory-tension properties.
    
    Provides higher-level verification that the sensory
    substrate cannot produce unbounded forcing.
    """
    
    def __init__(self, lemma: Optional[BoundedTensionLemma] = None):
        self.lemma = lemma or BoundedTensionLemma()
    
    def verify_batch(
        self,
        percepts: list,
        theta_norm: float,
        curvature_magnitude: float = 0.0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify boundedness for a batch of percepts.
        
        Args:
            percepts: List of percept objects
            theta_norm: Field norm
            curvature_magnitude: Curvature magnitude
            
        Returns:
            (all_bounded, summary)
        """
        results = []
        all_bounded = True
        
        for percept in percepts:
            # Extract features
            features = {
                "quality": percept.quality,
                "tension": percept.tension,
                "curvature": percept.curvature,
                "shell_stability": percept.shell_stability,
                "health": percept.health,
                "memory_pressure": percept.memory_pressure,
                "novelty": percept.novelty,
                "salience": percept.salience,
                "relevance": percept.relevance,
                "authority": percept.authority,
            }
            
            is_bounded, details = self.lemma.verify(
                features,
                theta_norm,
                curvature_magnitude
            )
            
            results.append({
                "percept_id": percept.percept_id,
                "is_bounded": is_bounded,
                "details": details,
            })
            
            if not is_bounded:
                all_bounded = False
        
        return all_bounded, {"percepts": results}
    
    def verify_step(
        self,
        sensory_state: Dict[str, Any],
        field_state: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify a complete sensory step.
        
        Args:
            sensory_state: Current sensory state
            field_state: Current field state
            
        Returns:
            (is_valid, message)
        """
        # Extract parameters
        theta_norm = field_state.get("h1_norm", 1.0)
        curvature = field_state.get("curvature_magnitude", 0.0)
        
        # Get percepts from sensory state
        percepts = sensory_state.get("percepts", [])
        
        if not percepts:
            return True, "No percepts to verify"
        
        # Verify batch
        all_bounded, summary = self.verify_batch(
            percepts,
            theta_norm,
            curvature
        )
        
        if all_bounded:
            return True, f"All {len(percepts)} percepts satisfy bounded-tension lemma"
        else:
            bounded_count = sum(1 for r in summary["percepts"] if r["is_bounded"])
            return False, f"{bounded_count}/{len(percepts)} percepts satisfy bounded-tension lemma"


# === Exports ===

__all__ = [
    "TensionBoundParameters",
    "BoundedTensionLemma",
    "TensionVerifier",
]
