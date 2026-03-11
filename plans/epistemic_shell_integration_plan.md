# Epistemic Shell Integration Plan

## Overview

This plan defines integration points for the Epistemic Shell v1-v4 into the GMI system. The Epistemic Shell adds 6 new tension terms that govern how the agent handles uncertainty, curiosity, and trust in information sources.

## Core Concepts (from specification)

| Symbol | Meaning |
|--------|---------|
| ℱ (fiber) | Admissible world-model class / hypothesis space |
| H_k (horizon) | Bounded observable evidence at step k |
| W_eff | Effective weight = A_0(s) × Γ_trust(s,t) × Ξ(e) |

## 6 New Tension Terms

| Term | Purpose | Source |
|------|---------|--------|
| V_collapse | Penalize premature fiber/hypothesis collapse | v1 |
| V_overreach | Penalize claims beyond horizon | v2 |
| V_curiosity_deficit | Penalize ignoring high-EVI observations | v3 |
| V_curiosity_mania | Penalize excessive exploration without learning | v3 |
| V_shock | Penalize surprise exceeding adaptive capacity | v4 |
| V_gullible | Penalize authority trust without verification | v4 |

---

## Integration Points

### 1. GMITensionState (tension_law.py:530-573)

**Current fields:**
- Core: latent_state
- Observation: predicted_sensory, actual_sensory, sensory_confidence
- Memory: predicted_memory, actual_memory, memory_weights, fragmentation
- Goals: goals
- Consistency: consistency
- Planning: plan_nodes
- Actions: pending_actions
- Meta: meta
- Budget: budget, reserves
- Authority: authority
- Weights: weights

**Add new fields:**
```python
# Fiber (hypothesis space)
fiber_active: bool = False  # Is fiber tracking active?
fiber_hypotheses: List[str] = field(default_factory=list)  # Current hypotheses
fiber_beliefs: np.ndarray = field(default_factory=lambda: np.array([]))  # Belief distribution

# Horizon (evidence bounds)
horizon_evidence: np.ndarray = field(default_factory=lambda: np.array([]))  # H_k
horizon_confidence: float = 1.0  # Confidence in horizon boundary

# Effective weight (authority × trust × evidence quality)
authority_source: str = ""  # Source identifier
authority_trust: float = 1.0  # Γ_trust(s,t)
authority_provenance: float = 1.0  # A_0(s)
evidence_quality: float = 1.0  # Ξ(e)

# Curiosity metrics
evi_observations: List[Tuple[np.ndarray, float]] = field(default_factory=list)  # (observation, EVI)
curiosity_expenditure: float = 0.0  # Total curiosity spend

# Shock metrics
surprise_history: List[float] = field(default_factory=list)
adaptive_capacity: float = 1.0  # Max surprise tolerance
```

### 2. TensionWeights (tension_law.py:72-90)

**Add new weight parameters:**
```python
@dataclass
class TensionWeights:
    # Existing weights...
    w_collapse: float = 0.5     # v1: Fiber collapse penalty
    w_overreach: float = 0.5    # v2: Horizon overreach penalty
    w_curiosity_def: float = 0.3  # v3: Curiosity deficit
    w_curiosity_man: float = 0.3   # v3: Curiosity mania
    w_shock: float = 0.4         # v4: Shock/surprise
    w_gullible: float = 0.4     # v4: Gullibility
```

### 3. GMITensionLaw.compute() (tension_law.py:637-711)

**Add new V_epi computation:**
```python
def compute(self, state: GMITensionState) -> float:
    # ... existing code ...
    
    # V_epi (Epistemic Shell v1-v4)
    V += self._compute_epistemic_potential(state)
    
    return V

def _compute_epistemic_potential(self, state: GMITensionState) -> float:
    V_epi = 0.0
    
    # v1: V_collapse - don't collapse fiber prematurely
    V_collapse = self._compute_collapse_potential(
        state.fiber_active,
        state.fiber_hypotheses,
        state.fiber_beliefs,
    )
    V_epi += self.weights.w_collapse * V_collapse
    
    # v2: V_overreach - stay within horizon
    V_overreach = self._compute_overreach_potential(
        state.fiber_beliefs,
        state.horizon_evidence,
        state.horizon_confidence,
    )
    V_epi += self.weights.w_overreach * V_overreach
    
    # v3: V_curiosity - balance exploration
    V_curiosity = self._compute_curiosity_potential(
        state.evi_observations,
        state.curiosity_expenditure,
    )
    V_epi += (self.weights.w_curiosity_def + self.weights.w_curiosity_man) * V_curiosity
    
    # v4: V_trust - verify authority
    V_trust = self._compute_trust_potential(
        state.authority_source,
        state.authority_trust,
        state.authority_provenance,
        state.evidence_quality,
    )
    V_epi += (self.weights.w_shock + self.weights.w_gullible) * V_trust
    
    return V_epi

def _compute_collapse_potential(...) -> float:
    """v1: Penalize if fiber has few hypotheses but high commitment."""
    # If beliefs are peaked (entropy low) but we haven't gathered enough evidence
    pass

def _compute_overreach_potential(...) -> float:
    """v2: Penalize if making claims beyond horizon evidence."""
    # Distance between belief support and evidence horizon
    pass

def _compute_curiosity_potential(...) -> float:
    """v3: Penalize both deficit (ignoring high-EVI) and mania (wasting budget)."""
    # EVI - expected value of information
    pass

def _compute_trust_potential(...) -> float:
    """v4: Penalize shock (surprise > capacity) and gullibility (trust > evidence)."""
    # W_eff = A_0 × Γ_trust × Ξ
    pass
```

---

## Supporting Modules

### 4. Memory Components (gmos/src/gmos/memory/)

**archive.py** - Track evidence history
- Add `evidence_archive: List[Tuple[np.ndarray, float]]` - stores observations with EVI scores
- Add `hypothesis_archive: Dict[str, np.ndarray]` - stores fiber belief states

**workspace.py** - Working memory for active processing
- Add `active_fiber: Optional[FiberState]` - current fiber being evaluated
- Add `horizon_buffer: np.ndarray` - recent evidence within horizon

### 5. Affective Components (gmos/src/gmos/agents/gmi/)

**affective_state.py** - Emotional scaffolding
- Add `shock_response: float` - current shock level (0-1)
- Add `trust_calibration: float` - trust adjustment factor

**affective_budget.py** - Budget allocation for curiosity
- Add `curiosity_budget: float` - allocation for EVI-driven exploration
- Add `trust_verification_cost: float` - cost to verify authority claims

### 6. Execution Loop (gmos/src/gmos/agents/gmi/execution_loop.py)

**Integration point: run_gmi_engine()**
- Before step: Compute fiber state and horizon
- After observation: Update V_collapse, V_overreach
- After memory update: Compute V_curiosity
- After authority check: Compute V_gullible

---

## Implementation Order

### Phase 1: Core Structures (Lowest Risk)
1. Add new fields to TensionWeights dataclass
2. Add new fields to GMITensionState dataclass
3. Create skeleton `_compute_epistemic_potential()` method

### Phase 2: v1-v2 Implementation (Medium Risk)
4. Implement `_compute_collapse_potential()` (v1)
5. Implement `_compute_overreach_potential()` (v2)
6. Add fiber/horizon tracking to memory components

### Phase 3: v3 Implementation (Medium Risk)
7. Implement EVI (Expected Value of Information) computation
8. Implement `_compute_curiosity_potential()` (v3)
9. Add curiosity budget allocation

### Phase 4: v4 Implementation (Highest Risk)
10. Implement authority trust tracking
11. Implement `_compute_trust_potential()` (v4)
12. Add shock response system

### Phase 5: Integration & Testing
13. Wire into execution_loop.py
14. Add comprehensive tests
15. Verify all 6 terms affect behavior correctly

---

## Test Requirements

New tests in `tests/test_epistemic_shell.py`:
- `test_v1_collapse_penalty` - Verify fiber collapse is penalized
- `test_v2_overreach_penalty` - Verify claims beyond horizon are penalized
- `test_v3_curiosity_deficit` - Verify high-EVI observations trigger exploration
- `test_v3_curiosity_mania` - Verify excessive exploration is penalized
- `test_v4_shock_penalty` - Verify surprise beyond capacity is penalized
- `test_v4_gullibility` - Verify unverified authority trust is penalized
- `test_fiber_tracking` - Verify hypothesis space tracking
- `test_horizon_computation` - Verify evidence horizon bounds
- `test_weff_computation` - Verify effective weight formula

---

## Files to Modify

| File | Changes |
|------|---------|
| `gmos/src/gmos/agents/gmi/tension_law.py` | Add V_epi computation |
| `gmos/src/gmos/agents/gmi/state.py` | May need new state fields |
| `gmos/src/gmos/memory/archive.py` | Track evidence history |
| `gmos/src/gmos/memory/workspace.py` | Active fiber workspace |
| `gmos/src/gmos/agents/gmi/affective_state.py` | Shock/trust emotions |
| `gmos/src/gmos/agents/gmi/affective_budget.py` | Curiosity budget |
| `gmos/src/gmos/agents/gmi/execution_loop.py` | Wire in epistemic terms |
| `tests/test_epistemic_shell.py` | New test file |

---

## Key Formulas

### v1: Local Evidence / Global Underdetermination
```
V_collapse = -β_collapse × (1 - H(fiber_beliefs)/H_max) × I(hypotheses > threshold)
```
Where H is entropy, I is indicator. Penalize low-entropy beliefs before sufficient evidence.

### v2: Representative Model / Fiber Distinction
```
V_overreach = β_overreach × dist(support(beliefs), horizon_evidence)
```
Penalize distance between belief support and observable evidence.

### v3: Targeted Curiosity
```
EVI(o) = Σ_p P(p|o) × [V(decision|p) - V(decision|¬p)]
V_curiosity = β_def × max(0, EVI - curiosity_threshold) - β_man × (expenditure / budget)
```
EVI = Expected Value of Information. Balance between deficit and mania.

### v4: Epistemic Trust
```
W_eff = A_0(source) × Γ_trust(source, agent) × Ξ(evidence_quality)
V_shock = β_shock × max(0, surprise - adaptive_capacity)
V_gullible = β_gullible × max(0, authority_trust - W_eff)
```

---

## Success Criteria

1. All 6 tension terms compute without errors
2. V_epi contributes meaningfully to total V_GMI
3. Fiber tracking correctly identifies hypothesis space
4. Horizon bounds limit overreach
5. Curiosity budget balances exploration/exploitation
6. Trust verification prevents gullibility
7. Tests pass for all new functionality
