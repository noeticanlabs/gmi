"""
GM-OS Mode Machine for Phase 3

Implements explicit operating modes and transitions for the runtime.
This makes the substrate stateful, observable, and controllable.

Key features:
- Explicit mode transitions (not just enum)
- Failure routing to different modes
- SafeHold pathway for abstention
- Mode-specific metrics and logging
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import uuid


class RuntimeMode(Enum):
    """
    Runtime operational modes.
    
    These are the active modes the system cycles through during execution,
    distinct from the lower-level OperationalMode in substrate_state.
    """
    OBSERVE = "observe"        # Ingest and anchor percepts
    RECALL = "recall"          # Retrieve and stage memory
    DELIBERATE = "deliberate"  # Generate and compare proposals
    VERIFY = "verify"           # Score admissibility, spend, residual
    COMMIT = "commit"           # Take action and write receipt
    REPAIR = "repair"           # Attempt lawful correction after failure
    SAFE_HOLD = "safe_hold"    # Abstain under high uncertainty/budget stress
    CONSOLIDATE = "consolidate" # Post-episode memory update
    
    # Shorthand
    def __str__(self):
        return self.value


class TransitionReason(Enum):
    """Why a mode transition occurred."""
    # Forward transitions
    PERCEPT_COMPLETE = "percept_anchor_complete"
    MEMORY_RETRIEVED = "memory_retrieval_complete"
    PROPOSALS_GENERATED = "proposals_generated"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_COMPLETE = "verification_complete"
    ACTION_COMMITTED = "action_committed"
    EPISODE_COMPLETE = "episode_complete"
    
    # Failure handling
    VERIFICATION_FAILED = "verification_failed"
    REPAIR_FAILED = "repair_failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    UNCERTAINTY_HIGH = "uncertainty_too_high"
    NO_PROPOSALS = "no_valid_proposals"
    
    # SafeHold triggers
    SAFE_HOLD_TRIGGERED = "safe_hold_triggered"
    SAFE_HOLD_RESOLVED = "safe_hold_resolved"


# Valid transitions: current_mode -> [(next_mode, reason), ...]
VALID_TRANSITIONS: Dict[RuntimeMode, List[tuple]] = {
    RuntimeMode.OBSERVE: [
        (RuntimeMode.RECALL, TransitionReason.PERCEPT_COMPLETE),
    ],
    RuntimeMode.RECALL: [
        (RuntimeMode.DELIBERATE, TransitionReason.MEMORY_RETRIEVED),
        (RuntimeMode.SAFE_HOLD, TransitionReason.UNCERTAINTY_HIGH),
    ],
    RuntimeMode.DELIBERATE: [
        (RuntimeMode.VERIFY, TransitionReason.PROPOSALS_GENERATED),
        (RuntimeMode.SAFE_HOLD, TransitionReason.NO_PROPOSALS),
    ],
    RuntimeMode.VERIFY: [
        (RuntimeMode.COMMIT, TransitionReason.VERIFICATION_PASSED),
        (RuntimeMode.REPAIR, TransitionReason.VERIFICATION_FAILED),
        (RuntimeMode.SAFE_HOLD, TransitionReason.VERIFICATION_FAILED),
    ],
    RuntimeMode.COMMIT: [
        (RuntimeMode.CONSOLIDATE, TransitionReason.ACTION_COMMITTED),
        (RuntimeMode.OBSERVE, TransitionReason.EPISODE_COMPLETE),
    ],
    RuntimeMode.REPAIR: [
        (RuntimeMode.VERIFY, TransitionReason.REPAIR_FAILED),  # Try again
        (RuntimeMode.SAFE_HOLD, TransitionReason.REPAIR_FAILED),
    ],
    RuntimeMode.SAFE_HOLD: [
        (RuntimeMode.OBSERVE, TransitionReason.SAFE_HOLD_RESOLVED),
        (RuntimeMode.CONSOLIDATE, TransitionReason.SAFE_HOLD_TRIGGERED),
    ],
    RuntimeMode.CONSOLIDATE: [
        (RuntimeMode.OBSERVE, TransitionReason.EPISODE_COMPLETE),
    ],
}


@dataclass
class ModeTransition:
    """Record of a mode transition."""
    from_mode: RuntimeMode
    to_mode: RuntimeMode
    reason: TransitionReason
    timestamp: float
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModeMetrics:
    """Metrics for a specific mode."""
    mode: RuntimeMode
    entry_count: int = 0
    total_time_ms: float = 0.0
    failure_count: int = 0
    success_count: int = 0
    
    @property
    def avg_time_ms(self) -> float:
        if self.entry_count == 0:
            return 0.0
        return self.total_time_ms / self.entry_count
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total


@dataclass
class SafeHoldConfig:
    """Configuration for SafeHold behavior."""
    # When to trigger SafeHold
    uncertainty_threshold: float = 0.7    # Confidence below this triggers SafeHold
    budget_threshold: float = 0.2          # Budget below 20% triggers SafeHold
    min_proposals: int = 1                # Minimum valid proposals required
    
    # What SafeHold does
    allow_commit: bool = False            # SafeHold prevents commits
    allow_repair: bool = False            # SafeHold prevents repairs
    force_observation: bool = True         # Force re-observation
    
    # Recovery
    max_consecutive_holds: int = 3        # Max SafeHolds before forcing action
    hold_decay: float = 0.8               # Decay hold urgency each step


class ModeMachine:
    """
    State machine for runtime mode transitions.
    
    Manages explicit transitions between OBSERVE → RECALL → DELIBERATE → 
    VERIFY → COMMIT → CONSOLIDATE, with REPAIR and SAFE_HOLD as 
    failure/abstention pathways.
    """
    
    def __init__(
        self,
        enable_safehold: bool = True,
        safehold_config: Optional[SafeHoldConfig] = None,
        enable_logging: bool = False
    ):
        self.current_mode = RuntimeMode.OBSERVE
        self.mode_history: List[ModeTransition] = []
        self.mode_metrics: Dict[RuntimeMode, ModeMetrics] = {
            mode: ModeMetrics(mode=mode) for mode in RuntimeMode
        }
        
        self.enable_safehold = enable_safehold
        self.safehold_config = safehold_config or SafeHoldConfig()
        self.enable_logging = enable_logging
        
        # Tracking
        self._mode_entry_time: Optional[float] = None
        self._consecutive_holds: int = 0
        self._episode_count: int = 0
        
        # Callbacks for mode entry/exit
        self._on_enter_callbacks: Dict[RuntimeMode, List[Callable]] = {
            mode: [] for mode in RuntimeMode
        }
        self._on_exit_callbacks: Dict[RuntimeMode, List[Callable]] = {
            mode: [] for mode in RuntimeMode
        }
    
    def reset(self) -> None:
        """Reset to initial state."""
        self.current_mode = RuntimeMode.OBSERVE
        self.mode_history.clear()
        for metrics in self.mode_metrics.values():
            metrics.entry_count = 0
            metrics.total_time_ms = 0.0
            metrics.failure_count = 0
            metrics.success_count = 0
        self._consecutive_holds = 0
        self._episode_count = 0
    
    def transition(
        self,
        next_mode: RuntimeMode,
        reason: TransitionReason,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Attempt to transition to a new mode.
        
        Returns True if transition was successful, False if invalid.
        """
        from_mode = self.current_mode
        to_mode = next_mode
        
        # Check if transition is valid
        valid_targets = VALID_TRANSITIONS.get(from_mode, [])
        valid = any(to_mode == target for target, _ in valid_targets)
        
        if not valid:
            # Log invalid transition attempt
            if self.enable_logging:
                print(f"Invalid transition: {from_mode} -> {to_mode} (reason: {reason})")
            return False
        
        # Record transition
        self._record_transition(from_mode, to_mode, reason, metadata or {})
        
        # Update metrics
        self._update_mode_metrics(from_mode, success=True)
        
        # Execute exit callbacks
        self._execute_callbacks(self._on_exit_callbacks[from_mode])
        
        # Update state
        self.current_mode = to_mode
        self._mode_entry_time = datetime.now().timestamp()
        
        # Track SafeHold count
        if to_mode == RuntimeMode.SAFE_HOLD:
            self._consecutive_holds += 1
        else:
            self._consecutive_holds = 0
        
        # Execute enter callbacks
        self._execute_callbacks(self._on_enter_callbacks[to_mode])
        
        return True
    
    def check_safehold_condition(
        self,
        confidence: float,
        budget_remaining: float,
        budget_total: float,
        valid_proposals: int
    ) -> bool:
        """
        Check if SafeHold should be triggered.
        
        Returns True if SafeHold condition is met.
        """
        if not self.enable_safehold:
            return False
        
        config = self.safehold_config
        
        # Check confidence
        if confidence < config.uncertainty_threshold:
            return True
        
        # Check budget
        budget_ratio = budget_remaining / budget_total if budget_total > 0 else 0
        if budget_ratio < config.budget_threshold:
            return True
        
        # Check proposals
        if valid_proposals < config.min_proposals:
            return True
        
        # Check consecutive holds (force action after threshold)
        if self._consecutive_holds >= config.max_consecutive_holds:
            return False  # Force action
        
        return False
    
    def force_safehold(
        self,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Force transition to SafeHold mode.
        
        Used when external conditions require SafeHold.
        """
        return self.transition(
            RuntimeMode.SAFE_HOLD,
            TransitionReason.SAFE_HOLD_TRIGGERED,
            {**(metadata or {}), "forced": True, "reason": reason}
        )
    
    def proceed_after_verification(
        self,
        verification_passed: bool,
        repair_successful: Optional[bool] = None
    ) -> RuntimeMode:
        """
        Determine next mode after verification.
        
        This is a convenience method that handles the common
        VERIFY → COMMIT / REPAIR / SAFE_HOLD decision.
        """
        if verification_passed:
            self.transition(RuntimeMode.COMMIT, TransitionReason.VERIFICATION_PASSED)
            return RuntimeMode.COMMIT
        
        # Verification failed - try repair or SafeHold
        if repair_successful is True:
            self.transition(RuntimeMode.VERIFY, TransitionReason.REPAIR_FAILED)
            return RuntimeMode.VERIFY
        
        # Repair failed or not attempted
        if self.enable_safehold and self._consecutive_holds < self.safehold_config.max_consecutive_holds:
            self.transition(RuntimeMode.SAFE_HOLD, TransitionReason.VERIFICATION_FAILED)
            return RuntimeMode.SAFE_HOLD
        
        # Force commit after too many SafeHolds
        self.transition(RuntimeMode.COMMIT, TransitionReason.VERIFICATION_FAILED)
        return RuntimeMode.COMMIT
    
    def on_enter(
        self,
        mode: RuntimeMode,
        callback: Callable
    ) -> None:
        """Register a callback to run when entering a mode."""
        self._on_enter_callbacks[mode].append(callback)
    
    def on_exit(
        self,
        mode: RuntimeMode,
        callback: Callable
    ) -> None:
        """Register a callback to run when exiting a mode."""
        self._on_exit_callbacks[mode].append(callback)
    
    def get_mode_distribution(self) -> Dict[str, int]:
        """Get distribution of modes in current episode."""
        distribution = {mode.value: 0 for mode in RuntimeMode}
        for transition in self.mode_history:
            distribution[transition.from_mode.value] += 1
        return distribution
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of mode metrics."""
        return {
            mode.value: {
                "entry_count": metrics.entry_count,
                "avg_time_ms": metrics.avg_time_ms,
                "success_rate": metrics.success_rate
            }
            for mode, metrics in self.mode_metrics.items()
        }
    
    def get_trace(self) -> List[Dict[str, Any]]:
        """Get full trace of mode transitions."""
        return [
            {
                "from": t.from_mode.value,
                "to": t.to_mode.value,
                "reason": t.reason.value,
                "timestamp": t.timestamp,
                "duration_ms": t.duration_ms,
                "metadata": t.metadata
            }
            for t in self.mode_history
        ]
    
    def _record_transition(
        self,
        from_mode: RuntimeMode,
        to_mode: RuntimeMode,
        reason: TransitionReason,
        metadata: Dict[str, Any]
    ) -> None:
        """Record a mode transition."""
        now = datetime.now().timestamp()
        duration = 0.0
        if self._mode_entry_time is not None:
            duration = (now - self._mode_entry_time) * 1000  # ms
        
        transition = ModeTransition(
            from_mode=from_mode,
            to_mode=to_mode,
            reason=reason,
            timestamp=now,
            duration_ms=duration,
            metadata=metadata
        )
        
        self.mode_history.append(transition)
        
        if self.enable_logging:
            print(f"MODE: {from_mode} -> {to_mode} ({reason.value}) [{duration:.1f}ms]")
    
    def _update_mode_metrics(
        self,
        mode: RuntimeMode,
        success: bool
    ) -> None:
        """Update metrics for a mode."""
        metrics = self.mode_metrics[mode]
        metrics.entry_count += 1
        
        if self._mode_entry_time is not None:
            duration = (datetime.now().timestamp() - self._mode_entry_time) * 1000
            metrics.total_time_ms += duration
        
        if success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
    
    def _execute_callbacks(self, callbacks: List[Callable]) -> None:
        """Execute all registered callbacks."""
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                if self.enable_logging:
                    print(f"Callback error: {e}")


def create_mode_machine(
    enable_safehold: bool = True,
    enable_logging: bool = False
) -> ModeMachine:
    """Factory function to create a mode machine."""
    return ModeMachine(
        enable_safehold=enable_safehold,
        enable_logging=enable_logging
    )
