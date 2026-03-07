"""
Scheduler for GM-OS Kernel.

Runs hosted processes on layered timescales, decides which process/layer
executes next, prevents starvation of survival-critical layers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import time


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
        
        # TODO: Implement actual wake condition evaluation
        # For now, return False - processes need explicit wake call
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
