from core.state import State, CompositeInstruction
from ledger.receipt import Receipt

class OplaxVerifier:
    """
    Enforces the geometric and thermodynamic constraints of the GMI.
    Velocity is eliminated instantly if constraints are violated.
    
    The potential function V_PL is injected at construction time to avoid
    global monkey-patching of module state.
    """
    def __init__(self, potential_fn):
        """
        Args:
            potential_fn: Callable that computes V(x) - the cognitive tension
        """
        self.V_PL = potential_fn

    def verify_composition(self, instr: CompositeInstruction) -> tuple[bool, str]:
        """Enforces the Oplax Operator Algebra for chained thoughts."""
        # Metabolic Honesty: Cannot undercharge for composite work
        if instr.sigma < (instr.r1.sigma + instr.r2.sigma):
            return False, "[HALT] Oplax Violation: Metabolic Undercharge Detected (Counterfeit Thought!)."
        
        # Defect Monotonicity: Cannot launder debt
        if instr.kappa > (instr.r1.kappa + instr.r2.kappa):
            return False, "[HALT] Oplax Violation: Defect Laundering Detected."
            
        return True, "Valid composition."

    def check(self, step_idx: int, state: State, instr, precomputed_x_prime=None) -> tuple[bool, State, Receipt]:
        """
        Audits the transition against the governing thermodynamic laws.
        
        Args:
            step_idx: Current step number
            state: Current State
            instr: Instruction to verify
            precomputed_x_prime: Optional pre-computed proposal to avoid double evaluation
        """
        is_comp = isinstance(instr, CompositeInstruction)
        x_hash_before = state.hash()
        v_current = self.V_PL(state.x)
        
        # 1. Check Composition Algebra (if applicable)
        if is_comp:
            valid_comp, msg = self.verify_composition(instr)
            if not valid_comp:
                receipt = Receipt(step_idx, instr.op_code, x_hash_before, x_hash_before, v_current, v_current, instr.sigma, instr.kappa, state.b, state.b, is_comp, "HALT", msg)
                return False, state, receipt

        # 2. Evaluate Proposed State (use precomputed if available)
        if precomputed_x_prime is not None:
            x_prime = precomputed_x_prime
        else:
            x_prime = instr.pi(state.x)
            
        v_prime = self.V_PL(x_prime)
        
        # 3. Soundness Contract: Thermodynamic Inequality
        thermo_valid = (v_prime + instr.sigma) <= (v_current + instr.kappa)
        
        # 4. Budget Integrity
        b_prime = state.b - instr.sigma
        budget_valid = b_prime >= 0
        
        if not thermo_valid:
            msg = f"Thermodynamic Inequality Failed. V_prime({v_prime:.2f}) + sigma({instr.sigma}) > V({v_current:.2f}) + kappa({instr.kappa})"
            receipt = Receipt(step_idx, instr.op_code, x_hash_before, x_hash_before, v_current, v_prime, instr.sigma, instr.kappa, state.b, state.b, is_comp, "REJECTED", msg)
            return False, state, receipt
            
        if not budget_valid:
            msg = "Budget Exhausted. Cannot pay metabolic cost."
            receipt = Receipt(step_idx, instr.op_code, x_hash_before, x_hash_before, v_current, v_prime, instr.sigma, instr.kappa, state.b, state.b, is_comp, "REJECTED", msg)
            return False, state, receipt
            
        # 5. Commit Valid Transition - Use honest message
        new_state = State(x_prime, b_prime)
        
        # Honest message about what actually happened
        if v_prime < v_current:
            msg = "Step valid. Tension descent verified."
        elif v_prime == v_current:
            msg = "Step valid. Tension unchanged."
        else:
            msg = f"Step valid; tension increased within allowed defect (V: {v_current:.2f} -> {v_prime:.2f}, kappa: {instr.kappa})"
            
        receipt = Receipt(step_idx, instr.op_code, x_hash_before, new_state.hash(), v_current, v_prime, instr.sigma, instr.kappa, state.b, b_prime, is_comp, "ACCEPTED", msg)
        
        return True, new_state, receipt
