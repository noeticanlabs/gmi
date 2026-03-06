"""
DEMO / RESEARCH SCRIPT
Not canonical runtime implementation.
This file demonstrates thermodynamic cognition concepts.
"""

import numpy as np

# --- 1. The Governed State ---
class State:
    def __init__(self, x, budget):
        self.x = np.array(x, dtype=float)  # Continuous cognition state
        self.b = budget                    # Thermodynamic budget

    def clone(self):
        return State(self.x.copy(), self.b)

# --- 2. The PhaseLoom Potential (Incoherence) ---
def V(x):
    # A simple convex potential well. 
    # The "Mind" wants to reach [0, 0] (zero tension).
    return np.sum(x**2)

# --- 3. The Instruction Set Architecture (Coh-IL) ---
class OpCode:
    EXPLORE = "EXPLORE"  # Stochastic/creative jump (moves uphill)
    INFER = "INFER"      # Logic/proof step (moves downhill)

class Instruction:
    def __init__(self, op, pi_func, sigma, kappa):
        self.op = op
        self.pi = pi_func    # Proposal: State transformer
        self.sigma = sigma   # Spend: Metabolic cost
        self.kappa = kappa   # Defect: Allowed undercharge / PV envelope

# --- 4. The Oplax Verifier ---
class Verifier:
    @staticmethod
    def check(state, instr):
        # 1. Propose new state
        x_prime = instr.pi(state.x)
        
        # 2. Evaluate potentials
        v_current = V(state.x)
        v_prime = V(x_prime)
        
        # 3. Thermodynamic Inequality (Soundness Contract)
        # V(x') + sigma <= V(x) + kappa
        thermo_valid = (v_prime + instr.sigma) <= (v_current + instr.kappa)
        
        # 4. Budget Update & Constraint
        b_prime = state.b - instr.sigma
        budget_valid = b_prime >= 0
        
        # 5. Tangent Cone Guard (Simplified: Are we within absolute bounds?)
        guard_valid = np.all(np.abs(x_prime) < 100.0) 

        if thermo_valid and budget_valid and guard_valid:
            return True, x_prime, b_prime, v_current, v_prime
        else:
            return False, None, None, v_current, v_prime

# --- 5. The Execution Loop (The "Mind" in Motion) ---
def run_trajectory(initial_x, initial_budget, steps=10):
    state = State(initial_x, initial_budget)
    print(f"INITIAL STATE: x={state.x}, Budget={state.b:.2f}, V={V(state.x):.2f}\n")
    print("-" * 50)

    for i in range(steps):
        print(f"--- Step {i+1} ---")
        
        # Define candidate moves from the current state
        
        # A) EXPLORE (Imagination Jump): Perturbs into higher V, high sigma, high kappa
        def explore_pi(x): return x + np.random.uniform(0.5, 1.5, size=2)
        explore_instr = Instruction(OpCode.EXPLORE, explore_pi, sigma=5.0, kappa=8.0)
        
        # B) INFER (Logic Descent): Local descent, V goes down, tiny sigma, zero kappa
        def infer_pi(x): return x - 0.2 * x  # Simple gradient step toward 0
        infer_instr = Instruction(OpCode.INFER, infer_pi, sigma=0.5, kappa=0.0)

        # The Engine tries to EXPLORE first (imagination prioritization)
        accepted, x_new, b_new, v_old, v_new = Verifier.check(state, explore_instr)
        
        if accepted:
            print(f"[ACCEPTED] {OpCode.EXPLORE}: Imagined new state.")
            print(f"  V changed: {v_old:.2f} -> {v_new:.2f} (Uphill)")
            print(f"  Paid sigma={explore_instr.sigma}, used kappa envelope={explore_instr.kappa}")
            state.x = x_new
            state.b = b_new
        else:
            # If EXPLORE fails (e.g., budget is too low), fallback to INFER
            print(f"[REJECTED] {OpCode.EXPLORE}: Insufficient budget or thermodynamic violation.")
            
            accepted_infer, x_new_inf, b_new_inf, v_old_inf, v_new_inf = Verifier.check(state, infer_instr)
            if accepted_infer:
                print(f"[ACCEPTED] {OpCode.INFER}: Collapsed to logic descent.")
                print(f"  V changed: {v_old_inf:.2f} -> {v_new_inf:.2f} (Downhill)")
                print(f"  Paid sigma={infer_instr.sigma}")
                state.x = x_new_inf
                state.b = b_new_inf
            else:
                print(f"[HALT] {OpCode.INFER} rejected. Mind is paralyzed (Budget 0).")
                break
                
        print(f"CURRENT STATE: x={state.x.round(2)}, Budget={state.b:.2f}\n")

# ============================================================================
# EXPERIMENT 1: Depleted State (x=[5,5]) - EXPLORE fails, collapses to INFER
# ============================================================================
print("\n" + "="*70)
print("EXPERIMENT 1: Depleted Cognitive State (x=[5.0, 5.0])")
print("="*70 + "\n")
run_trajectory(initial_x=[5.0, 5.0], initial_budget=12.0, steps=8)

# ============================================================================
# EXPERIMENT 2: Enriched State (x=[1,1]) with larger kappa - EXPLORE succeeds
# ============================================================================
def run_enriched_trajectory(initial_x, initial_budget, steps=10):
    """Modified trajectory with EXPLORE tuned to succeed"""
    state = State(initial_x, initial_budget)
    print(f"\n{'='*70}")
    print(f"EXPERIMENT 2: Enriched Cognitive State (x={initial_x})")
    print(f"{'='*70}\n")
    print(f"INITIAL STATE: x={state.x}, Budget={state.b:.2f}, V={V(state.x):.2f}\n")
    print("-" * 50)

    for i in range(steps):
        print(f"--- Step {i+1} ---")
        
        # A) EXPLORE - TUNED: Larger kappa envelope to allow imagination jumps
        # With initial V(x)=2, exploring to ~[2,2] gives V(x')=8
        # Inequality: 8 + 5 <= 2 + 10  → 13 <= 12 (still tight!)
        # Let's use kappa=15 for breathing room
        def explore_pi(x): return x + np.random.uniform(0.8, 1.2, size=2)
        explore_instr = Instruction(OpCode.EXPLORE, explore_pi, sigma=5.0, kappa=15.0)
        
        # B) INFER - Same as before
        def infer_pi(x): return x - 0.2 * x
        infer_instr = Instruction(OpCode.INFER, infer_pi, sigma=0.5, kappa=0.0)

        # Try EXPLORE first
        accepted, x_new, b_new, v_old, v_new = Verifier.check(state, explore_instr)
        
        if accepted:
            print(f"[ACCEPTED] {OpCode.EXPLORE}: Creative imagination leap!")
            print(f"  V changed: {v_old:.2f} -> {v_new:.2f} (Uphill - imagination)")
            print(f"  Paid sigma={explore_instr.sigma}, kappa envelope={explore_instr.kappa}")
            state.x = x_new
            state.b = b_new
        else:
            print(f"[REJECTED] {OpCode.EXPLORE}: Thermodynamic violation.")
            
            accepted_infer, x_new_inf, b_new_inf, v_old_inf, v_new_inf = Verifier.check(state, infer_instr)
            if accepted_infer:
                print(f"[ACCEPTED] {OpCode.INFER}: Logic descent.")
                print(f"  V changed: {v_old_inf:.2f} -> {v_new_inf:.2f} (Downhill)")
                print(f"  Paid sigma={infer_instr.sigma}")
                state.x = x_new_inf
                state.b = b_new_inf
            else:
                print(f"[HALT] {OpCode.INFER} rejected. Mind paralyzed.")
                break
                
        print(f"CURRENT STATE: x={state.x.round(2)}, Budget={state.b:.2f}\n")

# Run the tuned experiment
run_enriched_trajectory(initial_x=[1.0, 1.0], initial_budget=15.0, steps=8)
