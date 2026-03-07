"""
Runtime Projection Integration for the GMI Universal Cognition Engine.

Provides integration of constraint projection into the runtime loop.
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any

from core.constraints import (
    ConstraintSet,
    ConstraintGovernor,
    ProjectedDynamics,
    create_projected_dynamics,
    ProjectionResult
)
from core.state import State
from core.potential import GMIPotential


class ProjectedRuntime:
    """
    Runtime that uses projected dynamics instead of reject-after-propose.
    
    This replaces the traditional:
        propose → check → reject if illegal
    
    With:
        propose → project → verify → accept
    """
    
    def __init__(
        self,
        potential: Optional[GMIPotential] = None,
        state_lower: Optional[np.ndarray] = None,
        state_upper: Optional[np.ndarray] = None,
        budget_min: float = 0.0
    ):
        """
        Initialize projected runtime.
        
        Args:
            potential: GMIPotential instance
            state_lower: Lower bound on state
            state_upper: Upper bound on state
            budget_min: Minimum budget
        """
        self.potential = potential or GMIPotential()
        
        # Create projected dynamics
        self.projected_dynamics = create_projected_dynamics(
            state_lower=state_lower,
            state_upper=state_upper,
            budget_min=budget_min,
            potential_fn=self.potential.base
        )
        
        # Statistics
        self.total_steps = 0
        self.accepted_steps = 0
        self.projected_steps = 0
        self.rejected_steps = 0
    
    def step(
        self,
        state: State,
        instruction,
        precomputed_x_prime: Optional[np.ndarray] = None
    ) -> Tuple[bool, State, str, Dict[str, Any]]:
        """
        Execute one step with projection.
        
        Args:
            state: Current state
            instruction: Instruction to execute
            precomputed_x_prime: Optional precomputed proposal
            
        Returns:
            (accepted, new_state, message, info)
        """
        self.total_steps += 1
        
        # Use projected dynamics
        accepted, new_state, message, proj_result = self.projected_dynamics.step(
            state, instruction, precomputed_x_prime
        )
        
        if accepted:
            self.accepted_steps += 1
            if proj_result.was_modified:
                self.projected_steps += 1
        else:
            self.rejected_steps += 1
        
        info = {
            'projection_result': proj_result,
            'potential_before': self.potential.base(state.x),
            'potential_after': self.potential.base(new_state.x),
            'budget_before': state.b,
            'budget_after': new_state.b
        }
        
        return accepted, new_state, message, info
    
    def run(
        self,
        initial_x: list,
        initial_budget: float,
        instructions_generator,
        max_steps: int = 20,
        convergence_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        Run the projected dynamics loop.
        
        Args:
            initial_x: Initial state
            initial_budget: Initial budget
            instructions_generator: Generator yielding instructions
            max_steps: Maximum steps
            convergence_threshold: Stop when potential < this
            
        Returns:
            Run summary
        """
        state = State(initial_x, initial_budget)
        
        steps_log = []
        
        while self.total_steps < max_steps:
            # Check convergence
            if self.potential.base(state.x) < convergence_threshold:
                break
            
            # Check budget
            if state.b <= 0:
                break
            
            # Get next instruction
            try:
                instruction = next(instructions_generator)
            except StopIteration:
                break
            
            # Execute step with projection
            accepted, new_state, message, info = self.step(state, instruction)
            
            steps_log.append({
                'step': self.total_steps,
                'accepted': accepted,
                'message': message,
                'potential': info['potential_after'],
                'budget': info['budget_after'],
                'was_projected': info['projection_result'].was_modified
            })
            
            if accepted:
                state = new_state
                print(f"Step {self.total_steps}: ACCEPTED - {message}")
            else:
                print(f"Step {self.total_steps}: REJECTED - {message}")
        
        return {
            'final_state': state,
            'total_steps': self.total_steps,
            'accepted': self.accepted_steps,
            'rejected': self.rejected_steps,
            'projected': self.projected_steps,
            'final_potential': self.potential.base(state.x),
            'final_budget': state.b,
            'steps_log': steps_log
        }
    
    def summary(self) -> Dict[str, Any]:
        """Get runtime summary."""
        return {
            'total_steps': self.total_steps,
            'accepted': self.accepted_steps,
            'rejected': self.rejected_steps,
            'projected': self.projected_steps,
            'acceptance_rate': self.accepted_steps / max(1, self.total_steps),
            'projection_rate': self.projected_steps / max(1, self.accepted_steps)
        }


def create_projected_runtime(
    potential: Optional[GMIPotential] = None,
    state_bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    budget_min: float = 0.0
) -> ProjectedRuntime:
    """
    Factory to create projected runtime.
    
    Args:
        potential: GMIPotential instance
        state_bounds: Tuple of (lower, upper) bounds
        budget_min: Minimum budget
        
    Returns:
        ProjectedRuntime
    """
    state_lower = state_bounds[0] if state_bounds else None
    state_upper = state_bounds[1] if state_bounds else None
    
    return ProjectedRuntime(
        potential=potential,
        state_lower=state_lower,
        state_upper=state_upper,
        budget_min=budget_min
    )
