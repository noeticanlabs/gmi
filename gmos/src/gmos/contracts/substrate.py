"""
GM-OS Substrate Contract Interfaces

This module defines the interfaces that GM-OS must implement to provide
services to hosted processes.

Status: Canonical - Phase 1 Foundation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from gmos.contracts.types import (
    State,
    BudgetState,
    Proposal,
    VerifierResult,
    Receipt,
    MemoryEpisode,
    Workspace,
    Percept,
    AnchoredPercept,
    Action,
    Verdict,
)


# =============================================================================
# Substrate Service Interfaces
# =============================================================================


class StateHost(ABC):
    """
    Maintains canonical runtime state.
    
    This service manages the full substrate state and provides
    snapshot/restore capabilities.
    """
    
    @abstractmethod
    def get_state(self) -> State:
        """Get current full substrate state."""
        pass
    
    @abstractmethod
    def update_state(self, state: State) -> None:
        """Update substrate state after verified transition."""
        pass
    
    @abstractmethod
    def snapshot(self) -> dict[str, Any]:
        """Create a point-in-time snapshot of state."""
        pass
    
    @abstractmethod
    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore state from snapshot."""
        pass


class BudgetManager(ABC):
    """
    Tracks budget allocations, reserves, and spending.
    
    This service enforces the reserve law and ensures budget
    conservation.
    """
    
    @abstractmethod
    def get_budget(self) -> BudgetState:
        """Get current budget state."""
        pass
    
    @abstractmethod
    def can_spend(self, amount: float, channel: str = "default") -> bool:
        """Check if spend is allowed within reserves."""
        pass
    
    @abstractmethod
    def spend(self, amount: float, channel: str = "default") -> bool:
        """Execute a spend operation."""
        pass
    
    @abstractmethod
    def get_reserve(self, channel: str = "default") -> float:
        """Get current reserve for channel."""
        pass
    
    @abstractmethod
    def replenish(self, amount: float, channel: str = "default") -> None:
        """Replenish budget for channel."""
        pass


class Verifier(ABC):
    """
    Computes whether a proposal is admissible.
    
    This is the core governance enforcement point.
    """
    
    @abstractmethod
    def verify(
        self,
        current_state: State,
        proposal: Proposal,
        budget: BudgetState
    ) -> VerifierResult:
        """Verify if proposal is admissible."""
        pass
    
    @abstractmethod
    def compute_residual(
        self,
        current_state: State,
        proposed_state: State
    ) -> float:
        """Compute coherence residual: ρ = V(x_{t+1}) - V(x_t)"""
        pass
    
    @abstractmethod
    def check_admissibility(
        self,
        state: State,
        budget: BudgetState
    ) -> bool:
        """Check if state is in admissible region K."""
        pass


class RepairController(ABC):
    """
    Handles proposals that fail verification.
    
    Provides repair strategies and rejection handling.
    """
    
    @abstractmethod
    def repair(
        self,
        proposal: Proposal,
        verifier_result: VerifierResult
    ) -> Proposal:
        """Attempt to repair a failed proposal."""
        pass
    
    @abstractmethod
    def project_to_admissible(
        self,
        proposal: Proposal,
        budget: BudgetState
    ) -> Proposal:
        """Project proposal to admissible region."""
        pass
    
    @abstractmethod
    def reject(
        self,
        proposal: Proposal,
        reason: str
    ) -> None:
        """Reject proposal with reason."""
        pass
    
    @abstractmethod
    def abstain(self, proposal: Proposal) -> None:
        """Abstain from action (no-op)."""
        pass


class MemoryService(ABC):
    """
    Manages episodic memory and workspace.
    """
    
    @abstractmethod
    def store_episode(self, episode: MemoryEpisode) -> str:
        """Store a new memory episode. Returns episode ID."""
        pass
    
    @abstractmethod
    def retrieve(
        self,
        query: dict[str, Any],
        limit: int = 10
    ) -> list[MemoryEpisode]:
        """Retrieve relevant memories."""
        pass
    
    @abstractmethod
    def get_workspace(self) -> Workspace:
        """Get current working memory."""
        pass
    
    @abstractmethod
    def update_workspace(self, workspace: Workspace) -> None:
        """Update working memory."""
        pass


class AnchoringService(ABC):
    """
    Converts raw input into typed percept records.
    """
    
    @abstractmethod
    def anchor(self, raw_input: Any) -> Percept:
        """Anchor raw input to typed percept."""
        pass
    
    @abstractmethod
    def bind(
        self,
        percept: Percept,
        context: dict[str, Any]
    ) -> AnchoredPercept:
        """Bind percept to current context."""
        pass
    
    @abstractmethod
    def get_salience(self, percept: Percept) -> float:
        """Compute percept salience."""
        pass


class ReceiptService(ABC):
    """
    Writes append-only auditable records.
    """
    
    @abstractmethod
    def write(self, receipt: Receipt) -> str:
        """Write a new receipt. Returns receipt ID."""
        pass
    
    @abstractmethod
    def get(self, receipt_id: str) -> Receipt | None:
        """Retrieve a receipt by ID."""
        pass
    
    @abstractmethod
    def get_chain(
        self,
        from_step: int,
        to_step: int
    ) -> list[Receipt]:
        """Get receipt chain for step range."""
        pass
    
    @abstractmethod
    def verify_chain(self) -> bool:
        """Verify receipt chain integrity."""
        pass


class ActionCommit(ABC):
    """
    Commits approved action proposals.
    """
    
    @abstractmethod
    def commit(self, proposal: Proposal) -> Action:
        """Commit a verified proposal."""
        pass
    
    @abstractmethod
    def prepare(self, proposal: Proposal) -> dict[str, Any]:
        """Prepare action for commit (dry run)."""
        pass


# =============================================================================
# Combined Substrate Interface
# =============================================================================


class SubstrateInterface:
    """
    Combined interface providing all substrate services.
    
    This is the main interface that hosted processes use to
    interact with the substrate.
    """
    
    def __init__(
        self,
        state_host: StateHost,
        budget_manager: BudgetManager,
        verifier: Verifier,
        repair_controller: RepairController,
        memory_service: MemoryService,
        anchoring_service: AnchoringService,
        receipt_service: ReceiptService,
        action_commit: ActionCommit,
    ):
        self.state_host = state_host
        self.budget_manager = budget_manager
        self.verifier = verifier
        self.repair_controller = repair_controller
        self.memory_service = memory_service
        self.anchoring_service = anchoring_service
        self.receipt_service = receipt_service
        self.action_commit = action_commit
    
    def step(self, proposal: Proposal) -> tuple[VerifierResult, Action | None]:
        """
        Execute a single step: verify and potentially commit a proposal.
        
        Returns:
            Tuple of (verifier_result, action) where action is None if rejected.
        """
        # Get current state
        state = self.state_host.get_state()
        budget = self.budget_manager.get_budget()
        
        # Verify proposal
        result = self.verifier.verify(state, proposal, budget)
        
        if result.verdict == Verdict.ACCEPT:
            # Commit the action
            action = self.action_commit.commit(proposal)
            return result, action
        
        elif result.verdict == Verdict.REPAIR:
            # Try to repair
            repaired = self.repair_controller.repair(proposal, result)
            # Re-verify repaired proposal
            new_state = self.state_host.get_state()
            new_budget = self.budget_manager.get_budget()
            result = self.verifier.verify(new_state, repaired, new_budget)
            
            if result.verdict == Verdict.ACCEPT:
                action = self.action_commit.commit(repaired)
                return result, action
        
        # Reject or abstain
        return result, None
