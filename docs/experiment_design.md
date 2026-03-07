# GMI Experiment Design: Thermodynamic Governance vs Gradient Descent

## Objective

Design an experiment to compare:
1. **Baseline**: Standard gradient descent (no thermodynamic constraints)
2. **GMI Governance**: With thermodynamic inequality constraints
3. **GMI + Memory**: With memory scarring to measure learning effect

## Hypothesis

GMI's thermodynamic governance should:
- Prevent exploration of high-cost states (budget constraint)
- Enable escape from local minima via the κ (kappa) defect envelope
- Memory scarring should reduce repeated failures over multiple runs

## Experimental Setup

### Problem Landscape: Multi-Modal Potential

To demonstrate the difference between greedy descent and thermodynamic exploration, we use a multi-modal potential:

```
V(x) = Σ(x_i²) + trap_strength × exp(-||x - trap||² / 2)
```

| Feature | Value |
|---------|-------|
| Global minimum | (0, 0) with V ≈ 0 |
| Local trap | (3, 3) with V ≈ 2 |
| Starting position | (2.5, 2.5) |

This creates a scenario where:
- Gradient descent may get trapped in the local minimum
- GMI's EXPLORE can potentially jump out
- Memory scarring should penalize repeated failures

## Comparison Metrics

| Metric | Description | Measurement |
|--------|-------------|-------------|
| **Convergence Speed** | Steps to reach V < threshold | Count of iterations |
| **Budget Efficiency** | Total σ (sigma) spent | Sum of instruction costs |
| **Final Tension** | V(x) at termination | Potential function value |
| **Scar Avoidance** | Rejected paths avoided | Scar count / rejection count |
| **Trap Escape Rate** | % of runs reaching global minimum | Binary success flag |

## Implementation Architecture

### File: `experiments/gmi_comparison.py`

```python
# Core components

class MultiModalPotential:
    """Multi-modal landscape with trap"""
    def __call__(self, x): ...
    def gradient(self, x): ...  # For baseline comparison

def run_gradient_descent(initial_x, lr, max_steps, threshold):
    """Baseline: pure greedy descent"""
    ...

def run_gmi_governed(initial_x, budget, use_memory):
    """GMI with optional memory scarring"""
    ...

# Results
@dataclass
class ExperimentResult:
    baseline_steps_mean, baseline_steps_std
    gmi_steps_mean, gmi_steps_std  
    gmi_memory_steps_mean, gmi_memory_steps_std
    # ... additional metrics
```

### Key Parameters

| Parameter | Baseline | GMI | GMI+Memory |
|-----------|----------|-----|-------------|
| learning_rate | 0.1 | N/A | N/A |
| initial_budget | N/A | 50.0 | 50.0 |
| EXPLORE sigma | N/A | 3.0 | 3.0 |
| EXPLORE kappa | N/A | 8.0 | 8.0 |
| INFER sigma | N/A | 0.5 | 0.5 |
| INFER kappa | N/A | 0.0 | 0.0 |
| memory lambda_c | N/A | N/A | 10.0 |

## Expected Outcomes

### Baseline (Gradient Descent)
- **Behavior**: Greedy descent toward nearest minimum
- **Expected**: May get stuck at trap (3, 3) with V ≈ 2
- **Reason**: No exploration mechanism

### GMI (No Memory)
- **Behavior**: EXPLORE attempts random jumps, INFER fallback
- **Expected**: Mixed results - sometimes escapes trap, sometimes not
- **Reason**: Budget limits exploration, but κ allows some ascent

### GMI + Memory
- **Behavior**: Rejected paths create scars
- **Expected**: Over multiple runs, should show learning
- **Reason**: Scars increase local potential, discouraging repeated failures

## Statistical Analysis

Run each configuration 10 times with different random seeds:

```python
seeds = range(10)
for seed in seeds:
    baseline_result = run_gradient_descent(..., seed=seed)
    gmi_result = run_gmi_governed(..., seed=seed, use_memory=False)
    gmi_memory_result = run_gmi_governed(..., seed=seed, use_memory=True)
```

Report:
- Mean and standard deviation for each metric
- Statistical significance (t-test) between configurations
- Per-run trajectories for qualitative analysis

## Execution

```bash
cd /home/user/gmi
python experiments/gmi_comparison.py
```

Output:
- Console: Summary statistics per run
- File: `outputs/receipts/experiment_results.json`

## Success Criteria

| Criterion | Target |
|-----------|--------|
| GMI escape rate | > 50% (vs baseline 0%) |
| Memory benefit | > 20% improvement in final V |
| Budget efficiency | < 80% of initial budget used |
| Convergence | Within 2x baseline steps |

## Extension Possibilities

1. **Parameter Sweep**: Vary σ/κ ratios to find optimal budgets
2. **Trap Configuration**: Test different trap locations/strengths
3. **Multi-dimensional**: Scale to 10D, 100D problems
4. **Real-world tasks**: Integrate with actual NPE/solver tasks
