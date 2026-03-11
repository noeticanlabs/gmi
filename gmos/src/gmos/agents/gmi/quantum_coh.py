"""
Quantum-Coh Bridge - Volume V Implementation.

This module provides the quantum-classical bridge:
- Hidden density-state dynamics
- Born rule measurement
- Lindblad evolution
- Thermodynamic ledger bounds

Key concepts:
- The hidden Hilbert space H is not directly observable
- Measurement projects to classical boundary via Born rule
- Continuous evolution via Lindblad master equation
- Thermodynamic cost of quantum-to-classical transition
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List
import numpy as np


# ============================================================================
# Pauli Matrices (for qubit representation)
# ============================================================================

# Identity
I = np.array([[1, 0], [0, 1]], dtype=complex)

# Pauli X (bit flip)
sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)

# Pauli Y (phase flip)
sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)

# Pauli Z (phase)
sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)

PAULIS = [I, sigma_x, sigma_y, sigma_z]
PAULI_NAMES = ['I', 'X', 'Y', 'Z']


# ============================================================================
# Quantum-Coh State
# ============================================================================

@dataclass
class QuantumCohState:
    """
    Quantum-Coh state for a qubit.
    
    Represents a two-level quantum system (qubit) with:
    - Density matrix in Bloch representation: rho = (I + x·sigma) / 2
    - Boundary classical projection
    - Lindblad evolution parameters
    - Thermodynamic cost tracking
    """
    # Hilbert space dimension (default 2 for qubit)
    hilbert_dim: int = 2
    
    # Bloch vector: rho = (I + x·sigma)/2
    # [x, y, z] where x^2 + y^2 + z^2 <= 1
    bloch_vector: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 1.0]))
    
    # Boundary projection (classical state)
    boundary_state: float = 1.0  # +1 or -1 in Z basis
    boundary_basis: str = "z"  # measurement basis
    
    # Lindblad evolution parameters
    decoherence_rate: float = 0.1  # Gamma
    dissipation_type: str = "amplitude_damping"  # or "phase_damping", "depolarizing"
    
    # Thermodynamic tracking
    entropy_production: float = 0.0  # W: accumulated entropy
    projection_defect: float = 0.0  # kappa: lost coherence
    last_entropy: float = 0.0  # S(rho)
    
    # Measurement info
    last_measurement_basis: str = "z"
    last_measurement_outcome: Optional[int] = None  # 0 or 1
    last_measurement_time: int = 0
    
    def __post_init__(self):
        """Validate and normalize state."""
        self._validate_bloch()
        self._update_density_info()
    
    def _validate_bloch(self):
        """Ensure bloch vector is valid (|x| <= 1)."""
        norm = np.linalg.norm(self.bloch_vector)
        if norm > 1.0:
            self.bloch_vector = self.bloch_vector / norm
    
    def _update_density_info(self):
        """Update entropy and purity from bloch vector."""
        # Purity: Tr(rho^2) = (1 + |r|^2) / 2
        r = np.linalg.norm(self.bloch_vector)
        self.last_entropy = self._von_neumann_entropy(r)
    
    def _von_neumann_entropy(self, r: float) -> float:
        """
        Compute von Neumann entropy S(rho) = -Tr(rho log rho).
        
        For qubit: S = -((1+r)/2) log((1+r)/2) - ((1-r)/2) log((1-r)/2)
        """
        if r >= 1.0 - 1e-10:
            return 0.0  # Pure state
        if r <= 1e-10:
            return 1.0  # Maximally mixed
        
        # Convert to density eigenvalues
        lambda_plus = (1 + r) / 2
        lambda_minus = (1 - r) / 2
        
        # S = -sum lambda log lambda
        if lambda_plus > 1e-10:
            s_plus = -lambda_plus * np.log2(lambda_plus)
        else:
            s_plus = 0.0
        
        if lambda_minus > 1e-10:
            s_minus = -lambda_minus * np.log2(lambda_minus)
        else:
            s_minus = 0.0
        
        return s_plus + s_minus
    
    def get_density_matrix(self) -> np.ndarray:
        """
        Get full density matrix from Bloch vector.
        
        rho = (I + x·sigma) / 2
        """
        x, y, z = self.bloch_vector
        rho = (I + x * sigma_x + y * sigma_y + z * sigma_z) / 2
        return rho
    
    def probability_outcome(self, basis: str = "z", outcome: int = 0) -> float:
        """
        Compute Born rule probability: p(outcome) = Tr(|outcome><outcome| rho)
        
        For Z basis: p(0) = (1+z)/2, p(1) = (1-z)/2
        For X basis: p(0) = (1+x)/2, p(1) = (1-x)/2
        For Y basis: p(0) = (1+y)/2, p(1) = (1-y)/2
        """
        if basis == "z":
            r = self.bloch_vector[2]
        elif basis == "x":
            r = self.bloch_vector[0]
        elif basis == "y":
            r = self.bloch_vector[1]
        else:
            raise ValueError(f"Unknown basis: {basis}")
        
        if outcome == 0:
            return (1 + r) / 2
        else:
            return (1 - r) / 2
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'hilbert_dim': self.hilbert_dim,
            'bloch_vector': self.bloch_vector.tolist(),
            'boundary_state': self.boundary_state,
            'boundary_basis': self.boundary_basis,
            'decoherence_rate': self.decoherence_rate,
            'entropy_production': self.entropy_production,
            'projection_defect': self.projection_defect,
            'last_measurement_outcome': self.last_measurement_outcome,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QuantumCohState':
        """Deserialize from dictionary."""
        return cls(
            hilbert_dim=data.get('hilbert_dim', 2),
            bloch_vector=np.array(data.get('bloch_vector', [0, 0, 1])),
            boundary_state=data.get('boundary_state', 1.0),
            boundary_basis=data.get('boundary_basis', 'z'),
            decoherence_rate=data.get('decoherence_rate', 0.1),
            entropy_production=data.get('entropy_production', 0.0),
            projection_defect=data.get('projection_defect', 0.0),
            last_measurement_outcome=data.get('last_measurement_outcome'),
        )


# ============================================================================
# Lindblad Evolution
# ============================================================================

def lindblad_step(
    state: QuantumCohState,
    dt: float,
    hamiltonian: np.ndarray = None,
) -> QuantumCohState:
    """
    Apply Lindblad master equation step for qubit.
    
    d rho/dt = -i[H, rho] + D[rho]
    
    For amplitude damping (T1 process):
    D[rho] = gamma * (sigma_- rho sigma_+ - 0.5 {sigma_+ sigma_-, rho})
    
    Args:
        state: Current quantum state
        dt: Time step
        hamiltonian: System Hamiltonian (default: zero)
        
    Returns:
        Updated quantum state
    """
    if hamiltonian is None:
        hamiltonian = np.zeros((2, 2), dtype=complex)
    
    gamma = state.decoherence_rate
    x, y, z = state.bloch_vector
    
    # Compute bloch vector update based on dissipation type
    if state.dissipation_type == "amplitude_damping":
        # T1 process: relaxation toward |0><0| (z -> -1)
        dx = -gamma * x * dt / 2
        dy = -gamma * y * dt / 2
        dz = -gamma * (z + 1) * dt / 2
        
    elif state.dissipation_type == "phase_damping":
        # T2 process: dephasing (x, y -> 0, z unchanged)
        dx = -gamma * x * dt / 2
        dy = -gamma * y * dt / 2
        dz = 0
        
    elif state.dissipation_type == "depolarizing":
        # All directions decay toward maximally mixed
        dx = -gamma * x * dt / 2
        dy = -gamma * y * dt / 2
        dz = -gamma * z * dt / 2
        
    else:
        raise ValueError(f"Unknown dissipation type: {state.dissipation_type}")
    
    # Update bloch vector
    new_bloch = np.array([x + dx, y + dy, z + dz])
    
    # Normalize if needed
    norm = np.linalg.norm(new_bloch)
    if norm > 1.0:
        new_bloch = new_bloch / norm
    
    # Compute entropy production
    old_entropy = state.last_entropy
    new_state = QuantumCohState(
        hilbert_dim=state.hilbert_dim,
        bloch_vector=new_bloch,
        boundary_state=state.boundary_state,
        boundary_basis=state.boundary_basis,
        decoherence_rate=state.decoherence_rate,
        dissipation_type=state.dissipation_type,
        entropy_production=state.entropy_production,
        projection_defect=state.projection_defect,
        last_entropy=state.last_entropy,
    )
    new_entropy = new_state.last_entropy
    
    # Entropy production: increase in von Neumann entropy
    entropy_delta = max(0, new_entropy - old_entropy)
    new_state.entropy_production += entropy_delta
    
    return new_state


# ============================================================================
# Born Rule Measurement
# ============================================================================

def measure_born(
    state: QuantumCohState,
    basis: str = "z",
    time_step: int = 0,
) -> Tuple[QuantumCohState, int, float]:
    """
    Apply Born rule measurement.
    
    p(outcome) = Tr(|outcome><outcome| rho)
    
    Args:
        state: Quantum state to measure
        basis: Measurement basis ("x", "y", or "z")
        time_step: Current time step for tracking
        
    Returns:
        Tuple of (post-measurement state, outcome, probability)
    """
    # Compute probabilities
    p0 = state.probability_outcome(basis, 0)
    p1 = state.probability_outcome(basis, 1)
    
    # Sample from distribution
    r = np.random.random()
    if r < p0:
        outcome = 0
        probability = p0
    else:
        outcome = 1
        probability = p1
    
    # Post-measurement state
    if basis == "z":
        new_bloch = np.array([0.0, 0.0, 1.0 - 2*outcome])
    elif basis == "x":
        new_bloch = np.array([1.0 - 2*outcome, 0.0, 0.0])
    elif basis == "y":
        new_bloch = np.array([0.0, 1.0 - 2*outcome, 0.0])
    else:
        raise ValueError(f"Unknown basis: {basis}")
    
    # Compute projection defect
    old_entropy = state.last_entropy
    new_state = QuantumCohState(
        hilbert_dim=state.hilbert_dim,
        bloch_vector=new_bloch,
        boundary_state=1.0 if outcome == 0 else -1.0,
        boundary_basis=basis,
        decoherence_rate=state.decoherence_rate,
        dissipation_type=state.dissipation_type,
        entropy_production=state.entropy_production,
        last_measurement_basis=basis,
        last_measurement_outcome=outcome,
        last_measurement_time=time_step,
    )
    new_entropy = new_state.last_entropy
    
    # Projection defect: loss of entropy due to projection
    new_state.projection_defect = max(0, old_entropy - new_entropy)
    
    return new_state, outcome, probability


def compute_born_probabilities(state: QuantumCohState, basis: str = "z") -> Tuple[float, float]:
    """
    Compute Born rule probabilities without measurement.
    
    Returns:
        Tuple of (p(0), p(1))
    """
    p0 = state.probability_outcome(basis, 0)
    p1 = state.probability_outcome(basis, 1)
    return p0, p1


# ============================================================================
# Quantum Potential (Thermodynamic Cost)
# ============================================================================

@dataclass
class QuantumWeights:
    """Weights for quantum potential terms."""
    w_entropy: float = 0.5
    w_defect: float = 0.5
    w_coherence: float = 0.2


def compute_quantum_potential(
    state: QuantumCohState,
    weights: QuantumWeights = None,
) -> float:
    """
    Compute quantum thermodynamic potential.
    
    V_quantum = w_entropy * W + w_defect * kappa + w_coherence * (1 - purity)
    """
    if weights is None:
        weights = QuantumWeights()
    
    V = weights.w_entropy * state.entropy_production
    V += weights.w_defect * state.projection_defect
    
    r = np.linalg.norm(state.bloch_vector)
    purity = (1 + r) / 2
    coherence_cost = weights.w_coherence * (1 - purity)
    V += coherence_cost
    
    return V


# ============================================================================
# No-Signaling (Future Extension)
# ============================================================================

def verify_nosignaling(
    marginal_a: np.ndarray,
    marginal_b_given_a0: np.ndarray,
    marginal_b_given_a1: np.ndarray,
    tolerance: float = 1e-6,
) -> bool:
    """Verify no-signaling condition."""
    return np.allclose(marginal_b_given_a0, marginal_b_given_a1, atol=tolerance)


def compute_trace_defect(
    joint_entropy: float,
    mutual_information: float,
    subsystem_entropy: float,
) -> float:
    """Compute trace defect: thermodynamic cost of severing entanglement."""
    return max(0, mutual_information - subsystem_entropy)


# ============================================================================
# Utility Functions
# ============================================================================

def create_initial_pure_state(polarization: str = "up") -> QuantumCohState:
    """Create initial pure qubit state."""
    if polarization == "up":
        bloch = np.array([0.0, 0.0, 1.0])
    elif polarization == "down":
        bloch = np.array([0.0, 0.0, -1.0])
    elif polarization == "right":
        bloch = np.array([1.0, 0.0, 0.0])
    elif polarization == "left":
        bloch = np.array([-1.0, 0.0, 0.0])
    elif polarization == "forward":
        bloch = np.array([0.0, 1.0, 0.0])
    elif polarization == "backward":
        bloch = np.array([0.0, -1.0, 0.0])
    else:
        raise ValueError(f"Unknown polarization: {polarization}")
    return QuantumCohState(bloch_vector=bloch)


def create_maximally_mixed_state() -> QuantumCohState:
    """Create maximally mixed state (rho = I/2)."""
    return QuantumCohState(bloch_vector=np.array([0.0, 0.0, 0.0]))


def fidelity(p: QuantumCohState, q: QuantumCohState) -> float:
    """Compute quantum fidelity for qubits."""
    r_p = p.bloch_vector
    r_q = q.bloch_vector
    dot = np.dot(r_p, r_q)
    return (1 + dot) / 2


def bloch_distance(p: QuantumCohState, q: QuantumCohState) -> float:
    """Compute Bloch vector distance."""
    return np.linalg.norm(p.bloch_vector - q.bloch_vector)
