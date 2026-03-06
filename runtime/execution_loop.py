import os
import numpy as np
from core.state import State, V_PL, Instruction
from ledger.oplax_verifier import OplaxVerifier

def dynamics_step(state: State) -> tuple[Instruction, Instruction]:
    """
    Generates untrusted heuristic proposals based on current state.
    Returns: (explore_instruction, infer_instruction)
    """
    # EXPLORE: Large perturbation, high sigma, wide kappa envelope
    # Tuned: kappa=12 allows imagination when V(x) is low (e.g., ~2.0)
    # Inequality: V(x')+5 <= V(x)+12. With x=[1,1], V=2. If x'=[2,2], V'=8: 8+5=13 <= 2+12=14 ✓
    explore = Instruction("EXPLORE", lambda x: x + np.random.uniform(0.8, 1.2, size=len(x)), sigma=5.0, kappa=12.0)
    
    # INFER: Gradient-like local descent, low sigma, zero kappa
    # Tuned: Smaller gradient (0.1) to avoid overshooting when V is low
    infer = Instruction("INFER", lambda x: x - 0.1 * x, sigma=0.5, kappa=0.0)
    
    return explore, infer

def run_gmi_engine(initial_x: list[float], initial_budget: float, max_steps=20, artifact_file="outputs/receipts/receipts.jsonl"):
    """The Universal Execution Loop."""
    if os.path.exists(artifact_file):
        os.remove(artifact_file)
    
    # Create verifier with injected potential (no monkey-patching!)
    verifier = OplaxVerifier(potential_fn=V_PL)
        
    state = State(initial_x, initial_budget)
    print(f"=== GMI ENGINE BOOT ===")
    print(f"Initial State: {state.x}")
    print(f"Initial Tension (V_PL): {V_PL(state.x):.2f} | Initial Budget: {state.b:.2f}\n")
    
    step = 1
    with open(artifact_file, "a") as ledger_file:
        while step <= max_steps and V_PL(state.x) > 0.05:
            explore_instr, infer_instr = dynamics_step(state)
            
            # 1. Attempt Exploration (Imagination)
            accepted, next_state, receipt = verifier.check(step, state, explore_instr)
            
            if not accepted:
                # Log rejected explore attempt
                ledger_file.write(receipt.to_json() + "\n")
                
                # 2. Project to Constraint Boundary (Fallback to Logic)
                accepted, next_state, receipt = verifier.check(step, state, infer_instr)
            
            # Write final decision to ledger
            ledger_file.write(receipt.to_json() + "\n")
            
            if accepted:
                state = next_state
                print(f"Step {step}: [{receipt.op_code}] ACCEPTED. V_PL: {receipt.v_after:.2f} | Budget: {state.b:.2f}")
            else:
                print(f"Step {step}: [HALT] Paralysis. All viable directions rejected. {receipt.message}")
                break
                
            step += 1
            
    print(f"\n=== RUN COMPLETE ===")
    print(f"Final State: {state.x.round(3)} | Final Tension: {V_PL(state.x):.2f}")
    print(f"Proof artifact generated: {artifact_file}")

if __name__ == "__main__":
    # Test 2: Start with low tension. Watch phase transition from EXPLORE to INFER.
    run_gmi_engine(initial_x=[1.0, 1.0], initial_budget=15.0)
