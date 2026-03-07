# GM-OS File Creation Checklist

## Phase 1: NEW KERNEL LOGIC (6 modules with full implementation)

### 1.1 `src/gmos/kernel/state_host.py`

```python
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
```

### 1.2 `src/gmos/kernel/scheduler.py`

```python
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
```

### 1.3 `src/gmos/kernel/budget_router.py`

```python
"""
Budget Router for GM-OS Kernel.

Manages process and layer budgets, enforces reserve law, handles lawful
internal transfers, protects survival reserves.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class ReserveTier(Enum):
    """Reserve protection tiers."""
    SURVIVAL = "survival"       # layer 1 protected
    ESSENTIAL = "essential"     # layer 2 protected  
    DISCRETIONARY = "discretionary"  # can be depleted


@dataclass
class BudgetSlice:
    """Individual budget allocation."""
    process_id: str
    layer: int
    amount: float
    reserve: float
    tier: ReserveTier = ReserveTier.DISCRETIONARY
    
    @property
    def available(self) -> float:
        """Amount available to spend."""
        return max(0, self.amount - self.reserve)


class BudgetRouter:
    """
    Budget routing and reserve enforcement.
    
    Core laws enforced:
    - no internal minting
    - reserve floor preservation
    - protected layer-1 reserve
    - optional emergency override hook
    """
    
    def __init__(self, global_reserve: float = 0.0):
        self._global_budget: float = 0.0
        self._global_reserve: float = global_reserve
        self._process_budgets: Dict[str, BudgetSlice] = {}
        self._layer_budgets: Dict[str, Dict[int, BudgetSlice]] = {}
    
    def register_process_budget(
        self, 
        process_id: str, 
        layer: int,
        amount: float,
        reserve: float = 0.0,
        tier: ReserveTier = ReserveTier.DISCRETIONARY
    ) -> BudgetSlice:
        """Register budget for a process layer."""
        budget = BudgetSlice(
            process_id=process_id,
            layer=layer,
            amount=amount,
            reserve=reserve,
            tier=tier
        )
        self._process_budgets[process_id] = budget
        
        if process_id not in self._layer_budgets:
            self._layer_budgets[process_id] = {}
        self._layer_budgets[process_id][layer] = budget
        
        return budget
    
    def register_layer_budget(
        self,
        process_id: str,
        layer: int,
        amount: float,
        reserve: float
    ) -> BudgetSlice:
        """Register budget for a specific layer."""
        tier = ReserveTier.SURVIVAL if layer == 1 else ReserveTier.ESSENTIAL
        return self.register_process_budget(process_id, layer, amount, reserve, tier)
    
    def can_spend(self, process_id: str, layer: int, amount: float) -> bool:
        """Check if spend is feasible."""
        budget = self._get_budget(process_id, layer)
        if not budget:
            return False
        return budget.amount - amount >= budget.reserve
    
    def apply_spend(self, process_id: str, layer: int, amount: float) -> bool:
        """Apply a spend if legal."""
        if not self.can_spend(process_id, layer, amount):
            return False
        
        budget = self._get_budget(process_id, layer)
        budget.amount -= amount
        return True
    
    def route_budget(
        self, 
        from_process: str, 
        to_process: str, 
        layer: int, 
        amount: float
    ) -> bool:
        """Route budget between processes (parent delegation)."""
        if not self.can_spend(from_process, layer, amount):
            return False
        
        self.apply_spend(from_process, layer, amount)
        
        if to_process in self._process_budgets:
            self._process_budgets[to_process].amount += amount
        else:
            self.register_process_budget(to_process, layer, amount, 0.0)
        
        return True
    
    def reserve_ok(self, process_id: str, layer: int) -> bool:
        """Check if reserve is preserved."""
        budget = self._get_budget(process_id, layer)
        if not budget:
            return False
        return budget.amount >= budget.reserve
    
    def get_budget(self, process_id: str, layer: Optional[int] = None) -> Optional[float]:
        """Get current budget for process/layer."""
        if layer is not None:
            budget = self._get_budget(process_id, layer)
            return budget.amount if budget else None
        process_budget = self._process_budgets.get(process_id)
        return process_budget.amount if process_budget else None
    
    def get_reserve(self, process_id: str, layer: int) -> Optional[float]:
        """Get reserve amount for process/layer."""
        budget = self._get_budget(process_id, layer)
        return budget.reserve if budget else None
    
    def _get_budget(self, process_id: str, layer: int) -> Optional[BudgetSlice]:
        """Get budget slice for process and layer."""
        if process_id in self._layer_budgets:
            return self._layer_budgets[process_id].get(layer)
        return self._process_budgets.get(process_id)
```

### 1.4 `src/gmos/kernel/receipt_engine.py`

```python
"""
Receipt Engine for GM-OS Kernel.

Builds canonical receipts for kernel events, serializes receipt payloads,
interfaces with hash chain.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import uuid
import time


class ReceiptType(Enum):
    """Types of kernel receipts."""
    TRANSITION = "transition"
    BUDGET = "budget"
    HALT = "halt"
    TORPOR = "torpor"
    WAKE = "wake"
    ROUTING = "routing"


@dataclass
class KernelReceipt:
    """Canonical receipt for kernel events."""
    receipt_id: str
    receipt_type: ReceiptType
    process_id: str
    step_index: int
    state_hash_prev: str
    state_hash_next: str
    budget_prev: float
    budget_next: float
    decision_code: int  # 1=accepted, 0=rejected, -1=halt
    chain_digest_prev: str
    chain_digest_next: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "receipt_id": self.receipt_id,
            "receipt_type": self.receipt_type.value,
            "process_id": self.process_id,
            "step_index": self.step_index,
            "state_hash_prev": self.state_hash_prev,
            "state_hash_next": self.state_hash_next,
            "budget_prev": self.budget_prev,
            "budget_next": self.budget_next,
            "decision_code": self.decision_code,
            "chain_digest_prev": self.chain_digest_prev,
            "chain_digest_next": self.chain_digest_next,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class ReceiptEngine:
    """
    Generates canonical receipts for kernel events.
    
    Receipt fields:
    - receipt_id
    - receipt_type
    - process_id
    - step_index
    - state_hash_prev
    - state_hash_next
    - budget_prev
    - budget_next
    - decision_code
    - chain_digest_prev
    - chain_digest_next
    - metadata
    """
    
    def __init__(self, hash_chain=None):
        self._hash_chain = hash_chain
    
    def make_transition_receipt(
        self,
        process_id: str,
        step_index: int,
        state_hash_prev: str,
        state_hash_next: str,
        budget_prev: float,
        budget_next: float,
        decision_code: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KernelReceipt:
        """Create a state transition receipt."""
        chain_prev = self._chain_digest() if self._hash_chain else "genesis"
        
        receipt = KernelReceipt(
            receipt_id=str(uuid.uuid4())[:8],
            receipt_type=ReceiptType.TRANSITION,
            process_id=process_id,
            step_index=step_index,
            state_hash_prev=state_hash_prev,
            state_hash_next=state_hash_next,
            budget_prev=budget_prev,
            budget_next=budget_next,
            decision_code=decision_code,
            chain_digest_prev=chain_prev,
            chain_digest_next="",  # Will be updated after chain append
            metadata=metadata or {}
        )
        
        if self._hash_chain:
            receipt.chain_digest_next = self._hash_chain.append(receipt)
        
        return receipt
    
    def make_budget_receipt(
        self,
        process_id: str,
        budget_prev: float,
        budget_next: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KernelReceipt:
        """Create a budget change receipt."""
        chain_prev = self._chain_digest() if self._hash_chain else "genesis"
        
        receipt = KernelReceipt(
            receipt_id=str(uuid.uuid4())[:8],
            receipt_type=ReceiptType.BUDGET,
            process_id=process_id,
            step_index=0,
            state_hash_prev="",
            state_hash_next="",
            budget_prev=budget_prev,
            budget_next=budget_next,
            decision_code=1,
            chain_digest_prev=chain_prev,
            chain_digest_next="",
            metadata=metadata or {}
        )
        
        if self._hash_chain:
            receipt.chain_digest_next = self._hash_chain.append(receipt)
        
        return receipt
    
    def make_halt_receipt(
        self,
        process_id: str,
        step_index: int,
        state_hash: str,
        budget: float
    ) -> KernelReceipt:
        """Create a halt receipt (no lawful move)."""
        return self.make_transition_receipt(
            process_id=process_id,
            step_index=step_index,
            state_hash_prev=state_hash,
            state_hash_next=state_hash,
            budget_prev=budget,
            budget_next=budget,
            decision_code=-1,
            metadata={"reason": "no_lawful_move"}
        )
    
    def make_torpor_receipt(
        self,
        process_id: str,
        step_index: int,
        state_hash: str,
        budget: float
    ) -> KernelReceipt:
        """Create a torpor receipt (budget depleted)."""
        return self.make_transition_receipt(
            process_id=process_id,
            step_index=step_index,
            state_hash_prev=state_hash,
            state_hash_next=state_hash,
            budget_prev=budget,
            budget_next=0.0,
            decision_code=-1,
            metadata={"reason": "budget_depleted"}
        )
    
    def make_wake_receipt(
        self,
        process_id: str,
        state_hash: str,
        budget: float
    ) -> KernelReceipt:
        """Create a wake receipt (replenishment received)."""
        return self.make_transition_receipt(
            process_id=process_id,
            step_index=0,
            state_hash_prev=state_hash,
            state_hash_next=state_hash,
            budget_prev=0.0,
            budget_next=budget,
            decision_code=1,
            metadata={"reason": "replenishment"}
        )
    
    def canonical_payload(self, receipt: KernelReceipt) -> bytes:
        """Serialize receipt to canonical bytes."""
        import json
        return json.dumps(receipt.to_dict(), sort_keys=True).encode()
    
    def _chain_digest(self) -> str:
        """Get current chain digest."""
        if self._hash_chain:
            return self._hash_chain.current_digest
        return "genesis"
```

### 1.5 `src/gmos/kernel/macro_verifier.py`

```python
"""
Macro Verifier for GM-OS Kernel.

Verifies slabs / macro summaries instead of every microstep individually,
supports oplax roll-up verification.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import hashlib
import json


@dataclass
class SlabReceipt:
    """Receipt summarizing a batch of micro-receipts."""
    slab_id: str
    start_step: int
    end_step: int
    process_id: str
    receipts: List[Dict[str, Any]] = field(default_factory=list)
    total_spend: float = 0.0
    total_defect: float = 0.0
    slab_hash: str = ""
    
    def __post_init__(self):
        if not self.slab_hash:
            self.slab_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash of slab contents."""
        content = {
            "slab_id": self.slab_id,
            "start_step": self.start_step,
            "end_step": self.end_step,
            "process_id": self.process_id,
            "total_spend": self.total_spend,
            "total_defect": self.total_defect,
            "receipts": self.receipts
        }
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]


class MacroVerifier:
    """
    Verifies macro slabs and oplax roll-ups.
    
    Key law enforced:
    Spend(Slab) <= sum(Spend(receipt_k))
    
    This ensures subadditivity of verification cost.
    """
    
    def __init__(self):
        self._verified_slabs: Dict[str, SlabReceipt] = {}
    
    def build_slab(
        self,
        slab_id: str,
        process_id: str,
        start_step: int,
        end_step: int,
        micro_receipts: List[Dict[str, Any]]
    ) -> SlabReceipt:
        """Build a slab receipt from micro-receipts."""
        total_spend = sum(r.get("spend", 0.0) for r in micro_receipts)
        total_defect = sum(r.get("defect", 0.0) for r in micro_receipts)
        
        slab = SlabReceipt(
            slab_id=slab_id,
            start_step=start_step,
            end_step=end_step,
            process_id=process_id,
            receipts=micro_receipts,
            total_spend=total_spend,
            total_defect=total_defect
        )
        
        return slab
    
    def verify_slab(self, slab: SlabReceipt) -> bool:
        """Verify a slab receipt."""
        # Check all micro receipts are present
        if len(slab.receipts) != (slab.end_step - slab.start_step + 1):
            return False
        
        # Verify hash
        expected_hash = slab._compute_hash()
        if slab.slab_hash != expected_hash:
            return False
        
        # Verify oplax bound
        if not self.verify_oplax_bound(slab):
            return False
        
        self._verified_slabs[slab.slab_id] = slab
        return True
    
    def summarize_spend(self, slab: SlabReceipt) -> float:
        """Get total spend for slab."""
        return slab.total_spend
    
    def summarize_defect(self, slab: SlabReceipt) -> float:
        """Get total defect for slab."""
        return slab.total_defect
    
    def verify_oplax_bound(self, slab: SlabReceipt) -> bool:
        """
        Verify subadditive spend law:
        Spend(Slab) <= sum(Spend(receipt_k))
        
        In practice, this means slab totals should equal or be less than
        the sum of individual receipt values.
        """
        # Compute from individual receipts
        computed_spend = sum(r.get("spend", 0.0) for r in slab.receipts)
        computed_defect = sum(r.get("defect", 0.0) for r in slab.receipts)
        
        # Slab should not claim more than sum of parts
        return (
            slab.total_spend <= computed_spend + 1e-6 and
            slab.total_defect <= computed_defect + 1e-6
        )
```

### 1.6 `src/gmos/kernel/process_table.py`

```python
"""
Process Table for GM-OS Kernel.

Maintains registry of all hosted processes, tracks modes, priorities,
memory scopes, and verifier handles.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
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
```

---

## Phase 2: MEMORY LAYER - relevance.py (NEW implementation)

### 2.1 `src/gmos/memory/relevance.py`

```python
"""
Memory Relevance Engine for GM-OS Memory Fabric.

Decides which memories are worth retrieving under budget constraints.
Single source of truth for retrieval ranking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class RelevanceScore:
    """Score for a memory episode."""
    episode_id: str
    semantic_score: float = 0.0
    context_score: float = 0.0
    recency_score: float = 0.0
    anchor_score: float = 0.0
    validation_score: float = 0.0
    total_score: float = 0.0
    cost_to_replay: float = 0.0
    
    def compute_total(
        self,
        alpha_semantic: float = 0.3,
        alpha_context: float = 0.2,
        alpha_recency: float = 0.2,
        alpha_anchor: float = 0.15,
        alpha_validation: float = 0.15
    ) -> float:
        """
        Compute weighted total score.
        
        S(q,e_i) = α_s*S_semantic + α_c*S_context + α_r*S_recency + α_a*S_anchor + α_v*S_validation
        """
        self.total_score = (
            alpha_semantic * self.semantic_score +
            alpha_context * self.context_score +
            alpha_recency * self.recency_score +
            alpha_anchor * self.anchor_score +
            alpha_validation * self.validation_score
        )
        # Subtract replay cost penalty
        self.total_score -= self.cost_to_replay
        return self.total_score


class MemoryRelevanceEngine:
    """
    Memory retrieval ranking system.
    
    Scores episodes by:
    - semantic similarity (embedding overlap)
    - context relevance (tag overlap)
    - recency (temporal decay)
    - reality anchor weight (external validation)
    - validation score (contradiction/reward signals)
    """
    
    def __init__(
        self,
        alpha_semantic: float = 0.3,
        alpha_context: float = 0.2,
        alpha_recency: float = 0.2,
        alpha_anchor: float = 0.15,
        alpha_validation: float = 0.15
    ):
        self.alpha_semantic = alpha_semantic
        self.alpha_context = alpha_context
        self.alpha_recency = alpha_recency
        self.alpha_anchor = alpha_anchor
        self.alpha_validation = alpha_validation
    
    def score_episode(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> RelevanceScore:
        """Score a single episode against a query."""
        score = RelevanceScore(episode_id=episode.get("id", ""))
        
        # Semantic similarity (embedding-based)
        score.semantic_score = self._compute_semantic(episode, query)
        
        # Context overlap (tag-based)
        score.context_score = self._compute_context(episode, query)
        
        # Recency decay
        score.recency_score = self._compute_recency(episode)
        
        # Anchor weight
        score.anchor_score = self._compute_anchor(episode)
        
        # Validation score
        score.validation_score = self._compute_validation(episode)
        
        # Cost to replay
        score.cost_to_replay = episode.get("replay_cost", 0.0)
        
        # Compute total
        score.compute_total(
            self.alpha_semantic,
            self.alpha_context,
            self.alpha_recency,
            self.alpha_anchor,
            self.alpha_validation
        )
        
        return score
    
    def rank_candidates(
        self,
        episodes: List[Dict[str, Any]],
        query: Dict[str, Any]
    ) -> List[RelevanceScore]:
        """Rank all candidate episodes."""
        scores = [self.score_episode(ep, query) for ep in episodes]
        return sorted(scores, key=lambda s: s.total_score, reverse=True)
    
    def select_top_k(
        self,
        episodes: List[Dict[str, Any]],
        query: Dict[str, Any],
        k: int,
        budget: Optional[float] = None
    ) -> List[RelevanceScore]:
        """Select top-k episodes under budget constraint."""
        ranked = self.rank_candidates(episodes, query)
        
        if budget is None:
            return ranked[:k]
        
        selected = []
        total_cost = 0.0
        for score in ranked:
            if total_cost + score.cost_to_replay <= budget:
                selected.append(score)
                total_cost += score.cost_to_replay
                if len(selected) >= k:
                    break
        
        return selected
    
    def filter_by_budget(
        self,
        episodes: List[Dict[str, Any]],
        budget: float
    ) -> List[Dict[str, Any]]:
        """Filter episodes that fit within budget."""
        affordable = []
        total_cost = 0.0
        
        for ep in episodes:
            cost = ep.get("replay_cost", 0.0)
            if total_cost + cost <= budget:
                affordable.append(ep)
                total_cost += cost
        
        return affordable
    
    def _compute_semantic(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Compute semantic similarity score."""
        # Placeholder: would use embedding similarity
        ep_emb = episode.get("embedding", [])
        query_emb = query.get("embedding", [])
        
        if not ep_emb or not query_emb:
            return 0.0
        
        # Cosine similarity
        ep_arr = np.array(ep_emb)
        query_arr = np.array(query_emb)
        
        norm_ep = np.linalg.norm(ep_arr)
        norm_query = np.linalg.norm(query_arr)
        
        if norm_ep == 0 or norm_query == 0:
            return 0.0
        
        return float(np.dot(ep_arr, query_arr) / (norm_ep * norm_query))
    
    def _compute_context(
        self,
        episode: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Compute context/tag overlap score."""
        ep_tags = set(episode.get("tags", []))
        query_tags = set(query.get("tags", []))
        
        if not ep_tags or not query_tags:
            return 0.0
        
        overlap = len(ep_tags & query_tags)
        union = len(ep_tags | query_tags)
        
        return overlap / union if union > 0 else 0.0
    
    def _compute_recency(self, episode: Dict[str, Any]) -> float:
        """Compute recency decay score."""
        import time
        timestamp = episode.get("timestamp", time.time())
        age = time.time() - timestamp
        
        # Exponential decay with half-life of 1 hour
        half_life = 3600.0
        return np.exp(-age / half_life)
    
    def _compute_anchor(self, episode: Dict[str, Any]) -> float:
        """Compute reality anchor bonus."""
        anchor_weight = episode.get("anchor_weight", 0.0)
        return float(min(1.0, anchor_weight))
    
    def _compute_validation(self, episode: Dict[str, Any]) -> float:
        """Compute validation/contradiction score."""
        # Positive for validated, negative for contradictions
        validation = episode.get("validation_score", 0.0)
        contradiction = episode.get("contradiction_count", 0)
        
        return float(validation - 0.1 * contradiction)
```

---

## Phase 3: PLACEHOLDER STUBS

### 3.1 Sensory Layer - 5 files

### `src/gmos/sensory/manifold.py`
```python
"""
Sensory Manifold for GM-OS.

Defines sensory manifold container type, holds fused external/internal/
semantic percept bundles.

TODO: Implement charts and bundles for:
- External manifold (physical perception)
- Semantic manifold (conceptual/symbolic)
- Internal manifold (interoception)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class SensoryState:
    """Container for fused sensory state."""
    external: Optional[Dict[str, Any]] = None
    semantic: Optional[Dict[str, Any]] = None
    internal: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0


# TODO: Implement manifold charts
# TODO: Implement bundle fusion
# TODO: Implement coordinate transforms
```

### `src/gmos/sensory/projection.py`
```python
"""
Projection for GM-OS Sensory Manifold.

Defines interface for projecting raw observations into manifold state.

TODO: Implement projection functions for:
- World state -> external manifold
- Internal state -> internal manifold
- Symbolic state -> semantic manifold
"""

from typing import Dict, Any


def project_world_state(world_observation: Dict[str, Any]) -> Dict[str, Any]:
    """Project raw world observation into external manifold."""
    # TODO: Implement
    return {}


def project_internal_state(internal_observation: Dict[str, Any]) -> Dict[str, Any]:
    """Project internal observation into internal manifold."""
    # TODO: Implement
    return {}
```

### `src/gmos/sensory/fusion.py`
```python
"""
Fusion for GM-OS Sensory Manifold.

Defines how multiple percept streams combine.

TODO: Implement multi-modal fusion:
- Cross-modal attention
- Temporal alignment
- Confidence weighting
"""

from typing import Dict, Any, List


def fuse_modalities(modalities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fuse multiple sensory modalities into unified state."""
    # TODO: Implement
    return {}
```

### `src/gmos/sensory/salience.py`
```python
"""
Salience for GM-OS Sensory Manifold.

Defines salience scoring interface for percept fields.

TODO: Implement salience computation:
- Bottom-up salience
- Top-down attention
- Surprise detection
"""

from typing import Dict, Any


def compute_salience(sensory_state: Dict[str, Any]) -> float:
    """Compute salience score for sensory state."""
    # TODO: Implement
    return 0.0
```

### `src/gmos/sensory/anchors.py`
```python
"""
Anchors for GM-OS Sensory Manifold.

Defines reality-anchor tagging interface for sensory inputs.

TODO: Implement:
- External event anchoring
- Anchor weight computation
- Validation linkage
"""

from typing import Dict, Any


def anchor_external_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Anchor external validated event to sensory state."""
    # TODO: Implement
    return {"anchored": False}


def anchor_weight(anchor: Dict[str, Any]) -> float:
    """Compute anchor weight (0-1)."""
    # TODO: Implement
    return 0.0
```

### 3.2 Symbolic Layer - 3 files

### `src/gmos/symbolic/glyph_space.py`
```python
"""
Glyph Space for GM-OS Symbolic Layer.

Defines symbolic glyph coordinate container.

TODO: Implement:
- GlyphCoordinate type
- GlyphState container
- Glyph embeddings
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GlyphCoordinate:
    """Symbolic glyph coordinate."""
    x: float
    y: float
    z: Optional[float] = None
    glyph_type: str = "unknown"


@dataclass
class GlyphState:
    """Container for glyph coordinates."""
    coordinates: List[GlyphCoordinate] = None
    # TODO: Add more fields
```

### `src/gmos/symbolic/semantic_manifold.py`
```python
"""
Semantic Manifold for GM-OS Symbolic Layer.

Defines semantic manifold container and relation bundles.

TODO: Implement:
- SemanticState container
- embed_symbolic_structure()
- Relation bundles
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class SemanticState:
    """Container for semantic state."""
    concepts: List[str] = None
    relations: List[Dict[str, Any]] = None


def embed_symbolic_structure(structure: Dict[str, Any]) -> List[float]:
    """Embed symbolic structure into manifold coordinates."""
    # TODO: Implement
    return []
```

### `src/gmos/symbolic/binding.py`
```python
"""
Binding for GM-OS Symbolic Layer.

Defines symbolic-to-process binding logic.

TODO: Implement:
- bind_symbol_to_state()
- bind_state_to_symbol()
- Symbol grounding
"""

from typing import Dict, Any


def bind_symbol_to_state(symbol: Any, state: Dict[str, Any]) -> Dict[str, Any]:
    """Bind symbolic structure to process state."""
    # TODO: Implement
    return {}


def bind_state_to_symbol(state: Dict[str, Any]) -> Any:
    """Extract symbolic representation from state."""
    # TODO: Implement
    return None
```

### 3.3 Agent Layer - Placeholders + gmi_agent.py

### `src/gmos/agents/planner_agent.py`
```python
"""
Planner Agent for GM-OS.

Future hosted planner process, branch-heavy reflective process type.
"""

from typing import Dict, Any, Optional


class PlannerAgent:
    """Planner agent stub."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one planning step."""
        # TODO: Implement
        return {"action": "plan", "status": "stub"}
    
    def propose_plan(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a plan to achieve goal."""
        # TODO: Implement
        return {"plan": [], "status": "stub"}
```

### `src/gmos/agents/physics_agent.py`
```python
"""
Physics Agent for GM-OS.

Future hosted physics simulation process.
"""

from typing import Dict, Any, Optional


class PhysicsAgent:
    """Physics simulation agent stub."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute physics simulation step."""
        # TODO: Implement
        return {"simulation": "stub"}
```

### `src/gmos/agents/ns_agent.py`
```python
"""
NS Agent for GM-OS.

Future NS-GMI specialized hosted process.
"""

from typing import Dict, Any, Optional


class NSAgent:
    """Navier-Stokes GMI agent stub."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute NS-GMI step."""
        # TODO: Implement
        return {"ns_gmi": "stub"}
```

### `src/gmos/agents/symbolic_agent.py`
```python
"""
Symbolic Agent for GM-OS.

Future symbolic / Noetica process.
"""

from typing import Dict, Any, Optional


class SymbolicAgent:
    """Symbolic reasoning agent stub."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute symbolic reasoning step."""
        # TODO: Implement
        return {"symbolic": "stub"}
```

### 3.4 Action Layer - 3 files

### `src/gmos/action/commitment.py`
```python
"""
Commitment for GM-OS Action Layer.

Defines external action commitment interface, kernel-facing action commit API.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ActionCommitment:
    """Committed action record."""
    action_id: str
    process_id: str
    action_type: str
    parameters: Dict[str, Any]
    budget_spent: float


def commit_action(
    process_id: str,
    action: Dict[str, Any],
    budget: float
) -> ActionCommitment:
    """Commit an action for execution."""
    # TODO: Implement
    return ActionCommitment(
        action_id="stub",
        process_id=process_id,
        action_type="stub",
        parameters=action,
        budget_spent=budget
    )
```

### `src/gmos/action/external_io.py`
```python
"""
External I/O for GM-OS Action Layer.

Defines interface for lawful world coupling, sensor/actuator bridge.
"""

from typing import Dict, Any


def read_environment(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Read from environment."""
    # TODO: Implement
    return observation


def write_environment(action: Dict[str, Any]) -> Dict[str, Any]:
    """Write action to environment."""
    # TODO: Implement
    return {"status": "executed"}
```

### `src/gmos/action/replenishment.py`
```python
"""
Replenishment for GM-OS Action Layer.

Defines interface for externally verified budget replenishment.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ReplenishmentReceipt:
    """Verified replenishment record."""
    receipt_id: str
    amount: float
    source: str
    verified: bool


def compute_verified_replenishment(
    external_validation: Dict[str, Any]
) -> ReplenishmentReceipt:
    """Compute externally verified replenishment amount."""
    # TODO: Implement
    return ReplenishmentReceipt(
        receipt_id="stub",
        amount=0.0,
        source="external",
        verified=False
    )
```

---

## Summary: File Creation Order

### Priority 1: Kernel Layer (NEW logic - 6 files)
1. `state_host.py`
2. `scheduler.py`
3. `budget_router.py`
4. `receipt_engine.py`
5. `macro_verifier.py`
6. `process_table.py`

### Priority 2: Kernel Layer (COPY from ledger/)
7. `hash_chain.py` (copy)
8. `receipt.py` (copy)
9. `oplax_verifier.py` → `verifier.py` (copy + rename)

### Priority 3: Memory Layer
10. COPY all memory files
11. `relevance.py` (NEW)

### Priority 4: Placeholders
12-14. Sensory layer (5 files)
15-17. Symbolic layer (3 files)
18-21. Agent placeholders (4 files)
22-24. Action layer (3 files)
