# Character Shell Integration Plan

## Overview

The Character Shell is a **threshold modulation field** that defines how the GMI organism responds within the lawful epistemic space. It is NOT a second belief system - it is a lawful parameterization of response style.

**Critical Principle**: Character may modulate thresholds, costs, and preferences **inside** the lawful set, but may NOT override legality, anchor dominance, reserve floors, or deterministic verification.

## The Two Shells

| Shell | Governs | Output |
|-------|---------|--------|
| **Epistemic** | Truth-discipline | What is lawful to believe, ask, trust |
| **Character (χ)** | Style of lawful response | How aggressively/cautiously to act within lawful space |

### Key Distinction

- **Epistemic Shell** = "what is lawful to believe, ask, and trust"
- **Character Shell χ** = "how strongly the organism prefers caution, boldness, patience, curiosity, or cheapness inside that lawful space"

χ does NOT decide truth - it decides **style of lawful pursuit** of truth and action.

---

## The Character Parameters (χ)

Let the character shell be a parameter bundle:

```
χ = (χ_courage, χ_discipline, χ_patience, χ_curiosity, χ_restraint, χ_persistence, χ_laziness, χ_humility) ∈ [0,1]^m
```

These are control coefficients that modulate thresholds and weights inside the lawful epistemic space.

| Parameter | Effect |
|-----------|--------|
| **χ_courage** | Tolerance for acting under ambiguity |
| **χ_discipline** | Pointer preservation, bookkeeping rigor |
| **χ_patience** | Tolerance for delay in learning |
| **χ_curiosity** | Willingness to pay for evidence |
| **χ_restraint** | Corroboration demand before acting |
| **χ_persistence** | Resistance to giving up during repair |
| **χ_laziness** | Preference for cheap representatives |
| **χ_humility** | Resistance to premature fiber collapse |

---

## Integration Points

### 1. Character State Definition

```python
# In a new file: gmos/src/gmos/agents/gmi/character_shell.py

@dataclass
class CharacterState:
    """Character shell state - threshold modulation parameters."""
    
    # χ parameters (control coefficients in [0,1])
    chi_courage: float = 0.5       # Tolerance for acting under ambiguity
    chi_discipline: float = 0.5     # Pointer preservation, bookkeeping rigor
    chi_patience: float = 0.5      # Tolerance for delay in learning
    chi_curiosity: float = 0.5      # Willingness to pay for evidence
    chi_restraint: float = 0.5     # Corroboration demand before acting
    chi_persistence: float = 0.5   # Resistance to giving up during repair
    chi_laziness: float = 0.3      # Preference for cheap representatives
    chi_humility: float = 0.5      # Resistance to premature fiber collapse
    
    # Bounded reservoirs (for dynamics)
    pressure: float = 0.0           # Accumulated pressure from constraints
    shock_level: float = 0.0        # Model-falsification shock
    
    # Drift parameters (how character evolves)
    adaptation_rate: float = 0.05   # Rate of character drift under experience
```

### 2. Threshold Modulation Map (mathfrak M_χ)

The character induces a modulation map on epistemic thresholds:

```python
def compute_modulated_thresholds(
    base_thresholds: EpistemicThresholds,
    chi: CharacterState,
) -> ModulatedThresholds:
    """
    Apply character modulation to epistemic thresholds.
    
    Θ_χ = M_χ(Θ_0)
    """
    
    # v1: Humility modulates collapse resistance
    collapse_weight = base_thresholds.lambda_collapse * (
        1 + 0.5 * chi.chi_humility
    )
    
    # v1: Courage modulates ambiguity tolerance
    frag_threshold = base_thresholds.tau_frag + (
        0.3 * chi.chi_courage - 0.2 * chi.chi_restraint
    )
    
    # v2: Laziness modulates representative persistence
    refresh_threshold = base_thresholds.tau_refresh * (
        1 + 0.5 * chi.chi_laziness - 0.3 * chi.chi_discipline
    )
    
    # v2: Discipline guards against overreach
    overreach_weight = base_thresholds.lambda_overreach * (
        1 + 0.5 * chi.chi_discipline + 0.3 * chi.chi_humility
    )
    
    # v3: Curiosity modulates EVI threshold
    epi_threshold = base_thresholds.tau_epistemic * (
        1 + 0.5 * chi.chi_curiosity - 0.4 * chi.chi_laziness
    )
    
    # v3: Patience modulates delay cost
    delay_weight = base_thresholds.beta_delay * (
        1 + 0.3 * chi.chi_courage + 0.2 * chi.chi_laziness
        - 0.5 * chi.chi_patience
    )
    
    # v3: Restraint vs persistence modulates mania
    mania_weight = base_thresholds.lambda_mania * (
        1 + 0.5 * chi.chi_restraint - 0.4 * chi.chi_persistence
    )
    
    # v4: Restraint/humility demand corroboration
    corr_threshold = base_thresholds.tau_corr * (
        1 + 0.5 * chi.chi_restraint + 0.3 * chi.chi_humility
        - 0.3 * chi.chi_courage
    )
    
    # v4: Courage/patience soften shock
    shock_weight = base_thresholds.lambda_shock * (
        1 - 0.4 * chi.chi_courage - 0.4 * chi.chi_patience
        + 0.3 * chi.chi_laziness
    )
    
    return ModulatedThresholds(
        lambda_collapse=collapse_weight,
        tau_frag=frag_threshold,
        tau_refresh=refresh_threshold,
        lambda_overreach=overreach_weight,
        tau_epistemic=epi_threshold,
        beta_delay=delay_weight,
        lambda_mania=mania_weight,
        tau_corr=corr_threshold,
        lambda_shock=shock_weight,
    )
```

### 3. Character Non-Override Constraint (Theorem)

This is the most important design rule:

```python
def is_action_allowed(action, epistemic_state, character_state):
    """
    Character may bias lawful selection, but may NOT make an unlawful act lawful.
    
    χ does NOT override: verifier acceptance, reserve floors, anchor dominance,
    quarantine thresholds, deterministic receipt legality, admissibility bounds.
    """
    
    # Hard law check (always applies)
    if not meets_legal_constraints(action):
        return False, "violates hard lawful constraints"
    
    # Character can only modulate thresholds within the legal space
    thresholds = compute_modulated_thresholds(base_thresholds, character_state)
    
    # Now apply character-modulated thresholds
    return evaluate_action_under_thresholds(action, epistemic_state, thresholds)
```

**Theorem**: For any character state χ:

```
χ ∉ Override(L_hard)
```

Where L_hard includes: verifier acceptance, reserve floors, anchor dominance, quarantine thresholds, deterministic receipt legality, admissibility bounds.

### 4. Character Dynamics (Drift Under Experience)

Character is not static - it adapts under repeated experiences:

```python
def update_character(
    current: CharacterState,
    receipt: Receipt,
    success: bool,
    shock_received: bool,
) -> CharacterState:
    """
    Update character state based on experiences.
    
    Character drifts slowly under repeated experiences:
    - Successful high-pressure actions → increase courage
    - Repeated lazy refusals → increase laziness temporarily
    - Model falsification shock → increase humility
    - Failed repairs → increase patience
    """
    
    rate = current.adaptation_rate
    
    # Success under pressure increases courage
    if success and receipt.pressure > 0.3:
        new_courage = current.chi_courage + rate * 0.1
    else:
        new_courage = current.chi_courage - rate * 0.05
    
    # Shock from model falsification increases humility
    if shock_received:
        new_humility = current.chi_humility + rate * 0.2
    else:
        new_humility = current.chi_humility - rate * 0.02
    
    # Lazy refusal increases laziness temporarily
    if not success and receipt.action_value > 0:
        new_laziness = current.chi_laziness + rate * 0.1
    else:
        new_laziness = current.chi_laziness - rate * 0.02
    
    # Clamp all values to [0, 1]
    return CharacterState(
        chi_courage=clamp(new_courage),
        chi_discipline=current.chi_discipline,
        chi_patience=clamp(current.chi_patience + (rate * 0.05 if not success else -rate * 0.02)),
        chi_curiosity=current.chi_curiosity,
        chi_restraint=current.chi_restraint,
        chi_persistence=current.chi_persistence,
        chi_laziness=clamp(new_laziness),
        chi_humility=clamp(new_humility),
        pressure=current.pressure,
        shock_level=max(0, current.shock_level - rate * 0.1),
        adaptation_rate=current.adaptation_rate,
    )
```

### 5. Full Integration: Character-Aware GMI Potential

The complete GMI potential with character modulation:

```python
def compute_gmi_potential_with_character(
    state: GMITensionState,
    epistemic_thresholds: EpistemicThresholds,
    character: CharacterState,
) -> float:
    """
    Full GMI potential with character modulation.
    
    V_GMI(x; χ) = V_percept + V_memory + V_goal + V_cons + V_plan 
                + V_action + V_meta + V_resource + V_epi(x; Θ_χ)
    
    Where Θ_χ = M_χ(Θ_0) is the character-modulated epistemic threshold field.
    """
    
    # Base GMI components (unchanged)
    V = compute_base_potential(state)
    
    # Get character-modulated thresholds
    thresholds = compute_modulated_thresholds(epistemic_thresholds, character)
    
    # Compute epistemic potential with modulated thresholds
    V_epi = compute_epistemic_potential(state, thresholds)
    
    V += V_epi
    
    return V
```

The character-aware GMI equation:

```
V_GMI(x; χ) = V_percept + V_memory + V_goal + V_cons + V_plan + V_action + V_meta + V_resource + V_epi(x; Θ_χ)
```

Where χ appears only in the threshold modulation Θ_χ, not in the hard constraints.

### 6. Stack Order

The clean execution order:

```
Coh law → GM-OS substrate → GMI cognition → Epistemic shell v1-v4 → Character shell χ → Execution evaluator
```

Meaning:
1. **Coh** defines what lawful transition means
2. **GM-OS** defines the substrate and kernel
3. **GMI** defines the hosted intelligence
4. **Epistemic shell** constrains belief, uncertainty, curiosity, and trust
5. **Character shell** biases action selection within that lawful epistemic space
6. **Execution evaluator** turns the resulting intention into kernel-step proposals

These are computed from current state geometry:

```python
def compute_laziness(action_cost: float, action_value: float) -> float:
    """Λ = Σ / (Γ + ε)"""
    if action_value <= 0:
        return 0.0
    return action_cost / (action_value + 1e-10)

def compute_greed(short_term_gain: float, future_cost: float, reserve_cost: float) -> float:
    """G = Γ_short / (Σ + R_future + R_reserve)"""
    denominator = future_cost + reserve_cost + 1e-10
    return short_term_gain / denominator

def compute_freeze(pressure: float, action_capacity: float) -> float:
    """Φ = Π / (𝒜 + ε)"""
    return pressure / (action_capacity + 1e-10)
```

### 3. Effective Action Capacity

```python
def compute_effective_action(
    base_action: float,
    discipline: float,
    courage: float,
    laziness: float,
    greed: float,
    freeze: float,
    # Gains
    kappa_D: float = 1.0,
    kappa_C: float = 1.0,
    kappa_L: float = 1.0,
    kappa_G: float = 1.0,
    kappa_F: float = 1.0,
) -> float:
    """
    𝒜_eff = 𝒜_0 + κ_D 𝒟 + κ_C 𝒞 - κ_Λ Λ - κ_G G - κ_Φ Φ
    """
    return (
        base_action
        + kappa_D * discipline
        + kappa_C * courage
        - kappa_L * laziness
        - kappa_G * greed
        - kappa_F * freeze
    )
```

### 4. Dynamics (Per Epoch)

```python
def update_character_shell(
    state: CharacterShellState,
    action_taken: bool,
    action_successful: bool,
    action_cost: float,
    action_value: float,
    pressure_input: float,
    has_fallback: bool,
) -> CharacterShellState:
    """Update character shell state for next epoch."""
    
    # Pressure dynamics: Π_{k+1} = (1 - γ_Π)Π_k + pressure_input
    # If fallback taken, also: Π_{k+1} *= (1 - β_Π)
    new_pressure = (1 - state.gamma_pressure) * state.pressure + pressure_input
    if has_fallback:
        new_pressure *= (1 - state.beta_pressure)
    new_pressure = min(new_pressure, state.pressure_max)
    
    # Courage dynamics: fills on success, decays otherwise
    if action_taken and action_successful and pressure_input > 0.3:
        # Courage gains from high-pressure success
        courage_gain = 0.1 * pressure_input
    else:
        courage_gain = 0.0
    new_courage = (
        (1 - state.gamma_courage) * state.courage 
        + courage_gain
    )
    new_courage = min(max(new_courage, 0.0), state.courage_max)
    
    # Discipline debt: accumulates on lazy refusal, discharges on action
    if not action_taken and action_value > 0:
        # Lazy refusal adds debt
        debt_gain = action_value * 0.5
    elif action_taken and action_successful:
        # Successful action reduces debt
        debt_gain = -action_cost * 0.3
    else:
        debt_gain = 0.0
    new_debt = state.discipline_debt + debt_gain
    new_debt = min(max(new_debt, 0.0), state.discipline_debt_max)
    
    return CharacterShellState(
        pressure=new_pressure,
        courage=new_courage,
        discipline_debt=new_debt,
        courage_baseline=state.courage_baseline,
        courage_max=state.courage_max,
        pressure_max=state.pressure_max,
        discipline_debt_max=state.discipline_debt_max,
        gamma_pressure=state.gamma_pressure,
        beta_pressure=state.beta_pressure,
        gamma_courage=state.gamma_courage,
        gamma_debt=state.gamma_debt,
    )
```

---

## Stability Guarantees

### Contractivity Condition

For stability, feedback gains must satisfy:

```
κ_C * γ_C < κ_Φ * β_Π
```

This prevents "reckless panic" cycles where pressure breeds artificial courage.

### Boundedness Theorems

1. **Pressure**: `0 ≤ Π_k ≤ Π_max` - Always finite
2. **Courage**: `0 ≤ 𝒞_k ≤ 𝒞_max` - Finite reservoir  
3. **Discipline Debt**: `0 ≤ Δ_disc_k ≤ Δ_max` - Bounded accumulation

---

## Integration with Execution Loop

### Where to Add in execution_loop.py

```python
def run_gmi_engine(...):
    # Existing setup...
    
    # NEW: Initialize character shell
    character = CharacterShellState()
    
    while step <= max_steps:
        # Existing: dynamics_step generates instructions
        
        # NEW: Compute pathological projections
        laziness = compute_laziness(action_cost, action_value)
        greed = compute_greed(short_term_gain, future_cost, reserve_cost)
        freeze = compute_freeze(character.pressure, action_capacity)
        
        # NEW: Compute effective action capacity
        action_capacity = compute_effective_action(
            base_action=1.0,
            discipline=1.0 - character.discipline_debt,  # Debt reduces discipline
            courage=character.courage,
            laziness=laziness,
            greed=greed,
            freeze=freeze,
        )
        
        # NEW: Check if action is possible
        if action_capacity <= 0:
            # Force fallback or enter torpor
            pass
        
        # Existing: verification and execution...
        
        # NEW: Update character shell
        character = update_character_shell(
            character,
            action_taken=accepted,
            action_successful=accepted and v_after < v_before,
            action_cost=receipt.cost,
            action_value=v_before - v_after,
            pressure_input=constraint_proximity,
            has_fallback=used_fallback,
        )
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `gmos/src/gmos/agents/gmi/character_shell.py` | **NEW** - Character state, threshold modulation, dynamics |
| `gmos/src/gmos/agents/gmi/tension_law.py` | Extend with threshold modulation map M_χ |
| `gmos/src/gmos/agents/gmi/execution_loop.py` | Add character shell to execution |
| `tests/test_character_shell.py` | **NEW** - Test suite |

---

## Character Profiles (Examples)

| Profile | χ_courage | χ_discipline | χ_patience | χ_curiosity | χ_restraint | χ_humility |
|---------|------------|--------------|------------|-------------|-------------|-------------|
| **Scientist** | 0.3 | 0.8 | 0.8 | 0.6 | 0.7 | 0.8 |
| **Warrior** | 0.9 | 0.6 | 0.3 | 0.4 | 0.3 | 0.4 |
| **Explorer** | 0.7 | 0.4 | 0.5 | 0.9 | 0.3 | 0.5 |
| **Diplomat** | 0.5 | 0.7 | 0.6 | 0.5 | 0.8 | 0.7 |

---

## Summary

The Character Shell χ is a **threshold modulation field** that:

1. **Modulates** epistemic thresholds within the lawful space
2. **Cannot override** hard constraints (verifier, reserves, anchors)
3. **Adapts** slowly under repeated experiences
4. **Defines** response style (cautious vs bold, patient vs impulsive)

The clean separation:

```
Epistemic Shell = "what is lawful to believe, ask, and trust"
Character Shell χ = "how strongly the organism prefers caution, boldness, 
                     patience, curiosity, or cheapness inside that lawful space"
```

χ does NOT decide truth - it decides **style of lawful pursuit** of truth and action.

---

## Character Shell + Epistemic Shell = Complete Agent

| Shell | Governs | Output |
|-------|---------|--------|
| **Epistemic** | Belief quality | V_epi (tension term) |
| **Character** | Action quality | 𝒜_eff (action threshold) |

Together they form the **full behavioral control system**:

```
Decision = f(Epistemic Shell state, Character Shell state)
```

---

## Implementation Order

1. Create `character_shell.py` with state and projection functions
2. Add character shell to execution loop
3. Add character-based tension penalties to tension_law.py
4. Create tests
5. Verify stability theorems hold

---

## Success Criteria

1. All 6 primitives compute without errors
2. 𝒜_eff correctly gates action commitment
3. Stability bounds are maintained under stress
4. Contractivity condition prevents oscillation
5. Tests pass for all functionality
