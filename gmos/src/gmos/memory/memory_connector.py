"""
Memory Connector for GM-OS.

Integrates the memory layer with the hosted GMI agent:
- Archives episodes with proper tagging
- Retrieves relevant memories via relevance engine
- Ensures replayed content never gets external-anchor status without validation
- Connects retrieval cost to policy/verifier

Usage:
    from gmos.memory.memory_connector import MemoryConnector
    
    connector = MemoryConnector()
    
    # Archive current episode
    connector.archive_episode(state_data, action_taken, result)
    
    # Retrieve relevant memories
    relevant = connector.retrieve(query, budget_for_retrieval=0.5)
    
    # Check if retrieved content is validated
    is_validated = connector.is_external_validated(memory_episode)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import time


@dataclass
class ArchivedEpisode:
    """An archived cognitive episode."""
    episode_id: str
    state_snapshot: Dict[str, Any]
    action_taken: str
    result: str
    timestamp: float
    is_validated: bool = False  # Has this been externally validated?
    source: str = "external"  # "external", "replay", "generated"


@dataclass
class RetrievedMemory:
    """A retrieved memory with relevance score."""
    episode: ArchivedEpisode
    relevance_score: float
    cost_to_replay: float
    is_validated: bool


class MemoryConnector:
    """
    Connects memory layer to cognitive processing.
    
    Responsibilities:
    1. Archive episodes with proper source tagging
    2. Retrieve relevant memories via relevance scoring
    3. Ensure replayed content is never marked as externally validated
    4. Track retrieval costs for policy/verifier
    
    This ensures:
    - Replayed memory never gets external-anchor status without validation
    - Retrieval cost is tracked and can influence policy
    """
    
    def __init__(self, max_episodes: int = 1000):
        self.max_episodes = max_episodes
        self._episodes: List[ArchivedEpisode] = []
        self._episode_counter = 0
        
        # Retrieval cost tracking
        self._total_retrieval_cost = 0.0
        self._retrieval_count = 0
    
    def archive_episode(
        self,
        state_data: Dict[str, Any],
        action_taken: str,
        result: Dict[str, Any],
        source: str = "external"
    ) -> str:
        """
        Archive a cognitive episode.
        
        Args:
            state_data: Current state snapshot
            action_taken: Action that was taken
            result: Result of the action
            source: Source of the episode ("external", "replay", "generated")
            
        Returns:
            Episode ID
        """
        self._episode_counter += 1
        episode_id = f"ep_{self._episode_counter}_{int(time.time())}"
        
        episode = ArchivedEpisode(
            episode_id=episode_id,
            state_snapshot=state_data,
            action_taken=action_taken,
            result=result.get("status", "unknown"),
            timestamp=time.time(),
            is_validated=(source == "external"),  # Only external is validated by default
            source=source
        )
        
        self._episodes.append(episode)
        
        # Trim if over max
        if len(self._episodes) > self.max_episodes:
            self._episodes = self._episodes[-self.max_episodes:]
        
        return episode_id
    
    def retrieve(
        self,
        query: Dict[str, Any],
        budget_for_retrieval: float = 0.5,
        max_episodes: int = 5
    ) -> List[RetrievedMemory]:
        """
        Retrieve relevant memories.
        
        Args:
            query: Query dict with keys to match against episodes
            budget_for_retrieval: Budget available for retrieval
            max_episodes: Maximum number of episodes to retrieve
            
        Returns:
            List of RetrievedMemory sorted by relevance
        """
        # Simple relevance scoring (in production, use MemoryRelevanceEngine)
        scored_episodes = []
        
        for episode in self._episodes:
            # Compute relevance score
            score = self._compute_relevance(episode, query)
            
            # Compute cost (simulated - in production, more complex)
            cost = self._compute_retrieval_cost(episode)
            
            # Skip if over budget
            if cost > budget_for_retrieval:
                continue
            
            if score > 0:
                scored_episodes.append(RetrievedMemory(
                    episode=episode,
                    relevance_score=score,
                    cost_to_replay=cost,
                    is_validated=episode.is_validated
                ))
        
        # Sort by relevance
        scored_episodes.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Track retrieval cost
        top_episodes = scored_episodes[:max_episodes]
        total_cost = sum(e.cost_to_replay for e in top_episodes)
        self._total_retrieval_cost += total_cost
        self._retrieval_count += 1
        
        return top_episodes
    
    def _compute_relevance(
        self,
        episode: ArchivedEpisode,
        query: Dict[str, Any]
    ) -> float:
        """Compute simple relevance score."""
        score = 0.0
        
        # Match query keys against episode state
        for key, value in query.items():
            if key in episode.state_snapshot:
                if episode.state_snapshot[key] == value:
                    score += 1.0
                elif isinstance(value, list) and isinstance(episode.state_snapshot[key], list):
                    # Partial match for lists
                    common = set(value) & set(episode.state_snapshot[key])
                    score += len(common) / max(len(value), 1)
        
        # Boost validated external episodes
        if episode.is_validated and episode.source == "external":
            score *= 1.5
        
        return score
    
    def _compute_retrieval_cost(self, episode: ArchivedEpisode) -> float:
        """Compute cost to retrieve an episode."""
        # Base cost
        base_cost = 0.1
        
        # Older episodes cost more (simulated)
        age = time.time() - episode.timestamp
        age_cost = min(0.5, age / 10000)  # Cap at 0.5
        
        # Replayed episodes cost extra (need reconstruction)
        if episode.source == "replay":
            age_cost += 0.2
        
        return base_cost + age_cost
    
    def is_external_validated(self, episode: ArchivedEpisode) -> bool:
        """
        Check if an episode has external validation.
        
        This is critical: replayed content should NEVER have
        external-anchor status without explicit validation.
        
        Args:
            episode: The episode to check
            
        Returns:
            True only if externally validated
        """
        return episode.is_validated and episode.source == "external"
    
    def mark_validated(self, episode_id: str) -> bool:
        """
        Mark an episode as externally validated.
        
        This should only be called after external validation.
        
        Args:
            episode_id: ID of episode to validate
            
        Returns:
            True if found and marked
        """
        for episode in self._episodes:
            if episode.episode_id == episode_id:
                episode.is_validated = True
                return True
        return False
    
    def get_retrieval_cost_stats(self) -> Dict[str, float]:
        """Get retrieval cost statistics for policy/verifier."""
        if self._retrieval_count == 0:
            return {
                "total_cost": 0.0,
                "avg_cost": 0.0,
                "retrieval_count": 0
            }
        
        return {
            "total_cost": self._total_retrieval_cost,
            "avg_cost": self._total_retrieval_cost / self._retrieval_count,
            "retrieval_count": self._retrieval_count
        }
    
    def get_recent_episodes(self, n: int = 10) -> List[ArchivedEpisode]:
        """Get N most recent episodes."""
        return self._episodes[-n:]
    
    def clear(self) -> None:
        """Clear all episodes (call at session boundary)."""
        self._episodes.clear()
        self._episode_counter = 0
        self._total_retrieval_cost = 0.0
        self._retrieval_count = 0


def create_memory_connector(max_episodes: int = 1000) -> MemoryConnector:
    """Factory function to create a memory connector."""
    return MemoryConnector(max_episodes=max_episodes)
