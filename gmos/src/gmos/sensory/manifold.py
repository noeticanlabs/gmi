"""
Sensory Manifold for GM-OS.

Defines the full sensory manifold state and chart structure for:
- External perception (physical/world-facing)
- Semantic perception (symbolic/conceptual)
- Internal/interoceptive perception (budget, affect, process health)

This module defines the GEOMETRY of perception, not heavy perception logic.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time


class ModalityType(Enum):
    """Types of sensory modalities."""
    VISION = "vision"
    AUDIO = "audio"
    TEXT = "text"
    PROPRIOCEPTION = "proprioception"
    TOOL = "tool"
    SIMULATION = "simulation"


@dataclass
class ExternalChart:
    """
    External perception chart.
    
    Holds raw modality summaries, object/event fields, motion/location features,
    uncertainty/confidence, and timestamps.
    """
    # Raw modality data
    modalities: Dict[ModalityType, Dict[str, Any]] = field(default_factory=dict)
    
    # Object/event fields
    objects: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Spatial features
    locations: Dict[str, List[float]] = field(default_factory=dict)
    motions: Dict[str, List[float]] = field(default_factory=dict)
    
    # Uncertainty and confidence
    confidence: float = 1.0
    uncertainty: Dict[str, float] = field(default_factory=dict)
    
    # Temporal
    timestamp: float = field(default_factory=time.time)
    window_start: float = 0.0
    window_end: float = 0.0
    
    # Provenance
    source_tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "modality_type": [m.value for m in self.modalities.keys()],
            "object_count": len(self.objects),
            "event_count": len(self.events),
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "sources": self.source_tags,
        }


@dataclass
class SemanticChart:
    """
    Semantic perception chart.
    
    Holds symbol/glyph activations, concept tags, relation hints,
    and contextual weights.
    """
    # Symbol/glyph activations
    glyph_activations: Dict[str, float] = field(default_factory=dict)
    
    # Concept tags
    concepts: List[str] = field(default_factory=list)
    concept_weights: Dict[str, float] = field(default_factory=dict)
    
    # Relation hints
    relations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Contextual weights
    context_weights: Dict[str, float] = field(default_factory=dict)
    
    # Embedding representation
    embedding: Optional[List[float]] = None
    
    # Temporal
    timestamp: float = field(default_factory=time.time)
    
    # Provenance
    source_tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "glyph_count": len(self.glyph_activations),
            "concept_count": len(self.concepts),
            "relation_count": len(self.relations),
            "has_embedding": self.embedding is not None,
            "timestamp": self.timestamp,
        }


@dataclass
class InternalChart:
    """
    Internal/interoceptive perception chart.
    
    Holds budget, reserve, pressure, threat, discipline/freeze/greed shell,
    and process health metrics.
    """
    # Budget metrics
    budget: float = 0.0
    reserve: float = 0.0
    available: float = 0.0
    
    # Pressure metrics
    pressure: float = 0.0
    load: Dict[str, float] = field(default_factory=dict)
    
    # Threat/affect shell
    threat_level: float = 0.0
    freeze_level: float = 0.0
    greed_level: float = 0.0
    
    # Process health
    active_processes: int = 0
    mode: str = "unknown"
    health_score: float = 1.0
    
    # Memory metrics
    memory_load: float = 0.0
    replay_count: int = 0
    
    # Temporal
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "budget": self.budget,
            "reserve": self.reserve,
            "available": self.available,
            "pressure": self.pressure,
            "threat": self.threat_level,
            "mode": self.mode,
            "health": self.health_score,
            "timestamp": self.timestamp,
        }


@dataclass
class SensoryBundle:
    """
    Unified sensory bundle combining all three charts.
    
    This is the complete sensory state that gets passed to cognition.
    """
    external: Optional[ExternalChart] = None
    semantic: Optional[SemanticChart] = None
    internal: Optional[InternalChart] = None
    
    # Fusion metadata
    fusion_timestamp: float = field(default_factory=time.time)
    fusion_confidence: float = 1.0
    
    # Validated anchors (from ledger)
    anchors: List[Dict[str, Any]] = field(default_factory=list)
    
    def is_complete(self) -> bool:
        """Check if all charts are present."""
        return (
            self.external is not None or
            self.semantic is not None or
            self.internal is not None
        )
    
    def get_confidence(self) -> float:
        """Get overall confidence based on anchors and charts."""
        base = self.fusion_confidence
        
        # Boost confidence if we have anchored (externally validated) content
        if self.anchors:
            anchor_boost = min(0.2, len(self.anchors) * 0.05)
            base = min(1.0, base + anchor_boost)
        
        # Reduce confidence if charts are missing
        present = sum([
            self.external is not None,
            self.semantic is not None,
            self.internal is not None
        ])
        if present < 3:
            base *= (present / 3)
        
        return base


@dataclass
class SensoryState:
    """
    Container for fused sensory state.
    
    This is the main entry point for sensory manifold state.
    """
    # The unified bundle
    bundle: SensoryBundle = field(default_factory=SensoryBundle)
    
    # Individual chart access (for backward compatibility)
    external: Optional[ExternalChart] = None
    semantic: Optional[SemanticChart] = None
    internal: Optional[InternalChart] = None
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"

    def __post_init__(self):
        """Sync individual charts with bundle."""
        if self.external is None:
            self.external = self.bundle.external
        if self.semantic is None:
            self.semantic = self.bundle.semantic
        if self.internal is None:
            self.internal = self.bundle.internal

    def to_external_chart(self, data: Dict[str, Any]) -> ExternalChart:
        """Convert raw data to external chart."""
        chart = ExternalChart()
        
        # Parse modality data
        if "modalities" in data:
            for mod_type, mod_data in data["modalities"].items():
                if isinstance(mod_type, str):
                    mod_type = ModalityType(mod_type)
                chart.modalities[mod_type] = mod_data
        
        # Parse objects
        if "objects" in data:
            chart.objects = data["objects"]
        
        # Parse events
        if "events" in data:
            chart.events = data["events"]
        
        # Parse locations
        if "locations" in data:
            chart.locations = data["locations"]
        
        # Parse confidence
        chart.confidence = data.get("confidence", 1.0)
        
        # Parse timestamps
        chart.timestamp = data.get("timestamp", time.time())
        
        # Parse source tags
        if "sources" in data:
            chart.source_tags = data["sources"]
        
        return chart

    def to_semantic_chart(self, data: Dict[str, Any]) -> SemanticChart:
        """Convert data to semantic chart."""
        chart = SemanticChart()
        
        # Parse glyphs
        if "glyphs" in data:
            chart.glyph_activations = data["glyphs"]
        
        # Parse concepts
        if "concepts" in data:
            chart.concepts = data["concepts"]
            chart.concept_weights = data.get("concept_weights", {})
        
        # Parse relations
        if "relations" in data:
            chart.relations = data["relations"]
        
        # Parse embedding
        if "embedding" in data:
            chart.embedding = data["embedding"]
        
        # Parse source tags
        if "sources" in data:
            chart.source_tags = data["sources"]
        
        chart.timestamp = data.get("timestamp", time.time())
        return chart

    def to_internal_chart(self, data: Dict[str, Any]) -> InternalChart:
        """Convert data to internal chart."""
        chart = InternalChart()
        
        # Parse budget
        chart.budget = data.get("budget", 0.0)
        chart.reserve = data.get("reserve", 0.0)
        chart.available = data.get("available", chart.budget - chart.reserve)
        
        # Parse pressure
        chart.pressure = data.get("pressure", 0.0)
        chart.load = data.get("load", {})
        
        # Parse threat/affect
        chart.threat_level = data.get("threat", 0.0)
        chart.freeze_level = data.get("freeze", 0.0)
        chart.greed_level = data.get("greed", 0.0)
        
        # Parse process health
        chart.active_processes = data.get("active_processes", 0)
        chart.mode = data.get("mode", "unknown")
        chart.health_score = data.get("health", 1.0)
        
        # Parse memory
        chart.memory_load = data.get("memory_load", 0.0)
        chart.replay_count = data.get("replay_count", 0)
        
        chart.timestamp = data.get("timestamp", time.time())
        return chart

    def build_sensory_state(
        self,
        external_data: Optional[Dict[str, Any]] = None,
        semantic_data: Optional[Dict[str, Any]] = None,
        internal_data: Optional[Dict[str, Any]] = None,
        anchors: Optional[List[Dict[str, Any]]] = None
    ) -> 'SensoryState':
        """Build complete sensory state from raw data."""
        bundle = SensoryBundle()
        
        if external_data:
            bundle.external = self.to_external_chart(external_data)
        
        if semantic_data:
            bundle.semantic = self.to_semantic_chart(semantic_data)
        
        if internal_data:
            bundle.internal = self.to_internal_chart(internal_data)
        
        if anchors:
            bundle.anchors = anchors
        
        # Sync individual charts
        self.external = bundle.external
        self.semantic = bundle.semantic
        self.internal = bundle.internal
        self.bundle = bundle
        
        return self


# Alias for canonical naming (per spec §5)
SensoryManifold = SensoryState


# Convenience function
def create_sensory_state(
    external: Optional[Dict[str, Any]] = None,
    semantic: Optional[Dict[str, Any]] = None,
    internal: Optional[Dict[str, Any]] = None,
    anchors: Optional[List[Dict[str, Any]]] = None
) -> SensoryState:
    """Create a sensory state from raw data."""
    state = SensoryState()
    return state.build_sensory_state(external, semantic, internal, anchors)
