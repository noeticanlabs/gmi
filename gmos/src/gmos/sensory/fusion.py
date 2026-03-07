"""
Fusion for GM-OS Sensory Manifold.

Defines how multiple percept streams combine with:
- Confidence-weighted merge
- Timestamp alignment
- Source-preserving fusion
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time


@dataclass
class FusionSource:
    """A single sensory source for fusion."""
    source_id: str
    confidence: float  # 0.0 to 1.0
    timestamp: float
    data: Dict[str, Any]
    source_type: str = "unknown"  # "external", "replayed", "symbolic"


@dataclass
class FusedResult:
    """Result of fusing multiple sensory sources."""
    fused_data: Dict[str, Any]
    confidence: float
    timestamp: float
    source_ids: List[str]
    alignment_deltas: Dict[str, float] = field(default_factory=dict)


def fuse_modalities(sources: List[FusionSource]) -> FusedResult:
    """
    Fuse multiple sensory modalities into unified state.
    
    Uses confidence-weighted merge:
    - Higher confidence sources contribute more to the fusion
    - Timestamp alignment adjusts for temporal differences
    - Source IDs are preserved for provenance
    
    Args:
        sources: List of FusionSource objects to fuse
        
    Returns:
        FusedResult with fused data, overall confidence, and metadata
    """
    if not sources:
        return FusedResult(
            fused_data={},
            confidence=0.0,
            timestamp=time.time(),
            source_ids=[]
        )
    
    if len(sources) == 1:
        return FusedResult(
            fused_data=sources[0].data.copy(),
            confidence=sources[0].confidence,
            timestamp=sources[0].timestamp,
            source_ids=[sources[0].source_id]
        )
    
    # Calculate weighted confidence
    total_weight = sum(s.confidence for s in sources)
    if total_weight > 0:
        overall_confidence = total_weight / len(sources)
    else:
        overall_confidence = 0.0
    
    # Align timestamps - use median timestamp as reference
    timestamps = [s.timestamp for s in sources]
    median_timestamp = sorted(timestamps)[len(timestamps) // 2]
    
    # Calculate alignment deltas
    alignment_deltas = {}
    for s in sources:
        delta = abs(s.timestamp - median_timestamp)
        alignment_deltas[s.source_id] = delta
    
    # Fuse data fields
    fused_data = _fuse_data_fields(sources, total_weight)
    
    return FusedResult(
        fused_data=fused_data,
        confidence=overall_confidence,
        timestamp=median_timestamp,
        source_ids=[s.source_id for s in sources],
        alignment_deltas=alignment_deltas
    )


def _fuse_data_fields(sources: List[FusionSource], total_weight: float) -> Dict[str, Any]:
    """Fuse data fields from multiple sources using confidence weighting."""
    if not sources:
        return {}
    
    # Collect all keys
    all_keys = set()
    for s in sources:
        all_keys.update(s.data.keys())
    
    fused = {}
    
    for key in all_keys:
        values = []
        weights = []
        
        for s in sources:
            if key in s.data:
                values.append(s.data[key])
                weights.append(s.confidence)
        
        if not values:
            continue
            
        # Fuse based on value type
        fused[key] = _fuse_value(values, weights, total_weight)
    
    return fused


def _fuse_value(values: List[Any], weights: List[float], total_weight: float) -> Any:
    """Fuse a single field value based on type."""
    if not values:
        return None
    
    # If all values are numeric, compute weighted average
    if all(isinstance(v, (int, float)) for v in values):
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    # If all values are strings, pick highest weighted
    if all(isinstance(v, str) for v in values):
        best_idx = max(range(len(weights)), key=lambda i: weights[i])
        return values[best_idx]
    
    # If all values are lists, concatenate unique items
    if all(isinstance(v, list) for v in values):
        seen = set()
        result = []
        for v in values:
            for item in v:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
        return result
    
    # For dicts, recursively fuse
    if all(isinstance(v, dict) for v in values):
        result = {}
        for v in values:
            result.update(v)
        return result
    
    # Default: return highest weighted value
    best_idx = max(range(len(weights)), key=lambda i: weights[i])
    return values[best_idx]


def align_timestamps(sources: List[FusionSource], reference_time: float) -> List[FusionSource]:
    """
    Align timestamps of sources to a reference time.
    
    Args:
        sources: List of sources to align
        reference_time: Target timestamp to align to
        
    Returns:
        List of sources with adjusted timestamps
    """
    aligned = []
    for s in sources:
        # Create copy with aligned timestamp
        aligned_source = FusionSource(
            source_id=s.source_id,
            confidence=s.confidence,
            timestamp=reference_time,  # Align to reference
            data=s.data,
            source_type=s.source_type
        )
        aligned.append(aligned_source)
    return aligned


def merge_by_confidence(sources: List[FusionSource], threshold: float = 0.5) -> FusedResult:
    """
    Merge sources, filtering by confidence threshold.
    
    Args:
        sources: List of sources to merge
        threshold: Minimum confidence to include
        
    Returns:
        FusedResult with filtered and merged sources
    """
    filtered = [s for s in sources if s.confidence >= threshold]
    return fuse_modalities(filtered)


def fuse_external_with_internal(
    external_sources: List[FusionSource],
    internal_sources: List[FusionSource]
) -> Dict[str, FusedResult]:
    """
    Fuse external and internal sensory streams separately.
    
    Returns separate fused results for external and internal modalities.
    
    Args:
        external_sources: External perception sources
        internal_sources: Internal/budget/affect sources
        
    Returns:
        Dict with "external" and "internal" FusedResult objects
    """
    return {
        "external": fuse_modalities(external_sources),
        "internal": fuse_modalities(internal_sources)
    }
