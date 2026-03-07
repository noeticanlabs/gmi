"""
Memory Relevance Engine for GM-OS Memory Fabric.

Decides which memories are worth retrieving under budget constraints.
Single source of truth for retrieval ranking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class RelevanceScore:
    """Score for a memory episode."""
    episode_id: str
    semantic_score: float = 0.0
    context_score: float = 0.0
    recency_score: float = 0.0
    anchor_score: float = 0.0
    validation_score: float = 0.0
    total_score: float = 0.0
    cost_to_replay: float = 0.0
    
    def compute_total(
        self,
        alpha_semantic: float = 0.3,
        alpha_context: float = 0.2,
        alpha_recency: float = 0.2,
        alpha_anchor: float = 0.15,
        alpha_validation: float = 0.15
    ) -> float:
        """
        Compute weighted total score.
        
        S(q,e_i) = α_s*S_semantic + α_c*S_context + α_r*S_recency + α_a*S_anchor + α_v*S_validation
        """
        self.total_score = (
            alpha_semantic * self.semantic_score +
            alpha_context * self.context_score +
            alpha_recency * self.recency_score +
            alpha_anchor * self.anchor_score +
            alpha_validation * self.validation_score
        )
        # Subtract replay cost penalty
        self.total_score -= self.cost_to_replay
        return self.total_score


class MemoryRelevanceEngine:
    """
    Memory retrieval ranking system.
    
    Scores episodes by:
    - semantic similarity (embedding overlap)
    - context relevance (tag overlap)
    - recency (temporal decay)
    - reality anchor weight (external validation)
    - validation score (contradiction/reward signals)
    """
    
    def __init__(
        self,
        alpha_semantic: float = 0.3,
        alpha_context: float = 0.2,
        alpha_recency: float = 0.2,
        alpha_anchor: float = 0.15,
        alpha_validation: float = 0.15
    ):
        self.alpha_semantic = alpha_semantic
        self.alpha_context = alpha_context
        self.alpha_recency = alpha_recency
        self.alpha_anchor = alpha_anchor
        self.alpha_validation = alpha_validation
    
    def score_episode(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> RelevanceScore:
        """Score a single episode against a query."""
        score = RelevanceScore(episode_id=episode.get("id", ""))
        
        # Semantic similarity (embedding-based)
        score.semantic_score = self._compute_semantic(episode, query)
        
        # Context overlap (tag-based)
        score.context_score = self._compute_context(episode, query)
        
        # Recency decay
        score.recency_score = self._compute_recency(episode)
        
        # Anchor weight
        score.anchor_score = self._compute_anchor(episode)
        
        # Validation score
        score.validation_score = self._compute_validation(episode)
        
        # Cost to replay
        score.cost_to_replay = episode.get("replay_cost", 0.0)
        
        # Compute total
        score.compute_total(
            self.alpha_semantic,
            self.alpha_context,
            self.alpha_recency,
            self.alpha_anchor,
            self.alpha_validation
        )
        
        return score
    
    def rank_candidates(
        self,
        episodes: List[Dict[str, Any]],
        query: Dict[str, Any]
    ) -> List[RelevanceScore]:
        """Rank all candidate episodes."""
        scores = [self.score_episode(ep, query) for ep in episodes]
        return sorted(scores, key=lambda s: s.total_score, reverse=True)
    
    def select_top_k(
        self,
        episodes: List[Dict[str, Any]],
        query: Dict[str, Any],
        k: int,
        budget: Optional[float] = None
    ) -> List[RelevanceScore]:
        """Select top-k episodes under budget constraint."""
        ranked = self.rank_candidates(episodes, query)
        
        if budget is None:
            return ranked[:k]
        
        selected = []
        total_cost = 0.0
        for score in ranked:
            if total_cost + score.cost_to_replay <= budget:
                selected.append(score)
                total_cost += score.cost_to_replay
                if len(selected) >= k:
                    break
        
        return selected
    
    def filter_by_budget(
        self,
        episodes: List[Dict[str, Any]],
        budget: float
    ) -> List[Dict[str, Any]]:
        """Filter episodes that fit within budget."""
        affordable = []
        total_cost = 0.0
        
        for ep in episodes:
            cost = ep.get("replay_cost", 0.0)
            if total_cost + cost <= budget:
                affordable.append(ep)
                total_cost += cost
        
        return affordable
    
    def _compute_semantic(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Compute semantic similarity score."""
        # Placeholder: would use embedding similarity
        ep_emb = episode.get("embedding", [])
        query_emb = query.get("embedding", [])
        
        if not ep_emb or not query_emb:
            return 0.0
        
        # Cosine similarity
        ep_arr = np.array(ep_emb)
        query_arr = np.array(query_emb)
        
        norm_ep = np.linalg.norm(ep_arr)
        norm_query = np.linalg.norm(query_arr)
        
        if norm_ep == 0 or norm_query == 0:
            return 0.0
        
        return float(np.dot(ep_arr, query_arr) / (norm_ep * norm_query))
    
    def _compute_context(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Compute context/tag overlap score."""
        ep_tags = set(episode.get("tags", []))
        query_tags = set(query.get("tags", []))
        
        if not ep_tags or not query_tags:
            return 0.0
        
        overlap = len(ep_tags & query_tags)
        union = len(ep_tags | query_tags)
        
        return overlap / union if union > 0 else 0.0
    
    def _compute_recency(self, episode: Dict[str, Any]) -> float:
        """Compute recency decay score."""
        import time
        timestamp = episode.get("timestamp", time.time())
        age = time.time() - timestamp
        
        # Exponential decay with half-life of 1 hour
        half_life = 3600.0
        return np.exp(-age / half_life)
    
    def _compute_anchor(self, episode: Dict[str, Any]) -> float:
        """Compute reality anchor bonus."""
        anchor_weight = episode.get("anchor_weight", 0.0)
        return float(min(1.0, anchor_weight))
    
    def _compute_validation(self, episode: Dict[str, Any]) -> float:
        """Compute validation/contradiction score."""
        # Positive for validated, negative for contradictions
        validation = episode.get("validation_score", 0.0)
        contradiction = episode.get("contradiction_count", 0)
        return float(validation - 0.1 * contradiction)
