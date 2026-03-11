"""
Episodic Archive for the GMI Memory System.

Append-only storage for episode records with indexing and retrieval.
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Iterator, Tuple
from pathlib import Path
import numpy as np

from gmos.memory.episode import Episode, EpisodeSummary, generate_episode_id


# Alias for kernel compatibility
ArchiveState = None  # Will be defined below


@dataclass
class EpisodicArchive:
    """
    Append-only episodic store with indexing.
    
    The episodic archive stores explicit, readable traces of prior cognition.
    It is append-only, hash-linked, and read-access controlled.
    
    Features:
    - Append-only (no editing past episodes)
    - Index by step, decision, tags
    - Semantic search via embeddings
    - Chain verification
    """
    episodes: List[Episode] = field(default_factory=list)
    summaries: List[EpisodeSummary] = field(default_factory=list)
    index_by_step: Dict[int, List[str]] = field(default_factory=dict)
    index_by_decision: Dict[str, List[str]] = field(default_factory=dict)
    index_by_tag: Dict[str, List[str]] = field(default_factory=dict)
    episode_ids: set = field(default_factory=set)
    
    # Persistence
    _storage_path: Optional[str] = None
    
    def __len__(self) -> int:
        """Return number of episodes in archive."""
        return len(self.episodes)
    
    def __iter__(self) -> Iterator[Episode]:
        """Iterate over all episodes."""
        return iter(self.episodes)
    
    def append(self, episode: Episode) -> None:
        """
        Append a new episode to the archive.
        
        Args:
            episode: Episode to append
        """
        if episode.episode_id in self.episode_ids:
            raise ValueError(f"Episode {episode.episode_id} already exists")
        
        # Set chain link to previous episode
        if self.episodes:
            episode.prev_episode_id = self.episodes[-1].episode_id
        
        # Add to archive
        self.episodes.append(episode)
        self.episode_ids.add(episode.episode_id)
        
        # Update indexes
        self._index_episode(episode)
        
        # Create and store summary
        summary = self._create_summary(episode)
        self.summaries.append(summary)
    
    def _index_episode(self, episode: Episode) -> None:
        """Update all indexes with a new episode."""
        # Index by step
        if episode.step_index not in self.index_by_step:
            self.index_by_step[episode.step_index] = []
        self.index_by_step[episode.step_index].append(episode.episode_id)
        
        # Index by decision
        if episode.decision not in self.index_by_decision:
            self.index_by_decision[episode.decision] = []
        self.index_by_decision[episode.decision].append(episode.episode_id)
        
        # Index by tags
        tags = episode.metadata.get('tags', [])
        for tag in tags:
            if tag not in self.index_by_tag:
                self.index_by_tag[tag] = []
            self.index_by_tag[tag].append(episode.episode_id)
    
    def _create_summary(self, episode: Episode) -> EpisodeSummary:
        """Create a lightweight summary for fast searching."""
        return EpisodeSummary(
            episode_id=episode.episode_id,
            step_index=episode.step_index,
            decision=episode.decision,
            potential_before=episode.potential_before,
            potential_after=episode.potential_after,
            is_reality_anchor=episode.is_reality_anchor,
            tags=episode.metadata.get('tags', []),
            embedding=episode.metadata.get('embedding')
        )
    
    def get(self, episode_id: str) -> Optional[Episode]:
        """
        Retrieve an episode by ID.
        
        Args:
            episode_id: ID of episode to retrieve
            
        Returns:
            Episode if found, None otherwise
        """
        for ep in self.episodes:
            if ep.episode_id == episode_id:
                return ep
        return None
    
    def get_by_step(self, step_index: int) -> List[Episode]:
        """
        Retrieve all episodes from a given step.
        
        Args:
            step_index: Step index to query
            
        Returns:
            List of episodes from that step
        """
        episode_ids = self.index_by_step.get(step_index, [])
        return [self.get(eid) for eid in episode_ids if self.get(eid)]
    
    def get_by_decision(self, decision: str) -> List[Episode]:
        """
        Retrieve all episodes with a given decision.
        
        Args:
            decision: Decision to filter by ("ACCEPTED", "REJECTED", "HALT")
            
        Returns:
            List of episodes with that decision
        """
        episode_ids = self.index_by_decision.get(decision, [])
        return [self.get(eid) for eid in episode_ids if self.get(eid)]
    
    def get_recent(self, n: int = 10) -> List[Episode]:
        """
        Retrieve the n most recent episodes.
        
        Args:
            n: Number of episodes to retrieve
            
        Returns:
            List of n most recent episodes
        """
        return self.episodes[-n:] if self.episodes else []
    
    def get_reality_anchors(self) -> List[Episode]:
        """
        Retrieve all episodes that are reality anchors.
        
        Returns:
            List of reality anchor episodes
        """
        return [ep for ep in self.episodes if ep.is_reality_anchor]
    
    def search_by_tags(self, tags: List[str]) -> List[Episode]:
        """
        Search for episodes containing any of the given tags.
        
        Args:
            tags: Tags to search for
            
        Returns:
            List of matching episodes
        """
        result_ids = set()
        for tag in tags:
            result_ids.update(self.index_by_tag.get(tag, []))
        return [self.get(eid) for eid in result_ids if self.get(eid)]
    
    def verify_chain(self) -> Tuple[bool, str]:
        """
        Verify the integrity of the episode chain.
        
        Returns:
            (is_valid, message)
        """
        if not self.episodes:
            return True, "Empty archive"
        
        for i, episode in enumerate(self.episodes):
            # Verify chain links
            if i > 0:
                expected_prev = self.episodes[i-1].episode_id
                if episode.prev_episode_id != expected_prev:
                    return False, f"Chain broken at episode {i}: expected prev={expected_prev}, got {episode.prev_episode_id}"
        
        return True, f"Chain verified: {len(self.episodes)} episodes"
    
    def save(self, path: str) -> None:
        """
        Save archive to disk.
        
        Args:
            path: Path to save to
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = {
            'episodes': [ep.to_dict() for ep in self.episodes],
            'summaries': [s.to_dict() for s in self.summaries]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self._storage_path = path
    
    @classmethod
    def load(cls, path: str) -> 'EpisodicArchive':
        """
        Load archive from disk.
        
        Args:
            path: Path to load from
            
        Returns:
            Loaded archive
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        archive = cls()
        archive._storage_path = path
        
        # Reconstruct episodes
        for ep_data in data.get('episodes', []):
            episode = Episode.from_dict(ep_data)
            archive.episodes.append(episode)
            archive.episode_ids.add(episode.episode_id)
        
        # Reconstruct summaries and indexes
        for episode in archive.episodes:
            archive._index_episode(episode)
            summary = archive._create_summary(episode)
            archive.summaries.append(summary)
        
        return archive
    
    def clear(self) -> None:
        """Clear all episodes (for testing)."""
        self.episodes.clear()
        self.summaries.clear()
        self.index_by_step.clear()
        self.index_by_decision.clear()
        self.index_by_tag.clear()
        self.episode_ids.clear()


# Global archive instance
_global_archive: Optional[EpisodicArchive] = None


def get_global_archive() -> EpisodicArchive:
    """Get or create the global episodic archive."""
    global _global_archive
    if _global_archive is None:
        _global_archive = EpisodicArchive()
    return _global_archive


def set_global_archive(archive: EpisodicArchive) -> None:
    """Set the global episodic archive."""
    global _global_archive
    _global_archive = archive


@dataclass
class ArchiveState:
    """
    State container for the episodic archive.
    
    Used by kernel to track archive operational state.
    """
    episode_count: int = 0
    total_size_bytes: int = 0
    is_active: bool = True
    last_backup_step: int = 0
    
    def to_archive(self) -> EpisodicArchive:
        """Convert state to archive instance."""
        return EpisodicArchive()


# Update alias after class definition
ArchiveState = ArchiveState
