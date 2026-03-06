import numpy as np
import random
from core.state import State, Instruction
from ledger.oplax_verifier import OplaxVerifier
from core.embedder import GMI_Embedder
from core.memory import MemoryManifold

# --- Global Instantiations ---
embedder = GMI_Embedder()
memory = MemoryManifold(lambda_c=10.0)

def V_PL_with_memory(x: np.ndarray) -> float:
    """Tension = Base PhaseLoom potential + Memory Curvature"""
    return float(np.sum(x**2)) + memory.read_curvature(x)

# Wire the memory into the verifier's physics
import core.state
core.state.V_PL = V_PL_with_memory


# --- 1. The Dreaming System (Unconstrained Generator) ---
class NoeticanProposalEngine:
    """
    The NPE: A stochastic generator, a symbolic mutation engine.
    It does not know the rules. It does not check the budget.
    It proposes a 'pool' of candidates with intentionally high entropy.
    """
    def __init__(self, embedder, temperature=1.5):
        self.embedder = embedder
        self.temp = temperature

    def generate_proposals(self, current_x) -> list[Instruction]:
        pool = []
        
        # Candidate 1: INFER (The conservative, logical baseline)
        pool.append(Instruction("INFER (Logic)", lambda x: x - 0.2*x, sigma=0.5, kappa=0.0))
        
        # Candidate 2: EXPLORE (A wild leap to an existing concept)
        vocab = list(self.embedder.vocab.keys())
        wild_word = random.choice(vocab)
        pool.append(Instruction(f"EXPLORE ('{wild_word}')", lambda x: self.embedder.embed(wild_word), sigma=5.0, kappa=12.0))
        
        # Candidate 3: INVENT (Symbolic Evolution - A totally new mathematical structure)
        # We add high-variance noise to the current state to invent a coordinate that doesn't exist yet.
        noise = np.random.normal(0, 1.5 * self.temp, size=len(current_x))
        mutated_coord = current_x + noise
        glyph_id = f"glyph_{random.randint(1000, 9999)}"
        
        # Inventing new math is highly metabolically expensive, but carries a massive defect envelope
        pool.append(Instruction(f"INVENT ({glyph_id})", lambda x: mutated_coord, sigma=8.0, kappa=25.0))
        
        return pool


# --- 2. The Governing System (Strict Validator) ---
class NoeticanValidationEngine:
    """
    The NVE: The coherence verification layer.
    Takes the proposal pool (s') and tests s' ∈ K.
    Kills bad hypotheses, accepts valid ones, and scars the manifold for severe violations.
    """
    def __init__(self):
        self.verifier = OplaxVerifier()

    def filter_and_select(self, step_idx: int, state: State, proposal_pool: list[Instruction]):
        survivors = []
        
        for instr in proposal_pool:
            proposed_x = instr.pi(state.x)
            
            # The NVE projects the proposal against the thermodynamic ledger
            accepted, next_state, receipt = self.verifier.check(step_idx, state, instr)
            
            if accepted:
                survivors.append((instr, next_state, receipt))
            else:
                # If a wild imagination or invention step is rejected, it acts as an experiment failure.
                # The NVE "scars" the geometry so the NPE won't get stuck proposing it again.
                if "INVENT" in instr.op_code or "EXPLORE" in instr.op_code:
                    print(f"    [SCAR] Writing geometric scar at {proposed_x.round(2)}")
                    memory.write_scar(proposed_x, penalty=5.0)
                    
        # Selection Policy: If multiple proposals survive, pick the most "ambitious" one
        # (the one that burned the most budget to discover something new), otherwise fallback to logic.
        if survivors:
            # Sort by highest sigma (most ambitious work done) that was legally verified
            survivors.sort(key=lambda item: item[0].sigma, reverse=True)
            return True, survivors[0] # Return the winning candidate (instr, state, receipt)
            
        return False, None


# --- 3. The Execution Loop (Mutation -> Selection) ---
def run_gmi_evolution(initial_text="hypothesis", initial_budget=25.0, steps=10):
    npe = NoeticanProposalEngine(embedder)
    nve = NoeticanValidationEngine()
    
    state = State(embedder.embed(initial_text), initial_budget)
    
    print("=== GMI DUAL-DOMAIN EVOLUTION BOOT ===")
    print(f"Initial State: '{initial_text}' -> {state.x.round(2)}")
    print(f"Initial Tension: {V_PL_with_memory(state.x):.2f} | Budget: {state.b:.2f}\n")
    
    for i in range(1, steps + 1):
        if V_PL_with_memory(state.x) < 0.1:
            break
            
        print(f"--- Step {i} ---")
        
        # 1. NPE Dreams (Wild Proposals)
        pool = npe.generate_proposals(state.x)
        print(f"NPE Proposed: {[p.op_code for p in pool]}")
        
        # 2. NVE Filters (Strict Selection)
        success, winning_candidate = nve.filter_and_select(i, state, pool)
        
        if success:
            instr, state, receipt = winning_candidate
            print(f"NVE Selected: [ACCEPTED] {instr.op_code}")
            print(f"  -> New Tension: {receipt.v_after:.2f} | Remaining Budget: {state.b:.2f}")
        else:
            print(f"NVE Selected: [HALT] All proposals rejected by the manifold. System exhausted.")
            break
            
    print(f"\n=== EVOLUTION COMPLETE ===")
    print(f"Final Tension: {V_PL_with_memory(state.x):.2f} | Total Scars on Manifold: {len(memory.scars)}")

if __name__ == "__main__":
    run_gmi_evolution()
