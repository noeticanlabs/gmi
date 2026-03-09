"""
Continuous Dynamics for GM-OS.

Implements Moreau-projected dynamical systems per GM-OS Canon Spec v1 §17:

    ξ̇(t) ∈ F(ξ(t)) − N_K(ξ(t))

Where:
- F(ξ): Free drift induced by hosted processes, memory relaxation, queue aging
- N_K(ξ): Normal cone to admissible set K for projection
- K: Admissible domain (bounded potential, reserve floors, safety constraints)

This module provides:
1. FreeDriftFunction: Computes unconstrained drift
2. NormalConeProjector: Projects to admissible set
3. ProjectedDynamicalSystem: Full continuous dynamics solver
4. AbsorbingBoundary: Handles budget boundary behavior per spec §18
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, Callable, List
import numpy as np
from enum import Enum
import time

# For type hints
from gmos.kernel.substrate_state import FullSubstrateState, GMOSState


class DriftType(Enum):
    """Types of free drift in the system."""
    PROCESS_EVOLUTION = "process"      # Hosted process dynamics
    MEMORY_RELAXATION = "memory"        # Memory decay/consolidation
    QUEUE_AGING = "queue"               # Event queue aging
    SENSORY_REFRESH = "sensory"         # Passive sensory updates
    THERMAL_NOISE = "noise"             # Thermal/budget noise


@dataclass
class DriftComponent:
    """
    A single component of the free drift F(ξ).
    
    Each component has:
    - drift_type: What kind of drift
    - magnitude: Scaling factor
    - direction: Vector field direction
    - weight: Contribution weight to total drift
    """
    drift_type: DriftType
    magnitude: float
    direction: np.ndarray
    weight: float = 1.0
    
    def compute(self, state: GMOSState, dt: float) -> np.ndarray:
        """
        Compute drift contribution.
        
        Args:
            state: Current substrate state
            dt: Time step
            
        Returns:
            Drift vector contribution
        """
        return self.magnitude * self.direction * self.weight * dt


@dataclass 
class AdmissibleSet:
    """
    The admissible domain K per Canon Spec §4.
    
    K = K_GMOS ∩ K_budget ∩ K_anchor ∩ K_kernel ∩ K_authority ∩ K_ledger
    
    Where each factor defines hard safety constraints.
    """
    # Potential threshold (per spec §4)
    potential_threshold: float = 1000.0
    
    # Reserve floors per channel
    reserve_floors: Dict[str, float] = field(default_factory=dict)
    
    # Maximum values per channel
    max_values: Dict[str, float] = field(default_factory=dict)
    
    # Budget channels that are protected
    protected_channels: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.reserve_floors:
            self.reserve_floors = {
                "sens": 10.0,
                "mem": 10.0, 
                "branch": 5.0,
                "plan": 5.0,
                "act": 5.0,
                "safety": 20.0,
                "kernel": 5.0,
            }
        if not self.max_values:
            self.max_values = {
                "sens": 200.0,
                "mem": 200.0,
                "branch": 100.0,
                "plan": 100.0,
                "act": 100.0,
                "safety": 50.0,
                "kernel": 50.0,
            }
        if not self.protected_channels:
            self.protected_channels = ["safety"]  # Safety reserve is protected
    
    def is_admissible(self, state: GMOSState) -> bool:
        """
        Check if state is in admissible domain K.
        
        Args:
            state: Substrate state to check
            
        Returns:
            True if state is admissible
        """
        # Check reserve floors
        for channel, reserve in self.reserve_floors.items():
            if state.b.get(channel, 0.0) < reserve - 1e-6:
                return False
        
        # Check max bounds
        for channel, max_val in self.max_values.items():
            if state.b.get(channel, 0.0) > max_val + 1e-6:
                return False
        
        return True
    
    def project_to_admissible(self, state: GMOSState) -> GMOSState:
        """
        Project state to admissible set K.
        
        Uses projection that moves state to nearest point in K
        while respecting all constraints.
        
        Args:
            state: State to project
            
        Returns:
            Projected state
        """
        # Create copy
        projected = state.copy()
        
        # Project budget channels
        for channel in set(projected.b.keys()) | set(self.reserve_floors.keys()):
            current = projected.b.get(channel, 0.0)
            reserve = self.reserve_floors.get(channel, 0.0)
            max_val = self.max_values.get(channel, float('inf'))
            
            # Clamp to [reserve, max]
            projected.b[channel] = np.clip(current, reserve, max_val)
        
        projected.invalidate_hash()
        return projected
    
    def normal_cone_vector(self, state: GMOSState) -> np.ndarray:
        """
        Compute normal cone direction N_K(ξ).
        
        The normal cone contains vectors that would violate admissibility.
        For projection, we need vectors pointing outward from K.
        
        Returns vector in the normal cone (pointing toward boundary).
        """
        n = np.zeros(7)  # 7 factors in state
        
        # Check each constraint
        for i, channel in enumerate(sorted(state.b.keys())):
            current = state.b.get(channel, 0.0)
            reserve = self.reserve_floors.get(channel, 0.0)
            
            # If at reserve floor, any negative direction is in normal cone
            if abs(current - reserve) < 1e-6:
                n[i] = -1.0  # Pointing toward decreasing budget
        
        # Normalize if non-zero
        norm = np.linalg.norm(n)
        if norm > 1e-6:
            n = n / norm
            
        return n


class FreeDriftFunction:
    """
    Computes free drift F(ξ) per spec §17.
    
    F combines:
    - Process evolution (from hosted processes)
    - Memory relaxation (decay of inactive memories)
    - Queue aging (event queue processing)
    - Sensory refresh (passive perception updates)
    """
    
    def __init__(
        self,
        process_drift_fn: Optional[Callable] = None,
        memory_relaxation_rate: float = 0.01,
        queue_aging_rate: float = 0.05,
        sensory_refresh_rate: float = 0.1,
    ):
        """
        Initialize drift function.
        
        Args:
            process_drift_fn: Custom function for process dynamics
            memory_relaxation_rate: Rate of memory decay
            queue_aging_rate: Rate of queue aging
            sensory_refresh_rate: Rate of sensory updates
        """
        self.process_drift_fn = process_drift_fn
        self.memory_relaxation_rate = memory_relaxation_rate
        self.queue_aging_rate = queue_aging_rate
        self.sensory_refresh_rate = sensory_refresh_rate
    
    def compute(
        self, 
        state: GMOSState, 
        dt: float,
        external_drift: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Compute free drift F(ξ) * dt.
        
        Args:
            state: Current substrate state
            dt: Time step
            external_drift: Additional drift from external sources
            
        Returns:
            Drift vector (7 components matching state factors)
        """
        # Initialize drift vector for 7 state factors
        # Order: x_ext, s, m, b, p, k, ℓ
        drift = np.zeros(7)
        
        # 1. Process evolution drift (factor 5: p)
        if self.process_drift_fn is not None:
            process_drift = self.process_drift_fn(state, dt)
            drift[4] = process_drift  # p factor
        
        # 2. Memory relaxation (factor 3: m)
        # Decay inactive memory content
        drift[2] = -self.memory_relaxation_rate * state.m_curvature * dt
        
        # 3. Queue aging (factor 6: k)
        # Events in queue age over time
        queue_length = len(state.k.event_queue)
        drift[5] = -self.queue_aging_rate * queue_length * dt
        
        # 4. Sensory refresh (factor 2: s)
        # Passive sensory state updates
        drift[1] = self.sensory_refresh_rate * dt
        
        # 5. External drift
        if external_drift is not None:
            drift += external_drift * dt
        
        return drift


class ProjectedDynamicalSystem:
    """
    Moreau-projected dynamical system per spec §17.
    
    Implements: ξ̇(t) ∈ F(ξ(t)) - N_K(ξ(t))
    
    This ensures:
    1. Free drift when inside admissible set
    2. Projection onto boundary when reaching constraints
    3. Forward invariance of K (Theorem 24.1)
    """
    
    def __init__(
        self,
        admissible_set: Optional[AdmissibleSet] = None,
        free_drift: Optional[FreeDriftFunction] = None,
        dt: float = 0.01,
        integrator: str = "euler",  # "euler" or "rk4"
    ):
        """
        Initialize projected dynamical system.
        
        Args:
            admissible_set: The admissible domain K
            free_drift: Free drift function F
            dt: Default time step
            integrator: Integration method
        """
        self.admissible = admissible_set or AdmissibleSet()
        self.free_drift = free_drift or FreeDriftFunction()
        self.dt = dt
        self.integrator = integrator
    
    def step(
        self,
        state: GMOSState,
        dt: Optional[float] = None,
        external_drift: Optional[np.ndarray] = None,
    ) -> GMOSState:
        """
        Advance state by one time step using projected dynamics.
        
        Implements:
            ξ_{t+dt} = Π_K(ξ_t + F(ξ_t) * dt)
        
        Where Π_K is projection onto admissible set K.
        
        Args:
            state: Current state
            dt: Time step (uses default if None)
            external_drift: Additional drift contributions
            
        Returns:
            New state after projection
        """
        dt = dt or self.dt
        
        # Compute free drift
        F = self.free_drift.compute(state, dt, external_drift)
        
        # Apply drift
        new_state = self._apply_drift(state, F, dt)
        
        # Project to admissible set
        new_state = self.admissible.project_to_admissible(new_state)
        
        return new_state
    
    def _apply_drift(
        self, 
        state: GMOSState, 
        drift: np.ndarray, 
        dt: float
    ) -> GMOSState:
        """
        Apply drift vector to state.
        
        Args:
            state: Current state
            drift: Drift vector (7 components)
            dt: Time step
            
        Returns:
            State after drift application
        """
        new_state = state.copy()
        
        # Factor 2: Sensory (s) - bounded sensory update
        new_state.s.timestamp += drift[1] * dt
        
        # Factor 3: Memory (m) - curvature decay
        new_state.m_curvature = max(0.0, new_state.m_curvature + drift[2] * dt)
        
        # Factor 4: Budget (b) - budget changes from drift
        # This is simplified; actual budget dynamics are in BudgetRouter
        for channel in new_state.b:
            # Natural budget decay
            decay = 0.001 * new_state.b[channel] * dt
            new_state.b[channel] = max(0.0, new_state.b[channel] - decay)
        
        # Factor 6: Kernel (k) - queue aging
        if len(new_state.k.event_queue) > 0:
            # Age events (simplified)
            aging = abs(drift[5])
            # Remove old events
            if aging > 0.1:
                new_state.k.event_queue = new_state.k.event_queue[-5:]
        
        new_state.invalidate_hash()
        return new_state
    
    def simulate(
        self,
        state: GMOSState,
        T: float,
        dt: Optional[float] = None,
        callback: Optional[Callable[[GMOSState, float], None]] = None,
    ) -> GMOSState:
        """
        Simulate forward for time T.
        
        Args:
            state: Initial state
            T: Total simulation time
            dt: Time step
            callback: Optional callback for each step
            
        Returns:
            Final state after simulation
        """
        dt = dt or self.dt
        n_steps = int(T / dt)
        
        current_state = state.copy()
        t = 0.0
        
        for step in range(n_steps):
            # Check admissibility
            if not self.admissible.is_admissible(current_state):
                # Project back to admissible
                current_state = self.admissible.project_to_admissible(current_state)
            
            # Step
            current_state = self.step(current_state, dt)
            t += dt
            
            # Callback
            if callback is not None:
                callback(current_state, t)
        
        return current_state
    
    def compute_differential_inclusion(
        self,
        state: GMOSState,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the differential inclusion: ξ̇ ∈ F(ξ) - N_K(ξ).
        
        Returns both the free drift and the normal cone correction.
        
        Args:
            state: Current state
            
        Returns:
            (free_drift, normal_cone) tuple
        """
        # Compute free drift
        free_drift = self.free_drift.compute(state, 1.0)  # Unit time
        
        # Compute normal cone
        normal_cone = self.admissible.normal_cone_vector(state)
        
        return free_drift, normal_cone


class AbsorbingBoundary:
    """
    Absorbing budget boundary per spec §18.
    
    When a protected budget channel reaches its reserve floor:
    - b_i = b_i,reserve
    
    The admissible tangent directions require non-negative outward safety velocity.
    Therefore, the only compatible motion is zero in that protected direction.
    
    This is the direct substrate analog of the absorbing boundary theorem.
    """
    
    def __init__(
        self,
        reserve_floors: Dict[str, float],
        protected_channels: Optional[List[str]] = None,
    ):
        """
        Initialize absorbing boundary.
        
        Args:
            reserve_floors: Reserve floor values per channel
            protected_channels: Channels with hard protection
        """
        self.reserve_floors = reserve_floors
        self.protected_channels = protected_channels or ["safety"]
    
    def is_at_boundary(self, state: GMOSState, channel: str) -> bool:
        """
        Check if a channel is at its reserve boundary.
        
        Args:
            state: Current state
            channel: Budget channel to check
            
        Returns:
            True if at boundary
        """
        reserve = self.reserve_floors.get(channel, 0.0)
        current = state.b.get(channel, 0.0)
        return abs(current - reserve) < 1e-6
    
    def get_boundary_channels(self, state: GMOSState) -> List[str]:
        """
        Get all channels at boundary.
        
        Args:
            state: Current state
            
        Returns:
            List of channel names at boundary
        """
        return [
            ch for ch in state.b.keys()
            if self.is_at_boundary(state, ch)
        ]
    
    def can_spend(
        self, 
        state: GMOSState, 
        channel: str, 
        amount: float
    ) -> Tuple[bool, str]:
        """
        Check if spend is allowed considering absorbing boundary.
        
        Args:
            state: Current state
            channel: Budget channel
            amount: Spend amount
            
        Returns:
            (allowed, reason) tuple
        """
        # Check if protected channel at boundary
        if channel in self.protected_channels:
            if self.is_at_boundary(state, channel):
                return False, f"Protected channel '{channel}' at absorbing boundary"
        
        # Normal check
        reserve = self.reserve_floors.get(channel, 0.0)
        current = state.b.get(channel, 0.0)
        
        if current - amount < reserve - 1e-6:
            return False, f"Insufficient budget (would violate reserve)"
        
        return True, "allowed"
    
    def apply_spend_with_boundary(
        self,
        state: GMOSState,
        channel: str,
        amount: float,
    ) -> Tuple[GMOSState, bool, str]:
        """
        Apply spend with absorbing boundary enforcement.
        
        Args:
            state: Current state
            channel: Budget channel
            amount: Spend amount
            
        Returns:
            (new_state, success, message)
        """
        allowed, reason = self.can_spend(state, channel, amount)
        
        if not allowed:
            return state, False, reason
        
        # Apply spend
        new_state = state.copy()
        new_state.b[channel] = new_state.b.get(channel, 0.0) - amount
        new_state.invalidate_hash()
        
        return new_state, True, "spend executed"


# === Factory Functions ===

def create_projected_dynamics(
    dt: float = 0.01,
    potential_threshold: float = 1000.0,
) -> ProjectedDynamicalSystem:
    """
    Create projected dynamical system with default parameters.
    
    Args:
        dt: Default time step
        potential_threshold: Admissible potential threshold
        
    Returns:
        Configured ProjectedDynamicalSystem
    """
    admissible = AdmissibleSet(potential_threshold=potential_threshold)
    free_drift = FreeDriftFunction()
    
    return ProjectedDynamicalSystem(
        admissible=admissible,
        free_drift=free_drift,
        dt=dt,
    )


def create_absorbing_boundary(
    reserve_floors: Optional[Dict[str, float]] = None,
) -> AbsorbingBoundary:
    """
    Create absorbing boundary with default or custom reserves.
    
    Args:
        reserve_floors: Custom reserve floors
        
    Returns:
        Configured AbsorbingBoundary
    """
    reserves = reserve_floors or {
        "sens": 10.0,
        "mem": 10.0,
        "branch": 5.0,
        "plan": 5.0,
        "act": 5.0,
        "safety": 20.0,
        "kernel": 5.0,
    }
    
    return AbsorbingBoundary(
        reserve_floors=reserves,
        protected_channels=["safety"],
    )
