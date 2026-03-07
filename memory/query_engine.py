"""
Memory Query Engine for the GMI Memory System.

Provides structured interface for querying the episodic archive.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
import numpy as np

from memory.archive import EpisodicArchive
from memory.episode import Episode, EpisodeSummary


@dataclass
class MemoryQuery:
    """
    A structured memory query.
    
    Query types:
    - semantic_similarity: by embedding distance
    - causal_relevance: by action-outcome chain
    - contextual_proximity: by state similarity
    - recency: by step index
    - reward_history: by success/failure patterns
    - anomaly_markers: by unusual patterns
    """
    query_type: str  # "semantic", "contextual", "recency", "reward", "anomaly"
    
    # Query parameters
    density: Optional[np.ndarray] = None
    embedding: Optional[np.ndarray] = None
    tags: List[str] = None
    decision_filter: Optional[str] = None
    
    # Filters
    min_step: Optional[int] = None
    max_step: Optional[int] = None
    require_reality_anchor: bool = False
    
    # Limits
    max_results: int = 5
    
    # Weights for scoring
    weight_semantic: float = 0.3
    weight_contextual: float = 0.3
    weight_recency: float = 0.2
    weight_validation: float = 0.2


class QueryEngine:
    """
    Memory query engine.
    
    Provides structured interface for querying the episodic archive.
    """
    
    def __init__(self, archive: EpisodicArchive):
        self.archive = archive
    
    def query(self, query: MemoryQuery) -> List[Tuple[Episode, float]]:
        """
        Execute a query and return ranked episodes.
        
        Args:
            query: MemoryQuery to execute
            
        Returns:
            List of (episode, score) tuples, sorted by score descending
        """
        # Get candidates based on query type
        candidates = self._get_candidates(query)
        
        if not candidates:
            return []
        
        # Score each candidate
        scored = []
        for ep in candidates:
            score = self._compute_score(query, ep)
            scored.append((ep, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return scored[:query.max_results]
    
    def _get_candidates(self, query: MemoryQuery) -> List[Episode]:
        """Get candidate episodes based on query type and filters."""
        candidates = []
        
        # Get base candidates
        if query.tags:
            candidates = self.archive.search_by_tags(query.tags)
        elif query.decision_filter:
            candidates = self.archive.get_by_decision(query.decision_filter)
        else:
            candidates = self.archive.get_recent(20)
        
        # Apply filters
        filtered = []
        for ep in candidates:
            # Step filter
            if query.min_step is not None and ep.step_index < query.min_step:
                continue
            if query.max_step is not None and ep.step_index > query.max_step:
                continue
            
            # Reality anchor filter
            if query.require_reality_anchor and not ep.is_reality_anchor:
                continue
            
            filtered.append(ep)
        
        return filtered
    
    def _compute_score(self, query: MemoryQuery, episode: Episode) -> float:
        """
        Compute relevance score for an episode.
        
        S(q, e) = α_s * S_semantic + α_c * S_context + α_r * S_recency + α_v * S_validation
        """
        score = 0.0
        
        # Semantic similarity
        if query.density is not None and query.weight_semantic > 0:
            sim = self._cosine_similarity(episode.density_summary, query.density)
            score += query.weight_semantic * (1.0 + sim)
        
        # Contextual proximity
        if query.weight_contextual > 0:
            context_score = self._contextual_score(query, episode)
            score += query.weight_contextual * context_score
        
        # Recency
        if query.weight_recency > 0:
            recency = self._recency_score(episode)
            score += query.weight_recency * recency
        
        # Validation/reality anchor
        if query.weight_validation > 0:
            validation = self._validation_score(episode)
            score += query.weight_validation * validation
        
        return score
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def _contextual_score(self, query: MemoryQuery, episode: Episode) -> float:
        """Compute contextual proximity score."""
        # Simple implementation: check if episode metadata matches query
        score = 0.5  # Base score
        
        # Check decision match
        if query.decision_filter and episode.decision == query.decision_filter:
            score += 0.5
        
        return score
    
    def _recency_score(self, episode: Episode) -> float:
        """Compute recency score."""
        total_episodes = len(self.archive)
        if total_episodes == 0:
            return 0.5
        
        # More recent = higher score
        recency = 1.0 - (episode.step_index / total_episodes)
        return recency
    
    def _validation_score(self, episode: Episode) -> float:
        """Compute validation/reality anchor score."""
        if episode.is_reality_anchor:
            return 1.0
        
        # Check for external validation
        if episode.validation_source:
            return 0.7
        
        return 0.3
    
    # Convenience query methods
    
    def find_similar_states(
        self, 
        density: np.ndarray, 
        n: int = 5
    ) -> List[Episode]:
        """Find episodes with similar state densities."""
        query = MemoryQuery(
            query_type="semantic",
            density=density,
            max_results=n
        )
        return [ep for ep, _ in self.query(query)]
    
    def find_recent(self, n: int = 5) -> List[Episode]:
        """Find the n most recent episodes."""
        return self.archive.get_recent(n)
    
    def find_by_decision(
        self, 
        decision: str, 
        n: int = 10
    ) -> List[Episode]:
        """Find episodes by decision type."""
        return self.archive.get_by_decision(decision)[:n]
    
    def find_failures(self, n: int = 5) -> List[Episode]:
        """Find recent failed episodes (for learning)."""
        return self.find_by_decision("REJECTED", n)
    
    def find_successes(self, n: int = 5) -> List[Episode]:
        """Find recent successful episodes."""
        return self.find_by_decision("ACCEPTED", n)
    
    def find_reality_anchors(self, n: int = 5) -> List[Episode]:
        """Find reality-anchored episodes."""
        return self.archive.get_reality_anchors()[:n]
