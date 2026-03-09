"""
Semantic Loop for GM-OS GMI Agent.

Canonical implementation of the GMI Semantic Loop.

The semantic loop operator: σ: Z × M × S → S_sem
Maps latent state through memory to produce semantic representation.

This module integrates with:
- gmos.symbolic.semantic_manifold: For semantic processing
- gmos.symbolic.glyph_embedder: For text-to-vector embedding
- gmos.agents.gmi.state: For state representation
- gmos.memory: For memory context
"""

import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

# Canonical imports (GM-OS)
from gmos.symbolic.semantic_manifold import SemanticManifold, SemanticState, Concept, RelationBundle
from gmos.symbolic.glyph_embedder import GlyphEmbedder, get_default_embedder
from gmos.symbolic.glyph_space import GlyphType
from gmos.agents.gmi.state import State as CognitiveState


@dataclass
class SemanticRepresentation:
    """
    The output of the semantic loop - a grounded semantic representation.
    
    Contains:
    - embedding: Vector representation in semantic space
    - concepts: Extracted concepts
    - relations: Discovered relations
    - grounding_score: How well the representation is grounded
    """
    embedding: np.ndarray
    concepts: List[Concept]
    relations: List[RelationBundle]
    grounding_score: float
    attention_weights: Optional[np.ndarray] = None


class SemanticLoop:
    """
    The Semantic Loop processes cognitive state to extract semantic meaning.
    
    According to gmi_canon_spec.md:
    - Maps latent state through memory to produce semantic representation
    - Integrates with sensory manifold for grounded meaning
    - Uses glyph embedder for text-symbolic processing
    
    The semantic loop:
    1. Takes current cognitive state + sensory input + memory context
    2. Extracts semantic features through the glyph embedder
    3. Queries semantic manifold for relevant concepts
    4. Generates grounded semantic representation
    """
    
    def __init__(
        self,
        embedder: Optional[GlyphEmbedder] = None,
        semantic_manifold: Optional[SemanticManifold] = None,
        attention_dim: int = 64
    ):
        """
        Initialize the Semantic Loop.
        
        Args:
            embedder: GlyphEmbedder for text-to-vector (defaults to global)
            semantic_manifold: SemanticManifold for concept storage (creates new if None)
            attention_dim: Dimension of attention weights
        """
        self.embedder = embedder or get_default_embedder()
        self.manifold = semantic_manifold or SemanticManifold()
        self.attention_dim = attention_dim
        
        # Semantic processing parameters
        self.grounding_threshold = 0.5
        self.concept_activation_threshold = 0.1
        
        # Alias for backward compatibility
        self.semantic_state = self.manifold._state
        
    def process(
        self,
        state: CognitiveState,
        sensory_input: Optional[str] = None,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> SemanticRepresentation:
        """
        Process cognitive state to extract semantic representation.
        
        Args:
            state: Current cognitive state
            sensory_input: Optional sensory text input
            memory_context: Optional memory context dict
            
        Returns:
            SemanticRepresentation with extracted meaning
        """
        # Step 1: Extract base embedding from state coordinates
        state_embedding = self._state_to_embedding(state)
        
        # Step 2: If sensory input provided, integrate it
        if sensory_input:
            sensory_embedding = self.embedder.embed(sensory_input)
            # Fuse state and sensory embeddings
            state_embedding = self._fuse_embeddings(state_embedding, sensory_embedding)
        
        # Step 3: Extract concepts from the embedding
        concepts = self._extract_concepts(state_embedding)
        
        # Step 4: Query semantic manifold for relevant relations
        relations = self._query_relations(concepts)
        
        # Step 5: Compute grounding score
        grounding_score = self._compute_grounding(concepts, relations)
        
        # Step 6: Generate attention weights
        attention_weights = self._compute_attention(state_embedding, concepts)
        
        return SemanticRepresentation(
            embedding=state_embedding,
            concepts=concepts,
            relations=relations,
            grounding_score=grounding_score,
            attention_weights=attention_weights
        )
    
    def _state_to_embedding(self, state: CognitiveState) -> np.ndarray:
        """
        Convert cognitive state to semantic embedding.
        
        Args:
            state: CognitiveState object
            
        Returns:
            Embedding vector
        """
        # Use state coordinates as base embedding
        return state.x.copy() if hasattr(state, 'x') else np.array(state)
    
    def _fuse_embeddings(
        self,
        state_emb: np.ndarray,
        sensory_emb: np.ndarray,
        fusion_weight: float = 0.5
    ) -> np.ndarray:
        """
        Fuse state and sensory embeddings.
        
        Args:
            state_emb: State embedding
            sensory_emb: Sensory embedding
            fusion_weight: Weight for sensory (1-fusion_weight for state)
            
        Returns:
            Fused embedding
        """
        # Ensure same dimension
        min_dim = min(len(state_emb), len(sensory_emb))
        
        # Simple linear fusion
        fused = np.zeros(min_dim)
        fused += fusion_weight * sensory_emb[:min_dim]
        fused += (1 - fusion_weight) * state_emb[:min_dim]
        
        return fused
    
    def _extract_concepts(self, embedding: np.ndarray) -> List[Concept]:
        """
        Extract concepts from embedding using semantic manifold.
        
        Args:
            embedding: Input embedding vector
            
        Returns:
            List of activated concepts
        """
        # Use manifold's find_neighbors to get relevant concepts
        # This returns concept IDs, we need to get the actual Concept objects
        neighbor_ids = self.manifold.find_neighbors(embedding, k=5)
        
        activated = []
        for cid in neighbor_ids:
            concept = self.manifold.state.get_concept(cid)
            if concept:
                activated.append(concept)
        
        return activated
    
    def _query_relations(self, concepts: List[Concept]) -> List[RelationBundle]:
        """
        Query semantic manifold for relations between concepts.
        
        Args:
            concepts: List of activated concepts
            
        Returns:
            List of relation bundles
        """
        relations = []
        
        for concept in concepts:
            # Get relations for this concept from semantic state
            concept_relations = self.semantic_state.get_relations(concept.concept_id)
            if concept_relations:
                relations.extend(concept_relations)
        
        return relations
    
    def _compute_grounding(
        self,
        concepts: List[Concept],
        relations: List[RelationBundle]
    ) -> float:
        """
        Compute grounding score - how well concepts are connected.
        
        Args:
            concepts: Activated concepts
            relations: Discovered relations
            
        Returns:
            Grounding score between 0 and 1
        """
        if not concepts:
            return 0.0
        
        # Score based on concept activation and relation density
        concept_score = sum(c.activation for c in concepts) / len(concepts)
        
        # Relation density
        relation_score = min(1.0, len(relations) / max(1, len(concepts)))
        
        # Combined score
        grounding = 0.6 * concept_score + 0.4 * relation_score
        
        return min(1.0, grounding)
    
    def _compute_attention(
        self,
        embedding: np.ndarray,
        concepts: List[Concept]
    ) -> np.ndarray:
        """
        Compute attention weights over concepts.
        
        Args:
            embedding: Current embedding
            concepts: List of concepts
            
        Returns:
            Attention weight vector
        """
        if not concepts:
            return np.array([])
        
        # Compute attention based on embedding similarity
        weights = np.zeros(len(concepts))
        
        for i, concept in enumerate(concepts):
            concept_emb = concept.embed()
            # Cosine similarity
            similarity = np.dot(embedding, concept_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(concept_emb) + 1e-8
            )
            weights[i] = max(0, similarity)
        
        # Normalize
        if weights.sum() > 0:
            weights = weights / weights.sum()
        
        return weights
    
    def add_concept(self, concept: Concept) -> None:
        """
        Add a new concept to the semantic manifold.
        
        Args:
            concept: Concept to add
        """
        self.manifold.state.add_concept(concept)
    
    def add_relation(self, relation: RelationBundle) -> None:
        """
        Add a relation bundle to the semantic manifold.
        
        Args:
            relation: RelationBundle to add
        """
        self.manifold.add_bundle(relation)


# Factory function
def create_semantic_loop(
    embedder: Optional[GlyphEmbedder] = None,
    semantic_manifold: Optional[SemanticManifold] = None
) -> SemanticLoop:
    """
    Create a SemanticLoop instance.
    
    Args:
        embedder: Optional GlyphEmbedder
        semantic_manifold: Optional SemanticManifold
        
    Returns:
        SemanticLoop instance
    """
    return SemanticLoop(embedder=embedder, semantic_manifold=semantic_manifold)


# Default instance
_default_semantic_loop: Optional[SemanticLoop] = None


def get_default_semantic_loop() -> SemanticLoop:
    """Get or create the default SemanticLoop instance."""
    global _default_semantic_loop
    if _default_semantic_loop is None:
        _default_semantic_loop = SemanticLoop()
    return _default_semantic_loop


# Example usage and test
if __name__ == "__main__":
    # Create semantic loop
    loop = create_semantic_loop()
    
    # Create a test state
    state = CognitiveState([1.0, 1.0], budget=10.0)
    
    # Process with sensory input
    result = loop.process(
        state,
        sensory_input="This is a logical reasoning task"
    )
    
    print(f"Semantic Representation:")
    print(f"  Embedding: {result.embedding}")
    print(f"  Concepts: {len(result.concepts)}")
    print(f"  Relations: {len(result.relations)}")
    print(f"  Grounding Score: {result.grounding_score:.3f}")
