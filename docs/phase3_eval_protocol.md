# Phase 3 Evaluation Protocol

**Phase**: 3  
**Status**: Final v1.0  
**Purpose**: Multi-task evaluation protocol for Phase 3 — measuring substrate value across Task A (diagnosis) and Task B (triage).

---

## Overview

This protocol defines how to evaluate GM-OS substrate value across two tasks:
- **Task A**: Constrained Diagnosis (Phase 2 task)
- **Task B**: Constrained Maintenance Triage (Phase 3 task)

The key question: Does the substrate (memory, modes, adaptation) add value beyond governance alone?

---

## Task Specifications

### Task A: Constrained Diagnosis

From Phase 2 — given symptoms and memory, select correct diagnosis.

- **Input**: 20 symptoms, 1000 memory cases, 10 candidates
- **Output**: Selected diagnosis + confidence
- **Constraints**: 10 step budget, 20% reserve floor

### Task B: Constrained Maintenance Triage

From Phase 3 spec — given symptoms, context, severity, select next action.

- **Input**: 20 symptoms, equipment context, severity, 500 memory cases, 7 actions
- **Output**: Selected action + confidence + risk assessment
- **Constraints**: 8 step budget, 20% reserve floor, SafeHold option

---

## Systems Under Evaluation

### Baseline A: Simple Heuristic

- Task A: Pick diagnosis with highest symptom overlap
- Task B: Pick action matching highest severity
- No memory, no verification, no budget

### Baseline B: Ungoverned GMI

- Same architecture as full system
- Skip verification step
- Unlimited budget (no reserve enforcement)

### System C: Full GMI on GM-OS (Phase 2 variant)

- Complete loop: percept → memory → proposal → verify → commit → receipt
- Budget constraints enforced
- Memory retrieval enabled

### System D: Full GMI + Enhanced Memory (Phase 3)

- System C + improved retrieval scoring
- Noise filtering enabled
- Retrieval attribution

### System E: Full GMI + Mode Integration (Phase 3)

- System D + explicit mode machine
- SafeHold pathway enabled
- Mode transition logging

### System F: Full GMI + Adaptation (Phase 3)

- System E + cross-episode adaptation
- Memory utility reweighting
- Failure pattern tagging

---

## Ablation Variants

### Core Ablations (for each system)

| Ablation | Description |
|----------|-------------|
| `-Memory` | Disable memory retrieval entirely |
| `-Adaptation` | Disable cross-episode adaptation |
| `-Repair` | Disable repair pathway |
| `-SafeHold` | Disable SafeHold option (Task B only) |
| `-Modes` | Disable explicit mode transitions |

### Memory-Specific Ablations

| Ablation | Description |
|----------|-------------|
| `-Semantic` | Disable semantic/schema memory |
| `-Consolidation` | Disable memory consolidation |
| `TopK-1` | Retrieve only 1 memory (vs default 5) |
| `TopK-10` | Retrieve 10 memories |

---

## Metrics

### Primary KPI

**Multi-Task Governed Success Rate**

```
MGSR = (Task_A_Accuracy + Task_B_Accuracy) / 2
```

### Guardrails

| Guardrail | Description | Threshold |
|-----------|-------------|-----------|
| **Coherence Failure Rate** | % proposals rejected by verifier | < 20% |
| **Budget Efficiency** | Mean spend per successful episode | < 80% of limit |
| **Memory Harm Rate** | Accuracy with memory vs without | ≥ 0% (not negative) |
| **Latency** | Time per episode | < 2x baseline |

### Task-Specific Metrics

#### Task A (Diagnosis)

- Accuracy: Correct diagnosis rate
- Confidence calibration: |confidence - accuracy| < 0.1
- Verification rejection rate

#### Task B (Triage)

- Action accuracy: Correct/acceptable action rate
- SafeHold appropriate rate: % high-uncertainty cases with SafeHold
- Risk violation rate: Risky actions taken incorrectly
- Abstention rate: How often SafeHold used overall

---

## Evaluation Procedure

### 1. Generate Test Sets

```python
# Task A: Same as Phase 2
task_a_test = generate_test_cases(n=200, task_type="diagnosis")
task_a_memory = generate_memory_cases(n=1000, task_type="diagnosis")

# Task B: New for Phase 3
task_b_test = generate_test_cases(n=200, task_type="triage")
task_b_memory = generate_memory_cases(n=500, task_type="triage")
```

### 2. Run Each System Variant

```python
systems = [
    ("baseline_a", BaselineA()),
    ("baseline_b", BaselineB()),
    ("system_c", SystemC()),      # Phase 2 full GMI
    ("system_d", SystemD()),      # + enhanced memory
    ("system_e", SystemE()),      # + mode integration
    ("system_f", SystemF()),      # + adaptation
]

ablations = [
    ("full", {}),
    ("no_memory", {"memory_enabled": False}),
    ("no_adaptation", {"adaptation_enabled": False}),
    ("no_safehold", {"safehold_enabled": False}),  # Task B only
]

for task_name, test_cases, memory_cases in [("A", task_a_test, task_a_memory), 
                                              ("B", task_b_test, task_b_memory)]:
    for system_name, system in systems:
        for ablation_name, ablation_config in ablations:
            configure_system(system, ablation_config)
            results = run_evaluation(system, test_cases, memory_cases)
            save_results(f"{task_name}_{system_name}_{ablation_name}", results)
```

### 3. Compute Metrics

```python
def compute_metrics(results):
    accuracy = correct / total
    memory_benefit = accuracy_with_memory - accuracy_without_memory
    coherence_failures = rejected / total
    budget_efficiency = mean_spend / max_budget
    latency = mean_time_per_episode
    
    return {
        "accuracy": accuracy,
        "memory_benefit": memory_benefit,
        "coherence_failure_rate": coherence_failures,
        "budget_efficiency": budget_efficiency,
        "latency": latency,
    }
```

### 4. Statistical Comparison

- Compare full system vs ablations: Paired t-test or McNemar's chi-squared
- Significance threshold: p < 0.05
- Effect size: Cohen's d for accuracy differences

### 5. Repeated Trials

- Run with 10 different random seeds
- Report mean ± std deviation
- Compute 95% confidence intervals

---

## Required Comparisons

### Memory Value Demonstration

```
Memory helps if:
    System_F accuracy > System_F(no_memory) accuracy
    AND memory_benefit > 0
```

### Substrate Value Demonstration

```
Substrate helps if:
    System_F accuracy > System_C accuracy  (on at least one task)
    OR System_F accuracy > System_B accuracy  (on both tasks)
```

### Generalization Demonstration

```
Generalization if:
    Substrate value shown on Task_A
    AND Substrate value shown on Task_B
    AND No catastrophic collapse on either task
```

---

## Output Format

### Per-System Results

```json
{
  "system": "system_f",
  "task": "B",
  "accuracy": 0.78,
  "accuracy_std": 0.04,
  "memory_benefit": 0.06,
  "coherence_failure_rate": 0.08,
  "budget_efficiency": 0.65,
  "latency_ms": 145,
  "safehold_rate": 0.12,
  "safehold_appropriate_rate": 0.85,
  "n_trials": 10,
  "n_test_cases": 200
}
```

### Summary Comparison

```json
{
  "phase": 3,
  "tasks": ["diagnosis", "triage"],
  "multi_task_success_rate": 0.745,
  "memory_harm_rate": -0.02,
  "governance_value_retained": true,
  "substrate_value_demonstrated": true,
  "generalization_demonstrated": true,
  "systems": {
    "baseline_a": {"task_a": 0.09, "task_b": 0.15},
    "baseline_b": {"task_a": 0.63, "task_b": 0.58},
    "system_c": {"task_a": 0.72, "task_b": 0.65},
    "system_d": {"task_a": 0.74, "task_b": 0.71},
    "system_e": {"task_a": 0.75, "task_b": 0.74},
    "system_f": {"task_a": 0.76, "task_b": 0.78}
  },
  "ablations": {
    "no_memory": {"task_a": 0.80, "task_b": 0.72},
    "no_adaptation": {"task_a": 0.74, "task_b": 0.75},
    "no_safehold": {"task_a": null, "task_b": 0.71}
  }
}
```

---

## Success Criteria

### Phase 3 Complete (Minimum)

- [ ] Memory benefit ≥ 0% on at least one task
- [ ] Governance gains from Phase 2 retained
- [ ] Task B runs without catastrophic collapse

### Phase 3 Strong

- [ ] Full substrate beats no-memory variant on at least one task
- [ ] Multi-task results stable across seeds (std < 5%)
- [ ] SafeHold measurably improves guardrails

### Phase 3 Exceptional

- [ ] Memory AND adaptation both positive
- [ ] Repair becomes useful on real slice
- [ ] Two-task performance shows substrate value

---

## Fairness Notes

1. **Same information**: All systems see same symptoms, same memory
2. **Same time**: No latency advantages
3. **Same test sets**: All evaluated on identical cases
4. **No data leakage**: Memory cases ≠ test cases
5. **Ablation consistency**: Same ablation config across tasks

---

## Analysis Requirements

### Memory Utility Report

- Retrieval frequency by task
- Attribution quality scores
- Noise filtering effectiveness
- Memory influence on proposals

### Mode Transition Report

- Mode distribution by task
- SafeHold invocation reasons
- Mode-specific failure rates
- Transition latency impact

### Adaptation Impact Report

- Utility reweighting effectiveness
- Failure pattern detection accuracy
- Adaptation stability over episodes
- Rollback frequency

### Failure Cluster Report

- Failure types by task
- Substrate contribution to failures
- Recovery success rates

---

*This protocol defines how to fairly compare substrate variants across multiple tasks.*
