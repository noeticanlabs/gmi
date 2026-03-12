"""
Integrity Scorer for GM-OS Self-Repair System.

Provides integrity scoring functions for hash chain ledgers.
Per Self-Repair Model Section 15 and Identity Kernel Model Section 4.2.
"""

from typing import Dict, Any, Tuple, Optional


class IntegrityScorer:
    """
    Computes integrity scores for hash chain ledgers.
    
    Per Self-Repair Model Section 4:
    H_p: Receipt-chain continuity, checkpoint availability, hash-anchor coherence
    
    Per Identity Kernel Model Section 4.2:
    Omega = (H_n, r*, C*) - chain digest, checkpoint, ancestry
    """
    
    def __init__(self, rejection_penalty: float = 0.5, gap_penalty: float = 0.3):
        """
        Args:
            rejection_penalty: Max penalty fraction for rejections (0-1)
            gap_penalty: Max penalty fraction for chain gaps (0-1)
        """
        self.rejection_penalty = rejection_penalty
        self.gap_penalty = gap_penalty
    
    def compute_integrity_score(
        self,
        chain_length: int,
        accepted_count: int,
        rejected_count: int,
        halt_count: int,
        first_step: int = 0,
        last_step: int = -1
    ) -> float:
        """
        Compute integrity score H_p.
        
        Returns:
            Integrity score in [0, 1], where 1 = perfect integrity
        """
        if chain_length == 0:
            return 1.0  # Empty chain has perfect integrity
        
        # Start with full integrity
        score = 1.0
        
        # Penalize by rejection rate (broken trust)
        total = accepted_count + rejected_count + halt_count
        if total > 0:
            rejection_ratio = (rejected_count + halt_count) / total
            score *= (1.0 - rejection_ratio * self.rejection_penalty)
        
        # Penalize by chain gaps (missing continuity)
        expected_len = last_step - first_step + 1 if last_step >= first_step else chain_length
        if expected_len > chain_length:
            gap_penalty_val = (expected_len - chain_length) / expected_len
            score *= (1.0 - gap_penalty_val * self.gap_penalty)
        
        return max(0.0, min(1.0, score))
    
    def get_provenance_continuity(
        self,
        chain_length: int,
        accepted_count: int,
        rejected_count: int,
        halt_count: int,
        current_digest: str,
        genesis_hash: str,
        first_step: int = 0,
        last_step: int = -1,
        chain_verified: bool = True
    ) -> Dict[str, Any]:
        """
        Get provenance continuity metrics.
        
        Per Identity Kernel Model Section 4.2:
        Omega = (H_n, r*, C*) - chain digest, checkpoint, ancestry
        """
        if chain_length == 0:
            return {
                "chain_length": 0,
                "current_digest": genesis_hash,
                "continuity_intact": True,
                "checkpoint_count": 0,
                "integrity_score": 1.0
            }
        
        integrity = self.compute_integrity_score(
            chain_length=chain_length,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            halt_count=halt_count,
            first_step=first_step,
            last_step=last_step
        )
        
        return {
            "chain_length": chain_length,
            "current_digest": current_digest,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "halt_count": halt_count,
            "continuity_intact": chain_verified,
            "first_step": first_step,
            "last_step": last_step,
            "integrity_score": integrity
        }
    
    def verify_provenance_continuity(
        self,
        current_digest: str,
        expected_digest: str,
        max_rollback: int = 0
    ) -> Tuple[bool, str]:
        """
        Verify provenance continuity.
        
        Per Identity Kernel Model Section 5.2:
        Omega must be extendable from current state.
        """
        if current_digest == expected_digest:
            return True, "Provenance continuous"
        
        return False, f"Provenance broken: expected {expected_digest[:8]}, got {current_digest[:8]}"


# Default scorer instance
_default_scorer: Optional[IntegrityScorer] = None


def get_default_scorer() -> IntegrityScorer:
    """Get or create default integrity scorer."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = IntegrityScorer()
    return _default_scorer


def compute_integrity_score(
    chain_length: int,
    accepted_count: int,
    rejected_count: int = 0,
    halt_count: int = 0,
    first_step: int = 0,
    last_step: int = -1
) -> float:
    """
    Convenience function to compute integrity score.
    
    Args:
        chain_length: Number of entries in chain
        accepted_count: Number of accepted transitions
        rejected_count: Number of rejected transitions
        halt_count: Number of halts
        first_step: First step index
        last_step: Last step index
        
    Returns:
        Integrity score in [0, 1]
    """
    scorer = get_default_scorer()
    return scorer.compute_integrity_score(
        chain_length=chain_length,
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        halt_count=halt_count,
        first_step=first_step,
        last_step=last_step
    )
