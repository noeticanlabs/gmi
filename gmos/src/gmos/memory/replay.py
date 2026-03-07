"""
Replay Engine for the GMI Memory System.

Reconstructs phantom states from episodes for internal inspection.
"""

from typing import Optional, List
import numpy as np

from memory.episode import Episode
from memory.workspace import Workspace, PhantomState


class ReplayEngine:
    """
    Replay engine for reconstructing phantom states.
    
    Expands episodes into phantom states for:
    - Recall of prior states
    - Comparison with current state
    - Inspection of old failures
    - Loading scenarios for branching
    """
    
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
    
    def replay_episode(self, episode: Episode) -> Optional[PhantomState]:
        """
        Reconstruct a phantom state from an episode.
        
        Args:
            episode: Episode to replay
            
        Returns:
            PhantomState if successful
        """
        return self.workspace.replay(episode)
    
    def replay_multiple(
        self, 
        episodes: List[Episode]
    ) -> List[PhantomState]:
        """
        Reconstruct multiple phantom states.
        
        Args:
            episodes: Episodes to replay
            
        Returns:
            List of PhantomStates
        """
        phantoms = []
        for episode in episodes:
            phantom = self.replay_episode(episode)
            if phantom:
                phantoms.append(phantom)
        return phantoms
    
    def replay_recent(self, n: int = 3) -> List[PhantomState]:
        """
        Replay the n most recent episodes.
        
        Args:
            n: Number of episodes to replay
            
        Returns:
            List of PhantomStates
        """
        from memory.archive import get_global_archive
        archive = get_global_archive()
        recent = archive.get_recent(n)
        return self.replay_multiple(recent)
    
    def compare_with_current(
        self,
        phantom: PhantomState,
        current_density: np.ndarray,
        current_curvature: float,
        current_metadata: dict
    ) -> dict:
        """
        Compare a phantom with current state.
        
        Args:
            phantom: Phantom to compare
            current_density: Current density
            current_curvature: Current curvature
            current_metadata: Current metadata
            
        Returns:
            Comparison dict
        """
        comparison = self.workspace.compare(
            current_density,
            current_curvature,
            current_metadata,
            phantom
        )
        
        return {
            'phantom_id': phantom.episode_id,
            'state_mismatch': comparison.state_mismatch,
            'curvature_difference': comparison.curvature_difference,
            'metadata_delta': comparison.metadata_delta,
            'total_mismatch': comparison.total_mismatch()
        }
