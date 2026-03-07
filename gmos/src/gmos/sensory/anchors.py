"""
Anchors for GM-OS Sensory Manifold.

Tags externally validated events and computes trust/anchor weight.
This is the main anti-hallucination stabilizer for the sensory manifold.

Anchors integrate with:
- ledger receipts (externally verified events)
- external validation stream
- memory archive
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time


class AnchorSource(Enum):
    """Source of anchor validation."""
    EXTERNAL = "external"       # From external validation
    LEDGER = "ledger"            # Verified by ledger
    REPLAY = "replay"            # From memory replay (lower trust)
    INTERNAL = "internal"         # Internal computation
    PREDICTION = "prediction"    # From prediction (lowest trust)


@dataclass
class Anchor:
    """
    An anchored event with validation metadata.
    
    Anchors represent externally validated events that have higher
    trust weight in the sensory manifold.
    """
    anchor_id: str
    source: AnchorSource
    event_type: str
    timestamp: float
    
    # Validation metadata
    receipt_hash: Optional[str] = None
    validation_score: float = 1.0
    
    # Content
    content: Dict[str, Any] = field(default_factory=dict)
    
    # Provenance
    provenance: List[str] = field(default_factory=list)
    
    # Quality metrics
    contradiction_count: int = 0
    confirmation_count: int = 0
    
    def is_trusted(self) -> bool:
        """Check if anchor has sufficient trust."""
        return (
            self.validation_score > 0.5 and
            self.source in (AnchorSource.EXTERNAL, AnchorSource.LEDGER)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize anchor."""
        return {
            "anchor_id": self.anchor_id,
            "source": self.source.value,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "receipt_hash": self.receipt_hash,
            "validation_score": self.validation_score,
            "content": self.content,
            "provenance": self.provenance,
            "contradiction_count": self.contradiction_count,
            "confirmation_count": self.confirmation_count,
        }


def anchor_external_event(
    event: Dict[str, Any],
    source: AnchorSource = AnchorSource.EXTERNAL,
    receipt_hash: Optional[str] = None,
    validation_score: float = 1.0
) -> Anchor:
    """
    Anchor an externally validated event.
    
    Args:
        event: The event data to anchor
        source: Source of validation
        receipt_hash: Optional ledger receipt hash
        validation_score: Validation confidence (0-1)
        
    Returns:
        Anchor object with metadata
    """
    import uuid
    
    anchor = Anchor(
        anchor_id=str(uuid.uuid4())[:8],
        source=source,
        event_type=event.get("type", "unknown"),
        timestamp=event.get("timestamp", time.time()),
        receipt_hash=receipt_hash,
        validation_score=validation_score,
        content=event.get("content", event),
        provenance=[source.value],
    )
    
    return anchor


def anchor_weight(
    anchor: Anchor,
    recency_weight: float = 0.2,
    validation_weight: float = 0.5,
    contradiction_penalty: float = 0.3
) -> float:
    """
    Compute anchor weight based on source quality and validation.
    
    Anchor weight depends on:
    - external receipt validity (ledger anchors have highest)
    - recency (recent anchors weighted higher)
    - confirmation vs contradiction count
    - source quality
    
    Args:
        anchor: The anchor to weight
        recency_weight: Weight for recency
        validation_weight: Weight for validation score
        contradiction_penalty: Penalty per contradiction
        
    Returns:
        Anchor weight (0-1)
    """
    # Base weight from validation score
    base_score = anchor.validation_score * validation_weight
    
    # Source multiplier (ledger/external = highest)
    source_multiplier = {
        AnchorSource.LEDGER: 1.0,
        AnchorSource.EXTERNAL: 1.0,
        AnchorSource.INTERNAL: 0.7,
        AnchorSource.PREDICTION: 0.5,
        AnchorSource.REPLAY: 0.3,
    }.get(anchor.source, 0.5)
    
    # Recency decay (half-life of 1 hour)
    age = time.time() - anchor.timestamp
    half_life = 3600.0
    recency = max(0.1, 1.0 - (age / half_life) * recency_weight)
    
    # Confirmation bonus
    confirmation_bonus = min(0.2, anchor.confirmation_count * 0.05)
    
    # Contradiction penalty
    contradiction_pen = min(0.5, anchor.contradiction_count * contradiction_penalty)
    
    # Compute final weight
    weight = (
        base_score * source_multiplier * recency +
        confirmation_bonus -
        contradiction_pen
    )
    
    # Clamp to 0-1
    return max(0.0, min(1.0, weight))


def merge_anchors(
    anchors: List[Anchor],
    min_weight: float = 0.3
) -> List[Anchor]:
    """
    Merge multiple anchors, keeping only trusted ones.
    
    Args:
        anchors: List of anchors to merge
        min_weight: Minimum weight threshold
        
    Returns:
        Filtered list of anchors
    """
    result = []
    seen_content = {}
    
    # Sort by timestamp (newest first)
    sorted_anchors = sorted(anchors, key=lambda a: a.timestamp, reverse=True)
    
    for anchor in sorted_anchors:
        weight = anchor_weight(anchor)
        
        if weight < min_weight:
            continue
        
        # Check for duplicates
        content_key = str(sorted(anchor.content.items()))
        if content_key in seen_content:
            # Update confirmation count
            existing = seen_content[content_key]
            existing.confirmation_count += 1
            continue
        
        seen_content[content_key] = anchor
        result.append(anchor)
    
    return result


def validate_against_anchors(
    new_event: Dict[str, Any],
    anchors: List[Anchor]
) -> Dict[str, Any]:
    """
    Validate a new event against existing anchors.
    
    Args:
        new_event: Event to validate
        anchors: List of existing anchors
        
    Returns:
        Validation result with confirmed/contradicted status
    """
    # Simple content matching
    new_content = str(sorted(new_event.get("content", {}).items()))
    
    confirmed = []
    contradicted = []
    
    for anchor in anchors:
        anchor_content = str(sorted(anchor.content.items()))
        
        if new_content == anchor_content:
            confirmed.append(anchor.anchor_id)
        elif _is_contradiction(new_event, anchor.content):
            contradicted.append(anchor.anchor_id)
    
    return {
        "confirmed": confirmed,
        "contradicted": contradicted,
        "confirmation_count": len(confirmed),
        "contradiction_count": len(contradicted),
        "is_validated": len(confirmed) > 0,
        "is_contradicted": len(contradicted) > 0,
    }


def _is_contradiction(event1: Dict[str, Any], event2: Dict[str, Any]) -> bool:
    """Check if two events are contradictory."""
    # Simple contradiction check based on type and conflicting values
    if event1.get("type") != event2.get("type"):
        return False
    
    # Check for conflicting numeric values
    for key in ["value", "position", "state"]:
        if key in event1 and key in event2:
            if abs(event1[key] - event2[key]) > 0.5:
                return True
    
    return False


# Integration helpers for ledger
def create_ledger_anchor(
    receipt: Dict[str, Any],
    event: Dict[str, Any]
) -> Anchor:
    """
    Create an anchor from a ledger receipt.
    
    Args:
        receipt: Ledger receipt data
        event: Associated event data
        
    Returns:
        Anchor with ledger source
    """
    return anchor_external_event(
        event=event,
        source=AnchorSource.LEDGER,
        receipt_hash=receipt.get("receipt_hash"),
        validation_score=receipt.get("validation_score", 1.0)
    )
