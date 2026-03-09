# GMI Canon Specification v1

## Overview

GMI (Governed Manifold Intelligence) is a hosted reflective intelligence process inside GM-OS, operating under Coh governance.

**Canonical ID:** `gmi.hosted_intelligence.v1`  
**Version:** `1.0.0`  
**Layer:** L3–L5 (Hosted intelligence law, internal cognition dynamics, planning/branching, action commitment)

---

## 0. Purpose

GMI is **not** the universal governance law. GMI is **not** the operating substrate. GMI is the **intelligence payload** hosted within GM-OS.

Its role is to:
1. Maintain an internal model
2. Compare sensory evidence against goals, memory, and consistency
3. Generate and evaluate internal branches
4. Choose lawful updates under finite budget
5. Emit action proposals
6. Commit externally only through kernel-certified pathways

---

## 1. State Space

### Full Local State

```
x = (z, m, s, g, c, b, ℓ) ∈ X_GMI
```

Where:
- `z`: Latent/intensional state
- `m`: Local memory slice
- `s`: Current sensory evidence view
- `g`: Active goals / tasks
- `c`: Internal consistency / contract state
- `b`: Local budget bundle
- `ℓ`: Local boundary/ledger state

### Internal State Decomposition

```
z = (z_world, z_self, z_plan, z_act, z_meta)
```

Where:
- `z_world`: World-model state
- `z_self`: Self-state / capability estimate
- `z_plan`: Current plan graph state
- `z_act`: Pending action state
- `z_meta`: Reflective / monitoring state

See: [`gmos/src/gmos/agents/gmi/state.py`](gmos/src/gmos/agents/gmi/state.py)

---

## 2. Memory Interface

GMI accesses memory through kernel-mediated view:

```
M = M_C^(I) ⊕ M_E^(I) ⊕ M_W^(I)
```

- `M_C^(I)`: Structural memory slice
- `M_E^(I)`: Episodic recall slice
- `M_W^(I)`: Active workspace slice

See: [`gmos/src/gmos/memory/`](gmos/src/gmos/memory/)

---

## 3. Goal Structure

Each goal has:
- goal_id, type, priority weight (w_j > 0)
- deadline or horizon class
- success predicate
- revocation flag
- required authority class
- acceptable defect tolerance

See: [`gmos/src/gmos/agents/gmi/tension_law.py:GoalState`](gmos/src/gmos/agents/gmi/tension_law.py)

---

## 4. Consistency State

Encodes:
- Contradiction set
- Unresolved ambiguity set
- Violated internal commitments
- Stale inference burden

See: [`gmos/src/gmos/agents/gmi/tension_law.py:ConsistencyMetrics`](gmos/src/gmos/agents/gmi/tension_law.py)

---

## 5. Tension Law

The GMI tension law is:

```
V_GMI(x) = λ_p V_percept + λ_m V_memory + λ_g V_goal + λ_c V_cons + λ_a V_action + λ_r V_resource + λ_q V_meta
```

### Residual Components

| Component | Formula | Purpose |
|-----------|---------|---------|
| V_percept | d_obs(ŝ(z,m), s)² + Σω_u | Perceptual error |
| V_memory | d_M(Π_M(z), m)² + frag(m) | Memory coherence |
| V_goal | Σ w_j δ_j(z, g_j)² | Goal distance |
| V_cons | Σ α_i 1_contradiction + β_j 1_assumption | Consistency burden |
| V_action | Σ (α_u R_ext + β_u R_auth + γ_u R_irrev) | Action risk |
| V_resource | Σ κ_i / (b_i - b_reserve) | Budget barrier |
| V_meta | η₁ osc + η₂ uncertainty + η₃ V_cons | Meta-stability |

See: [`gmos/src/gmos/agents/gmi/tension_law.py:GMITensionLaw`](gmos/src/gmos/agents/gmi/tension_law.py)

---

## 6. Budget Bundle

Local GMI budget channels:
- `b_infer`: Inference/update budget
- `b_mem`: Memory access budget
- `b_branch`: Branch/reflection budget
- `b_plan`: Plan refinement budget
- `b_act`: Action preparation budget
- `b_repair`: Contradiction-repair budget
- `b_safety`: Hard safety reserve

See: [`gmos/src/gmos/agents/gmi/affective_budget.py`](gmos/src/gmos/agents/gmi/affective_budget.py)

---

## 7. Policy Operator

Proposal generation: π: Z × M × S × G × C × B → P(U)

Generates candidates for:
- Perceptual reinterpretation
- Memory retrieval
- Contradiction repair
- Goal reprioritization
- Branch expansion
- Plan revision
- Action preparation

See: [`gmos/src/gmos/agents/gmi/policy_selection.py`](gmos/src/gmos/agents/gmi/policy_selection.py)

---

## 8. Branching

### Branch Operator

ρ: Z × M × S × G × C → Λ

Each branch λ_j carries:
- Latent update proposal
- Memory usage plan
- Expected goal effect
- Expected spend vector
- Expected defect bound

### Branch Score

```
η(λ_j) = Δ⁻V_GMI(λ_j) / (Σ_branch(λ_j) + ε)
```

See: [`gmos/src/gmos/agents/gmi/tension_law.py:Branch`](gmos/src/gmos/agents/gmi/tension_law.py)

---

## 9. Repair Regime

In repair mode:
- Only contradiction resolution, memory reconciliation, plan pruning
- No external action commit
- Strict descent: V_GMI(x') ≤ V_GMI(x)

See: [`gmos/src/gmos/agents/gmi/tension_law.py:RepairModeTensionLaw`](gmos/src/gmos/agents/gmi/tension_law.py)

---

## 10. Action Preparation

Action preparation operator: χ: Z × M × S × G × C × B → P(U_act)

Each action carries:
- Action class, intended effect
- Required authority class
- Estimated spend vector
- Irreversibility class
- Rollback availability

See: [`gmos/src/gmos/agents/gmi/execution_loop.py`](gmos/src/gmos/agents/gmi/execution_loop.py)

---

## 11. External Commitment

GMI cannot directly mutate the external world. Every external effect must pass through GM-OS kernel:

```
GMI proposes → GM-OS kernel validates → External commit
```

This is the firebreak between cognition and uncontrolled actuation.

---

## 12. Core Theorems

### Theorem 27.1: Forward Invariance
Trajectories stay in admissible set K.

### Theorem 27.2: Local Soundness
V' + Spend ≤ V + Defect for all accepted steps.

### Theorem 27.3: Budget Reserve Preservation
Protected channels cannot go below reserve.

### Theorem 27.4: Branch Finiteness
Finite branch budget → finite branch evaluation.

### Theorem 27.5: Repair Descent
Repair mode → non-increasing tension.

### Theorem 27.6: Anchor Respect
Lower-authority claims cannot override anchor dominance.

### Theorem 27.7: Kernel-Mediated Action
No direct external mutation.

### Theorem 27.8: Deterministic Consensus
Equal inputs → equal verifier decisions.

See: [`gmos/src/gmos/kernel/theorems.py`](gmos/src/gmos/kernel/theorems.py)

---

## 13. Operational Modes

| Mode | Description |
|------|-------------|
| `observe` | Perception and anchor updating |
| `infer` | Model update and memory retrieval |
| `repair` | Contradiction reduction |
| `plan` | Branching and scenario evaluation |
| `prepare_act` | Action preparation only |
| `safe_hold` | Maintain coherence, no escalation |

---

## 14. File Reference

| Component | File |
|-----------|------|
| State | [`agents/gmi/state.py`](gmos/src/gmos/agents/gmi/state.py) |
| Tension Law | [`agents/gmi/tension_law.py`](gmos/src/gmos/agents/gmi/tension_law.py) |
| Budget | [`agents/gmi/affective_budget.py`](gmos/src/gmos/agents/gmi/affective_budget.py) |
| Policy | [`agents/gmi/policy_selection.py`](gmos/src/gmos/agents/gmi/policy_selection.py) |
| Evolution | [`agents/gmi/evolution_loop.py`](gmos/src/gmos/agents/gmi/evolution_loop.py) |
| Execution | [`agents/gmi/execution_loop.py`](gmos/src/gmos/agents/gmi/execution_loop.py) |
| Constraints | [`agents/gmi/constraints.py`](gmos/src/gmos/agents/gmi/constraints.py) |
| Anchors | [`sensory/anchors.py`](gmos/src/gmos/sensory/anchors.py) |

---

## 15. Stack Relationship

```
Coh ⊃ Coh_oplax ⊃ GMOS ⊃ GMI
```

- **Coh**: Universal law layer (X, V, RV)
- **Coh_oplax**: Discrete thermodynamic realization
- **GMOS**: Operating substrate
- **GMI**: Hosted intelligence process
