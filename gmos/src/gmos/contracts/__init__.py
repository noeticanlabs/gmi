"""
GM-OS Contracts Package

This package contains the canonical type definitions and contracts
for Phase 1. These types define the interfaces between the substrate,
hosted agents, and external systems.

Status: Canonical - Phase 1 Foundation
"""

from gmos.contracts.types import (
    # Core types
    State,
    Percept,
    MemoryEpisode,
    Proposal,
    BudgetState,
    VerifierResult,
    Receipt,
    ReceiptData,
    Workspace,
    AnchoredPercept,
    CognitiveState,
    Verdict,
)

from gmos.contracts.substrate import (
    # Substrate interfaces
    StateHost,
    BudgetManager,
    Verifier,
    RepairController,
    MemoryService,
    AnchoringService,
    ReceiptService,
    ActionCommit,
    SubstrateInterface,
)

from gmos.contracts.hosted_agent import (
    # Hosted agent interfaces
    HostedAgent,
    GMIInputs,
    GMIOutputs,
    ProposalGenerator,
)

__all__ = [
    # Types
    "State",
    "Percept",
    "MemoryEpisode",
    "Proposal",
    "BudgetState",
    "VerifierResult",
    "Receipt",
    "ReceiptData",
    "Workspace",
    "AnchoredPercept",
    "CognitiveState",
    "Verdict",
    # Substrate
    "StateHost",
    "BudgetManager",
    "Verifier",
    "RepairController",
    "MemoryService",
    "AnchoringService",
    "ReceiptService",
    "ActionCommit",
    "SubstrateInterface",
    # Hosted Agent
    "HostedAgent",
    "GMIInputs",
    "GMIOutputs",
    "ProposalGenerator",
]
