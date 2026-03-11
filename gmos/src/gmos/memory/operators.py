"""
Memory Operators for the GMI Memory System.

Five primary operators:
- Write (O_W): Encode current state into episodic record
- Read (O_R): Retrieve memory records matching query
- Replay (O_P): Reconstruct phantom state from episode
- Compare (O_C): Compare current state with replayed memory
- Prune (O_K): Compress archive while preserving auditability
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import time

from gmos.memory.episode import Episode, EpisodeSummary, create_episode
from gmos.memory.archive import EpisodicArchive
from gmos.memory.workspace import Workspace, PhantomState, ComparisonResult
from gmos.memory.budget_costs import MemoryBudgetLaw


@dataclass
class MemoryOperationResult:
    """Result of a memory operation."""
    success: bool
    episode_ids: List[str]
    cost: float
    message: str
    metadata: Dict[str, Any]


class WriteOperator:
    """
    O_W: Write/Encode Operator
    
    Compresses a current lawful state into a new episode and appends to archive.
    
    Write duties:
    - Choose what is worth storing
    - Summarize state
    - Attach costs and outcomes
    - Commit hash links
    - Emit a write receipt
    
    Write cost:
    Σ_W = μ_W * |O_W|² + σ_W
    """
    
    def __init__(
        self, 
        archive: EpisodicArchive,
        budget_law: Optional[MemoryBudgetLaw] = None
    ):
        self.archive = archive
        self.budget_law = budget_law or MemoryBudgetLaw()
        self.min_cost = self.budget_law.sigma_write
    
    def execute(
        self,
        state_density: np.ndarray,
        state_hash_before: str,
        state_hash_after: str,
        potential_before: float,
        potential_after: float,
        action_summary: str,
        decision: str,
        sigma: float = 0.0,
        kappa: float = 0.0,
        metadata: Optional[Dict] = None,
        is_reality_anchor: bool = False,
        validation_source: str = ""
    ) -> MemoryOperationResult:
        """
        Execute write operation: encode state into episode.
        
        Args:
            state_density: Current cognitive density
            state_hash_before: Hash of state before transition
            state_hash_after: Hash of state after transition
            potential_before: Potential before
            potential_after: Potential after
            action_summary: Description of action taken
            decision: Decision ("ACCEPTED", "REJECTED", "HALT")
            sigma: Metabolic cost
            kappa: Allowed defect
            metadata: Additional metadata
            is_reality_anchor: Is this tied to external receipt?
            validation_source: Source of validation
            
        Returns:
            MemoryOperationResult
        """
        # Compute cost
        operation_magnitude = len(state_density)
        cost = self.budget_law.cost_write(operation_magnitude)
        
        # Check budget
        if cost < 0:
            return MemoryOperationResult(
                success=False,
                episode_ids=[],
                cost=cost,
                message="Budget exhausted",
                metadata={}
            )
        
        # Create episode
        step_index = len(self.archive)
        episode = create_episode(
            step_index=step_index,
            state_before_hash=state_hash_before,
            state_after_hash=state_hash_after,
            density_before=state_density,
            potential_before=potential_before,
            potential_after=potential_after,
            action_summary=action_summary,
            decision=decision,
            sigma=sigma,
            kappa=kappa,
            metadata=metadata
        )
        
        # Mark as reality anchor if applicable
        if is_reality_anchor:
            episode.is_reality_anchor = True
            episode.validation_source = validation_source
        
        # Append to archive
        self.archive.append(episode)
        
        return MemoryOperationResult(
            success=True,
            episode_ids=[episode.episode_id],
            cost=cost,
            message=f"Episode {episode.episode_id} written",
            metadata={'step_index': step_index, 'is_reality_anchor': is_reality_anchor}
        )


class ReadOperator:
    """
    O_R: Read/Retrieval Operator
    
    Retrieves memory records matching query.
    
    Query types:
    - semantic_similarity: by embedding distance
    - causal_relevance: by action-outcome chain
    - contextual_proximity: by state similarity
    - recency: by step index
    - reward_history: by success/failure
    - anomaly_markers: by unusual patterns
    
    Read cost:
    Σ_R = μ_R * |O_R|² + σ_R
    """
    
    def __init__(
        self,
        archive: EpisodicArchive,
        budget_law: Optional[MemoryBudgetLaw] = None
    ):
        self.archive = archive
        self.budget_law = budget_law or MemoryBudgetLaw()
        self.min_cost = self.budget_law.sigma_read
    
    def execute(
        self,
        query_density: np.ndarray,
        query_embedding: Optional[np.ndarray] = None,
        decision_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_results: int = 5,
        budget: float = float('inf')
    ) -> Tuple[List[Episode], float]:
        """
        Execute read operation: retrieve episodes matching query.
        
        Args:
            query_density: Density to compare against
            query_embedding: Optional embedding for semantic search
            decision_filter: Filter by decision type
            tags: Filter by tags
            max_results: Maximum number of results
            budget: Available budget for operation
            
        Returns:
            (matching_episodes, cost)
        """
        # Compute cost
        operation_magnitude = len(query_density)
        cost = self.budget_law.cost_read(operation_magnitude)
        
        if cost > budget:
            return [], cost
        
        # Get candidate episodes
        candidates = self._get_candidates(decision_filter, tags)
        
        if not candidates:
            return [], cost
        
        # Score candidates
        scored = []
        for ep in candidates:
            score = self._compute_relevance(
                ep, query_density, query_embedding
            )
            scored.append((ep, score))
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        results = [ep for ep, _ in scored[:max_results]]
        
        return results, cost
    
    def _get_candidates(
        self, 
        decision_filter: Optional[str],
        tags: Optional[List[str]]
    ) -> List[Episode]:
        """Get candidate episodes based on filters."""
        if tags:
            return self.archive.search_by_tags(tags)
        elif decision_filter:
            return self.archive.get_by_decision(decision_filter)
        else:
            return self.archive.get_recent(20)  # Default to recent
    
    def _compute_relevance(
        self,
        episode: Episode,
        query_density: np.ndarray,
        query_embedding: Optional[np.ndarray]
    ) -> float:
        """Compute relevance score for an episode."""
        # Base score starts at 1.0
        score = 1.0
        
        # Recency bonus (more recent = higher score)
        recency_factor = 1.0 / (1.0 + 0.1 * (len(self.archive) - episode.step_index))
        score *= (1.0 + recency_factor)
        
        # Reality anchor bonus
        if episode.is_reality_anchor:
            score *= 2.0
        
        # State similarity (if query density available)
        if query_density is not None:
            similarity = self._cosine_similarity(
                episode.density_summary, query_density
            )
            score *= (1.0 + similarity)
        
        return score
    
    def _cosine_similarity(
        self, 
        a: np.ndarray, 
        b: np.ndarray
    ) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class ReplayOperator:
    """
    O_P: Replay/Reconstruction Operator
    
    Expands an episode into a phantom state for internal inspection.
    
    Replay uses:
    - Recall prior state
    - Compare prior and current gradients
    - Inspect old failures
    - Load a scenario for branching
    
    Replay cost:
    Σ_P = μ_P * |O_P|² + σ_P (more expensive than read)
    """
    
    def __init__(
        self,
        workspace: Workspace,
        budget_law: Optional[MemoryBudgetLaw] = None
    ):
        self.workspace = workspace
        self.budget_law = budget_law or MemoryBudgetLaw()
        self.min_cost = self.budget_law.sigma_replay
    
    def execute(
        self,
        episode: Episode,
        budget: float = float('inf')
    ) -> Tuple[Optional[PhantomState], float]:
        """
        Execute replay: reconstruct phantom from episode.
        
        Args:
            episode: Episode to replay
            budget: Available budget
            
        Returns:
            (phantom_state, cost)
        """
        # Compute cost
        operation_magnitude = len(episode.density_summary)
        cost = self.budget_law.cost_replay(operation_magnitude)
        
        if cost > budget:
            return None, cost
        
        # Reconstruct phantom
        phantom = self.workspace.replay(episode)
        
        return phantom, cost


class CompareOperator:
    """
    O_C: Compare Operator
    
    Computes differences between current state and replayed memory:
    - State mismatch
    - Policy mismatch
    - Cost discrepancy
    - Expectation error
    
    Compare cost:
    Σ_C = μ_C * |O_C|² + σ_C
    """
    
    def __init__(
        self,
        workspace: Workspace,
        budget_law: Optional[MemoryBudgetLaw] = None
    ):
        self.workspace = workspace
        self.budget_law = budget_law or MemoryBudgetLaw()
        self.min_cost = self.budget_law.sigma_compare
    
    def execute(
        self,
        current_density: np.ndarray,
        current_curvature: float,
        current_metadata: Dict[str, float],
        episode_id: str,
        budget: float = float('inf')
    ) -> Tuple[Optional[ComparisonResult], float]:
        """
        Execute compare: compare current state with phantom.
        
        Args:
            current_density: Current cognitive density
            current_curvature: Current curvature
            current_metadata: Current domain metrics
            episode_id: Episode/phantom to compare
            budget: Available budget
            
        Returns:
            (comparison_result, cost)
        """
        # Compute cost
        operation_magnitude = len(current_density)
        cost = self.budget_law.cost_compare(operation_magnitude)
        
        if cost > budget:
            return None, cost
        
        # Get phantom from workspace
        phantom = self.workspace.get_replay(episode_id)
        if phantom is None:
            return None, cost
        
        # Compare
        comparison = self.workspace.compare(
            current_density,
            current_curvature,
            current_metadata,
            phantom
        )
        
        return comparison, cost


class PruneOperator:
    """
    O_K: Prune/Consolidate Operator
    
    Compresses the archive while preserving auditability.
    
    - Compress redundant episodes
    - Merge near-duplicates
    - Retain high-salience episodes
    - Demote stale entries
    - Keep cryptographic summary links
    
    Important: Pruning must preserve auditability!
    No silent deletion - all operations create receipts.
    """
    
    def __init__(
        self,
        archive: EpisodicArchive,
        budget_law: Optional[MemoryBudgetLaw] = None
    ):
        self.archive = archive
        self.budget_law = budget_law or MemoryBudgetLaw()
        self.min_cost = self.budget_law.sigma_prune
    
    def consolidate(
        self,
        similarity_threshold: float = 0.95,
        min_recent_episodes: int = 10
    ) -> Dict[str, Any]:
        """
        Consolidate the archive.
        
        Args:
            similarity_threshold: Threshold for merging similar episodes
            min_recent_episodes: Minimum recent episodes to keep
            
        Returns:
            Consolidation report
        """
        # This is a simplified implementation
        # Real implementation would use clustering, etc.
        
        original_count = len(self.archive)
        
        # For now, just mark the archive as consolidated
        # A full implementation would compress and create slab receipts
        
        return {
            'original_count': original_count,
            'consolidated_count': original_count,  # No compression in this version
            'slabs_created': 0,
            'message': 'Consolidation placeholder - implement clustering for production'
        }
    
    def create_slab_receipt(
        self,
        start_idx: int,
        end_idx: int
    ) -> Dict[str, Any]:
        """
        Create a proof over a compressed block (slab).
        
        Args:
            start_idx: Start index of slab
            end_idx: End index of slab
            
        Returns:
            Slab receipt
        """
        if start_idx < 0 or end_idx > len(self.archive):
            raise ValueError("Invalid slab range")
        
        episodes = self.archive.episodes[start_idx:end_idx]
        
        # Create hash of all episodes in slab
        import hashlib
        combined = "".join(ep.hash() for ep in episodes)
        slab_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return {
            'start_idx': start_idx,
            'end_idx': end_idx,
            'count': len(episodes),
            'slab_hash': slab_hash,
            'first_episode_id': episodes[0].episode_id if episodes else "",
            'last_episode_id': episodes[-1].episode_id if episodes else ""
        }


class MemoryOperatorFactory:
    """
    Factory for creating memory operators.
    """
    
    def __init__(
        self,
        archive: EpisodicArchive,
        workspace: Workspace,
        budget_law: Optional[MemoryBudgetLaw] = None
    ):
        self.archive = archive
        self.workspace = workspace
        self.budget_law = budget_law or MemoryBudgetLaw()
    
    def create_write_operator(self) -> WriteOperator:
        return WriteOperator(self.archive, self.budget_law)
    
    def create_read_operator(self) -> ReadOperator:
        return ReadOperator(self.archive, self.budget_law)
    
    def create_replay_operator(self) -> ReplayOperator:
        return ReplayOperator(self.workspace, self.budget_law)
    
    def create_compare_operator(self) -> CompareOperator:
        return CompareOperator(self.workspace, self.budget_law)
    
    def create_prune_operator(self) -> PruneOperator:
        return PruneOperator(self.archive, self.budget_law)
