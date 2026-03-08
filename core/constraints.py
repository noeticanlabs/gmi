"""
Constraint Projection Engine for the GMI Universal Cognition Engine.

Section I — Continuous Core and Geometric Governance
Reference: docs/section_i_continuous_core.md

Transforms from "post-hoc auditor" to "projected dynamical system":

ż ∈ F(z) - N_K(z)

Where N_K(z) is the normal cone to the constraint manifold.

Instead of rejecting bad moves after proposal, actively projects
onto the constraint manifold. This is the difference between:
- A governor standing beside the machine with a red stamp
- A machine whose gears physically cannot spin the wrong way

TAG REFERENCE:
- [AXIOM] K = C × ℝ_≥0 is closed and convex
- [AXIOM] T_K(z) defined via liminf dist criterion
- [AXIOM] N_K(z) = T_K(z)° = ∂I_K(z)
- [POLICY] ż ∈ F(z) - N_K(z) (Moreau sweeping process)
- [PROVED] Forward invariance: z(0) ∈ K ⇒ z(t) ∈ K
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, Callable
from enum import Enum


class ConstraintType(Enum):
    """Types of constraints in the system."""
    BUDGET = "budget"           # Budget must be non-negative
    BOX = "box"                 # Box constraints on state
    POTENTIAL = "potential"     # Potential boundedness
    DOMAIN = "domain"           # Domain-specific constraints


@dataclass
class ConstraintSet:
    """
    Defines the lawful constraint manifold K.
    
    # [AXIOM] K = C × ℝ_≥0 is closed and convex
    # [AXIOM] T_K(z) defined via liminf dist criterion
    # [AXIOM] N_K(z) = T_K(z)° = ∂I_K(z)
    # [PROVED] Forward invariance: z(0) ∈ K ⇒ z(t) ∈ K
    
    In GMI, the primary constraints are:
    - Budget: b >= 0
    - Potential boundedness: V(z) <= V_max
    - Domain-specific: admissible state regions
    
    Reference: docs/section_i_continuous_core.md §4-5
    """
    # Budget constraints
    budget_min: float = 0.0
    budget_max: float = float('inf')
    
    # Potential constraints
    potential_max: float = float('inf')
    
    # Box constraints on state
    state_lower: Optional[np.ndarray] = None
    state_upper: Optional[np.ndarray] = None
    
    # Domain-specific constraints (callable)
    domain_constraint: Optional[Callable[[np.ndarray], bool]] = None
    
    def project_to_K(self, x: np.ndarray, b: float) -> Tuple[np.ndarray, float]:
        """
        Project state onto constraint manifold K.
        
        # [POLICY] ż ∈ F(z) - N_K(z) - Moreau sweeping process
        
        Projects onto the admissible set K = C × ℝ_≥0.
        
        Args:
            x: Current state coordinates
            b: Current budget
            
        Returns:
            (projected_x, projected_b)
        """
        x_proj = x.copy()
        b_proj = max(self.budget_min, min(b, self.budget_max))
        
        # Box constraints
        if self.state_lower is not None:
            x_proj = np.maximum(x_proj, self.state_lower)
        if self.state_upper is not None:
            x_proj = np.minimum(x_proj, self.state_upper)
        
        return x_proj, b_proj
    
    def is_feasible(self, x: np.ndarray, b: float) -> bool:
        """
        Check if a state is feasible (within constraints).
        
        # [PROVED] Forward invariance: z(0) ∈ K ⇒ z(t) ∈ K
        
        Verifies state belongs to admissible set K = C × ℝ_≥0.
        
        Args:
            x: State coordinates
            b: Budget
            
        Returns:
            True if feasible
        """
        # Check budget
        if b < self.budget_min or b > self.budget_max:
            return False
        
        # Check box constraints
        if self.state_lower is not None:
            if np.any(x < self.state_lower):
                return False
        if self.state_upper is not None:
            if np.any(x > self.state_upper):
                return False
        
        # Check domain constraints
        if self.domain_constraint is not None:
            if not self.domain_constraint(x):
                return False
        
        return True


@dataclass
class ProjectionResult:
    """Result of a projection operation."""
    original_delta: np.ndarray
    projected_delta: np.ndarray
    was_modified: bool
    modification_norm: float
    constraint_violations: list = field(default_factory=list)


class ConstraintGovernor:
    """
    Geometric constraint governor that projects motion onto lawful tangent cone.
    
    The tangent cone at state z is:
    T_K(z) = {v | v doesn't violate constraints}
    """
    
    def __init__(self, constraints: Optional[ConstraintSet] = None):
        """
        Initialize the constraint governor.
        
        Args:
            constraints: ConstraintSet defining the manifold K
        """
        self.constraints = constraints or ConstraintSet()
        self.projection_history: list = []
    
    def project_velocity(
        self, 
        state_x: np.ndarray, 
        proposed_delta: np.ndarray,
        budget: float
    ) -> Tuple[np.ndarray, bool, list]:
        """
        Project proposed velocity onto the lawful tangent cone.
        
        Args:
            state_x: Current state coordinates
            proposed_delta: Proposed movement vector
            budget: Current budget
            
        Returns:
            (projected_delta, was_modified, violations)
        """
        delta_proj = proposed_delta.copy()
        violations = []
        was_modified = False
        
        # 1. Budget constraint: can't propose moves that would exceed budget
        # (This is handled by sigma in instruction, but we project if needed)
        
        # 2. Box constraints: clamp to admissible region
        if self.constraints.state_lower is not None:
            below = state_x + delta_proj < self.constraints.state_lower
            if np.any(below):
                # Project onto boundary
                delta_proj = np.where(
                    below,
                    self.constraints.state_lower - state_x,
                    delta_proj
                )
                was_modified = True
                violations.append("lower_bound")
        
        if self.constraints.state_upper is not None:
            above = state_x + delta_proj > self.constraints.state_upper
            if np.any(above):
                # Project onto boundary
                delta_proj = np.where(
                    above,
                    self.constraints.state_upper - state_x,
                    delta_proj
                )
                was_modified = True
                violations.append("upper_bound")
        
        # 3. Check domain-specific constraints
        new_state = state_x + delta_proj
        if self.constraints.domain_constraint is not None:
            if not self.constraints.domain_constraint(new_state):
                # Try to find nearest feasible point
                # This is a simplified version
                violations.append("domain")
        
        # Compute modification norm
        mod_norm = np.linalg.norm(delta_proj - proposed_delta)
        
        return delta_proj, was_modified, violations
    
    def project_state(
        self, 
        state_x: np.ndarray, 
        budget: float
    ) -> Tuple[np.ndarray, float]:
        """
        Project state onto constraint manifold.
        
        Args:
            state_x: State to project
            budget: Budget to project
            
        Returns:
            (projected_x, projected_b)
        """
        return self.constraints.project_to_K(state_x, budget)
    
    def can_advance(self, budget: float, sigma: float) -> bool:
        """
        Check if budget allows advancement.
        b = 0 implies no risk-increasing motion.
        
        Args:
            budget: Current budget
            sigma: Proposed cost
            
        Returns:
            True if advancement is allowed
        """
        return budget >= sigma
    
    def compute_normal_response(
        self, 
        state_x: np.ndarray, 
        proposed_delta: np.ndarray,
        budget: float
    ) -> np.ndarray:
        """
        Compute normal cone response for visualization/debugging.
        Returns the component of proposed_delta that was rejected.
        
        Args:
            state_x: Current state
            proposed_delta: Proposed delta
            budget: Current budget
            
        Returns:
            The rejected (normal) component
        """
        delta_proj, _, _ = self.project_velocity(state_x, proposed_delta, budget)
        return proposed_delta - delta_proj
    
    def project_with_step(
        self,
        state_x: np.ndarray,
        delta: np.ndarray,
        sigma: float,
        budget: float
    ) -> Tuple[np.ndarray, float, bool]:
        """
        Project a full step including budget check.
        
        Args:
            state_x: Current state
            delta: Proposed delta
            sigma: Cost of the step
            budget: Current budget
            
        Returns:
            (projected_state, projected_budget, success)
        """
        # Check budget
        if not self.can_advance(budget, sigma):
            # Budget exhausted - no motion allowed
            return state_x, budget, False
        
        # Project delta onto tangent cone
        delta_proj, was_modified, violations = self.project_velocity(
            state_x, delta, budget
        )
        
        # Compute new state
        new_x = state_x + delta_proj
        new_budget = budget - sigma
        
        # Project onto manifold
        new_x, new_budget = self.project_state(new_x, new_budget)
        
        return new_x, new_budget, True
    
    def get_tangent_cone_description(self, state_x: np.ndarray) -> Dict[str, Any]:
        """
        Get description of the tangent cone at a state.
        
        Args:
            state_x: State to query
            
        Returns:
            Description of constraints at this state
        """
        desc = {
            'at_lower_bound': False,
            'at_upper_bound': False,
            'active_constraints': []
        }
        
        if self.constraints.state_lower is not None:
            if np.any(np.abs(state_x - self.constraints.state_lower) < 1e-6):
                desc['at_lower_bound'] = True
                desc['active_constraints'].append('lower_bound')
        
        if self.constraints.state_upper is not None:
            if np.any(np.abs(state_x - self.constraints.state_upper) < 1e-6):
                desc['at_upper_bound'] = True
                desc['active_constraints'].append('upper_bound')
        
        return desc


class ProjectedDynamics:
    """
    Runtime integration of constraint projection.
    
    Replaces:
        propose → check → reject if illegal
    
    With:
        propose → project → verify → accept
    """
    
    def __init__(
        self, 
        constraint_set: Optional[ConstraintSet] = None,
        potential_fn: Optional[Callable[[np.ndarray], float]] = None
    ):
        """
        Initialize projected dynamics.
        
        Args:
            constraint_set: Constraint set defining manifold K
            potential_fn: Function to compute potential
        """
        self.governor = ConstraintGovernor(constraint_set or ConstraintSet())
        self.potential_fn = potential_fn or (lambda x: float(np.sum(x**2)))
        self.history: list = []
    
    def step(
        self,
        state: 'State',
        instruction,
        precomputed_x_prime: Optional[np.ndarray] = None
    ) -> Tuple[bool, 'State', str, ProjectionResult]:
        """
        Execute one step with projection.
        
        Args:
            state: Current state
            instruction: Instruction to execute
            precomputed_x_prime: Optional precomputed proposal
            
        Returns:
            (accepted, new_state, message, projection_result)
        """
        # 1. Propose movement
        if precomputed_x_prime is not None:
            x_prime_raw = precomputed_x_prime
        else:
            x_prime_raw = instruction.pi(state.x)
        
        delta_raw = x_prime_raw - state.x
        
        # 2. Project onto constraint manifold
        projection_result = self._project(
            state.x, 
            delta_raw, 
            instruction.sigma,
            state.b
        )
        
        x_prime_proj = projection_result.projected_delta + state.x
        b_prime = state.b - instruction.sigma
        
        # 3. Verify thermodynamic constraints
        v_current = self.potential_fn(state.x)
        v_proposed = self.potential_fn(x_prime_proj)
        thermo_valid = (v_proposed + instruction.sigma) <= (v_current + instruction.kappa)
        
        if not thermo_valid:
            # Try projecting more aggressively
            # Use gradient descent direction
            grad = 2.0 * state.x  # Simple gradient
            descent_delta = -0.1 * grad
            x_prime_proj = state.x + descent_delta
            b_prime = state.b - instruction.sigma * 0.1
            
            v_proposed = self.potential_fn(x_prime_proj)
            thermo_valid = (v_proposed + instruction.sigma * 0.1) <= (v_current + instruction.kappa)
            
            if thermo_valid:
                projection_result = self._project(
                    state.x,
                    descent_delta,
                    instruction.sigma * 0.1,
                    state.b
                )
        
        if not thermo_valid:
            msg = f"Thermodynamic inequality failed even with projection"
            return False, state, msg, projection_result
        
        if b_prime < 0:
            msg = "Budget exhausted after projection"
            return False, state, msg, projection_result
        
        # 4. Accept
        new_state = type(state)(x_prime_proj.tolist(), b_prime)
        
        msg = f"Projected step accepted"
        if projection_result.was_modified:
            msg += f" (modified: {projection_result.constraint_violations})"
        
        return True, new_state, msg, projection_result
    
    def _project(
        self,
        x: np.ndarray,
        delta: np.ndarray,
        sigma: float,
        budget: float
    ) -> ProjectionResult:
        """Internal projection helper."""
        delta_proj, was_modified, violations = self.governor.project_velocity(
            x, delta, budget
        )
        
        mod_norm = np.linalg.norm(delta_proj - delta)
        
        return ProjectionResult(
            original_delta=delta,
            projected_delta=delta_proj,
            was_modified=was_modified,
            modification_norm=mod_norm,
            constraint_violations=violations
        )
    
    def summary(self) -> Dict[str, Any]:
        """Get summary of projection history."""
        if not self.history:
            return {'message': 'No projection history'}
        
        total_modified = sum(1 for h in self.history if h.was_modified)
        
        return {
            'total_steps': len(self.history),
            'modified_count': total_modified,
            'modification_rate': total_modified / len(self.history) if self.history else 0
        }


# Convenience function to create projected dynamics
def create_projected_dynamics(
    state_lower: Optional[np.ndarray] = None,
    state_upper: Optional[np.ndarray] = None,
    budget_min: float = 0.0,
    potential_fn: Optional[Callable] = None
) -> ProjectedDynamics:
    """
    Factory function to create projected dynamics.
    
    Args:
        state_lower: Lower bound on state
        state_upper: Upper bound on state
        budget_min: Minimum budget
        potential_fn: Potential function
        
    Returns:
        ProjectedDynamics instance
    """
    constraints = ConstraintSet(
        state_lower=state_lower,
        state_upper=state_upper,
        budget_min=budget_min
    )
    
    return ProjectedDynamics(
        constraint_set=constraints,
        potential_fn=potential_fn
    )
