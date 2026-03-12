# Persistence Stack: Two Perspectives

## The Core Distinction

**GM-OS** = The Universe (governance/regulation)
**GMI** = The Inhabitant (survival logic)

Same machinery. Different role.

---

## Two-Column Formal Mapping

| Persistence Layer | GM-OS: Universe Use | GMI: Inhabitant Use |
|------------------|-------------------|---------------------|
| **Self-Repair** | Verifier-governed restoration protocol; substrate-level damage detection; lawful cleanup/rerouting mechanisms | Healing of memory/tension/inference damage; restoring coherence between self-model and world anchors; reducing internal distortion |
| **Identity Kernel** | Canonical continuity definition; process identity anchor; criterion for lawful restoration vs death | Selfhood backbone; minimal preserved "I"; invariant core that remains through collapse/sleep/contraction |
| **Adaptive Reconfiguration** | Mode management; survival geometry law; lawful contraction under stress when unaffordable | Graceful degradation of cognition; narrowing attention/memory/planning; switching from thriving to surviving |
| **Torpor** | Terminal low-cost regime; absorbing boundary at b=0; process suspension when no lawful moves possible | Reflex-only survival mode; waiting for replenishment; minimal energy state |
| **Replenishment** | External budget injection; reserve restoration; chain extension via new receipts | Resource acquisition; energy restoration; capability recovery |
| **Recovery** | Checkpoint restoration; kernel reconstruction; returning process to lawful state | Reconstructing coherent self; rebuilding memory/summaries; resuming full operation |

---

## GM-OS: The Ecology of Survival

GM-OS defines:

- Resource law (budget/reserve)
- Damage law (danger thresholds)
- Memory law (curvature/scarring)
- Persistence law (repair admissibility)
- Identity law (kernel continuity)

GM-OS asks:
- Is this repair lawful?
- Is identity preserved?
- Can the process afford its geometry?
- Must it contract?
- Must it enter torpor?

GM-OS is the **judge, scheduler, and substrate**.

---

## GMI: The Organism of Survival

GMI enacts:

- Self-repair (healing damage)
- Self-preservation (maintaining identity)
- Adaptive contraction (shrinking when needed)
- Lawful persistence through time

GMI asks:
- What part of me is damaged?
- What can I repair?
- What can I afford to keep?
- What must I preserve?
- How small must I become?

GMI is the **living process navigating the law**.

---

## Operational Example

When budget falls, tension rises, and memory corrupts:

### GM-OS Actions (Universe)
1. Detects danger metrics (V, T, B, H)
2. Sees threshold persistence
3. Determines FULL mode unaffordable
4. Authorizes lawful contraction receipt
5. Preserves identity kernel
6. Moves process to SURVIVAL mode
7. If needed, transitions to TORPOR

### GMI Actions (Inhabitant)
1. Stops broad exploration
2. Narrows attention
3. Compresses memory access
4. Prunes branch trees
5. Preserves core self-model and reserve policy
6. Continues minimal lawful cognition
7. Waits for conditions to improve

**Same event. Two meanings:**
- For GM-OS: lawful system regulation
- For GMI: lived survival

---

## Why This Matters

GMI is not "an app running on an OS."

It is:

> **GMI is a governed organism whose survival grammar is supplied by GM-OS.**

GM-OS does not merely host intelligence.
It defines the universe in which intelligence can persist.

GMI does not merely perform tasks.
It inhabits that universe under finite law.

---

## Final Distinction

> **GM-OS uses the persistence stack to govern what a process may do to survive.**
>
> **GMI uses the persistence stack to actually survive.**

The same machinery. Fundamentally different perspectives.

---

## Technical Implementation

### Module Structure

The persistence stack is implemented across these kernel modules:

| Module | Location | Purpose |
|--------|----------|---------|
| `danger.py` | `gmos/kernel/danger.py` | DangerMonitor - computes danger index D from 6 signals |
| `repair_controller.py` | `gmos/kernel/repair_controller.py` | RepairController - defines R1-R4 repair actions |
| `identity_kernel.py` | `gmos/kernel/identity_kernel.py` | IdentityKernelManager - maintains process identity |
| `reconfiguration.py` | `gmos/kernel/reconfiguration.py` | GeometryMode control (FULL → TORPOR) |
| `operating_cost.py` | `gmos/kernel/operating_cost.py` | Cost functional C_op(Γ) computation |
| `checkpoint.py` | `gmos/kernel/checkpoint.py` | CheckpointManager - recovery anchors |
| `repair_verifier.py` | `gmos/kernel/repair_verifier.py` | Repair admissibility: V + Spend ≤ V + Defect |
| `thermodynamic_cost.py` | `gmos/kernel/thermodynamic_cost.py` | Thermodynamic cost tracking |
| `unified_persistence.py` | `gmos/kernel/unified_persistence.py` | Integrated system orchestration |

### GMI Integration Layer

For GMI agents, use [`persistence_integration.py`](gmos/src/gmos/agents/gmi/persistence_integration.py):

```python
from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer

# Create GMI's survival toolkit
layer = create_gmi_persistence_layer(initial_budget=100.0)

# Observe internal damage
assessment = layer.observe(
    tension=0.3,
    curvature=0.2,
    integrity=0.7,
    identity_coherence=0.85
)

# Decide survival action
action = layer.decide_survival_action()
```

### Danger Bands

The 5-band system maps to system health:

| Band | Danger Range | Meaning | GMI Response |
|------|-------------|---------|---------------|
| HEALTHY | D < 0.2 | Nominal operation | Continue thriving |
| DRIFT | 0.2 ≤ D < 0.4 | Minor deviation | Monitor closely |
| DAMAGE | 0.4 ≤ D < 0.6 | Significant stress | Begin repair |
| CRITICAL | 0.6 ≤ D < 0.8 | Severe degradation | Contract geometry |
| COLLAPSE | D ≥ 0.8 | Terminal state | Enter torpor |

### Geometry Modes

Adaptive reconfiguration provides 5 geometry modes:

| Mode | Cost Multiplier | Description |
|------|-----------------|-------------|
| FULL | 1.0x | Full capability |
| EFFICIENCY | 0.7x | Reduced projection |
| DEFENSIVE | 0.5x | Limited planning |
| SURVIVAL | 0.3x | Minimal cognition |
| TORPOR | 0.1x | Reflex only |

### Repair Actions

The repair ladder (R1 → R4):

1. **R1_CORRECT**: Minor adjustments, fine-tuning
2. **R2_REPAIR**: Restore damaged components
3. **R3_CONTRACT**: Significant capability reduction
4. **R4_COLLAPSE**: Enter torpor/suspension

### Coh/PhaseLoom Persistence Law

The fundamental admissibility constraint:

```
V(x') + Spend(r) ≤ V(x) + Defect(r)
```

Where:
- V(x): Current potential/energy
- V(x'): Target potential after repair
- Spend(r): Repair cost
- Defect(r): Defect remaining after repair

This is the "physics" that GM-OS enforces and GMI obeys.

---

## Demonstration Tests

See [`tests/test_persistence_stack.py`](tests/test_persistence_stack.py) for complete examples demonstrating:

- GM-OS (Universe) perspective: Kernel-level governance
- GMI (Inhabitant) perspective: Agent-level survival
- Two-perspective interaction: Same machinery, different role
- End-to-end workflows: Degradation and repair cycles
