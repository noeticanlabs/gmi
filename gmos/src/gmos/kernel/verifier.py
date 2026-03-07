"""
Verifier for GM-OS Kernel.

Enforces geometric and thermodynamic constraints for GM-OS processes.
Provides Oplax verification with reserve law enforcement.

Note: This is a self-contained version that defines its own types
rather than depending on core.state or ledger.receipt.
"""

from typing import Callable, Optional, Any, Dict, List, Tuple
from dataclasses import dataclass, field

# Try to import numpy, fall back to list-based if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False


# === Local type definitions (previously imported from core.state and ledger) ===

@dataclass
class State:
    """Minimal state representation for GM-OS kernel."""
    x: Any  # Can be np.ndarray or list
    b: float  # budget
    process_id: str = ""
    step: int = 0
    
    def copy(self) -> 'State':
        if HAS_NUMPY and isinstance(self.x, np.ndarray):
            return State(x=self.x.copy(), b=self.b, process_id=self.process_id, step=self.step)
        return State(x=self.x[:] if isinstance(self.x, list) else self.x, b=self.b, process_id=self.process_id, step=self.step)


@dataclass 
class CompositeInstruction:
    """Composite instruction for Oplax operations."""
    r1: Any  # First instruction
    r2: Any  # Second instruction
    sigma: float  # Combined cost
    kappa: float  # Combined defect
    compose_type: str = "sequence"


@dataclass
class Proposal:
    """A proposal for state transition."""
    x_prime: Any  # Proposed next state (can be list or np.ndarray)
    cost: float = 0.0
    defect: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Receipt:
    """Minimal receipt for verification."""
    receipt_id: str
    process_id: str
    step: int
    accepted: bool
    state_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# === Verifier Config ===

@dataclass
class VerifierConfig:
    """Configuration for the OplaxVerifier."""
    reserve_floor: float = 1.0
    # Dynamic reserve parameters
    alpha: float = 0.5  # pressure scaling
    beta: float = 0.3   # uncertainty scaling
    gamma: float = 0.2  # branch load scaling


# === Main Verifier Class ===

class OplaxVerifier:
    """
    Enforces the geometric and thermodynamic constraints of the GMI.
    Velocity is eliminated instantly if constraints are violated.
    
    RESERVE LAW: The verifier also enforces the Reserve Law - a protected
    minimum budget that must be preserved after every non-emergency action.
    
    Admissible(a) => b_next >= b_reserve
    
    This prevents "locally rational but strategically suicidal" moves that
    exhaust budget for immediate gain but destroy future viability.
    """
    
    def __init__(
        self, 
        potential_fn: Any = None, 
        reserve_floor: float = 1.0,
        alpha: float = 0.5,
        beta: float = 0.3,
        gamma: float = 0.2
    ):
        """
        Args:
            potential_fn: Callable that computes V(x), OR GMIPotential instance.
                         If GMIPotential is passed, uses .total() method.
            reserve_floor: Protected minimum budget (b_reserve). Default: 1.0
                          Moves that would drive budget below this are rejected.
            alpha: Pressure scaling for dynamic reserve
            beta: Uncertainty scaling for dynamic reserve
            gamma: Branch load scaling for dynamic reserve
        """
        self.V_PL = potential_fn
        self.reserve_floor = reserve_floor
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        
        # Detect if we're using GMIPotential or simple callable
        self._is_full_potential = (
            hasattr(potential_fn, 'total') and 
            callable(getattr(potential_fn, 'total'))
        )
    
    def compute_reserve(
        self, 
        budget: float,
        pressure: float = 0.0,
        uncertainty: float = 0.0,
        branch_load: float = 0.0
    ) -> float:
        """
        Dynamic prudential reserve formula.
        
        b_reserve = r0 + α⋅pressure + β⋅uncertainty + γ⋅branch_load
        
        This makes the system prudential rather than merely conservative.
        """
        base_reserve = self.reserve_floor
        return base_reserve + self.alpha * pressure + self.beta * uncertainty + self.gamma * branch_load
    
    def _compute_v_current(self, state: State) -> float:
        """Compute potential using appropriate method."""
        if self._is_full_potential and self.V_PL is not None:
            # Use full GMIPotential.total()
            return self.V_PL.total(state.x, state.b)
        elif self.V_PL is not None:
            # Legacy: simple callable
            return self.V_PL(state.x)
        return 0.0
    
    def verify_composition(self, instr: CompositeInstruction) -> Tuple[bool, str]:
        """Enforces the Oplax Operator Algebra for chained thoughts."""
        # Metabolic Honesty: Cannot undercharge for composite work
        if hasattr(instr, 'sigma') and hasattr(instr, 'r1') and hasattr(instr, 'r2'):
            if instr.sigma < (instr.r1.sigma + instr.r2.sigma):
                return False, "[HALT] Oplax Violation: Metabolic Undercharge Detected."
        
        # Defect Monotonicity: Cannot launder debt
        if hasattr(instr, 'kappa'):
            if instr.kappa > (instr.r1.kappa + instr.r2.kappa):
                return False, "[HALT] Oplax Violation: Defect Laundering Detected."
                
        return True, "Valid composition."
    
    def check(
        self, 
        step_idx: int, 
        state: State, 
        proposal: Proposal,
        budget_next: float,
        precomputed_v_next: Optional[float] = None,
        memory: Any = None,
        domain_metrics: Optional[Dict[str, float]] = None,
        episodic_penalty: float = 0.0
    ) -> Tuple[bool, State, Receipt]:
        """
        Audits the transition against the governing thermodynamic laws.
        
        Args:
            step_idx: Current step number
            state: Current state
            proposal: Proposed transition
            budget_next: Budget after transition
            precomputed_v_next: Precomputed potential value (optional)
            memory: Memory context (optional)
            domain_metrics: Domain-specific metrics (optional)
            episodic_penalty: Penalty for episodic violations
            
        Returns:
            Tuple of (accepted, new_state, receipt)
        """
        import uuid
        
        # Compute current potential
        v_current = self._compute_v_current(state)
        
        # Compute next potential
        if precomputed_v_next is not None:
            v_next = precomputed_v_next
        elif self._is_full_potential and self.V_PL is not None:
            v_next = self.V_PL.total(proposal.x_prime, budget_next)
        elif self.V_PL is not None:
            v_next = self.V_PL(proposal.x_prime)
        else:
            v_next = 0.0
        
        # === RESERVE LAW CHECK ===
        # Compute dynamic reserve requirement
        pressure = domain_metrics.get("pressure", 0.0) if domain_metrics else 0.0
        uncertainty = domain_metrics.get("uncertainty", 0.0) if domain_metrics else 0.0
        branch_load = domain_metrics.get("branch_load", 0.0) if domain_metrics else 0.0
        
        reserve_required = self.compute_reserve(
            budget_next, pressure, uncertainty, branch_load
        )
        
        # Check reserve law
        if budget_next < reserve_required:
            receipt = Receipt(
                receipt_id=str(uuid.uuid4())[:8],
                process_id=state.process_id,
                step=step_idx,
                accepted=False,
                metadata={
                    "reason": "reserve_violation",
                    "budget_next": budget_next,
                    "reserve_required": reserve_required,
                    "v_current": v_current,
                    "v_next": v_next
                }
            )
            return False, state, receipt
        
        # === VELOCITY CHECK (for valid proposals) ===
        velocity = v_next - v_current
        if velocity > 0:  # Velocity must be <= 0 (non-increasing potential)
            receipt = Receipt(
                receipt_id=str(uuid.uuid4())[:8],
                process_id=state.process_id,
                step=step_idx,
                accepted=False,
                metadata={
                    "reason": "velocity_violation",
                    "v_current": v_current,
                    "v_next": v_next,
                    "velocity": velocity
                }
            )
            return False, state, receipt
        
        # === ACCEPT THE TRANSITION ===
        new_state = State(
            x=proposal.x_prime,
            b=budget_next,
            process_id=state.process_id,
            step=step_idx + 1
        )
        
        receipt = Receipt(
            receipt_id=str(uuid.uuid4())[:8],
            process_id=state.process_id,
            step=step_idx,
            accepted=True,
            metadata={
                "v_current": v_current,
                "v_next": v_next,
                "cost": proposal.cost,
                "defect": proposal.defect
            }
        )
        
        return True, new_state, receipt
    
    def verify_lawful_move(
        self,
        state: State,
        proposal: Proposal,
        budget_next: float,
        domain_metrics: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, str]:
        """
        Simplified verification for checking if a move is lawful.
        
        Returns:
            Tuple of (is_lawful, reason)
        """
        # Check reserve law
        pressure = domain_metrics.get("pressure", 0.0) if domain_metrics else 0.0
        uncertainty = domain_metrics.get("uncertainty", 0.0) if domain_metrics else 0.0
        branch_load = domain_metrics.get("branch_load", 0.0) if domain_metrics else 0.0
        
        reserve_required = self.compute_reserve(
            budget_next, pressure, uncertainty, branch_load
        )
        
        if budget_next < reserve_required:
            return False, f"Reserve violation: need {reserve_required}, have {budget_next}"
        
        # Check velocity constraint
        v_current = self._compute_v_current(state)
        
        if self._is_full_potential and self.V_PL is not None:
            v_next = self.V_PL.total(proposal.x_prime, budget_next)
        elif self.V_PL is not None:
            v_next = self.V_PL(proposal.x_prime)
        else:
            v_next = 0.0
        
        if v_next - v_current > 0:
            return False, f"Velocity violation: {v_next - v_current} > 0"
        
        return True, "lawful"
