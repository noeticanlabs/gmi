# GMI Reserve Law Implementation Plan

## Problem Identified

The Greed Test revealed a critical flaw: the system allows moves that satisfy immediate thermodynamic constraints but exhaust budget to near-zero, destroying future viability.

Example from test:
- Initial budget: b = 5.0
- Greedy move sigma: σ = 4.5
- Resulting budget: b' = 0.5
- Move passes thermodynamic check (V' + σ < V)
- But system becomes too weak to recover

## Solution: Reserve Law

### Core Principle
> A system must preserve a protected minimum budget after every non-emergency action.

### Mathematical Formulation

**Fixed Reserve:**
```
b_next = b - σ + G
Admissible iff: b_next >= b_reserve
```

**State-Dependent Reserve:**
```
b_reserve = R(z) = r_0 + α·Π + β·U_env + γ·N_branches
```
Where:
- Π = pressure load
- U_env = environmental uncertainty  
- N_branches = memory/branching factor

### Implementation

**Current Verifier Logic:**
```python
accepted = (V_next + sigma <= V_now) and (sigma <= budget)
```

**With Reserve Law:**
```python
b_next = budget - sigma + replenishment

accepted = (
    V_next + sigma <= V_now
    and sigma <= budget
    and b_next >= b_reserve  # NEW: Reserve Law
)
```

## Implementation Steps

### 1. Add Reserve Law to OplaxVerifier

Modify `ledger/oplax_verifier.py`:
- Add `reserve_floor` parameter (default: 1.0)
- Add reserve check in `check()` method
- Return REJECTED if budget would fall below reserve

### 2. Test with Greed Scenario

Run greed test - greedy move should now be REJECTED because:
- σ = 4.5, b = 5.0
- b_next = 5.0 - 4.5 = 0.5
- b_reserve = 1.0
- 0.5 < 1.0 → REJECTED

### 3. Add Dynamic Reserve (Optional)

Create a state-dependent reserve function:
```python
def compute_reserve(state: State, instruction: Instruction) -> float:
    base_reserve = 1.0
    pressure_factor = 0.1 * instruction.sigma
    uncertainty_factor = 0.2 * instruction.kappa
    return base_reserve + pressure_factor + uncertainty_factor
```

### 4. Emergency Override (Optional)

Allow bypassing reserve for critical actions:
```python
accepted = (
    V_next + sigma <= V_now
    and sigma <= budget
    and (b_next >= b_reserve or instruction.is_emergency)
)
```

## Expected Results

| Scenario | Before Reserve | After Reserve |
|----------|---------------|---------------|
| Greedy move (σ=4.5, b=5.0) | Accepted | **Rejected** (b_next=0.5 < 1.0) |
| Safe move (σ=0.5, b=5.0) | Accepted | Accepted (b_next=4.5 >= 1.0) |
| Pressure test | Pass | Pass (unchanged) |
| Lazy test | Pass | Pass (unchanged) |

## Anti-Greed Stability Theorem

**If all non-emergency transitions satisfy the reserve law, then no admissible action can maximize immediate potential descent while forcing deterministic near-term budget bankruptcy below the protected reserve threshold.**

This mathematically proves the greed test will fail when reserve law is enforced.

## Files to Modify

1. `ledger/oplax_verifier.py` - Add reserve law
2. `experiments/stress_tests.py` - Verify greed test now rejects greedy move

## Success Criteria

- [ ] Greedy move (σ=4.5, b=5.0) is REJECTED
- [ ] Safe moves still accepted
- [ ] All other tests still pass
