"""
Canonical Energy Law for the Universal Cognition Engine.

Section I — Continuous Core and Geometric Governance
Reference: docs/section_i_continuous_core.md

V_GMI(z) = V_base(x) + V_memory(x, M) + V_budget(b) + V_domain(μ)

This is the single source of truth for:
- Verifier checks
- Runtime control
- Learning rewards
- Convergence diagnostics
- Cross-domain interoperability

TAG REFERENCE:
- [AXIOM] V: H → ℝ is proper, lower semicontinuous, convex
- [AXIOM] Safe region C = {x: V(x) ≤ Θ}
- [AXIOM] Extended state z = (x, b) ∈ H × ℝ_≥0
- [PROVED] Sublevel set C = {V ≤ Θ} is closed and convex
"""

import numpy as np
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from core.memory import MemoryManifold


@dataclass
class GMIPotential:
    """
    Canonical energy law for the universal cognition engine.
    
    # [AXIOM] V: H → ℝ is proper, lower semicontinuous, convex
    # [AXIOM] Safe region C = {x: V(x) ≤ Θ}
    
    The total potential is a sum of:
    - Base cognitive tension (coherent = 0, incoherent = high)
    - Memory curvature cost (passive structural memory)
    - Budget barrier (diverges as b → 0)
    - Domain-specific residuals
    
    Reference: docs/section_i_continuous_core.md §2
    """
    lambda_curvature: float = 5.0
    lambda_budget: float = 1.0
    lambda_domain: float = 1.0
    budget_scale: float = 10.0
    
    def base(self, x: np.ndarray) -> float:
        """
        Base cognitive tension: V_base(x) = sum(x²)
        
        Represents total cognitive tension. Bounded below, coercive.
        Coherent states (near zero) have low potential.
        """
        return float(np.sum(x ** 2))
    
    def memory_term(self, x: np.ndarray, memory: Optional['MemoryManifold'] = None) -> float:
        """
        Curvature cost from memory manifold scars/rewards.
        
        Passive structural memory (C) deforms future dynamics by
        changing local geometry, resistances, and trajectory shape.
        
        Args:
            x: Current cognitive state coordinates
            memory: Optional MemoryManifold instance for curvature evaluation
            
        Returns:
            Curvature cost (positive = harder to move through this region)
        """
        if memory is None:
            return 0.0
        return memory.read_curvature(x)
    
    def budget_barrier(self, b: float) -> float:
        """
        Barrier term that diverges as b → 0.
        
        # [AXIOM] b ∈ ℝ_≥0 (nonnegative budget)
        # [POLICY] b = 0 → no risk-increasing motion allowed
        
        Prevents risk-increasing motion when budget exhausted.
        The law: b = 0 → no risk-increasing motion allowed.
        
        Args:
            b: Thermodynamic budget (b >= 0)
            
        Returns:
            Barrier potential (infinite when b <= 0)
        """
        if b <= 0:
            return float('inf')
        return self.lambda_budget * (self.budget_scale / b)
    
    def domain_term(self, domain_metrics: Optional[Dict[str, float]] = None) -> float:
        """
        Domain-specific residual penalty.
        
        Adapters contribute their specific coherence metrics here.
        Allows domain-specific shaping of the potential landscape.
        
        Args:
            domain_metrics: Dict of domain-specific metric values
            
        Returns:
            Domain contribution to potential
        """
        if not domain_metrics:
            return 0.0
        return self.lambda_domain * sum(domain_metrics.values())
    
    def total(
        self, 
        x: np.ndarray, 
        b: float, 
        memory: Optional['MemoryManifold'] = None,
        domain_metrics: Optional[Dict[str, float]] = None,
        episodic_penalty: float = 0.0
    ) -> float:
        """
        Full GMI potential: combines all energy terms.
        
        V_GMI(z) = V_base(x) + V_memory(x, M) + V_budget(b) + V_domain(μ) + V_episodic(ε)
        
        Args:
            x: Cognitive state coordinates
            b: Thermodynamic budget (b >= 0)
            memory: Optional memory manifold for curvature
            domain_metrics: Optional domain-specific metrics
            episodic_penalty: Optional penalty from episodic memory retrieval
            
        Returns:
            Total system energy (lower = more coherent)
        """
        V = self.base(x)
        
        if memory is not None:
            V += self.memory_term(x, memory)
        
        V += self.budget_barrier(b)
        
        if domain_metrics is not None:
            V += self.domain_term(domain_metrics)
        
        V += episodic_penalty
        
        return V
    
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """
        Gradient of base potential for descent.
        
        ∂V/∂x = 2x
        
        Used for gradient-based inference.
        """
        return 2.0 * x
    
    def is_admissible(self, b: float) -> bool:
        """
        Check if budget allows any motion.
        
        # [AXIOM] K = C × ℝ_≥0 is closed and convex
        # [PROVED] Forward invariance: z(0) ∈ K ⇒ z(t) ∈ K
        
        b = 0 → no risk-increasing motion
        """
        return b > 0
    
    def compute_descent_direction(self, x: np.ndarray) -> np.ndarray:
        """
        Compute normalized gradient descent direction.
        
        Returns:
            Unit vector pointing toward lower potential
        """
        grad = self.gradient(x)
        norm = np.linalg.norm(grad)
        if norm < 1e-10:
            return np.zeros_like(x)
        return -grad / norm


# Legacy compatibility: keep V_PL for existing code
def V_PL(x: np.ndarray) -> float:
    """
    Legacy PhaseLoom Potential: V_{PL}(x).
    Kept for backward compatibility.
    
    Note: This is now a GMIPotential.base()
 special case of    """
    return float(np.sum(x**2))


# Convenience function to create configured potential
def create_potential(
    lambda_curvature: float = 5.0,
    lambda_budget: float = 1.0,
    lambda_domain: float = 1.0,
    budget_scale: float = 10.0
) -> GMIPotential:
    """
    Factory function to create a configured GMIPotential.
    """
    return GMIPotential(
        lambda_curvature=lambda_curvature,
        lambda_budget=lambda_budget,
        lambda_domain=lambda_domain,
        budget_scale=budget_scale
    )
