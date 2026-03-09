# Canon Specification Index

This document indexes the canonical specifications for the GMI/GMOS system.

---

## GM-OS Canon Spec v1

**Canonical ID:** `gmos.substrate.v1`  
**Version:** 1.0.0

GM-OS (Governed Manifold Operating Substrate) is the operating substrate that hosts lawful processes under Coh governance.

### Key Components
- **Full State**: ξ = (x_ext, s, m, b, p, k, ℓ)
- **Continuous Dynamics**: Moreau-projected ξ̇(t) ∈ F(ξ) - N_K(ξ)
- **Budget System**: Protected channels with reserve floors
- **Kernel**: Deterministic step operator with receipt certification
- **Verification**: Boundary-hash verifier with chain closure

### Files
- [`docs/gmos_canon_spec.md`](gmos_canon_spec.md) - Full specification

---

## GMI Canon Spec v1

**Canonical ID:** `gmi.hosted_intelligence.v1`  
**Version:** 1.0.0

GMI (Governed Manifold Intelligence) is the hosted intelligence process inside GM-OS.

### Key Components
- **Local State**: x = (z, m, s, g, c, b, ℓ)
- **Tension Law**: V_GMI with 8 residual components
- **Policy**: Proposal generation π
- **Branching**: Branch evaluation with efficiency scoring
- **Repair Mode**: Stricter descent requirements

### Files
- [`docs/gmi_canon_spec.md`](gmi_canon_spec.md) - Full specification

---

## Architecture Layers

```
Coh (Universal Law Layer)
    ↓
Coh_oplax (Discrete Thermodynamic Realization)
    ↓
GMOS (Operating Substrate)
    ↓
GMI (Hosted Intelligence Process)
```

---

## Quick Reference

| Concept | GM-OS | GMI |
|---------|-------|-----|
| State | ξ = (x_ext,s,m,b,p,k,ℓ) | x = (z,m,s,g,c,b,ℓ) |
| Potential | V_GMOS | V_GMI |
| Verifier | RV_GMOS | RV_GMI |
| Budget | Substrate channels | Local channels |
| Modes | observe, repair, plan, act... | observe, infer, repair, plan... |
| Action | Kernel-mediated commit | χ operator → kernel |

---

## Implementation Files

### GM-OS Kernel
- [`gmos/src/gmos/kernel/substrate_state.py`](gmos/src/gmos/kernel/substrate_state.py) - Full state
- [`gmos/src/gmos/kernel/continuous_dynamics.py`](gmos/src/gmos/kernel/continuous_dynamics.py) - Dynamics
- [`gmos/src/gmos/kernel/budget_router.py`](gmos/src/gmos/kernel/budget_router.py) - Budget
- [`gmos/src/gmos/kernel/verifier.py`](gmos/src/gmos/kernel/verifier.py) - Verification
- [`gmos/src/gmos/kernel/theorems.py`](gmos/src/gmos/kernel/theorems.py) - Theorems

### GMI Agent
- [`gmos/src/gmos/agents/gmi/state.py`](gmos/src/gmos/agents/gmi/state.py) - State
- [`gmos/src/gmos/agents/gmi/tension_law.py`](gmos/src/gmos/agents/gmi/tension_law.py) - Tension law
- [`gmos/src/gmos/agents/gmi/affective_budget.py`](gmos/src/gmos/agents/gmi/affective_budget.py) - Budget
- [`gmos/src/gmos/agents/gmi/policy_selection.py`](gmos/src/gmos/agents/gmi/policy_selection.py) - Policy
- [`gmos/src/gmos/agents/gmi/execution_loop.py`](gmos/src/gmos/agents/gmi/execution_loop.py) - Execution

### Sensory & Memory
- [`gmos/src/gmos/sensory/anchors.py`](gmos/src/gmos/sensory/anchors.py) - Anchor authority
- [`gmos/src/gmos/sensory/manifold.py`](gmos/src/gmos/sensory/manifold.py) - Sensory manifold
- [`gmos/src/gmos/memory/`](gmos/src/gmos/memory/) - Memory fabric
