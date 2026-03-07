"""
Reality Anchors for the GMI Memory System.

Reality anchors are memory items strongly tied to verified external receipts.
They carry higher epistemic weight than purely internal episodes.

This helps the system prefer:
- Grounded memories over self-generated fantasies
- World-confirmed structure over internal echo
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime

from memory.episode import Episode


@dataclass
class RealityAnchor:
    """
    Memory item strongly tied to verified external receipts.
    
    Reality anchors carry higher epistemic weight than purely internal episodes.
    They represent memories that have been validated by external interaction,
    making them more trustworthy for guiding future decisions.
    
    Attributes:
        episode_id: ID of the anchored episode
        external_receipt_id: ID of the external receipt that validates this
        validation_source: Source of validation
            - "verifier_outcome": Verified by GMI verifier
            - "task_completion": External task completion
            - "physical_measurement": Measured by external sensors
            - "user_confirmation": Confirmed by human
        anchor_weight: Epistemic weight (higher = more trustworthy)
        validation_timestamp: When this was validated
        confidence: Confidence in the validation (0-1)
    """
    episode_id: str
    external_receipt_id: str
    validation_source: str  # "verifier_outcome", "task_completion", etc.
    anchor_weight: float = 2.0  # Higher than internal episodes (default 1.0)
    validation_timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    confidence: float = 1.0
    
    # Additional metadata
    validation_details: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=lambda: ["reality_anchor"])
    
    @classmethod
    def from_verified_outcome(
        cls, 
        episode: Episode, 
        receipt_id: str,
        confidence: float = 1.0
    ) -> 'RealityAnchor':
        """
        Create a reality anchor from a verified outcome.
        
        Args:
            episode: Episode to anchor
            receipt_id: External receipt ID
            confidence: Validation confidence
            
        Returns:
            RealityAnchor
        """
        return cls(
            episode_id=episode.episode_id,
            external_receipt_id=receipt_id,
            validation_source="verifier_outcome",
            anchor_weight=2.0,
            confidence=confidence,
            validation_details={
                'potential_before': episode.potential_before,
                'potential_after': episode.potential_after,
                'decision': episode.decision
            }
        )
    
    @classmethod
    def from_task_completion(
        cls,
        episode: Episode,
        task_id: str,
        success: bool,
        confidence: float = 0.9
    ) -> 'RealityAnchor':
        """
        Create a reality anchor from external task completion.
        
        Args:
            episode: Episode to anchor
            task_id: External task ID
            success: Whether task was successful
            confidence: Validation confidence
            
        Returns:
            RealityAnchor
        """
        return cls(
            episode_id=episode.episode_id,
            external_receipt_id=task_id,
            validation_source="task_completion",
            anchor_weight=2.5 if success else 1.5,  # Higher weight for success
            confidence=confidence,
            validation_details={
                'success': success,
                'task_id': task_id
            }
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'episode_id': self.episode_id,
            'external_receipt_id': self.external_receipt_id,
            'validation_source': self.validation_source,
            'anchor_weight': self.anchor_weight,
            'validation_timestamp': self.validation_timestamp,
            'confidence': self.confidence,
            'validation_details': self.validation_details,
            'tags': self.tags
        }


class RealityAnchorManager:
    """
    Manager for reality anchors.
    
    Provides:
    - Registration of new anchors
    - Retrieval of anchors by various criteria
    - Weight adjustment based on validation recency
    """
    
    def __init__(self):
        self.anchors: Dict[str, RealityAnchor] = {}  # episode_id -> anchor
        self.by_source: Dict[str, List[str]] = {}  # source -> episode_ids
    
    def register(self, anchor: RealityAnchor) -> None:
        """
        Register a new reality anchor.
        
        Args:
            anchor: RealityAnchor to register
        """
        self.anchors[anchor.episode_id] = anchor
        
        # Index by source
        if anchor.validation_source not in self.by_source:
            self.by_source[anchor.validation_source] = []
        self.by_source[anchor.validation_source].append(anchor.episode_id)
    
    def get(self, episode_id: str) -> Optional[RealityAnchor]:
        """
        Get anchor by episode ID.
        
        Args:
            episode_id: Episode ID to look up
            
        Returns:
            RealityAnchor if found, None otherwise
        """
        return self.anchors.get(episode_id)
    
    def get_by_source(self, source: str) -> List[RealityAnchor]:
        """
        Get all anchors from a validation source.
        
        Args:
            source: Validation source
            
        Returns:
            List of RealityAnchors
        """
        episode_ids = self.by_source.get(source, [])
        return [self.anchors[eid] for eid in episode_ids if eid in self.anchors]
    
    def get_highest_weight(self, n: int = 5) -> List[RealityAnchor]:
        """
        Get the n highest-weight anchors.
        
        Args:
            n: Number of anchors to return
            
        Returns:
            List of top-n RealityAnchors by weight
        """
        anchors = list(self.anchors.values())
        anchors.sort(key=lambda a: a.anchor_weight, reverse=True)
        return anchors[:n]
    
    def get_weighted_episode_ids(self) -> Dict[str, float]:
        """
        Get all episode IDs with their anchor weights.
        
        Returns:
            Dict of episode_id -> anchor_weight
        """
        return {
            ep_id: anchor.anchor_weight 
            for ep_id, anchor in self.anchors.items()
        }
    
    def adjust_weight(
        self, 
        episode_id: str, 
        new_weight: float
    ) -> bool:
        """
        Adjust the weight of an anchor.
        
        Args:
            episode_id: Episode to adjust
            new_weight: New weight
            
        Returns:
            True if adjustment successful
        """
        if episode_id not in self.anchors:
            return False
        
        self.anchors[episode_id].anchor_weight = new_weight
        return True
    
    def decay_weights(self, decay_factor: float = 0.99) -> None:
        """
        Decay all anchor weights slightly (forgetting).
        
        Args:
            decay_factor: Factor to multiply weights by
        """
        for anchor in self.anchors.values():
            anchor.anchor_weight *= decay_factor
    
    def count(self) -> int:
        """Get number of anchors."""
        return len(self.anchors)


# Global reality anchor manager
_global_anchor_manager: Optional[RealityAnchorManager] = None


def get_anchor_manager() -> RealityAnchorManager:
    """Get or create the global anchor manager."""
    global _global_anchor_manager
    if _global_anchor_manager is None:
        _global_anchor_manager = RealityAnchorManager()
    return _global_anchor_manager


def set_anchor_manager(manager: RealityAnchorManager) -> None:
    """Set the global anchor manager."""
    global _global_anchor_manager
    _global_anchor_manager = manager
