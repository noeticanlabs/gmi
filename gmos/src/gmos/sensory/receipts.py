"""
Sensory Receipt Schema for Dual-Use Sensory Substrate.

Per spec §15: Canonical receipt schema for sensory observation steps.
This module defines the receipt structure that all sensory operations
must produce for Coh verification.

The sensory substrate is a governed object that:
1. Acquires world observations (GM-OS role)
2. Transforms them into forcing terms for GMI (organism role)

All observation steps must be receipt-verified under the frozen Coh canon.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time
import hashlib
import json


# === Schema Constants ===

SCHEMA_ID = "receipt_sensory_micro.v1"
OBJECT_ID = "gmos.sensory.substrate.core.v1"
VERSION = "v1"


# === Source Tags (per spec §7) ===

class SourceTag(Enum):
    """Valid source tags for sensory percepts."""
    EXTERNAL = "ext"      # Externally validated
    INTERNAL = "int"      # Internal/interoceptive
    MEMORY = "mem"        # Memory replay
    SIMULATION = "sim"    # Internal simulation


# === Step Types ===

class StepType(Enum):
    """Types of sensory observation steps."""
    OBSERVE = "OBSERVE"
    FUSE = "FUSE"
    ANCHOR = "ANCHOR"
    SALIENCE = "SALIENCE"
    INGRESS = "INGRESS"


# === Verdict ===

class Verdict(Enum):
    """Accept/reject verdict for sensory receipt."""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


# === Reject Codes ===

class RejectCode(Enum):
    """Rejection codes for sensory receipt verification."""
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_HASH = "INVALID_HASH"
    INVALID_CHAIN = "INVALID_CHAIN"
    INVALID_SOURCE_TAG = "INVALID_SOURCE_TAG"
    INVALID_NUMERIC = "INVALID_NUMERIC"
    COST_NOT_POSITIVE = "COST_NOT_POSITIVE"
    SALIENCE_OUT_OF_BOUNDS = "SALIENCE_OUT_OF_BOUNDS"
    ANCHOR_MISMATCH = "ANCHOR_MISMATCH"


# === Sensory Receipt ===

@dataclass
class SensoryReceipt:
    """
    Canonical sensory receipt per spec §15.
    
    This is the primary artifact proving that a sensory observation
    step was performed lawfully under the dual-use substrate.
    
    Attributes:
        schema_id: Receipt schema identifier
        object_id: Object this receipt is for
        canon_profile_hash: Hash of canonical profile
        policy_hash: Hash of governance policy
        step_type: Type of observation step
        step_index: Sequential step number
        chain_digest_prev: Previous chain digest
        chain_digest_next: Computed chain digest
        state_hash_prev: Previous state hash
        state_hash_next: New state hash
        source_tag: Source of percept (ext/int/mem/sim)
        authority_weight: Authority score [0,1]
        quality_score: Quality/confidence [0,1]
        salience_score: Computed salience [0,1]
        observation_cost: Cost of this observation
        content_hash: Hash of percept content
        anchor_hash: Hash of anchor/provenance
        fusion_trace_hash: Hash of fusion trace (if fused)
        verdict: ACCEPT or REJECT
    
    Numeric fields are encoded as strings per the frozen numeric domain.
    """
    # Schema identification
    schema_id: str = SCHEMA_ID
    object_id: str = OBJECT_ID
    version: str = VERSION
    
    # Governance hashes
    canon_profile_hash: str = ""
    policy_hash: str = ""
    
    # Step identification
    step_type: str = StepType.OBSERVE.value
    step_index: int = 0
    
    # Chain linkage
    chain_digest_prev: str = ""
    chain_digest_next: str = ""
    state_hash_prev: str = ""
    state_hash_next: str = ""
    
    # Sensory properties
    source_tag: str = SourceTag.EXTERNAL.value
    authority_weight: str = "0.0"
    quality_score: str = "0.0"
    salience_score: str = "0.0"
    observation_cost: str = "0.0"
    
    # Content hashes
    content_hash: str = ""
    anchor_hash: str = ""
    fusion_trace_hash: str = ""
    
    # Metadata
    verdict: str = Verdict.ACCEPT.value
    reject_code: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "schema_id": self.schema_id,
            "object_id": self.object_id,
            "version": self.version,
            "canon_profile_hash": self.canon_profile_hash,
            "policy_hash": self.policy_hash,
            "step_type": self.step_type,
            "step_index": self.step_index,
            "chain_digest_prev": self.chain_digest_prev,
            "chain_digest_next": self.chain_digest_next,
            "state_hash_prev": self.state_hash_prev,
            "state_hash_next": self.state_hash_next,
            "source_tag": self.source_tag,
            "authority_weight": self.authority_weight,
            "quality_score": self.quality_score,
            "salience_score": self.salience_score,
            "observation_cost": self.observation_cost,
            "content_hash": self.content_hash,
            "anchor_hash": self.anchor_hash,
            "fusion_trace_hash": self.fusion_trace_hash,
            "verdict": self.verdict,
            "reject_code": self.reject_code,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SensoryReceipt":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_json(self, canonical: bool = True) -> str:
        """
        Serialize to JSON.
        
        Args:
            canonical: If True, use canonical form for hashing
        """
        if canonical:
            # Sort keys for deterministic output
            return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
        return json.dumps(self.to_dict())
    
    def compute_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Compute hash of percept content.
        
        Args:
            content: Percept content dictionary
            
        Returns:
            SHA256 hash as hex string
        """
        content_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def compute_chain_digest(self) -> str:
        """
        Compute chain digest linking this receipt to the chain.
        
        Returns:
            SHA256 hash of (prev_digest + state_hash + step_index)
        """
        chain_input = f"{self.chain_digest_prev}:{self.state_hash_next}:{self.step_index}"
        return hashlib.sha256(chain_input.encode()).hexdigest()
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate receipt structure and field constraints.
        
        Returns:
            (is_valid, error_message)
        """
        # Check schema ID
        if self.schema_id != SCHEMA_ID:
            return False, f"Invalid schema_id: {self.schema_id}"
        
        # Check source tag validity
        valid_sources = {s.value for s in SourceTag}
        if self.source_tag not in valid_sources:
            return False, f"Invalid source_tag: {self.source_tag}"
        
        # Check numeric fields can be parsed
        try:
            auth = float(self.authority_weight)
            if not (0 <= auth <= 1):
                return False, f"authority_weight out of range: {auth}"
        except ValueError:
            return False, f"Invalid authority_weight: {self.authority_weight}"
        
        try:
            quality = float(self.quality_score)
            if not (0 <= quality <= 1):
                return False, f"quality_score out of range: {quality}"
        except ValueError:
            return False, f"Invalid quality_score: {self.quality_score}"
        
        try:
            salience = float(self.salience_score)
            if not (0 <= salience <= 1):
                return False, f"salience_score out of range: {salience}"
        except ValueError:
            return False, f"Invalid salience_score: {self.salience_score}"
        
        try:
            cost = float(self.observation_cost)
            if cost <= 0:
                return False, f"observation_cost must be positive: {cost}"
        except ValueError:
            return False, f"Invalid observation_cost: {self.observation_cost}"
        
        # Check verdict validity
        valid_verbs = {v.value for v in Verdict}
        if self.verdict not in valid_verbs:
            return False, f"Invalid verdict: {self.verdict}"
        
        return True, None


# === Receipt Factory ===

class SensoryReceiptFactory:
    """
    Factory for creating sensory receipts with proper defaults.
    
    Per spec §15: All observation steps must produce receipts.
    """
    
    def __init__(self, canon_profile_hash: str = "", policy_hash: str = ""):
        self.canon_profile_hash = canon_profile_hash
        self.policy_hash = policy_hash
        self._step_counter = 0
    
    def create_observation_receipt(
        self,
        content: Dict[str, Any],
        source_tag: SourceTag,
        authority: float,
        quality: float,
        salience: float,
        cost: float,
        chain_digest_prev: str = "",
        state_hash_prev: str = ""
    ) -> SensoryReceipt:
        """
        Create a receipt for an observation step.
        
        Args:
            content: Percept content
            source_tag: Source of the percept
            authority: Authority weight [0,1]
            quality: Quality/confidence [0,1]
            salience: Computed salience [0,1]
            cost: Observation cost (must be > 0)
            chain_digest_prev: Previous chain digest
            state_hash_prev: Previous state hash
            
        Returns:
            Completed SensoryReceipt
        """
        self._step_counter += 1
        
        # Create receipt
        receipt = SensoryReceipt(
            canon_profile_hash=self.canon_profile_hash,
            policy_hash=self.policy_hash,
            step_type=StepType.OBSERVE.value,
            step_index=self._step_counter,
            chain_digest_prev=chain_digest_prev,
            state_hash_prev=state_hash_prev,
            source_tag=source_tag.value,
            authority_weight=str(authority),
            quality_score=str(quality),
            salience_score=str(salience),
            observation_cost=str(cost),
        )
        
        # Compute hashes
        receipt.content_hash = receipt.compute_content_hash(content)
        
        # Generate state hash (simplified - in real impl would hash full state)
        receipt.state_hash_next = hashlib.sha256(
            f"{receipt.state_hash_prev}:{receipt.content_hash}".encode()
        ).hexdigest()
        
        # Compute chain digest
        receipt.chain_digest_next = receipt.compute_chain_digest()
        
        return receipt
    
    def create_fusion_receipt(
        self,
        percept_hashes: List[str],
        fused_content: Dict[str, Any],
        chain_digest_prev: str,
        state_hash_prev: str
    ) -> SensoryReceipt:
        """
        Create a receipt for a fusion step.
        
        Args:
            percept_hashes: Hashes of fused percepts
            fused_content: Content of fused percept
            chain_digest_prev: Previous chain digest
            state_hash_prev: Previous state hash
            
        Returns:
            Completed SensoryReceipt
        """
        self._step_counter += 1
        
        # Compute fusion trace hash
        fusion_input = ":".join(percept_hashes)
        fusion_trace_hash = hashlib.sha256(fusion_input.encode()).hexdigest()
        
        receipt = SensoryReceipt(
            canon_profile_hash=self.canon_profile_hash,
            policy_hash=self.policy_hash,
            step_type=StepType.FUSE.value,
            step_index=self._step_counter,
            chain_digest_prev=chain_digest_prev,
            state_hash_prev=state_hash_prev,
            fusion_trace_hash=fusion_trace_hash,
        )
        
        receipt.content_hash = receipt.compute_content_hash(fused_content)
        receipt.state_hash_next = hashlib.sha256(
            f"{receipt.state_hash_prev}:{receipt.content_hash}".encode()
        ).hexdigest()
        receipt.chain_digest_next = receipt.compute_chain_digest()
        
        return receipt
    
    def create_ingress_receipt(
        self,
        sensory_state: Dict[str, Any],
        force_term: Dict[str, Any],
        chain_digest_prev: str,
        state_hash_prev: str
    ) -> SensoryReceipt:
        """
        Create a receipt for an ingress (substrate→organism) step.
        
        This is the "optic nerve" step where sensory state
        becomes a forcing term for GMI.
        
        Args:
            sensory_state: Current sensory state
            force_term: Computed force term
            chain_digest_prev: Previous chain digest
            state_hash_prev: Previous state hash
            
        Returns:
            Completed SensoryReceipt
        """
        self._step_counter += 1
        
        receipt = SensoryReceipt(
            canon_profile_hash=self.canon_profile_hash,
            policy_hash=self.policy_hash,
            step_type=StepType.INGRESS.value,
            step_index=self._step_counter,
            chain_digest_prev=chain_digest_prev,
            state_hash_prev=state_hash_prev,
        )
        
        # Hash the forcing term
        force_str = json.dumps(force_term, sort_keys=True, separators=(',', ':'))
        receipt.content_hash = hashlib.sha256(force_str.encode()).hexdigest()
        
        receipt.state_hash_next = hashlib.sha256(
            f"{receipt.state_hash_prev}:{receipt.content_hash}".encode()
        ).hexdigest()
        receipt.chain_digest_next = receipt.compute_chain_digest()
        
        return receipt


# === Exports ===

__all__ = [
    "SCHEMA_ID",
    "OBJECT_ID",
    "VERSION",
    "SourceTag",
    "StepType",
    "Verdict",
    "RejectCode",
    "SensoryReceipt",
    "SensoryReceiptFactory",
]
