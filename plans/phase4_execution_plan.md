# Phase 4 Execution Plan

## Overview

This plan implements **Phase 4: Selective, Calibrated, Extensible Substrate Intelligence**.

The core goal: Make GM-OS selectively intelligent about when to use its own features.

---

## Phase 3 Summary

| What Works | What Doesn't |
|------------|--------------|
| Memory helps Task B (+53%) | Memory doesn't help Task A (0%) |
| Mode machine integrated | SafeHold overactive (67%) |
| Multi-task evaluation | Adaptation not valuable |
| Path handling fixed | Repair not valuable |

---

## Workstreams

### Workstream A: Feature Gating (Priority: HIGH)
**Goal**: Build policy layer deciding when features activate

**Files to create**:
- `gmos/src/gmos/agents/gmi/gating.py`
- `gmos/src/gmos/agents/gmi/gating_config.py`
- `gmos/src/gmos/agents/gmi/gating_context.py`

**Deliverables**:
- Memory gating policy
- SafeHold gating policy
- Repair gating policy
- Evidence request gating policy
- Adaptation gating policy

---

### Workstream B: Calibration Layer (Priority: HIGH)
**Goal**: Make confidence, uncertainty, and abstention thresholds explicit

**Files to create**:
- `gmos/src/gmos/agents/gmi/calibration.py`
- `gmos/src/gmos/runtime/confidence.py`

**Deliverables**:
- Confidence estimator
- Uncertainty scorer
- Abstention threshold policy
- Calibration curves

---

### Workstream C: Evidence Request Mode (Priority: HIGH)
**Goal**: Teach system to request more evidence instead of acting or freezing

**Files to create**:
- `gmos/src/gmos/runtime/evidence_request.py`
- `gmos/benchmarks/phase4/task_c/dataset.py`

**Deliverables**:
- Evidence request action
- Task C dataset
- Evidence type selection

---

### Workstream D: Task C / Distribution Shift (Priority: MEDIUM)
**Goal**: Add third evaluation regime

**Files to create**:
- `gmos/benchmarks/phase4/task_c/`
- `docs/phase4_task_c_spec.md` (done)

**Deliverables**:
- Task C dataset generator
- Shifted-regime variants

---

### Workstream E: Targeted Repair (Priority: MEDIUM)
**Goal**: Make repair useful or demote honestly

**Files to create**:
- `gmos/src/gmos/runtime/repair_strategies.py`

**Deliverables**:
- Repair strategy classes
- Failure-type-specific repair
- Repair value demonstration or honest demotion

---

### Workstream F: Evaluation and Analysis (Priority: HIGH)
**Goal**: Prove selective intelligence works

**Files to create**:
- `gmos/benchmarks/phase4/run_eval.py`
- `gmos/benchmarks/phase4/repeated_seeds.py`
- `gmos/benchmarks/phase4/analyze_calibration.py`
- `gmos/benchmarks/phase4/analyze_gating.py`

**Deliverables**:
- 10-seed multi-system evaluation
- Calibration analysis
- Gating analysis

---

## Recommended Build Order

### Step 1: Foundation (Week 1)
1. Create Phase 4 directory structure
2. Implement gating configuration classes
3. Implement gating context structures

### Step 2: Feature Gating (Week 2)
1. Implement memory gating logic
2. Implement SafeHold gating logic
3. Integrate gating into existing evaluation

### Step 3: Calibration (Week 3)
1. Implement confidence estimation
2. Implement threshold policies
3. Run calibration sweeps

### Step 4: Evidence Request (Week 4)
1. Create Task C dataset
2. Implement evidence request action
3. Test evidence gathering decisions

### Step 5: Task C Evaluation (Week 5)
1. Run full evaluation on Tasks A, B, C
2. Compare gated vs always-on
3. Analyze results

### Step 6: Repair Specialization (Week 6)
1. Implement targeted repair strategies
2. Test repair value
3. Decide: useful or demote

### Step 7: Final Analysis (Week 7)
1. 10-seed repeated evaluation
2. Write closure memo
3. Update status docs

---

## Required Ablations

### Must Run
1. Always-on memory vs gated memory
2. Always-on SafeHold vs calibrated SafeHold
3. Generic repair vs targeted repair
4. Adaptation on vs off
5. Evidence request on vs off

### Must Analyze
1. Task A, B, C accuracy
2. SafeHold rate vs accuracy
3. Memory benefit per task
4. Evidence request value

---

## Success Criteria

### Minimum Completion
- [ ] Gated memory > always-on in at least one regime
- [ ] SafeHold rate reduced from 67%
- [ ] Task C operational
- [ ] Repeated-seed shows selective benefit

### Strong Completion
- [ ] Selective beats always-on on utility
- [ ] Evidence request adds value
- [ ] Repair shows value OR is demoted
- [ ] Memory harm rate decreases

### Exceptional Completion
- [ ] Both performance and guardrails improve
- [ ] Calibration demonstrably good
- [ ] System chooses right behavior

---

## Files Created So Far

| File | Status |
|------|--------|
| `docs/phase4_objective.md` | ✅ Complete |
| `docs/phase4_eval_protocol.md` | ✅ Complete |
| `docs/phase4_task_c_spec.md` | ✅ Complete |
| `docs/phase4_policy_gating_spec.md` | ✅ Complete |
| `plans/phase4_execution_plan.md` | ✅ Complete |

---

## Next Steps

1. Create directory structure: `gmos/benchmarks/phase4/`
2. Implement gating configuration classes
3. Begin feature gating implementation
