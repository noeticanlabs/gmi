"""
Comparator for the GMI Memory System.

Compare current state with replayed phantom states.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

from gmos.memory.workspace import PhantomState, ComparisonResult


@dataclass
class StateComparison:
    """
    Result of comparing current state with a phantom state.
    
    Computes:
    - state_mismatch: ||ρ_current - ρ_phantom||
    - policy_mismatch: differences in actions
    - cost_discrepancy: expected vs actual costs
    - expectation_error: how wrong was the prediction
    """
    phantom_id: str
    step_index: int
    
    # State differences
    state_mismatch: float
    curvature_difference: float
    
    # Domain metrics differences
    domain_differences: Dict[str, float]
    
    # Potential differences
    potential_before_diff: float
    potential_after_diff: float
    
    # Summary
    total_mismatch: float
    
    # Interpretation
    interpretation: str = ""
    
    @classmethod
    def from_comparison(
        cls,
        phantom: PhantomState,
        current_density: np.ndarray,
        current_curvature: float,
        current_metadata: Dict[str, float],
        comparison: ComparisonResult
    ) -> 'StateComparison':
        """Create from a ComparisonResult."""
        # Compute interpretation
        interp = cls._interpret(comparison)
        
        return cls(
            phantom_id=phantom.episode_id,
            step_index=phantom.metadata.get('step_index', 0),
            state_mismatch=comparison.state_mismatch,
            curvature_difference=comparison.curvature_difference,
            domain_differences=comparison.metadata_delta,
            potential_before_diff=0.0,  # Would need historical data
            potential_after_diff=0.0,
            total_mismatch=comparison.total_mismatch(),
            interpretation=interp
        )
    
    @staticmethod
    def _interpret(comparison: ComparisonResult) -> str:
        """Interpret the comparison result."""
        if comparison.state_mismatch < 0.1:
            return "State largely unchanged since episode"
        elif comparison.state_mismatch < 0.5:
            return "State moderately different from episode"
        else:
            return "State significantly different from episode"


class Comparator:
    """
    Compare operator for the GMI memory system.
    
    Computes differences between current state and replayed memory.
    """
    
    def __init__(self, workspace):
        self.workspace = workspace
    
    def compare(
        self,
        current_density: np.ndarray,
        current_curvature: float,
        current_metadata: Dict[str, float],
        phantom_id: str
    ) -> Optional[StateComparison]:
        """
        Compare current state with a phantom.
        
        Args:
            current_density: Current cognitive density
            current_curvature: Current curvature
            current_metadata: Current domain metrics
            phantom_id: ID of phantom to compare
            
        Returns:
            StateComparison if phantom found
        """
        phantom = self.workspace.get_replay(phantom_id)
        if phantom is None:
            return None
        
        # Perform comparison
        comparison = self.workspace.compare(
            current_density,
            current_curvature,
            current_metadata,
            phantom
        )
        
        # Create result
        return StateComparison.from_comparison(
            phantom,
            current_density,
            current_curvature,
            current_metadata,
            comparison
        )
    
    def compare_all(
        self,
        current_density: np.ndarray,
        current_curvature: float,
        current_metadata: Dict[str, float]
    ) -> List[StateComparison]:
        """
        Compare current state with all active phantoms.
        
        Args:
            current_density: Current cognitive density
            current_curvature: Current curvature
            current_metadata: Current domain metrics
            
        Returns:
            List of StateComparisons
        """
        results = []
        
        for phantom in self.workspace.state.active_replays:
            comparison = self.compare(
                current_density,
                current_curvature,
                current_metadata,
                phantom.episode_id
            )
            if comparison:
                results.append(comparison)
        
        # Sort by mismatch (lowest first = most similar)
        results.sort(key=lambda x: x.total_mismatch)
        
        return results
    
    def find_most_similar(self, current_density: np.ndarray) -> Optional[PhantomState]:
        """
        Find the most similar phantom to current state.
        
        Args:
            current_density: Current density
            
        Returns:
            Most similar PhantomState, or None
        """
        if not self.workspace.state.active_replays:
            return None
        
        best = None
        best_dist = float('inf')
        
        for phantom in self.workspace.state.active_replays:
            dist = np.linalg.norm(current_density - phantom.density)
            if dist < best_dist:
                best_dist = dist
                best = phantom
        
        return best
    
    def generate_insight(self, comparisons: List[StateComparison]) -> str:
        """
        Generate an insight from comparison results.
        
        Args:
            comparisons: List of comparisons
            
        Returns:
            Human-readable insight
        """
        if not comparisons:
            return "No comparisons available"
        
        most_similar = comparisons[0]
        least_similar = comparisons[-1]
        
        return (
            f"Current state most similar to episode {most_similar.phantom_id} "
            f"(mismatch: {most_similar.total_mismatch:.3f}). "
            f"Least similar to {least_similar.phantom_id} "
            f"(mismatch: {least_similar.total_mismatch:.3f}). "
            f"Interpretation: {most_similar.interpretation}"
        )
