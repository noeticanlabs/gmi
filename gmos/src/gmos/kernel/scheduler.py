"""
Scheduler for GM-OS Kernel.

Runs hosted processes on layered timescales, decides which process/layer
executes next, prevents starvation of survival-critical layers.

Per GM-OS Canon Spec v1 §22: Operational modes control admissible events.
Maps between spec modes and internal scheduling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import time

# Import spec modes from substrate_state
from gmos.kernel.substrate_state import OperationalMode


class ScheduleMode(Enum):
    """Scheduling priority modes."""
    SURVIVAL_CRITICAL = 1   # reflex / survival
    SAFETY = 2              # collision avoidance
    ACTIVE = 3             # working cognition
    REFLECTIVE = 4         # planning
    CONSOLIDATION = 5      # maintenance
    STRATEGIC = 6          # long-term planning
    TORPOR = 99            # no budget


class ProcessStatus(Enum):
    """Process execution status."""
    RUNNING = "running"
    HALTED = "halted"
    TORPOR = "torpor"


@dataclass
class ScheduledProcess:
    """Process scheduled for execution."""
    process_id: str
    mode: ScheduleMode
    priority: int
    status: ProcessStatus = ProcessStatus.RUNNING
    last_tick: float = 0.0
    tick_count: int = 0
    wake_condition: Optional[str] = None  # Condition for waking from torpor


class KernelScheduler:
    """
    Kernel scheduler for multi-process, multi-layer execution.
    
    Priority order:
    1. reflex / survival
    2. safety / collision avoidance
    3. active working loop
    4. reflective planning
    5. consolidation / maintenance
    6. strategic planning
    
    Features:
    - Skips halted processes
    - Skips torpor processes unless wake condition is met
    - Reflex/survival priority always runs first
    - Deterministic tie-breaking (by process_id)
    """
    
    def __init__(self):
        self._processes: Dict[str, ScheduledProcess] = {}
        self._current_mode: ScheduleMode = ScheduleMode.ACTIVE
        self._execution_queue: List[str] = []
    
    def register_process(
        self, 
        process_id: str, 
        mode: ScheduleMode = ScheduleMode.ACTIVE,
        wake_condition: Optional[str] = None
    ) -> None:
        """Register a process for scheduling."""
        self._processes[process_id] = ScheduledProcess(
            process_id=process_id,
            mode=mode,
            priority=mode.value,
            wake_condition=wake_condition
        )
        self._rebuild_queue()
    
    def next_process(self) -> Optional[str]:
        """Get next process to execute (skipping halted/torpor)."""
        while self._execution_queue:
            pid = self._execution_queue.pop(0)
            if pid in self._processes:
                proc = self._processes[pid]
                
                # Skip halted processes
                if proc.status == ProcessStatus.HALTED:
                    continue
                
                # Skip torpor processes unless wake condition is met
                if proc.status == ProcessStatus.TORPOR:
                    if not self._check_wake_condition(pid):
                        continue
                    # Wake up the process
                    proc.status = ProcessStatus.RUNNING
                
                # Execute this process
                proc.tick_count += 1
                proc.last_tick = time.time()
                return pid
        
        return None
    
    def tick(self) -> Optional[str]:
        """Execute one scheduling tick."""
        return self.next_process()
    
    def suspend_process(self, process_id: str) -> bool:
        """Temporarily suspend a process."""
        if process_id in self._execution_queue:
            self._execution_queue.remove(process_id)
            return True
        return False
    
    def resume_process(self, process_id: str) -> bool:
        """Resume a suspended process."""
        if process_id in self._processes:
            self._rebuild_queue()
            return True
        return False
    
    def set_mode(self, mode: ScheduleMode) -> None:
        """Set current scheduling mode."""
        self._current_mode = mode
    
    def mark_halted(self, process_id: str) -> bool:
        """Mark process as halted (skipped in scheduling)."""
        if process_id in self._processes:
            self._processes[process_id].status = ProcessStatus.HALTED
            # Remove from execution queue
            if process_id in self._execution_queue:
                self._execution_queue.remove(process_id)
            return True
        return False
    
    def mark_torpor(self, process_id: str) -> bool:
        """Mark process as in torpor (budget depleted)."""
        if process_id in self._processes:
            self._processes[process_id].status = ProcessStatus.TORPOR
            # Remove from execution queue (will be reconsidered on wake)
            if process_id in self._execution_queue:
                self._execution_queue.remove(process_id)
            return True
        return False
    
    def wake_process(self, process_id: str) -> bool:
        """Wake a process from torpor (requires budget replenishment)."""
        if process_id in self._processes:
            proc = self._processes[process_id]
            if proc.status == ProcessStatus.TORPOR:
                proc.status = ProcessStatus.RUNNING
                self._rebuild_queue()
                return True
        return False
    
    def get_status(self, process_id: str) -> Optional[ProcessStatus]:
        """Get process status."""
        if process_id in self._processes:
            return self._processes[process_id].status
        return None
    
    def _check_wake_condition(self, process_id: str) -> bool:
        """Check if torpor process should wake up."""
        proc = self._processes[process_id]
        
        # If no wake condition, process stays in torpor indefinitely
        if proc.wake_condition is None:
            return False
        
        # Evaluate wake condition based on condition type
        condition = proc.wake_condition
        
        # Parse condition: "budget_above_X" or "queue_nonempty" or "age_above_X"
        if condition.startswith("budget_above_"):
            try:
                threshold = float(condition.split("_")[2])
                # Would check actual budget - for now return False
                # This requires access to budget router
                return False
            except (IndexError, ValueError):
                return False
        
        elif condition == "queue_nonempty":
            # Check if execution queue has items
            return len(self._execution_queue) > 0
        
        elif condition.startswith("age_above_"):
            try:
                # Age in seconds
                threshold = float(condition.split("_")[2])
                import time
                age = time.time() - proc.last_tick
                return age > threshold
            except (IndexError, ValueError):
                return False
        
        elif condition == "repair_mode":
            # Would check if system is in repair mode
            return False
        
        elif condition == "action_ready":
            # Would check if action preparation is ready
            return False
        
        # Unknown condition - stay in torpor
        return False
    
    def _rebuild_queue(self) -> None:
        """Rebuild execution queue by priority (with deterministic tie-breaking)."""
        # Filter out halted processes
        active_procs = [
            p for p in self._processes.values()
            if p.status != ProcessStatus.HALTED
        ]
        
        # Sort by: priority (ascending), then tick_count (descending), then process_id (ascending for determinism)
        sorted_procs = sorted(
            active_procs,
            key=lambda p: (p.priority, -p.tick_count, p.process_id)
        )
        self._execution_queue = [p.process_id for p in sorted_procs]
    
    def list_active(self) -> List[str]:
        """List all active (running) processes."""
        return [
            p.process_id for p in self._processes.values()
            if p.status == ProcessStatus.RUNNING
        ]
    
    def list_all(self) -> List[str]:
        """List all registered process IDs."""
        return list(self._processes.keys())
    
    
    # === Mode Mapping (per spec §22) ===
    
    # Mapping from spec operational modes to allowed event classes
    MODE_EVENT_PERMISSIONS: Dict[OperationalMode, Set[str]] = {
        OperationalMode.OBSERVE: {"sense", "mem", "branch"},
        OperationalMode.REPAIR: {"sense", "mem", "branch", "merge"},
        OperationalMode.PLAN: {"sense", "mem", "branch", "plan"},
        OperationalMode.ACT: {"sense", "mem", "branch", "plan", "act"},
        OperationalMode.SAFE_HOLD: {"sense", "mem", "audit"},
        OperationalMode.AUDIT: {"audit"},
    }
    
    # Mapping from spec operational modes to schedule modes
    MODE_SCHEDULE_MAPPING: Dict[OperationalMode, List[ScheduleMode]] = {
        OperationalMode.OBSERVE: [ScheduleMode.ACTIVE],
        OperationalMode.REPAIR: [ScheduleMode.ACTIVE, ScheduleMode.CONSOLIDATION],
        OperationalMode.PLAN: [ScheduleMode.ACTIVE, ScheduleMode.REFLECTIVE],
        OperationalMode.ACT: [
            ScheduleMode.SURVIVAL_CRITICAL,
            ScheduleMode.SAFETY,
            ScheduleMode.ACTIVE,
            ScheduleMode.REFLECTIVE,
        ],
        OperationalMode.SAFE_HOLD: [ScheduleMode.SAFETY],
        OperationalMode.AUDIT: [],  # No process execution
    }
    
    def get_allowed_events(self, mode: OperationalMode) -> Set[str]:
        """
        Get allowed event classes for a mode.
        
        Per spec §22: Mode affects admissible event classes.
        
        Args:
            mode: Operational mode
            
        Returns:
            Set of allowed event class names
        """
        return self.MODE_EVENT_PERMISSIONS.get(mode, set())
    
    def is_event_allowed(self, mode: OperationalMode, event_class: str) -> bool:
        """
        Check if event class is allowed in mode.
        
        Args:
            mode: Current operational mode
            event_class: Event class to check
            
        Returns:
            True if allowed
        """
        return event_class in self.get_allowed_events(mode)
    
    def get_schedule_modes(self, mode: OperationalMode) -> List[ScheduleMode]:
        """
        Get schedule modes for operational mode.
        
        Args:
            mode: Operational mode
            
        Returns:
            List of schedule modes (priority order)
        """
        return self.MODE_SCHEDULE_MAPPING.get(mode, [])
    
    @classmethod
    def mode_to_schedule_modes(cls, mode: OperationalMode) -> List[ScheduleMode]:
        """Get schedule modes for operational mode (class method)."""
        return cls.MODE_SCHEDULE_MAPPING.get(mode, [])
    
    @classmethod
    def map_spec_mode_to_schedule_mode(cls, mode: OperationalMode) -> ScheduleMode:
        """
        Map spec mode to primary schedule mode.
        
        Args:
            mode: Spec operational mode
            
        Returns:
            Primary schedule mode
        """
        schedule_modes = cls.MODE_SCHEDULE_MAPPING.get(mode, [])
        if schedule_modes:
            return schedule_modes[0]
        return ScheduleMode.IDLE
    
    def set_mode(self, mode: OperationalMode):
        """
        Set operational mode and update scheduler accordingly.
        
        Per spec §22: Mode affects admissible event classes, branch limits,
        defect tolerances, action permissions, reserve floors, and authority
        thresholds.
        
        Args:
            mode: New operational mode
        """
        # Get primary schedule mode
        primary = self.map_spec_mode_to_schedule_mode(mode)
        
        # Get allowed events
        allowed = self.get_allowed_events(mode)
        
        # Update internal state if needed
        # (In a full implementation, this would adjust scheduling priorities)
        self._mode = mode
        
        # For AUDIT mode, halt all processes
        if mode == OperationalMode.AUDIT:
            for proc in self._processes.values():
                proc.status = ProcessStatus.HALTED
    
    def get_current_mode(self) -> OperationalMode:
        """Get current operational mode."""
        return getattr(self, '_mode', OperationalMode.OBSERVE)
