"""
Salience for GM-OS Sensory Manifold.

Defines salience scoring for percept fields:
- Novelty score (how new is this information)
- Task relevance score (does this relate to current goals)
- Surprise score (deviation from expectations)
- Combined salience output
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import math
import time


@dataclass
class SalienceScore:
    """Individual salience component score."""
    novelty: float = 0.0       # 0.0 to 1.0
    relevance: float = 0.0      # 0.0 to 1.0
    surprise: float = 0.0       # 0.0 to 1.0
    
    # Weights for combining scores
    novelty_weight: float = 0.33
    relevance_weight: float = 0.34
    surprise_weight: float = 0.33
    
    @property
    def combined(self) -> float:
        """Combined salience score."""
        return (
            self.novelty * self.novelty_weight +
            self.relevance * self.relevance_weight +
            self.surprise * self.surprise_weight
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "novelty": self.novelty,
            "relevance": self.relevance,
            "surprise": self.surprise,
            "combined": self.combined
        }


@dataclass
class SalienceResult:
    """Result of salience computation for multiple percepts."""
    scores: Dict[str, SalienceScore] = field(default_factory=dict)
    ranked_percepts: List[tuple] = field(default_factory=list)  # (percept_id, score)
    timestamp: float = field(default_factory=time.time)
    
    def get_top(self, n: int = 5) -> List[tuple]:
        """Get top N most salient percepts."""
        return self.ranked_percepts[:n]
    
    def get_above_threshold(self, threshold: float = 0.5) -> List[tuple]:
        """Get percepts above threshold."""
        return [(pid, score) for pid, score in self.ranked_percepts if score.combined >= threshold]


class SalienceTracker:
    """Tracks history for novelty and surprise computation."""
    
    def __init__(self, history_size: int = 100):
        self._history: List[Dict[str, Any]] = []
        self._history_size = history_size
        self._seen_features: Set[str] = set()
    
    def add_observation(self, observation: Dict[str, Any]) -> None:
        """Add observation to history."""
        self._history.append(observation)
        if len(self._history) > self._history_size:
            self._history.pop(0)
        
        # Track seen features
        if "features" in observation:
            for f in observation.get("features", []):
                self._seen_features.add(str(f))
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get observation history."""
        return self._history.copy()
    
    def is_novel(self, features: List[Any]) -> float:
        """Compute novelty based on how many features are new."""
        if not features:
            return 0.0
        
        new_count = sum(1 for f in features if str(f) not in self._seen_features)
        return new_count / len(features)


def compute_salience(
    sensory_state: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None,
    tracker: Optional[SalienceTracker] = None
) -> SalienceResult:
    """
    Compute salience scores for sensory state.
    
    Args:
        sensory_state: Current sensory state (from manifold)
        task_context: Optional task/goal context for relevance scoring
        tracker: Optional SalienceTracker for history-based scoring
        
    Returns:
        SalienceResult with scores for each percept
    """
    result = SalienceResult()
    
    # Extract percepts from sensory state
    percepts = _extract_percepts(sensory_state)
    
    for percept_id, percept_data in percepts:
        score = SalienceScore()
        
        # Compute novelty
        score.novelty = compute_novelty(percept_data, tracker)
        
        # Compute relevance
        score.relevance = compute_task_relevance(percept_data, task_context)
        
        # Compute surprise
        score.surprise = compute_surprise(percept_data, tracker)
        
        result.scores[percept_id] = score
    
    # Rank percepts by combined score
    result.ranked_percepts = sorted(
        result.scores.items(),
        key=lambda x: x[1].combined,
        reverse=True
    )
    
    # Update tracker
    if tracker:
        tracker.add_observation(sensory_state)
    
    return result


def compute_novelty(
    percept_data: Dict[str, Any],
    tracker: Optional[SalienceTracker] = None
) -> float:
    """
    Compute novelty score for a percept.
    
    Novelty = how new/unexpected this information is compared to history.
    """
    # If no tracker, use timestamp-based novelty (newer = more novel)
    if tracker is None:
        timestamp = percept_data.get("timestamp", time.time())
        age = time.time() - timestamp
        # Newer (less than 1 second) = high novelty
        return max(0.0, 1.0 - (age / 10.0))
    
    # Use tracker for feature-based novelty
    features = percept_data.get("features", [])
    return tracker.is_novel(features)


def compute_task_relevance(
    percept_data: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None
) -> float:
    """
    Compute task relevance score.
    
    Relevance = how much this percept relates to current goals/tasks.
    """
    if task_context is None:
        # Default: use explicit relevance flag or object type
        return percept_data.get("relevance", 0.5)
    
    relevance = 0.0
    
    # Check for goal alignment
    goals = task_context.get("goals", [])
    if goals and "tags" in percept_data:
        tags = set(percept_data.get("tags", []))
        for goal in goals:
            if goal in tags:
                relevance += 0.5
    
    # Check for task type alignment
    task_type = task_context.get("task_type", "")
    if task_type and percept_data.get("type") == task_type:
        relevance += 0.5
    
    return min(1.0, relevance)


def compute_surprise(
    percept_data: Dict[str, Any],
    tracker: Optional[SalienceTracker] = None
) -> float:
    """
    Compute surprise score.
    
    Surprise = deviation from expected values based on history.
    """
    if tracker is None:
        # Default: use confidence as inverse of certainty
        confidence = percept_data.get("confidence", 0.5)
        return 1.0 - confidence
    
    # Compute deviation from history
    history = tracker.get_history()
    if not history:
        return 0.5  # No history = moderate surprise
    
    # Compare to most recent observation
    last = history[-1]
    
    # Check for value changes
    surprise = 0.0
    changes = 0
    
    for key in ["value", "position", "state", "status"]:
        if key in percept_data and key in last:
            if percept_data[key] != last[key]:
                surprise += 0.25
                changes += 1
    
    # Check for unexpected new events
    if percept_data.get("is_new_event", False):
        surprise += 0.5
    
    return min(1.0, surprise)


def rank_by_salience(
    sensory_state: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None,
    top_k: int = 5
) -> List[tuple]:
    """
    Get top K percepts ranked by salience.
    
    Convenience function combining salience computation and ranking.
    """
    result = compute_salience(sensory_state, task_context)
    return result.get_top(top_k)


def adjust_weights(
    salience_result: SalienceResult,
    novelty_weight: Optional[float] = None,
    relevance_weight: Optional[float] = None,
    surprise_weight: Optional[float] = None
) -> SalienceResult:
    """
    Adjust salience weights and recompute combined scores.
    """
    for score in salience_result.scores.values():
        if novelty_weight is not None:
            score.novelty_weight = novelty_weight
        if relevance_weight is not None:
            score.relevance_weight = relevance_weight
        if surprise_weight is not None:
            score.surprise_weight = surprise_weight
    
    # Re-rank
    salience_result.ranked_percepts = sorted(
        salience_result.scores.items(),
        key=lambda x: x[1].combined,
        reverse=True
    )
    
    return salience_result


def _extract_percepts(sensory_state: Dict[str, Any]) -> List[tuple]:
    """Extract percepts from sensory state."""
    percepts = []
    
    # Handle ExternalChart-style state
    if "objects" in sensory_state:
        for i, obj in enumerate(sensory_state.get("objects", [])):
            percepts.append((f"object_{i}", obj))
    
    if "events" in sensory_state:
        for i, event in enumerate(sensory_state.get("events", [])):
            percepts.append((f"event_{i}", event))
    
    # Handle InternalChart-style state
    if "budget" in sensory_state:
        percepts.append(("budget", sensory_state.get("budget", {})))
    
    if "affect" in sensory_state:
        percepts.append(("affect", sensory_state.get("affect", {})))
    
    # Handle raw dict-style state
    for key, value in sensory_state.items():
        if isinstance(value, dict) and key not in ["objects", "events", "budget", "affect"]:
            percepts.append((key, value))
    
    return percepts
