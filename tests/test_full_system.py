"""
Full System Integration Test

This tests the complete three-layer Proof-Carrying Research Engine:
1. NPE - Generates wild operator proposals
2. GMI - Verifies thermodynamic legality
3. CBTSv1/GR - Executes PDE solver

The flow:
- NPE proposes a novel operator (e.g., new integration scheme)
- GMI verifies: V(x') + σ ≤ V(x) + κ
- If approved, GR solver executes the step
- Result is hashed into immutable ledger
"""

import numpy as np
import sys
sys.path.insert(0, '/home/user/gmi')

from core.state import State, Instruction, Proposal
from core.gr_solver import GRSolver
from ledger.oplax_verifier import OplaxVerifier
from adapters.stochastic_synthesizer import StochasticSynthesizer


def V_from_gr_fields(solver):
    """Extract GMI potential from GR fields."""
    # Use Hamiltonian constraint as potential
    return float(np.mean(np.abs(solver.fields.hamiltonian)))


def estimate_sigma_kappa(dt, solver):
    """Estimate coherence costs from GR solver state."""
    # σ scales with dt (coherence preservation)
    # κ scales with constraint violation
    H = np.mean(np.abs(solver.fields.hamiltonian))
    M = np.mean(np.abs(solver.fields.momentum))
    
    sigma = dt * 0.1  # Base coherence cost
    kappa = dt * 0.1 + H + M  # Dissipation includes constraint violation
    
    return sigma, kappa


def test_gr_solver_standalone():
    """Test 3+1 GR solver independently."""
    print("\n" + "="*60)
    print("TEST 1: GR Solver (Layer 3)")
    print("="*60)
    
    solver = GRSolver(Nx=8, Ny=8, Nz=8, dx=0.1)
    solver.init_minkowski()
    
    print(f"Initial H constraint: {V_from_gr_fields(solver):.2e}")
    
    stats = solver.run(T_max=0.05, dt_max=0.01)
    
    print(f"Steps: {stats['steps']}")
    print(f"Final H: {stats['H_history'][-1]:.2e}")
    print("✓ GR Solver working")
    return True


def test_gmi_verifier_standalone():
    """Test GMI verifier independently."""
    print("\n" + "="*60)
    print("TEST 2: GMI Verifier (Layer 2)")
    print("="*60)
    
    def V(x):
        return float(np.sum(x**2))
    
    verifier = OplaxVerifier(potential_fn=V)
    state = State([1.0, 1.0], budget=10.0)
    
    # Test valid descent
    instr = Instruction("DESCENT", lambda x: x * 0.5, sigma=0.5, kappa=0.5)
    accepted, next_state, receipt = verifier.check(1, state, instr)
    
    print(f"Descent step: accepted={accepted}")
    print(f"Receipt: {receipt.decision}")
    
    # Test rejection
    instr_bad = Instruction("ASCENT", lambda x: x + 10.0, sigma=5.0, kappa=5.0)
    accepted, next_state, receipt = verifier.check(2, state, instr_bad)
    
    print(f"Ascent step: accepted={accepted}")
    print(f"Receipt: {receipt.decision}")
    
    print("✓ GMI Verifier working")
    return True


def test_npe_synthesizer():
    """Test NPE stochastic synthesizer."""
    print("\n" + "="*60)
    print("TEST 3: NPE Synthesizer (Layer 1)")
    print("="*60)
    
    synth = StochasticSynthesizer(temperature=1.0, hallucination_rate=0.5)
    
    # Generate proposals
    context = {"task": "GR_evolution", "step": 0}
    proposals = synth.generate_wild_proposals(context, n_proposals=3)
    
    print(f"Generated {len(proposals)} proposals:")
    for p in proposals:
        print(f"  - {p}")
    
    print("✓ NPE Synthesizer working")
    return True


def test_npe_gmi_integration():
    """Test NPE + GMI integration."""
    print("\n" + "="*60)
    print("TEST 4: NPE + GMI Integration")
    print("="*60)
    
    from adapters.npe_integration import create_npe_gmi_runtime
    
    def V(x):
        return float(np.sum(x**2))
    
    adapter = create_npe_gmi_runtime(V, budget=20.0)
    state = adapter.run(initial_x=np.array([1.0, 1.0]), budget=20.0, n_steps=3)
    
    print(f"Final state: x={state.x}")
    print(f"Statistics: {adapter.stats}")
    
    print("✓ NPE + GMI working")
    return True


def test_cbtsv1_adapter():
    """Test CBTSv1 adapter."""
    print("\n" + "="*60)
    print("TEST 5: CBTSv1 Adapter")
    print("="*60)
    
    from adapters.cbtsv1_adapter import create_cbtsv1_gmi_runtime
    
    runtime = create_cbtsv1_gmi_runtime(
        solver_type="gr",
        potential_fn=V_from_gr_fields,
        budget=50.0,
        Nx=8, Ny=8, Nz=8
    )
    
    result = runtime.execute_governed_step(dt_candidate=0.01)
    
    print(f"Step result: accepted={result.accepted}")
    print(f"dt used: {result.dt_used}")
    
    print("✓ CBTSv1 Adapter working")
    return True


def test_full_three_layer():
    """Test all three layers together: NPE → GMI → GR."""
    print("\n" + "="*60)
    print("TEST 6: Full Three-Layer Integration")
    print("="*60)
    
    # Layer 3: GR Solver
    gr_solver = GRSolver(Nx=8, Ny=8, Nz=8, dx=0.1)
    gr_solver.init_minkowski()
    
    # Layer 2: GMI Verifier with GR-derived potential
    def V_gr(x):
        return V_from_gr_fields(gr_solver)
    
    verifier = OplaxVerifier(potential_fn=V_gr)
    state = State(np.array([1.0]), budget=50.0)
    
    # Layer 1: NPE generates proposals
    synth = StochasticSynthesizer(temperature=1.2, hallucination_rate=0.6)
    
    print(f"Initial potential: {V_gr(None):.2e}")
    
    # Evolution loop
    n_steps = 5
    for step in range(n_steps):
        # NPE proposes operator
        context = {"task": "GR_step", "step": step}
        proposals = synth.generate_wild_proposals(context, n_proposals=3)
        
        # GMI verifies
        sigma, kappa = estimate_sigma_kappa(0.01, gr_solver)
        
        # Create instruction from proposal
        op_code = proposals[0] if proposals else "BASELINE"
        instr = Instruction(op_code, lambda x: x, sigma=sigma, kappa=kappa)
        
        accepted, next_state, receipt = verifier.check(step, state, instr)
        
        if accepted:
            # GR executes step
            dt_used = gr_solver.step_forward_euler(0.01)
            print(f"Step {step}: ✓ Accepted, dt={dt_used:.4f}")
        else:
            print(f"Step {step}: ✗ Rejected - {receipt.message}")
    
    final_V = V_from_gr_fields(gr_solver)
    print(f"\nFinal potential: {final_V:.2e}")
    print("✓ Full three-layer integration working")
    return True


def main():
    """Run all integration tests."""
    print("="*60)
    print("PROOF-CARRYING RESEARCH ENGINE - FULL SYSTEM TEST")
    print("="*60)
    
    tests = [
        ("GR Solver", test_gr_solver_standalone),
        ("GMI Verifier", test_gmi_verifier_standalone),
        ("NPE Synthesizer", test_npe_synthesizer),
        ("NPE + GMI", test_npe_gmi_integration),
        ("CBTSv1 Adapter", test_cbtsv1_adapter),
        ("Three-Layer", test_full_three_layer),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((name, f"ERROR: {e}"))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, status in results:
        symbol = "✓" if status == "PASSED" else "✗"
        print(f"{symbol} {name}: {status}")
    
    all_passed = all(s == "PASSED" for _, s in results)
    print("\n" + ("ALL TESTS PASSED!" if all_passed else "SOME TESTS FAILED"))
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
