"""
Affective Cognitive State for the GMI Universal Cognition Engine.

Module 16: Affective Mode Geometry and Cognitive Mode Switching

Extends the cognitive state to include:
- χ ∈ [0, 1]: Perceived safety-threat level
  - χ → 0: High safety, expansive regime
  - χ → 1: High threat, defensive compression
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import numpy as np

from gmos.agents.gmi.state import CognitiveState as BaseCognitiveState


@dataclass
class AffectiveCognitiveState:
    """
    Extended GMI state: z = (ρ, θ, C, E, W, B, Ω, χ)
    
    Components:
    - ρ (rho): Continuous cognitive density
    - θ (theta): Directional/phase field
    - C: Passive structural memory / curvature
    - E: Episodic archive reference
    - W: Active workspace with phantom states
    - B: Thermodynamic budget
    - Ω: Ledger anchor
    - χ (chi): Affective mode (0=safe/expansive, 1=threat/defensive)
    """
    # Core cognition (from BaseCognitiveState)
    rho: np.ndarray = None
    theta: np.ndarray = None
    
    # Memory layers
    curvature: float = 0.0
    episodic_references: list = field(default_factory=list)
    workspace_active: bool = False
    
    # Budget
    budget: float = 10.0
    
    # Domain adaptation
    domain_metrics: Dict[str, float] = field(default_factory=dict)
    authority: float = 1.0
    
    # Ledger anchoring
    chain_digest: str = ""
    step_count: int = 0
    
    # NEW: Affective mode
    chi: float = 0.5  # Default: neutral
    
    def __post_init__(self):
        """Ensure arrays and validate χ."""
        if self.rho is not None and not isinstance(self.rho, np.ndarray):
            self.rho = np.array(self.rho, dtype=float)
        if self.theta is not None and not isinstance(self.theta, np.ndarray):
            self.theta = np.array(self.theta, dtype=float)
        
        # Clamp χ to [0, 1]
        self.chi = float(np.clip(self.chi, 0.0, 1.0))
    
    @property
    def is_safe(self) -> bool:
        """Is the system in safe mode (χ < 0.3)?"""
        return self.chi < 0.3
    
    @property
    def is_threatened(self) -> bool:
        """Is the system in threat mode (χ > 0.7)?"""
        return self.chi > 0.7
    
    @property
    def is_flow(self) -> bool:
        """Is the system in flow state (optimal thermodynamic efficiency)?"""
        return 0.2 <= self.chi <= 0.4
    
    @property
    def affective_mode_name(self) -> str:
        """Get human-readable affective mode."""
        if self.chi < 0.2:
            return "deep_safety"
        elif self.chi < 0.4:
            return "flow"
        elif self.chi < 0.6:
            return "neutral"
        elif self.chi < 0.8:
            return "caution"
        else:
            return "defensive"
    
    def to_base(self) -> BaseCognitiveState:
        """Convert to base CognitiveState."""
        return BaseCognitiveState(
            rho=self.rho,
            theta=self.theta,
            curvature=self.curvature,
            budget=self.budget,
            domain_metrics=self.domain_metrics,
            authority=self.authority,
            chain_digest=self.chain_digest,
            step_count=self.step_count
        )
    
    @classmethod
    def from_base(cls, state: BaseCognitiveState, chi: float = 0.5) -> 'AffectiveCognitiveState':
        """Create from base CognitiveState."""
        return cls(
            rho=state.rho,
            theta=state.theta,
            curvature=state.curvature,
            episodic_references=state.episodic_references,
            workspace_active=state.workspace_active,
            budget=state.budget,
            domain_metrics=state.domain_metrics,
            authority=state.authority,
            chain_digest=state.chain_digest,
            step_count=state.step_count,
            chi=chi
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'rho': self.rho.tolist() if self.rho is not None else [],
            'theta': self.theta.tolist() if self.theta is not None else [],
            'curvature': self.curvature,
            'budget': self.budget,
            'domain_metrics': self.domain_metrics,
            'chi': self.chi,
            'affective_mode': self.affective_mode_name,
            'chain_digest': self.chain_digest,
            'step_count': self.step_count
        }


class AffectiveStateFactory:
    """Factory for creating affective states."""
    
    @staticmethod
    def create_safe(initial_rho, budget=10.0) -> AffectiveCognitiveState:
        """Create state in safe mode."""
        rho = np.array(initial_rho)
        theta = rho / (np.linalg.norm(rho) + 1e-8)
        return AffectiveCognitiveState(
            rho=rho, theta=theta, budget=budget, chi=0.1
        )
    
    @staticmethod
    def create_flow(initial_rho, budget=10.0) -> AffectiveCognitiveState:
        """Create state in flow mode."""
        rho = np.array(initial_rho)
        theta = rho / (np.linalg.norm(rho) + 1e-8)
        return AffectiveCognitiveState(
            rho=rho, theta=theta, budget=budget, chi=0.3
        )
    
    @staticmethod
    def create_defensive(initial_rho, budget=10.0) -> AffectiveCognitiveState:
        """Create state in defensive mode."""
        rho = np.array(initial_rho)
        theta = rho / (np.linalg.norm(rho) + 1e-8)
        return AffectiveCognitiveState(
            rho=rho, theta=theta, budget=budget, chi=0.9
        )


# Alias for backward compatibility
AffectiveState = AffectiveCognitiveState
