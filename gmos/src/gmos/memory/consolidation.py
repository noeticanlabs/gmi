"""
Consolidation for the GMI Memory System.

Compress and maintain the episodic archive while preserving auditability.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import hashlib
import json

from memory.archive import EpisodicArchive
from memory.episode import Episode


@dataclass
class ConsolidationReport:
    """
    Report from a consolidation operation.
    """
    original_count: int
    consolidated_count: int
    slabs_created: int
    episodes_removed: int
    total_cost: float
    message: str


@dataclass 
class SlabReceipt:
    """
    Receipt for a compressed block (slab) of episodes.
    
    Enables partial verification without loading all episodes.
    """
    start_idx: int
    end_idx: int
    count: int
    slab_hash: str
    first_episode_id: str
    last_episode_id: str
    created_at: float
    
    def to_dict(self) -> Dict:
        return {
            'start_idx': self.start_idx,
            'end_idx': self.end_idx,
            'count': self.count,
            'slab_hash': self.slab_hash,
            'first_episode_id': self.first_episode_id,
            'last_episode_id': self.last_episode_id,
            'created_at': self.created_at
        }
    
    def verify(
        self, 
        episodes: List[Episode]
    ) -> bool:
        """
        Verify a slab against actual episodes.
        
        Args:
            episodes: Episodes in the slab range
            
        Returns:
            True if verification passes
        """
        if len(episodes) != self.count:
            return False
        
        # Compute expected hash
        combined = "".join(ep.hash() for ep in episodes)
        computed_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return computed_hash == self.slab_hash


class Consolidator:
    """
    Prune/Consolidate operator for the memory system.
    
    Compresses the archive while preserving auditability:
    - Compress redundant episodes
    - Merge near-duplicates
    - Retain high-salience episodes
    - Demote stale entries
    - Keep cryptographic summary links
    
    Important: Pruning must preserve auditability!
    No silent deletion - all operations create receipts.
    """
    
    def __init__(self, archive: EpisodicArchive):
        self.archive = archive
        self.slab_receipts: List[SlabReceipt] = []
    
    def consolidate(
        self,
        similarity_threshold: float = 0.95,
        min_recent_episodes: int = 10,
        max_staleness: int = 100
    ) -> ConsolidationReport:
        """
        Consolidate the archive.
        
        Args:
            similarity_threshold: Threshold for merging similar episodes
            min_recent_episodes: Minimum recent episodes to always keep
            max_staleness: Maximum age for demotion
            
        Returns:
            ConsolidationReport
        """
        original_count = len(self.archive)
        
        if original_count == 0:
            return ConsolidationReport(
                original_count=0,
                consolidated_count=0,
                slabs_created=0,
                episodes_removed=0,
                total_cost=0.0,
                message="Empty archive"
            )
        
        # For now, this is a placeholder implementation
        # A full implementation would use clustering, etc.
        
        # Create a slab receipt for the entire archive
        if original_count > min_recent_episodes:
            slab = self.create_slab_receipt(0, original_count)
            self.slab_receipts.append(slab)
            slabs_created = 1
        else:
            slabs_created = 0
        
        consolidated_count = original_count
        
        return ConsolidationReport(
            original_count=original_count,
            consolidated_count=consolidated_count,
            slabs_created=slabs_created,
            episodes_removed=0,
            total_cost=0.0,
            message="Consolidation placeholder - implement clustering for production"
        )
    
    def create_slab_receipt(
        self,
        start_idx: int,
        end_idx: int
    ) -> SlabReceipt:
        """
        Create a proof over a compressed block (slab).
        
        Args:
            start_idx: Start index of slab
            end_idx: End index of slab
            
        Returns:
            SlabReceipt
        """
        import time
        
        if start_idx < 0 or end_idx > len(self.archive):
            raise ValueError("Invalid slab range")
        
        episodes = self.archive.episodes[start_idx:end_idx]
        
        # Create hash of all episodes in slab
        combined = "".join(ep.hash() for ep in episodes)
        slab_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return SlabReceipt(
            start_idx=start_idx,
            end_idx=end_idx,
            count=len(episodes),
            slab_hash=slab_hash,
            first_episode_id=episodes[0].episode_id if episodes else "",
            last_episode_id=episodes[-1].episode_id if episodes else "",
            created_at=time.time()
        )
    
    def verify_slab(
        self,
        slab_receipt: SlabReceipt
    ) -> Tuple[bool, str]:
        """
        Verify a slab receipt.
        
        Args:
            slab_receipt: SlabReceipt to verify
            
        Returns:
            (is_valid, message)
        """
        episodes = self.archive.episodes[slab_receipt.start_idx:slab_receipt.end_idx]
        
        if len(episodes) != slab_receipt.count:
            return False, f"Count mismatch: expected {slab_receipt.count}, got {len(episodes)}"
        
        # Verify hash
        combined = "".join(ep.hash() for ep in episodes)
        computed_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        if computed_hash != slab_receipt.slab_hash:
            return False, "Hash mismatch"
        
        return True, "Slab verified"
    
    def get_memory_footprint(self) -> Dict[str, Any]:
        """
        Get current memory footprint statistics.
        
        Returns:
            Dict of memory statistics
        """
        total_episodes = len(self.archive)
        
        # Estimate memory usage
        import sys
        total_size = sum(sys.getsizeof(ep.to_json()) for ep in self.archive.episodes)
        
        return {
            'total_episodes': total_episodes,
            'estimated_size_bytes': total_size,
            'slab_receipts': len(self.slab_receipts),
            'indexes': {
                'by_step': len(self.archive.index_by_step),
                'by_decision': len(self.archive.index_by_decision),
                'by_tag': len(self.archive.index_by_tag)
            }
        }
    
    def estimate_compression_ratio(self) -> float:
        """
        Estimate potential compression ratio.
        
        Returns:
            Estimated compression ratio
        """
        # This is a placeholder - real implementation would analyze redundancy
        return 1.0


# Global consolidator instance
_consolidator: Optional[Consolidator] = None


def get_consolidator(archive: Optional[EpisodicArchive] = None) -> Consolidator:
    """Get or create the global consolidator."""
    global _consolidator
    if _consolidator is None:
        from memory.archive import get_global_archive
        _consolidator = Consolidator(archive or get_global_archive())
    return _consolidator
