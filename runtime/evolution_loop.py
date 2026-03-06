import numpy as np
import random
from core.state import State, Instruction
from core.embedder import GMI_Embedder
from core.memory import MemoryManifold
from ledger.oplax_verifier import OplaxVerifier

# --- Global Instantiations ---
embedder = GMI_Embedder()
memory = MemoryManifold(lambda_c=10.0)

def base_potential(x: np.ndarray) -> float:
    """Pure PhaseLoom potential without scars"""
    return float(np.sum(x**2))

def total_potential(x: np.ndarray) -> float:
    """Total tension = Base potential + Memory curvature"""
    return base_potential(x) + memory.read_curvature(x)

# Create verifier with injected potential (no monkey-patching!)
verifier = OplaxVerifier(potential_fn=total_potential)


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

    def generate_proposals(self, current_x) -> list:
        """Generate proposals with pre-computed x_prime to avoid double evaluation"""
        pool = []
        
        # Candidate 1: INFER (The conservative, logical baseline)
        # Pre-compute the proposal
        x_infer = current_x - 0.2 * current_x
        pool.append({
            'instr': Instruction("INFER (Logic)", lambda x: x - 0.2*x, sigma=0.5, kappa=0.0),
            'x_prime': x_infer
        })
        
        # Candidate 2: EXPLORE (A wild leap to an existing concept)
        vocab = list(self.embedder.vocab.keys())
        wild_word = random.choice(vocab)
        x_explore = self.embedder.embed(wild_word)
        pool.append({
            'instr': Instruction(f"EXPLORE ('{wild_word}')", lambda x: self.embedder.embed(wild_word), sigma=5.0, kappa=12.0),
            'x_prime': x_explore
        })
        
        # Candidate 3: INVENT (Symbolic Evolution - A totally new mathematical structure)
        noise = np.random.normal(0, 1.5 * self.temp, size=len(current_x))
        mutated_coord = current_x + noise
        glyph_id = f"glyph_{random.randint(1000, 9999)}"
        pool.append({
            'instr': Instruction(f"INVENT ({glyph_id})", lambda x: mutated_coord, sigma=8.0, kappa=25.0),
            'x_prime': mutated_coord
        })
        
        return pool


# --- 2. The Governing System (Strict Validator) ---
class NoeticanValidationEngine:
    """
    The NVE: The coherence verification layer.
    Takes the proposal pool and tests them against the thermodynamic ledger.
    Kills bad hypotheses, accepts valid ones, and scars the manifold for severe violations.
    """
    def __init__(self, verifier, memory):
        self.verifier = verifier
        self.memory = memory

    def filter_and_select(self, step_idx: int, state: State, proposal_pool: list):
        """
        Evaluate proposals and select the best one.
        
        Selection now uses: best energy descent per cost (efficiency score)
        Instead of: highest sigma (most expensive)
        """
        survivors = []
        
        for proposal in proposal_pool:
            instr = proposal['instr']
            x_prime = proposal['x_prime']
            
            # Evaluate with pre-computed proposal (avoid double evaluation)
            accepted, next_state, receipt = self.verifier.check(step_idx, state, instr, precomputed_x_prime=x_prime)
            
            if accepted:
                # Calculate efficiency score: descent per unit cost
                v_before = receipt.v_before
                v_after = receipt.v_after
                sigma = instr.sigma
                efficiency = (v_before - v_after) / max(sigma, 1e-6)
                
                survivors.append({
                    'instr': instr,
                    'next_state': next_state,
                    'receipt': receipt,
                    'efficiency': efficiency,
                    'descent': v_before - v_after
                })
            else:
                # If wild imagination or invention is rejected, scar the geometry
                if "INVENT" in instr.op_code or "EXPLORE" in instr.op_code:
                    print(f"    [SCAR] Writing geometric scar at {x_prime.round(2)}")
                    self.memory.write_scar(x_prime, penalty=5.0)
        
        # Selection: Pick highest efficiency (best descent per cost)
        if survivors:
            survivors.sort(key=lambda x: x['efficiency'], reverse=True)
            best = survivors[0]
            return True, (best['instr'], best['next_state'], best['receipt'])
            
        return False, None


# --- 3. The Execution Loop (Mutation -> Selection) ---
def run_gmi_evolution(initial_text="hypothesis", initial_budget=25.0, steps=10):
    npe = NoeticanProposalEngine(embedder)
    nve = NoeticanValidationEngine(verifier, memory)
    
    # Clear memory for fresh run
    memory.clear()
    
    state = State(embedder.embed(initial_text), initial_budget)
    
    print("=== GMI DUAL-DOMAIN EVOLUTION BOOT ===")
    print(f"Initial State: '{initial_text}' -> {state.x.round(2)}")
    
    # Track tensions separately
    base_t = base_potential(state.x)
    scar_t = memory.read_curvature(state.x)
    total_t = total_potential(state.x)
    
    print(f"Base Tension: {base_t:.2f} | Scar Tension: {scar_t:.2f} | Total Tension: {total_t:.2f}")
    print(f"Initial Budget: {state.b:.2f}\n")
    
    for i in range(1, steps + 1):
        if total_potential(state.x) < 0.1:
            break
            
        print(f"--- Step {i} ---")
        
        # 1. NPE Dreams (Wild Proposals)
        pool = npe.generate_proposals(state.x)
        print(f"NPE Proposed: {[p['instr'].op_code for p in pool]}")
        
        # 2. NVE Filters (Strict Selection with efficiency-based choice)
        success, result = nve.filter_and_select(i, state, pool)
        
        if success:
            instr, state, receipt = result
            print(f"NVE Selected: [ACCEPTED] {instr.op_code}")
            print(f"  -> Base Tension: {receipt.v_after:.2f} | Remaining Budget: {state.b:.2f}")
            print(f"  -> Efficiency Score: {(receipt.v_before - receipt.v_after) / max(instr.sigma, 1e-6):.2f}")
        else:
            print(f"NVE Selected: [HALT] All proposals rejected by the manifold. System exhausted.")
            break
        
        # Print separate tension components
        base_t = base_potential(state.x)
        scar_t = memory.read_curvature(state.x)
        total_t = total_potential(state.x)
        print(f"  -> [Tensions] Base: {base_t:.2f} | Scar: {scar_t:.2f} | Total: {total_t:.2f}\n")
            
    print(f"\n=== EVOLUTION COMPLETE ===")
    final_base = base_potential(state.x)
    final_scar = memory.read_curvature(state.x)
    final_total = total_potential(state.x)
    print(f"Final State: '{embedder.decode(state.x)}'")
    print(f"Final Base Tension: {final_base:.2f}")
    print(f"Final Scar Tension: {final_scar:.2f}")
    print(f"Final Total Tension: {final_total:.2f}")
    print(f"Total Scars on Manifold: {len(memory.scars)}")

if __name__ == "__main__":
    run_gmi_evolution()
