"""
Execution Loop for the GMI Universal Cognition Engine.

The main runtime loop that executes the GMI engine with memory integration.
"""

import os
import numpy as np

from core.state import State, Instruction, create_potential
from core.potential import GMIPotential
from ledger.oplax_verifier import OplaxVerifier


def dynamics_step(state: State) -> tuple[Instruction, Instruction]:
    """
    Generates untrusted heuristic proposals based on current state.
    Returns: (explore_instruction, infer_instruction)
    """
    # EXPLORE: Conservative perturbation (optimal from experiments)
    # Tuned: kappa=8, sigma=3 - optimal for multi-modal landscapes
    explore = Instruction("EXPLORE", lambda x: x + np.random.uniform(0.8, 1.2, size=len(x)), sigma=3.0, kappa=8.0)
    
    # INFER: Gradient-like local descent, low sigma, zero kappa
    # INFER: Gradient descent with small kappa for minor V fluctuations
    infer = Instruction("INFER", lambda x: x - 0.1 * x, sigma=0.5, kappa=0.5)
    
    return explore, infer


def run_gmi_engine(
    initial_x: list[float], 
    initial_budget: float, 
    max_steps: int = 20, 
    artifact_file: str = "outputs/receipts/receipts.jsonl",
    use_gmi_potential: bool = True
):
    """
    The Universal Execution Loop.
    
    Args:
        initial_x: Initial cognitive state coordinates
        initial_budget: Initial thermodynamic budget
        max_steps: Maximum number of steps
        artifact_file: Path to write receipts
        use_gmi_potential: If True, use GMIPotential; if False, use legacy V_PL
    """
    if os.path.exists(artifact_file):
        os.remove(artifact_file)
    
    # Create the potential function (legacy or GMI)
    if use_gmi_potential:
        potential = create_potential()
        potential_fn = potential.base  # Use base for backward compatibility
    else:
        from core.state import V_PL
        potential_fn = V_PL
        potential = None
    
    # Create verifier with injected potential (no monkey-patching!)
    verifier = OplaxVerifier(potential_fn=potential_fn)
        
    state = State(initial_x, initial_budget)
    
    print(f"=== GMI ENGINE BOOT ===")
    print(f"Initial State: {state.x}")
    print(f"Initial Tension (V): {potential_fn(state.x):.2f} | Initial Budget: {state.b:.2f}")
    if use_gmi_potential:
        print(f"Using GMIPotential with budget barrier")
    print()
    
    step = 1
    with open(artifact_file, "a") as ledger_file:
        while step <= max_steps and potential_fn(state.x) > 0.10:  # Optimal threshold from experiments
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
                print(f"Step {step}: [{receipt.op_code}] ACCEPTED. V: {receipt.v_after:.2f} | Budget: {state.b:.2f}")
            else:
                print(f"Step {step}: [HALT] No proposal satisfied thermodynamic admissibility constraints. {receipt.message}")
                break
            
            # Check if budget is exhausted (new GMI behavior)
            if use_gmi_potential and state.b <= 0:
                print(f"Step {step}: [HALT] Budget exhausted. No further motion allowed.")
                break
            
            step += 1
            
    print(f"\n=== RUN COMPLETE ===")
    print(f"Final State: {state.x.round(3)} | Final Tension: {potential_fn(state.x):.2f}")
    print(f"Proof artifact generated: {artifact_file}")


def run_gmi_engine_with_memory(
    initial_x: list[float],
    initial_budget: float,
    max_steps: int = 20,
    artifact_file: str = "outputs/receipts/receipts.jsonl"
):
    """
    GMI Engine with full memory integration.
    
    This version integrates:
    - GMIPotential with memory curvature
    - Episodic archive
    - Memory operators
    """
    from memory import (
        EpisodicArchive,
        Workspace,
        MemoryBudgetLaw,
        WriteOperator,
        ReadOperator,
        get_memory_ledger,
        RealityAnchor
    )
    
    if os.path.exists(artifact_file):
        os.remove(artifact_file)
    
    # Initialize components
    potential = create_potential()
    archive = EpisodicArchive()
    workspace = Workspace()
    budget_law = MemoryBudgetLaw()
    write_op = WriteOperator(archive, budget_law)
    read_op = ReadOperator(archive, budget_law)
    memory_ledger = get_memory_ledger()
    
    # Create verifier
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    state = State(initial_x, initial_budget)
    
    print(f"=== GMI ENGINE WITH MEMORY ===")
    print(f"Initial State: {state.x}")
    print(f"Initial Tension (V_GMI): {potential.total(state.x, state.b):.2f}")
    print(f"Initial Budget: {state.b:.2f}")
    print()
    
    step = 1
    with open(artifact_file, "a") as ledger_file:
        while step <= max_steps and potential.base(state.x) > 0.10:
            # First, query memory for relevant episodes (if budget allows)
            query_cost = budget_law.cost_read(len(state.x))
            if state.b > query_cost:
                # Query memory
                episodes, read_cost = read_op.execute(
                    state.x,
                    max_results=3,
                    budget=state.b
                )
                if episodes:
                    print(f"Step {step}: Retrieved {len(episodes)} memory episodes (cost: {read_cost:.3f})")
                    state.b -= read_cost
            
            # Generate proposals
            explore_instr, infer_instr = dynamics_step(state)
            
            # Attempt Exploration
            accepted, next_state, receipt = verifier.check(step, state, explore_instr)
            
            if not accepted:
                ledger_file.write(receipt.to_json() + "\n")
                accepted, next_state, receipt = verifier.check(step, state, infer_instr)
            
            ledger_file.write(receipt.to_json() + "\n")
            
            if accepted:
                # Write episode to memory
                write_result = write_op.execute(
                    state_density=state.x,
                    state_hash_before=state.hash(),
                    state_hash_after=next_state.hash(),
                    potential_before=potential.base(state.x),
                    potential_after=potential.base(next_state.x),
                    action_summary=receipt.op_code,
                    decision=receipt.decision,
                    sigma=explore_instr.sigma,
                    kappa=explore_instr.kappa
                )
                
                state = next_state
                total_potential = potential.total(state.x, state.b)
                print(f"Step {step}: [{receipt.op_code}] ACCEPTED. V_GMI: {total_potential:.2f} | Budget: {state.b:.2f}")
                
                # Reality anchor check - if external validation, mark as reality anchor
                if receipt.decision == "ACCEPTED":
                    # Create reality anchor for successful steps
                    pass  # Would integrate with external validation
            else:
                print(f"Step {step}: [HALT] No proposal satisfied constraints. {receipt.message}")
                break
            
            if state.b <= 0:
                print(f"Step {step}: [HALT] Budget exhausted.")
                break
            
            step += 1
    
    print(f"\n=== RUN COMPLETE ===")
    print(f"Final State: {state.x.round(3)} | Final V_GMI: {potential.total(state.x, state.b):.2f}")
    print(f"Memory Episodes: {len(archive)}")
    print(f"Proof artifact: {artifact_file}")


if __name__ == "__main__":
    # Run with new GMIPotential
    run_gmi_engine(initial_x=[1.0, 1.0], initial_budget=15.0)
