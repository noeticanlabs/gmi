import os
import random
import numpy as np
from core.state import State, V_PL, Instruction
from ledger.oplax_verifier import OplaxVerifier
from core.embedder import GMI_Embedder 

# Instantiate the semantic bridge
embedder = GMI_Embedder()

def semantic_dynamics_step(state: State) -> tuple[Instruction, Instruction]:
    """
    The 'Untrusted LLM' proposing text strings.
    The physics engine embeds these strings and audits their thermodynamic cost.
    """
    # Simulated LLM "Imagination" (High Temperature)
    # EXPLORE: Add the semantic vector to current position (relative jump)
    explore_words = ["brainstorm", "idea", "hypothesis", "guess", "chaos"]
    chosen_explore = random.choice(explore_words)
    explore_vector = embedder.embed(chosen_explore)
    
    # Simulated LLM "Logic" (Low Temperature)
    # INFER: Move TOWARD the logical concept (relative gradient descent)
    infer_words = ["axiom", "proof", "logic"]
    chosen_infer = random.choice(infer_words)
    infer_vector = embedder.embed(chosen_infer)

    # EXPLORE: Attempt a creative jump (optimized sigma/kappa)
    explore_instr = Instruction(
        op_code=f"EXPLORE ('{chosen_explore}')", 
        pi_func=lambda x: x + 0.3 * explore_vector,  # Scaled creative jump
        sigma=3.0, 
        kappa=8.0  # Optimal from experiments
    )
    
    # INFER: Move toward logical concept (optimized)
    infer_instr = Instruction(
        op_code=f"INFER ('{chosen_infer}')", 
        pi_func=lambda x: x - 0.3 * (x - infer_vector),  # Move toward the concept
        sigma=0.5, 
        kappa=0.5   # Optimized: allows minor V fluctuations
    )
    
    return explore_instr, infer_instr

def run_semantic_engine(initial_text: str, initial_budget: float, max_steps=15):
    """The Semantic Execution Loop."""
    artifact_file = "outputs/receipts/semantic_receipts.jsonl"
    if os.path.exists(artifact_file):
        os.remove(artifact_file)
    
    # Create verifier with injected potential (no monkey-patching!)
    verifier = OplaxVerifier(potential_fn=V_PL)
        
    # Embed the initial prompt into physics
    initial_x = embedder.embed(initial_text)
    state = State(initial_x, initial_budget)
    
    print(f"=== SEMANTIC GMI ENGINE BOOT ===")
    print(f"Prompt: '{initial_text}' -> Physical Coordinates: {state.x.round(2)}")
    print(f"Initial Tension (V_PL): {V_PL(state.x):.2f} | Initial Budget: {state.b:.2f}\n")
    
    step = 1
    with open(artifact_file, "a") as ledger_file:
        while step <= max_steps and V_PL(state.x) > 0.10:  # Optimal threshold
            explore_instr, infer_instr = semantic_dynamics_step(state)
            
            # 1. Attempt the creative word
            accepted, next_state, receipt = verifier.check(step, state, explore_instr)
            
            if not accepted:
                ledger_file.write(receipt.to_json() + "\n")
                print(f"Step {step}: [REJECTED] {explore_instr.op_code}. Tension too high for budget.")
                
                # 2. Fallback to the logical word
                accepted, next_state, receipt = verifier.check(step, state, infer_instr)
            
            ledger_file.write(receipt.to_json() + "\n")
            
            if accepted:
                state = next_state
                # Project the physical state back to language
                current_concept = embedder.decode(state.x)
                print(f"Step {step}: [{receipt.op_code}] ACCEPTED. Mind state: '{current_concept}' (V_PL: {receipt.v_after:.2f}, Budget: {state.b:.2f})")
            else:
                print(f"Step {step}: [HALT] No proposal satisfied thermodynamic admissibility constraints. {receipt.message}")
                break
                
            step += 1
            
    print(f"\n=== RUN COMPLETE ===")
    print(f"Final State: '{embedder.decode(state.x)}' | Tension: {V_PL(state.x):.2f}")

if __name__ == "__main__":
    # Test: Start with higher-tension prompt to allow exploration first
    # "hypothesis" has V=8.0, allowing EXPLORE to succeed before collapsing to logic
    run_semantic_engine(initial_text="hypothesis", initial_budget=20.0)
