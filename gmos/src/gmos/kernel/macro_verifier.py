"""
Macro Verifier for GM-OS Kernel.

Verifies slabs / macro summaries instead of every microstep individually,
supports oplax roll-up verification.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import hashlib
import json


@dataclass
class SlabReceipt:
    """Receipt summarizing a batch of micro-receipts."""
    slab_id: str
    start_step: int
    end_step: int
    process_id: str
    receipts: List[Dict[str, Any]] = field(default_factory=list)
    total_spend: float = 0.0
    total_defect: float = 0.0
    slab_hash: str = ""
    
    def __post_init__(self):
        if not self.slab_hash:
            self.slab_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash of slab contents."""
        content = {
            "slab_id": self.slab_id,
            "start_step": self.start_step,
            "end_step": self.end_step,
            "process_id": self.process_id,
            "total_spend": self.total_spend,
            "total_defect": self.total_defect,
            "receipts": self.receipts
        }
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]


class MacroVerifier:
    """
    Verifies macro slabs and oplax roll-ups.
    
    Key law enforced:
    Spend(Slab) <= sum(Spend(receipt_k))
    
    This ensures subadditivity of verification cost.
    """
    
    def __init__(self):
        self._verified_slabs: Dict[str, SlabReceipt] = {}
    
    def build_slab(
        self,
        slab_id: str,
        process_id: str,
        start_step: int,
        end_step: int,
        micro_receipts: List[Dict[str, Any]]
    ) -> SlabReceipt:
        """Build a slab receipt from micro-receipts."""
        total_spend = sum(r.get("spend", 0.0) for r in micro_receipts)
        total_defect = sum(r.get("defect", 0.0) for r in micro_receipts)
        
        slab = SlabReceipt(
            slab_id=slab_id,
            start_step=start_step,
            end_step=end_step,
            process_id=process_id,
            receipts=micro_receipts,
            total_spend=total_spend,
            total_defect=total_defect
        )
        
        return slab
    
    def verify_slab(self, slab: SlabReceipt) -> bool:
        """Verify a slab receipt."""
        # Check all micro receipts are present
        if len(slab.receipts) != (slab.end_step - slab.start_step + 1):
            return False
        
        # Verify hash
        expected_hash = slab._compute_hash()
        if slab.slab_hash != expected_hash:
            return False
        
        # Verify oplax bound
        if not self.verify_oplax_bound(slab):
            return False
        
        self._verified_slabs[slab.slab_id] = slab
        return True
    
    def summarize_spend(self, slab: SlabReceipt) -> float:
        """Get total spend for slab."""
        return slab.total_spend
    
    def summarize_defect(self, slab: SlabReceipt) -> float:
        """Get total defect for slab."""
        return slab.total_defect
    
    def verify_oplax_bound(self, slab: SlabReceipt) -> bool:
        """
        Verify subadditive spend law:
        Spend(Slab) <= sum(Spend(receipt_k))
        
        In practice, this means slab totals should equal or be less than
        the sum of individual receipt values.
        """
        # Compute from individual receipts
        computed_spend = sum(r.get("spend", 0.0) for r in slab.receipts)
        computed_defect = sum(r.get("defect", 0.0) for r in slab.receipts)
        
        # Slab should not claim more than sum of parts
        return (
            slab.total_spend <= computed_spend + 1e-6 and
            slab.total_defect <= computed_defect + 1e-6
        )
