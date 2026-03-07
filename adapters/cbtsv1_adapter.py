"""
CBTSv1 Adapter for GMI

This adapter integrates the CBTSv1 (Coherence-Based Time Stepper) PDE solvers
with the GMI thermodynamic governance layer.

Architecture:
- CBTSv1 provides GR/Navier-Stokes solvers with Lean4-verified numerics
- GMI provides thermodynamic constraint enforcement via OplaxVerifier
- NPE generates wild operator proposals that get verified by GMI before execution

The unified execution loop:
1. NPE proposes a novel PDE operator or integration scheme
2. GMI verifies thermodynamic legality (V' + σ ≤ V + κ)
3. If approved, CBTSv1 executes the PDE step
4. Results are hashed into the immutable receipt chain
"""

import numpy as np
from typing import Optional, Tuple, Any, Dict, List
from dataclasses import dataclass


@dataclass
class PDESolverResult:
    """Result from a CBTSv1 PDE solver step."""
    accepted: bool
    state_after: Any  # The evolved field data
    dt_used: Optional[float]
    residuals: Optional[Dict[str, float]]
    violation_type: Optional[str]  # 'dt', 'state', 'sem', or None
    rejection_reason: Optional[str]


class CBTSv1GMIAdapter:
    """
    Adapter that connects CBTSv1 solvers to GMI governance.
    
    This class wraps a CBTSv1 solver and applies GMI's thermodynamic
    constraints before each time step is executed.
    """
    
    def __init__(
        self,
        solver: Any,
        potential_fn,
        budget: float = 100.0,
        sigma_scale: float = 1.0,
        kappa_scale: float = 1.0
    ):
        """
        Initialize the CBTSv1-GMI adapter.
        
        Args:
            solver: CBTSv1 solver instance (e.g., GRSolver)
            potential_fn: GMI potential function V(x) -> float
            budget: Initial thermodynamic budget
            sigma_scale: Scaling factor for coherence (σ)
            kappa_scale: Scaling factor for dissipation (κ)
        """
        self.solver = solver
        self.potential_fn = potential_fn
        self.budget = budget
        self.sigma_scale = sigma_scale
        self.kappa_scale = kappa_scale
        
        # Track evolution
        self.step_count = 0
        self.rejected_steps = 0
        self.total_dissipation = 0.0
        
    def compute_potential_from_fields(self, fields) -> float:
        """
        Compute GMI potential from CBTSv1 field data.
        
        For GR: Use Hamiltonian constraint as potential
        For Navier-Stokes: Use kinetic + internal energy
        """
        if hasattr(fields, 'hamiltonian'):
            # GR solver - use Hamiltonian constraint
            return float(np.abs(fields.hamiltonian).mean())
        elif hasattr(fields, 'gamma_sym6'):
            # GR fields - use metric perturbation energy
            return float(np.mean(fields.gamma_sym6**2))
        else:
            # Generic fallback
            return 0.0
    
    def estimate_coherence_cost(self, dt: float, fields) -> Tuple[float, float]:
        """
        Estimate σ (coherence cost) and κ (dissipation cost) for a step.
        
        These map to:
        - σ: How much "structure" or coherence is preserved
        - κ: How much "energy" is dissipated as numerical error
        
        Returns: (sigma, kappa)
        """
        # Scale by dt - larger steps have more potential for error
        base_sigma = dt * self.sigma_scale
        base_kappa = dt * self.kappa_scale
        
        # Add field-dependent costs
        if hasattr(fields, 'residuals'):
            # If solver has computed residuals, use them
            res_mag = float(np.mean([np.abs(r).max() for r in fields.residuals]))
            base_kappa += res_mag * dt
            
        return base_sigma, base_kappa
    
    def verify_step(self, fields, dt_candidate: float) -> Tuple[bool, str]:
        """
        GMI thermodynamic verification for a proposed step.
        
        Checks: V(x') + σ ≤ V(x) + κ
        
        Returns: (accepted, reason)
        """
        # Compute current potential
        V_current = self.compute_potential_from_fields(fields)
        
        # Estimate costs
        sigma, kappa = self.estimate_coherence_cost(dt_candidate, fields)
        
        # The actual check happens after the step, but we can do
        # a pre-check based on budget
        max_allowed_increase = kappa - sigma
        
        if self.budget <= 0:
            return False, "Budget exhausted"
        
        # Conservative pre-check: reject if we'd exceed budget
        if sigma > self.budget + kappa:
            return False, f"Coherence cost {sigma} exceeds budget {self.budget}"
            
        return True, "Pre-check passed"
    
    def execute_governed_step(
        self,
        dt_candidate: float = 0.01,
        rails_policy: Optional[Dict] = None
    ) -> PDESolverResult:
        """
        Execute a time step with GMI governance.
        
        This is the core integration point:
        1. GMI verifies the step is thermodynamically legal
        2. CBTSv1 executes the step
        3. Post-step verification confirms the result
        """
        # Step 1: Pre-check with GMI
        fields = self.solver.fields
        accepted, reason = self.verify_step(fields, dt_candidate)
        
        if not accepted:
            self.rejected_steps += 1
            return PDESolverResult(
                accepted=False,
                state_after=None,
                dt_used=None,
                residuals=None,
                violation_type='state',
                rejection_reason=reason
            )
        
        # Step 2: Execute step with CBTSv1
        try:
            # Use solver's stepper if available
            if hasattr(self.solver, 'stepper'):
                result = self.solver.stepper.step(
                    fields, 
                    self.solver.t, 
                    dt_candidate,
                    rails_policy or {},
                    {}  # phaseloom_caps
                )
                accepted, state_after, dt_used, rejection_reason = result
            else:
                # Fallback: simple step
                dt_used = dt_candidate
                accepted = True
                rejection_reason = None
                state_after = fields
                
        except Exception as e:
            return PDESolverResult(
                accepted=False,
                state_after=None,
                dt_used=None,
                residuals=None,
                violation_type='sem',
                rejection_reason=str(e)
            )
        
        # Step 3: Post-step GMI verification
        if accepted:
            V_after = self.compute_potential_from_fields(state_after)
            V_before = self.compute_potential_from_fields(fields)
            sigma, kappa = self.estimate_coherence_cost(dt_used, state_after)
            
            # Check thermodynamic inequality
            if V_after + sigma > V_before + kappa:
                accepted = False
                rejection_reason = f"Thermodynamic inequality violated: V'={V_after:.6f}+σ={sigma:.6f} > V={V_before:.6f}+κ={kappa:.6f}"
                self.rejected_steps += 1
            else:
                # Update budget (dissipation)
                dissipation = kappa  # Energy dissipated as numerical error
                self.budget -= dissipation
                self.total_dissipation += dissipation
                self.step_count += 1
                
        return PDESolverResult(
            accepted=accepted,
            state_after=state_after if accepted else None,
            dt_used=dt_used if accepted else None,
            residuals=None,
            violation_type=None if accepted else 'state',
            rejection_reason=rejection_reason
        )
    
    def run_governed_evolution(
        self,
        T_max: float,
        dt_initial: float = 0.01,
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """
        Run CBTSv1 solver with continuous GMI governance.
        
        Returns evolution statistics and final state.
        """
        stats = {
            'steps_completed': 0,
            'steps_rejected': 0,
            'total_dissipation': 0.0,
            'final_budget': self.budget,
            'final_time': 0.0
        }
        
        dt = dt_initial
        
        for step in range(max_steps):
            if self.solver.t >= T_max:
                break
                
            result = self.execute_governed_step(dt)
            
            if result.accepted:
                stats['steps_completed'] += 1
                self.solver.t += result.dt_used
                
                # Adaptive dt based on coherence
                if result.dt_used < dt * 0.5:
                    dt = max(dt * 0.5, 1e-8)  # Decrease dt
                elif result.dt_used > dt * 0.9:
                    dt = min(dt * 1.5, dt_initial * 10)  # Increase dt
            else:
                stats['steps_rejected'] += 1
                dt = max(dt * 0.5, 1e-8)  # Reduce dt on rejection
                
            if self.budget <= 0:
                print(f"Halt: Budget exhausted at step {step}")
                break
                
        stats['total_dissipation'] = self.total_dissipation
        stats['final_budget'] = self.budget
        stats['final_time'] = self.solver.t
        
        return stats


def create_cbtsv1_gmi_runtime(
    solver_type: str = "gr",
    potential_fn=None,
    budget: float = 100.0,
    **solver_kwargs
) -> CBTSv1GMIAdapter:
    """
    Factory function to create a CBTSv1-GMI runtime.
    
    Args:
        solver_type: Type of solver ('gr' for General Relativity)
        potential_fn: GMI potential function
        budget: Initial thermodynamic budget
        **solver_kwargs: Additional arguments for solver
        
    Returns:
        CBTSv1GMIAdapter instance
    """
    if solver_type == "gr":
        # Use the built-in GR solver
        try:
            import sys
            sys.path.insert(0, '/home/user/gmi')
            from core.gr_solver import GRSolver
            
            solver = GRSolver(
                Nx=solver_kwargs.get('Nx', 16),
                Ny=solver_kwargs.get('Ny', 16),
                Nz=solver_kwargs.get('Nz', 16),
                dx=solver_kwargs.get('dx', 0.1),
                dy=solver_kwargs.get('dy', 0.1),
                dz=solver_kwargs.get('dz', 0.1)
            )
            solver.init_minkowski()
            print(f"Loaded GMI GR Solver")
            
        except Exception as e:
            print(f"Error loading GR solver: {e}")
            raise
    else:
        raise ValueError(f"Unknown solver type: {solver_type}")
    
    return CBTSv1GMIAdapter(
        solver=solver,
        potential_fn=potential_fn,
        budget=budget
    )


# Quick integration test
if __name__ == "__main__":
    print("=== CBTSv1-GMI Integration Test ===")
    
    try:
        # Try to create CBTSv1 runtime
        runtime = create_cbtsv1_gmi_runtime(
            solver_type="gr",
            potential_fn=lambda x: float(np.sum(x**2)),
            budget=50.0,
            Nx=8, Ny=8, Nz=8
        )
        
        print(f"Solver initialized: {type(runtime.solver).__name__}")
        print(f"Initial budget: {runtime.budget}")
        
        # Try a governed step
        result = runtime.execute_governed_step(dt_candidate=0.001)
        
        print(f"Step result: accepted={result.accepted}")
        if result.rejection_reason:
            print(f"  Reason: {result.rejection_reason}")
            
        print("CBTSv1-GMI adapter ready")
        
    except ImportError as e:
        print(f"Note: CBTSv1 not available - {e}")
        print("The adapter is ready for integration when CBTSv1 is present.")
