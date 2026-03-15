# Phase 4 Status Matrix

## Overview

Phase 4 transforms GM-OS from a system with always-on features to a **selectively intelligent** substrate that decides when to use memory, SafeHold, repair, and evidence gathering.

**Status**: 🚧 IN PROGRESS

---

## Phase 3 Summary

| Metric | Value |
|--------|-------|
| Task A Accuracy | 68.7% ± 4.6% |
| Task A Memory Benefit | 0.0% |
| Task B Accuracy | 67.1% ± 3.0% |
| Task B Memory Benefit | **+53.0% ± 5.6%** ✓ |
| SafeHold Rate | 67% (overactive) |
| Multi-Task Success | 67.9% |

---

## Phase 4 Objective

> GM-OS hosts calibrated GMI processes that selectively use memory, SafeHold, repair, and evidence-gathering under governance, improving robustness and guardrails across at least three task regimes without unacceptable accuracy loss or complexity debt.

---

## Deliverables Status

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| 1 | Phase 4 Objective | ✅ Complete | [`phase4_objective.md`](phase4_objective.md) |
| 2 | Evaluation Protocol | ✅ Complete | [`phase4_eval_protocol.md`](phase4_eval_protocol.md) |
| 3 | Calibration Protocol | ✅ Complete | [`phase4_calibration_protocol.md`](phase4_calibration_protocol.md) |
| 4 | Task C Specification | ✅ Complete | [`phase4_task_c_spec.md`](phase4_task_c_spec.md) |
| 5 | Policy Gating Spec | ✅ Complete | [`phase4_policy_gating_spec.md`](phase4_policy_gating_spec.md) |
| 6 | Gating Config | ✅ Complete | [`gating_config.py`](gmos/src/gmos/agents/gmi/gating_config.py) |
| 7 | Gating Context | ✅ Complete | [`gating_context.py`](gmos/src/gmos/agents/gmi/gating_context.py) |
| 8 | Gating Policy | ✅ Complete | [`gating.py`](gmos/src/gmos/agents/gmi/gating.py) |
| 9 | Calibration Layer | ✅ Complete | [`calibration.py`](gmos/src/gmos/agents/gmi/calibration.py) |
| 10 | Task C Dataset | ✅ Complete | [`task_c/dataset.py`](gmos/benchmarks/phase4/task_c/dataset.py) |
| 11 | Component Tests | ✅ Complete | [`test_gating.py`](gmos/benchmarks/phase4/test_gating.py) |
| 12 | Evaluation Harness | ⏳ Pending | Not yet created |
| 13 | Task C Integration | ⏳ Pending | Not yet created |
| 14 | Repeated-Seed Eval | ⏳ Pending | Not yet created |
| 15 | Closure Memo | ⏳ Pending | Not yet created |

---

## Implementation vs Value Demonstrated

| Component | Implemented | Value Demonstrated | Notes |
|-----------|-------------|-------------------|-------|
| Memory gating | ✅ Yes | ⏳ Pending | Need to show gated > always-on |
| SafeHold calibration | ✅ Yes | ⏳ Pending | Need to show calibrated < blunt |
| Evidence request | ✅ Yes | ⏳ Pending | Need Task C integration |
| Repair specialization | ⏳ Partial | ⏳ Pending | Need targeted strategies |
| Task C | ⏳ Partial | ⏳ Pending | Dataset ready, eval pending |
| Calibration analysis | ✅ Yes | ⏳ Pending | ECE < 0.1 target |

---

## Phase 4 Success Metrics

### Memory Rehabilitation
- [ ] Gated memory > always-on on at least one task
- [ ] Memory harm rate decreases on Task A
- [ ] Memory benefit preserved on Task B

### SafeHold Calibration
- [ ] SafeHold rate reduced from 67% to 10-30%
- [ ] Accuracy maintained or improved
- [ ] ECE < 0.1

### Evidence Gathering
- [ ] Evidence requests improve downstream accuracy
- [ ] Evidence request rate < 20%
- [ ] Task C operational

### Multi-Task
- [ ] Task A runs with gating
- [ ] Task B runs with gating
- [ ] Task C runs with gating
- [ ] Combined utility > always-on

---

## Required Experiments

### Experiment 1: Gated vs Always-On Memory
- [ ] Task A: always-on vs gated vs no memory
- [ ] Task B: always-on vs gated vs no memory
- [ ] Task C: gated vs no memory

### Experiment 2: SafeHold Calibration
- [ ] No SafeHold baseline
- [ ] Blunt SafeHold (current)
- [ ] Calibrated SafeHold (Phase 4)

### Experiment 3: Evidence Request Value
- [ ] Without evidence requests
- [ ] With evidence requests

### Experiment 4: Repeated Seeds
- [ ] 10-seed evaluation on Tasks A, B, C
- [ ] Statistical significance testing

---

## Phase 4 Completion Criteria

### Minimum Completion
- [ ] Gated memory improves utility in at least one regime
- [ ] SafeHold rate reduced from 67%
- [ ] Task C operational
- [ ] Repeated-seed supports selective-policy benefit

### Strong Completion
- [ ] Selective substrate beats always-on on utility
- [ ] Evidence request adds measurable value
- [ ] Memory harm rate drops materially

### Exceptional Completion
- [ ] Both performance and guardrails improve
- [ ] Calibration demonstrably good (ECE < 0.1)
- [ ] System chooses right behavior by context

---

## Key Insights from Phase 3

### What Works
- Memory helps Task B (+53%)
- Multi-task substrate functional
- Mode machine integrated

### What Doesn't Work
- Memory doesn't help Task A (0%)
- SafeHold overactive (67%)
- Adaptation shows no value

### Phase 4 Response
- **Gated memory**: Use only when beneficial
- **Calibrated SafeHold**: Tune thresholds
- **Task C**: Evidence gathering under uncertainty

---

## Files Created

### Documentation
```
docs/phase4_objective.md
docs/phase4_eval_protocol.md
docs/phase4_calibration_protocol.md
docs/phase4_task_c_spec.md
docs/phase4_policy_gating_spec.md
docs/phase4_status_matrix.md
```

### Code
```
gmos/src/gmos/agents/gmi/gating_config.py
gmos/src/gmos/agents/gmi/gating_context.py
gmos/src/gmos/agents/gmi/gating.py
gmos/src/gmos/agents/gmi/calibration.py
gmos/benchmarks/phase4/task_c/dataset.py
gmos/benchmarks/phase4/test_gating.py
```

---

## Next Steps

1. **Integrate gating into existing evaluation** (run_eval.py)
2. **Run Task A/B with gated vs always-on comparison**
3. **Complete Task C integration**
4. **Run repeated-seed evaluation**
5. **Write closure memo**

---

## Phase 4 Verdict (Current)

**IN PROGRESS - Minimum completion not yet achieved**

The Phase 4 scaffolding is in place:
- Gating policy implemented ✓
- Calibration layer implemented ✓
- Task C dataset implemented ✓

But value demonstration requires:
- Running the experiments
- Comparing gated vs always-on
- Measuring SafeHold calibration improvement
- Evaluating Task C

---

## Core Insight

> **Phase 4 is where the substrate learns when NOT to use its own features.**
