# Phase 3 Execution Plan

## Executive Summary

Phase 3 transforms GM-OS from a working governed host into a genuine cognitive substrate with useful memory, explicit operating modes, and cross-episode adaptation. Based on Phase 2 results, the critical bottleneck is **memory quality** — memory exists but actively degrades performance by ~9%.

---

## Phase 2 Baseline (Starting Point)

| Component | Implementation | Value Demonstrated |
|-----------|----------------|-------------------|
| Hosted GMI loop | ✅ Complete | ✅ Yes |
| Budget constraints | ✅ Complete | ✅ Yes (+12%) |
| Verification | ✅ Complete | ✅ Yes |
| Memory retrieval | ✅ Complete | ❌ No (-9%) |
| Repair pathway | ✅ Complete | ❌ No (0% activation) |
| Operating modes | ⚠️ Enum exists | ⚠️ Not integrated |
| Cross-episode adaptation | ❌ Missing | ❌ N/A |
| Multi-task evaluation | ⚠️ 1 task | ❌ Need 2nd |

---

## Phase 3 Objectives

1. **Memory becomes useful** — beat no-memory ablation on at least one task
2. **Substrate contributes beyond governance** — show memory, mode, state, adaptation value
3. **Gains generalize** — demonstrate on at least two distinct tasks

### Primary KPI
**Multi-task governed success rate** — average task success across two frozen task suites

### Guardrails
- Coherence failure rate
- Budget efficiency (mean spend per success)
- Memory harm rate (must decrease from Phase 2's -9%)
- Latency (substrate richness cannot become computational oatmeal)

---

## Workstream Breakdown

### Workstream A — Memory Rehabilitation
**Goal**: Turn memory from harmful to helpful

**Required Components**:
- [ ] Enhanced retrieval scoring with task-specific weights
- [ ] Noise filtering (reject low similarity, contradictory context)
- [ ] Attribution (each retrieval states why it was included)
- [ ] Memory influence control (not blind obedience)
- [ ] Working memory (short-lived active context)
- [ ] Semantic/schema memory (failure motifs, success templates)

**Key Files**:
- `gmos/src/gmos/memory/retrieval.py` (create)
- `gmos/src/gmos/memory/relevance.py` (enhance)
- `gmos/src/gmos/memory/consolidation.py` (enhance)

**Success Criteria**:
- Full system beats no-memory ablation on at least one task
- Memory harm rate decreases substantially
- Retrieval decisions are inspectable

---

### Workstream B — Mode Architecture Integration
**Goal**: Give GM-OS explicit operating modes and transitions

**Required Components**:
- [ ] Mode state machine in episode runner
- [ ] Explicit transitions: Observe → Recall → Deliberate → Verify → Commit → Repair → Consolidate
- [ ] SafeHold pathway (abstention under uncertainty)
- [ ] Mode-specific metrics
- [ ] Mode transition logging in traces

**Existing Assets**:
- `gmos/src/gmos/kernel/substrate_state.py` already has `OperationalMode` enum (10 modes)
- Need to integrate into `gmos/src/gmos/runtime/minimal_loop.py`

**Key Files**:
- `gmos/src/gmos/runtime/mode_machine.py` (create)
- `gmos/src/gmos/runtime/episode_runner.py` (create)
- `gmos/src/gmos/runtime/safehold.py` (create)

**Success Criteria**:
- Transitions are explicit in traces
- Different failure types route to different modes
- SafeHold exists as real pathway

---

### Workstream C — Cross-Episode Adaptation
**Goal**: Make system learn from prior cases without full retraining

**Allowed Mechanisms**:
- Memory utility reweighting
- Retrieval score updates
- Policy threshold calibration
- Failure pattern tagging
- Proposal ranking adjustments
- Confidence calibration

**NOT Required**:
- Gradient-based continual learning
- Giant model retraining
- Self-modifying core logic

**Key Files**:
- `gmos/src/gmos/agents/gmi/adaptation.py` (create)
- `gmos/src/gmos/memory/utility_tracker.py` (create)

**Success Criteria**:
- Later episodes benefit from earlier episodes on at least one task slice
- Adaptation pathway is auditable
- Bad adaptation can be detected and rolled back

---

### Workstream D — Multi-Task Evaluation
**Goal**: Show substrate is not a one-benchmark trick

**Task A**: Constrained Diagnosis (existing Phase 2 task)
- Symptoms → diagnosis (10 candidates)
- 1000 memory cases
- 10 step budget

**Task B**: Memory-informed constrained maintenance triage / next-action recommendation

- **Input**: symptoms, equipment context, severity indicators, prior cases, budget/risk constraints, optional ambiguity
- **Output**: recommended action from finite set (inspect locally, shut down, continue/monitor, escalate, replace, gather evidence, SafeHold/abstain)
- **Why it fits**: Tests state-dependent action selection (vs Task A's state interpretation), rewards memory, budget-aware verification, SafeHold, verifier rejection of risky actions

**Key Insight from Phase 2**: Memory hurt by 9% on diagnosis. This means Task B should have:
- Different memory noise profile (less noisy retrieval)
- Action-oriented success criteria (vs classification)
- Natural abstention opportunity (SafeHold should help)

**Evaluation Protocol**:
- [ ] Define Task B specification
- [ ] Run Task A with all ablations
- [ ] Run Task B with all ablations
- [ ] Compare: weak baseline, ungoverned, governed, governed+memory, no-memory ablation

**Key Files**:
- `gmos/benchmarks/phase3/task_a/` (reuse)
- `gmos/benchmarks/phase3/task_b/` (create)
- `gmos/benchmarks/phase3/run_eval.py` (create)
- `gmos/benchmarks/phase3/ablation.py` (create)

---

### Workstream E — Instrumentation and Analysis
**Goal**: Make substrate behavior diagnosable

**Required Traces**:
- Mode transitions
- Percept bundle
- Retrieved memory IDs and scores
- Proposal set
- Verifier scores by component
- Repair attempts
- SafeHold/abstention events
- Budget before/after
- Confidence and uncertainty measures
- Final action
- Success/failure outcome

**Analysis Outputs**:
- Memory utility report
- Mode transition report
- Adaptation impact report
- Failure cluster report by task

**Key Files**:
- `gmos/benchmarks/phase3/analyze_memory.py` (create)
- `gmos/benchmarks/phase3/analyze_modes.py` (create)

---

### Workstream F — Documentation
**Required Docs**:
- `docs/phase3_objective.md` — mission, KPI, guardrails, scope
- `docs/phase3_memory_spec.md` — memory layers, retrieval, consolidation
- `docs/phase3_mode_architecture.md` — modes, transitions, SafeHold
- `docs/phase3_eval_protocol.md` — both tasks, ablations, metrics
- `docs/phase3_status_matrix.md` — implementation vs value status
- `docs/phase3_error_analysis.md` — where substrate helps/hurts

---

## Ablations Required

### Core Ablations
- Full governed substrate
- No memory
- No adaptation
- No repair
- No SafeHold
- Ungoverned control

### Memory-Specific Ablations
- Episodic only
- Episodic + semantic
- With consolidation
- Without consolidation
- Top-k retrieval sweep

### Mode-Specific Ablations
- SafeHold disabled
- Forced direct commit
- No explicit Recall mode
- No explicit Consolidate mode

---

## Execution Order

### Step 1: Foundation (Week 1-2)
1. Define Task B specification
2. Create Phase 3 eval protocol
3. Set up benchmark infrastructure for Task B

### Step 2: Memory Rehabilitation (Week 2-4)
1. Rebuild retrieval scoring with task-specific weights
2. Add noise filtering mechanisms
3. Add retrieval attribution
4. Add memory influence control (not blind obedience)
5. Run Task A ablations until memory stops hurting

### Step 3: Mode Integration (Week 3-4)
1. Create mode machine
2. Integrate modes into episode runner
3. Add SafeHold pathway
4. Add mode transition logging

### Step 4: Adaptation (Week 4-5)
1. Create utility tracking
2. Implement basic reweighting
3. Add failure pattern tagging

### Step 5: Multi-Task Eval (Week 5-6)
1. Run Task B with all variants
2. Compare substrate value on both tasks
3. Run repeated-seed evaluation

### Step 6: Analysis & Docs (Week 6-7)
1. Generate all analysis reports
2. Create all documentation
3. Final status matrix

---

## Completion Thresholds

### Minimum Completion
- [ ] Memory helps at least one meaningful slice or one task
- [ ] Governance gains from Phase 2 do not vanish
- [ ] Task B runs successfully with no catastrophic collapse

### Strong Completion
- [ ] Full substrate beats no-memory/no-adaptation variants on at least one task
- [ ] Multi-task results are stable across seeds
- [ ] SafeHold or mode routing measurably improves guardrails

### Exceptional Completion
- [ ] Memory and adaptation both show positive contribution
- [ ] Repair becomes useful on a real slice
- [ ] Two-task performance shows substrate value beyond single-task governance

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Memory still hurts | Iteratively tune retrieval; accept memory might not work for all tasks |
| Mode machine adds complexity without value | Keep modes minimal; measure mode-specific metrics |
| Task B chosen poorly | Pick Task B that shares Task A's substrate requirements |
| Adaptation becomes unstable | Add rollback mechanism; keep adaptations explicit |

---

## Bottleneck Focus

**The critical quantity to optimize first**: Memory quality and integration

Specifically:
- Retrieval relevance
- Noise suppression
- Weighting memory against percept evidence
- Deciding when memory should be ignored

This is the make-or-break component of Phase 3.
