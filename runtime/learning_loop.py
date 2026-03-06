import os
import random
import numpy as np
from core.state import State, Instruction
from ledger.oplax_verifier import OplaxVerifier
from core.embedder import GMI_Embedder
from core.memory import MemoryManifold

embedder = GMI_Embedder()
memory = MemoryManifold(lambda_c=10.0)  # High penalty for touching the stove

def V_PL_with_memory(x: np.ndarray) -> float:
    """The total cognitive tension: Base PhaseLoom potential + Memory Curvature"""
    base_tension = float(np.sum(x**2))
    curvature_tension = memory.read_curvature(x)
    return base_tension + curvature_tension

# Create verifier with injected potential (no monkey-patching!)
verifier = OplaxVerifier(potential_fn=V_PL_with_memory)

def semantic_dynamics_step(state: State, attempt_type="chaos") -> tuple[Instruction, Instruction]:
    """
    Stubbornly propose the same expensive word to watch memory repel it.
    Uses smaller jumps to allow more exploration attempts.
    """
    # Try different words based on attempt type
    if attempt_type == "chaos":
        chosen_explore = "chaos" 
        explore_vector = embedder.embed(chosen_explore)
        # Absolute jump to chaos coordinates
        explore_instr = Instruction(
            f"EXPLORE ('{chosen_explore}')", 
            lambda x: explore_vector,
            sigma=5.0, 
            kappa=12.0
        )
    else:
        # Try a moderate jump
        chosen_explore = "brainstorm"
        explore_vector = embedder.embed(chosen_explore)
        explore_instr = Instruction(
            f"EXPLORE ('{chosen_explore}')", 
            lambda x: x + explore_vector * 0.3,  # Scaled jump
            sigma=3.0, 
            kappa=10.0
        )
    
    infer_words = ["axiom", "proof", "logic"]
    chosen_infer = random.choice(infer_words)
    infer_vector = embedder.embed(chosen_infer)

    # INFER: Move toward logical concept (small gradient step)
    infer_instr = Instruction(
        f"INFER ('{chosen_infer}')", 
        lambda x: x - 0.2 * x,  # Gradient descent
        sigma=0.5, 
        kappa=0.5
    )
    
    return explore_instr, infer_instr

def run_learning_engine(initial_text: str, initial_budget: float, max_steps=8):
    artifact_file = "outputs/receipts/learning_receipts.jsonl"
    if os.path.exists(artifact_file):
        os.remove(artifact_file)
        
    # Clear memory for fresh run
    memory.clear()
        
    initial_x = embedder.embed(initial_text)
    state = State(initial_x, initial_budget)
    
    print(f"=== GMI MEMORY ENGINE BOOT ===")
    print(f"Prompt: '{initial_text}' -> Physical Coordinates: {state.x.round(2)}")
    print(f"Initial Tension: {V_PL_with_memory(state.x):.2f} | Initial Budget: {state.b:.2f}")
    print(f"Scars on manifold: {len(memory.scars)}\n")
    
    step = 1
    with open(artifact_file, "a") as ledger_file:
        while step <= max_steps and V_PL_with_memory(state.x) > 0.1:
            # Cycle between chaos attempts to show memory scarring
            attempt = "chaos" if step <= 3 else "brainstorm"
            explore_instr, infer_instr = semantic_dynamics_step(state, attempt)
            
            # Evaluate tension BEFORE checking (for display)
            proposed_x = explore_instr.pi(state.x)
            tension_before = V_PL_with_memory(proposed_x)
            
            # 1. Attempt the creative word
            accepted, next_state, receipt = verifier.check(step, state, explore_instr)
            
            if not accepted:
                # Log rejected attempt
                receipt.v_before = V_PL_with_memory(state.x)
                receipt.v_after = tension_before
                ledger_file.write(receipt.to_json() + "\n")
                
                print(f"Step {step}: [REJECTED] {explore_instr.op_code}.")
                print(f"  Tension at rejected coordinate: {tension_before:.2f}")
                
                # TRIGGER MEMORY GEOMETRY: The system burns its hand on the stove
                print(f"  -> [WRITE] Scarring manifold at {proposed_x.round(2)}")
                memory.write_scar(proposed_x, penalty=5.0)
                print(f"  -> Curvature at that coordinate now: {memory.read_curvature(proposed_x):.2f}\n")
                
                # 2. Fallback to logic
                accepted, next_state, receipt = verifier.check(step, state, infer_instr)
            
            if accepted:
                # Update receipt with memory-augmented tension
                receipt.v_before = V_PL_with_memory(state.x)
                receipt.v_after = V_PL_with_memory(next_state.x)
                ledger_file.write(receipt.to_json() + "\n")
                
                state = next_state
                current_concept = embedder.decode(state.x)
                tension_now = V_PL_with_memory(state.x)
                print(f"Step {step}: [{receipt.op_code}] ACCEPTED. Mind state: '{current_concept}'")
                print(f"  Tension: {tension_now:.2f} | Budget: {state.b:.2f} | Scars: {len(memory.scars)}\n")
            else:
                print(f"Step {step}: [HALT] Paralysis. {receipt.message}\n")
                break
                
            step += 1
            
    print(f"=== RUN COMPLETE ===")
    print(f"Final State: '{embedder.decode(state.x)}' | Tension: {V_PL_with_memory(state.x):.2f}")
    print(f"Total scars written: {len(memory.scars)}")

if __name__ == "__main__":
    run_learning_engine(initial_text="hypothesis", initial_budget=20.0)
