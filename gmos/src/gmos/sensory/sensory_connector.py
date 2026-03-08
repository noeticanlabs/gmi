"""
Sensory Connector for GM-OS.

Integrates the sensory layer with the hosted GMI agent:
- Projects raw observations into manifold coordinates
- Computes salience scores (novelty, relevance, surprise)
- Passes filtered percepts to the policy

Usage:
    from gmos.sensory.projection import project_world_state
    from gmos.sensory.salience import SalienceTracker
    
    # In hosted agent or main loop
    connector = SensoryConnector()
    
    # Process observation
    sensory_state = connector.process_observation(raw_observation)
    
    # Get top percepts for policy
    top_percepts = connector.get_top_percepts(sensory_state, n=3)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from gmos.sensory.manifold import (
    ExternalChart,
    InternalChart, 
    SensoryState,
    create_sensory_state
)
from gmos.sensory.projection import project_world_state, project_internal_state
from gmos.sensory.salience import SalienceTracker, SalienceScore, SalienceResult


@dataclass
class ProcessedPercept:
    """A processed percept ready for policy consumption."""
    percept_id: str
    features: Dict[str, Any]
    salience: SalienceScore
    source: str  # "external", "internal", "replay"
    timestamp: float


class SensoryConnector:
    """
    Connects sensory layer to cognitive processing.
    
    Responsibilities:
    1. Project raw observations into manifold charts
    2. Compute salience scores for each percept
    3. Rank percepts by salience
    4. Provide filtered input to policy
    
    Usage:
        connector = SensoryConnector()
        
        # Process incoming observation
        sensory_state = connector.process_observation(
            {"objects": [{"id": "ball", "position": [1, 2]}], ...}
        )
        
        # Get top percepts for current step
        top_percepts = connector.get_top_percepts(sensory_state, n=3)
    """
    
    def __init__(
        self,
        novelty_weight: float = 0.33,
        relevance_weight: float = 0.34,
        surprise_weight: float = 0.33,
        history_size: int = 100
    ):
        self.salience_tracker = SalienceTracker(history_size=history_size)
        
        # Salience weights
        self.novelty_weight = novelty_weight
        self.relevance_weight = relevance_weight
        self.surprise_weight = surprise_weight
        
        # Current processed percepts
        self._current_percepts: Dict[str, ProcessedPercept] = {}
        self._percept_counter = 0
    
    def process_observation(
        self,
        observation: Dict[str, Any],
        current_goal: Optional[str] = None
    ) -> SensoryState:
        """
        Process a raw observation into a SensoryState.
        
        Args:
            observation: Raw observation from environment
            current_goal: Optional goal for relevance scoring
            
        Returns:
            SensoryState with projected charts and salience
        """
        # Project into external chart
        external_chart = project_world_state(observation)
        
        # Create internal chart (can be extended with budget/affect state)
        internal_chart = self._create_internal_chart(observation)
        
        # Create sensory state
        sensory_state = create_sensory_state(
            external=external_chart,
            internal=internal_chart
        )
        
        # Compute salience for each percept
        self._compute_salience(sensory_state, current_goal)
        
        return sensory_state
    
    def _create_internal_chart(self, observation: Dict[str, Any]) -> InternalChart:
        """Create internal chart from observation."""
        chart = InternalChart()
        
        # Extract budget/affect from observation if present
        chart.budget_level = observation.get("budget_level", 0.5)
        chart.affect_state = observation.get("affect", {})
        chart.process_health = observation.get("health", 1.0)
        
        return chart
    
    def _compute_salience(
        self,
        sensory_state: SensoryState,
        current_goal: Optional[str]
    ) -> None:
        """Compute salience for percepts in sensory state."""
        self._current_percepts.clear()
        
        # Process external objects
        for i, obj in enumerate(sensory_state.external.objects):
            percept_id = f"obj_{i}"
            
            # Create observation for salience tracker
            obs = {
                "percept_id": percept_id,
                "features": obj,
                "timestamp": sensory_state.external.timestamp
            }
            self.salience_tracker.add_observation(obs)
            
            # Compute salience scores
            novelty = self.salience_tracker.compute_novelty(percept_id)
            relevance = self._compute_relevance(obj, current_goal)
            surprise = self.salience_tracker.compute_surprise(percept_id)
            
            salience = SalienceScore(
                novelty=novelty,
                relevance=relevance,
                surprise=surprise,
                novelty_weight=self.novelty_weight,
                relevance_weight=self.relevance_weight,
                surprise_weight=self.surprise_weight
            )
            
            self._current_percepts[percept_id] = ProcessedPercept(
                percept_id=percept_id,
                features=obj,
                salience=salience,
                source="external",
                timestamp=sensory_state.external.timestamp
            )
        
        # Process external events
        for i, event in enumerate(sensory_state.external.events):
            percept_id = f"event_{i}"
            
            obs = {
                "percept_id": percept_id,
                "features": event,
                "timestamp": sensory_state.external.timestamp,
                "type": "event"
            }
            self.salience_tracker.add_observation(obs)
            
            novelty = self.salience_tracker.compute_novelty(percept_id)
            relevance = self._compute_relevance(event, current_goal)
            surprise = self.salience_tracker.compute_surprise(percept_id)
            
            salience = SalienceScore(
                novelty=novelty,
                relevance=relevance,
                surprise=surprise,
                novelty_weight=self.novelty_weight,
                relevance_weight=self.relevance_weight,
                surprise_weight=self.surprise_weight
            )
            
            self._current_percepts[percept_id] = ProcessedPercept(
                percept_id=percept_id,
                features=event,
                salience=salience,
                source="external",
                timestamp=sensory_state.external.timestamp
            )
    
    def _compute_relevance(
        self,
        features: Dict[str, Any],
        current_goal: Optional[str]
    ) -> float:
        """Compute task relevance score."""
        if current_goal is None:
            # Default: moderate relevance
            return 0.5
        
        # Check if features mention goal-related content
        goal_mentions = 0
        total_features = 0
        
        for key, value in features.items():
            total_features += 1
            if isinstance(value, str) and current_goal.lower() in value.lower():
                goal_mentions += 1
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, str) and current_goal.lower() in v.lower():
                        goal_mentions += 1
        
        if total_features == 0:
            return 0.5
        
        return min(1.0, goal_mentions / total_features * 2)
    
    def get_top_percepts(
        self,
        sensory_state: SensoryState,
        n: int = 5,
        threshold: Optional[float] = None
    ) -> List[ProcessedPercept]:
        """
        Get top N most salient percepts.
        
        Args:
            sensory_state: Current sensory state
            n: Number of top percepts to return
            threshold: Optional minimum salience threshold
            
        Returns:
            List of top percepts sorted by combined salience
        """
        # Recompute salience if needed
        if not self._current_percepts:
            self._compute_salience(sensory_state, None)
        
        # Sort by combined salience
        sorted_percepts = sorted(
            self._current_percepts.values(),
            key=lambda p: p.salience.combined,
            reverse=True
        )
        
        # Filter by threshold if provided
        if threshold is not None:
            sorted_percepts = [
                p for p in sorted_percepts 
                if p.salience.combined >= threshold
            ]
        
        return sorted_percepts[:n]
    
    def get_percepts_for_policy(self, n: int = 3) -> Dict[str, Any]:
        """
        Get percepts formatted for policy consumption.
        
        Returns:
            Dict with keys:
            - top_percepts: list of top percept features
            - salience_scores: dict of percept_id -> combined score
            - source_mix: dict of source -> count
        """
        if not self._current_percepts:
            return {
                "top_percepts": [],
                "salience_scores": {},
                "source_mix": {}
            }
        
        top = self.get_top_percepts(None, n=n)
        
        return {
            "top_percepts": [p.features for p in top],
            "salience_scores": {p.percept_id: p.salience.combined for p in top},
            "source_mix": self._count_sources()
        }
    
    def _count_sources(self) -> Dict[str, int]:
        """Count percepts by source."""
        counts = {}
        for p in self._current_percepts.values():
            counts[p.source] = counts.get(p.source, 0) + 1
        return counts
    
    def mark_as_replayed(self, percept_ids: List[str]) -> None:
        """
        Mark specific percepts as replayed (phantom) content.
        
        This is used when memory replay generates content that should
        be tagged distinctly from external content.
        
        Args:
            percept_ids: List of percept IDs to mark as replayed
        """
        for pid in percept_ids:
            if pid in self._current_percepts:
                self._current_percepts[pid].source = "replay"
    
    def clear(self) -> None:
        """Clear current percepts (call at step boundary)."""
        self._current_percepts.clear()


def create_sensory_connector(
    novelty_weight: float = 0.33,
    relevance_weight: float = 0.34,
    surprise_weight: float = 0.33
) -> SensoryConnector:
    """Factory function to create a sensory connector."""
    return SensoryConnector(
        novelty_weight=novelty_weight,
        relevance_weight=relevance_weight,
        surprise_weight=surprise_weight
    )
