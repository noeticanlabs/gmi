"""
Receipt Module for the GMI Universal Cognition Engine.

Provides immutable proof artifacts for state transitions with hash chain integration.
"""

import json
import struct
import hashlib
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any


@dataclass
class Receipt:
    """
    The immutable proof artifact for a single state transition.
    Must be re-checkable without re-running the inner loop.
    
    Extended with hash chain fields:
    - chain_digest_prev: H_k (previous chain digest)
    - chain_digest_next: H_{k+1} (computed)
    - state_hash_prev: Hash of state before transition
    - state_hash_next: Hash of state after transition
    - decision_code: Numeric encoding (1=ACCEPTED, 0=REJECTED, -1=HALT)
    """
    # Core fields
    step_index: int
    op_code: str
    x_hash_before: str
    x_hash_after: str
    v_before: float
    v_after: float
    sigma: float
    kappa: float
    budget_before: float
    budget_after: float
    is_composite: bool
    decision: str       # "ACCEPTED", "REJECTED", or "HALT"
    message: str
    
    # NEW: Hash chain fields
    chain_digest_prev: str = ""      # H_k
    chain_digest_next: str = ""      # H_{k+1} (computed)
    state_hash_prev: str = ""        # Explicit state hash before
    state_hash_next: str = ""        # Explicit state hash after
    decision_code: int = 0           # Numeric encoding: 1=ACCEPTED, 0=REJECTED, -1=HALT
    
    # Additional metadata
    timestamp: float = 0.0
    potential_fn_hash: str = ""      # Hash of potential function config
    
    def __post_init__(self):
        """Set derived fields."""
        if not self.decision_code:
            self.decision_code = self._compute_decision_code()
    
    def _compute_decision_code(self) -> int:
        """Compute numeric decision code."""
        mapping = {"ACCEPTED": 1, "REJECTED": 0, "HALT": -1}
        return mapping.get(self.decision, 0)
    
    def to_json(self) -> str:
        """Serializes the receipt for the cryptographic ledger log."""
        return json.dumps(asdict(self), sort_keys=True)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Receipt':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)
    
    def canonical_encoding(self) -> bytes:
        """
        Deterministic binary encoding for cryptographic operations.
        All numeric values encoded as fixed-width integers.
        
        This is used for computing chain digests.
        """
        # Encode decision as int
        decision_int = self.decision_code
        
        # Build canonical byte string
        data = [
            struct.pack(">I", self.step_index),           # 4 bytes
            self.op_code.encode('utf-8').ljust(32, b'\0'), # 32 bytes
            self.x_hash_before.encode('utf-8'),            # 64 bytes (hex = 32 bytes)
            self.x_hash_after.encode('utf-8'),             # 64 bytes
            struct.pack(">d", self.v_before),             # 8 bytes
            struct.pack(">d", self.v_after),               # 8 bytes
            struct.pack(">d", self.sigma),                # 8 bytes
            struct.pack(">d", self.kappa),                # 8 bytes
            struct.pack(">d", self.budget_before),         # 8 bytes
            struct.pack(">d", self.budget_after),         # 8 bytes
            struct.pack("?", self.is_composite),           # 1 byte
            struct.pack("b", decision_int),               # 1 byte
        ]
        
        return b"".join(data)
    
    def compute_hash(self) -> str:
        """Compute deterministic hash of this receipt."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()
    
    def verify(self, expected_potential_fn) -> tuple[bool, str]:
        """
        Verify this receipt is consistent.
        
        Args:
            expected_potential_fn: The potential function that was used
            
        Returns:
            (is_valid, message)
        """
        # Check decision code consistency
        if self.decision_code != self._compute_decision_code():
            return False, "Decision code mismatch"
        
        # Check potential values are reasonable
        if self.v_before < 0 or self.v_after < 0:
            return False, "Negative potential values"
        
        # Check budget consistency
        expected_budget_after = self.budget_before - self.sigma
        if abs(self.budget_after - expected_budget_after) > 1e-6:
            return False, f"Budget mismatch: expected {expected_budget_after}, got {self.budget_after}"
        
        return True, "Receipt valid"
    
    def summary(self) -> Dict[str, Any]:
        """Get receipt summary."""
        return {
            'step': self.step_index,
            'op': self.op_code,
            'decision': self.decision,
            'v_before': round(self.v_before, 4),
            'v_after': round(self.v_after, 4),
            'sigma': self.sigma,
            'kappa': self.kappa,
            'budget_before': round(self.budget_before, 4),
            'budget_after': round(self.budget_after, 4),
            'chain_digest': self.chain_digest_next[:16] + "..." if self.chain_digest_next else ""
        }


def create_receipt_from_verifier(
    step_index: int,
    op_code: str,
    x_hash_before: str,
    x_hash_after: str,
    v_before: float,
    v_after: float,
    sigma: float,
    kappa: float,
    budget_before: float,
    budget_after: float,
    is_composite: bool,
    decision: str,
    message: str,
    chain_digest_prev: str = "",
    state_hash_prev: str = "",
    state_hash_next: str = ""
) -> Receipt:
    """
    Factory function to create a receipt from verifier results.
    
    Args:
        step_index: Current step number
        op_code: Operation code
        x_hash_before: Hash of state before
        x_hash_after: Hash of state after
        v_before: Potential before
        v_after: Potential after
        sigma: Metabolic cost
        kappa: Allowed defect
        budget_before: Budget before
        budget_after: Budget after
        is_composite: Whether this is a composite instruction
        decision: Decision string
        message: Message
        chain_digest_prev: Previous chain digest
        state_hash_prev: Previous state hash
        state_hash_next: Next state hash
        
    Returns:
        Receipt
    """
    return Receipt(
        step_index=step_index,
        op_code=op_code,
        x_hash_before=x_hash_before,
        x_hash_after=x_hash_after,
        v_before=v_before,
        v_after=v_after,
        sigma=sigma,
        kappa=kappa,
        budget_before=budget_before,
        budget_after=budget_after,
        is_composite=is_composite,
        decision=decision,
        message=message,
        chain_digest_prev=chain_digest_prev,
        state_hash_prev=state_hash_prev,
        state_hash_next=state_hash_next
    )
