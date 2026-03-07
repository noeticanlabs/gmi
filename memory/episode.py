"""
Episode Schema for the Episodic Archive.

Episode records store explicit, readable traces of prior cognition.
Each episode is append-only, hash-linked, and canonical-serialized.
"""

import uuid
import time
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
import numpy as np


def generate_episode_id() -> str:
    """Generate a unique episode identifier."""
    return f"ep_{uuid.uuid4().hex[:12]}"


def compute_hash(obj: Dict) -> str:
    """Compute deterministic hash for chain integrity."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True).encode('utf-8')
    ).hexdigest()


@dataclass
class Episode:
    """
    Canonical episode record for the episodic archive.
    
    Stores compressed, discrete traces of prior cognition and interaction.
    Append-only, hash-linked, never directly rewritable.
    
    Episode schema:
    e_i = (id, t_i, h_i^pre, h_i^post, s_i, a_i, r_i, c_i, m_i)
    
    Where:
    - id: episode identifier
    - t_i: timestamp / local step index
    - h_i^pre, h_i^post: state hashes before/after
    - s_i: compressed state summary
    - a_i: action or internal decision summary
    - r_i: outcome summary
    - c_i: certified cost profile
    - m_i: metadata / tags / semantic descriptors
    """
    # Identity
    episode_id: str = field(default_factory=generate_episode_id)
    step_index: int = 0
    timestamp: float = field(default_factory=time.time)
    
    # State hashes
    state_hash_before: str = ""
    state_hash_after: str = ""
    
    # Compressed state summary (density values)
    density_summary: np.ndarray = field(default_factory=lambda: np.array([0.0]))
    
    # Potential values
    potential_before: float = 0.0
    potential_after: float = 0.0
    
    # Action/decision
    action_summary: str = ""
    decision: str = ""  # "ACCEPTED", "REJECTED", "HALT"
    
    # Cost profile
    cost_sigma: float = 0.0      # Metabolic work
    cost_kappa: float = 0.0     # Allowed defect
    cost_memory_read: float = 0.0   # Memory read cost
    cost_memory_write: float = 0.0  # Memory write cost
    cost_memory_replay: float = 0.0  # Memory replay cost
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_reality_anchor: bool = False  # Tied to external receipt?
    validation_source: str = ""  # "verifier_outcome", "external_measurement", etc.
    
    # Chain links
    chain_digest: str = ""
    prev_episode_id: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert numpy array to list
        if isinstance(data.get('density_summary'), np.ndarray):
            data['density_summary'] = data['density_summary'].tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Episode':
        """Reconstruct from dictionary."""
        if 'density_summary' in data and isinstance(data['density_summary'], list):
            data['density_summary'] = np.array(data['density_summary'])
        return cls(**data)
    
    def hash(self) -> str:
        """Canonical hash for chain integrity."""
        # Create canonical representation (exclude self-referential fields)
        canonical = {
            'episode_id': self.episode_id,
            'step_index': self.step_index,
            'state_hash_before': self.state_hash_before,
            'state_hash_after': self.state_hash_after,
            'potential_before': round(self.potential_before, 6),
            'potential_after': round(self.potential_after, 6),
            'action_summary': self.action_summary,
            'decision': self.decision,
            'cost_sigma': round(self.cost_sigma, 6),
            'cost_kappa': round(self.cost_kappa, 6),
            'cost_memory_read': round(self.cost_memory_read, 6),
            'cost_memory_write': round(self.cost_memory_write, 6),
            'cost_memory_replay': round(self.cost_memory_replay, 6),
            'is_reality_anchor': self.is_reality_anchor,
            'prev_episode_id': self.prev_episode_id,
        }
        return compute_hash(canonical)
    
    def total_cost(self) -> float:
        """Compute total cost of this episode."""
        return (
            self.cost_sigma + 
            self.cost_kappa + 
            self.cost_memory_read + 
            self.cost_memory_write + 
            self.cost_memory_replay
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Episode':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_valid(self) -> bool:
        """Check if episode has minimum required fields."""
        return (
            self.episode_id and
            self.state_hash_before and
            self.state_hash_after and
            self.decision in ("ACCEPTED", "REJECTED", "HALT")
        )


@dataclass
class EpisodeSummary:
    """
    Lightweight summary of an episode for indexing and retrieval.
    Used for fast searching without loading full episode data.
    """
    episode_id: str
    step_index: int
    decision: str
    potential_before: float
    potential_after: float
    is_reality_anchor: bool
    # Semantic descriptors for querying
    tags: list = field(default_factory=list)
    # Embedding for semantic search (optional)
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data


@dataclass
class EpisodeRef:
    """
    Reference to a stored episode with relevance score.
    Used for pointing to episodic memory without storing full episodes.
    """
    episode_id: str
    score: float
    anchor_weight: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            'episode_id': self.episode_id,
            'score': self.score,
            'anchor_weight': self.anchor_weight
        }


# Convenience function to create episode from state transition
def create_episode(
    step_index: int,
    state_before_hash: str,
    state_after_hash: str,
    density_before: np.ndarray,
    potential_before: float,
    potential_after: float,
    action_summary: str,
    decision: str,
    sigma: float = 0.0,
    kappa: float = 0.0,
    prev_episode_id: str = "",
    metadata: Optional[Dict] = None
) -> Episode:
    """
    Factory function to create an episode from a state transition.
    """
    return Episode(
        step_index=step_index,
        state_hash_before=state_before_hash,
        state_hash_after=state_after_hash,
        density_summary=density_before.copy(),
        potential_before=potential_before,
        potential_after=potential_after,
        action_summary=action_summary,
        decision=decision,
        cost_sigma=sigma,
        cost_kappa=kappa,
        prev_episode_id=prev_episode_id,
        metadata=metadata or {}
    )
