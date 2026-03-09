"""
Full Substrate State for GM-OS.

Implements the unified state type ξ per GM-OS Canon Spec v1 §3.1:

    ξ = (x_ext, s, m, b, p, k, ℓ) ∈ Ξ

Where:
- x_ext: External world interface state
- s: Sensory manifold (S_ext ⊕ S_sem ⊕ S_int)
- m: Memory manifold (M_C ⊕ M_E ⊕ M_W)
- b: Budget bundle (B = [0,B_1^max] × ... × [0,B_N^max])
- p: Hosted process product state (P = ∏ P_i)
- k: Kernel control state (K_ctl)
- ℓ: Ledger state

This unifies all components into a single state type for kernel operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import hashlib
import json
import time

# Import existing component types
from gmos.sensory.manifold import (
    SensoryManifold,
    ExternalChart,
    SemanticChart,
    InternalChart,
)
from gmos.memory.workspace import WorkspaceState
from gmos.memory.archive import ArchiveState
from gmos.kernel.state_host import StateHost, HostedState, ProcessStateFlag
from gmos.kernel.scheduler import KernelScheduler
from gmos.kernel.budget_router import BudgetRouter, BudgetSlice
from gmos.kernel.hash_chain import ChainDigest


class OperationalMode(Enum):
    """
    GM-OS operational modes per Canon Spec §22.
    
    Mode affects:
    - admissible event classes
    - branch limits
    - defect tolerances
    - action permissions
    - reserve floors
    - required authority thresholds
    """
    OBSERVE = "observe"      # No external action commits
    REPAIR = "repair"        # Memory reconciliation prioritized
    PLAN = "plan"            # Branching allowed under capped budget
    ACT = "act"              # External commits allowed with valid handles
    SAFE_HOLD = "safe_hold"  # Only safety-preserving maintenance events
    AUDIT = "audit"          # Read-only plus ledger verification


@dataclass
class ExternalInterfaceState:
    """
    External world interface state (x_ext).
    
    Represents the boundary between GM-OS and the external world.
    Hosted processes cannot directly mutate this - only through
    action commitment (Γ_act).
    """
    # World state snapshot
    world_state: Dict[str, Any] = field(default_factory=dict)
    
    # Pending action requests (not yet committed)
    pending_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Last committed action
    last_action: Optional[Dict[str, Any]] = None
    
    # External observation buffer
    observations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    last_update: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "world_state": self.world_state,
            "pending_actions_count": len(self.pending_actions),
            "has_last_action": self.last_action is not None,
            "observation_count": len(self.observations),
            "last_update": self.last_update,
        }


@dataclass
class HostedProcessState:
    """
    Hosted process product state (p).
    
    p = (P_1, ..., P_M) where each P_i is a process state.
    This wraps the StateHost to provide a unified interface.
    """
    # Process count
    process_count: int = 0
    
    # Active process IDs
    active_processes: List[str] = field(default_factory=list)
    
    # Process states (reference to StateHost)
    # Note: Actual state data is in StateHost, this is metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "process_count": self.process_count,
            "active_processes": self.active_processes,
        }


@dataclass
class KernelControlState:
    """
    Kernel control state (k) per Canon Spec §10.1.
    
    k = (Π, Q, H, R, G) where:
    - Π: scheduler / priority state
    - Q: event queue
    - H: authority-handle table
    - R: routing and reserve register state
    - G: governance mode flags / interlocks
    """
    # Scheduler state (reference)
    scheduler_state: Dict[str, Any] = field(default_factory=dict)
    
    # Event queue
    event_queue: List[Dict[str, Any]] = field(default_factory=list)
    
    # Authority handles table
    authority_handles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Routing state
    routing_state: Dict[str, float] = field(default_factory=dict)
    
    # Governance mode
    mode: OperationalMode = OperationalMode.OBSERVE
    
    # Governance flags
    flags: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scheduler_state": self.scheduler_state,
            "event_queue_length": len(self.event_queue),
            "authority_handle_count": len(self.authority_handles),
            "routing_state": self.routing_state,
            "mode": self.mode.value,
            "flags": self.flags,
        }


@dataclass
class LedgerState:
    """
    Ledger state (ℓ) per Canon Spec §13.1.
    
    Contains:
    - previous chain digest (Ω_prev)
    - current chain digest (Ω_curr)
    - previous boundary state hash
    - current boundary state hash
    - object id
    - canon profile hash
    - policy hash
    - monotone event counter
    """
    # Chain digests
    chain_digest_prev: str = ""
    chain_digest_curr: str = ""
    
    # State hashes
    state_hash_prev: str = ""
    state_hash_curr: str = ""
    
    # Identifiers
    object_id: str = "gmos.substrate.v1"
    canon_profile_hash: str = ""
    policy_hash: str = ""
    
    # Event counter
    event_counter: int = 0
    
    # Receipt history (for replay)
    receipt_history: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "chain_digest_prev": self.chain_digest_prev,
            "chain_digest_curr": self.chain_digest_curr,
            "state_hash_prev": self.state_hash_prev,
            "state_hash_curr": self.state_hash_curr,
            "object_id": self.object_id,
            "canon_profile_hash": self.canon_profile_hash,
            "policy_hash": self.policy_hash,
            "event_counter": self.event_counter,
            "receipt_history_length": len(self.receipt_history),
        }


@dataclass
class FullSubstrateState:
    """
    Full substrate state (ξ) per GM-OS Canon Spec v1 §3.1.
    
    ξ = (x_ext, s, m, b, p, k, ℓ) ∈ Ξ
    
    This is the canonical state type that unifies all GM-OS components
    into a single state for kernel operations, receipt generation,
    and chain verification.
    
    Attributes:
        x_ext: External world interface state
        s: Sensory manifold (S_ext ⊕ S_sem ⊕ S_int)
        m: Memory manifold (M_C ⊕ M_E ⊕ M_W) - stored as dict with keys
        b: Budget bundle (vector of budget channels)
        p: Hosted process product state
        k: Kernel control state
        ℓ: Ledger state
    
    Properties:
        state_hash: Deterministic hash of entire state for receipts
    """
    # Per spec §3.1: ξ = (x_ext, s, m, b, p, k, ℓ)
    
    # Factor 1: External world interface (x_ext)
    x_ext: ExternalInterfaceState = field(default_factory=ExternalInterfaceState)
    
    # Factor 2: Sensory manifold (s = S_ext ⊕ S_sem ⊕ S_int)
    s: SensoryManifold = field(default_factory=SensoryManifold)
    
    # Factor 3: Memory manifold (m = M_C ⊕ M_E ⊕ M_W)
    # Stored as components for serialization
    m_workspace: WorkspaceState = field(default_factory=WorkspaceState)
    m_archive: ArchiveState = field(default_factory=ArchiveState)
    m_curvature: float = 0.0  # Structural memory M_C
    
    # Factor 4: Budget bundle (b ∈ B ⊂ ℝ_≥0^N)
    # Per spec: B = [0,B_1^max] × ... × [0,B_N^max]
    b: Dict[str, float] = field(default_factory=dict)
    b_reserves: Dict[str, float] = field(default_factory=dict)
    b_max: Dict[str, float] = field(default_factory=dict)
    
    # Factor 5: Hosted process product state (p = ∏ P_i)
    p: HostedProcessState = field(default_factory=HostedProcessState)
    
    # Factor 6: Kernel control state (k)
    k: KernelControlState = field(default_factory=KernelControlState)
    
    # Factor 7: Ledger state (ℓ)
    ℓ: LedgerState = field(default_factory=LedgerState)
    
    # Metadata
    step_index: int = 0
    timestamp: float = field(default_factory=time.time)
    
    # Cached state hash
    _state_hash: Optional[str] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Initialize default budget channels if not provided."""
        if not self.b:
            # Default budget channels per spec §7.1
            self.b = {
                "sens": 100.0,
                "mem": 100.0,
                "branch": 50.0,
                "plan": 50.0,
                "act": 50.0,
                "safety": 20.0,
                "kernel": 20.0,
            }
        if not self.b_reserves:
            # Default reserve floors per spec §7.2
            self.b_reserves = {
                "sens": 10.0,
                "mem": 10.0,
                "branch": 5.0,
                "plan": 5.0,
                "act": 5.0,
                "safety": 20.0,  # Safety reserve is protected
                "kernel": 5.0,
            }
        if not self.b_max:
            # Default max values
            self.b_max = {
                "sens": 200.0,
                "mem": 200.0,
                "branch": 100.0,
                "plan": 100.0,
                "act": 100.0,
                "safety": 50.0,
                "kernel": 50.0,
            }
    
    @property
    def state_hash(self) -> str:
        """
        Compute deterministic hash of entire state.
        
        This is the boundary hash h(ξ) used in receipts and chain digests
        per Canon Spec §13.2.
        """
        if self._state_hash is not None:
            return self._state_hash
        
        # Serialize state to canonical form
        canonical = self.to_canonical_json()
        
        # Compute SHA256 hash
        self._state_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self._state_hash
    
    def invalidate_hash(self):
        """Invalidate cached state hash after mutation."""
        self._state_hash = None
    
    def _serialize_component(self, obj) -> Dict[str, Any]:
        """Serialize a component, handling objects with or without to_dict."""
        if hasattr(obj, 'to_dict') and callable(obj.to_dict):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            # Fallback for dataclasses without to_dict
            result = {}
            for key, value in vars(obj).items():
                if not key.startswith('_'):
                    if hasattr(value, '__dict__'):
                        result[key] = self._serialize_component(value)
                    elif isinstance(value, (list, tuple)):
                        result[key] = [self._serialize_component(v) if hasattr(v, '__dict__') else v for v in value]
                    elif isinstance(value, dict):
                        result[key] = {k: (self._serialize_component(v) if hasattr(v, '__dict__') else v) for k, v in value.items()}
                    else:
                        result[key] = value
            return result
        else:
            return str(obj)
    
    def to_canonical_json(self) -> str:
        """
        Serialize to canonical JSON for hashing.
        
        This ensures deterministic hashing regardless of dict ordering.
        """
        data = {
            "x_ext": self._serialize_component(self.x_ext),
            "s": self._serialize_component(self.s),
            "m_workspace": self._serialize_component(self.m_workspace),
            "m_archive": self._serialize_component(self.m_archive),
            "m_curvature": self.m_curvature,
            "b": dict(sorted(self.b.items())),
            "b_reserves": dict(sorted(self.b_reserves.items())),
            "p": self._serialize_component(self.p),
            "k": self._serialize_component(self.k),
            "ℓ": self._serialize_component(self.ℓ),
            "step_index": self.step_index,
            "timestamp": self.timestamp,
        }
        return json.dumps(data, sort_keys=True, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Full serialization for receipts."""
        return {
            "state_hash": self.state_hash,
            "x_ext": self.x_ext.to_dict(),
            "s": self.s.to_dict(),
            "m_workspace": self.m_workspace.to_dict(),
            "m_archive": self.m_archive.to_dict(),
            "m_curvature": self.m_curvature,
            "b": self.b,
            "b_reserves": self.b_reserves,
            "p": self.p.to_dict(),
            "k": self.k.to_dict(),
            "ℓ": self.ℓ.to_dict(),
            "step_index": self.step_index,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FullSubstrateState':
        """Deserialize from dictionary."""
        # Extract budget channels
        b = data.get("b", {})
        b_reserves = data.get("b_reserves", {})
        
        # Create instance
        state = cls(
            step_index=data.get("step_index", 0),
            timestamp=data.get("timestamp", time.time()),
        )
        state.b = b
        state.b_reserves = b_reserves
        state._state_hash = data.get("state_hash")
        
        return state
    
    # === Budget Operations (per spec §7) ===
    
    def get_budget(self, channel: str) -> float:
        """Get budget for a channel."""
        return self.b.get(channel, 0.0)
    
    def get_available_budget(self, channel: str) -> float:
        """Get available budget (total - reserve)."""
        total = self.b.get(channel, 0.0)
        reserve = self.b_reserves.get(channel, 0.0)
        return max(0.0, total - reserve)
    
    def can_spend(self, channel: str, amount: float) -> bool:
        """Check if spend is allowed (respects reserve)."""
        return self.get_available_budget(channel) >= amount
    
    def spend(self, channel: str, amount: float) -> bool:
        """
        Execute spend on a budget channel.
        
        Returns True if spend was executed, False if not allowed
        (respects reserve floors per spec §7.2).
        """
        if not self.can_spend(channel, amount):
            return False
        
        self.b[channel] = self.b.get(channel, 0.0) - amount
        self.invalidate_hash()
        return True
    
    def route_budget(self, source: str, target: str, amount: float) -> bool:
        """
        Route budget between channels (per spec §7.3).
        
        Conservation law: Σ Δb_i = 0
        
        Returns True if routing succeeded.
        """
        if not self.can_spend(source, amount):
            return False
        if self.b.get(target, 0.0) + amount > self.b_max.get(target, float('inf')):
            return False
        
        # Execute routing
        self.b[source] = self.b.get(source, 0.0) - amount
        self.b[target] = self.b.get(target, 0.0) + amount
        self.invalidate_hash()
        return True
    
    # === Admissibility Check (per spec §4) ===
    
    def is_admissible(self) -> bool:
        """
        Check if state is in admissible domain K.
        
        Per spec §4, admissibility requires:
        - V(ξ) ≤ Θ (potential below threshold)
        - All reserve floors satisfied: b_i ≥ b_i,reserve
        - Anchor conflicts resolved
        - Kernel constraints satisfied
        """
        # Check reserve floors
        for channel, reserve in self.b_reserves.items():
            if self.b.get(channel, 0.0) < reserve:
                return False
        
        # Check budget bounds
        for channel, max_val in self.b_max.items():
            if self.b.get(channel, 0.0) > max_val:
                return False
        
        # Check non-negative
        for channel, value in self.b.items():
            if value < 0:
                return False
        
        return True
    
    # === Copy and Snapshot ===
    
    def copy(self) -> 'FullSubstrateState':
        """Create a deep copy of the state."""
        import copy
        return copy.deepcopy(self)
    
    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot for receipts."""
        return {
            "state_hash": self.state_hash,
            "step_index": self.step_index,
            "timestamp": self.timestamp,
            "is_admissible": self.is_admissible(),
            "budget_summary": {
                channel: {
                    "total": self.b.get(channel, 0),
                    "reserve": self.b_reserves.get(channel, 0),
                    "available": self.get_available_budget(channel),
                }
                for channel in set(self.b.keys()) | set(self.b_reserves.keys())
            },
        }
    
    # === Step Integration ===
    
    def advance_step(self):
        """Advance the step counter after a discrete transition."""
        self.step_index += 1
        self.timestamp = time.time()
        self.invalidate_hash()
    
    def apply_receipt(self, receipt_data: Dict[str, Any]):
        """
        Apply receipt data to state after acceptance.
        
        Updates ledger state and advances step.
        """
        # Update ledger
        self.ℓ.event_counter += 1
        self.ℓ.state_hash_prev = self.ℓ.state_hash_curr
        self.ℓ.state_hash_curr = self.state_hash
        
        # Record receipt in history
        receipt_json = json.dumps(receipt_data, sort_keys=True, default=str)
        self.ℓ.receipt_history.append(receipt_json)
        
        # Advance step
        self.advance_step()


# === Factory Functions ===

def create_initial_state(
    object_id: str = "gmos.substrate.v1",
    initial_budget: Optional[Dict[str, float]] = None,
    mode: OperationalMode = OperationalMode.OBSERVE,
) -> FullSubstrateState:
    """
    Create initial substrate state.
    
    Args:
        object_id: Unique identifier for this GM-OS instance
        initial_budget: Initial budget values (uses defaults if None)
        mode: Initial operational mode
    
    Returns:
        Initialized FullSubstrateState
    """
    state = FullSubstrateState()
    
    if initial_budget:
        state.b.update(initial_budget)
    
    state.ℓ.object_id = object_id
    state.k.mode = mode
    
    # Initialize with genesis chain digest
    state.ℓ.chain_digest_curr = hashlib.sha256(
        f"genesis:{object_id}".encode()
    ).hexdigest()
    
    return state


# === Receipt Integration ===

def compute_chain_digest(
    prev_digest: str,
    receipt_data: Dict[str, Any],
    state_hash: str,
) -> str:
    """
    Compute next chain digest per spec §13.3.
    
    Ω_{k+1} = Hash(Ω_k ;|; encode(r_k) ;|; h(ξ_k) ;|; h(ξ_{k+1}))
    
    Simplified: Ω_{k+1} = Hash(Ω_k || receipt_json || state_hash)
    """
    receipt_json = json.dumps(receipt_data, sort_keys=True, default=str)
    combined = f"{prev_digest}|{receipt_json}|{state_hash}"
    return hashlib.sha256(combined.encode()).hexdigest()


# === Type Alias ===

# Full state type for type hints
GMOSState = FullSubstrateState
