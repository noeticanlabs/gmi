# Coh, GM-OS, and GMI Canonical Doctrine

**Canonical ID:** `coh.doctrine.v1`  
**Version:** `1.0.0`  
**Status:** Canonical - Phase 1 Foundation Document

---

## 1. Purpose

This document defines the canonical doctrine governing the Coh/GM-OS/GMI system stack. It establishes the single source of truth for core concepts, architectural relationships, and the formal contract between the governance law, the operating substrate, and hosted intelligence processes.

### What the System Is

Coh/GM-OS/GMI is a governed cognitive architecture that enforces thermodynamic-style budget constraints on all computational processes. It provides a receipt-chain audit trail for every state transition and maintains strict admissibility boundaries on proposals.

- **Coh** is the universal governance law: a set of mathematical constraints that govern coherence, budget conservation, and admissible state transitions.
- **GM-OS** is the governed runtime substrate: a deterministic kernel that hosts processes, routes budgets, verifies proposals, and writes immutable receipts.
- **GMI** is the hosted intelligence process: a lawful cognitive agent that generates proposals within the constraints imposed by Coh and GM-OS.

### What the System Is Not

- **Not AGI**: The system does not claim general intelligence. It is a governed substrate with bounded rationality.
- **Not conscious**: No claim of consciousness, sentience, or phenomenal experience.
- **Not a physics engine**: While the mathematical formalism borrows from thermodynamics, this is not a physical simulation.
- **Not a multi-agent orchestration system**: Phase 1 implements a single hosted process. Multi-agent coordination is out of scope.

### Where Speculation Ends and Canon Begins

Canon is everything in this document and in the canonical specification files referenced herein. Speculation includes any feature, agent, or mathematical extension not explicitly marked as canonical. Experimental code lives in `gmos.experimental` and must not be exported as production-ready.

---

## 2. Stack Hierarchy

```
Coh (Governance Law)
    |
    v
GM-OS (Governed Runtime Substrate)
    |
    v
GMI (Hosted Intelligence Process)
```

### Coh — Governance Law

Coh defines the fundamental constraints:

1. **Coherence Functional** `V(x)`: A scalar measure of system coherence/debt
2. **Admissibility Region** `K`: The set of all states/proposals that satisfy governance constraints
3. **Reserve Law**: Budget reserves must never fall below a configurable floor
4. **Verifier Inequality**: Every proposal must satisfy `V(x_{t+1}) + σ ≤ V(x_t) + κ + r`
5. **Receipt-Chain Law**: Every meaningful transition must produce an immutable receipt

### GM-OS — Governed Runtime Substrate

GM-OS is the concrete runtime that enforces Coh:

- Maintains canonical runtime state `ξ`
- Routes budgets across protected channels with reserve floors
- Hosts isolated internal processes (e.g., GMI)
- Mediates every discrete commit through a deterministic kernel
- Binds all accepted events into an append-only receipt chain

### GMI — Hosted Intelligence Process

GMI is the intelligence payload hosted within GM-OS:

- Maintains internal model and cognitive state
- Generates proposals under budget constraints
- Evaluates proposals for coherence and admissibility
- Emits action proposals through kernel-certified pathways
- Must not directly mutate substrate outside contract

---

## 3. Primitive Objects

### State

```
x ∈ X: The full state of the system at a given step
```

### Percept

```
p ∈ P: Raw sensory input anchored into a typed perceptual record
```

### Memory Episode

```
m_e ∈ M_E: A discrete memory unit containing (timestamp, content, salience, coherence_weight)
```

### Workspace

```
w ∈ M_W: Active working memory containing current context and relevant recalled episodes
```

### Proposal

```
u ∈ U: A candidate action or state update proposed by the hosted process
```

### Action

```
a ∈ A: A committed action that has passed verification and been executed
```

### Residual

```
ρ = V(x_{t+1}) - V(x_t): The change in coherence functional between states
```

### Coherence/Debt

```
V(x): Scalar measure where higher values indicate more coherence debt (less organized state)
```

### Budget

```
b ∈ B = [0, B_1^max] × ... × [0, B_N^max]: Vector of budget allocations across channels
```

### Reserve Floor

```
r_min: Minimum budget reserve that must never be violated
```

### Verifier Result

```
v ∈ {ACCEPT, REPAIR, REJECT}: The result of evaluating a proposal against admissibility
```

### Receipt

```
ℓ: Immutable record containing (step, proposal_id, spend, defect, verdict, repair_notes, state_hash, memory_refs, percept_refs)
```

### Repair

```
π(u): A projection operator that modifies a proposal to satisfy admissibility
```

### Rejection

```
⊥: The null action when a proposal cannot be repaired or is outright rejected
```

---

## 4. Governing Laws

### 4.1 Coherence Functional / Residual Law

The coherence functional `V: X → ℝ` maps any state to a scalar representing coherence debt. The residual is:

```
ρ = V(x_{t+1}) - V(x_t)
```

A proposal is coherent if it reduces or maintains coherence debt.

### 4.2 Admissibility Law

A proposal `u` is admissible if the resulting state `x' = T(x, u)` satisfies:

```
x' ∈ K  (where K is the admissible region)
```

The admissible region is defined by budget constraints, reserve floors, and coherence thresholds.

### 4.3 Reserve Law

For every budget channel `i`:

```
b_i ≥ r_min_i
```

If a proposal would violate the reserve floor, it must be repaired or rejected.

### 4.4 Verifier Inequality

Every proposal must satisfy:

```
V(x_{t+1}) + σ ≤ V(x_t) + κ + r
```

Where:
- `σ`: spend (budget consumption)
- `κ`: defect tolerance (allowed incoherence)
- `r`: reserve slack (available reserve)

### 4.5 Repair/Reject Semantics

If a proposal fails verification:

1. **Repair** (`REPAIR`): Apply projection operator `π(u)` to produce a modified proposal that satisfies constraints
2. **Reject** (`REJECT`): If repair is impossible or would lose essential information, reject and emit `⊥`

### 4.6 Receipt-Chain Law

Every meaningful transition must produce a receipt:

```
ℓ_t = L(x_t, p_t, m_t, û_t, A_t, b_t)
```

Receipts are append-only and cryptographically chainable.

---

## 5. Runtime Transition Loop

The canonical step sequence executed by GM-OS:

```
1. OBSERVE     : Receive raw input
2. ANCHOR      : Convert raw input to typed percept p_t
3. RETRIEVE   : Fetch relevant memory m_t from archive/workspace
4. PROPOSE    : Hosted process generates candidate proposal u_t
5. EVALUATE   : Compute residual, budget impact, admissibility
6. VERIFY     : Check verifier inequality V(x_{t+1}) + σ ≤ V(x_t) + κ + r
7. REPAIR/REJECT: If failed, attempt repair or reject
8. COMMIT     : If verified, execute action a_t = û_t
9. RECEIPT    : Write immutable receipt ℓ_t
10. UPDATE     : Update state x_{t+1}, memory, and budget b_{t+1}
```

---

## 6. Canonical Boundaries

### Canon (Production-Ready)

- `gmos.kernel.*` - Core substrate runtime
- `gmos.memory.*` - Canonical memory management
- `gmos.sensory.*` - Percept anchoring
- `gmos.action.*` - Action commitment
- `gmos.agents.gmi.*` - Canonical hosted intelligence
- All documents in `docs/` tagged as "canonical"

### Extension (Allowed, Non-Canonical)

- `gmos.symbolic.*` - Symbolic reasoning extensions
- Additional domain-specific agents

### Speculation (Doc-Only, Not Implemented)

- Multi-agent orchestration protocols
- Learned proposal networks
- Consciousness or organism shell models

### Archive/Deprecated

- Legacy code in root directories (`core/`, `memory/`, `runtime/`, `ledger/`)
- Stub agents (`agents/ns_agent.py`, `agents/physics_agent.py`, etc.)

---

## 7. Minimal Executable Contract

The smallest lawful end-to-end loop that must run in code:

```
Given:
  - Initial state x_0
  - Percept p_0
  - Memory m_0
  - Budget b_0

Execute:
  1. Anchor percept: p = anchor(raw_input)
  2. Retrieve memory: m = retrieve(p, workspace)
  3. Form proposal: u = propose(x, m, p)
  4. Compute spend: σ = spend(u)
  5. Compute verifier: v = verify(x, u, b)
  6. If v == ACCEPT:
       commit u
       write receipt
       update state
     Else if v == REPAIR:
       u' = repair(u)
       commit u' or reject
     Else:
       reject

Return:
  - Final state x'
  - Receipt ℓ
  - Verdict v
```

---

## 8. Non-Goals for Phase 1

The following are explicitly NOT Phase 1 objectives:

- Building AGI or general intelligence
- Proving physics unification
- Shipping multi-agent orchestration
- Claiming consciousness or sentience
- Implementing learned proposal networks
- Building tool-use ecosystems
- Speculative physics bridges as load-bearing code
- Organism shells as canonical runtime components

Phase 1 is about establishing the governed substrate and stable contracts. Intelligence capability comes later.

---

## References

- [`gmos_canon_spec.md`](gmos_canon_spec.md) - GM-OS canonical specification
- [`gmi_canon_spec.md`](gmi_canon_spec.md) - GMI canonical specification
- [`canon_spec_index.md`](canon_spec_index.md) - Specification index
- [`repo_status_matrix.md`](repo_status_matrix.md) - Implementation status

---

*This document is canonical. Any change to this doctrine requires Phase 1 completion and explicit labeling as a breaking change.*
