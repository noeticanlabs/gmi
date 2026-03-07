"""
Memory Receipts for the GMI Memory System.

Binds memory operations to the ledger for auditability.
All meaningful memory events must be tied into the ledger.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import hashlib
import time


@dataclass
class MemoryReceipt:
    """
    Receipt for a memory operation.
    
    All memory operations create receipts that are tied into the ledger:
    - writes create memory receipts
    - reads create memory receipts
    - replay creates memory receipts
    - branch-assisted memory operations create memory receipts
    
    This ensures:
    - auditable memory history
    - replayability
    - tamper-evidence
    """
    operation: str  # "WRITE", "READ", "REPLAY", "COMPARE", "PRUNE", "BRANCH"
    episode_ids: List[str]
    cost: float
    chain_digest: str  # Current ledger chain digest
    timestamp: float = field(default_factory=time.time)
    
    # Operation details
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Success/failure
    success: bool = True
    message: str = ""
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            'operation': self.operation,
            'episode_ids': self.episode_ids,
            'cost': round(self.cost, 6),
            'chain_digest': self.chain_digest,
            'timestamp': self.timestamp,
            'details': self.details,
            'success': self.success,
            'message': self.message
        }
        return json.dumps(data, sort_keys=True)
    
    def hash(self) -> str:
        """Compute hash of this receipt."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


class MemoryReceiptLedger:
    """
    Ledger of all memory operations.
    
    Provides:
    - Append-only storage of memory receipts
    - Verification of memory operation history
    - Integration with main ledger chain
    """
    
    def __init__(self):
        self.receipts: List[MemoryReceipt] = []
        self._current_digest = "0" * 64  # Genesis
    
    def append(self, receipt: MemoryReceipt) -> None:
        """
        Append a memory receipt to the ledger.
        
        Args:
            receipt: MemoryReceipt to append
        """
        self.receipts.append(receipt)
        # Update chain digest
        self._current_digest = receipt.hash()
    
    def create_write_receipt(
        self,
        episode_ids: List[str],
        cost: float,
        details: Optional[Dict] = None
    ) -> MemoryReceipt:
        """
        Create a receipt for a write operation.
        """
        receipt = MemoryReceipt(
            operation="WRITE",
            episode_ids=episode_ids,
            cost=cost,
            chain_digest=self._current_digest,
            details=details or {},
            success=True,
            message=f"Wrote {len(episode_ids)} episode(s)"
        )
        self.append(receipt)
        return receipt
    
    def create_read_receipt(
        self,
        episode_ids: List[str],
        cost: float,
        details: Optional[Dict] = None
    ) -> MemoryReceipt:
        """
        Create a receipt for a read operation.
        """
        receipt = MemoryReceipt(
            operation="READ",
            episode_ids=episode_ids,
            cost=cost,
            chain_digest=self._current_digest,
            details=details or {},
            success=True,
            message=f"Read {len(episode_ids)} episode(s)"
        )
        self.append(receipt)
        return receipt
    
    def create_replay_receipt(
        self,
        episode_id: str,
        cost: float,
        details: Optional[Dict] = None
    ) -> MemoryReceipt:
        """
        Create a receipt for a replay operation.
        """
        receipt = MemoryReceipt(
            operation="REPLAY",
            episode_ids=[episode_id],
            cost=cost,
            chain_digest=self._current_digest,
            details=details or {},
            success=True,
            message=f"Replayed episode {episode_id}"
        )
        self.append(receipt)
        return receipt
    
    def create_compare_receipt(
        self,
        episode_ids: List[str],
        cost: float,
        details: Optional[Dict] = None
    ) -> MemoryReceipt:
        """
        Create a receipt for a compare operation.
        """
        receipt = MemoryReceipt(
            operation="COMPARE",
            episode_ids=episode_ids,
            cost=cost,
            chain_digest=self._current_digest,
            details=details or {},
            success=True,
            message=f"Compared {len(episode_ids)} episode(s)"
        )
        self.append(receipt)
        return receipt
    
    def create_prune_receipt(
        self,
        original_count: int,
        consolidated_count: int,
        cost: float,
        details: Optional[Dict] = None
    ) -> MemoryReceipt:
        """
        Create a receipt for a prune/consolidation operation.
        """
        receipt = MemoryReceipt(
            operation="PRUNE",
            episode_ids=[],
            cost=cost,
            chain_digest=self._current_digest,
            details=details or {
                'original_count': original_count,
                'consolidated_count': consolidated_count
            },
            success=True,
            message=f"Consolidated {original_count} -> {consolidated_count} episodes"
        )
        self.append(receipt)
        return receipt
    
    def create_branch_receipt(
        self,
        base_episode_ids: List[str],
        branch_id: str,
        cost: float,
        details: Optional[Dict] = None
    ) -> MemoryReceipt:
        """
        Create a receipt for a branch operation.
        """
        receipt = MemoryReceipt(
            operation="BRANCH",
            episode_ids=base_episode_ids,
            cost=cost,
            chain_digest=self._current_digest,
            details=details or {'branch_id': branch_id},
            success=True,
            message=f"Created branch {branch_id} from {len(base_episode_ids)} episodes"
        )
        self.append(receipt)
        return receipt
    
    def get_operation_count(self, operation: str) -> int:
        """
        Get count of operations by type.
        
        Args:
            operation: Operation type
            
        Returns:
            Count of that operation type
        """
        return sum(1 for r in self.receipts if r.operation == operation)
    
    def get_total_memory_cost(self) -> float:
        """
        Get total cost of all memory operations.
        
        Returns:
            Total cost in budget units
        """
        return sum(r.cost for r in self.receipts)
    
    def verify(self) -> tuple[bool, str]:
        """
        Verify the memory receipt ledger.
        
        Returns:
            (is_valid, message)
        """
        # Check chain integrity
        for i, receipt in enumerate(self.receipts):
            if i > 0:
                expected_prev = self.receipts[i-1].hash()
                if receipt.chain_digest != expected_prev:
                    return False, f"Chain broken at receipt {i}"
        
        return True, f"Ledger verified: {len(self.receipts)} receipts"
    
    def summary(self) -> Dict[str, Any]:
        """
        Get summary of memory operations.
        
        Returns:
            Summary dict
        """
        operations = {}
        for receipt in self.receipts:
            op = receipt.operation
            if op not in operations:
                operations[op] = {'count': 0, 'total_cost': 0.0}
            operations[op]['count'] += 1
            operations[op]['total_cost'] += receipt.cost
        
        return {
            'total_receipts': len(self.receipts),
            'total_cost': self.get_total_memory_cost(),
            'operations': operations
        }
    
    def current_digest(self) -> str:
        """Get current chain digest."""
        return self._current_digest


# Global memory receipt ledger
_global_memory_ledger: Optional[MemoryReceiptLedger] = None


def get_memory_ledger() -> MemoryReceiptLedger:
    """Get or create the global memory receipt ledger."""
    global _global_memory_ledger
    if _global_memory_ledger is None:
        _global_memory_ledger = MemoryReceiptLedger()
    return _global_memory_ledger


def set_memory_ledger(ledger: MemoryReceiptLedger) -> None:
    """Set the global memory receipt ledger."""
    global _global_memory_ledger
    _global_memory_ledger = ledger
