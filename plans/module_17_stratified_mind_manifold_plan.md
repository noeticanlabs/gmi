# Module 17: Stratified Mind Manifold Implementation Plan

## Overview

This plan addresses the mathematical tightening and implementation of Module 17 - the Stratified Mind Manifold architecture for the GMI system. The module implements the core insight that **minds must stratify to survive** through fast, cheap control loops under slow, expensive supervisory loops.

## Feedback Analysis Summary

The reviewer confirms that Module 17's core architecture is "correct in spirit and mostly sound structurally." The key mathematical formulations (layered direct sum, separated timescales, hierarchical budget delegation) are validated. The task is to **tighten the bolts** to make theorem claims mathematically honest.

---

## Gap Analysis: Current State vs. Required State

### Current System (Modules 1-16)

| Component | Current Implementation |
|-----------|----------------------|
| **State** | Flat `z(t) = (x(t), b(t))` in `core/state.py` |
| **Budget** | Single scalar `b(t)` with Reserve Law in `ledger/oplax_verifier.py` |
| **Operators** | Single pool of operators with affective pricing in `core/affective_budget.py` |
| **Verification** | Single-layer inequality: `V' + σ ≤ V + κ + b` |
| **Reserve** | Dynamic `b_reserve = r₀ + α·Π + β·U + γ·N` |

### Required for Module 17

| Component | Module 17 Requirement |
|-----------|----------------------|
| **State** | Stratified: `Z = (Z⁽¹⁾, ..., Z⁽ᴸ⁾)` with coupling maps |
| **Budget** | Hierarchical: `B_total = Σₗ B⁽ˡ⁾` with downward flow |
| **Operators** | Layer-restricted: Layer 1 = no branching, L≥2 = branching |
| **Verification** | Layer-specific constraints with budget transfer invariants |
| **Reserve** | Per-layer reserves with Layer 1 protected survival reserve |

---

## Implementation Components

### Component 1: Stratified State Manifold

**File**: `core/stratified_state.py` (NEW)

**Mathematical Specification**:
```
Z = (Z⁽¹⁾, ..., Z⁽ᴸ⁾)

where each layer l has:
- z⁽ˡ⁾(t) = (x⁽ˡ⁾(t), b⁽ˡ⁾(t))
- Δt⁽ˡ⁾: characteristic timescale
- Coupling maps: Φ⁽ˡ→ˡ⁻¹⁾ (budget delegation), Ψ⁽ˡ⁻¹→ˡ⁾ (information abstraction)
```

**Implementation Requirements**:
1. Define `StratifiedState` dataclass with per-layer states
2. Implement `LayerCoupling` protocol for inter-layer communication
3. Add `LayerConfig` for timescale and operator restrictions per layer

### Component 2: Hierarchical Budget Delegation

**File**: `core/hierarchical_budget.py` (NEW)

**Mathematical Specification**:
```
B_total = Σₗ B⁽ˡ⁾

Budget Flow (downward only):
B⁽ˡ⁾ → B⁽ˡ⁻¹⁾ for l > 1

Protected Survival Reserve:
B_reserve⁽¹⁾ ≥ b_min  (Layer 1 cannot be starved)

Internal Transfer Invariant (explicit):
Σₗ ΔB⁽ˡ⁾ = 0  (for internal budget transfers)
```

**Implementation Requirements**:
1. Extend `OplaxVerifier` to handle multi-layer budgets
2. Add `BudgetDelegationPool` for inter-layer transfers
3. Implement `LayerBudgetMonitor` tracking per-layer and total budgets

**Explicit Theorem Assumption (to be stated)**:
```
ASSUMPTION (Budget Transfer Energy Conservation):
For internal budget transfers between layers:
  Σₗ ΔB⁽ˡ⁾ = 0
  
This ensures budget transfers do not create or destroy energy.
```

### Component 3: Stratified Operator Access

**File**: `core/stratified_operators.py` (NEW)

**Mathematical Specification**:
```
Layer 1 (Reflex):
  O_I = ∅  (no branching allowed)
  μ⁽¹⁾: minimum operator cost

Layer l ≥ 2 (Reflective):
  O_I unrestricted
  μ⁽ˡ⁺¹⁾ ≫ μ⁽ˡ⁾  (exponential cost scaling)
```

**Implementation Requirements**:
1. Add `layer` field to `Instruction` class
2. Implement `LayerOperatorRegistry` with per-layer operator restrictions
3. Add `BranchPricing` to charge for speculative branching

**Explicit Theorem Assumption (to be stated)**:
```
ASSUMPTION (Branch Evaluation Cost):
σ_branch > 0

Branch evaluation itself consumes budget. Without this,
the system could open arbitrarily many speculative nodes.
```

### Component 4: Oplax Slab Roll-up

**File**: `ledger/slab_verifier.py` (NEW)

**Mathematical Specification**:
```
Micro-receipts at Layer 1:
  r_k⁽¹⁾ for k = 1,...,K

Slab composition:
  S_K = ⊙_k r_k⁽¹⁾  (oplax composition)

Subadditivity Law (Oplax Category):
  Spend(S_K) ≤ Σ_k Spend(r_k⁽¹⁾)
  
This justifies batch verification.
```

**Implementation Requirements**:
1. Add `Slab` dataclass for batched receipts
2. Implement `SlabVerifier` with subadditivity checks
3. Add `OplaxComposition` operator for receipt aggregation

### Component 5: Theorem 17.1 - Combinatorial Explosion Bound

**File**: `core/stratified_theorems.py` (NEW)

**Mathematical Specification**:
```
Given:
- B⁽ˡ⁾: budget for layer l
- σ_min⁽ˡ⁾: minimum branching cost at layer l
- σ_branch > 0 (explicit assumption)

Then:
  m⁽ˡ⁾ ≤ B⁽ˡ⁾ / σ_min⁽ˡ⁾
  
Where m⁽ˡ⁾ = maximum number of branches at layer l.
```

**Proof Requirements**:
1. State explicit assumption: σ_branch > 0
2. Show finite budget bounds branching
3. Show minimum cost prevents infinite speculation

### Component 6: Theorem 17.2 - Global Viability

**File**: `core/stratified_theorems.py` (NEW)

**Mathematical Specification**```
Local viability at layer l:
  V⁽ˡ⁾_{k+1} + Spend⁽ˡ⁾ ≤ V⁽ˡ⁾_k + Defect⁽ˡ⁾
  
Summing over all layers:
  V_GMI(t_{k+1}) + Σ_global ≤ V_GMI(t_k) + τ_global

With budget transfer invariant:
  Σₗ ΔB⁽ˡ⁾ = 0
```

**Proof Requirements**:
1. State explicit assumption: Σₗ ΔB⁽ˡ⁾ = 0 for internal transfers
2. Show global thermodynamic accounting preserved
3. Show budget cascade maintains viability

---

## File Structure

```
core/
├── stratified_state.py      # NEW: StratifiedState, LayerConfig
├── hierarchical_budget.py    # NEW: HierarchicalBudget, BudgetDelegation
├── stratified_operators.py  # NEW: LayerOperatorRegistry, BranchPricing
└── stratified_theorems.py    # NEW: Theorem 17.1, 17.2 proofs

ledger/
├── slab_verifier.py         # NEW: SlabVerifier, OplaxComposition

runtime/
└── stratified_execution.py # MODIFY: Adapt execution_loop for layers
```

---

## Integration Points

### 1. With Existing OplaxVerifier

The `OplaxVerifier` in `ledger/oplax_verifier.py` will be extended:
- New method: `verify_stratified(state: StratifiedState) -> VerificationResult`
- Existing `verify()` method remains for backward compatibility

### 2. With Affective Budget (Module 16)

The `AffectiveBudgetLaw` in `core/affective_budget.py` will be adapted:
- Layer-specific χ modulation
- Cross-layer affective coordination

### 3. With Execution Loop

The `runtime/execution_loop.py` will be refactored:
- Layer-by-layer execution with different Δt
- Budget delegation between layers
- Slab verification at Layer 1

---

## Mathematical Tightening Summary

| Theorem | Current State | Required Explicit Assumption |
|---------|---------------|------------------------------|
| Theorem 17.1 | Implicit σ_branch > 0 | **Add**: `ASSUMPTION: σ_branch > 0` |
| Theorem 17.2 | Implicit budget conservation | **Add**: `ASSUMPTION: Σₗ ΔB⁽ˡ⁾ = 0` |
| Layer coupling | Direct sum notation | **Refine**: Add coupling maps Φ, Ψ |
| Slab verification | Subadditivity assumed | **Prove**: From oplax category |

---

## Implementation Todo List

```
[ ] Create core/stratified_state.py
    [ ] Define StratifiedState dataclass
    [ ] Define LayerConfig with timescale and operators
    [ ] Implement LayerCoupling protocol

[ ] Create core/hierarchical_budget.py
    [ ] Define HierarchicalBudget dataclass
    [ ] Implement budget delegation logic
    [ ] Add BudgetTransferInvariant assertion

[ ] Create core/stratified_operators.py
    [ ] Add layer field to Instruction
    [ ] Implement LayerOperatorRegistry
    [ ] Add BranchPricing with σ_branch > 0

[ ] Create ledger/slab_verifier.py
    [ ] Define Slab dataclass
    [ ] Implement SlabVerifier with subadditivity
    [ ] Add OplaxComposition operator

[ ] Create core/stratified_theorems.py
    [ ] Document Theorem 17.1 with explicit assumptions
    [ ] Document Theorem 17.2 with explicit assumptions
    [ ] Add unit tests for theorem claims

[ ] Integrate with runtime/execution_loop.py
    [ ] Refactor for stratified execution
    [ ] Add budget cascade between layers
    [ ] Add slab verification at Layer 1
```

---

## Testing Strategy

### Unit Tests
- `test_stratified_state_creation`: Verify layer initialization
- `test_budget_delegation_invariant`: Verify ΣΔB = 0
- `test_layer_operator_restrictions`: Verify Layer 1 no-branching
- `test_slab_subadditivity`: Verify batch verification savings

### Integration Tests
- `test_stratified_execution_loop`: Full 3-layer execution
- `test_branching_explosion_bound`: Verify m⁽ˡ⁾ ≤ B⁽ˡ⁾/σ
- `test_global_viability`: Verify V_GMI descent maintained

---

## Notes on Scope

The reviewer correctly notes that the theorem proves:
- ✅ Hierarchical viability
- ✅ Bounded branching  
- ✅ Preserved thermodynamic descent

But does NOT yet prove:
- ❌ Distributed multi-agent stability
- ❌ Adversarial robustness
- ❌ Network-scale coordination

These would require future modules (e.g., `coh.multi_agent_governance`, `coh.network_budget_exchange`).

---

## References

- Feedback Section 1: Stratified mind manifold - direct sum → fibered hierarchy
- Feedback Section 2: Hierarchical budget delegation - downward flow, reserve
- Feedback Section 3: Stratified operator access - layer restrictions
- Feedback Section 4: Oplax slab roll-up - subadditivity justification
- Feedback Section 5: Theorem 17.1 - explicit σ_branch > 0
- Feedback Section 6: Theorem 17.2 - explicit ΣΔB⁽ˡ⁾ = 0
