"""
Commitment for GM-OS Action Layer.

Defines external action commitment interface, kernel-facing action commit API.
Budget-aware commitment that integrates with BudgetRouter.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import uuid
import time


@dataclass
class ActionCommitment:
    """Committed action record with budget tracking."""
    action_id: str
    process_id: str
    action_type: str
    parameters: Dict[str, Any]
    budget_spent: float
    budget_remaining: float
    timestamp: float = field(default_factory=time.time)
    status: str = "pending"  # pending, committed, executed, failed


@dataclass 
class CommitmentReceipt:
    """Cryptographic proof of action commitment."""
    receipt_id: str = field(default_factory=lambda: f"commit_{uuid.uuid4().hex[:12]}")
    action_id: str = ""
    process_id: str = ""
    state_hash_before: str = ""
    state_hash_after: str = ""
    budget_allocated: float = 0.0
    budget_spent: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'receipt_id': self.receipt_id,
            'action_id': self.action_id,
            'process_id': self.process_id,
            'state_hash_before': self.state_hash_before,
            'state_hash_after': self.state_hash_after,
            'budget_allocated': self.budget_allocated,
            'budget_spent': self.budget_spent,
            'timestamp': self.timestamp,
        }


class CommitmentManager:
    """
    Manages action commitments with budget awareness.
    
    Integrates with BudgetRouter for proper budget allocation and tracking.
    """
    
    def __init__(self, budget_router=None):
        """
        Initialize commitment manager.
        
        Args:
            budget_router: Optional BudgetRouter for budget tracking
        """
        self.budget_router = budget_router
        self.pending_commitments: List[ActionCommitment] = []
        self.completed_commitments: List[ActionCommitment] = []
        self.failed_commitments: List[ActionCommitment] = []
    
    def commit_action(
        self,
        process_id: str,
        action: Dict[str, Any],
        budget: float,
        budget_layer: int = 0,
    ) -> ActionCommitment:
        """
        Commit an action with budget allocation.
        
        Args:
            process_id: ID of the process committing the action
            action: Action parameters
            budget: Requested budget for the action
            budget_layer: Budget layer (0=process, 1+=nested)
            
        Returns:
            ActionCommitment with budget tracking
        """
        action_id = f"action_{uuid.uuid4().hex[:12]}"
        
        # Check budget availability if router is available
        if self.budget_router:
            can_spend = self.budget_router.can_spend(process_id, budget_layer, budget)
            if not can_spend:
                # Create failed commitment
                commitment = ActionCommitment(
                    action_id=action_id,
                    process_id=process_id,
                    action_type=action.get('type', 'unknown'),
                    parameters=action,
                    budget_spent=0.0,
                    budget_remaining=0.0,
                    status="failed",
                )
                self.failed_commitments.append(commitment)
                return commitment
            
            # Allocate budget
            allocated = self.budget_router.get_budget(process_id, budget_layer) or 0.0
            budget_remaining = allocated - budget
        else:
            budget_remaining = budget
        
        # Create commitment
        commitment = ActionCommitment(
            action_id=action_id,
            process_id=process_id,
            action_type=action.get('type', 'unknown'),
            parameters=action,
            budget_spent=0.0,
            budget_remaining=budget_remaining,
            status="committed",
        )
        
        self.pending_commitments.append(commitment)
        return commitment
    
    def execute_action(self, action_id: str, actual_cost: float) -> bool:
        """
        Mark an action as executed and update budget.
        
        Args:
            action_id: ID of the action to execute
            actual_cost: Actual cost incurred
            
        Returns:
            True if successful, False otherwise
        """
        # Find pending commitment
        commitment = None
        for c in self.pending_commitments:
            if c.action_id == action_id:
                commitment = c
                break
        
        if not commitment:
            return False
        
        # Update budget if router available
        if self.budget_router:
            success = self.budget_router.apply_spend(
                commitment.process_id, 
                0,  # layer
                actual_cost
            )
            if not success:
                commitment.status = "failed"
                self.failed_commitments.append(commitment)
                self.pending_commitments.remove(commitment)
                return False
        
        # Update commitment
        commitment.budget_spent = actual_cost
        commitment.budget_remaining = commitment.budget_remaining - actual_cost
        commitment.status = "executed"
        
        self.completed_commitments.append(commitment)
        self.pending_commitments.remove(commitment)
        
        return True
    
    def get_pending(self, process_id: Optional[str] = None) -> List[ActionCommitment]:
        """Get pending commitments, optionally filtered by process."""
        if process_id:
            return [c for c in self.pending_commitments if c.process_id == process_id]
        return self.pending_commitments.copy()
    
    def get_completed(self, process_id: Optional[str] = None) -> List[ActionCommitment]:
        """Get completed commitments, optionally filtered by process."""
        if process_id:
            return [c for c in self.completed_commitments if c.process_id == process_id]
        return self.completed_commitments.copy()


# Backwards compatibility function
def commit_action(
    process_id: str,
    action: Dict[str, Any],
    budget: float
) -> ActionCommitment:
    """Commit an action for execution."""
    manager = CommitmentManager()
    return manager.commit_action(process_id, action, budget)
