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


# === Extended Fusion Law with Provenance (per spec §10) ===

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json


@dataclass
class ProvenanceTrace:
    """
    Provenance trace for fused percepts.
    
    Per spec §10: Fusion combines content but keeps provenance
    as a multiset or trace. This prevents the agent from
    silently equating external observation with internal memory.
    """
    source_tags: List[str] = field(default_factory=list)
    authority_weights: List[float] = field(default_factory=list)
    content_hashes: List[str] = field(default_factory=list)
    fusion_order: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_tags": self.source_tags,
            "authority_weights": self.authority_weights,
            "content_hashes": self.content_hashes,
            "fusion_order": self.fusion_order,
        }
    
    def compute_trace_hash(self) -> str:
        """Compute hash of the entire provenance trace."""
        trace_str = json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(trace_str.encode()).hexdigest()


@dataclass 
class FusedPerceptWithProvenance:
    """
    A fused percept with provenance preservation.
    
    Per spec §10: The fusion law must fuse internal and external
    sensing without erasing provenance.
    """
    # Fused content
    content: Dict[str, Any]
    fused_confidence: float
    fused_authority: float
    
    # Provenance trace
    provenance: ProvenanceTrace
    
    # Conflict markers
    conflicts: List[Tuple[str, str]] = field(default_factory=list)
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    fusion_trace_hash: str = ""
    
    def __post_init__(self):
        self.fusion_trace_hash = self.provenance.compute_trace_hash()


def fuse_with_provenance(
    percepts: List[Dict[str, Any]],
    weights: Optional[List[float]] = None
) -> FusedPerceptWithProvenance:
    """
    Fuse percepts while preserving provenance.
    
    Per spec §10:
    F_fuse(s₁, ..., s_n) = (∑ᵢ wᵢ φᵢ, {provᵢ}, {authᵢ}, {conflictᵢⱼ})
    
    Where weights:
    wᵢ = aᵢ qᵢ / ∑ⱼ aⱼ qⱼ
    
    This ensures the agent cannot later pretend that an
    internal guess came from the external world.
    
    Args:
        percepts: List of percept dictionaries
        weights: Optional explicit weights
        
    Returns:
        FusedPerceptWithProvenance with full provenance trace
    """
    if not percepts:
        return FusedPerceptWithProvenance(
            content={},
            fused_confidence=0.0,
            fused_authority=0.0,
            provenance=ProvenanceTrace(),
        )
    
    if len(percepts) == 1:
        # Single percept - just wrap with provenance
        p = percepts[0]
        return FusedPerceptWithProvenance(
            content=p.get("content", {}),
            fused_confidence=p.get("confidence", 0.0),
            fused_authority=p.get("authority", 0.0),
            provenance=ProvenanceTrace(
                source_tags=[p.get("source", "unknown")],
                authority_weights=[p.get("authority", 0.0)],
                content_hashes=[p.get("content_hash", "")],
                fusion_order=[0],
            ),
        )
    
    # Extract authorities and qualities
    authorities = [p.get("authority", 0.5) for p in percepts]
    qualities = [p.get("quality", p.get("confidence", 0.5)) for p in percepts]
    
    # Compute weights: w_i = a_i * q_i / sum(a_j * q_j)
    if weights is None:
        products = [a * q for a, q in zip(authorities, qualities)]
        total = sum(products)
        weights = [p / total if total > 0 else 1.0 / len(percepts) for p in products]
    
    # Fuse content
    fused_content = _fuse_provenance_content(percepts, weights)
    
    # Compute fused confidence
    fused_confidence = sum(w * q for w, q in zip(weights, qualities))
    
    # Compute fused authority
    fused_authority = sum(w * a for w, a in zip(weights, authorities))
    
    # Build provenance trace
    provenance = ProvenanceTrace(
        source_tags=[p.get("source", "unknown") for p in percepts],
        authority_weights=authorities,
        content_hashes=[p.get("content_hash", "") for p in percepts],
        fusion_order=list(range(len(percepts))),
    )
    
    return FusedPerceptWithProvenance(
        content=fused_content,
        fused_confidence=fused_confidence,
        fused_authority=fused_authority,
        provenance=provenance,
    )


def _fuse_provenance_content(
    percepts: List[Dict[str, Any]],
    weights: List[float]
) -> Dict[str, Any]:
    """Fuse content fields with provenance awareness."""
    if not percepts:
        return {}
    
    # Collect all keys
    all_keys = set()
    for p in percepts:
        if "content" in p:
            all_keys.update(p["content"].keys())
    
    fused = {}
    for key in all_keys:
        values = []
        wts = []
        
        for p, w in zip(percepts, weights):
            if "content" in p and key in p["content"]:
                values.append(p["content"][key])
                wts.append(w)
        
        if not values:
            continue
        
        # Fuse numeric values
        if all(isinstance(v, (int, float)) for v in values):
            total_w = sum(wts)
            fused[key] = sum(v * w for v, w in zip(values, wts)) / total_w if total_w > 0 else 0.0
        else:
            # For non-numeric, pick highest weight
            best_idx = max(range(len(wts)), key=lambda i: wts[i])
            fused[key] = values[best_idx]
    
    return fused


class FusionEngineWithProvenance:
    """
    Extended fusion engine with provenance preservation.
    
    Per spec §10: Fusion must preserve provenance so the agent
    cannot hallucinate reality without paying.
    """
    
    def __init__(self):
        self.fusion_history: List[FusedPerceptWithProvenance] = []
    
    def fuse(
        self,
        percepts: List[Dict[str, Any]],
        weights: Optional[List[float]] = None
    ) -> FusedPerceptWithProvenance:
        """
        Fuse percepts with provenance preservation.
        
        Args:
            percepts: List of percepts to fuse
            weights: Optional weights override
            
        Returns:
            FusedPerceptWithProvenance
        """
        result = fuse_with_provenance(percepts, weights)
        self.fusion_history.append(result)
        return result
    
    def get_provenance_trace(self, index: int) -> Optional[ProvenanceTrace]:
        """Get provenance trace for a past fusion."""
        if 0 <= index < len(self.fusion_history):
            return self.fusion_history[index].provenance
        return None
    
    def verify_provenance_distinction(
        self,
        fused: FusedPerceptWithProvenance
    ) -> Tuple[bool, str]:
        """
        Verify that provenance distinguishes external from internal.
        
        Per spec §7: This prevents the GMI from silently equating:
        - external observation
        - internal memory
        - imagined simulation
        - policy suggestion
        """
        sources = fused.provenance.source_tags
        
        has_external = "ext" in sources
        has_internal = any(s in ["int", "mem", "sim"] for s in sources)
        
        if has_external and has_internal:
            # Mixed - this is valid but should be flagged
            return True, "Mixed provenance fusion"
        elif has_external:
            return True, "Pure external fusion"
        elif has_internal:
            return True, "Pure internal fusion"
        else:
            return False, "Unknown provenance sources"
