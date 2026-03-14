"""
12-Block State Decomposition for GMI Resonant Field Framework.

Implements the 12-block orthogonal state decomposition per the mathematical specification:

    z = (ξ_pos, ξ_mem, ξ_sens, ξ_affect, ξ_action, ξ_coh, 
         ξ_Φ, ξ_task, ξ_shell, ξ_policy, ξ_aux, b)

Where:
- ξ_pos: Position/topology (embodied state)
- ξ_mem: Memory curvature / trauma archive
- ξ_sens: Subjective sensory manifold
- ξ_affect: Tension / pressure / affective loading
- ξ_action: Motor or control intent
- ξ_coh: Coherence / purity block
- ξ_Φ: 88-octave resonant substrate field
- ξ_task: Goal/task alignment
- ξ_shell: Epistemic/character shell
- ξ_policy: Continuous policy weights
- ξ_aux: Domain-specific reserve block
- b: Budget coordinate

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import hashlib
import json

# Visibility discipline enums
class VisibilityLevel:
    """Visibility levels per hidden-fiber doctrine."""
    HIDDEN = "hidden"      # Hidden fiber - not visible externally
    MIXED = "mixed"        # Mixed - boundary projections visible
    BOUNDARY = "boundary"  # Boundary-visible (budget, receipts)


@dataclass
class TwelveBlockState:
    """
    12-block orthogonal state decomposition.
    
    z = (ξ_pos, ξ_mem, ξ_sens, ξ_affect, ξ_action, ξ_coh, 
         ξ_Φ, ξ_task, ξ_shell, ξ_policy, ξ_aux, b)
    
    This is the native state type for the resonant field + ears + voice framework.
    """
    
    # Block 1: Position/topology (embodied)
    # Physical or abstract position in environment
    xi_pos: np.ndarray = field(default_factory=lambda: np.zeros(3))
    
    # Block 2: Memory curvature / trauma archive
    # Memory state with curvature representing traumatic/deep memories
    xi_mem: np.ndarray = field(default_factory=lambda: np.zeros(16))
    
    # Block 3: Subjective sensory manifold
    # Processed sensory information
    xi_sens: np.ndarray = field(default_factory=lambda: np.zeros(32))
    
    # Block 4: Tension / pressure / affective loading
    # Affective state: urgency, pressure, threat, conflict mass
    xi_affect: np.ndarray = field(default_factory=lambda: np.zeros(8))
    
    # Block 5: Motor or control intent
    # Action intentions, motor commands
    xi_action: np.ndarray = field(default_factory=lambda: np.zeros(16))
    
    # Block 6: Coherence / purity block
    # Quantum-like coherence state
    xi_coh: np.ndarray = field(default_factory=lambda: np.zeros(3))
    
    # Block 7: 88-octave resonant substrate field
    # The resonant field - spectral energy across 88 octaves
    xi_Phi: np.ndarray = field(default_factory=lambda: np.zeros(88))
    
    # Block 8: Goal/task alignment
    # Task representation and goal state
    xi_task: np.ndarray = field(default_factory=lambda: np.zeros(16))
    
    # Block 9: Epistemic/character shell
    # Character and epistemic state
    xi_shell: np.ndarray = field(default_factory=lambda: np.zeros(16))
    
    # Block 10: Continuous policy weights
    # Policy parameters and weights
    xi_policy: np.ndarray = field(default_factory=lambda: np.zeros(16))
    
    # Block 11: Domain-specific reserve block
    # Auxiliary/domain-specific state
    xi_aux: np.ndarray = field(default_factory=lambda: np.zeros(8))
    
    # Block 12: Budget coordinate
    # Thermodynamic budget b >= 0
    b: float = 10.0
    
    # Visibility annotations (for hidden-fiber discipline)
    _visibility: Dict[str, VisibilityLevel] = field(default_factory=lambda: {
        'xi_pos': VisibilityLevel.MIXED,
        'xi_mem': VisibilityLevel.HIDDEN,
        'xi_sens': VisibilityLevel.MIXED,
        'xi_affect': VisibilityLevel.HIDDEN,
        'xi_action': VisibilityLevel.MIXED,
        'xi_coh': VisibilityLevel.HIDDEN,
        'xi_Phi': VisibilityLevel.MIXED,
        'xi_task': VisibilityLevel.MIXED,
        'xi_shell': VisibilityLevel.MIXED,
        'xi_policy': VisibilityLevel.HIDDEN,
        'xi_aux': VisibilityLevel.MIXED,
        'b': VisibilityLevel.BOUNDARY,
    })
    
    def __post_init__(self):
        """Ensure arrays are numpy arrays."""
        # Convert all blocks to numpy arrays
        for attr_name in ['xi_pos', 'xi_mem', 'xi_sens', 'xi_affect', 
                         'xi_action', 'xi_coh', 'xi_Phi', 'xi_task', 
                         'xi_shell', 'xi_policy', 'xi_aux']:
            value = getattr(self, attr_name)
            if not isinstance(value, np.ndarray):
                setattr(self, attr_name, np.array(value, dtype=float))
        
        # Ensure budget is non-negative
        self.b = max(0.0, float(self.b))
    
    # =========================================================================
    # Properties for each block's Hilbert space
    # =========================================================================
    
    @property
    def H_pos(self) -> int:
        """Dimension of position space."""
        return len(self.xi_pos)
    
    @property
    def H_mem(self) -> int:
        """Dimension of memory space."""
        return len(self.xi_mem)
    
    @property
    def H_sens(self) -> int:
        """Dimension of sensory space."""
        return len(self.xi_sens)
    
    @property
    def H_affect(self) -> int:
        """Dimension of affect space."""
        return len(self.xi_affect)
    
    @property
    def H_action(self) -> int:
        """Dimension of action space."""
        return len(self.xi_action)
    
    @property
    def H_coh(self) -> int:
        """Dimension of coherence space."""
        return len(self.xi_coh)
    
    @property
    def H_Phi(self) -> int:
        """Dimension of resonant field (should be 88)."""
        return len(self.xi_Phi)
    
    @property
    def H_task(self) -> int:
        """Dimension of task space."""
        return len(self.xi_task)
    
    @property
    def H_shell(self) -> int:
        """Dimension of shell space."""
        return len(self.xi_shell)
    
    @property
    def H_policy(self) -> int:
        """Dimension of policy space."""
        return len(self.xi_policy)
    
    @property
    def H_aux(self) -> int:
        """Dimension of auxiliary space."""
        return len(self.xi_aux)
    
    # =========================================================================
    # Field energy computations
    # =========================================================================
    
    def compute_field_energy(self) -> float:
        """
        Compute field energy: E_field = 0.5 * |ξ_Φ|²
        """
        return 0.5 * np.sum(self.xi_Phi ** 2)
    
    def compute_weighted_field_energy(self, K: np.ndarray) -> float:
        """
        Compute weighted field energy: E_field^K = 0.5 * |K * ξ_Φ|²
        Used for octave-weighted dissipation.
        """
        if K.shape != (len(self.xi_Phi), len(self.xi_Phi)):
            raise ValueError(f"K must be {len(self.xi_Phi)}x{len(self.xi_Phi)} diagonal matrix")
        weighted = K @ self.xi_Phi
        return 0.5 * np.sum(weighted ** 2)
    
    # =========================================================================
    # State vector operations
    # =========================================================================
    
    def to_vector(self) -> np.ndarray:
        """
        Flatten entire state to 1D vector.
        """
        parts = [
            self.xi_pos,
            self.xi_mem,
            self.xi_sens,
            self.xi_affect,
            self.xi_action,
            self.xi_coh,
            self.xi_Phi,
            self.xi_task,
            self.xi_shell,
            self.xi_policy,
            self.xi_aux,
            np.array([self.b])
        ]
        return np.concatenate(parts)
    
    @classmethod
    def from_vector(cls, vec: np.ndarray) -> 'TwelveBlockState':
        """
        Reconstruct state from flat vector.
        
        Assumes standard dimensions:
        - pos: 3, mem: 16, sens: 32, affect: 8
        - action: 16, coh: 3, Phi: 88
        - task: 16, shell: 16, policy: 16, aux: 8, b: 1
        Total: 3+16+32+8+16+3+88+16+16+16+8+1 = 223
        """
        # Define cumulative indices
        dims = [3, 16, 32, 8, 16, 3, 88, 16, 16, 16, 8, 1]
        cumsum = np.cumsum([0] + dims)
        
        return cls(
            xi_pos=vec[cumsum[0]:cumsum[1]],
            xi_mem=vec[cumsum[1]:cumsum[2]],
            xi_sens=vec[cumsum[2]:cumsum[3]],
            xi_affect=vec[cumsum[3]:cumsum[4]],
            xi_action=vec[cumsum[4]:cumsum[5]],
            xi_coh=vec[cumsum[5]:cumsum[6]],
            xi_Phi=vec[cumsum[6]:cumsum[7]],
            xi_task=vec[cumsum[7]:cumsum[8]],
            xi_shell=vec[cumsum[8]:cumsum[9]],
            xi_policy=vec[cumsum[9]:cumsum[10]],
            xi_aux=vec[cumsum[10]:cumsum[11]],
            b=float(vec[cumsum[11]:cumsum[12]][0])
        )
    
    def copy(self) -> 'TwelveBlockState':
        """Create a deep copy of the state."""
        return TwelveBlockState(
            xi_pos=self.xi_pos.copy(),
            xi_mem=self.xi_mem.copy(),
            xi_sens=self.xi_sens.copy(),
            xi_affect=self.xi_affect.copy(),
            xi_action=self.xi_action.copy(),
            xi_coh=self.xi_coh.copy(),
            xi_Phi=self.xi_Phi.copy(),
            xi_task=self.xi_task.copy(),
            xi_shell=self.xi_shell.copy(),
            xi_policy=self.xi_policy.copy(),
            xi_aux=self.xi_aux.copy(),
            b=self.b
        )
    
    # =========================================================================
    # Hash and ledger operations
    # =========================================================================
    
    def hash(self) -> str:
        """
        Deterministic hash for ledger chain integrity.
        
        Per hidden-fiber doctrine: uses boundary-visible projections,
        not full internal state.
        """
        state_dict = {
            "xi_pos": self.xi_pos.round(6).tolist(),
            "xi_Phi": self.xi_Phi.round(6).tolist(),
            "xi_sens": self.xi_sens.round(6).tolist(),
            "xi_task": self.xi_task.round(6).tolist(),
            "b": round(self.b, 6),
        }
        state_str = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'xi_pos': self.xi_pos.tolist(),
            'xi_mem': self.xi_mem.tolist(),
            'xi_sens': self.xi_sens.tolist(),
            'xi_affect': self.xi_affect.tolist(),
            'xi_action': self.xi_action.tolist(),
            'xi_coh': self.xi_coh.tolist(),
            'xi_Phi': self.xi_Phi.tolist(),
            'xi_task': self.xi_task.tolist(),
            'xi_shell': self.xi_shell.tolist(),
            'xi_policy': self.xi_policy.tolist(),
            'xi_aux': self.xi_aux.tolist(),
            'b': self.b,
            'hash': self.hash()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TwelveBlockState':
        """Create state from dictionary."""
        return cls(
            xi_pos=np.array(data.get('xi_pos', [0, 0, 0])),
            xi_mem=np.array(data.get('xi_mem', [0] * 16)),
            xi_sens=np.array(data.get('xi_sens', [0] * 32)),
            xi_affect=np.array(data.get('xi_affect', [0] * 8)),
            xi_action=np.array(data.get('xi_action', [0] * 16)),
            xi_coh=np.array(data.get('xi_coh', [0, 0, 1])),
            xi_Phi=np.array(data.get('xi_Phi', [0] * 88)),
            xi_task=np.array(data.get('xi_task', [0] * 16)),
            xi_shell=np.array(data.get('xi_shell', [0] * 16)),
            xi_policy=np.array(data.get('xi_policy', [0] * 16)),
            xi_aux=np.array(data.get('xi_aux', [0] * 8)),
            b=data.get('b', 10.0)
        )
    
    # =========================================================================
    # Visibility discipline
    # =========================================================================
    
    def get_boundary_visible(self) -> Dict[str, Any]:
        """
        Get boundary-visible projections only.
        
        Per hidden-fiber doctrine: verifiers operate on boundary
        hashes and receipt bytes, never full internal state.
        """
        return {
            'hash': self.hash(),
            'b': self.b,
            'field_energy': self.compute_field_energy(),
            'sensory_magnitude': float(np.linalg.norm(self.xi_sens)),
            'task_alignment': float(np.linalg.norm(self.xi_task)),
        }
    
    def is_visible(self, block_name: str) -> VisibilityLevel:
        """Get visibility level for a block."""
        return self._visibility.get(block_name, VisibilityLevel.HIDDEN)


# =============================================================================
# Factory functions
# =============================================================================

def create_initial_state(
    budget: float = 10.0,
    seed: Optional[int] = None
) -> TwelveBlockState:
    """
    Create an initial 12-block state.
    
    Args:
        budget: Initial budget
        seed: Random seed for reproducibility
        
    Returns:
        Initialized TwelveBlockState
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Coherence starts at |0> state (0, 0, 1) in Bloch sphere
    return TwelveBlockState(
        xi_pos=np.zeros(3),
        xi_mem=np.zeros(16),
        xi_sens=np.zeros(32),
        xi_affect=np.zeros(8),
        xi_action=np.zeros(16),
        xi_coh=np.array([0.0, 0.0, 1.0]),  # |0⟩ state
        xi_Phi=np.zeros(88),  # No initial field excitation
        xi_task=np.zeros(16),
        xi_shell=np.zeros(16),
        xi_policy=np.zeros(16),
        xi_aux=np.zeros(8),
        b=budget
    )


def create_random_state(
    budget_range: tuple = (5.0, 20.0),
    field_excitation: float = 0.1,
    seed: Optional[int] = None
) -> TwelveBlockState:
    """
    Create a random 12-block state.
    
    Args:
        budget_range: (min, max) for budget
        field_excitation: Scale for field energy
        seed: Random seed
        
    Returns:
        Randomized TwelveBlockState
    """
    if seed is not None:
        np.random.seed(seed)
    
    return TwelveBlockState(
        xi_pos=np.random.randn(3),
        xi_mem=np.random.randn(16) * 0.1,
        xi_sens=np.random.randn(32) * 0.1,
        xi_affect=np.random.randn(8) * 0.1,
        xi_action=np.random.randn(16) * 0.1,
        xi_coh=np.array([0.0, 0.0, 1.0]),  # Start coherent
        xi_Phi=np.random.randn(88) * field_excitation,
        xi_task=np.random.randn(16) * 0.1,
        xi_shell=np.random.randn(16) * 0.1,
        xi_policy=np.random.randn(16) * 0.1,
        xi_aux=np.random.randn(8) * 0.1,
        b=np.random.uniform(*budget_range)
    )


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    # Test basic functionality
    print("Testing 12-block state decomposition...")
    
    # Create initial state
    state = create_initial_state(budget=10.0)
    print(f"Initial state budget: {state.b}")
    print(f"Field energy: {state.compute_field_energy()}")
    
    # Create random state
    state2 = create_random_state(seed=42)
    print(f"Random state budget: {state2.b}")
    print(f"Random field energy: {state2.compute_field_energy()}")
    
    # Test vector conversion
    vec = state.to_vector()
    print(f"State vector length: {len(vec)}")
    
    # Test reconstruction
    state3 = TwelveBlockState.from_vector(vec)
    assert np.allclose(state3.xi_Phi, state.xi_Phi)
    print("Vector conversion: OK")
    
    # Test hash
    h1 = state.hash()
    h2 = state2.hash()
    print(f"Hash 1: {h1[:16]}...")
    print(f"Hash 2: {h2[:16]}...")
    
    # Test boundary visibility
    bv = state.get_boundary_visible()
    print(f"Boundary visible: {list(bv.keys())}")
    
    print("\nAll tests passed!")
