"""
State Host for GM-OS Kernel.

Hosts process state objects, provides typed process state containers,
handles safe read/write access to process-local state, exposes state 
snapshots for receipts and replay.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import hashlib
import json


class ProcessStateFlag(Enum):
    """Process state lifecycle flags."""
    ACTIVE = "active"
    HALTED = "halted"
    TORPOR = "torpor"
    WAKING = "waking"


@dataclass
class HostedState:
    """Container for a hosted process state."""
    process_id: str
    state_data: Dict[str, Any]
    state_hash: str = ""
    flag: ProcessStateFlag = ProcessStateFlag.ACTIVE
    step_index: int = 0
    
    def __post_init__(self):
        if not self.state_hash:
            self.state_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute deterministic hash of state."""
        serialized = json.dumps(self.state_data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    
    def snapshot(self) -> Dict[str, Any]:
        """Return state snapshot for receipts."""
        return {
            "process_id": self.process_id,
            "state_hash": self.state_hash,
            "flag": self.flag.value,
            "step_index": self.step_index,
            "state_data": self.state_data
        }


class StateHost:
    """
    Manager for hosted process states.
    
    Provides:
    - register a process state by process id
    - fetch current state
    - commit next state after verifier approval
    - expose state hash input view
    - support halt / torpor / wake state flags
    """
    
    def __init__(self):
        self._states: Dict[str, HostedState] = {}
    
    def register_process(self, process_id: str, initial_state: Dict[str, Any]) -> HostedState:
        """Register a new process with initial state."""
        state = HostedState(
            process_id=process_id,
            state_data=initial_state
        )
        self._states[process_id] = state
        return state
    
    def get_state(self, process_id: str) -> Optional[HostedState]:
        """Fetch current state for a process."""
        return self._states.get(process_id)
    
    def set_state(self, process_id: str, new_state: Dict[str, Any]) -> HostedState:
        """Commit new state after verifier approval."""
        if process_id not in self._states:
            raise ValueError(f"Process {process_id} not registered")
        
        current = self._states[process_id]
        updated = HostedState(
            process_id=process_id,
            state_data=new_state,
            step_index=current.step_index + 1,
            flag=current.flag
        )
        self._states[process_id] = updated
        return updated
    
    def snapshot_state(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Expose state hash input view for receipts."""
        state = self.get_state(process_id)
        return state.snapshot() if state else None
    
    def mark_halt(self, process_id: str) -> bool:
        """Mark process as halted (no lawful move available)."""
        if process_id in self._states:
            self._states[process_id].flag = ProcessStateFlag.HALTED
            return True
        return False
    
    def mark_torpor(self, process_id: str) -> bool:
        """Mark process as in torpor (budget depleted)."""
        if process_id in self._states:
            self._states[process_id].flag = ProcessStateFlag.TORPOR
            return True
        return False
    
    def mark_wake(self, process_id: str) -> bool:
        """Mark process as waking (replenishment received)."""
        if process_id in self._states:
            self._states[process_id].flag = ProcessStateFlag.WAKING
            return True
        return False
    
    def list_active(self) -> list[str]:
        """List all active process IDs."""
        return [
            pid for pid, s in self._states.items()
            if s.flag == ProcessStateFlag.ACTIVE
        ]
