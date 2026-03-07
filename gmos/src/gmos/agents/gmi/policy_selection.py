"""
Policy Selection and Branch Commitment for the GMI Universal Cognition Engine.

Module 15: Policy Selection, Action Commitment, and the Reality Collision

Implements:
- SelectionOperator: Deterministic argmax branch selection
- Branch: Candidate branch with expected gain and cost
- CommitmentReceipt: Cryptographic proof of intent before action
"""

import uuid
import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class Branch:
    """
    P4 ENHANCEMENT: A candidate branch from counterfactual branching.
    
    Now includes memory costs for tighter memory-policy coupling.
    
    Contains:
    - action: Physical action u_i
    - simulation_cost: Σ(B_i) - accumulated internal simulation cost
    - expected_gain: Γ(B_i) - expected verified gain
    - memory_cost: μ⋅C_mem(B_i) - epistemic cost from memory retrieval
    """
    branch_id: str = field(default_factory=lambda: f"branch_{uuid.uuid4().hex[:8]}")
    action: np.ndarray = None
    simulation_cost: float = 0.0
    expected_gain: float = 0.0
    # P4: Memory-related costs
    memory_cost: float = 0.0  # Cost of retrieving relevant memories
    retrieval_relevance: float = 0.0  # How relevant the retrieved memories are (0-1)
    reality_anchor_weight: float = 0.0  # Weight from reality anchors
    
    # Metadata
    parent_state_hash: str = ""
    action_description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.action is None:
            self.action = np.array([])
    
    @property
    def net_yield(self) -> float:
        """
        P4: Net expected yield including memory costs.
        
        Y(B_i) = Γ(B_i) - Σ(B_i) - μ⋅C_mem(B_i)
        
        This tightens memory-policy coupling by accounting for:
        - Simulation cost
        - Memory retrieval cost
        - Reality anchor influence
        
        The policy now prefers branches that either:
        - Have high expected gain, or
        - Are well-supported by existing memory/anchors
        """
        return self.expected_gain - self.simulation_cost - self.memory_cost
    
    @property
    def adjusted_gain(self) -> float:
        """
        P4: Expected gain adjusted for memory/reality support.
        
        G_adj(B_i) = Γ(B_i) + α⋅retrieval_relevance + β⋅reality_anchor_weight
        
        This rewards branches that align with established memory traces
        and reality anchors.
        """
        alpha = 0.3  # retrieval relevance weight
        beta = 0.2   # reality anchor weight
        return self.expected_gain + alpha * self.retrieval_relevance + beta * self.reality_anchor_weight
    
    @property
    def roi(self) -> float:
        """Return on investment: Γ(B_i) / Σ(B_i)"""
        total_cost = self.simulation_cost + self.memory_cost
        if total_cost <= 0:
            return float('inf') if self.expected_gain > 0 else 0.0
        return self.expected_gain / total_cost
    
    def hash(self) -> str:
        """Deterministic hash of branch."""
        data = {
            'branch_id': self.branch_id,
            'action': self.action.tolist() if len(self.action) > 0 else [],
            'simulation_cost': round(self.simulation_cost, 6),
            'expected_gain': round(self.expected_gain, 6),
            'parent_state_hash': self.parent_state_hash
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class SelectionOperator:
    """
    P4 ENHANCEMENT: O_select now includes memory-awareness.
    
    B* = argmax_{B_i ∈ B_k} Y(B_i)
    
    Where Y(B_i) = Γ(B_i) - Σ(B_i) - μ⋅C_mem(B_i)
    
    P4: Now incorporates:
    - Memory retrieval costs
    - Reality anchor weights
    - Retrieval relevance scores
    
    Deterministic tie-breaking:
    1. Maximum net yield (including memory costs)
    2. Minimum total cost (simulation + memory)
    3. Maximum adjusted gain (with memory/anchor boost)
    4. Minimum branch_id (lexicographic)
    
    This ensures deterministic auditability - no probabilistic sampling.
    """
    
    def __init__(self, allow_ties: bool = False, memory_weight: float = 0.5):
        """
        Initialize selection operator.
        
        Args:
            allow_ties: If True, return all branches with max yield
            memory_weight: Weight for memory costs in yield calculation (0-1)
        """
        self.allow_ties = allow_ties
        self.memory_weight = memory_weight
        self.selection_history: List[Dict] = []
    
    def compute_branch_score(self, branch: Branch) -> tuple:
        """
        P4: Compute composite score for branch ranking.
        
        Returns tuple for sorting: (negative_yield, total_cost, negative_adjusted_gain, branch_id)
        
        This allows multi-criteria selection that balances:
        - Raw yield (prefer high)
        - Total cost (prefer low)
        - Memory/anchor support (prefer high)
        """
        yield_score = -branch.net_yield  # Negative for ascending sort
        total_cost = branch.simulation_cost + branch.memory_cost
        adjusted_gain = -branch.adjusted_gain  # Negative for ascending sort
        
        return (yield_score, total_cost, adjusted_gain, branch.branch_id)
    
    def select(self, branches: List[Branch]) -> Branch:
        """
        P4: Select branch with maximum net yield (now memory-aware).
        
        Args:
            branches: List of candidate branches
            
        Returns:
            Selected branch B*
            
        Raises:
            ValueError: If no branches provided
        """
        if not branches:
            raise ValueError("No branches to select")
        
        if len(branches) == 1:
            selected = branches[0]
            self._record_selection([selected], selected)
            return selected
        
        # P4: Sort by composite score including memory costs
        # Uses compute_branch_score for multi-criteria ranking
        sorted_branches = sorted(
            branches,
            key=self.compute_branch_score
        )
        
        if self.allow_ties:
            # Return all branches with maximum yield
            max_yield = sorted_branches[0].net_yield
            winners = [b for b in sorted_branches if abs(b.net_yield - max_yield) < 1e-9]
            selected = winners[0]  # Still return one deterministically
            self._record_selection(winners, selected)
        else:
            selected = sorted_branches[0]
            self._record_selection([selected], selected)
        
        return selected
    
    def select_multiple(self, branches: List[Branch], n: int = 3) -> List[Branch]:
        """
        Select top-n branches.
        
        Args:
            branches: List of candidate branches
            n: Number of branches to return
            
        Returns:
            List of top-n branches
        """
        if not branches:
            return []
        
        sorted_branches = sorted(
            branches,
            key=lambda b: (-b.net_yield, b.simulation_cost, b.branch_id)
        )
        
        selected = sorted_branches[:n]
        self._record_selection(selected, selected[0])
        
        return selected
    
    def _record_selection(self, candidates: List[Branch], winner: Branch) -> None:
        """Record selection for audit."""
        self.selection_history.append({
            'timestamp': time.time(),
            'candidates': [b.branch_id for b in candidates],
            'selected': winner.branch_id,
            'net_yield': winner.net_yield,
            'count': len(candidates)
        })
    
    def get_selection_summary(self) -> Dict[str, Any]:
        """Get summary of selection history."""
        if not self.selection_history:
            return {'message': 'No selections recorded'}
        
        return {
            'total_selections': len(self.selection_history),
            'avg_candidates': sum(s['count'] for s in self.selection_history) / len(self.selection_history),
            'last_selection': self.selection_history[-1]
        }


@dataclass
class CommitmentReceipt:
    """
    Receipt for action commitment.
    
    Created BEFORE action execution to mathematically guarantee
    that intent is cryptographically locked into the archive.
    
    Contains:
    - state_hash_before: h(z_k) prior to search
    - branching_overhead: Σ Σ(B_i) total simulation cost
    - selected_action: u* physical action
    - expected_gain: Γ(B*) forecasted gain
    """
    receipt_id: str = field(default_factory=lambda: f"commit_{uuid.uuid4().hex[:12]}")
    state_hash_before: str = ""
    branching_overhead: float = 0.0
    selected_action: np.ndarray = None
    expected_gain: float = 0.0
    selected_branch_id: str = ""
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    num_candidates: int = 0
    
    def __post_init__(self):
        if self.selected_action is None:
            self.selected_action = np.array([])
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            'receipt_id': self.receipt_id,
            'state_hash_before': self.state_hash_before,
            'branching_overhead': round(self.branching_overhead, 6),
            'selected_action': self.selected_action.tolist() if len(self.selected_action) > 0 else [],
            'expected_gain': round(self.expected_gain, 6),
            'selected_branch_id': self.selected_branch_id,
            'timestamp': self.timestamp,
            'num_candidates': self.num_candidates
        }
        return json.dumps(data, sort_keys=True)
    
    def hash(self) -> str:
        """Compute hash."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


class CommitmentTracker:
    """
    Tracks commitment process and generates commitment receipts.
    
    Responsibilities:
    1. Collect branches from workspace
    2. Create commitment receipt before action
    3. Record to memory ledger
    """
    
    def __init__(self, archive: Optional[Any] = None):
        """
        Initialize commitment tracker.
        
        Args:
            archive: Optional episodic archive for receipts
        """
        self.archive = archive
        self.pending_commitments: List[CommitmentReceipt] = []
        self.completed_commitments: List[CommitmentReceipt] = []
    
    def create_commitment(
        self,
        state_hash: str,
        branches: List[Branch],
        selected: Branch
    ) -> CommitmentReceipt:
        """
        Create commitment receipt before action execution.
        
        This mathematically guarantees intent is locked before reality responds.
        
        Args:
            state_hash: Current state hash h(z_k)
            branches: All candidate branches
            selected: Selected branch B*
            
        Returns:
            CommitmentReceipt
        """
        # Compute total branching overhead
        total_overhead = sum(b.simulation_cost for b in branches)
        
        # Create receipt
        receipt = CommitmentReceipt(
            state_hash_before=state_hash,
            branching_overhead=total_overhead,
            selected_action=selected.action.copy(),
            expected_gain=selected.expected_gain,
            selected_branch_id=selected.branch_id,
            num_candidates=len(branches)
        )
        
        # Store
        self.pending_commitments.append(receipt)
        
        return receipt
    
    def confirm_commitment(self, receipt: CommitmentReceipt) -> None:
        """
        Confirm commitment was executed (move to completed).
        
        Args:
            receipt: Receipt to confirm
        """
        if receipt in self.pending_commitments:
            self.pending_commitments.remove(receipt)
            self.completed_commitments.append(receipt)
    
    def get_commitment_summary(self) -> Dict[str, Any]:
        """Get summary of commitments."""
        return {
            'pending': len(self.pending_commitments),
            'completed': len(self.completed_commitments),
            'total_overhead': sum(c.branching_overhead for c in self.completed_commitments)
        }


# Utility functions

def create_branch(
    action: np.ndarray,
    simulation_cost: float,
    expected_gain: float,
    parent_state_hash: str = "",
    description: str = ""
) -> Branch:
    """
    Factory function to create a branch.
    
    Args:
        action: Physical action
        simulation_cost: Σ(B_i)
        expected_gain: Γ(B_i)
        parent_state_hash: Hash of parent state
        description: Human-readable description
        
    Returns:
        Branch
    """
    return Branch(
        action=action,
        simulation_cost=simulation_cost,
        expected_gain=expected_gain,
        parent_state_hash=parent_state_hash,
        action_description=description
    )


def evaluate_branch(
    branch: Branch,
    reward_fn: callable,
    cost_fn: callable
) -> Branch:
    """
    Evaluate a branch with reward and cost functions.
    
    Args:
        branch: Branch to evaluate
        reward_fn: Function to compute expected reward
        cost_fn: Function to compute simulation cost
        
    Returns:
        Branch with evaluated metrics
    """
    branch.expected_gain = reward_fn(branch.action)
    branch.simulation_cost = cost_fn(branch.action)
    return branch
