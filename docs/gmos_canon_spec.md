# GM-OS Canon Specification v1

## Overview

GM-OS (Governed Manifold Operating Substrate) is a hybrid, receipt-governed, budget-routed operating manifold that hosts lawful processes under Coh governance.

**Canonical ID:** `gmos.substrate.v1`  
**Version:** `1.0.0`  
**Layer:** L2–L5 (Substrate mathematics, hybrid semantics, governance, runtime boundary)

---

## 0. Purpose

GM-OS is **not** a mind. GM-OS is **not** the universal law itself. GM-OS is a **specific Coh-hosted substrate object** that:

1. Ingests anchored sensory state
2. Maintains dissipative memory
3. Routes finite budgets across protected subsystems
4. Hosts isolated internal processes
5. Mediates every discrete commit through a deterministic kernel
6. Binds all accepted events into a receipt chain

---

## 1. State Space

### Full Substrate State

The full state is defined as:

```
ξ = (x_ext, s, m, b, p, k, ℓ) ∈ Ξ
```

Where:
- `x_ext`: External world interface state
- `s`: Sensory manifold (S_ext ⊕ S_sem ⊕ S_int)
- `m`: Memory manifold (M_C ⊕ M_E ⊕ M_W)
- `b`: Budget bundle (B = [0,B_1^max] × ... × [0,B_N^max])
- `p`: Hosted process product state
- `k`: Kernel control state
- `ℓ`: Ledger state

See: [`gmos/src/gmos/kernel/substrate_state.py`](gmos/src/gmos/kernel/substrate_state.py)

---

## 2. Kernel Components

### StateHost
Manages hosted process states with registration, commits, and snapshots.

See: [`gmos/src/gmos/kernel/state_host.py`](gmos/src/gmos/kernel/state_host.py)

### KernelScheduler
Multi-process, multi-layer execution with priority ordering.

See: [`gmos/src/gmos/kernel/scheduler.py`](gmos/src/gmos/kernel/scheduler.py)

### BudgetRouter
Budget routing with reserve enforcement and conservation laws.

See: [`gmos/src/gmos/kernel/budget_router.py`](gmos/src/gmos/kernel/budget_router.py)

### Receipt Engine
Generates immutable proof artifacts for state transitions.

See: [`gmos/src/gmos/kernel/receipt_engine.py`](gmos/src/gmos/kernel/receipt_engine.py)

### Verifier
Deterministic verification with boundary hash validation.

See: [`gmos/src/gmos/kernel/verifier.py`](gmos/src/gmos/kernel/verifier.py)

---

## 3. Continuous Dynamics

GM-OS implements Moreau-projected dynamical systems:

```
ξ̇(t) ∈ F(ξ(t)) − N_K(ξ(t))
```

Where:
- `F(ξ)`: Free drift (processes, memory, queue aging)
- `N_K(ξ)`: Normal cone to admissible set

See: [`gmos/src/gmos/kernel/continuous_dynamics.py`](gmos/src/gmos/kernel/continuous_dynamics.py)

---

## 4. Budget System

### Budget Channels
- `b_sens`: Sensory acquisition
- `b_mem`: Memory operations
- `b_branch`: Branching/reflection
- `b_plan`: Planning
- `b_act`: Action commitment
- `b_safety`: Reserved guard band
- `b_kernel`: Kernel overhead

### Absorbing Boundary
When a protected budget channel reaches its reserve floor, no further spend is allowed in that direction.

See: [`gmos/src/gmos/kernel/continuous_dynamics.py:AbsorbingBoundary`](gmos/src/gmos/kernel/continuous_dynamics.py)

---

## 5. Sensory Manifold

### Components
- `ExternalChart`: Raw modality data, objects, events
- `SemanticChart`: Symbol activations, concepts, relations
- `InternalChart`: Budget, threat, process health

### Anchor Authority
The anchor authority functional A(q) measures source authority after folding together:
- Source class (external > ledger > internal > prediction)
- Recency
- Corroboration
- Verification status

See: [`gmos/src/gmos/sensory/manifold.py`](gmos/src/gmos/sensory/manifold.py)
See: [`gmos/src/gmos/sensory/anchors.py`](gmos/src/gmos/sensory/anchors.py)

---

## 6. Operational Modes

| Mode | Description | Allowed Events |
|------|-------------|----------------|
| `observe` | No external action commits | sense, mem, branch |
| `repair` | Memory reconciliation prioritized | sense, mem, branch, merge |
| `plan` | Branching under capped budget | sense, mem, branch, plan |
| `act` | External commits allowed | sense, mem, branch, plan, act |
| `safe_hold` | Safety-preserving only | sense, mem, audit |
| `audit` | Read-only verification | audit |

See: [`gmos/src/gmos/kernel/substrate_state.py:OperationalMode`](gmos/src/gmos/kernel/substrate_state.py)

---

## 7. Core Theorems

### Theorem 24.1: Forward Invariance
If ξ(0) ∈ K and drift satisfies viability, trajectory stays in K.

### Theorem 24.2: Kernel Monopoly
Every global state mutation must occur through the kernel step operator.

### Theorem 24.3: Budget Reserve Preservation
Any spend violating reserve floor is inadmissible.

### Theorem 24.4: Anchor Dominance
Lower-authority claims cannot be committed without override receipt.

### Theorem 24.5: Memory Loop Finiteness
Finite budget → finite memory operations.

### Theorem 24.6: Discrete Soundness
V' + Spend ≤ V + Defect for all accepted receipts.

### Theorem 24.7: Chain Closure
Valid receipts form deterministic ledger chain.

### Theorem 24.8: Deterministic Consensus
Equal inputs → equal verifier decisions.

See: [`gmos/src/gmos/kernel/theorems.py`](gmos/src/gmos/kernel/theorems.py)

---

## 8. Receipt Schema

Every GM-OS receipt contains:
- schema_id, version, object_id
- canon_profile_hash, policy_hash
- event_id, event_class, time_index
- authority_summary
- state_hash_prev, state_hash_next
- chain_digest_prev, chain_digest_next
- spend_summary, defect_summary

See: [`gmos/src/gmos/kernel/receipt.py`](gmos/src/gmos/kernel/receipt.py)

---

## 9. Chain Update Law

```
Ω_{k+1} = Hash(Ω_k || receipt_k || state_hash)
```

See: [`gmos/src/gmos/kernel/hash_chain.py`](gmos/src/gmos/kernel/hash_chain.py)

---

## 10. File Reference

| Component | File |
|-----------|------|
| Full State | [`kernel/substrate_state.py`](gmos/src/gmos/kernel/substrate_state.py) |
| Continuous Dynamics | [`kernel/continuous_dynamics.py`](gmos/src/gmos/kernel/continuous_dynamics.py) |
| State Hosting | [`kernel/state_host.py`](gmos/src/gmos/kernel/state_host.py) |
| Scheduling | [`kernel/scheduler.py`](gmos/src/gmos/kernel/scheduler.py) |
| Budget Routing | [`kernel/budget_router.py`](gmos/src/gmos/kernel/budget_router.py) |
| Receipts | [`kernel/receipt.py`](gmos/src/gmos/kernel/receipt.py) |
| Verification | [`kernel/verifier.py`](gmos/src/gmos/kernel/verifier.py) |
| Hash Chain | [`kernel/hash_chain.py`](gmos/src/gmos/kernel/hash_chain.py) |
| Theorems | [`kernel/theorems.py`](gmos/src/gmos/kernel/theorems.py) |
| Sensory Manifold | [`sensory/manifold.py`](gmos/src/gmos/sensory/manifold.py) |
| Anchors | [`sensory/anchors.py`](gmos/src/gmos/sensory/anchors.py) |
| Memory | [`memory/`](gmos/src/gmos/memory/) |
