# GMI Hosted Agent Contract

**Canonical ID:** `gmi.hosted_agent_contract.v1`  
**Version:** `1.0.0`  
**Status:** Canonical - Phase 1 Foundation Document

This document defines what GMI (Governed Manifold Intelligence) is allowed to assume from the substrate and what it must return. This is the boundary between substrate and intelligence.

---

## 1. Required Inputs

GMI receives the following from the substrate on each step:

### 1.1 Current State

```python
@dataclass
class GMIStateInput:
    """State information provided to GMI each step."""
    state: FullSubstrateState       # Current substrate state x_t
    coherence: float                # V(x_t) - current coherence/debt
    operational_mode: str           # Current mode (OBSERVE, PROPOSE, etc.)
```

### 1.2 Current Budget Summary

```python
@dataclass
class GMIBudgetInput:
    """Budget information provided to GMI each step."""
    total_budget: float             # Total budget allocation
    available: float               # Currently available (not spent)
    reserves: dict[str, float]     # Reserve levels per channel
    spent_this_step: float         # Amount spent in current step
    defect_allowance: float        # κ - allowed incoherence
```

### 1.3 Current Workspace

```python
@dataclass
class GMIWorkspaceInput:
    """Working memory provided to GMI each step."""
    workspace: Workspace            # Current working memory M_W
    context: dict                  # Current cognitive context
    active_goals: list[Goal]        # Currently active goals
```

### 1.4 Retrieved Memory Bundle

```python
@dataclass
class GMIMemoryInput:
    """Memory information provided to GMI each step."""
    episodes: list[MemoryEpisode]   # Retrieved relevant episodes
    archived_count: int            # Total episodes in archive
    consolidation_candidates: list[MemoryEpisode]  # Episodes due for consolidation
```

### 1.5 Anchored Percept Bundle

```python
@dataclass
class GMIPerceptInput:
    """Percept information provided to GMI each step."""
    current_percept: AnchoredPercept  # Most recent anchored percept
    history: list[AnchoredPercept]   # Recent percept history
    salience: float                   # Current percept salience
```

---

## 2. Required Outputs

GMI must produce the following for the substrate:

### 2.1 Proposal Set

```python
@dataclass
class GMIProposalOutput:
    """Proposal output from GMI."""
    proposals: list[Proposal]      # Candidate proposals
    selected: Proposal | None      # Selected proposal (if single)
    alternates: list[Proposal]     # Alternative options
```

### 2.2 Estimated Spend

```python
@dataclass
class GMISpendEstimate:
    """GMI's estimate of proposal cost."""
    estimated_spend: float          # σ - estimated budget consumption
    confidence: float               # Confidence in estimate [0, 1]
    breakdown: dict[str, float]     # Per-channel spend estimate
```

### 2.3 Estimated Defect/Risk

```python
@dataclass
class GMIDefectEstimate:
    """GMI's estimate of proposal risk/defect."""
    estimated_defect: float         # κ - estimated incoherence
    risk_factors: list[str]         # Identified risk factors
    severity: float                 # Overall severity [0, 1]
```

### 2.4 Confidence / Abstention Score

```python
@dataclass
class GMIConfidence:
    """GMI's confidence in its proposal."""
    confidence: float               # Overall confidence [0, 1]
    abstention_score: float         # Should we abstain? [0, 1]
    reasoning: str                  # Explanation for confidence
    uncertainty_sources: list[str] # What we're uncertain about
```

### 2.5 Action Intent

```python
@dataclass
class GMIActionIntent:
    """GMI's intended action."""
    action_type: str               # e.g., "move", "reason", "wait"
    parameters: dict               # Action parameters
    target: str | None             # Target entity (if applicable)
    expected_effect: str          # Expected outcome description
```

### 2.6 Explanation Fields (for Receipt)

```python
@dataclass
class GMIExplanation:
    """Explanation fields for receipt/audit."""
    rationale: str                 # Why this proposal
    alternatives_considered: str   # What else was considered
    coherence_impact: str          # Expected impact on V(x)
    budget_impact: str            # Expected budget impact
    memory_influence: str         # How memory influenced decision
    goal_alignment: str          # Alignment with active goals
```

---

## 3. Required Behavioral Laws

GMI must adhere to the following laws:

### 3.1 Cannot Directly Mutate Substrate

```python
# GMI MUST NOT do this:
state_host.update_state(new_state)  # VIOLATION
budget_manager.spend(amount)        # VIOLATION

# GMI MUST do this:
return proposal  # Let substrate handle mutations
```

GMI generates proposals but cannot execute them directly. All mutations go through the substrate's verification and commit process.

### 3.2 Must Pass Verifier Before Commit

```python
# GMI MUST ensure:
proposal = gmi.generate_proposal(...)
result = substrate.verify(proposal)

if result.verdict == ACCEPT:
    substrate.commit(proposal)
elif result.verdict == REPAIR:
    repaired = substrate.repair(proposal, result)
    substrate.commit(repaired)
else:
    # Abstain - no action
    pass
```

No proposal can be committed without passing the verifier.

### 3.3 Must Produce Receipt-Ready Rationale

```python
# Every proposal must include:
proposal.explanation = GMIExplanation(
    rationale="...",
    alternatives_considered="...",
    coherence_impact="...",
    budget_impact="...",
    memory_influence="...",
    goal_alignment="..."
)
```

GMI must be able to explain its reasoning for audit purposes.

### 3.4 Must Degrade Gracefully

When over budget or incoherent:

```python
def generate_proposal(self, inputs, budget, state):
    # Check constraints BEFORE generating
    if budget.available < MIN_SPEND:
        return Proposal(type="abstain", reason="insufficient_budget")
    
    if state.coherence > MAX_INCOHERENCE:
        return Proposal(type="repair", target="restore_coherence")
    
    # Normal proposal generation
    ...
```

GMI must recognize its limits and abstain or request repair rather than generate harmful proposals.

---

## 4. Proposal Contract

### 4.1 Proposal Structure

```python
@dataclass
class Proposal:
    """A candidate action from GMI."""
    proposal_id: str               # Unique identifier
    type: str                      # Proposal type
    parameters: dict               # Type-specific parameters
    intent: GMIActionIntent        # Action intent
    spend_estimate: GMISpendEstimate
    defect_estimate: GMIDefectEstimate
    confidence: GMIConfidence
    explanation: GMIExplanation
    priority: float                # Priority relative to other proposals
```

### 4.2 Valid Proposal Types

| Type | Description | Required Parameters |
|------|-------------|-------------------|
| `act` | Execute an action | `action`, `target` |
| `reason` | Perform reasoning | `query`, `depth` |
| `learn` | Update internal model | `learning_signal` |
| `remember` | Store to memory | `content`, `importance` |
| `abstain` | Do nothing | `reason` |
| `repair` | Restore coherence | `target_state` |

### 4.3 Proposal Validation

GMI must ensure proposals are valid before returning:

```python
def validate_proposal(proposal: Proposal) -> bool:
    # Must have ID
    if not proposal.proposal_id:
        return False
    
    # Must be in valid type set
    if proposal.type not in VALID_TYPES:
        return False
    
    # Must have spend estimate
    if not proposal.spend_estimate:
        return False
    
    # Must have explanation
    if not proposal.explanation:
        return False
    
    # Spend must be positive
    if proposal.spend_estimate.estimated_spend < 0:
        return False
    
    return True
```

---

## 5. Memory Contract

### 5.1 What GMI Can Read

- `workspace`: Current working memory
- `episodes`: Retrieved relevant episodes
- `archived_count`: Total memory size

### 5.2 What GMI Can Write

GMI can request memory operations through proposals:

```python
# To store a memory:
Proposal(
    type="remember",
    parameters={"content": "...", "importance": 0.8}
)

# To retrieve memory:
# Done via substrate.retrieve() - not direct access
```

### 5.3 Memory Constraints

- GMI cannot directly write to memory; must use proposals
- Memory operations consume budget
- Consolidation happens asynchronously

---

## 6. Error Handling

### 6.1 GMI Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `InsufficientInput` | Missing required input | Request re-provision |
| `BudgetExceeded` | Proposal would overspend | Reduce spend or abstain |
| `LowConfidence` | Uncertain about proposal | Reduce priority or abstain |
| `CoherenceViolation` | Would increase V(x) too much | Propose repair instead |

### 6.2 Substrate Errors

| Error | Cause | GMI Response |
|-------|-------|--------------|
| `VerificationFailed` | Proposal rejected | Accept rejection or attempt repair |
| `BudgetExhausted` | No budget remaining | Abstain |
| `StateCorrupted` | Substrate state bad | Wait for recovery |

---

## 7. Full GMI Contract Interface

```python
class HostedAgent(Protocol):
    """The complete GMI hosted agent contract."""
    
    def initialize(self, config: dict) -> None:
        """Initialize GMI with configuration."""
    
    def get_inputs(self) -> GMIInputs:
        """Request current inputs from substrate."""
    
    def generate_proposal(self, inputs: GMIInputs) -> Proposal:
        """Generate a proposal based on inputs."""
    
    def evaluate_proposal(
        self,
        proposal: Proposal,
        verifier_result: VerifierResult
    ) -> Proposal:
        """Evaluate and potentially repair proposal after verification."""
    
    def get_state(self) -> CognitiveState:
        """Get GMI's internal cognitive state."""
    
    def set_state(self, state: CognitiveState) -> None:
        """Restore GMI's internal cognitive state."""
    
    def get_capabilities(self) -> AgentCapabilities:
        """Return GMI's capabilities."""
```

---

## References

- [`coh_gmos_gmi_doctrine.md`](coh_gmos_gmi_doctrine.md) - Canonical doctrine
- [`definition_ledger.md`](definition_ledger.md) - Term definitions
- [`substrate_contract.md`](substrate_contract.md) - Substrate contract
- [`gmi_canon_spec.md`](gmi_canon_spec.md) - GMI specification
- [`architecture_spec.md`](architecture_spec.md) - Package structure

---

*This contract is canonical for Phase 1. Any change requires explicit versioning.*
