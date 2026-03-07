"""
Benchmark Suite for Proof-Carrying Research Engine

This benchmark tests:
1. Capability: What the system can do
2. Performance: How fast it runs

Metrics tracked:
- Constraint preservation (GR Hamiltonian/Momentum)
- GMI rejection rate (thermodynamic validity)
- NPE novelty generation
- End-to-end evolution quality
"""

import numpy as np
import sys
import time
sys.path.insert(0, '/home/user/gmi')

from core.state import State, Instruction, Proposal
from core.gr_solver import GRSolver
from ledger.oplax_verifier import OplaxVerifier
from adapters.stochastic_synthesizer import StochasticSynthesizer
from adapters.npe_integration import create_npe_gmi_runtime
from adapters.cbtsv1_adapter import create_cbtsv1_gmi_runtime


class BenchmarkResults:
    """Container for benchmark results."""
    def __init__(self):
        self.results = {}
        
    def add(self, name, value, unit=""):
        self.results[name] = {"value": value, "unit": unit}
        
    def print_summary(self):
        print("\n" + "="*70)
        print("BENCHMARK RESULTS")
        print("="*70)
        for name, data in self.results.items():
            print(f"  {name}: {data['value']:.4f} {data['unit']}")


def benchmark_gr_solver_capability():
    """
    Benchmark 1: GR Solver Capability
    Tests: Constraint preservation, convergence
    """
    print("\n" + "="*70)
    print("BENCHMARK 1: GR Solver Capability")
    print("="*70)
    
    results = BenchmarkResults()
    
    # Test different grid resolutions
    for N in [8, 16, 32]:
        solver = GRSolver(Nx=N, Ny=N, Nz=N, dx=0.1)
        solver.init_minkowski()
        
        # Run evolution
        stats = solver.run(T_max=0.1, dt_max=0.01)
        
        # Measure constraint preservation
        final_H = stats['H_history'][-1] if stats['H_history'] else 0
        final_M = stats['M_history'][-1] if stats['M_history'] else 0
        
        print(f"  Grid {N}x{N}x{N}: H={final_H:.2e}, M={final_M:.2e}, steps={stats['steps']}")
        
        if N == 16:
            results.add("constraint_preservation_H", final_H, "units")
            results.add("constraint_preservation_M", final_M, "units")
            results.add("steps_completed", stats['steps'], "count")
    
    return results


def benchmark_gr_solver_performance():
    """
    Benchmark 2: GR Solver Performance
    Tests: Steps per second, time to solution
    """
    print("\n" + "="*70)
    print("BENCHMARK 2: GR Solver Performance")
    print("="*70)
    
    results = BenchmarkResults()
    
    N = 16
    n_runs = 5
    
    times = []
    for _ in range(n_runs):
        solver = GRSolver(Nx=N, Ny=N, Nz=N, dx=0.1)
        solver.init_minkowski()
        
        start = time.perf_counter()
        stats = solver.run(T_max=0.2, dt_max=0.01)
        elapsed = time.perf_counter() - start
        
        times.append(elapsed)
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    steps_per_sec = stats['steps'] / avg_time
    
    print(f"  Grid {N}x{N}x{N}: {avg_time:.3f}s ± {std_time:.3f}s")
    print(f"  Steps/second: {steps_per_sec:.1f}")
    
    results.add("solve_time", avg_time, "seconds")
    results.add("steps_per_second", steps_per_sec, "steps/s")
    results.add("time_std", std_time, "seconds")
    
    return results


def benchmark_gmi_verifier():
    """
    Benchmark 3: GMI Verifier
    Tests: Acceptance rate, throughput
    """
    print("\n" + "="*70)
    print("BENCHMARK 3: GMI Verifier")
    print("="*70)
    
    results = BenchmarkResults()
    
    def V(x):
        return float(np.sum(x**2))
    
    verifier = OplaxVerifier(potential_fn=V)
    state = State([1.0, 1.0], budget=100.0)
    
    n_proposals = 100
    accepted = 0
    rejected = 0
    
    # Test various proposal types
    for i in range(n_proposals):
        # Generate test proposals
        scale = np.random.uniform(0.1, 2.0)
        
        if scale < 1.0:
            # Valid descent
            instr = Instruction("DESCENT", lambda x: x * scale, sigma=scale, kappa=scale)
        else:
            # Invalid (potentially)
            instr = Instruction("STEP", lambda x: x + scale, sigma=scale, kappa=scale)
        
        result, _, receipt = verifier.check(i, state, instr)
        
        if result:
            accepted += 1
        else:
            rejected += 1
    
    acceptance_rate = accepted / n_proposals
    
    print(f"  Proposals tested: {n_proposals}")
    print(f"  Accepted: {accepted}, Rejected: {rejected}")
    print(f"  Acceptance rate: {acceptance_rate:.1%}")
    
    results.add("acceptance_rate", acceptance_rate, "ratio")
    results.add("proposals_tested", n_proposals, "count")
    
    return results


def benchmark_npe_synthesizer():
    """
    Benchmark 4: NPE Synthesizer
    Tests: Novelty generation, uniqueness
    """
    print("\n" + "="*70)
    print("BENCHMARK 4: NPE Synthesizer")
    print("="*70)
    
    results = BenchmarkResults()
    
    synth = StochasticSynthesizer(temperature=1.0, hallucination_rate=0.7)
    
    n_runs = 10
    n_proposals_per_run = 20
    
    all_proposals = []
    novelty_scores = []
    
    for _ in range(n_runs):
        context = {"task": "benchmark", "step": _}
        proposals = synth.generate_wild_proposals(context, n_proposals=n_proposals_per_run)
        
        for p in proposals:
            all_proposals.append(str(p))
            novelty_scores.append(p.novelty_score)
    
    # Calculate uniqueness
    unique = len(set(all_proposals))
    uniqueness = unique / len(all_proposals)
    
    avg_novelty = np.mean(novelty_scores)
    std_novelty = np.std(novelty_scores)
    
    print(f"  Total proposals: {len(all_proposals)}")
    print(f"  Unique: {unique} ({uniqueness:.1%})")
    print(f"  Novelty: {avg_novelty:.2f} ± {std_novelty:.2f}")
    
    results.add("uniqueness", uniqueness, "ratio")
    results.add("avg_novelty", avg_novelty, "score")
    results.add("novelty_std", std_novelty, "score")
    results.add("total_generated", len(all_proposals), "count")
    
    return results


def benchmark_npe_gmi_integration():
    """
    Benchmark 5: NPE + GMI Integration
    Tests: End-to-end proposal verification
    """
    print("\n" + "="*70)
    print("BENCHMARK 5: NPE + GMI Integration")
    print("="*70)
    
    results = BenchmarkResults()
    
    def V(x):
        return float(np.sum(x**2))
    
    n_runs = 3
    total_steps = 0
    total_accepted = 0
    total_rejected = 0
    
    times = []
    
    for run in range(n_runs):
        adapter = create_npe_gmi_runtime(V, budget=50.0)
        
        start = time.perf_counter()
        state = adapter.run(initial_x=np.array([1.0, 1.0]), budget=50.0, n_steps=10)
        elapsed = time.perf_counter() - start
        
        times.append(elapsed)
        total_steps += adapter.stats['proposals_generated']
        total_accepted += adapter.stats['proposals_accepted']
        total_rejected += adapter.stats['proposals_rejected']
    
    avg_time = np.mean(times)
    acceptance_rate = total_accepted / total_steps if total_steps > 0 else 0
    
    print(f"  Runs: {n_runs}")
    print(f"  Total proposals: {total_steps}")
    print(f"  Accepted: {total_accepted}, Rejected: {total_rejected}")
    print(f"  Acceptance rate: {acceptance_rate:.1%}")
    print(f"  Time per run: {avg_time:.3f}s")
    
    results.add("integration_time", avg_time, "seconds")
    results.add("acceptance_rate", acceptance_rate, "ratio")
    results.add("total_accepted", total_accepted, "count")
    results.add("steps_per_second", total_steps / avg_time, "steps/s")
    
    return results


def benchmark_cbtsv1_gmi():
    """
    Benchmark 6: CBTSv1 + GMI Integration
    Tests: GR solver with thermodynamic governance
    """
    print("\n" + "="*70)
    print("BENCHMARK 6: CBTSv1 + GMI")
    print("="*70)
    
    results = BenchmarkResults()
    
    def V_from_solver(solver):
        return float(np.mean(np.abs(solver.fields.hamiltonian)))
    
    n_runs = 3
    steps_completed = 0
    steps_rejected = 0
    final_constraints = []
    
    times = []
    
    for run in range(n_runs):
        runtime = create_cbtsv1_gmi_runtime(
            solver_type="gr",
            potential_fn=V_from_solver,
            budget=100.0,
            Nx=16, Ny=16, Nz=16
        )
        
        start = time.perf_counter()
        
        for _ in range(10):
            result = runtime.execute_governed_step(dt_candidate=0.01)
            if result.accepted:
                steps_completed += 1
            else:
                steps_rejected += 1
        
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        
        # Final constraint
        H = np.mean(np.abs(runtime.solver.fields.hamiltonian))
        final_constraints.append(H)
    
    avg_time = np.mean(times)
    acceptance_rate = steps_completed / (steps_completed + steps_rejected)
    avg_constraint = np.mean(final_constraints)
    
    print(f"  Runs: {n_runs}")
    print(f"  Steps completed: {steps_completed}, Rejected: {steps_rejected}")
    print(f"  Acceptance rate: {acceptance_rate:.1%}")
    print(f"  Final H constraint: {avg_constraint:.2e}")
    print(f"  Time: {avg_time:.3f}s")
    
    results.add("gr_governance_time", avg_time, "seconds")
    results.add("acceptance_rate", acceptance_rate, "ratio")
    results.add("final_constraint_H", avg_constraint, "units")
    results.add("steps_completed", steps_completed, "count")
    
    return results


def benchmark_full_three_layer():
    """
    Benchmark 7: Full Three-Layer Evolution
    Tests: Complete NPE → GMI → GR pipeline
    """
    print("\n" + "="*70)
    print("BENCHMARK 7: Full Three-Layer Evolution")
    print("="*70)
    
    results = BenchmarkResults()
    
    # Initialize
    gr_solver = GRSolver(Nx=8, Ny=8, Nz=8, dx=0.1)
    gr_solver.init_minkowski()
    
    def V_gr(x):
        return float(np.mean(np.abs(gr_solver.fields.hamiltonian)))
    
    verifier = OplaxVerifier(potential_fn=V_gr)
    state = State(np.array([0.0]), budget=100.0)
    synth = StochasticSynthesizer(temperature=1.2, hallucination_rate=0.5)
    
    n_steps = 20
    accepted_steps = 0
    rejected_steps = 0
    
    # Evolution
    start = time.perf_counter()
    
    for step in range(n_steps):
        # Layer 1: NPE proposes
        context = {"step": step}
        proposals = synth.generate_wild_proposals(context, n_proposals=3)
        
        # Use first proposal
        proposal = proposals[0] if proposals else None
        
        # Estimate costs
        H = np.mean(np.abs(gr_solver.fields.hamiltonian))
        M = np.mean(np.abs(gr_solver.fields.momentum))
        sigma = 0.01
        kappa = 0.01 + H + M
        
        # Layer 2: GMI verifies
        if proposal:
            instr = Instruction(
                proposal.module.name if hasattr(proposal.module, 'name') else "NPE",
                lambda x: x,
                sigma=sigma,
                kappa=kappa
            )
        else:
            instr = Instruction("BASELINE", lambda x: x, sigma=sigma, kappa=kappa)
        
        accepted, next_state, receipt = verifier.check(step, state, instr)
        
        if accepted:
            # Layer 3: GR executes
            gr_solver.step_forward_euler(0.01)
            accepted_steps += 1
        else:
            rejected_steps += 1
    
    elapsed = time.perf_counter() - start
    
    acceptance_rate = accepted_steps / n_steps
    
    # Final metrics
    final_H = np.mean(np.abs(gr_solver.fields.hamiltonian))
    final_M = np.mean(np.abs(gr_solver.fields.momentum))
    
    print(f"  Steps: {n_steps}")
    print(f"  Accepted: {accepted_steps}, Rejected: {rejected_steps}")
    print(f"  Acceptance rate: {acceptance_rate:.1%}")
    print(f"  Final H: {final_H:.2e}, M: {final_M:.2e}")
    print(f"  Time: {elapsed:.3f}s ({n_steps/elapsed:.1f} steps/s)")
    
    results.add("total_time", elapsed, "seconds")
    results.add("acceptance_rate", acceptance_rate, "ratio")
    results.add("final_H", final_H, "units")
    results.add("final_M", final_M, "units")
    results.add("throughput", n_steps/elapsed, "steps/s")
    
    return results


def run_all_benchmarks():
    """Run complete benchmark suite."""
    print("="*70)
    print("PROOF-CARRYING RESEARCH ENGINE - BENCHMARK SUITE")
    print("="*70)
    
    benchmarks = [
        ("GR Solver Capability", benchmark_gr_solver_capability),
        ("GR Solver Performance", benchmark_gr_solver_performance),
        ("GMI Verifier", benchmark_gmi_verifier),
        ("NPE Synthesizer", benchmark_npe_synthesizer),
        ("NPE + GMI", benchmark_npe_gmi_integration),
        ("CBTSv1 + GMI", benchmark_cbtsv1_gmi),
        ("Full Three-Layer", benchmark_full_three_layer),
    ]
    
    all_results = {}
    
    for name, benchmark_fn in benchmarks:
        try:
            results = benchmark_fn()
            all_results[name] = results
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[name] = None
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    summary_data = []
    
    for name, results in all_results.items():
        if results:
            print(f"\n{name}:")
            for key, data in results.results.items():
                print(f"  {key}: {data['value']:.4f} {data['unit']}")
                summary_data.append((name, key, data['value'], data['unit']))
    
    return all_results


if __name__ == "__main__":
    run_all_benchmarks()
