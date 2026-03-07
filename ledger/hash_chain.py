"""
Hash Chain Ledger for the GMI Universal Cognition Engine.

Provides cryptographic execution chain where every accepted transition is chained:

H_{k+1} = SHA256(H_k || receipt_k)

The verifier validates not only "was this step legal?" but also:
- Does it point to the correct previous state hash?
- Does it point to the correct previous receipt hash?
- Is the chain deterministic under replay?
- Can a slab summary be checked against the underlying micro receipts?
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple, Any
from enum import Enum


class DecisionCode(Enum):
    """Canonical numeric encoding for decisions."""
    ACCEPTED = 1
    REJECTED = 0
    HALT = -1
    
    @classmethod
    def from_string(cls, s: str) -> 'DecisionCode':
        mapping = {
            "ACCEPTED": cls.ACCEPTED,
            "REJECTED": cls.REJECTED,
            "HALT": cls.HALT
        }
        return mapping.get(s, cls.REJECTED)
    
    def to_int(self) -> int:
        return self.value


@dataclass
class ChainDigest:
    """
    Cryptographic anchor for the ledger chain.
    Links state hashes and receipt hashes into an immutable history.
    
    H_{k+1} = SHA256(H_k || receipt_k || state_next)
    """
    step_index: int
    state_hash_prev: str
    state_hash_next: str
    receipt_hash: str
    chain_digest_prev: str   # H_k
    chain_digest_next: str    # H_{k+1}
    decision_code: str        # "ACCEPTED" | "REJECTED" | "HALT"
    timestamp: float = field(default_factory=time.time)
    
    # Additional metadata
    op_code: str = ""
    potential_before: float = 0.0
    potential_after: float = 0.0
    sigma: float = 0.0
    kappa: float = 0.0
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            'step_index': self.step_index,
            'state_hash_prev': self.state_hash_prev,
            'state_hash_next': self.state_hash_next,
            'receipt_hash': self.receipt_hash,
            'chain_digest_prev': self.chain_digest_prev,
            'chain_digest_next': self.chain_digest_next,
            'decision_code': self.decision_code,
            'timestamp': self.timestamp,
            'op_code': self.op_code,
            'potential_before': round(self.potential_before, 6),
            'potential_after': round(self.potential_after, 6),
            'sigma': round(self.sigma, 6),
            'kappa': round(self.kappa, 6)
        }
        return json.dumps(data, sort_keys=True)
    
    @staticmethod
    def compute(
        prev_digest: str, 
        receipt_json: str, 
        state_hash_next: str
    ) -> str:
        """
        Compute next chain digest: SHA256(H_k || receipt_k || state_next)
        
        Args:
            prev_digest: H_k (previous chain digest)
            receipt_json: Serialized receipt
            state_hash_next: Hash of state after transition
            
        Returns:
            H_{k+1}
        """
        payload = f"{prev_digest}|{receipt_json}|{state_hash_next}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()
    
    def hash(self) -> str:
        """Compute hash of this digest record."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


@dataclass
class SlabSummary:
    """
    Summary of a slab (range) of the ledger.
    Enables efficient partial verification.
    """
    start_step: int
    end_step: int
    chain_digest_start: str   # H_start-1
    chain_digest_end: str     # H_end
    num_receipts: int
    slab_hash: str           # Hash of all receipts in slab
    first_receipt_hash: str
    last_receipt_hash: str
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)
    
    def verify(self, receipts: List[Any]) -> Tuple[bool, str]:
        """
        Verify slab against actual receipts.
        
        Args:
            receipts: List of receipts in this slab range
            
        Returns:
            (is_valid, message)
        """
        if len(receipts) != self.num_receipts:
            return False, f"Receipt count mismatch: expected {self.num_receipts}, got {len(receipts)}"
        
        # Compute expected slab hash
        combined = "".join(r.to_json() if hasattr(r, 'to_json') else str(r) for r in receipts)
        expected_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        if expected_hash != self.slab_hash:
            return False, "Slab hash mismatch"
        
        return True, "Slab verified"


class HashChainLedger:
    """
    Immutable cryptographic ledger with hash chaining.
    Enables offline replay and verification of entire execution history.
    
    Each entry links:
    - Previous state hash
    - Next state hash  
    - Receipt hash
    - Previous chain digest
    - Next chain digest (computed)
    """
    
    GENESIS_HASH = "0" * 64  # SHA256 of empty string
    
    def __init__(self):
        self.chain: List[ChainDigest] = []
        self.receipts: List[Any] = []
        self.state_hashes: List[str] = []
        self._current_digest = self.GENESIS_HASH
        
        # Statistics
        self.accepted_count = 0
        self.rejected_count = 0
        self.halt_count = 0
    
    def append(
        self, 
        receipt: Any, 
        state_hash_next: str,
        include_in_chain: bool = True
    ) -> ChainDigest:
        """
        Append a new step to the chain.
        
        Args:
            receipt: Receipt for this step
            state_hash_next: Hash of state after transition
            include_in_chain: Whether to include in chain verification
            
        Returns:
            ChainDigest for this step
        """
        step_idx = len(self.chain)
        
        # Get previous hashes
        prev_state_hash = (
            self.state_hashes[-1] 
            if self.state_hashes else self.GENESIS_HASH
        )
        
        prev_digest = (
            self.chain[-1].chain_digest_next 
            if self.chain else self.GENESIS_HASH
        )
        
        # Get receipt hash
        receipt_json = receipt.to_json() if hasattr(receipt, 'to_json') else str(receipt)
        receipt_hash = hashlib.sha256(receipt_json.encode()).hexdigest()
        
        # Compute chain digest
        chain_digest_next = ChainDigest.compute(
            prev_digest, 
            receipt_json, 
            state_hash_next
        )
        
        # Create chain record
        chain_record = ChainDigest(
            step_index=step_idx,
            state_hash_prev=prev_state_hash,
            state_hash_next=state_hash_next,
            receipt_hash=receipt_hash,
            chain_digest_prev=prev_digest,
            chain_digest_next=chain_digest_next,
            decision_code=getattr(receipt, 'decision', 'UNKNOWN'),
            op_code=getattr(receipt, 'op_code', ''),
            potential_before=getattr(receipt, 'v_before', 0.0),
            potential_after=getattr(receipt, 'v_after', 0.0),
            sigma=getattr(receipt, 'sigma', 0.0),
            kappa=getattr(receipt, 'kappa', 0.0)
        )
        
        if include_in_chain:
            self.chain.append(chain_record)
            self.receipts.append(receipt)
            self.state_hashes.append(state_hash_next)
            
            # Update statistics
            decision = chain_record.decision_code
            if decision == "ACCEPTED":
                self.accepted_count += 1
            elif decision == "REJECTED":
                self.rejected_count += 1
            else:
                self.halt_count += 1
        
        # Update current digest
        self._current_digest = chain_digest_next
        
        return chain_record
    
    def verify_chain(self) -> Tuple[bool, str]:
        """
        Verify entire chain integrity via replay.
        
        Returns:
            (is_valid, message)
        """
        if not self.chain:
            return True, "Empty chain"
        
        current_digest = self.GENESIS_HASH
        
        for i, record in enumerate(self.chain):
            # Verify digest links
            receipt_json = self.receipts[i].to_json() if hasattr(self.receipts[i], 'to_json') else str(self.receipts[i])
            expected_next = ChainDigest.compute(
                current_digest,
                receipt_json,
                record.state_hash_next
            )
            
            if expected_next != record.chain_digest_next:
                return False, f"Chain integrity failed at step {i}"
            
            # Verify state hash continuity
            if i > 0:
                if record.state_hash_prev != self.state_hashes[i-1]:
                    return False, f"State hash discontinuity at step {i}"
            
            current_digest = record.chain_digest_next
        
        return True, f"Chain verified: {len(self.chain)} steps"
    
    def get_slab_summary(self, start: int, end: int) -> SlabSummary:
        """
        Generate a summary of a slab (range) of the ledger.
        
        Args:
            start: Start step index (inclusive)
            end: End step index (exclusive)
            
        Returns:
            SlabSummary
        """
        if start < 0 or end > len(self.chain):
            raise ValueError(f"Invalid slab range: {start}-{end}")
        
        receipts = self.receipts[start:end]
        
        # Compute slab hash
        combined = "".join(
            r.to_json() if hasattr(r, 'to_json') else str(r) 
            for r in receipts
        )
        slab_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return SlabSummary(
            start_step=start,
            end_step=end,
            chain_digest_start=(
                self.chain[start-1].chain_digest_next 
                if start > 0 else self.GENESIS_HASH
            ),
            chain_digest_end=self.chain[end-1].chain_digest_next,
            num_receipts=len(receipts),
            slab_hash=slab_hash,
            first_receipt_hash=self.chain[start].receipt_hash if start < len(self.chain) else "",
            last_receipt_hash=self.chain[end-1].receipt_hash if end > 0 else ""
        )
    
    def verify_slab(self, start: int, end: int) -> Tuple[bool, str]:
        """
        Verify a specific slab of the ledger.
        
        Args:
            start: Start step index
            end: End step index
            
        Returns:
            (is_valid, message)
        """
        summary = self.get_slab_summary(start, end)
        receipts = self.receipts[start:end]
        return summary.verify(receipts)
    
    def get_state_hash_at(self, step: int) -> Optional[str]:
        """Get state hash at a specific step."""
        if 0 <= step < len(self.state_hashes):
            return self.state_hashes[step]
        return None
    
    def get_receipt_at(self, step: int) -> Optional[Any]:
        """Get receipt at a specific step."""
        if 0 <= step < len(self.receipts):
            return self.receipts[step]
        return None
    
    def current_digest(self) -> str:
        """Get current chain digest (H_k)."""
        return self._current_digest
    
    def current_state_hash(self) -> str:
        """Get current state hash."""
        if self.state_hashes:
            return self.state_hashes[-1]
        return self.GENESIS_HASH
    
    def summary(self) -> Dict[str, Any]:
        """Get ledger summary."""
        return {
            'total_steps': len(self.chain),
            'accepted': self.accepted_count,
            'rejected': self.rejected_count,
            'halted': self.halt_count,
            'current_digest': self._current_digest,
            'current_state_hash': self.current_state_hash()
        }
    
    def save(self, path: str) -> None:
        """Save ledger to disk."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = {
            'chain': [json.loads(c.to_json()) for c in self.chain],
            'receipts': [r.to_json() if hasattr(r, 'to_json') else str(r) for r in self.receipts],
            'state_hashes': self.state_hashes,
            'statistics': {
                'accepted': self.accepted_count,
                'rejected': self.rejected_count,
                'halted': self.halt_count
            }
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'HashChainLedger':
        """Load ledger from disk."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        ledger = cls()
        
        # Reconstruct chain
        for chain_data in data.get('chain', []):
            digest = ChainDigest(
                step_index=chain_data['step_index'],
                state_hash_prev=chain_data['state_hash_prev'],
                state_hash_next=chain_data['state_hash_next'],
                receipt_hash=chain_data['receipt_hash'],
                chain_digest_prev=chain_data['chain_digest_prev'],
                chain_digest_next=chain_data['chain_digest_next'],
                decision_code=chain_data['decision_code'],
                timestamp=chain_data.get('timestamp', 0.0),
                op_code=chain_data.get('op_code', ''),
                potential_before=chain_data.get('potential_before', 0.0),
                potential_after=chain_data.get('potential_after', 0.0),
                sigma=chain_data.get('sigma', 0.0),
                kappa=chain_data.get('kappa', 0.0)
            )
            ledger.chain.append(digest)
        
        ledger.state_hashes = data.get('state_hashes', [])
        
        stats = data.get('statistics', {})
        ledger.accepted_count = stats.get('accepted', 0)
        ledger.rejected_count = stats.get('rejected', 0)
        ledger.halt_count = stats.get('halted', 0)
        
        # Set current digest
        if ledger.chain:
            ledger._current_digest = ledger.chain[-1].chain_digest_next
        
        return ledger


# Global ledger instance
_global_ledger: Optional[HashChainLedger] = None


def get_global_ledger() -> HashChainLedger:
    """Get or create the global hash chain ledger."""
    global _global_ledger
    if _global_ledger is None:
        _global_ledger = HashChainLedger()
    return _global_ledger


def set_global_ledger(ledger: HashChainLedger) -> None:
    """Set the global hash chain ledger."""
    global _global_ledger
    _global_ledger = ledger
