"""
Glyph Space for GM-OS Symbolic Layer.

Defines the symbolic coordinate space with Noetica-compatible glyph structures.

This module defines how symbols occupy structured space, not how they are interpreted.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import numpy as np


class GlyphType(Enum):
    """Types of glyphs."""
    CONCEPT = "concept"         # Abstract concept
    ENTITY = "entity"           # Named entity
    RELATION = "relation"       # Relational structure
    ACTION = "action"           # Action/event
    MODIFIER = "modifier"       # Qualifier/modifier
    PREDICATE = "predicate"      # Truth claim
    QUERY = "query"             # Question/goal


@dataclass
class GlyphCoordinate:
    """
    Symbolic glyph coordinate.
    
    Represents a symbol's position in the glyph space.
    """
    x: float
    y: float
    z: Optional[float] = None
    glyph_type: GlyphType = GlyphType.CONCEPT
    
    def distance_to(self, other: 'GlyphCoordinate') -> float:
        """Compute Euclidean distance to another coordinate."""
        d = (self.x - other.x) ** 2 + (self.y - other.y) ** 2
        if self.z is not None and other.z is not None:
            d += (self.z - other.z) ** 2
        return np.sqrt(d)
    
    def to_vector(self) -> List[float]:
        """Convert to vector representation."""
        if self.z is not None:
            return [self.x, self.y, self.z]
        return [self.x, self.y]
    
    @classmethod
    def from_vector(cls, vector: List[float], glyph_type: GlyphType = GlyphType.CONCEPT) -> 'GlyphCoordinate':
        """Create from vector."""
        if len(vector) >= 3:
            return cls(x=vector[0], y=vector[1], z=vector[2], glyph_type=glyph_type)
        return cls(x=vector[0], y=vector[1], glyph_type=glyph_type)


@dataclass
class GlyphEmbedding:
    """
    Glyph embedding with optional feature vector.
    
    Provides both coordinate position and semantic features.
    """
    coordinate: GlyphCoordinate
    features: Optional[np.ndarray] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.features is None:
            coord_vec = self.coordinate.to_vector()
            self.features = np.array(coord_vec)
    
    def similarity(self, other: 'GlyphEmbedding') -> float:
        """Compute cosine similarity."""
        a = self.features
        b = other.features
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "coordinate": {
                "x": self.coordinate.x,
                "y": self.coordinate.y,
                "z": self.coordinate.z,
                "glyph_type": self.coordinate.glyph_type.value,
            },
            "features": self.features.tolist() if self.features is not None else None,
            "confidence": self.confidence,
        }


@dataclass
class GlyphState:
    """
    Container for glyph state.
    
    Holds multiple glyphs with their coordinates and embeddings.
    """
    glyphs: Dict[str, GlyphEmbedding] = field(default_factory=dict)
    
    # Grouping
    groups: Dict[str, List[str]] = field(default_factory=dict)
    
    # Neighborhood structure
    neighborhoods: Dict[str, List[str]] = field(default_factory=dict)
    
    # Metadata
    timestamp: float = 0.0
    source: str = "unknown"
    
    def add_glyph(
        self,
        glyph_id: str,
        coordinate: GlyphCoordinate,
        features: Optional[np.ndarray] = None,
        confidence: float = 1.0,
        group: Optional[str] = None
    ) -> GlyphEmbedding:
        """Add a glyph to the state."""
        embedding = GlyphEmbedding(
            coordinate=coordinate,
            features=features,
            confidence=confidence
        )
        self.glyphs[glyph_id] = embedding
        
        # Add to group if specified
        if group:
            if group not in self.groups:
                self.groups[group] = []
            self.groups[group].append(glyph_id)
        
        return embedding
    
    def get_glyph(self, glyph_id: str) -> Optional[GlyphEmbedding]:
        """Get a glyph by ID."""
        return self.glyphs.get(glyph_id)
    
    def find_neighbors(
        self,
        glyph_id: str,
        radius: float = 1.0
    ) -> List[Tuple[str, float]]:
        """Find neighboring glyphs within radius."""
        if glyph_id not in self.glyphs:
            return []
        
        target = self.glyphs[glyph_id]
        neighbors = []
        
        for gid, embedding in self.glyphs.items():
            if gid == glyph_id:
                continue
            
            dist = target.coordinate.distance_to(embedding.coordinate)
            if dist <= radius:
                neighbors.append((gid, dist))
        
        return sorted(neighbors, key=lambda x: x[1])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "glyph_count": len(self.glyphs),
            "groups": {k: len(v) for k, v in self.groups.items()},
            "glyphs": {k: v.to_dict() for k, v in self.glyphs.items()},
        }


@dataclass
class GlyphSpace:
    """
    The full glyph space with coordinate system and structure.
    
    Provides the coordinate system for symbolic representations.
    """
    # Space dimensions
    dimension: int = 3
    
    # Coordinate bounds
    x_range: Tuple[float, float] = (-1.0, 1.0)
    y_range: Tuple[float, float] = (-1.0, 1.0)
    z_range: Optional[Tuple[float, float]] = (-1.0, 1.0)
    
    # Space metadata
    space_type: str = "euclidean"
    embedding_dim: int = 64
    
    # Glyph state
    state: GlyphState = field(default_factory=GlyphState)
    
    def create_glyph(
        self,
        glyph_id: str,
        position: List[float],
        glyph_type: GlyphType = GlyphType.CONCEPT,
        confidence: float = 1.0,
        group: Optional[str] = None
    ) -> GlyphEmbedding:
        """Create a glyph at the given position."""
        coordinate = GlyphCoordinate.from_vector(position, glyph_type)
        return self.state.add_glyph(
            glyph_id,
            coordinate,
            confidence=confidence,
            group=group
        )
    
    def project_to_space(self, embedding: np.ndarray) -> GlyphCoordinate:
        """Project an embedding to glyph coordinates."""
        # Simple projection: use first 2-3 dimensions
        if len(embedding) >= 3:
            return GlyphCoordinate(
                x=float(embedding[0]),
                y=float(embedding[1]),
                z=float(embedding[2])
            )
        return GlyphCoordinate(
            x=float(embedding[0]),
            y=float(embedding[1])
        )
    
    def distance(self, glyph_id1: str, glyph_id2: str) -> float:
        """Compute distance between two glyphs."""
        g1 = self.state.get_glyph(glyph_id1)
        g2 = self.state.get_glyph(glyph_id2)
        
        if not g1 or not g2:
            return float('inf')
        
        return g1.coordinate.distance_to(g2.coordinate)
    
    def similarity(self, glyph_id1: str, glyph_id2: str) -> float:
        """Compute similarity between two glyphs."""
        g1 = self.state.get_glyph(glyph_id1)
        g2 = self.state.get_glyph(glyph_id2)
        
        if not g1 or not g2:
            return 0.0
        
        return g1.similarity(g2)


# Convenience function
def create_glyph_space(
    dimension: int = 3,
    embedding_dim: int = 64
) -> GlyphSpace:
    """Create a new glyph space."""
    return GlyphSpace(
        dimension=dimension,
        embedding_dim=embedding_dim
    )
