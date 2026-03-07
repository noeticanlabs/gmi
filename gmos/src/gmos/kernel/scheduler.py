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


@dataclass
class ScheduledProcess:
    """Process scheduled for execution."""
    process_id: str
    mode: ScheduleMode
    priority: int
    last_tick: float = 0.0
    tick_count: int = 0


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
    """
    
    def __init__(self):
        self._processes: Dict[str, ScheduledProcess] = {}
        self._current_mode: ScheduleMode = ScheduleMode.ACTIVE
        self._execution_queue: List[str] = []
    
    def register_process(self, process_id: str, mode: ScheduleMode = ScheduleMode.ACTIVE) -> None:
        """Register a process for scheduling."""
        self._processes[process_id] = ScheduledProcess(
            process_id=process_id,
            mode=mode,
            priority=mode.value
        )
        self._rebuild_queue()
    
    def next_process(self) -> Optional[str]:
        """Get next process to execute."""
        if self._execution_queue:
            pid = self._execution_queue.pop(0)
            if pid in self._processes:
                self._processes[pid].tick_count += 1
                self._processes[pid].last_tick = time.time()
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
    
    def _rebuild_queue(self) -> None:
        """Rebuild execution queue by priority."""
        sorted_procs = sorted(
            self._processes.values(),
            key=lambda p: (p.priority, -p.tick_count)
        )
        self._execution_queue = [p.process_id for p in sorted_procs]
    
    def list_active(self) -> List[str]:
        """List all active (non-torpor) processes."""
        return [p.process_id for p in self._processes.values()]
