"""
GMI Receipt Schemas

Canonical receipt schemas for GMI operation types.
Each schema includes all fields needed for verification.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time


class GMIReceiptType(Enum):
    """GMI receipt types."""
    INFER = "gmi.receipt.infer.v1"
    RETRIEVE = "gmi.receipt.retrieve.v1"
    REPAIR = "gmi.receipt.repair.v1"
    BRANCH = "gmi.receipt.branch.v1"
    PLAN = "gmi.receipt.plan.v1"
    ACT_PREPARE = "gmi.receipt.act_prepare.v1"


@dataclass
class GMIReceipt:
    """Base GMI receipt with common fields."""
    schema_id: str
    version: str = "v1"
    process_id: str = ""
    step: int = 0
    mode: str = ""
    state_hash_prev: str = ""
    state_hash_next: str = ""
    chain_digest_prev: str = ""
    chain_digest_next: str = ""
    timestamp: float = field(default_factory=time.time)
    spend_summary: float = 0.0
    defect_summary: float = 0.0
    anchor_summary: float = 0.0
    contradiction_summary: float = 0.0
    goal_summary: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'schema_id': self.schema_id,
            'version': self.version,
            'process_id': self.process_id,
            'step': self.step,
            'mode': self.mode,
            'state_hash_prev': self.state_hash_prev,
            'state_hash_next': self.state_hash_next,
            'chain_digest_prev': self.chain_digest_prev,
            'chain_digest_next': self.chain_digest_next,
            'timestamp': self.timestamp,
            'spend_summary': self.spend_summary,
            'defect_summary': self.defect_summary,
            'anchor_summary': self.anchor_summary,
            'contradiction_summary': self.contradiction_summary,
            'goal_summary': self.goal_summary,
            'metrics': self.metrics,
            'payload': self.payload,
        }


@dataclass
class InferReceipt(GMIReceipt):
    """Receipt for inference operation."""
    def __init__(self, **kwargs):
        super().__init__(schema_id=GMIReceiptType.INFER.value, **kwargs)
        self.schema_id = GMIReceiptType.INFER.value


@dataclass
class RetrieveReceipt(GMIReceipt):
    """Receipt for memory retrieval operation."""
    def __init__(self, **kwargs):
        super().__init__(schema_id=GMIReceiptType.RETRIEVE.value, **kwargs)
        self.schema_id = GMIReceiptType.RETRIEVE.value


@dataclass
class RepairReceipt(GMIReceipt):
    """Receipt for repair operation."""
    def __init__(self, **kwargs):
        super().__init__(schema_id=GMIReceiptType.REPAIR.value, **kwargs)
        self.schema_id = GMIReceiptType.REPAIR.value


@dataclass
class BranchReceipt(GMIReceipt):
    """Receipt for branch selection operation."""
    def __init__(self, **kwargs):
        super().__init__(schema_id=GMIReceiptType.BRANCH.value, **kwargs)
        self.schema_id = GMIReceiptType.BRANCH.value


@dataclass
class PlanReceipt(GMIReceipt):
    """Receipt for planning operation."""
    def __init__(self, **kwargs):
        super().__init__(schema_id=GMIReceiptType.PLAN.value, **kwargs)
        self.schema_id = GMIReceiptType.PLAN.value


@dataclass
class ActPrepareReceipt(GMIReceipt):
    """Receipt for action preparation operation."""
    def __init__(self, **kwargs):
        super().__init__(schema_id=GMIReceiptType.ACT_PREPARE.value, **kwargs)
        self.schema_id = GMIReceiptType.ACT_PREPARE.value


# Factory function
def create_receipt(receipt_type: GMIReceiptType, **kwargs) -> GMIReceipt:
    """Create a receipt of the specified type."""
    receipt_classes = {
        GMIReceiptType.INFER: InferReceipt,
        GMIReceiptType.RETRIEVE: RetrieveReceipt,
        GMIReceiptType.REPAIR: RepairReceipt,
        GMIReceiptType.BRANCH: BranchReceipt,
        GMIReceiptType.PLAN: PlanReceipt,
        GMIReceiptType.ACT_PREPARE: ActPrepareReceipt,
    }
    cls = receipt_classes.get(receipt_type)
    if cls is None:
        raise ValueError(f"Unknown receipt type: {receipt_type}")
    return cls(**kwargs)


# Schema validation
def validate_receipt(data: Dict[str, Any]) -> bool:
    """Validate a receipt has required fields."""
    required = ['schema_id', 'version', 'process_id', 'step', 'state_hash_prev', 'state_hash_next']
    for field in required:
        if field not in data:
            return False
    return True
