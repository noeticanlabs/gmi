"""
Cognitive State Module for the GMI Universal Cognition Engine.

Provides:
- State: Legacy state representation (x, b)
- CognitiveState: Full multi-manifold state with memory integration
- Proposal: Materialized proposal wrapper
- Instruction: Base transition operator
- CompositeInstruction: Chained operators
"""

import numpy as np
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING

# Import from new potential module
from core.potential import GMIPotential, V_PL, create_potential

if TYPE_CHECKING:
    from memory.episode import EpisodeRef
    from memory.workspace import WorkspaceState


@dataclass
class Proposal:
    """
    A materialized proposal for state transition.
    Typed wrapper around instruction + precomputed result.
    
    Using a dataclass instead of dict prevents:
    - Key typos
    - Missing fields
    - Unclear field meanings
    """
    instruction: 'Instruction'
    x_prime: np.ndarray


class State:
    """
    The cognitive state mapped as a coordinate in the PhaseLoom space.
    z(t) = (x(t), b(t)) representing cognitive coordinates and thermodynamic budget.
    
    This is the legacy representation, kept for backward compatibility.
    For the full multi-manifold state, use CognitiveState.
    """
    def __init__(self, x: list[float], budget: float):
        self.x = np.array(x, dtype=float)  # Continuous cognition state
        self.b = float(budget)             # Thermodynamic budget b >= 0
        
        # Memory integration
        self.curvature: float = 0.0  # From MemoryManifold
        self.domain_metrics: Dict[str, float] = {}  # Domain-specific metrics
        self.episodic_refs: List['EpisodeRef'] = []  # References to episodic memory
        self.workspace_active: bool = False  # Is workspace active?
    
    def compute_potential(self, potential: GMIPotential = None) -> float:
        """
        Compute the GMI potential for this state.
        
        Args:
            potential: GMIPotential instance (creates default if None)
            
        Returns:
            Total potential energy
        """
        if potential is None:
            potential = create_potential()
        
        return potential.total(
            self.x, 
            self.b,
            domain_metrics=self.domain_metrics
        )
    
    def is_admissible(self, potential: GMIPotential = None) -> bool:
        """
        Check if state is admissible (budget > 0).
        
        Args:
            potential: GMIPotential instance
            
        Returns:
            True if state is admissible
        """
        if potential is None:
            potential = create_potential()
        return potential.is_admissible(self.b)

    def hash(self) -> str:
        """Deterministic hash for ledger chain integrity."""
        state_dict = {
            "x": self.x.round(6).tolist(), 
            "b": round(self.b, 6),
            "curvature": round(self.curvature, 6),
            "domain_metrics": {k: round(v, 6) for k, v in self.domain_metrics.items()}
        }
        state_str = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'x': self.x.tolist(),
            'b': self.b,
            'curvature': self.curvature,
            'domain_metrics': self.domain_metrics,
            'hash': self.hash()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'State':
        """Create State from dictionary."""
        state = cls(data['x'], data['b'])
        state.curvature = data.get('curvature', 0.0)
        state.domain_metrics = data.get('domain_metrics', {})
        return state


@dataclass
class CognitiveState:
    """
    Universal cognitive state with typed multi-manifold structure.
    
    z = (ρ, θ, C, E, W, B, Ω)
    
    Components:
    - rho: Continuous cognitive density / embedding field
    - theta: Directional / phase field  
    - C: Passive structural memory / curvature (from MemoryManifold)
    - E: Episodic archive reference (episode IDs)
    - W: Active workspace with phantom states
    - B: Thermodynamic budget (b >= 0)
    - mu: Domain metrics / residuals
    - alpha: Authority / allowed amplification
    - chain_digest: Ledger anchoring metadata
    
    This is the full state representation for the universal cognition engine.
    """
    # Core cognition
    rho: np.ndarray          # Density/embedding field
    theta: np.ndarray        # Phase/direction field
    
    # Memory layers
    curvature: float = 0.0   # Passive structural memory (C)
    episodic_references: List[Any] = field(default_factory=list)  # (E)
    workspace_active: bool = False  # (W) - is workspace active?
    
    # Budget
    budget: float = 10.0     # Thermodynamic budget
    
    # Domain adaptation
    domain_metrics: Dict[str, float] = field(default_factory=dict)
    authority: float = 1.0   # Amplification factor
    
    # Ledger anchoring
    chain_digest: str = ""   # Hash chain position
    step_count: int = 0      # For episode indexing
    
    def __post_init__(self):
        """Ensure arrays are numpy arrays."""
        if not isinstance(self.rho, np.ndarray):
            self.rho = np.array(self.rho, dtype=float)
        if not isinstance(self.theta, np.ndarray):
            self.theta = np.array(self.theta, dtype=float)
    
    def to_vector(self) -> np.ndarray:
        """Flatten to 1D vector for compatibility."""
        parts = [self.rho, self.theta]
        if len(self.domain_metrics) > 0:
            parts.append(np.array(list(self.domain_metrics.values())))
        return np.concatenate(parts)
    
    @classmethod
    def from_vector(cls, vec: np.ndarray, budget: float = 10.0):
        """Reconstruct from flat vector (legacy compatibility)."""
        dim = len(vec) // 2
        rho = vec[:dim]
        theta = vec[dim:]
        return cls(rho=rho, theta=theta, budget=budget)
    
    @classmethod
    def from_legacy(cls, state: State) -> 'CognitiveState':
        """Create CognitiveState from legacy State."""
        dim = len(state.x)
        
        # Infer phase from density
        norm = np.linalg.norm(state.x)
        if norm > 1e-10:
            theta = state.x / norm
        else:
            theta = np.zeros(dim)
        
        return cls(
            rho=state.x.copy(),
            theta=theta,
            curvature=state.curvature,
            budget=state.b,
            domain_metrics=state.domain_metrics.copy(),
            episodic_references=state.episodic_refs.copy(),
            workspace_active=state.workspace_active
        )
    
    def to_legacy(self) -> State:
        """Convert to legacy State representation."""
        return State(self.rho.tolist(), self.budget)
    
    def hash(self) -> str:
        """Deterministic hash for ledger."""
        state_dict = {
            "rho": self.rho.round(6).tolist(),
            "theta": self.theta.round(6).tolist(),
            "curvature": round(self.curvature, 6),
            "budget": round(self.budget, 6),
            "domain_metrics": {k: round(v, 6) for k, v in self.domain_metrics.items()},
            "authority": round(self.authority, 6),
            "chain_digest": self.chain_digest,
            "step_count": self.step_count
        }
        return hashlib.sha256(
            json.dumps(state_dict, sort_keys=True).encode('utf-8')
        ).hexdigest()
    
    def compute_potential(self, potential: GMIPotential = None) -> float:
        """
        Compute the GMI potential for this state.
        
        Args:
            potential: GMIPotential instance
            
        Returns:
            Total potential energy
        """
        if potential is None:
            potential = create_potential()
        
        return potential.total(
            self.rho, 
            self.budget,
            domain_metrics=self.domain_metrics
        )
    
    def is_admissible(self, potential: GMIPotential = None) -> bool:
        """Check if state is admissible."""
        if potential is None:
            potential = create_potential()
        return potential.is_admissible(self.budget)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'rho': self.rho.tolist(),
            'theta': self.theta.tolist(),
            'curvature': self.curvature,
            'budget': self.budget,
            'domain_metrics': self.domain_metrics,
            'authority': self.authority,
            'chain_digest': self.chain_digest,
            'step_count': self.step_count,
            'hash': self.hash()
        }


def V_PL(x: np.ndarray) -> float:
    """
    PhaseLoom Potential: V_{PL}(x).
    Represents total cognitive tension. Bounded below, coercive.
    
    Note: This is now a special case of GMIPotential.base()
    Kept for backward compatibility.
    """
    return float(np.sum(x**2))


class Instruction:
    """Base Coh-IL Transition Operator."""
    def __init__(self, op_code: str, pi_func, sigma: float, kappa: float):
        self.op_code = op_code  # Generator choice (INFER, EXPLORE, etc.)
        self.pi = pi_func       # Untrusted heuristic proposal 
        self.sigma = sigma      # Metabolic work / Spend
        self.kappa = kappa      # Allowed defect / Positive-variation dominance
    
    def __repr__(self) -> str:
        return f"Instruction(op_code={self.op_code}, sigma={self.sigma}, kappa={self.kappa})"


class CompositeInstruction(Instruction):
    """Represents r2 ⊙ r1. Enforces Oplax operator algebra."""
    def __init__(self, r1: Instruction, r2: Instruction, claimed_sigma: float, claimed_kappa: float):
        super().__init__(
            op_code=f"({r2.op_code} ⊙ {r1.op_code})",
            pi_func=lambda x: r2.pi(r1.pi(x)),
            sigma=claimed_sigma,
            kappa=claimed_kappa
        )
        self.r1 = r1
        self.r2 = r2
    
    def __repr__(self) -> str:
        return f"CompositeInstruction({self.op_code}, sigma={self.sigma}, kappa={self.kappa})"


# Convenience function to create configured potential
def create_potential(
    lambda_curvature: float = 5.0,
    lambda_budget: float = 1.0,
    lambda_domain: float = 1.0,
    budget_scale: float = 10.0
) -> GMIPotential:
    """
    Factory function to create a configured GMIPotential.
    """
    return GMIPotential(
        lambda_curvature=lambda_curvature,
        lambda_budget=lambda_budget,
        lambda_domain=lambda_domain,
        budget_scale=budget_scale
    )
