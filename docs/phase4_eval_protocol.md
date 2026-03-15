# Phase 4 Evaluation Protocol

**Phase**: 4  
**Status**: Draft  
**Purpose**: Multi-regime evaluation protocol for Phase 4 — measuring selective intelligence across Tasks A, B, and C.

---

## Overview

This protocol defines how to evaluate GM-OS selective intelligence across three or more task regimes:
- **Task A**: Constrained Diagnosis (from Phase 2)
- **Task B**: Constrained Maintenance Triage (from Phase 3)
- **Task C**: Evidence-Gathering Recommendation (new for Phase 4)

The key question: Does selective feature use outperform always-on feature use?

---

## Primary KPI

### Primary KPI: Calibrated Multi-Task Utility

A weighted score combining:
- Task success rate
- Incoherent-commit penalty
- Unnecessary SafeHold penalty
- Catastrophic error penalty
- Spend efficiency

**Simplified public KPI**: Mean task success across Tasks A, B, and C

---

## Guardrails

### Guardrail 1 — Incoherent Commit Rate
How often the system commits an action that violates constraints or is clearly wrong under governance.

### Guardrail 2 — Unnecessary Abstention / SafeHold Rate
How often SafeHold fires when a correct action would have been better.

### Guardrail 3 — Memory Harm Rate
How often memory lowers performance relative to no-memory ablation.

### Guardrail 4 — Latency / Compute Overhead
Selective intelligence that takes forever becomes decorative.

### Guardrail 5 — Evidence-Request Quality
If the system asks for more evidence, it should actually improve downstream outcomes often enough to justify the detour.

---

## Systems Under Evaluation

### Baseline Systems
- **Baseline A**: Simple Heuristic (task-specific rules)
- **Baseline B**: Ungoverned GMI (no substrate features)
- **System C**: Always-On Governance (all features enabled)

### Selective Systems (Phase 4)
- **System D**: Gated Governance (selective feature use)
- **System E**: Gated + Evidence Request
- **System F**: Gated + No Memory
- **System G**: Gated + No SafeHold
- **System H**: Gated + No Repair
- **System I**: Gated + No Adaptation

---

## Task Specifications

### Task A: Constrained Diagnosis
Same as Phase 2. Input: symptoms. Output: diagnosis from fixed set.

### Task B: Constrained Maintenance Triage  
Same as Phase 3. Input: maintenance situation. Output: action from fixed set.

### Task C: Evidence-Gathering Recommendation (NEW)
Input: diagnostic situation with uncertainty
Output: 
- Proceed with current evidence
- Request specific additional evidence
- Abstain (SafeHold)

This fits directly with calibration and selective intelligence goals.

---

## Required Ablations

### Feature-Use Ablations
1. Always-on memory vs gated memory
2. Always-on SafeHold vs calibrated SafeHold
3. Generic repair vs targeted repair
4. Adaptation on vs off
5. Evidence request on vs off

### Task/Regime Ablations
1. Task A
2. Task B
3. Task C or shifted regime
4. Low ambiguity
5. High ambiguity
6. Low budget
7. Tight budget
8. Noisy percepts
9. Missing evidence

### Utility Sweeps
1. SafeHold threshold sweep
2. Memory top-k sweep
3. Evidence-request threshold sweep
4. Repair-trigger threshold sweep

---

## Evaluation Procedure

### 1. Define Task Regimes
- Task A (diagnosis)
- Task B (triage)
- Task C (evidence gathering) or shifted regimes

### 2. Define System Configurations
- Baseline A, B, C (always-on)
- D-I (selective variants)

### 3. Run Each Configuration
Use 10-seed repeated trials across all tasks.

### 4. Compute Metrics
- Task success rate (per task and combined)
- Guardrail metrics
- Utility scores

### 5. Statistical Comparison
- Compare selective vs always-on
- Confidence intervals
- Significance testing

### 6. Calibration Analysis
- Reliability curves
- Confidence buckets
- Abstention-performance curves

---

## Completion Thresholds

### Phase 4 Minimum Completion
- [ ] Gated memory improves utility over always-on in at least one regime
- [ ] Calibrated SafeHold reduces harmful overuse
- [ ] Task C or shifted regime is operational
- [ ] Repeated-seed evaluation supports selective-policy benefit

### Phase 4 Strong Completion
- [ ] Selective substrate beats always-on on combined utility
- [ ] Evidence-request mode adds measurable value
- [ ] Repair becomes useful on at least one failure class
- [ ] Memory harm rate drops materially

### Phase 4 Exceptional Completion
- [ ] Selective policy improves both performance and guardrails
- [ ] Calibration is demonstrably good
- [ ] System chooses right internal behavior

---

## Reproducibility

### Seeds
10-seed evaluation: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

### Data
- Task A: 100 cases
- Task B: 100 cases  
- Task C: 100 cases (new)

### Expected Runtime
- Single evaluation: ~30 seconds per task
- Full 10-seed multi-system: ~15 minutes

---

## Output Format

### Results Schema
```json
{
  "phase": 4,
  "timestamp": "ISO-8601",
  "tasks": ["A", "B", "C"],
  "systems": [...],
  "seeds": [0-9],
  "results": {
    "system_name": {
      "task_a": {"accuracy": X, "std": Y},
      "task_b": {"accuracy": X, "std": Y},
      "task_c": {"accuracy": X, "std": Y},
      "combined": {"utility": X, "std": Y}
    }
  },
  "guardrails": {...},
  "calibration": {...}
}
```
