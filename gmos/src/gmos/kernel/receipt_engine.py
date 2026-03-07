"""
Receipt Engine for GM-OS Kernel.

Builds canonical receipts for kernel events, serializes receipt payloads,
interfaces with hash chain.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import uuid
import time


class ReceiptType(Enum):
    """Types of kernel receipts."""
    TRANSITION = "transition"
    BUDGET = "budget"
    HALT = "halt"
    TORPOR = "torpor"
    WAKE = "wake"
    ROUTING = "routing"


@dataclass
class KernelReceipt:
    """Canonical receipt for kernel events."""
    receipt_id: str
    receipt_type: ReceiptType
    process_id: str
    step_index: int
    state_hash_prev: str
    state_hash_next: str
    budget_prev: float
    budget_next: float
    decision_code: int  # 1=accepted, 0=rejected, -1=halt
    chain_digest_prev: str
    chain_digest_next: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "receipt_id": self.receipt_id,
            "receipt_type": self.receipt_type.value,
            "process_id": self.process_id,
            "step_index": self.step_index,
            "state_hash_prev": self.state_hash_prev,
            "state_hash_next": self.state_hash_next,
            "budget_prev": self.budget_prev,
            "budget_next": self.budget_next,
            "decision_code": self.decision_code,
            "chain_digest_prev": self.chain_digest_prev,
            "chain_digest_next": self.chain_digest_next,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class ReceiptEngine:
    """
    Generates canonical receipts for kernel events.
    
    Receipt fields:
    - receipt_id
    - receipt_type
    - process_id
    - step_index
    - state_hash_prev
    - state_hash_next
    - budget_prev
    - budget_next
    - decision_code
    - chain_digest_prev
    - chain_digest_next
    - metadata
    """
    
    def __init__(self, hash_chain=None):
        self._hash_chain = hash_chain
    
    def make_transition_receipt(
        self,
        process_id: str,
        step_index: int,
        state_hash_prev: str,
        state_hash_next: str,
        budget_prev: float,
        budget_next: float,
        decision_code: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KernelReceipt:
        """Create a state transition receipt."""
        chain_prev = self._chain_digest() if self._hash_chain else "genesis"
        
        receipt = KernelReceipt(
            receipt_id=str(uuid.uuid4())[:8],
            receipt_type=ReceiptType.TRANSITION,
            process_id=process_id,
            step_index=step_index,
            state_hash_prev=state_hash_prev,
            state_hash_next=state_hash_next,
            budget_prev=budget_prev,
            budget_next=budget_next,
            decision_code=decision_code,
            chain_digest_prev=chain_prev,
            chain_digest_next="",  # Will be updated after chain append
            metadata=metadata or {}
        )
        
        if self._hash_chain:
            receipt.chain_digest_next = self._hash_chain.append(receipt)
        
        return receipt
    
    def make_budget_receipt(
        self,
        process_id: str,
        budget_prev: float,
        budget_next: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KernelReceipt:
        """Create a budget change receipt."""
        chain_prev = self._chain_digest() if self._hash_chain else "genesis"
        
        receipt = KernelReceipt(
            receipt_id=str(uuid.uuid4())[:8],
            receipt_type=ReceiptType.BUDGET,
            process_id=process_id,
            step_index=0,
            state_hash_prev="",
            state_hash_next="",
            budget_prev=budget_prev,
            budget_next=budget_next,
            decision_code=1,
            chain_digest_prev=chain_prev,
            chain_digest_next="",
            metadata=metadata or {}
        )
        
        if self._hash_chain:
            receipt.chain_digest_next = self._hash_chain.append(receipt)
        
        return receipt
    
    def make_halt_receipt(
        self,
        process_id: str,
        step_index: int,
        state_hash: str,
        budget: float
    ) -> KernelReceipt:
        """Create a halt receipt (no lawful move)."""
        return self.make_transition_receipt(
            process_id=process_id,
            step_index=step_index,
            state_hash_prev=state_hash,
            state_hash_next=state_hash,
            budget_prev=budget,
            budget_next=budget,
            decision_code=-1,
            metadata={"reason": "no_lawful_move"}
        )
    
    def make_torpor_receipt(
        self,
        process_id: str,
        step_index: int,
        state_hash: str,
        budget: float
    ) -> KernelReceipt:
        """Create a torpor receipt (budget depleted)."""
        return self.make_transition_receipt(
            process_id=process_id,
            step_index=step_index,
            state_hash_prev=state_hash,
            state_hash_next=state_hash,
            budget_prev=budget,
            budget_next=0.0,
            decision_code=-1,
            metadata={"reason": "budget_depleted"}
        )
    
    def make_wake_receipt(
        self,
        process_id: str,
        state_hash: str,
        budget: float
    ) -> KernelReceipt:
        """Create a wake receipt (replenishment received)."""
        return self.make_transition_receipt(
            process_id=process_id,
            step_index=0,
            state_hash_prev=state_hash,
            state_hash_next=state_hash,
            budget_prev=0.0,
            budget_next=budget,
            decision_code=1,
            metadata={"reason": "replenishment"}
        )
    
    def canonical_payload(self, receipt: KernelReceipt) -> bytes:
        """Serialize receipt to canonical bytes."""
        import json
        return json.dumps(receipt.to_dict(), sort_keys=True).encode()
    
    def _chain_digest(self) -> str:
        """Get current chain digest."""
        if self._hash_chain:
            return self._hash_chain.current_digest
        return "genesis"
