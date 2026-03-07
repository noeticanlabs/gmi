"""
Process Table for GM-OS Kernel.

Maintains registry of all hosted processes, tracks modes, priorities,
memory scopes, and verifier handles.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from enum import Enum


class ProcessType(Enum):
    """Types of hosted processes."""
    GMI = "gmi"
    PLANNER = "planner"
    PHYSICS = "physics"
    SYMBOLIC = "symbolic"
    NS = "ns"


class ProcessMode(Enum):
    """Process execution modes."""
    RUNNING = "running"
    SUSPENDED = "suspended"
    HALTED = "halted"
    TORPOR = "torpor"
    WAITING = "waiting"


@dataclass
class ProcessRecord:
    """Metadata record for a hosted process."""
    process_id: str
    process_type: ProcessType
    mode: ProcessMode
    priority: int
    state_host_key: str
    budget_handle: str
    verifier_handle: Optional[str] = None
    memory_scope: Optional[str] = None
    layer_count: int = 4
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProcessTable:
    """
    Registry for all hosted processes.
    
    Tracks:
    - process registration
    - process metadata lookup
    - mode tracking
    - active/inactive status
    - links to state host, budget, verifier, memory
    """
    
    def __init__(self):
        self._processes: Dict[str, ProcessRecord] = {}
    
    def register(
        self,
        process_id: str,
        process_type: ProcessType,
        priority: int = 5,
        state_host_key: str = "",
        budget_handle: str = "",
        verifier_handle: Optional[str] = None,
        memory_scope: Optional[str] = None,
        layer_count: int = 4
    ) -> ProcessRecord:
        """Register a new process."""
        record = ProcessRecord(
            process_id=process_id,
            process_type=process_type,
            mode=ProcessMode.RUNNING,
            priority=priority,
            state_host_key=state_host_key,
            budget_handle=budget_handle,
            verifier_handle=verifier_handle,
            memory_scope=memory_scope,
            layer_count=layer_count
        )
        self._processes[process_id] = record
        return record
    
    def get(self, process_id: str) -> Optional[ProcessRecord]:
        """Get process record by ID."""
        return self._processes.get(process_id)
    
    def set_mode(self, process_id: str, mode: ProcessMode) -> bool:
        """Set process mode."""
        if process_id in self._processes:
            self._processes[process_id].mode = mode
            return True
        return False
    
    def list_active(self) -> List[ProcessRecord]:
        """List all active (running) processes."""
        return [
            r for r in self._processes.values()
            if r.mode == ProcessMode.RUNNING
        ]
    
    def list_halted(self) -> List[ProcessRecord]:
        """List all halted processes."""
        return [
            r for r in self._processes.values()
            if r.mode == ProcessMode.HALTED
        ]
    
    def remove(self, process_id: str) -> bool:
        """Remove a process from the table."""
        if process_id in self._processes:
            del self._processes[process_id]
            return True
        return False
    
    def list_by_type(self, process_type: ProcessType) -> List[ProcessRecord]:
        """List all processes of a given type."""
        return [
            r for r in self._processes.values()
            if r.process_type == process_type
        ]
