# Definition Ledger

**Canonical ID:** `coh.definition_ledger.v1`  
**Version:** `1.0.0`  
**Status:** Canonical - Phase 1 Foundation Document

This document pins all slippery terms to the wall. Each entry has a canonical definition, type, allowed aliases, forbidden overloaded meanings, used in modules, and status.

---

## Core Terms

### Coh

| Field | Value |
|-------|-------|
| **Term** | Coh |
| **Canonical Definition** | The universal governance law: a set of mathematical constraints that govern coherence, budget conservation, and admissible state transitions. Coh defines V(x), K, and the verifier inequality. |
| **Type** | Governance Law (Abstract) |
| **Allowed Aliases** | Coherence, Governance Law, Cohesion Law |
| **Forbidden Meanings** | - Not a specific software module<br>- Not "consciousness"<br>- Not "the system" as a whole |
| **Used In** | `gmos.kernel.*`, `gmos.agents.gmi.*`, docs |
| **Status** | Canonical |

---

### Coherence

| Field | Value |
|-------|-------|
| **Term** | Coherence |
| **Canonical Definition** | A scalar property of system state. Higher coherence = lower V(x). Represents organizational integrity, consistency, and bounded entropy. |
| **Type** | State Property (Scalar ℝ) |
| **Allowed Aliases** | V(x), Coherence Functional, Potential |
| **Forbidden Meanings** | - Not "logical consistency" alone<br>- Not "conscious awareness"<br>- Not "quantum coherence" |
| **Used In** | `gmos.kernel.verifier`, `gmos.kernel.cohil_evaluator`, `gmos.agents.gmi.tension_law` |
| **Status** | Canonical |

---

### Debt

| Field | Value |
|-------|-------|
| **Term** | Debt |
| **Canonical Definition** | Inverse of coherence. Debt = V(x). Higher debt means more incoherence/entropy must be "paid off" to restore coherence. |
| **Type** | State Property (Scalar ℝ) |
| **Allowed Aliases** | Incoherence, Entropy Debt, Coherence Debt |
| **Forbidden Meanings** | - Not monetary debt<br>- Not "cognitive debt" metaphor |
| **Used In** | `gmos.kernel.cohil_evaluator`, `gmos.kernel.thermodynamic_cost` |
| **Status** | Canonical |

---

### Residual

| Field | Value |
|-------|-------|
| **Term** | Residual |
| **Canonical Definition** | The change in coherence functional: ρ = V(x_{t+1}) - V(x_t). A proposal that reduces residual (makes ρ negative or zero) improves coherence. |
| **Type** | Transition Property (Scalar ℝ) |
| **Allowed Aliases** | Delta-V, Coherence Change, ρ |
| **Forbidden Meanings** | - Not "error" in ML sense<br>- Not "residual" in statistical sense |
| **Used In** | `gmos.kernel.verifier`, `gmos.kernel.cohil_evaluator` |
| **Status** | Canonical |

---

### Admissibility

| Field | Value |
|-------|-------|
| **Term** | Admissibility |
| **Canonical Definition** | The property of a state or proposal being within the admissible region K. K is defined by budget constraints, reserve floors, and coherence thresholds. |
| **Type** | Constraint Property (Boolean) |
| **Allowed Aliases** | K, Admissible Region, Legal, Permissible |
| **Forbidden Meanings** | - Not "logical validity"<br>- Not "truth" |
| **Used In** | `gmos.kernel.verifier`, `gmos.kernel.continuous_dynamics` |
| **Status** | Canonical |

---

### Verifier

| Field | Value |
|-------|-------|
| **Term** | Verifier |
| **Canonical Definition** | The component that evaluates proposals against admissibility constraints. Returns ACCEPT, REPAIR, or REJECT. Checks V(x_{t+1}) + σ ≤ V(x_t) + κ + r. |
| **Type** | Kernel Component |
| **Allowed Aliases** | RV (Result Verifier), Verification Module |
| **Forbidden Meanings** | - Not a security verification system<br>- Not "proof verifier" |
| **Used In** | `gmos.kernel.verifier` |
| **Status** | Canonical |

---

### Reserve

| Field | Value |
|-------|-------|
| **Term** | Reserve |
| **Canonical Definition** | The minimum budget allocation that must remain untouched. r_min is the reserve floor. Reserve slack r = b - r_min is available for spending. |
| **Type** | Budget Property (Vector or Scalar) |
| **Allowed Aliases** | Reserve Floor, Minimum Budget, r_min |
| **Forbidden Meanings** | - Not "savings"<br>- Not "buffer" in general sense |
| **Used In** | `gmos.kernel.budget_router`, `gmos.kernel.verifier` |
| **Status** | Canonical |

---

### Spend

| Field | Value |
|-------|-------|
| **Term** | Spend |
| **Canonical Definition** | The budget consumption (σ) of a proposal. Represents computational resources, memory operations, or other metered costs. |
| **Type** | Budget Property (Scalar) |
| **Allowed Aliases** | σ, Cost, Resource Consumption |
| **Forbidden Meanings** | - Not monetary spend<br>- Not "time" alone |
| **Used In** | `gmos.kernel.budget_router`, `gmos.kernel.operating_cost` |
| **Status** | Canonical |

---

### Defect

| Field | Value |
|-------|-------|
| **Term** | Defect |
| **Canonical Definition** | The incoherence introduced (κ) by a proposal. Defect tolerance is the allowed incoherence budget. |
| **Type** | Budget Property (Scalar) |
| **Allowed Aliases** | κ, Incoherence Allowance, Defect Tolerance |
| **Forbidden Meanings** | - Not "bug"<br>- Not "error" |
| **Used In** | `gmos.kernel.verifier`, `gmos.kernel.cohil_evaluator` |
| **Status** | Canonical |

---

### Projection

| Field | Value |
|-------|-------|
| **Term** | Projection |
| **Canonical Definition** | An operator π(u) that modifies a proposal to satisfy admissibility. Projects from infeasible to feasible region. |
| **Type** | Operator |
| **Allowed Aliases** | π, Repair Projection, Moreau Projection |
| **Forbidden Meanings** | - Not "map projection"<br>- Not "ML embedding" |
| **Used In** | `gmos.kernel.repair_controller`, `gmos.kernel.continuous_dynamics` |
| **Status** | Canonical |

---

### Repair

| Field | Value |
|-------|-------|
| **Term** | Repair |
| **Canonical Definition** | The process of applying projection to a proposal that failed verification. Produces a modified proposal that satisfies constraints. |
| **Type** | Process |
| **Allowed Aliases** | π(u), Projection, Fix |
| **Forbidden Meanings** | - Not "debugging"<br>- Not "self-healing" |
| **Used In** | `gmos.kernel.repair_controller`, `gmos.kernel.repair_verifier` |
| **Status** | Canonical |

---

### Receipt

| Field | Value |
|-------|-------|
| **Term** | Receipt |
| **Canonical Definition** | An immutable audit record ℓ containing (step, proposal_id, spend, defect, verdict, repair_notes, state_hash, memory_refs, percept_refs). Append-only. |
| **Type** | Ledger Record |
| **Allowed Aliases** | ℓ, Audit Record, Transaction Record |
| **Forbidden Meanings** | - Not "financial receipt"<br>- Not "debug log" |
| **Used In** | `gmos.kernel.receipt`, `gmos.kernel.receipt_engine`, `gmos.memory.receipts` |
| **Status** | Canonical |

---

### Memory Episode

| Field | Value |
|-------|-------|
| **Term** | Memory Episode |
| **Canonical Definition** | A discrete memory unit m_e containing (timestamp, content, salience, coherence_weight). The episodic archive stores these. |
| **Type** | Data Structure |
| **Allowed Aliases** | m_e, Episode, Memory Unit |
| **Forbidden Meanings** | - Not "episodic memory" in psychology sense<br>- Not "experience replay" in ML sense |
| **Used In** | `gmos.memory.episode`, `gmos.memory.archive`, `gmos.memory.replay` |
| **Status** | Canonical |

---

### Sensory Anchor

| Field | Value |
|-------|-------|
| **Term** | Sensory Anchor |
| **Canonical Definition** | The process of converting raw sensory input into a typed percept record. Anchors provide stable semantic binding. |
| **Type** | Process |
| **Allowed Aliases** | Anchor, Percept Binding, Sensory Binding |
| **Forbidden Meanings** | - Not "grounding"<br>- Not "reference" |
| **Used In** | `gmos.sensory.anchors`, `gmos.sensory.manifold` |
| **Status** | Canonical |

---

### Workspace

| Field | Value |
|-------|-------|
| **Term** | Workspace |
| **Canonical Definition** | Active working memory w containing current context and relevant recalled episodes. The "scratchpad" for current operations. |
| **Type** | Memory Region |
| **Allowed Aliases** | w, Working Memory, M_W |
| **Forbidden Meanings** | - Not "workspace" in OS sense<br>- Not "scratch space" |
| **Used In** | `gmos.memory.workspace` |
| **Status** | Canonical |

---

### Hosted Process

| Field | Value |
|-------|-------|
| **Term** | Hosted Process |
| **Canonical Definition** | An intelligence process (like GMI) hosted within GM-OS. Runs under kernel mediation, cannot directly mutate substrate. |
| **Type** | Runtime Entity |
| **Allowed Aliases** | Agent, GMI, Internal Process |
| **Forbidden Meanings** | - Not "container process"<br>- Not "subprocess" |
| **Used In** | `gmos.kernel.state_host`, `gmos.agents.gmi.hosted_agent` |
| **Status** | Canonical |

---

### Substrate

| Field | Value |
|-------|-------|
| **Term** | Substrate |
| **Canonical Definition** | The GM-OS runtime environment that hosts processes, manages state, budgets, and receipts. Not the hardware, but the software runtime. |
| **Type** | Runtime Environment |
| **Allowed Aliases** | GM-OS, Runtime, Kernel Environment |
| **Forbidden Meanings** | - Not "hardware"<br>- Not "computing substrate" in physics sense |
| **Used In** | `gmos.kernel.*`, docs |
| **Status** | Canonical |

---

### Policy

| Field | Value |
|-------|-------|
| **Term** | Policy |
| **Canonical Definition** | A function π that maps (state, memory, percept) to a proposal. The hosted process's proposal generation strategy. |
| **Type** | Function |
| **Allowed Aliases** | π, Proposal Generator, Strategy |
| **Forbidden Meanings** | - Not "company policy"<br>- Not "security policy" |
| **Used In** | `gmos.agents.gmi.policy_selection` |
| **Status** | Canonical |

---

### Action Commit

| Field | Value |
|-------|-------|
| **Term** | Action Commit |
| **Canonical Definition** | The process of executing a verified proposal. The χ operator that commits actions to the world or simulated environment through kernel mediation. |
| **Type** | Process |
| **Allowed Aliases** | Commit, Execute, χ operator |
| **Forbidden Meanings** | - Not "version commit"<br>- Not "database commit" |
| **Used In** | `gmos.action.commitment` |
| **Status** | Canonical |

---

## GM-OS Specific Terms

### GM-OS

| Field | Value |
|-------|-------|
| **Term** | GM-OS |
| **Canonical Definition** | Governed Manifold Operating Substrate. The deterministic kernel that hosts processes, routes budgets, verifies proposals, and writes immutable receipts. |
| **Type** | System Component |
| **Allowed Aliases** | Substrate, Kernel, Runtime |
| **Forbidden Meanings** | - Not "operating system"<br>- Not "OS" in traditional sense |
| **Used In** | All `gmos.kernel.*` modules |
| **Status** | Canonical |

---

### GMI

| Field | Value |
|-------|-------|
| **Term** | GMI |
| **Canonical Definition** | Governed Manifold Intelligence. The hosted intelligence process that generates proposals under Coh governance. |
| **Type** | Hosted Process |
| **Allowed Aliases** | Agent, Hosted Intelligence, GMI Agent |
| **Forbidden Meanings** | - Not "the entire system"<br>- Not "the mind" |
| **Used In** | `gmos.agents.gmi.*` |
| **Status** | Canonical |

---

### Kernel

| Field | Value |
|-------|-------|
| **Term** | Kernel |
| **Canonical Definition** | The deterministic core of GM-OS that mediates all state transitions, budget operations, and receipt writing. |
| **Type** | System Component |
| **Allowed Aliases** | GM-OS Kernel, Core |
| **Forbidden Meanings** | - Not "OS kernel"<br>- Not "GPU kernel" |
| **Used In** | `gmos.kernel.*` |
| **Status** | Canonical |

---

### Budget Router

| Field | Value |
|-------|-------|
| **Term** | Budget Router |
| **Canonical Definition** | The component that allocates budget across protected channels (sensory, memory, planning, action) with reserve enforcement. |
| **Type** | Kernel Component |
| **Allowed Aliases** | Router, Budget Manager |
| **Forbidden Meanings** | - Not "network router"<br>- Not "packet routing" |
| **Used In** | `gmos.kernel.budget_router` |
| **Status** | Canonical |

---

### Operational Mode

| Field | Value |
|-------|-------|
| **Term** | Operational Mode |
| **Canonical Definition** | The current phase of the execution loop: OBSERVE, ANCHOR, RETRIEVE, PROPOSE, EVALUATE, VERIFY, REPAIR/REJECT, COMMIT, RECEIPT, UPDATE. |
| **Type** | Runtime State |
| **Allowed Aliases** | Mode, Phase, Step Type |
| **Forbidden Meanings** | - Not "user mode"<br>- Not "privilege level" |
| **Used In** | `gmos.kernel.substrate_state`, `gmos.kernel.scheduler` |
| **Status** | Canonical |

---

## Status Tags

| Status | Meaning |
|--------|---------|
| **Canonical** | Production-ready, stable API, officially supported |
| **Extension** | Allowed but not core to Phase 1, may evolve |
| **Speculative** | Doc-only, not implemented, future exploration |
| **Archive** | Deprecated, kept for reference, not for production |
| **Legacy** | Old prototype code, should not be used |

---

## Usage Notes

1. **One Definition Per Term**: If a term appears in multiple places with conflicting meanings, this ledger takes precedence.
2. **Module Mapping**: Every canonical term should map to exactly one code module.
3. **Vocabulary Tests**: Automated tests should verify that no module uses a forbidden meaning.
4. **Canon Drift Prevention**: Any new term must be added to this ledger before being used in canonical code.

---

## References

- [`coh_gmos_gmi_doctrine.md`](coh_gmos_gmi_doctrine.md) - Canonical doctrine
- [`gmos_canon_spec.md`](gmos_canon_spec.md) - GM-OS specification
- [`gmi_canon_spec.md`](gmi_canon_spec.md) - GMI specification

---

*This ledger is canonical. Changes require Phase 1 completion and explicit versioning.*
