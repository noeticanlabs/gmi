import numpy as np

# --- 1. State and Potential ---
class State:
    def __init__(self, x, budget):
        self.x = np.array(x, dtype=float)
        self.b = budget

def V(x): return np.sum(x**2)

# --- 2. Instructions ---
class Instruction:
    def __init__(self, name, pi_func, sigma, kappa):
        self.name = name
        self.pi = pi_func
        self.sigma = sigma
        self.kappa = kappa

class CompositeInstruction:
    def __init__(self, r1, r2, claimed_sigma, claimed_kappa):
        self.r1 = r1
        self.r2 = r2
        self.name = f"({r2.name} ⊙ {r1.name})"
        self.pi = lambda x: r2.pi(r1.pi(x))
        # This is where a system might try to lie to the ledger:
        self.sigma = claimed_sigma
        self.kappa = claimed_kappa

# --- 3. The Oplax Verifier ---
class OplaxVerifier:
    @staticmethod
    def verify_composition(r1, r2, composite_r):
        """Checks the structural integrity of the composite receipt."""
        # 1. Metabolic Honesty: Can't undercharge for the work done
        valid_spend = composite_r.sigma >= (r1.sigma + r2.sigma)
        
        # 2. Defect Monotonicity: Can't launder debt
        valid_defect = composite_r.kappa <= (r1.kappa + r2.kappa)
        
        return valid_spend, valid_defect

    @staticmethod
    def check(state, instr):
        """Audits the step against the thermodynamic inequality."""
        # If it's a composite instruction, verify the ledger algebra first
        if isinstance(instr, CompositeInstruction):
            valid_spend, valid_defect = OplaxVerifier.verify_composition(instr.r1, instr.r2, instr)
            if not valid_spend:
                return False, "[HALT] Oplax Violation: Metabolic Undercharge Detected (Counterfeit Thought!)."
            if not valid_defect:
                return False, "[HALT] Oplax Violation: Defect Laundering Detected."

        x_prime = instr.pi(state.x)
        v_current = V(state.x)
        v_prime = V(x_prime)
        
        # The Core Soundness Contract
        thermo_valid = (v_prime + instr.sigma) <= (v_current + instr.kappa)
        budget_valid = (state.b - instr.sigma) >= 0
        
        if not thermo_valid: 
            return False, f"[REJECTED] Thermodynamic Inequality Failed. V_prime({v_prime:.2f}) + sigma({instr.sigma}) > V({v_current:.2f}) + kappa({instr.kappa})"
        if not budget_valid: 
            return False, "[REJECTED] Budget Exhausted."
            
        return True, f"[ACCEPTED] Valid Step. V changed: {v_current:.2f} -> {v_prime:.2f}"

# --- 4. The Counterfeit Thought Experiment ---
def run_ledger_test():
    state = State([1.0, 1.0], budget=15.0)
    print(f"INITIAL STATE: x={state.x}, Budget={state.b:.2f}, V={V(state.x):.2f}\n")

    # Define the base instructions
    # r1: An expensive, chaotic imagination jump
    r1_explore = Instruction("EXPLORE", lambda x: x + np.array([1.5, 1.5]), sigma=5.0, kappa=8.0)
    
    # r2: A cheap, logical proof step down the gradient
    r2_infer = Instruction("INFER", lambda x: x - 0.2 * x, sigma=0.5, kappa=0.0)

    print("--- ATTEMPT 1: The Counterfeit Thought ---")
    print("System explores wildly, finds a good state, but tries to claim it only did pure logic.")
    # The system lies about the true cost, claiming it only costs 1.0 instead of the true 5.5
    counterfeit_thought = CompositeInstruction(r1_explore, r2_infer, claimed_sigma=1.0, claimed_kappa=0.0)
    
    success, message = OplaxVerifier.check(state, counterfeit_thought)
    print(message, "\n")

    print("--- ATTEMPT 2: The Honest Chain ---")
    print("System submits the true metabolic cost of the explore + infer chain.")
    # The system honestly reports the sum of the sigmas and kappas
    honest_thought = CompositeInstruction(r1_explore, r2_infer, claimed_sigma=5.5, claimed_kappa=8.0)
    
    success, message = OplaxVerifier.check(state, honest_thought)
    print(message)

run_ledger_test()
