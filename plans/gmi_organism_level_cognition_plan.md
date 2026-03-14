# GMI Organism-Level Cognition Roadmap

## Vision Statement

Transform GMI from a perceptual demonstration into a robust organism-level cognitive system that demonstrates genuine planning, generalization, and semantic competence—measured by repeatable benchmarks.

---

## Gap Analysis & Roadmap

### 1. Strong Planning (Beyond Gradient Chasing)

**Current State**: GMI moves toward light/away from shadow via direct sensory-motor coupling (gradient following)

**Target State**: GMI decomposes goals into subgoals, switches strategies lawfully, remembers constraints, completes staged tasks

**Required Capabilities**:
- [ ] Goal decomposition: High-level objective → sequence of subgoals
- [ ] Subgoal monitoring: Track progress toward intermediate states
- [ ] Constraint tracking: Remember task-specific rules (e.g., "key required before door")
- [ ] State-space planning: Compute action sequences without execution

**Key-Door Maze Example**:
```
Goal: Reach goal state
  → Subgoal 1: Acquire key (requires: explore, detect key)
  → Subgoal 2: Reach door with key (requires: navigate, avoid obstacles)
  → Subgoal 3: Exit through door (requires: key in inventory, door unlocked)
```

**Implementation Approach**:
1. Extend 12-block state with `xi_goal ∈ ℝ^k` (goal representation)
2. Add planning operator: `P: (xi_goal, xi_world) → action_sequence`
3. Subgoal transitions via `ξ_task` block updates

---

### 2. Robust Task Completion

**Current State**: Behavioral response works in clean test environment

**Target State**: Completes tasks repeatedly, under noise, under budget pressure, no hidden scripting

**Required Capabilities**:
- [ ] Repetition resilience: Same task, multiple trials → consistent success
- [ ] Noise robustness: Sensory noise, action noise, state perturbations
- [ ] Budget pressure: Task completion under constrained reserves
- [ ] Error recovery: Detect failure, replan, retry

**Test Requirements**:
- [ ] Run maze task 100 times, track success rate
- [ ] Add Gaussian noise (σ=0.1, 0.2, 0.5) to sensory inputs
- [ ] Limit budget to 20% of nominal, verify graceful degradation
- [ ] Introduce dead-ends, measure recovery time

---

### 3. Wider Generalization (Transfer Learning)

**Current State**: Pattern discrimination in single visual field

**Target State**: Same machinery works across environments; learned skills transfer

**Required Capabilities**:
- [ ] Environment invariance: Core cognition independent of specific sensory layout
- [ ] Skill transfer: Poison avoidance in maze A → faster learning in maze B
- [ ] Visual salience → spatial navigation transfer

**Test Requirements**:
- [ ] Maze family: 10 maze variants, measure zero-shot performance
- [ ] Skill transfer: Learn object → navigate to object → new object, new location
- [ ] Cross-modal: Learn visual salience → apply to depth map

---

### 4. Strong Semantic Competence

**Current State**: Spectral signatures are mathematically distinguished but lack meaning

**Target State**: Track objects, relations, intentions, uncertainty, context

**Required Capabilities**:
- [ ] Object persistence: Track "same object" across time and viewpoint
- [ ] Relation representation: Spatial relations (above, below, near), causal relations
- [ ] Intention modeling: Infer goals from observed behavior
- [ ] Uncertainty representation: Confidence, ambiguity, unknown states

**Noetica Integration**:
- [ ] Semantic manifold: `S ∈ ℝ^d` for meaning representation
- [ ] Binding operator: Link perceptual features to object identities
- [ ] Context tracking: Maintain task-relevant world state

---

### 5. Mature Prediction

**Current State**: Spectral pattern discrimination (static memory comparison)

**Target State**: Forecast next state, action outcomes, route blockage, other agents

**Required Capabilities**:
- [ ] World model: `f: (state, action) → next_state`
- [ ] Action consequences: Predict outcome before execution
- [ ] Route prediction: Forecast path viability
- [ ] Theory of mind: Predict other agent behavior

**Implementation**:
- [ ] Forward model: Learn dynamics `ξ_{t+1} = F(ξ_t, a_t)`
- [ ] Rollout: Simulate n-step futures, select best
- [ ] Counterfactuals: "What if I took action b instead?"

---

### 6. Broad Benchmark Evidence

**Current State**: Custom perceptual tests (spectral discrimination, light/shadow)

**Target State**: Repeatable, legible benchmarks understandable without canon pilgrimage

**Benchmark Suite**:

| Benchmark | What It Tests | Success Metric |
|-----------|--------------|----------------|
| **Maze Family** | Planning, exploration, memory | Success rate across 10 variants |
| **Object Nav** | Semantic competence, transfer | Steps to object, novel objects |
| **Poison Avoidance** | Learning, generalization | Trials to convergence |
| **Key-Door** | Hierarchical planning, subgoals | Completion with constraints |
| **Multi-Agent** | Theory of mind, prediction | Predict other agent moves |

**Deliverable**: `benchmark_suite.py` with:
- [ ] Standardized task definitions
- [ ] Automated scoring
- [ ] Result logging (JSON/CSV)
- [ ] Comparison baselines

---

### 7. Polished Implementation

**Current State**: Working but with "repo seams" and "naming mismatches"

**Target State**: Clean APIs, consistent receipts, stable module boundaries

**Cleanup Tasks**:
- [ ] API audit: Consistent naming (e.g., `compute_drift` vs `drift`)
- [ ] Receipt consistency: All operations produce valid receipts
- [ ] Import paths: Resolve `gmos.gmi` vs `gmos.agents.gmi` issues
- [ ] Test isolation: No cross-test pollution
- [ ] Documentation: Each public API has docstring with parameters/returns

---

## Implementation Phases

### Phase 1: Planning Infrastructure (Weeks 1-3)

1. Extend `TwelveBlockState` with goal representation
2. Implement goal decomposition operator
3. Create simple maze environment (no obstacles)
4. Test: Navigate to goal, simple case

### Phase 2: Maze Tasks (Weeks 4-6)

1. Implement key-door maze environment
2. Add constraint tracking
3. Subgoal sequencing
4. Test: Complete key-door task 10/10 times

### Phase 3: Robustness (Weeks 7-9)

1. Add noise injection
2. Budget pressure testing
3. Error recovery mechanisms
4. Test: 100-trial success rate measurement

### Phase 4: Generalization (Weeks 10-12)

1. Maze family generation
2. Transfer learning setup
3. Cross-modal binding
4. Test: Zero-shot on novel mazes

### Phase 5: Prediction & Semantics (Weeks 13-16)

1. Forward model learning
2. Object persistence
3. Uncertainty representation
4. Benchmark suite finalization

---

## Priority Recommendations

Based on "strongest signal per effort":

1. **Start with Phase 1-2**: Planning + key-door maze gives clearest evidence of "not just gradient chasing"
2. **Parallelize Phase 7**: Clean up as you go—don't let tech debt compound
3. **Phase 3 before Phase 4**: Robustness first, then generalization
4. **Phase 5 is hardest**: Prediction and semantics require significant new machinery

---

## Key Files to Modify/Create

```
gmos/src/gmos/agents/gmi/
  planning/              # NEW: Planning infrastructure
    goal_decomposition.py
    task_graph.py
    forward_model.py
  environments/         # NEW: Benchmark environments
    maze.py
    key_door.py
  benchmarks/           # NEW: Benchmark suite
    suite.py
    scoring.py
  twelve_block_state.py # MODIFY: Add goal blocks
  full_dynamics.py      # MODIFY: Add planning operators

gmos/tests/agents/gmi/
  test_planning.py      # NEW
  test_maze.py          # NEW
  test_transfer.py      # NEW
  benchmark_runner.py   # NEW
```

---

## Success Criteria

The system has reached "organism-level cognition" when:

- [ ] Completes key-door maze task with 90%+ success rate
- [ ] Generalizes to novel maze layouts without retraining
- [ ] Shows noisy-input degradation curve (not binary failure)
- [ ] Achieves >50% transfer learning improvement on second maze
- [ ] Benchmarks runnable by outsiders in <5 minutes
- [ ] No pytest warnings, clear module boundaries
