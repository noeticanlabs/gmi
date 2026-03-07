"""
Semantic Manifold for GM-OS Symbolic Layer.

Defines semantic manifold container and relation bundles:
- SemanticState container
- embed_symbolic_structure() 
- Relation bundles
- Concept composition operator
- Semantic neighborhood logic
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
import numpy as np
import hashlib
import json


@dataclass
class RelationBundle:
    """A bundle of semantic relations between concepts."""
    bundle_id: str
    relations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    
    def add_relation(self, subject: str, predicate: str, obj: str, weight: float = 1.0):
        """Add a relation to the bundle."""
        self.relations.append({
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "weight": weight
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "relations": self.relations,
            "confidence": self.confidence
        }


@dataclass
class Concept:
    """A concept in the semantic manifold."""
    concept_id: str
    features: List[float] = field(default_factory=list)
    relations: List[str] = field(default_factory=list)  # IDs of related concepts
    activation: float = 0.0
    confidence: float = 1.0
    
    def embed(self) -> np.ndarray:
        """Get embedding vector for concept."""
        if self.features:
            return np.array(self.features)
        # Default: hash-based embedding
        h = int(hashlib.sha256(self.concept_id.encode()).hexdigest()[:8], 16)
        return np.array([np.sin(h / 1000), np.cos(h / 1000)])


@dataclass
class SemanticState:
    """Container for semantic state."""
    concepts: Dict[str, Concept] = field(default_factory=dict)
    bundles: Dict[str, RelationBundle] = field(default_factory=dict)
    active_concepts: List[str] = field(default_factory=list)
    
    def add_concept(self, concept: Concept):
        """Add a concept to the state."""
        self.concepts[concept.concept_id] = concept
    
    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID."""
        return self.concepts.get(concept_id)
    
    def get_active(self) -> List[Concept]:
        """Get all active concepts."""
        return [self.concepts[cid] for cid in self.active_concepts if cid in self.concepts]


class SemanticManifold:
    """
    Semantic manifold for symbolic layer.
    
    Provides:
    - Relation bundle management
    - Concept composition
    - Semantic embedding
    - Neighborhood queries
    """
    
    def __init__(self, embedding_dim: int = 64):
        self.embedding_dim = embedding_dim
        self._state = SemanticState()
        self._embeddings: Dict[str, np.ndarray] = {}
    
    @property
    def state(self) -> SemanticState:
        """Get current semantic state."""
        return self._state
    
    def embed_symbolic_structure(self, structure: Dict[str, Any]) -> np.ndarray:
        """
        Embed symbolic structure into manifold coordinates.
        
        Args:
            structure: Dict with keys like "concepts", "relations", "type"
            
        Returns:
            Embedding vector in manifold space
        """
        if not structure:
            return np.zeros(self.embedding_dim)
        
        # Extract concept IDs
        concept_ids = structure.get("concepts", [])
        
        if not concept_ids:
            # Hash-based embedding for structure
            serialized = json.dumps(structure, sort_keys=True)
            h = hashlib.sha256(serialized.encode()).hexdigest()
            return self._hash_to_embedding(h)
        
        # Average embeddings of constituent concepts
        embeddings = []
        for cid in concept_ids:
            if cid in self._embeddings:
                embeddings.append(self._embeddings[cid])
            else:
                # Create default embedding
                h = hashlib.sha256(cid.encode()).hexdigest()
                embeddings.append(self._hash_to_embedding(h))
        
        if embeddings:
            return np.mean(embeddings, axis=0)
        
        return np.zeros(self.embedding_dim)
    
    def _hash_to_embedding(self, h: str) -> np.ndarray:
        """Convert hash to embedding vector."""
        # Use hash bytes to create deterministic embedding
        h_bytes = h.encode()
        # Repeat to get enough bytes
        h_full = (h_bytes * (self.embedding_dim // len(h_bytes) + 1))[:self.embedding_dim]
        return np.array([b / 255.0 for b in h_full[:self.embedding_dim]])
    
    def compose_concepts(
        self, 
        concept_ids: List[str], 
        operation: str = "union"
    ) -> Optional[str]:
        """
        Compose multiple concepts into a new concept.
        
        Args:
            concept_ids: Concepts to compose
            operation: Composition operation ("union", "intersection", "difference")
            
        Returns:
            ID of new composed concept
        """
        if not concept_ids:
            return None
        
        # Get constituent concepts
        concepts = []
        for cid in concept_ids:
            c = self._state.get_concept(cid)
            if c:
                concepts.append(c)
        
        if not concepts:
            return None
        
        # Create composed concept ID
        composed_id = f"{operation}({'+'.join(concept_ids[:3])})"
        
        # Compute composed features
        if operation == "union":
            features = np.mean([c.embed() for c in concepts], axis=0)
        elif operation == "intersection":
            features = np.min([c.embed() for c in concepts], axis=0)
        elif operation == "difference":
            features = concepts[0].embed()
            for c in concepts[1:]:
                features = features - c.embed()
        else:
            features = np.mean([c.embed() for c in concepts], axis=0)
        
        # Create new concept
        new_concept = Concept(
            concept_id=composed_id,
            features=features.tolist(),
            relations=concept_ids.copy(),
            activation=np.mean([c.activation for c in concepts])
        )
        
        self._state.add_concept(new_concept)
        self._embeddings[composed_id] = features
        
        return composed_id
    
    def find_neighbors(
        self, 
        query: np.ndarray, 
        k: int = 5,
        exclude: Optional[Set[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        Find k nearest neighbors in semantic space.
        
        Args:
            query: Query embedding vector
            k: Number of neighbors
            exclude: Set of concept IDs to exclude
            
        Returns:
            List of (concept_id, distance) tuples
        """
        if exclude is None:
            exclude = set()
        
        distances = []
        for cid, emb in self._embeddings.items():
            if cid in exclude:
                continue
            dist = np.linalg.norm(query - emb)
            distances.append((cid, dist))
        
        # Sort by distance
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def semantic_neighborhood(
        self, 
        concept_id: str, 
        radius: float = 0.5
    ) -> List[str]:
        """
        Get all concepts within semantic neighborhood.
        
        Args:
            concept_id: Center concept
            radius: Neighborhood radius
            
        Returns:
            List of concept IDs in neighborhood
        """
        if concept_id not in self._embeddings:
            return []
        
        center = self._embeddings[concept_id]
        neighbors = self.find_neighbors(center, k=100, exclude={concept_id})
        
        return [cid for cid, dist in neighbors if dist <= radius]
    
    def add_bundle(self, bundle: RelationBundle):
        """Add a relation bundle to the manifold."""
        self._state.bundles[bundle.bundle_id] = bundle
    
    def get_bundle(self, bundle_id: str) -> Optional[RelationBundle]:
        """Get a relation bundle by ID."""
        return self._state.bundles.get(bundle_id)
    
    def bind_to_glyph(self, concept_id: str, glyph_id: str):
        """Bind semantic concept to glyph coordinate."""
        # Store binding in concept
        concept = self._state.get_concept(concept_id)
        if concept:
            if "glyph_id" not in concept.relations:
                concept.relations.append(f"glyph:{glyph_id}")


def embed_symbolic_structure(structure: Dict[str, Any]) -> List[float]:
    """
    Embed symbolic structure into manifold coordinates.
    
    This is a convenience function for simple embedding without manifold state.
    
    Args:
        structure: Dict with symbolic structure
        
    Returns:
        Embedding vector as list
    """
    manifold = SemanticManifold()
    embedding = manifold.embed_symbolic_structure(structure)
    return embedding.tolist()


def create_relation_bundle(
    bundle_id: str,
    relations: List[Tuple[str, str, str]]
) -> RelationBundle:
    """
    Create a relation bundle from tuples.
    
    Args:
        bundle_id: Unique ID for the bundle
        relations: List of (subject, predicate, object) tuples
        
    Returns:
        RelationBundle object
    """
    bundle = RelationBundle(bundle_id=bundle_id)
    for subject, predicate, obj in relations:
        bundle.add_relation(subject, predicate, obj)
    return bundle
