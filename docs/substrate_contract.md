# GM-OS Substrate Contract

**Canonical ID:** `gmos.substrate_contract.v1`  
**Version:** `1.0.0`  
**Status:** Canonical - Phase 1 Foundation Document

This document defines what GM-OS must provide to any hosted process. It specifies the service interfaces, inputs, outputs, invariants, error modes, and receipt requirements for each substrate service.

---

## 1. State Host

Maintains canonical runtime state.

### Interface

```python
class StateHost:
    def get_state(self) -> FullSubstrateState:
        """Get current full substrate state."""
    
    def update_state(self, state: FullSubstrateState) -> None:
        """Update substrate state after verified transition."""
    
    def snapshot(self) -> StateSnapshot:
        """Create a point-in-time snapshot of state."""
    
    def restore(self, snapshot: StateSnapshot) -> None:
        """Restore state from snapshot."""
```

### Inputs

- None (manages internal state)

### Outputs

- `FullSubstrateState`: Complete state vector `ξ = (x_ext, s, m, b, p, k, ℓ)`

### Invariants

- State updates only occur through verified transitions
- No direct mutation outside transaction boundary

### Error Modes

- `StateCorruptedError`: State integrity check failed
- `SnapshotError`: Snapshot creation failed

### Receipt Requirements

- Every state update must produce a receipt

---

## 2. Budget Manager

Tracks budget allocations, reserves, and spending.

### Interface

```python
class BudgetManager:
    def get_budget(self) -> BudgetState:
        """Get current budget state."""
    
    def can_spend(self, amount: float, channel: str = "default") -> bool:
        """Check if spend is allowed within reserves."""
    
    def spend(self, amount: float, channel: str = "default") -> SpendResult:
        """Execute a spend operation."""
    
    def get_reserve(self, channel: str = "default") -> float:
        """Get current reserve for channel."""
    
    def replenish(self, amount: float, channel: str = "default") -> None:
        """Replenish budget for channel."""
```

### Inputs

- `amount`: Amount to spend
- `channel`: Budget channel identifier

### Outputs

- `BudgetState`: Current budget, reserves, spend, defect allowance
- `SpendResult`: Success/failure, amount spent, remaining budget

### Invariants

- `reserve >= reserve_floor` always holds
- `total_spend <= budget_allocation` always holds
- No negative spends allowed

### Error Modes

- `InsufficientBudgetError`: Spend would violate reserve floor
- `InvalidChannelError`: Unknown budget channel

### Receipt Requirements

- Every spend operation must be recorded in receipt

---

## 3. Verifier

Computes whether a proposal is admissible.

### Interface

```python
class Verifier:
    def verify(
        self,
        current_state: FullSubstrateState,
        proposal: Proposal,
        budget: BudgetState
    ) -> VerifierResult:
        """Verify if proposal is admissible."""
    
    def compute_residual(
        self,
        current_state: FullSubstrateState,
        proposed_state: FullSubstrateState
    ) -> float:
        """Compute coherence residual: ρ = V(x_{t+1}) - V(x_t)"""
    
    def check_admissibility(
        self,
        state: FullSubstrateState,
        budget: BudgetState
    ) -> bool:
        """Check if state is in admissible region K."""
```

### Inputs

- `current_state`: Current full substrate state `x_t`
- `proposal`: Proposed action/state update `u_t`
- `budget`: Current budget state

### Outputs

- `VerifierResult`: One of `ACCEPT`, `REPAIR`, `REJECT`
- Includes: `residual`, `spend`, `defect`, `reserve_slack`, `verdict`

### Invariants

- Verifier must be deterministic: same inputs → same outputs
- Must check: `V(x_{t+1}) + σ ≤ V(x_t) + κ + r`

### Error Modes

- `VerificationError`: Internal verification failure
- `InvalidProposalError`: Malformed proposal

### Receipt Requirements

- Every verification must produce a receipt with verdict and scores

---

## 4. Repair/Reject Interface

Handles proposals that fail verification.

### Interface

```python
class RepairController:
    def repair(self, proposal: Proposal, verifier_result: VerifierResult) -> Proposal:
        """Attempt to repair a failed proposal."""
    
    def project_to_admissible(
        self,
        proposal: Proposal,
        budget: BudgetState
    ) -> Proposal:
        """Project proposal to admissible region."""
    
    def reject(self, proposal: Proposal, reason: RejectCode) -> None:
        """Reject proposal with reason."""
    
    def abstain(self, proposal: Proposal) -> None:
        """Abstain from action (no-op)."""
```

### Repair Strategies

1. **Project**: Apply Moreau projection to admissible region
2. **Reduce Spend**: Scale down resource consumption
3. **Defer**: Delay proposal to future step
4. **Split**: Break into smaller sub-proposals
5. **Abstain**: Do nothing

### Inputs

- `proposal`: Failed proposal
- `verifier_result`: Original verification result
- `reason`: Rejection reason code

### Outputs

- `Proposal`: Repaired proposal or `⊥` (rejected)

### Invariants

- Repaired proposals must pass verifier
- Original proposal intent preserved where possible

### Error Modes

- `RepairImpossibleError`: Cannot repair to admissible state
- `RepairFailedError`: Repair operation failed

### Receipt Requirements

- All repair attempts must be logged with before/after state

---

## 5. Memory Service

Manages episodic memory and workspace.

### Interface

```python
class MemoryService:
    def store_episode(self, episode: MemoryEpisode) -> EpisodeId:
        """Store a new memory episode."""
    
    def retrieve(
        self,
        query: MemoryQuery,
        limit: int = 10
    ) -> list[MemoryEpisode]:
        """Retrieve relevant memories."""
    
    def get_workspace(self) -> Workspace:
        """Get current working memory."""
    
    def update_workspace(self, workspace: Workspace) -> None:
        """Update working memory."""
    
    def consolidate(self) -> ConsolidationResult:
        """Consolidate recent episodes to long-term memory."""
```

### Inputs

- `episode`: New memory episode to store
- `query`: Memory retrieval query
- `workspace`: Working memory updates

### Outputs

- `EpisodeId`: Unique identifier for stored episode
- `list[MemoryEpisode]`: Retrieved relevant episodes
- `Workspace`: Current working memory contents

### Invariants

- Episodes are append-only (immutable once stored)
- Workspace is mutable but versioned
- Retrieval must respect budget constraints

### Error Modes

- `MemoryFullError`: Storage capacity exceeded
- `QueryError`: Invalid memory query
- `ConsolidationError`: Consolidation failed

### Receipt Requirements

- Every stored episode must be referenced in receipt
- Workspace updates must be logged

---

## 6. Percept Anchoring Service

Converts raw input into typed percept records.

### Interface

```python
class AnchoringService:
    def anchor(self, raw_input: RawInput) -> Percept:
        """Anchor raw input to typed percept."""
    
    def bind(self, percept: Percept, context: dict) -> AnchoredPercept:
        """Bind percept to current context."""
    
    def get_salience(self, percept: Percept) -> float:
        """Compute percept salience."""
```

### Inputs

- `raw_input`: Raw sensory data (pixels, text, etc.)
- `context`: Current cognitive context

### Outputs

- `Percept`: Typed perceptual record
- `AnchoredPercept`: Context-bound percept

### Invariants

- Anchoring must be deterministic given same input
- Must produce stable semantic binding

### Error Modes

- `AnchoringError`: Failed to anchor input
- `BindingError`: Failed to bind to context

### Receipt Requirements

- Every anchored percept must be logged with timestamp

---

## 7. Receipt Service

Writes append-only auditable records.

### Interface

```python
class ReceiptService:
    def write(self, receipt: Receipt) -> ReceiptId:
        """Write a new receipt."""
    
    def get(self, receipt_id: ReceiptId) -> Receipt:
        """Retrieve a receipt by ID."""
    
    def get_chain(self, from_step: int, to_step: int) -> list[Receipt]:
        """Get receipt chain for step range."""
    
    def verify_chain(self) -> bool:
        """Verify receipt chain integrity."""
    
    def get_latest(self) -> Receipt:
        """Get most recent receipt."""
```

### Receipt Structure

```python
@dataclass
class Receipt:
    step: int                          # Timestep
    proposal_id: str                   # Unique proposal ID
    percept_ref: list[str]             # Percept references
    memory_ref: list[str]              # Memory references
    state_before: StateHash            # Pre-transition state hash
    state_after: StateHash             # Post-transition state hash
    spend: float                       # Budget spent
    defect: float                      # Defect introduced
    reserve_slack: float              # Remaining reserve
    verdict: Verdict                  # ACCEPT/REPAIR/REJECT
    repair_notes: str | None          # Repair information
    timestamp: datetime               # Wall-clock time
    coherence_before: float            # V(x_t)
    coherence_after: float            # V(x_{t+1})
    residual: float                   # ρ = V(x_{t+1}) - V(x_t)
```

### Inputs

- `Receipt`: Complete receipt data

### Outputs

- `ReceiptId`: Unique receipt identifier

### Invariants

- Receipts are append-only (no updates or deletes)
- Chain is cryptographically verifiable
- Timestamps are monotonically increasing

### Error Modes

- `WriteError`: Failed to write receipt
- `ChainVerificationError`: Chain integrity check failed

---

## 8. Action Commit Interface

Commits approved action proposals.

### Interface

```python
class ActionCommit:
    def commit(self, proposal: Proposal) -> CommitResult:
        """Commit a verified proposal."""
    
    def prepare(self, proposal: Proposal) -> PreparedAction:
        """Prepare action for commit (dry run)."""
    
    def rollback(self, commit_id: CommitId) -> None:
        """Rollback a committed action (if supported)."""
```

### Inputs

- `proposal`: Verified and accepted proposal

### Outputs

- `CommitResult`: Commit success/failure, action ID, effects

### Invariants

- Only verified proposals can be committed
- Commit is atomic (all-or-nothing)
- Effects must be deterministic

### Error Modes

- `CommitError`: Commit operation failed
- `RollbackError`: Rollback failed
- `InvalidProposalError`: Proposal not verified

### Receipt Requirements

- Every commit must produce a receipt with action effects

---

## Substrate Service Summary

| Service | Core Responsibility | Key Methods |
|---------|-------------------|-------------|
| StateHost | State management | `get_state()`, `update_state()` |
| BudgetManager | Budget tracking | `can_spend()`, `spend()`, `get_reserve()` |
| Verifier | Proposal verification | `verify()`, `compute_residual()` |
| RepairController | Failure handling | `repair()`, `reject()`, `abstain()` |
| MemoryService | Memory ops | `store_episode()`, `retrieve()` |
| AnchoringService | Percept binding | `anchor()`, `bind()` |
| ReceiptService | Audit trail | `write()`, `get_chain()` |
| ActionCommit | Execution | `commit()`, `prepare()` |

---

## References

- [`coh_gmos_gmi_doctrine.md`](coh_gmos_gmi_doctrine.md) - Canonical doctrine
- [`definition_ledger.md`](definition_ledger.md) - Term definitions
- [`architecture_spec.md`](architecture_spec.md) - Package structure
- [`gmos_canon_spec.md`](gmos_canon_spec.md) - GM-OS specification

---

*This contract is canonical for Phase 1. Any change requires explicit versioning.*
