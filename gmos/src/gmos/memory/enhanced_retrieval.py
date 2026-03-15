"""
Enhanced Memory Retrieval System for Phase 3

Key improvements over baseline retrieval:
1. Task-specific scoring weights
2. Noise filtering (reject low similarity, contradictory context)
3. Retrieval attribution (why each memory was included)
4. Memory influence control (not blind obedience)

This addresses Phase 2's finding that memory hurt by 9% on diagnosis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

# Use built-in math instead of numpy for portability
import math


class RetrievalStrategy(Enum):
    """Retrieval strategy types."""
    DIAGNOSIS = "diagnosis"      # Task A: classification
    TRIAGE = "triage"            # Task B: action selection
    GENERAL = "general"          # Default


class NoiseFilterMode(Enum):
    """How aggressively to filter noisy memories."""
    OFF = "off"                  # No filtering
    CONSERVATIVE = "conservative"  # High threshold, fewer results
    BALANCED = "balanced"         # Medium threshold
    AGGRESSIVE = "aggressive"     # Low threshold, more filtering


@dataclass
class RetrievalAttribution:
    """Why a memory was retrieved."""
    episode_id: str
    primary_reason: str          # e.g., "symptom_match", "action_outcome"
    score_breakdown: Dict[str, float]
    confidence: float            # How confident we are in this retrieval
    is_noisy: bool              # Flag if this might be noise


@dataclass
class EnhancedRetrievalResult:
    """Result from enhanced retrieval."""
    episode: Dict[str, Any]
    score: float
    attribution: RetrievalAttribution
    should_include: bool        # After noise filtering
    influence_weight: float     # How much this should influence decisions (0-1)


@dataclass
class TaskSpecificWeights:
    """Task-specific weight configuration."""
    # Scoring weights (must sum to ~1.0)
    semantic_weight: float = 0.3
    context_weight: float = 0.2
    recency_weight: float = 0.15
    outcome_weight: float = 0.2   # NEW: action outcome relevance
    anchor_weight: float = 0.15
    
    # Noise filtering thresholds
    min_score_threshold: float = 0.1
    max_noise_ratio: float = 0.3   # Max contradictory signals allowed
    
    # Influence control
    max_influence_weight: float = 0.7  # Memory can't dominate
    min_influence_weight: float = 0.1  # Memory always has some weight
    
    @classmethod
    def for_diagnosis(cls) -> "TaskSpecificWeights":
        """Weights optimized for diagnosis task."""
        return cls(
            semantic_weight=0.35,
            context_weight=0.25,
            recency_weight=0.1,
            outcome_weight=0.1,
            anchor_weight=0.2,
            min_score_threshold=0.15,
            max_noise_ratio=0.25,
            max_influence_weight=0.6,
            min_influence_weight=0.1
        )
    
    @classmethod
    def for_triage(cls) -> "TaskSpecificWeights":
        """Weights optimized for triage/action selection task."""
        return cls(
            semantic_weight=0.25,
            context_weight=0.15,
            recency_weight=0.15,
            outcome_weight=0.35,   # Higher: action-outcome matters more
            anchor_weight=0.1,
            min_score_threshold=0.1,
            max_noise_ratio=0.35,
            max_influence_weight=0.75,
            min_influence_weight=0.15
        )


class NoiseFilter:
    """Filter out noisy or irrelevant memories."""
    
    def __init__(
        self,
        mode: NoiseFilterMode = NoiseFilterMode.BALANCED,
        min_threshold: float = 0.1,
        max_contradiction: float = 0.3
    ):
        self.mode = mode
        self.min_threshold = min_threshold
        self.max_contradiction = max_contradiction
    
    def is_noisy(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any],
        score: float
    ) -> Tuple[bool, str]:
        """Check if a memory episode is too noisy to include."""
        
        # Check minimum threshold
        if self.mode != NoiseFilterMode.OFF and score < self.min_threshold:
            return True, f"score_below_threshold ({score} < {self.min_threshold})"
        
        # Check for contradictory signals
        if self._has_contradiction(episode, query):
            return True, "contradictory_signals"
        
        # Check outcome quality (for triage)
        outcome = episode.get("outcome", "")
        if outcome in ["overreaction", "unnecessary", "missed_issue"]:
            # These outcomes are noise
            return True, f"poor_outcome ({outcome})"
        
        return False, ""
    
    def _has_contradiction(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> bool:
        """Check if episode contradicts query."""
        
        # Handle both list and dict formats for symptoms
        def get_symptom_set(symptoms):
            if isinstance(symptoms, dict):
                return set(symptoms.keys())
            elif isinstance(symptoms, list):
                return set(symptoms)
            return set()
        
        # Check symptom contradiction
        ep_symptoms = get_symptom_set(episode.get("symptoms", {}))
        query_symptoms = get_symptom_set(query.get("symptoms", {}))
        
        # Count overlap vs unique
        overlap = len(ep_symptoms & query_symptoms)
        
        if len(ep_symptoms) > 0:
            contradiction_ratio = 1 - (overlap / len(ep_symptoms))
            if contradiction_ratio > self.max_contradiction:
                return True
        
        return False


class EnhancedRetrievalEngine:
    """
    Enhanced memory retrieval with task-specific optimization.
    
    Key features:
    - Task-adaptive scoring weights
    - Noise filtering
    - Attribution for each retrieval
    - Configurable influence weight
    """
    
    def __init__(
        self,
        strategy: RetrievalStrategy = RetrievalStrategy.GENERAL,
        noise_filter_mode: NoiseFilterMode = NoiseFilterMode.BALANCED,
        default_weights: Optional[TaskSpecificWeights] = None
    ):
        self.strategy = strategy
        self.noise_filter = NoiseFilter(mode=noise_filter_mode)
        
        # Set default weights based on strategy
        if default_weights:
            self.weights = default_weights
        elif strategy == RetrievalStrategy.DIAGNOSIS:
            self.weights = TaskSpecificWeights.for_diagnosis()
        elif strategy == RetrievalStrategy.TRIAGE:
            self.weights = TaskSpecificWeights.for_triage()
        else:
            self.weights = TaskSpecificWeights()
    
    def set_strategy(self, strategy: RetrievalStrategy) -> None:
        """Change retrieval strategy."""
        self.strategy = strategy
        if strategy == RetrievalStrategy.DIAGNOSIS:
            self.weights = TaskSpecificWeights.for_diagnosis()
        elif strategy == RetrievalStrategy.TRIAGE:
            self.weights = TaskSpecificWeights.for_triage()
    
    def retrieve(
        self,
        episodes: List[Dict[str, Any]],
        query: Dict[str, Any],
        top_k: int = 5
    ) -> List[EnhancedRetrievalResult]:
        """
        Retrieve top-k relevant episodes with attribution.
        
        Returns enhanced results with:
        - Score breakdown
        - Attribution (why included)
        - Noise filtering decision
        - Influence weight
        """
        
        # Score all episodes
        scored = []
        for ep in episodes:
            result = self._score_episode(ep, query)
            scored.append(result)
        
        # Sort by score
        scored.sort(key=lambda x: x.score, reverse=True)
        
        # Apply noise filtering and select top-k
        results = []
        for result in scored:
            if len(results) >= top_k:
                break
            
            is_noisy, reason = self.noise_filter.is_noisy(
                result.episode, query, result.score
            )
            
            result.should_include = not is_noisy
            result.attribution.is_noisy = is_noisy
            
            if not is_noisy:
                results.append(result)
        
        # Compute influence weights
        self._compute_influence_weights(results)
        
        return results
    
    def _score_episode(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> EnhancedRetrievalResult:
        """Score a single episode with full attribution."""
        
        # Compute individual scores
        semantic = self._compute_semantic(episode, query)
        context = self._compute_context(episode, query)
        recency = self._compute_recency(episode)
        outcome = self._compute_outcome(episode, query)
        anchor = self._compute_anchor(episode)
        
        # Weighted total
        total = (
            self.weights.semantic_weight * semantic +
            self.weights.context_weight * context +
            self.weights.recency_weight * recency +
            self.weights.outcome_weight * outcome +
            self.weights.anchor_weight * anchor
        )
        
        # Determine primary reason for retrieval
        scores = {
            "semantic": semantic,
            "context": context,
            "recency": recency,
            "outcome": outcome,
            "anchor": anchor
        }
        primary_reason = max(scores, key=scores.get)
        
        # Confidence in this retrieval
        confidence = self._compute_confidence(scores, total)
        
        # Create attribution
        attribution = RetrievalAttribution(
            episode_id=episode.get("id", ""),
            primary_reason=primary_reason,
            score_breakdown=scores,
            confidence=confidence,
            is_noisy=False
        )
        
        return EnhancedRetrievalResult(
            episode=episode,
            score=total,
            attribution=attribution,
            should_include=True,
            influence_weight=1.0  # Will be adjusted later
        )
    
    def _compute_semantic(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Compute semantic similarity (symptom overlap)."""
        
        # Handle both list and dict formats for symptoms
        def get_symptom_set(symptoms):
            if isinstance(symptoms, dict):
                return set(symptoms.keys())
            elif isinstance(symptoms, list):
                # List of indices or values
                return set(symptoms)
            return set()
        
        # Use symptom overlap as proxy for semantic similarity
        ep_symptoms = get_symptom_set(episode.get("symptoms", {}))
        query_symptoms = get_symptom_set(query.get("symptoms", {}))
        
        if not ep_symptoms or not query_symptoms:
            return 0.0
        
        # Jaccard similarity
        intersection = len(ep_symptoms & query_symptoms)
        union = len(ep_symptoms | query_symptoms)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _compute_context(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Compute context relevance."""
        
        ep_context = episode.get("context", {})
        query_context = query.get("context", {})
        
        if not ep_context or not query_context:
            return 0.0
        
        # Equipment type match
        ep_type = ep_context.get("equipment_type", "")
        query_type = query_context.get("equipment_type", "")
        
        if ep_type and query_type and ep_type == query_type:
            return 1.0
        
        return 0.0
    
    def _compute_recency(
        self,
        episode: Dict[str, Any]
    ) -> float:
        """Compute recency score (temporal decay)."""
        
        # Use episode index as proxy for recency
        # Higher index = more recent
        idx = episode.get("episode_index", 0)
        
        # Simple decay: assume max 1000 episodes
        max_idx = 1000
        return min(idx / max_idx, 1.0)
    
    def _compute_outcome(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Compute outcome relevance (important for triage)."""
        
        outcome = episode.get("outcome", "")
        success = episode.get("success", None)
        
        # Strong positive outcomes
        if outcome in ["resolved", "correct_caution", "appropriate_caution", "success"]:
            return 1.0
        # Mild positive
        elif outcome in ["informative", "partial"]:
            return 0.5
        # Negative outcomes
        elif outcome in ["overreaction", "unnecessary", "missed_issue", "inconclusive"]:
            return 0.0
        
        # If no outcome, check success flag
        if success is True:
            return 0.8
        elif success is False:
            return 0.2
        
        return 0.5  # Unknown
    
    @staticmethod
    def _mean(values: List[float]) -> float:
        """Compute mean of a list."""
        return sum(values) / len(values) if values else 0.0
    
    def _compute_anchor(
        self,
        episode: Dict[str, Any]
    ) -> float:
        """Compute reality anchor weight."""
        
        # Verified episodes have higher anchor
        if episode.get("verified", False):
            return 1.0
        
        # Episodes with receipts have medium anchor
        if episode.get("has_receipt", False):
            return 0.7
        
        return 0.3
    
    def _compute_confidence(
        self,
        scores: Dict[str, float],
        total: float
    ) -> float:
        """Compute confidence in this retrieval."""
        
        # High confidence if:
        # 1. Total score is high
        # 2. Scores are not spread evenly (one dominant factor)
        
        if total < 0.1:
            return 0.1
        
        # Check score concentration
        max_score = max(scores.values())
        if max_score > 0.5:
            confidence = 0.7 + 0.3 * max_score
        else:
            confidence = 0.5 + 0.2 * total
        
        return min(confidence, 1.0)
    
    def _compute_influence_weights(
        self,
        results: List[EnhancedRetrievalResult]
    ) -> None:
        """Compute how much each memory should influence decisions."""
        
        if not results:
            return
        
        # Normalize scores to influence weights
        max_score = max(r.score for r in results)
        
        for result in results:
            if max_score > 0:
                # Normalize to [min, max] range
                raw_weight = result.score / max_score
                
                # Apply influence bounds
                result.influence_weight = (
                    self.weights.min_influence_weight +
                    raw_weight * (
                        self.weights.max_influence_weight - 
                        self.weights.min_influence_weight
                    )
                )
            else:
                result.influence_weight = self.weights.min_influence_weight


class AdaptiveRetrievalEngine(EnhancedRetrievalEngine):
    """
    Retrieval engine that adapts based on memory utility.
    
    Tracks which retrieval patterns work and adjusts weights accordingly.
    """
    
    def __init__(
        self,
        strategy: RetrievalStrategy = RetrievalStrategy.GENERAL,
        noise_filter_mode: NoiseFilterMode = NoiseFilterMode.BALANCED
    ):
        super().__init__(strategy, noise_filter_mode)
        
        # Track retrieval utility
        self.utility_history: List[Dict[str, Any]] = []
        self.adaptive_weights = {
            "semantic": 1.0,
            "context": 1.0,
            "recency": 1.0,
            "outcome": 1.0,
            "anchor": 1.0
        }
    
    def record_outcome(
        self,
        retrieved_episodes: List[EnhancedRetrievalResult],
        outcome_success: bool
    ) -> None:
        """Record retrieval outcome for adaptation."""
        
        # Extract which factors were present in successful retrievals
        for result in retrieved_episodes:
            reason = result.attribution.primary_reason
            
            # Update adaptive weights
            if outcome_success:
                self.adaptive_weights[reason] = min(
                    self.adaptive_weights[reason] * 1.1, 2.0
                )
            else:
                self.adaptive_weights[reason] = max(
                    self.adaptive_weights[reason] * 0.9, 0.5
                )
        
        # Store in history
        self.utility_history.append({
            "retrieved_ids": [r.episode.get("id") for r in retrieved_episodes],
            "success": outcome_success,
            "weights": self.adaptive_weights.copy()
        })
    
    def get_adaptive_weights(self) -> Dict[str, float]:
        """Get current adaptive weight multipliers."""
        return self.adaptive_weights.copy()


def create_retrieval_engine(
    task_type: str,
    enable_adaptation: bool = False,
    noise_filter: str = "balanced"
) -> EnhancedRetrievalEngine:
    """Factory function to create appropriate retrieval engine."""
    
    strategy = RetrievalStrategy.GENERAL
    if task_type.lower() in ["diagnosis", "a", "task_a"]:
        strategy = RetrievalStrategy.DIAGNOSIS
    elif task_type.lower() in ["triage", "b", "task_b"]:
        strategy = RetrievalStrategy.TRIAGE
    
    noise_mode = NoiseFilterMode.BALANCED
    if noise_filter.lower() == "off":
        noise_mode = NoiseFilterMode.OFF
    elif noise_filter.lower() == "conservative":
        noise_mode = NoiseFilterMode.CONSERVATIVE
    elif noise_filter.lower() == "aggressive":
        noise_mode = NoiseFilterMode.AGGRESSIVE
    
    if enable_adaptation:
        return AdaptiveRetrievalEngine(strategy, noise_mode)
    else:
        return EnhancedRetrievalEngine(strategy, noise_mode)
