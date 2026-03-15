# Phase 2 Evaluation Protocol

**Phase**: 2  
**Status**: Final (v1.0)  
**Purpose**: Define how to evaluate GMI on the constrained diagnosis task.

---

## Overview

This document defines the evaluation protocol for Phase 2: measuring whether the governed GMI substrate can host useful intelligence that outperforms simpler baselines.

---

## Task: Constrained Diagnosis

### Input
- **Symptoms**: Binary vector (20 symptoms)
- **Memory**: 1000 past (symptoms → diagnosis) cases
- **Candidates**: 10 possible diagnoses

### Output
- **Selected Diagnosis**: One of 10 candidates
- **Confidence**: 0-1 scale
- **Rationale**: Why this diagnosis

### Constraints
- **Budget**: Max 10 reasoning steps per episode
- **Reserve Floor**: Must preserve 20% budget for future episodes

---

## Systems Under Evaluation

### System A: Simple Heuristic
- Pick diagnosis with highest symptom overlap
- No memory, no verification, no budget
- **Baseline**

### System B: Ungoverned GMI
- Same architecture as full GMI
- Skip verification step
- Unlimited budget
- **Control**

### System C: Full GMI on GM-OS
- Complete loop: percept → memory → proposal → verify → commit → receipt
- Budget constraints enforced
- Reserve floor protected
- **System Under Test**

---

## Metrics

### Primary KPI

| Metric | Description | Target |
|--------|-------------|--------|
| **Accuracy** | Correct diagnosis rate on 200 held-out test cases | > Baseline A |

### Guardrails

| Guardrail | Description | Threshold |
|-----------|-------------|-----------|
| **Coherence Violations** | % of proposals rejected by verifier | < 20% |
| **Budget Discipline** | Reserve floor violations | = 0% |
| **Average Spend** | Mean budget per episode | < 80% of limit |

### Secondary Metrics

| Metric | Description |
|--------|-------------|
| **Memory Benefit** | Accuracy improvement with memory vs without |
| **Verification Impact** | % of proposals repaired/blocked |
| **Latency** | Time per episode |

---

## Evaluation Procedure

### 1. Generate Test Set

```python
# 200 held-out cases
# 1000 training cases (memory)
# 10 diagnoses, 20 symptoms
```

### 2. Run Each System

```python
for system in [A, B, C]:
    results = []
    for case in test_set:
        diagnosis = system.diagnose(case.symptoms, case.memory)
        results.append({
            "predicted": diagnosis,
            "actual": case.diagnosis,
            "spend": system.spent,
            "verified": system.verification_used
        })
```

### 3. Compute Metrics

```python
accuracy = correct / total
coherence_violations = rejected / total
reserve_violations = (budget < reserve_floor).sum() / total
```

### 4. Statistical Comparison

- Compare C vs A: Chi-squared test
- Compare C vs B: Chi-squared test
- Significance threshold: p < 0.05

---

## Success Criteria

| Criterion | Threshold |
|-----------|-----------|
| C beats A | Yes (p < 0.05) |
| C beats B | Yes or No |
| Coherence violations | < 20% |
| Reserve violations | = 0% |
| Average spend | < 80% of limit |

---

## Output Format

Results should be saved to JSON:

```json
{
  "system": "C",
  "accuracy": 0.85,
  "coherence_violations": 0.12,
  "reserve_violations": 0.0,
  "avg_spend": 6.5,
  "n_test_cases": 200,
  "memory_benefit": 0.15,
  "verification_impact": 0.08,
  "baseline_a_accuracy": 0.65,
  "baseline_b_accuracy": 0.72,
  "p_value_vs_a": 0.001,
  "p_value_vs_b": 0.023
}
```

---

## Fairness Notes

1. **Same information**: All systems see same symptoms, same memory
2. **Same time**: No latency advantages
3. **Same test set**: All evaluated on identical 200 cases
4. **No data leakage**: Memory cases ≠ test cases

---

*This protocol defines how to fairly compare governed vs ungoverned vs heuristic systems.*
