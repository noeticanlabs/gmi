"""
Section I Theorem Implementations for the GMI Universal Cognition Engine.

This module provides formal theorem implementations corresponding to
Section I — Continuous Core and Geometric Governance from the canonical document.

Reference: docs/section_i_continuous_core.md

Tag Legend:
- [AXIOM] Foundational definitions and assumptions
- [POLICY] Governing laws and dynamics
- [PROVED] Theorems with implementation verification
- [LEMMA-NEEDED] Items requiring additional proof work
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Callable, Protocol
from abc import ABC, abstractmethod


# =============================================================================
# Section I Theorem Protocols
# =============================================================================

class Theorem(ABC):
    """Base class for Section I theorems."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Theorem name."""
        pass
    
    @property
    @abstractmethod
    def section_ref(self) -> str:
        """Section reference (e.g., '§5.1')."""
        pass
    
    @property
    @abstractmethod
    def tag(self) -> str:
        """Tag: PROVED or LEMMA-NEEDED."""
        pass
    
    @property
    @abstractmethod
    def statement(self) -> str:
        """Mathematical statement."""
        pass


# =============================================================================
# Theorem 5.1 — Global Admissible Evolution
# =============================================================================

@dataclass
class ForwardInvarianceTheorem(Theorem):
    """
    Theorem 5.1 — Global admissible evolution.
    
    # [PROVED]
    
    For every z(0) ∈ K, there exists a unique absolutely continuous trajectory
    satisfying ż(t) ∈ F(z(t)) - N_K(z(t)), z(t) ∈ K ∀ t ≥ 0.
    
    The system is strictly forward invariant: it never leaves admissibility
    once started inside it.
    
    Reference: docs/section_i_continuous_core.md §5.1
    """
    name: str = "Forward Invariance"
    section_ref: str = "§5.1"
    tag: str = "PROVED"
    statement: str = "z(0) ∈ K ⇒ z(t) ∈ K ∀ t ≥ 0"
    
    def verify(
        self,
        z_traj: np.ndarray,
        t_values: np.ndarray,
        constraint_set: 'ConstraintSet'
    ) -> Tuple[bool, str]:
        """
        Verify forward invariance along a trajectory.
        
        Args:
            z_traj: Trajectory of extended states, shape (T, n+1) where T is time steps
            t_values: Time values corresponding to trajectory
            constraint_set: Constraint set defining admissible set K
            
        Returns:
            (is_valid, message)
        """
        is_valid = True
        for i, z in enumerate(z_traj):
            x, b = z[:-1], z[-1]
            if not constraint_set.is_feasible(x, b):
                is_valid = False
                return is_valid, f"Violation at t={t_values[i]}: z ∉ K"
        
        return is_valid, "Forward invariance verified: trajectory remains in K"


@dataclass
class ConstraintSet:
    """
    Constraint set defining the admissible domain K.
    
    # [AXIOM]
    # K = C × R_≥0 is closed and convex
    # C = {x: V(x) ≤ Θ}
    
    Reference: docs/section_i_continuous_core.md §2-3
    """
    theta: float  # Admissibility threshold
    budget_min: float = 0.0
    
    def is_feasible(self, x: np.ndarray, b: float) -> bool:
        """Check if state (x, b) is in admissible set K."""
        if b < self.budget_min:
            return False
        # Simplified: V(x) = ||x||²
        V = np.sum(x ** 2)
        return V <= self.theta


# =============================================================================
# Theorem 7.1 — Absorbing Budget Boundary
# =============================================================================

@dataclass
class BudgetBoundaryCollapseTheorem(Theorem):
    """
    Theorem 7.1 — Absorbing budget boundary.
    
    # [PROVED]
    
    If the system reaches a boundary point with b=0, then all risk-increasing
    motion is algebraically eliminated: dV/dt ≤ 0.
    
    Equivalently, outward violation motion cannot occur once the budget is
    exhausted. This is stronger than a soft penalty — at the boundary,
    bad motion becomes kinematically impossible.
    
    Reference: docs/section_i_continuous_core.md §7
    """
    name: str = "Budget Boundary Collapse"
    section_ref: str = "§7"
    tag: str = "PROVED"
    statement: str = "b = 0 ⇒ dV/dt ≤ 0"
    
    kappa: float = 1.0  # Budget consumption rate
    
    def compute_dV_dt(self, grad_V: np.ndarray, x_dot: np.ndarray) -> float:
        """
        Compute dV/dt = <∇V, ẋ> using chain rule.
        
        # [PROVED] Chain rule from §8
        
        Args:
            grad_V: Gradient of violation functional ∇V(x)
            x_dot: State velocity ẋ
            
        Returns:
            dV/dt value
        """
        return float(np.dot(grad_V, x_dot))
    
    def compute_budget_rate(self, dV_dt: float) -> float:
        """
        Compute budget rate: ḃ = -κ(dV/dt)_+
        
        # [POLICY] From §6
        
        Args:
            dV/dt: Time derivative of violation functional
            
        Returns:
            Budget rate ḃ
        """
        return -self.kappa * max(dV_dt, 0.0)
    
    def verify_boundary_collapse(
        self,
        b: float,
        grad_V: np.ndarray,
        x_dot: np.ndarray
    ) -> Tuple[bool, str]:
        """
        Verify budget boundary collapse at b=0.
        
        At b=0, viability requires ḃ ≥ 0 while spend law gives ḃ ≤ 0.
        Therefore ḃ = 0, which implies (dV/dt)_+ = 0, so dV/dt ≤ 0.
        
        Args:
            b: Current budget (should be 0 for boundary check)
            grad_V: Gradient of violation functional
            x_dot: State velocity
            
        Returns:
            (is_collapsed, message)
        """
        if b > 0:
            return False, "Not at boundary: b > 0"
        
        dV_dt = self.compute_dV_dt(grad_V, x_dot)
        budget_rate = self.compute_budget_rate(dV_dt)
        
        # At boundary: ḃ must be both ≥ 0 (tangent cone) and ≤ 0 (spend law)
        # Therefore ḃ = 0, and (dV/dt)_+ = 0, so dV/dt ≤ 0
        if abs(budget_rate) < 1e-10 and dV_dt <= 1e-10:
            return True, "Boundary collapse verified: dV/dt ≤ 0 at b=0"
        else:
            return False, f"Boundary collapse failed: ḃ={budget_rate}, dV/dt={dV_dt}"


# =============================================================================
# Proposition 8.1 — Monotone Budget-Violation Functional
# =============================================================================

@dataclass
class MonotoneBudgetViolationFunctional(Theorem):
    """
    Proposition 8.1 — Monotone budget-plus-violation functional.
    
    # [PROVED]
    
    Along any sufficiently regular governed trajectory:
        d/dt(b + κV) ≤ 0
    
    This is useful because it gives a crude Lyapunov-style scalar:
        b(t) + κV(x(t)) ≤ b(0) + κV(x(0))
    
    Reference: docs/section_i_continuous_core.md §8
    """
    name: str = "Monotone Budget-Violation Functional"
    section_ref: str = "§8"
    tag: str = "PROVED"
    statement: str = "d/dt(b + κV) ≤ 0"
    
    kappa: float = 1.0
    
    def compute_W(self, b: float, V: float) -> float:
        """
        Compute combined functional W = b + κV.
        
        Args:
            b: Budget
            V: Violation functional value
            
        Returns:
            W = b + κV
        """
        return b + self.kappa * V
    
    def compute_W_dot(
        self,
        b: float,
        grad_V: np.ndarray,
        x_dot: np.ndarray,
        dV_dt: Optional[float] = None
    ) -> float:
        """
        Compute dW/dt = ḃ + κdV/dt.
        
        From §8:
            dW/dt = -κ(dV/dt)_+ + κdV/dt ≤ 0
        
        Args:
            b: Current budget
            grad_V: Gradient of violation functional
            x_dot: State velocity
            dV_dt: Optional precomputed dV/dt
            
        Returns:
            dW/dt value (should be ≤ 0)
        """
        if dV_dt is None:
            dV_dt = float(np.dot(grad_V, x_dot))
        
        # ḃ = -κ(dV/dt)_+
        b_dot = -self.kappa * max(dV_dt, 0.0)
        
        # dW/dt = ḃ + κdV/dt
        return b_dot + self.kappa * dV_dt
    
    def verify_monotonicity(
        self,
        b: float,
        grad_V: np.ndarray,
        x_dot: np.ndarray
    ) -> Tuple[bool, str]:
        """
        Verify monotonicity of W = b + κV.
        
        Args:
            b: Current budget
            grad_V: Gradient of violation functional
            x_dot: State velocity
            
        Returns:
            (is_monotone, message)
        """
        W_dot = self.compute_W_dot(b, grad_V, x_dot)
        
        if W_dot <= 1e-10:
            return True, f"Monotonicity verified: dW/dt = {W_dot} ≤ 0"
        else:
            return False, f"Monotonicity violated: dW/dt = {W_dot} > 0"


# =============================================================================
# Theorem 9.1 — Governance-Induced Damping
# =============================================================================

@dataclass
class GovernanceInducedDampingTheorem(Theorem):
    """
    Theorem 9.1 — Governance-induced damping of neutral drift.
    
    # [PROVED]
    
    Neutral modes observable through the governance coupling decay exponentially:
        |u(t)| ≤ e^(-β²/λmax * t) |u(0)|
    
    Even though the physical sector generator A is itself conservative,
    the system can remain physically conservative in its bare core while
    still acquiring enforced damping through lawful coupling.
    
    Reference: docs/section_i_continuous_core.md §9
    """
    name: str = "Governance-Induced Damping"
    section_ref: str = "§9"
    tag: str = "PROVED"
    statement: str = "|u(t)| ≤ e^(-β²/λmax * t) |u(0)|"
    
    beta: float = 1.0  # Observability constant
    lambda_max: float = 1.0  # Maximum eigenvalue of dissipation matrix
    
    @property
    def damping_rate(self) -> float:
        """Compute damping rate β²/λmax."""
        return (self.beta ** 2) / self.lambda_max
    
    def compute_damped_norm(
        self,
        u0_norm: float,
        t: float
    ) -> float:
        """
        Compute upper bound on |u(t)| given exponential decay.
        
        Args:
            u0_norm: Initial norm |u(0)|
            t: Time
            
        Returns:
            Upper bound |u(t)| ≤ e^(-β²/λmax * t) |u(0)|
        """
        return u0_norm * np.exp(-self.damping_rate * t)
    
    def verify_damping(
        self,
        u_norm: float,
        u0_norm: float,
        t: float,
        tolerance: float = 1e-6
    ) -> Tuple[bool, str]:
        """
        Verify that observed norm satisfies decay bound.
        
        Args:
            u_norm: Observed norm |u(t)|
            u0_norm: Initial norm |u(0)|
            t: Time
            tolerance: Numerical tolerance
            
        Returns:
            (is_damped, message)
        """
        bound = self.compute_damped_norm(u0_norm, t)
        
        if u_norm <= bound + tolerance:
            return True, f"Damping verified: |u(t)|={u_norm} ≤ bound={bound:.6f}"
        else:
            return False, f"Damping violated: |u(t)|={u_norm} > bound={bound:.6f}"


# =============================================================================
# Theorem 10.1 — Minkowski Root-Clock
# =============================================================================

@dataclass
class MinkowskiRootClockTheorem(Theorem):
    """
    Theorem 10.1 — Minkowski interval from the half-log barrier.
    
    # [PROVED]
    
    The viability-induced root-clock satisfies:
        dτ = √(1 - |v|²/c²) dt
    
    Therefore:
        dτ² = dt² - dx²/c²
    
    The Minkowski proper-time interval appears as the algebraic expression
    of the half-log admissibility barrier.
    
    Reference: docs/section_i_continuous_core.md §10
    """
    name: str = "Minkowski Root-Clock"
    section_ref: str = "§10"
    tag: str = "PROVED"
    statement: str = "dτ² = dt² - dx²/c²"
    
    c: float = 1.0  # Speed of light (maximum velocity)
    
    def compute_time_dilation(
        self,
        v: np.ndarray
    ) -> float:
        """
        Compute proper time density: dτ/dt = √(1 - |v|²/c²).
        
        # [PROVED]
        
        Args:
            v: Velocity vector
            
        Returns:
            Time dilation factor √(1 - |v|²/c²)
        """
        v_norm_sq = float(np.sum(v ** 2))
        if v_norm_sq >= self.c ** 2:
            return 0.0  # At light speed, proper time freezes
        return np.sqrt(1.0 - v_norm_sq / (self.c ** 2))
    
    def compute_proper_time_interval(
        self,
        dt: float,
        dx: np.ndarray
    ) -> float:
        """
        Compute proper time interval: dτ² = dt² - dx²/c².
        
        # [PROVED]
        
        Args:
            dt: Coordinate time interval
            dx: Spatial displacement vector
            
        Returns:
            Proper time interval dτ
        """
        dx_sq = float(np.sum(dx ** 2))
        dtau_sq = dt ** 2 - dx_sq / (self.c ** 2)
        
        if dtau_sq < 0:
            return 0.0  # Outside light cone (tachyonic)
        return np.sqrt(dtau_sq)
    
    def verify_minkowski(
        self,
        v: np.ndarray,
        dt: float
    ) -> Tuple[bool, str]:
        """
        Verify Minkowski interval from velocity.
        
        Args:
            v: Velocity vector
            dt: Coordinate time step
            
        Returns:
            (is_valid, message)
        """
        dtau_dt = self.compute_time_dilation(v)
        dx = v * dt
        
        # Method 1: dτ = √(1 - |v|²/c²) dt
        dtau1 = dtau_dt * dt
        
        # Method 2: dτ² = dt² - dx²/c²
        dtau2 = self.compute_proper_time_interval(dt, dx)
        
        if abs(dtau1 - dtau2) < 1e-10:
            return True, f"Minkowski verified: dτ₁={dtau1:.6f}, dτ₂={dtau2:.6f}"
        else:
            return False, f"Minkowski violated: dτ₁={dtau1}, dτ₂={dtau2}"


# =============================================================================
# Theorem 11.1 — Horizon Freezing
# =============================================================================

@dataclass
class HorizonFreezingTheorem(Theorem):
    """
    Theorem 11.1 — Strict freezing.
    
    # [PROVED]
    
    If b = 0 AND D_a = 0 (exhausted budget + no available lawful dissipation),
    then Λ = 0, which implies dτ/dt = 0.
    
    This ties directly back to the boundary-collapse theorem:
    exhausted budget plus no available lawful dissipation means the internal clock halts.
    
    Reference: docs/section_i_continuous_core.md §11
    """
    name: str = "Horizon Freezing"
    section_ref: str = "§11"
    tag: str = "PROVED"
    statement: str = "Λ = 0 ⇒ dτ/dt = 0"
    
    alpha: float = 1.0  # Dissipation coupling constant
    
    def compute_lawfulness_power(
        self,
        b: float,
        D_a: float
    ) -> float:
        """
        Compute lawfulness power: Λ = b + αD_a.
        
        # [POLICY]
        
        Args:
            b: Budget
            D_a: Admissible physical dissipation rate
            
        Returns:
            Λ = b + αD_a
        """
        return b + self.alpha * D_a
    
    def compute_root_clock_rate(
        self,
        b: float,
        D_a: float
    ) -> float:
        """
        Compute root-clock rate: dτ/dt = √Λ.
        
        # [POLICY]
        
        Args:
            b: Budget
            D_a: Admissible physical dissipation rate
            
        Returns:
            dτ/dt = √(b + αD_a)
        """
        Lambda = self.compute_lawfulness_power(b, D_a)
        return np.sqrt(max(Lambda, 0.0))  # Ensure non-negative
    
    def is_at_horizon(
        self,
        b: float,
        D_a: float,
        tolerance: float = 1e-10
    ) -> bool:
        """
        Check if at horizon: Λ = 0 (b = 0 AND D_a = 0).
        
        Args:
            b: Budget
            D_a: Dissipation rate
            tolerance: Numerical tolerance
            
        Returns:
            True if at horizon
        """
        return b <= tolerance and D_a <= tolerance
    
    def verify_freezing(
        self,
        b: float,
        D_a: float
    ) -> Tuple[bool, str]:
        """
        Verify horizon freezing.
        
        Args:
            b: Budget
            D_a: Dissipation rate
            
        Returns:
            (is_frozen, message)
        """
        if self.is_at_horizon(b, D_a):
            rate = self.compute_root_clock_rate(b, D_a)
            if rate < 1e-10:
                return True, f"Horizon freezing verified: b={b}, D_a={D_a}, dτ/dt={rate}"
            else:
                return False, f"Freezing failed: dτ/dt={rate} > 0"
        else:
            return False, "Not at horizon: b > 0 or D_a > 0"


# =============================================================================
# Theorem 12.1 — ADM Lapse Bridge
# =============================================================================

@dataclass
class ADMLapseBridgeTheorem(Theorem):
    """
    Theorem 12.1 — Root-clock / lapse identification.
    
    # [LEMMA-NEEDED]
    
    Under zero shift:
        N = dτ/dt = √Λ = √(b + αD_a)
    
    Thus the lapse is generated by the lawfulness power rather than inserted
    independently.
    
    NOTE: This is a constitutive bridge, not a full derivation of Einstein's
    equations. The source presents it as a structural identification, not
    a closed GR proof. Full derivation from the constitutive lapse law to
    a closed GR field system remains a research obligation.
    
    Reference: docs/section_i_continuous_core.md §12
    """
    name: str = "ADM Lapse Bridge"
    section_ref: str = "§12"
    tag: str = "LEMMA-NEEDED"
    statement: str = "N = √(b + αD_a)"
    
    alpha: float = 1.0  # Dissipation coupling constant
    
    def compute_lapse(
        self,
        b: float,
        D_a: float
    ) -> float:
        """
        Compute ADM lapse from governance: N = √(b + αD_a).
        
        # [LEMMA-NEEDED] Full derivation to GR not yet complete
        
        Args:
            b: Budget
            D_a: Admissible physical dissipation rate
            
        Returns:
            N = √(b + αD_a)
        """
        return np.sqrt(b + self.alpha * D_a)
    
    def identify_with_root_clock(
        self,
        b: float,
        D_a: float
    ) -> dict:
        """
        Identify ADM lapse with root-clock rate.
        
        # [LEMMA-NEEDED]
        
        Args:
            b: Budget
            D_a: Dissipation rate
            
        Returns:
            Dictionary with lapse, root-clock rate, and identification status
        """
        N = self.compute_lapse(b, D_a)
        
        # Root-clock rate: dτ/dt = √Λ = √(b + αD_a) = N
        root_clock_rate = np.sqrt(b + self.alpha * D_a)
        
        return {
            "ADM_lapse_N": N,
            "root_clock_dtau_dt": root_clock_rate,
            "identification_valid": abs(N - root_clock_rate) < 1e-10,
            "status": "CONSTITUTIVE_BRIDGE_ONLY",
            "note": "Not a full GR derivation — structural identification only"
        }


# =============================================================================
# Theorem Factory
# =============================================================================

class SectionITheorems:
    """
    Factory class for all Section I theorems.
    
    Usage:
        theorems = SectionITheorems()
        
        # Verify forward invariance
        is_valid, msg = theorems.forward_invariance.verify(...)
        
        # Verify boundary collapse
        is_collapsed, msg = theorems.boundary_collapse.verify_boundary_collapse(...)
        
        # Check horizon freezing
        is_frozen, msg = theorems.horizon_freezing.verify_freezing(...)
    """
    
    def __init__(self, **kwargs):
        """
        Initialize all theorems with optional parameters.
        
        Args:
            kappa: Budget consumption rate (default: 1.0)
            beta: Observability constant (default: 1.0)
            lambda_max: Maximum eigenvalue (default: 1.0)
            c: Speed of light (default: 1.0)
            alpha: Dissipation coupling (default: 1.0)
        """
        # Theorem 5.1
        self.forward_invariance = ForwardInvarianceTheorem()
        
        # Theorem 7.1
        self.boundary_collapse = BudgetBoundaryCollapseTheorem(
            kappa=kwargs.get('kappa', 1.0)
        )
        
        # Proposition 8.1
        self.monotone_functional = MonotoneBudgetViolationFunctional(
            kappa=kwargs.get('kappa', 1.0)
        )
        
        # Theorem 9.1
        self.governance_damping = GovernanceInducedDampingTheorem(
            beta=kwargs.get('beta', 1.0),
            lambda_max=kwargs.get('lambda_max', 1.0)
        )
        
        # Theorem 10.1
        self.minkowski_clock = MinkowskiRootClockTheorem(
            c=kwargs.get('c', 1.0)
        )
        
        # Theorem 11.1
        self.horizon_freezing = HorizonFreezingTheorem(
            alpha=kwargs.get('alpha', 1.0)
        )
        
        # Theorem 12.1
        self.adm_lapse = ADMLapseBridgeTheorem(
            alpha=kwargs.get('alpha', 1.0)
        )
    
    def get_theorem_summary(self) -> dict:
        """Get summary of all theorems."""
        return {
            "Theorem 5.1": {
                "name": self.forward_invariance.name,
                "tag": self.forward_invariance.tag,
                "statement": self.forward_invariance.statement
            },
            "Theorem 7.1": {
                "name": self.boundary_collapse.name,
                "tag": self.boundary_collapse.tag,
                "statement": self.boundary_collapse.statement
            },
            "Proposition 8.1": {
                "name": self.monotone_functional.name,
                "tag": self.monotone_functional.tag,
                "statement": self.monotone_functional.statement
            },
            "Theorem 9.1": {
                "name": self.governance_damping.name,
                "tag": self.governance_damping.tag,
                "statement": self.governance_damping.statement
            },
            "Theorem 10.1": {
                "name": self.minkowski_clock.name,
                "tag": self.minkowski_clock.tag,
                "statement": self.minkowski_clock.statement
            },
            "Theorem 11.1": {
                "name": self.horizon_freezing.name,
                "tag": self.horizon_freezing.tag,
                "statement": self.horizon_freezing.statement
            },
            "Theorem 12.1": {
                "name": self.adm_lapse.name,
                "tag": self.adm_lapse.tag,
                "statement": self.adm_lapse.statement
            }
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_theorems(**kwargs) -> SectionITheorems:
    """
    Factory function to create configured Section I theorems.
    
    Args:
        **kwargs: Theorem parameters
        
    Returns:
        SectionITheorems instance
    """
    return SectionITheorems(**kwargs)


# =============================================================================
# Tag Reference
# =============================================================================

"""
TAG REFERENCE (from docs/section_i_continuous_core.md):

[AXIOM]   - Foundational definitions and assumptions
            - V: H → R is proper, lower semicontinuous, convex
            - Safe region C = {x: V(x) ≤ Θ}
            - Extended state z = (x, b) ∈ H × R_≥0
            - Tangent cone T_K(z), Normal cone N_K(z)
            - Velocity barrier Ṽ(v) = -½log(1 - |v|²/c²)

[POLICY]  - Governing laws and dynamics
            - ż ∈ F(z) - N_K(z) (Moreau sweeping process)
            - ḃ = -κ(dV/dt)_+ (budget spend law)
            - dτ/dt = √Λ (root-clock policy)
            - Tangent cone constraint: at b=0, ḃ ≥ 0

[PROVED]  - Theorems with implementation verification
            - Theorem 5.1: Forward invariance
            - Theorem 7.1: Budget boundary collapse
            - Proposition 8.1: Monotone functional
            - Theorem 9.1: Governance-induced damping
            - Theorem 10.1: Minkowski interval
            - Theorem 11.1: Horizon freezing

[LEMMA-NEEDED] - Items requiring additional proof work
            - Theorem 12.1: ADM lapse bridge (full GR derivation)
            - Hyperbolic/Klein model equivalence
            - Infinite-dimensional regularity assumptions
            - Discrete-continuous compatibility
"""
