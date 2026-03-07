"""
Reconstructive Workspace for the GMI Memory System.

The workspace is the internal stage where memory becomes experience-like.
It hosts active phantom states, comparisons, and temporary branch inputs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
import time

from memory.episode import Episode


@dataclass
class PhantomState:
    """
    Reconstructed internal phantom state from replay.
    
    A phantom state is NOT a physical state transition.
    It may influence evaluation, guide branch construction, alter action ranking,
    but it cannot directly change the world, generate reward, replenish budget,
    or bypass the verifier.
    
    Components:
    - episode_id: Source episode
    - density: Reconstructed cognitive density
    - phase: Reconstructed directional/phase field
    - curvature: Reconstructed memory curvature
    - metadata: Contextual/semantic metadata
    """
    episode_id: str
    density: np.ndarray
    phase: np.ndarray
    curvature: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    
    # Relevance tracking
    relevance_score: float = 1.0
    access_count: int = 0
    
    def to_state_dict(self) -> Dict[str, Any]:
        """Convert phantom to state dictionary."""
        return {
            'rho': self.density,
            'theta': self.phase,
            'curvature': self.curvature,
            'metadata': self.metadata
        }
    
    def access(self) -> None:
        """Record an access to this phantom."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def age(self) -> float:
        """Return age in seconds."""
        return time.time() - self.created_at


@dataclass
class ComparisonResult:
    """
    Result of comparing current state with a phantom state.
    """
    phantom_id: str
    state_mismatch: float      # ||ρ - ρ̂||
    curvature_difference: float  # |C - Ĉ|
    metadata_delta: Dict[str, float]  # Difference in domain metrics
    expectation_error: float = 0.0
    
    # Computed differences
    potential_difference: float = 0.0
    budget_difference: float = 0.0
    
    def total_mismatch(self) -> float:
        """Compute total mismatch score."""
        return (
            self.state_mismatch + 
            abs(self.curvature_difference) +
            sum(abs(v) for v in self.metadata_delta.values()) +
            abs(self.expectation_error)
        )


@dataclass
class BranchSeed:
    """
    Seed for a counterfactual branch, informed by memory.
    
    A branch may be seeded from:
    - Current state only (blind branch)
    - Current state plus replayed episode (informed branch)
    - Current state plus multiple recalled episodes (multi-modal branch)
    """
    seed_id: str
    base_episode_ids: List[str] = field(default_factory=list)
    density: np.ndarray = None
    phase: np.ndarray = None
    curvature: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Branch parameters
    temperature: float = 1.0  # For stochastic branching
    num_variations: int = 3
    
    created_at: float = field(default_factory=time.time)


@dataclass
class WorkspaceState:
    """
    Volatile active replay states and workspace contents.
    
    The workspace is small and volatile:
    - Finite capacity prevents memory bloat
    - Eviction by age, relevance, expected gain, or budget stress
    """
    active_replays: List[PhantomState] = field(default_factory=list)
    comparisons: List[ComparisonResult] = field(default_factory=list)
    branch_seeds: List[BranchSeed] = field(default_factory=list)
    
    # Configuration
    max_capacity: int = 5
    max_comparisons: int = 10
    max_branch_seeds: int = 3
    
    # Statistics
    total_replays: int = 0
    total_comparisons: int = 0
    
    def add_replay(self, phantom: PhantomState) -> None:
        """
        Add a phantom state to the workspace.
        
        Evicts oldest if at capacity.
        """
        # Evict if at capacity
        if len(self.active_replays) >= self.max_capacity:
            self.evict_oldest()
        
        self.active_replays.append(phantom)
        self.total_replays += 1
    
    def get_replay(self, episode_id: str) -> Optional[PhantomState]:
        """Get a phantom by episode ID."""
        for phantom in self.active_replays:
            if phantom.episode_id == episode_id:
                phantom.access()
                return phantom
        return None
    
    def add_comparison(self, comparison: ComparisonResult) -> None:
        """Add a comparison result."""
        self.comparisons.append(comparison)
        self.total_comparisons += 1
        
        # Trim if too many
        while len(self.comparisons) > self.max_comparisons:
            self.comparisons.pop(0)
    
    def add_branch_seed(self, seed: BranchSeed) -> None:
        """Add a branch seed."""
        self.branch_seeds.append(seed)
        
        # Trim if too many
        while len(self.branch_seeds) > self.max_branch_seeds:
            self.branch_seeds.pop(0)
    
    def evict_oldest(self) -> Optional[PhantomState]:
        """
        Evict the oldest phantom by creation time.
        
        Returns the evicted phantom, or None if workspace empty.
        """
        if not self.active_replays:
            return None
        
        # Sort by age
        self.active_replays.sort(key=lambda p: p.created_at)
        return self.active_replays.pop(0)
    
    def evict_least_relevant(self) -> Optional[PhantomState]:
        """
        Evict the phantom with lowest relevance score.
        
        Returns the evicted phantom, or None if workspace empty.
        """
        if not self.active_replays:
            return None
        
        # Sort by relevance (lowest first)
        self.active_replays.sort(key=lambda p: p.relevance_score)
        return self.active_replays.pop(0)
    
    def evict_by_age(self, max_age: float) -> List[PhantomState]:
        """
        Evict all phantoms older than max_age seconds.
        
        Returns list of evicted phantoms.
        """
        evicted = []
        remaining = []
        
        for phantom in self.active_replays:
            if phantom.age() > max_age:
                evicted.append(phantom)
            else:
                remaining.append(phantom)
        
        self.active_replays = remaining
        return evicted
    
    def clear(self) -> None:
        """Clear all workspace contents."""
        self.active_replays.clear()
        self.comparisons.clear()
        self.branch_seeds.clear()
    
    def is_active(self) -> bool:
        """Check if workspace has any active content."""
        return (
            len(self.active_replays) > 0 or
            len(self.comparisons) > 0 or
            len(self.branch_seeds) > 0
        )
    
    def summary(self) -> Dict[str, Any]:
        """Get workspace summary."""
        return {
            'active_replays': len(self.active_replays),
            'comparisons': len(self.comparisons),
            'branch_seeds': len(self.branch_seeds),
            'total_replays': self.total_replays,
            'total_comparisons': self.total_comparisons,
            'capacity': f"{len(self.active_replays)}/{self.max_capacity}"
        }


class Workspace:
    """
    Workspace manager for reconstructive memory operations.
    
    Provides high-level interface for:
    - Replaying episodes into phantom states
    - Comparing current state with phantoms
    - Generating branch seeds from memory
    """
    def __init__(self, max_capacity: int = 5):
        self.state = WorkspaceState(max_capacity=max_capacity)
    
    def replay(self, episode: Episode) -> PhantomState:
        """
        Reconstruct a phantom state from an episode.
        
        Args:
            episode: Episode to replay
            
        Returns:
            Reconstructed phantom state
        """
        # Reconstruct density from summary (with some noise for variety)
        # In a real system, this would be a learned reconstruction
        density = episode.density_summary.copy()
        
        # Infer phase (direction) from density
        norm = np.linalg.norm(density)
        if norm > 1e-10:
            phase = density / norm
        else:
            phase = np.zeros_like(density)
        
        # Create phantom
        phantom = PhantomState(
            episode_id=episode.episode_id,
            density=density,
            phase=phase,
            curvature=0.0,  # Would be reconstructed from episode
            metadata={
                'step_index': episode.step_index,
                'decision': episode.decision,
                'potential_before': episode.potential_before,
                'potential_after': episode.potential_after,
                'action': episode.action_summary
            }
        )
        
        # Add to workspace
        self.state.add_replay(phantom)
        
        return phantom
    
    def compare(
        self, 
        current_density: np.ndarray,
        current_curvature: float,
        current_metadata: Dict[str, float],
        phantom: PhantomState
    ) -> ComparisonResult:
        """
        Compare current state with a phantom state.
        
        Args:
            current_density: Current cognitive density
            current_curvature: Current curvature
            current_metadata: Current domain metrics
            phantom: Phantom to compare against
            
        Returns:
            Comparison result
        """
        # State mismatch
        state_mismatch = float(np.linalg.norm(current_density - phantom.density))
        
        # Curvature difference
        curvature_diff = current_curvature - phantom.curvature
        
        # Metadata delta
        metadata_delta = {}
        current_meta = current_metadata or {}
        for key in set(list(current_meta.keys()) + list(phantom.metadata.keys())):
            current_val = current_meta.get(key, 0.0)
            phantom_val = phantom.metadata.get(key, 0.0)
            metadata_delta[key] = current_val - phantom_val
        
        # Create comparison
        comparison = ComparisonResult(
            phantom_id=phantom.episode_id,
            state_mismatch=state_mismatch,
            curvature_difference=curvature_diff,
            metadata_delta=metadata_delta
        )
        
        self.state.add_comparison(comparison)
        
        return comparison
    
    def create_branch_seed(
        self,
        episode_ids: List[str],
        current_density: np.ndarray,
        temperature: float = 1.0
    ) -> BranchSeed:
        """
        Create a branch seed informed by memory.
        
        Args:
            episode_ids: Episodes to inform the branch
            current_density: Current density to seed from
            temperature: Branch temperature (higher = more variation)
            
        Returns:
            Branch seed
        """
        import uuid
        
        seed = BranchSeed(
            seed_id=f"seed_{uuid.uuid4().hex[:8]}",
            base_episode_ids=episode_ids,
            density=current_density.copy(),
            temperature=temperature
        )
        
        self.state.add_branch_seed(seed)
        
        return seed
    
    def clear(self) -> None:
        """Clear the workspace."""
        self.state.clear()
    
    def is_empty(self) -> bool:
        """Check if workspace is empty."""
        return not self.state.is_active()
    
    def summary(self) -> Dict[str, Any]:
        """Get workspace summary."""
        return self.state.summary()
