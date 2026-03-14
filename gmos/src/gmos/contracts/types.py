"""
GM-OS Core Type Definitions

This module defines the canonical types for Phase 1. These are the primitive
objects that form the foundation of the governed substrate.

Status: Canonical - Phase 1 Foundation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable


# =============================================================================
# Enumerations
# =============================================================================


class Verdict(Enum):
    """Result of proposal verification."""
    ACCEPT = "accept"
    REPAIR = "repair"
    REJECT = "reject"
    ABSTAIN = "abstain"


class OperationalMode(Enum):
    """Current phase of the execution loop."""
    OBSERVE = "observe"
    ANCHOR = "anchor"
    RETRIEVE = "retrieve"
    PROPOSE = "propose"
    EVALUATE = "evaluate"
    VERIFY = "verify"
    REPAIR = "repair"
    REJECT = "reject"
    COMMIT = "commit"
    RECEIPT = "receipt"
    UPDATE = "update"


class ProposalType(Enum):
    """Types of proposals GMI can generate."""
    ACT = "act"
    REASON = "reason"
    LEARN = "learn"
    REMEMBER = "remember"
    ABSTAIN = "abstain"
    REPAIR = "repair"


# =============================================================================
# Core State Types
# =============================================================================


@dataclass
class State:
    """
    Full state of the system at a given step.
    
    This is the primary state container for the substrate.
    """
    state_id: str
    step: int
    coherence: float = 0.0  # V(x) - coherence functional value
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __hash__(self) -> int:
        return hash((self.state_id, self.step))


@dataclass
class BudgetState:
    """
    Budget allocation state.
    
    Tracks current budget, reserves, and spending across channels.
    """
    total: float
    available: float
    spent: float = 0.0
    reserves: dict[str, float] = field(default_factory=dict)
    reserve_floors: dict[str, float] = field(default_factory=dict)
    defect_allowance: float = 0.0
    
    @property
    def reserve_slack(self) -> dict[str, float]:
        """Calculate reserve slack (available - floor) per channel."""
        return {
            channel: max(0, self.reserves.get(channel, 0) - floor)
            for channel, floor in self.reserve_floors.items()
        }


# =============================================================================
# Memory Types
# =============================================================================


@dataclass
class MemoryEpisode:
    """
    A discrete memory unit.
    
    Contains timestamped content with salience and coherence weight.
    """
    episode_id: str
    timestamp: datetime
    content: Any
    salience: float = 0.0
    coherence_weight: float = 1.0
    embedding: list[float] | None = None
    
    def __hash__(self) -> int:
        return hash(self.episode_id)


@dataclass
class Workspace:
    """
    Active working memory.
    
    Contains current context and relevant recalled episodes.
    """
    workspace_id: str
    context: dict[str, Any] = field(default_factory=dict)
    episodes: list[MemoryEpisode] = field(default_factory=list)
    active_goals: list[dict[str, Any]] = field(default_factory=list)


# =============================================================================
# Sensory Types
# =============================================================================


@dataclass
class Percept:
    """
    Raw sensory input anchored into a typed perceptual record.
    """
    percept_id: str
    raw_input: Any
    modality: str  # e.g., "vision", "audio", "text"
    timestamp: datetime = field(default_factory=datetime.now)
    features: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnchoredPercept:
    """
    Percept bound to current context.
    """
    percept: Percept
    context: dict[str, Any] = field(default_factory=dict)
    salience: float = 0.0
    binding_strength: float = 1.0


# =============================================================================
# Proposal Types
# =============================================================================


@dataclass
class Proposal:
    """
    A candidate action or state update proposed by the hosted process.
    """
    proposal_id: str
    type: ProposalType
    parameters: dict[str, Any] = field(default_factory=dict)
    intent: dict[str, Any] = field(default_factory=dict)
    spend_estimate: float = 0.0
    defect_estimate: float = 0.0
    confidence: float = 1.0
    priority: float = 0.0
    explanation: dict[str, str] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash(self.proposal_id)


@dataclass
class Action:
    """
    A committed action that has passed verification.
    """
    action_id: str
    proposal_id: str
    type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    effects: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# Verification Types
# =============================================================================


@dataclass
class VerifierResult:
    """
    Result of evaluating a proposal against admissibility.
    """
    verdict: Verdict
    residual: float = 0.0  # ρ = V(x_{t+1}) - V(x_t)
    spend: float = 0.0  # σ - budget consumption
    defect: float = 0.0  # κ - incoherence introduced
    reserve_slack: float = 0.0  # r - available reserve
    coherence_before: float = 0.0
    coherence_after: float = 0.0
    repair_notes: str | None = None
    reasons: list[str] = field(default_factory=list)
    
    @property
    def is_acceptable(self) -> bool:
        """Check if proposal satisfies verifier inequality."""
        if self.verdict == Verdict.ACCEPT:
            return True
        if self.verdict == Verdict.REPAIR:
            return True
        return False


# =============================================================================
# Receipt Types
# =============================================================================


@dataclass
class ReceiptData:
    """
    Data for creating a receipt.
    """
    step: int
    proposal_id: str
    percept_refs: list[str] = field(default_factory=list)
    memory_refs: list[str] = field(default_factory=list)
    state_before_hash: str = ""
    state_after_hash: str = ""
    spend: float = 0.0
    defect: float = 0.0
    reserve_slack: float = 0.0
    verdict: Verdict = Verdict.ABSTAIN
    repair_notes: str | None = None
    coherence_before: float = 0.0
    coherence_after: float = 0.0
    residual: float = 0.0


@dataclass
class Receipt:
    """
    Immutable audit record for a state transition.
    """
    receipt_id: str
    step: int
    proposal_id: str
    percept_refs: list[str]
    memory_refs: list[str]
    state_before_hash: str
    state_after_hash: str
    spend: float
    defect: float
    reserve_slack: float
    verdict: Verdict
    repair_notes: str | None
    coherence_before: float
    coherence_after: float
    residual: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __hash__(self) -> int:
        return hash(self.receipt_id)


# =============================================================================
# Cognitive Types
# =============================================================================


@dataclass
class CognitiveState:
    """
    GMI's internal cognitive state.
    """
    state_id: str
    latent_state: dict[str, Any] = field(default_factory=dict)
    memory_slice: list[MemoryEpisode] = field(default_factory=list)
    sensory_view: AnchoredPercept | None = None
    active_goals: list[dict[str, Any]] = field(default_factory=list)
    consistency_state: dict[str, Any] = field(default_factory=dict)
    local_budget: BudgetState | None = None


# =============================================================================
# Protocol Definitions
# =============================================================================


@runtime_checkable
class StateHost(Protocol):
    """Protocol for state management."""
    def get_state(self) -> State: ...
    def update_state(self, state: State) -> None: ...


@runtime_checkable
class BudgetManager(Protocol):
    """Protocol for budget management."""
    def get_budget(self) -> BudgetState: ...
    def can_spend(self, amount: float) -> bool: ...
    def spend(self, amount: float) -> bool: ...


@runtime_checkable
class Verifier(Protocol):
    """Protocol for proposal verification."""
    def verify(self, state: State, proposal: Proposal, budget: BudgetState) -> VerifierResult: ...


@runtime_checkable
class ReceiptService(Protocol):
    """Protocol for receipt management."""
    def write(self, receipt: Receipt) -> str: ...
    def get(self, receipt_id: str) -> Receipt | None: ...


@runtime_checkable
class ProposalGenerator(Protocol):
    """Protocol for proposal generation."""
    def generate(self, inputs: dict[str, Any]) -> Proposal: ...


# =============================================================================
# Utility Functions
# =============================================================================


def compute_residual(coherence_before: float, coherence_after: float) -> float:
    """
    Compute coherence residual: ρ = V(x_{t+1}) - V(x_t)
    
    A negative residual means coherence improved.
    """
    return coherence_after - coherence_before


def check_verifier_inequality(
    coherence_before: float,
    coherence_after: float,
    spend: float,
    defect: float,
    reserve_slack: float
) -> bool:
    """
    Check the verifier inequality: V(x_{t+1}) + σ ≤ V(x_t) + κ + r
    
    Returns True if the proposal is admissible.
    """
    return (coherence_after + spend) <= (coherence_before + defect + reserve_slack)


def create_initial_state(state_id: str = "initial", coherence: float = 0.0) -> State:
    """Create an initial state with default values."""
    return State(
        state_id=state_id,
        step=0,
        coherence=coherence,
        data={},
        timestamp=datetime.now()
    )


def create_initial_budget(
    total: float = 100.0,
    reserve_floor: float = 10.0
) -> BudgetState:
    """Create an initial budget state."""
    return BudgetState(
        total=total,
        available=total,
        spent=0.0,
        reserves={"default": total - reserve_floor},
        reserve_floors={"default": reserve_floor},
        defect_allowance=10.0
    )
