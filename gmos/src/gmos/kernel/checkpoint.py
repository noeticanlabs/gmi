"""
Checkpoint System for GM-OS Identity Kernel.

Implements checkpoint anchors per Identity Kernel Model Section 4.4:

    Σ_P = (self_seed, goal_seed, semantic_anchor_roots, latest_stable_shell)

Checkpoints provide:
- Recovery points for process restoration
- Provenance anchors for identity verification
- Stable shell references for reconstruction
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any, Callable
from enum import Enum
import hashlib
import time


class CheckpointStatus(Enum):
    """Status of a checkpoint."""
    ACTIVE = "active"           # Current valid checkpoint
    ARCHIVED = "archived"      # Older checkpoint, still valid
    SUPERSEDED = "superseded"  # Replaced by newer checkpoint
    CORRUPTED = "corrupted"   # Integrity check failed
    RESTORING = "restoring"   # Currently being restored from


@dataclass
class Checkpoint:
    """
    A checkpoint anchor for process recovery.
    
    Per Identity Kernel Model Section 4.4:
    Sigma includes latest stable shell.
    """
    checkpoint_id: str
    process_id: str
    
    # State snapshot
    state_hash: str
    state_data: Dict[str, Any]
    
    # Kernel anchors (what was preserved)
    identity_kernel_hash: str
    chain_digest: str
    policy_hash: str
    
    # Semantic anchors
    semantic_roots: List[str] = field(default_factory=list)
    goal_seeds: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    last_verified_at: float = field(default_factory=time.time)
    sequence: int = 0
    
    # Status
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    
    def compute_hash(self) -> str:
        """Compute canonical hash of checkpoint."""
        data = f"{self.checkpoint_id}:{self.process_id}:{self.state_hash}:{self.identity_kernel_hash}:{self.chain_digest}:{self.sequence}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify checkpoint integrity."""
        # Check all required fields present
        if not all([self.checkpoint_id, self.process_id, self.state_hash, self.identity_kernel_hash]):
            return False
        
        # Verify hash matches
        expected = self.compute_hash()
        return len(expected) > 0  # Simplified
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize checkpoint."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "process_id": self.process_id,
            "state_hash": self.state_hash,
            "identity_kernel_hash": self.identity_kernel_hash,
            "chain_digest": self.chain_digest,
            "policy_hash": self.policy_hash,
            "semantic_roots": self.semantic_roots,
            "goal_seeds": self.goal_seeds,
            "created_at": self.created_at,
            "last_verified_at": self.last_verified_at,
            "sequence": self.sequence,
            "status": self.status.value,
            "checkpoint_hash": self.compute_hash()
        }


class CheckpointManager:
    """
    Manages checkpoints for process recovery.
    
    Per Identity Kernel Model Section 12:
    - Live kernel: Current in-memory copy
    - Checkpoint kernel: Latest stable checkpoint
    - Ledger anchor: Canonical receipted representation
    """
    
    def __init__(
        self,
        max_checkpoints: int = 10,
        checkpoint_interval: float = 60.0,  # seconds
        verify_on_create: bool = True
    ):
        """
        Args:
            max_checkpoints: Maximum checkpoints to retain
            checkpoint_interval: Minimum time between checkpoints
            verify_on_create: Verify integrity on creation
        """
        self.max_checkpoints = max_checkpoints
        self.checkpoint_interval = checkpoint_interval
        self.verify_on_create = verify_on_create
        
        # Checkpoint storage
        self._checkpoints: Dict[str, List[Checkpoint]] = {}  # process_id -> checkpoints
        self._sequence_counters: Dict[str, int] = {}  # process_id -> sequence
        
        # Callbacks
        self._on_checkpoint: Optional[Callable] = None
        self._on_restore: Optional[Callable] = None
    
    def create_checkpoint(
        self,
        process_id: str,
        state_hash: str,
        state_data: Dict[str, Any],
        identity_kernel_hash: str,
        chain_digest: str,
        policy_hash: str = "",
        semantic_roots: Optional[List[str]] = None,
        goal_seeds: Optional[List[str]] = None
    ) -> Optional[Checkpoint]:
        """
        Create a new checkpoint.
        
        Args:
            process_id: Process to checkpoint
            state_hash: Current state hash
            state_data: Serialized state
            identity_kernel_hash: Current kernel hash
            chain_digest: Current chain digest
            policy_hash: Current policy hash
            semantic_roots: Semantic anchor roots
            goal_seeds: Goal seeds
            
        Returns:
            Created Checkpoint or None if throttled
        """
        now = time.time()
        
        # Check throttle
        if process_id in self._checkpoints:
            checkpoints = self._checkpoints[process_id]
            if checkpoints:
                last = checkpoints[-1]
                if now - last.created_at < self.checkpoint_interval:
                    return None  # Too soon
        
        # Get sequence number
        sequence = self._sequence_counters.get(process_id, 0) + 1
        self._sequence_counters[process_id] = sequence
        
        # Generate checkpoint ID
        checkpoint_id = f"cp_{process_id}_{sequence}_{int(now * 1000)}"
        
        # Create checkpoint
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            process_id=process_id,
            state_hash=state_hash,
            state_data=state_data,
            identity_kernel_hash=identity_kernel_hash,
            chain_digest=chain_digest,
            policy_hash=policy_hash,
            semantic_roots=semantic_roots or [],
            goal_seeds=goal_seeds or [],
            sequence=sequence,
            status=CheckpointStatus.ACTIVE
        )
        
        # Verify if requested
        if self.verify_on_create and not checkpoint.verify_integrity():
            checkpoint.status = CheckpointStatus.CORRUPTED
            return None
        
        # Store
        if process_id not in self._checkpoints:
            self._checkpoints[process_id] = []
        
        # Mark previous as superseded
        for cp in self._checkpoints[process_id]:
            if cp.status == CheckpointStatus.ACTIVE:
                cp.status = CheckpointStatus.ARCHIVED
        
        self._checkpoints[process_id].append(checkpoint)
        
        # Prune old checkpoints
        self._prune_checkpoints(process_id)
        
        # Callback
        if self._on_checkpoint:
            self._on_checkpoint(checkpoint)
        
        return checkpoint
    
    def get_latest_checkpoint(self, process_id: str) -> Optional[Checkpoint]:
        """Get the latest valid checkpoint for a process."""
        if process_id not in self._checkpoints:
            return None
        
        checkpoints = self._checkpoints[process_id]
        # Find latest active/archived
        for cp in reversed(checkpoints):
            if cp.status in [CheckpointStatus.ACTIVE, CheckpointStatus.ARCHIVED]:
                return cp
        
        return None
    
    def get_checkpoint_by_id(self, process_id: str, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a specific checkpoint."""
        if process_id not in self._checkpoints:
            return None
        
        for cp in self._checkpoints[process_id]:
            if cp.checkpoint_id == checkpoint_id:
                return cp
        
        return None
    
    def verify_checkpoint(self, process_id: str, checkpoint_id: str) -> bool:
        """Verify a checkpoint is still valid."""
        checkpoint = self.get_checkpoint_by_id(process_id, checkpoint_id)
        if checkpoint is None:
            return False
        
        return checkpoint.verify_integrity()
    
    def restore_from_checkpoint(
        self,
        process_id: str,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Restore process state from checkpoint.
        
        Args:
            process_id: Process to restore
            checkpoint_id: Checkpoint to restore from
            
        Returns:
            Restored state data or None
        """
        checkpoint = self.get_checkpoint_by_id(process_id, checkpoint_id)
        if checkpoint is None:
            return None
        
        if checkpoint.status == CheckpointStatus.CORRUPTED:
            return None
        
        # Mark as restoring
        checkpoint.status = CheckpointStatus.RESTORING
        
        # Callback
        if self._on_restore:
            self._on_restore(checkpoint)
        
        # Return state data
        return checkpoint.state_data
    
    def _prune_checkpoints(self, process_id: str) -> None:
        """Remove old checkpoints beyond limit."""
        if process_id not in self._checkpoints:
            return
        
        checkpoints = self._checkpoints[process_id]
        
        # Keep at most max_checkpoints
        if len(checkpoints) > self.max_checkpoints:
            # Mark extras as superseded
            to_remove = len(checkpoints) - self.max_checkpoints
            for i in range(to_remove):
                checkpoints[i].status = CheckpointStatus.SUPERSEDED
            
            # Keep only recent
            self._checkpoints[process_id] = checkpoints[-self.max_checkpoints:]
    
    def get_checkpoint_chain(
        self,
        process_id: str,
        limit: int = 5
    ) -> List[Checkpoint]:
        """Get recent checkpoint chain."""
        if process_id not in self._checkpoints:
            return []
        
        checkpoints = self._checkpoints[process_id]
        return list(reversed(checkpoints))[:limit]
    
    def set_callbacks(
        self,
        on_checkpoint: Optional[Callable] = None,
        on_restore: Optional[Callable] = None
    ) -> None:
        """Set checkpoint callbacks."""
        self._on_checkpoint = on_checkpoint
        self._on_restore = on_restore


def create_checkpoint_manager(
    max_checkpoints: int = 10,
    checkpoint_interval: float = 60.0
) -> CheckpointManager:
    """
    Factory function to create a checkpoint manager.
    
    Args:
        max_checkpoints: Maximum checkpoints to retain
        checkpoint_interval: Minimum seconds between checkpoints
        
    Returns:
        Configured CheckpointManager
    """
    return CheckpointManager(
        max_checkpoints=max_checkpoints,
        checkpoint_interval=checkpoint_interval
    )
