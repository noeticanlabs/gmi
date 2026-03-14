"""
GM-OS Hosted Agent Contract Interfaces

This module defines the interfaces that hosted agents (like GMI) must implement
to interact with the substrate.

Status: Canonical - Phase 1 Foundation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from gmos.contracts.types import (
    State,
    BudgetState,
    Proposal,
    Workspace,
    MemoryEpisode,
    AnchoredPercept,
    CognitiveState,
    VerifierResult,
    ProposalType,
    Verdict,
)


# =============================================================================
# Input Types (from Substrate to Agent)
# =============================================================================


@dataclass
class GMIStateInput:
    """State information provided to GMI each step."""
    state: State
    coherence: float  # V(x_t) - current coherence/debt
    operational_mode: str


@dataclass
class GMIBudgetInput:
    """Budget information provided to GMI each step."""
    total_budget: float
    available: float
    reserves: dict[str, float]
    spent_this_step: float
    defect_allowance: float


@dataclass
class GMIWorkspaceInput:
    """Working memory provided to GMI each step."""
    workspace: Workspace
    context: dict[str, Any]
    active_goals: list[dict[str, Any]]


@dataclass
class GMIMemoryInput:
    """Memory information provided to GMI each step."""
    episodes: list[MemoryEpisode]
    archived_count: int
    consolidation_candidates: list[MemoryEpisode]


@dataclass
class GMIPerceptInput:
    """Percept information provided to GMI each step."""
    current_percept: AnchoredPercept | None
    history: list[AnchoredPercept]
    salience: float


@dataclass
class GMIInputs:
    """
    Complete input bundle provided to GMI each step.
    
    This is the canonical input format from substrate to hosted agent.
    """
    state: GMIStateInput
    budget: GMIBudgetInput
    workspace: GMIWorkspaceInput
    memory: GMIMemoryInput
    percept: GMIPerceptInput


# =============================================================================
# Output Types (from Agent to Substrate)
# =============================================================================


@dataclass
class GMISpendEstimate:
    """GMI's estimate of proposal cost."""
    estimated_spend: float
    confidence: float  # [0, 1]
    breakdown: dict[str, float]


@dataclass
class GMIDefectEstimate:
    """GMI's estimate of proposal risk/defect."""
    estimated_defect: float
    risk_factors: list[str]
    severity: float  # [0, 1]


@dataclass
class GMIConfidence:
    """GMI's confidence in its proposal."""
    confidence: float  # [0, 1]
    abstention_score: float  # [0, 1]
    reasoning: str
    uncertainty_sources: list[str]


@dataclass
class GMIActionIntent:
    """GMI's intended action."""
    action_type: str
    parameters: dict[str, Any]
    target: str | None
    expected_effect: str


@dataclass
class GMIExplanation:
    """Explanation fields for receipt/audit."""
    rationale: str
    alternatives_considered: str
    coherence_impact: str
    budget_impact: str
    memory_influence: str
    goal_alignment: str


@dataclass
class GMIProposalOutput:
    """Proposal output from GMI."""
    proposals: list[Proposal]
    selected: Proposal | None
    alternates: list[Proposal]


@dataclass
class GMIOutputs:
    """
    Complete output bundle from GMI to substrate.
    
    This is the canonical output format from hosted agent to substrate.
    """
    proposals: list[Proposal]
    selected: Proposal | None
    spend_estimate: GMISpendEstimate
    defect_estimate: GMIDefectEstimate
    confidence: GMIConfidence
    action_intent: GMIActionIntent | None
    explanation: GMIExplanation


# =============================================================================
# Hosted Agent Protocol
# =============================================================================


class HostedAgent(ABC):
    """
    Protocol for hosted intelligence processes.
    
    Any agent hosted within GM-OS must implement this interface.
    """
    
    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the agent with configuration."""
        pass
    
    @abstractmethod
    def get_inputs(self) -> GMIInputs:
        """Request current inputs from substrate."""
        pass
    
    @abstractmethod
    def generate_proposal(self, inputs: GMIInputs) -> GMIOutputs:
        """Generate proposals based on inputs."""
        pass
    
    @abstractmethod
    def evaluate_proposal(
        self,
        proposal: Proposal,
        verifier_result: VerifierResult
    ) -> Proposal:
        """Evaluate and potentially repair proposal after verification."""
        pass
    
    @abstractmethod
    def get_state(self) -> CognitiveState:
        """Get agent's internal cognitive state."""
        pass
    
    @abstractmethod
    def set_state(self, state: CognitiveState) -> None:
        """Restore agent's internal cognitive state."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """Return agent's capabilities."""
        pass


# =============================================================================
# Proposal Generator Protocol
# =============================================================================


class ProposalGenerator(ABC):
    """
    Protocol for proposal generation.
    
    This is the core contract: convert inputs into proposals.
    """
    
    @abstractmethod
    def generate(self, inputs: GMIInputs) -> list[Proposal]:
        """Generate candidate proposals from inputs."""
        pass
    
    @abstractmethod
    def select(self, proposals: list[Proposal]) -> Proposal | None:
        """Select best proposal from candidates."""
        pass
    
    @abstractmethod
    def estimate_spend(self, proposal: Proposal) -> GMISpendEstimate:
        """Estimate budget cost of proposal."""
        pass
    
    @abstractmethod
    def estimate_defect(self, proposal: Proposal) -> GMIDefectEstimate:
        """Estimate risk/defect of proposal."""
        pass
    
    @abstractmethod
    def explain(self, proposal: Proposal, inputs: GMIInputs) -> GMIExplanation:
        """Generate explanation for proposal."""
        pass


# =============================================================================
# Default Implementations
# =============================================================================


def create_default_proposal(
    proposal_id: str,
    proposal_type: ProposalType = ProposalType.ABSTAIN,
    reason: str = "default_abstain"
) -> Proposal:
    """
    Create a default abstain proposal.
    
    Used when agent cannot or should not act.
    """
    return Proposal(
        proposal_id=proposal_id,
        type=proposal_type,
        parameters={"reason": reason},
        intent={"action": "abstain"},
        spend_estimate=0.0,
        defect_estimate=0.0,
        confidence=1.0,
        priority=0.0,
        explanation={
            "rationale": f"Abstaining: {reason}",
            "alternatives_considered": "none",
            "coherence_impact": "neutral",
            "budget_impact": "none",
            "memory_influence": "none",
            "goal_alignment": "abstain"
        }
    )


def validate_proposal(proposal: Proposal) -> bool:
    """
    Validate a proposal meets basic requirements.
    
    Returns True if proposal is valid.
    """
    # Must have ID
    if not proposal.proposal_id:
        return False
    
    # Must have valid type
    try:
        ProposalType(proposal.type.value)
    except ValueError:
        return False
    
    # Must have explanation
    if not proposal.explanation:
        return False
    
    # Spend must be non-negative
    if proposal.spend_estimate < 0:
        return False
    
    return True
