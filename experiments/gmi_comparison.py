"""
GMI Experiment Suite: Thermodynamic Governance vs Gradient Descent

This experiment compares:
1. Baseline: Standard gradient descent (no thermodynamic constraints)
2. GMI Governance: With thermodynamic inequality constraints
3. GMI + Memory: With memory scarring
4. GMI No-Scar: Without memory scarring

Metrics:
- Convergence speed (steps to reach V < threshold)
- Budget efficiency (total sigma spent)
- Scar avoidance ratio (how often rejected paths are avoided)
- Final tension achieved

The experiment uses a multi-modal potential landscape to demonstrate
the difference between greedy descent and thermodynamic exploration.
"""

import numpy as np
import json
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

# GMI imports
from core.state import State, Instruction, Proposal
from core.memory import MemoryManifold
from core.embedder import GMI_Embedder
from ledger.oplax_verifier import OplaxVerifier
from ledger.receipt import Receipt


# =============================================================================
# MULTI-MODAL POTENTIAL LANDSCAPE
# =============================================================================

class MultiModalPotential:
    """
    A multi-modal potential landscape with:
    - Global minimum at origin (0, 0)
    - Local minima traps
    - A "danger zone" that represents high-cost states
    
    This forces the system to make choices - gradient descent gets trapped,
    while GMI's thermodynamic constraints can prevent bad paths.
    """
    
    def __init__(self, trap_location: np.ndarray = None, trap_strength: float = 2.0):
        if trap_location is None:
            self.trap_location = np.array([3.0, 3.0])
        else:
            self.trap_location = trap_location
        self.trap_strength = trap_strength
    
    def __call__(self, x: np.ndarray) -> float:
        """Compute multi-modal potential V(x)"""
        # Global quadratic bowl (main attractor)
        v_main = np.sum(x**2)
        
        # Local trap (creates a secondary minimum)
        dist_to_trap = np.linalg.norm(x - self.trap_location)
        v_trap = self.trap_strength * np.exp(-dist_to_trap**2 / 2.0)
        
        return float(v_main + v_trap)
    
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """Analytical gradient for baseline comparison"""
        # Gradient of main bowl: 2x
        grad_main = 2.0 * x
        
        # Gradient of trap: -trap_strength * exp(...) * (x - trap_location)
        dist_sq = np.sum((x - self.trap_location)**2)
        trap_term = self.trap_strength * np.exp(-dist_sq / 2.0)
        grad_trap = -trap_term * (x - self.trap_location)
        
        return grad_main + grad_trap


# =============================================================================
# BASELINE: STANDARD GRADIENT DESCENT
# =============================================================================

@dataclass
class GradientDescentResult:
    """Results from gradient descent run"""
    final_x: np.ndarray
    final_v: float
    steps: int
    total_gradient_magnitude: float
    path: List[np.ndarray]
    v_history: List[float]


def run_gradient_descent(
    initial_x: np.ndarray,
    learning_rate: float = 0.1,
    max_steps: int = 100,
    threshold: float = 0.05,
    potential: MultiModalPotential = None
) -> GradientDescentResult:
    """
    Standard gradient descent (no GMI constraints).
    
    This is the baseline for comparison - pure greedy optimization.
    """
    potential = potential or MultiModalPotential()
    x = initial_x.copy()
    
    path = [x.copy()]
    v_history = []
    total_grad_mag = 0.0
    
    for step in range(max_steps):
        v_current = potential(x)
        v_history.append(v_current)
        
        if v_current < threshold:
            return GradientDescentResult(
                final_x=x.copy(),
                final_v=v_current,
                steps=step + 1,
                total_gradient_magnitude=total_grad_mag,
                path=path.copy(),
                v_history=v_history
            )
        
        # Pure gradient descent step
        grad = potential.gradient(x)
        total_grad_mag += np.linalg.norm(grad)
        x = x - learning_rate * grad
        path.append(x.copy())
    
    return GradientDescentResult(
        final_x=x.copy(),
        final_v=potential(x),
        steps=max_steps,
        total_gradient_magnitude=total_grad_mag,
        path=path.copy(),
        v_history=v_history
    )


# =============================================================================
# GMI GOVERNANCE VARIANT
# =============================================================================

@dataclass
class GMIGovernedResult:
    """Results from GMI-governed run"""
    final_x: np.ndarray
    final_v: float
    steps: int
    total_budget_spent: float
    initial_budget: float
    decisions: List[str]  # "EXPLORE_ACCEPTED", "EXPLORE_REJECTED", "INFER_ACCEPTED"
    path: List[np.ndarray]
    v_history: List[float]
    receipts: List[Receipt]


def run_gmi_governed(
    initial_x: np.ndarray,
    initial_budget: float,
    max_steps: int = 100,
    threshold: float = 0.05,
    potential_fn=None,
    use_memory: bool = False,
    memory: MemoryManifold = None,
    seed: int = None,
    scar_penalty: float = 5.0  # How much to penalize rejected paths
) -> GMIGovernedResult:
    """
    GMI-governed execution with thermodynamic constraints.
    
    Key differences from gradient descent:
    1. Proposals must satisfy: V(x') + sigma <= V(x) + kappa + b
    2. Budget is finite and must be managed
    3. Memory scarring can penalize rejected paths
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Setup potential (with or without memory)
    if potential_fn is None:
        base_potential = MultiModalPotential()
        if use_memory and memory is None:
            memory = MemoryManifold(lambda_c=10.0)
        
        if use_memory:
            def total_potential(x):
                return base_potential(x) + memory.read_curvature(x)
            potential_fn = total_potential
        else:
            potential_fn = base_potential
    
    verifier = OplaxVerifier(potential_fn=potential_fn)
    state = State(initial_x, initial_budget)
    
    decisions = []
    path = [state.x.copy()]
    v_history = [potential_fn(state.x)]
    receipts = []
    
    for step in range(max_steps):
        v_current = potential_fn(state.x)
        
        if v_current < threshold:
            break
        
        # Generate EXPLORE and INFER proposals
        explore, infer = generate_proposals(state.x, step)
        
        # Try EXPLORE first (imagination)
        accepted, next_state, receipt = verifier.check(step, state, explore)
        
        if accepted:
            decisions.append("EXPLORE_ACCEPTED")
            state = next_state
        else:
            decisions.append("EXPLORE_REJECTED")
            
            # If memory is enabled, scar the rejected path
            if use_memory:
                rejected_x = explore.pi(state.x)
                memory.write_scar(rejected_x, penalty=scar_penalty)
            
            # Fallback to INFER
            accepted, next_state, receipt = verifier.check(step, state, infer)
            
            if accepted:
                decisions.append("INFER_ACCEPTED")
                state = next_state
            else:
                decisions.append("INFER_REJECTED")
                # If both fail, we're stuck
                break
        
        receipts.append(receipt)
        path.append(state.x.copy())
        v_history.append(potential_fn(state.x))
    
    return GMIGovernedResult(
        final_x=state.x.copy(),
        final_v=potential_fn(state.x),
        steps=len(path) - 1,
        total_budget_spent=initial_budget - state.b,
        initial_budget=initial_budget,
        decisions=decisions,
        path=path,
        v_history=v_history,
        receipts=receipts
    )


def generate_proposals(x: np.ndarray, step: int) -> Tuple[Instruction, Instruction]:
    """Generate EXPLORE and INFER instructions"""
    
    # EXPLORE: Random perturbation (attempts to escape local minima)
    # High sigma (cost), high kappa (allowed defect)
    noise = np.random.uniform(-1.5, 1.5, size=len(x))
    explore = Instruction(
        "EXPLORE",
        lambda x, n=noise: x + n,
        sigma=3.0,
        kappa=8.0
    )
    
    # INFER: Gradient-like descent (safe but slow)
    # Low sigma, zero kappa - must actually descend
    grad = 2.0 * x  # Simple gradient of x^2
    infer = Instruction(
        "INFER",
        lambda x, g=grad: x - 0.15 * g,
        sigma=0.5,
        kappa=0.0
    )
    
    return explore, infer


# =============================================================================
# MAIN EXPERIMENT RUNNER
# =============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for the comparison experiment"""
    # Problem setup
    initial_x: np.ndarray = None
    trap_location: np.ndarray = field(default_factory=lambda: np.array([3.0, 3.0]))
    trap_strength: float = 2.0
    
    # GMI parameters
    initial_budget: float = 50.0
    threshold: float = 0.05
    max_steps: int = 100
    
    # Baseline parameters
    learning_rate: float = 0.1
    
    # Experiment parameters
    n_runs: int = 10
    seeds: List[int] = None


@dataclass
class ExperimentResult:
    """Aggregated results from multiple experiment runs"""
    # Baseline stats
    baseline_steps_mean: float
    baseline_steps_std: float
    baseline_final_v_mean: float
    baseline_final_v_std: float
    
    # GMI stats (no memory)
    gmi_steps_mean: float
    gmi_steps_std: float
    gmi_final_v_mean: float
    gmi_final_v_std: float
    gmi_budget_spent_mean: float
    
    # GMI + Memory stats
    gmi_memory_steps_mean: float
    gmi_memory_steps_std: float
    gmi_memory_final_v_mean: float
    gmi_memory_final_v_std: float
    gmi_memory_budget_spent_mean: float
    gmi_memory_scar_count_mean: float
    
    # Per-run data
    baseline_runs: List[GradientDescentResult]
    gmi_runs: List[GMIGovernedResult]
    gmi_memory_runs: List[GMIGovernedResult]


def run_comparison_experiment(config: ExperimentConfig = None) -> ExperimentResult:
    """
    Run the full comparison experiment.
    
    Returns statistics comparing:
    - Baseline (gradient descent)
    - GMI (no memory)
    - GMI + Memory
    """
    config = config or ExperimentConfig()
    
    if config.initial_x is None:
        # Start near the trap to see if we can avoid it
        config.initial_x = np.array([2.5, 2.5])
    
    if config.seeds is None:
        config.seeds = list(range(config.n_runs))
    
    # Storage for results
    baseline_runs = []
    gmi_runs = []
    gmi_memory_runs = []
    
    potential = MultiModalPotential(
        trap_location=config.trap_location,
        trap_strength=config.trap_strength
    )
    
    print("=" * 60)
    print("GMI COMPARISON EXPERIMENT")
    print("=" * 60)
    print(f"Initial position: {config.initial_x}")
    print(f"Trap location: {config.trap_location}")
    print(f"Initial budget: {config.initial_budget}")
    print(f"Threshold: {config.threshold}")
    print(f"Number of runs: {config.n_runs}")
    print("=" * 60)
    
    for i, seed in enumerate(config.seeds):
        print(f"\n--- Run {i+1}/{config.n_runs} (seed={seed}) ---")
        
        np.random.seed(seed)
        
        # 1. Baseline: Gradient Descent
        baseline_result = run_gradient_descent(
            initial_x=config.initial_x,
            learning_rate=config.learning_rate,
            max_steps=config.max_steps,
            threshold=config.threshold,
            potential=potential
        )
        baseline_runs.append(baseline_result)
        print(f"  Baseline: steps={baseline_result.steps}, V_final={baseline_result.final_v:.4f}")
        
        # 2. GMI (no memory)
        gmi_result = run_gmi_governed(
            initial_x=config.initial_x,
            initial_budget=config.initial_budget,
            max_steps=config.max_steps,
            threshold=config.threshold,
            potential_fn=potential,
            use_memory=False,
            seed=seed
        )
        gmi_runs.append(gmi_result)
        print(f"  GMI: steps={gmi_result.steps}, V_final={gmi_result.final_v:.4f}, budget_spent={gmi_result.total_budget_spent:.2f}")
        
        # 3. GMI + Memory
        memory = MemoryManifold(lambda_c=10.0)
        gmi_memory_result = run_gmi_governed(
            initial_x=config.initial_x,
            initial_budget=config.initial_budget,
            max_steps=config.max_steps,
            threshold=config.threshold,
            potential_fn=potential,
            use_memory=True,
            memory=memory,
            seed=seed
        )
        gmi_memory_runs.append(gmi_memory_result)
        print(f"  GMI+Memory: steps={gmi_memory_result.steps}, V_final={gmi_memory_result.final_v:.4f}, scars={len(memory.scars)}")
    
    # Compute statistics
    def stats(runs, key):
        values = [getattr(r, key) for r in runs]
        return np.mean(values), np.std(values)
    
    baseline_steps_mean, baseline_steps_std = stats(baseline_runs, 'steps')
    baseline_v_mean, baseline_v_std = stats(baseline_runs, 'final_v')
    
    gmi_steps_mean, gmi_steps_std = stats(gmi_runs, 'steps')
    gmi_v_mean, gmi_v_std = stats(gmi_runs, 'final_v')
    gmi_budget_mean, _ = stats(gmi_runs, 'total_budget_spent')
    
    gmi_mem_steps_mean, gmi_mem_steps_std = stats(gmi_memory_runs, 'steps')
    gmi_mem_v_mean, gmi_mem_v_std = stats(gmi_memory_runs, 'final_v')
    gmi_mem_budget_mean, _ = stats(gmi_memory_runs, 'total_budget_spent')
    
    # Count scars per run
    scar_counts = [len(r.receipts) for r in gmi_memory_runs]
    scar_count_mean = np.mean(scar_counts)
    
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"\nBaseline (Gradient Descent):")
    print(f"  Steps: {baseline_steps_mean:.1f} ± {baseline_steps_std:.1f}")
    print(f"  Final V: {baseline_v_mean:.4f} ± {baseline_v_std:.4f}")
    
    print(f"\nGMI (No Memory):")
    print(f"  Steps: {gmi_steps_mean:.1f} ± {gmi_steps_std:.1f}")
    print(f"  Final V: {gmi_v_mean:.4f} ± {gmi_v_std:.4f}")
    print(f"  Budget Spent: {gmi_budget_mean:.2f}")
    
    print(f"\nGMI + Memory Scarring:")
    print(f"  Steps: {gmi_mem_steps_mean:.1f} ± {gmi_mem_steps_std:.1f}")
    print(f"  Final V: {gmi_mem_v_mean:.4f} ± {gmi_mem_v_std:.4f}")
    print(f"  Budget Spent: {gmi_mem_budget_mean:.2f}")
    print(f"  Avg Scar Count: {scar_count_mean:.1f}")
    
    return ExperimentResult(
        baseline_steps_mean=baseline_steps_mean,
        baseline_steps_std=baseline_steps_std,
        baseline_final_v_mean=baseline_v_mean,
        baseline_final_v_std=baseline_v_std,
        gmi_steps_mean=gmi_steps_mean,
        gmi_steps_std=gmi_steps_std,
        gmi_final_v_mean=gmi_v_mean,
        gmi_final_v_std=gmi_v_std,
        gmi_budget_spent_mean=gmi_budget_mean,
        gmi_memory_steps_mean=gmi_mem_steps_mean,
        gmi_memory_steps_std=gmi_mem_steps_std,
        gmi_memory_final_v_mean=gmi_mem_v_mean,
        gmi_memory_final_v_std=gmi_mem_v_std,
        gmi_memory_budget_spent_mean=gmi_mem_budget_mean,
        gmi_memory_scar_count_mean=scar_count_mean,
        baseline_runs=baseline_runs,
        gmi_runs=gmi_runs,
        gmi_memory_runs=gmi_memory_runs
    )


def save_results(result: ExperimentResult, filename: str = "outputs/receipts/experiment_results.json"):
    """Save experiment results to JSON"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Convert to serializable format
    data = {
        "baseline": {
            "steps_mean": result.baseline_steps_mean,
            "steps_std": result.baseline_steps_std,
            "final_v_mean": result.baseline_final_v_mean,
            "final_v_std": result.baseline_final_v_std,
        },
        "gmi": {
            "steps_mean": result.gmi_steps_mean,
            "steps_std": result.gmi_steps_std,
            "final_v_mean": result.gmi_final_v_mean,
            "final_v_std": result.gmi_final_v_std,
            "budget_spent_mean": result.gmi_budget_spent_mean,
        },
        "gmi_memory": {
            "steps_mean": result.gmi_memory_steps_mean,
            "steps_std": result.gmi_memory_steps_std,
            "final_v_mean": result.gmi_memory_final_v_mean,
            "final_v_std": result.gmi_memory_final_v_std,
            "budget_spent_mean": result.gmi_memory_budget_spent_mean,
            "scar_count_mean": result.gmi_memory_scar_count_mean,
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nResults saved to: {filename}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Default configuration
    # Start BEHIND the trap (at 3.5, 3.5) - gradient descent will get stuck in local minimum
    config = ExperimentConfig(
        initial_x=np.array([3.5, 3.5]),  # Start behind the trap
        trap_location=np.array([3.0, 3.0]),
        trap_strength=2.0,
        initial_budget=50.0,
        threshold=0.05,
        max_steps=100,
        learning_rate=0.1,
        n_runs=10,
        seeds=list(range(10))
    )
    
    # Run experiment
    results = run_comparison_experiment(config)
    
    # Save results
    save_results(results)
    
    # ============================================================================
    # MEMORY LEARNING EFFECT TEST
    # Compare: persistent memory (accumulates scars) vs fresh memory (control)
    # ============================================================================
    print("\n" + "=" * 60)
    print("MEMORY LEARNING EFFECT TEST")
    print("=" * 60)
    print("Comparing: Persistent memory (accumulates) vs Fresh memory (control)\n")
    
    n_episodes = 3
    
    # Test A: Persistent memory - same memory object across episodes
    print("--- Persistent Memory (Scars Accumulate) ---")
    persistent_memory = MemoryManifold(lambda_c=10.0)
    persistent_potential = MultiModalPotential(
        trap_location=config.trap_location,
        trap_strength=config.trap_strength
    )
    
    def persistent_V(x):
        return persistent_potential(x) + persistent_memory.read_curvature(x)
    
    persistent_results = []
    for episode in range(n_episodes):
        np.random.seed(episode)
        r = run_gmi_governed(
            initial_x=config.initial_x,
            initial_budget=config.initial_budget,
            max_steps=config.max_steps,
            threshold=config.threshold,
            potential_fn=persistent_V,
            use_memory=True,
            memory=persistent_memory,
            seed=episode
        )
        persistent_results.append(r)
        print(f"  Episode {episode+1}: V_final={r.final_v:.4f}, scars={len(persistent_memory.scars)}")
    
    # Test B: Fresh memory - new memory object each episode (control)
    print("\n--- Fresh Memory (Control - No Accumulation) ---")
    fresh_results = []
    for episode in range(n_episodes):
        np.random.seed(episode)
        fresh_memory = MemoryManifold(lambda_c=10.0)  # NEW memory each time
        
        def fresh_V(x):
            return persistent_potential(x) + fresh_memory.read_curvature(x)
        
        r = run_gmi_governed(
            initial_x=config.initial_x,
            initial_budget=config.initial_budget,
            max_steps=config.max_steps,
            threshold=config.threshold,
            potential_fn=fresh_V,
            use_memory=True,
            memory=fresh_memory,
            seed=episode
        )
        fresh_results.append(r)
        print(f"  Episode {episode+1}: V_final={r.final_v:.4f}, scars={len(fresh_memory.scars)}")
    
    # Summary
    print("\n" + "-" * 40)
    print("MEMORY COMPARISON SUMMARY:")
    print("-" * 40)
    
    persistent_mean = np.mean([r.final_v for r in persistent_results])
    fresh_mean = np.mean([r.final_v for r in fresh_results])
    
    print(f"Persistent Memory avg V: {persistent_mean:.4f}")
    print(f"Fresh Memory avg V:      {fresh_mean:.4f}")
    
    if persistent_mean < fresh_mean:
        improvement = (fresh_mean - persistent_mean) / fresh_mean * 100
        print(f"Memory persistence IMPROVED performance by {improvement:.1f}%")
    else:
        degradation = (persistent_mean - fresh_mean) / fresh_mean * 100
        print(f"Memory persistence DEGRADED performance by {degradation:.1f}%")
    
    print("\n" + "=" * 60)
    print("EXTENSIVE MEMORY PARAMETER SWEEP")
    print("=" * 60)
    print("Testing: lambda_c values [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]")
    print("         scar penalties [1.0, 2.0, 5.0, 10.0]")
    print("Running 3 episodes per configuration...\n")
    
    # Test different lambda_c values (curvature strength)
    lambda_c_values = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    penalty_values = [1.0, 2.0, 5.0, 10.0]
    
    best_lambda_c = None
    best_lambda_c_score = float('inf')
    lambda_results = []
    
    print("--- Testing lambda_c (curvature strength) ---")
    for lambda_c in lambda_c_values:
        # Test with persistent memory
        test_memory = MemoryManifold(lambda_c=lambda_c)
        test_potential = MultiModalPotential(
            trap_location=config.trap_location,
            trap_strength=config.trap_strength
        )
        
        def test_V(x):
            return test_potential(x) + test_memory.read_curvature(x)
        
        # Run 3 episodes with SAME memory
        episode_vs = []
        for ep in range(3):
            np.random.seed(ep)
            r = run_gmi_governed(
                initial_x=config.initial_x,
                initial_budget=config.initial_budget,
                max_steps=config.max_steps,
                threshold=config.threshold,
                potential_fn=test_V,
                use_memory=True,
                memory=test_memory,
                seed=ep
            )
            episode_vs.append(r.final_v)
        
        avg_v = np.mean(episode_vs)
        lambda_results.append((lambda_c, avg_v))
        
        if avg_v < best_lambda_c_score:
            best_lambda_c_score = avg_v
            best_lambda_c = lambda_c
        
        print(f"  lambda_c={lambda_c:5.1f}: avg V={avg_v:.4f}, scars={len(test_memory.scars)}")
    
    print(f"\n  BEST lambda_c: {best_lambda_c} with avg V={best_lambda_c_score:.4f}")
    
    # Test different penalty heights (with best lambda_c)
    print("\n--- Testing scar penalty heights ---")
    best_penalty = None
    best_penalty_score = float('inf')
    penalty_results = []
    best_lc = best_lambda_c if best_lambda_c else 0.5
    
    for penalty in penalty_values:
        test_memory = MemoryManifold(lambda_c=best_lc)
        test_potential = MultiModalPotential(
            trap_location=config.trap_location,
            trap_strength=config.trap_strength
        )
        
        def test_V_penalty(x):
            return test_potential(x) + test_memory.read_curvature(x)
        
        episode_vs = []
        for ep in range(3):
            np.random.seed(ep)
            r = run_gmi_governed(
                initial_x=config.initial_x,
                initial_budget=config.initial_budget,
                max_steps=config.max_steps,
                threshold=config.threshold,
                potential_fn=test_V_penalty,
                use_memory=True,
                memory=test_memory,
                seed=ep,
                scar_penalty=penalty  # Now using the parameter!
            )
            episode_vs.append(r.final_v)
        
        avg_v = np.mean(episode_vs)
        penalty_results.append((penalty, avg_v))
        
        if avg_v < best_penalty_score:
            best_penalty_score = avg_v
            best_penalty = penalty
        
        print(f"  penalty={penalty:5.1f}: avg V={avg_v:.4f}, scars={len(test_memory.scars)}")
    
    print(f"\n  BEST penalty: {best_penalty} with avg V={best_penalty_score:.4f}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("PARAMETER SWEEP SUMMARY")
    print("=" * 60)
    print(f"Optimal lambda_c: {best_lambda_c}")
    print(f"Optimal penalty: {best_penalty}")
    print("\nFull results:")
    print("lambda_c sweep:", [(l, f"{v:.4f}") for l, v in lambda_results])
    print("penalty sweep:", [(p, f"{v:.4f}") for p, v in penalty_results])
    
    # ============================================================================
    # EMBEDDER VOCABULARY TEST
    # ============================================================================
    print("\n" + "=" * 60)
    print("EXTENDED EMBEDDER VOCABULARY TEST")
    print("=" * 60)
    
    from core.embedder import GMI_Embedder
    
    embedder = GMI_Embedder()
    
    print(f"Vocabulary size: {len(embedder.vocab)} words")
    print("\nTension zones:")
    for zone, (low, high) in embedder.tension_zones.items():
        print(f"  {zone}: {low} - {high}")
    
    # Test new words
    test_phrases = [
        "truth and proof",
        "logic and reason",
        "creative imagination",
        "speculation and guess",
        "paradox and contradiction",
        "chaos and nonsense",
        "new_word_xyz"  # Unknown word test
    ]
    
    print("\nEmbedding test:")
    for phrase in test_phrases:
        coords = embedder.embed(phrase)
        zone = embedder.get_tension_zone(coords)
        tension = np.sum(coords**2)
        print(f"  '{phrase}' -> V={tension:.2f} ({zone})")
    
    # Test dynamic word addition
    print("\nDynamic word addition:")
    embedder.add_word("test_concept", tension=2.0, quadrant="first")
    coords = embedder.add_word("quantum_state", tension=1.5, quadrant="both")
    coords = embedder.embed("test_concept")
    print(f"  Added 'test_concept' at V={np.sum(coords**2):.2f}")
    print(f"  Vocabulary size now: {len(embedder.vocab)}")
    
    # ============================================================================
    # BUDGET AND CONVERGENCE PARAMETER SWEEP
    # ============================================================================
    print("\n" + "=" * 60)
    print("BUDGET AND CONVERGENCE PARAMETER SWEEP")
    print("=" * 60)
    
    # Test different budget values
    budget_values = [10, 20, 30, 50, 100]
    threshold_values = [0.01, 0.05, 0.1, 0.5]
    
    print("\n--- Testing initial budget values ---")
    budget_results = []
    for budget in budget_values:
        r = run_gmi_governed(
            initial_x=np.array([3.5, 3.5]),
            initial_budget=budget,
            max_steps=50,
            threshold=0.05,
            use_memory=False,
            seed=42
        )
        budget_results.append((budget, r.final_v, r.steps))
        print(f"  budget={budget:3d}: V_final={r.final_v:.4f}, steps={r.steps}")
    
    print("\n--- Testing convergence thresholds ---")
    threshold_results = []
    for thresh in threshold_values:
        r = run_gmi_governed(
            initial_x=np.array([3.5, 3.5]),
            initial_budget=50,
            max_steps=50,
            threshold=thresh,
            use_memory=False,
            seed=42
        )
        threshold_results.append((thresh, r.final_v, r.steps))
        print(f"  threshold={thresh:.2f}: V_final={r.final_v:.4f}, steps={r.steps}")
    
    # Find optimal budget
    best_budget = min(budget_results, key=lambda x: x[1])
    print(f"\nBest budget: {best_budget[0]} (V={best_budget[1]:.4f})")
    
    # ============================================================================
    # SIGMA/KAPPA (EXPLORATION) PARAMETER SWEEP
    # ============================================================================
    print("\n" + "=" * 60)
    print("SIGMA/KAPPA EXPLORATION PARAMETER SWEEP")
    print("=" * 60)
    
    # Test different sigma/kappa combinations
    # Higher kappa = more exploration allowed (can go uphill more)
    # Higher sigma = more expensive exploration
    
    sigma_kappa_configs = [
        (3.0, 8.0),   # Conservative
        (5.0, 12.0),   # Default
        (5.0, 20.0),   # Very exploratory
        (8.0, 25.0),   # High exploration (INVENT level)
    ]
    
    print("\n--- Testing sigma/kappa for EXPLORE ---")
    sk_results = []
    for sigma, kappa in sigma_kappa_configs:
        # Create custom proposal generator with specific sigma/kappa
        np.random.seed(42)
        
        # Quick test with specific sigma/kappa
        test_potential = MultiModalPotential(
            trap_location=config.trap_location,
            trap_strength=config.trap_strength
        )
        
        # Run a few iterations with this sigma/kappa
        from core.state import State, Instruction
        
        vs = []
        for _ in range(3):
            state = State(config.initial_x.copy(), 50.0)
            for _ in range(10):
                if test_potential(state.x) < 0.1:
                    break
                # EXPLORE with specific sigma/kappa
                noise = np.random.uniform(-1.5, 1.5, size=len(state.x))
                instr = Instruction("EXPLORE", lambda x, n=noise: x + n, sigma=sigma, kappa=kappa)
                
                x_prime = instr.pi(state.x)
                v_current = test_potential(state.x)
                v_prime = test_potential(x_prime)
                
                if (v_prime + sigma) <= (v_current + kappa):
                    state = State(x_prime, state.b - sigma)
                else:
                    # Fallback to INFER
                    infer = Instruction("INFER", lambda x: x - 0.15 * x, sigma=0.5, kappa=0.0)
                    x_prime = infer.pi(state.x)
                    v_current = test_potential(state.x)
                    v_prime = test_potential(x_prime)
                    if (v_prime + 0.5) <= v_current:
                        state = State(x_prime, state.b - 0.5)
            
            vs.append(test_potential(state.x))
        
        avg_v = np.mean(vs)
        sk_results.append(((sigma, kappa), avg_v))
        print(f"  sigma={sigma}, kappa={kappa}: avg V={avg_v:.4f}")
    
    best_sk = min(sk_results, key=lambda x: x[1])
    print(f"\n  Best sigma/kappa: {best_sk[0]} (V={best_sk[1]:.4f})")
    
    # ============================================================================
    # NVE ALPHA/BETA (EFFICIENCY VS NOVELTY) SWEEP
    # ============================================================================
    print("\n" + "=" * 60)
    print("NVE ALPHA/BETA SELECTION WEIGHT SWEEP")
    print("=" * 60)
    
    alpha_beta_configs = [
        (0.9, 0.1),  # Heavily efficiency-focused
        (0.7, 0.3),  # Default
        (0.5, 0.5),  # Balanced
        (0.3, 0.7),  # Heavily novelty-focused
    ]
    
    print("\n--- Testing alpha (efficiency) / beta (novelty) weights ---")
    ab_results = []
    
    for alpha, beta in alpha_beta_configs:
        # Simulate NVE selection with different weights
        # Higher beta = more likely to pick novel but less efficient paths
        
        np.random.seed(42)
        
        # Simulate proposal pool: [efficient_low_novel, inefficient_high_novel]
        proposal_scores = [
            (0.8, 0.0),  # Efficient but no novelty
            (0.2, 0.5),  # Inefficient but novel
        ]
        
        # Selection score = alpha * efficiency + beta * novelty
        scores = [alpha * eff + beta * nov for eff, nov in proposal_scores]
        chosen = 0 if scores[0] > scores[1] else 1
        
        # Record what would be chosen
        ab_results.append(((alpha, beta), "efficient" if chosen == 0 else "novel"))
        print(f"  alpha={alpha}, beta={beta}: chooses {'efficient' if chosen == 0 else 'novel'} proposal")
    
    # Summary
    print("\n" + "=" * 60)
    print("EXPLORATION PARAMETER SUMMARY")
    print("=" * 60)
    print(f"\nSigma/Kappa recommendations:")
    print(f"  - Conservative (sigma=3, kappa=8): Low budget, safe exploration")
    print(f"  - Default (sigma=5, kappa=12): Balanced (current)")
    print(f"  - Exploratory (sigma=5, kappa=20): Bold exploration")
    print(f"\nAlpha/Beta recommendations:")
    print(f"  - alpha=0.9, beta=0.1: Pure exploitation (fast convergence)")
    print(f"  - alpha=0.7, beta=0.3: Balanced (current)")
    print(f"  - alpha=0.5, beta=0.5: Balanced exploration")
    print(f"  - alpha=0.3, beta=0.7: Pure exploration (slow but novel)")
    
    print("\n" + "=" * 60)
    print("EXPECTED BEHAVIOR")
    print("=" * 60)
    print("""
    The multi-modal potential has:
    - Global minimum at (0, 0) with V ≈ 0
    - Local minimum/trap at (3, 3) with V ≈ 2
    
    Starting at (2.5, 2.5):
    
    BASELINE (Gradient Descent):
    - Pure greedy descent - will head toward (3, 3) trap
    - May get stuck in local minimum
    - Fast but imprecise
    
    GMI (No Memory):
    - EXPLORE can jump randomly, may escape trap
    - Budget constraint limits exploration
    - Trade-off between exploration and exploitation
    
    GMI + Memory:
    - Rejected paths create scars
    - Scars increase local potential
    - System learns to avoid previously failed paths
    - Over multiple runs: should show learning effect
    """)
