"""
GM-OS Kernel Module.

Provides operating substrate including:
- State hosting
- Scheduling
- Budget routing
- Receipt generation
- Macro verification
- Process management
- Full substrate state (per Canon Spec §3.1)
- Continuous dynamics (per Canon Spec §17)
- Formal theorems (per Canon Spec §24)
"""

from gmos.kernel.state_host import StateHost, HostedState, ProcessStateFlag
from gmos.kernel.scheduler import KernelScheduler, ScheduleMode, ScheduledProcess
from gmos.kernel.budget_router import BudgetRouter, BudgetSlice, ReserveTier
from gmos.kernel.receipt_engine import ReceiptEngine, KernelReceipt, ReceiptType
from gmos.kernel.macro_verifier import MacroVerifier, SlabReceipt
from gmos.kernel.process_table import ProcessTable, ProcessRecord, ProcessType, ProcessMode
from gmos.kernel import theorems
from gmos.kernel.theorems import (
    TheoremResult,
    theorem_forward_invariance,
    theorem_kernel_monopoly,
    theorem_budget_reserve_preservation,
    theorem_anchor_dominance,
    theorem_memory_loop_finiteness,
    theorem_discrete_soundness,
    theorem_chain_closure,
    theorem_deterministic_consensus,
    GMOSTheorems,
)
from gmos.kernel.substrate_state import (
    FullSubstrateState,
    OperationalMode,
    ExternalInterfaceState,
    HostedProcessState,
    KernelControlState,
    LedgerState,
    create_initial_state,
    compute_chain_digest,
    GMOSState,
)
from gmos.kernel.continuous_dynamics import (
    ProjectedDynamicalSystem,
    FreeDriftFunction,
    AdmissibleSet,
    AbsorbingBoundary,
    DriftType,
    DriftComponent,
    create_projected_dynamics,
    create_absorbing_boundary,
)
from gmos.kernel.reject_codes import (
    RejectCode,
    get_reject_description,
    is_recoverable,
    is_fatal,
)
from gmos.kernel.gmi_receipts import (
    GMIReceipt,
    GMIReceiptType,
    InferReceipt,
    RetrieveReceipt,
    RepairReceipt,
    BranchReceipt,
    PlanReceipt,
    ActPrepareReceipt,
    create_receipt,
    validate_receipt,
)
from gmos.kernel.hash_chain import (
    HashChainLedger,
    ChainDigest,
    get_global_ledger,
    set_global_ledger,
)
from gmos.kernel.receipt import Receipt
from gmos.kernel.verifier import OplaxVerifier

__all__ = [
    # State hosting
    "StateHost",
    "HostedState", 
    "ProcessStateFlag",
    # Scheduling
    "KernelScheduler",
    "ScheduleMode",
    "ScheduledProcess",
    # Budget routing
    "BudgetRouter",
    "BudgetSlice",
    "ReserveTier",
    # Receipt generation
    "ReceiptEngine",
    "KernelReceipt",
    "ReceiptType",
    # Verification
    "MacroVerifier",
    "SlabReceipt",
    # Process management
    "ProcessTable",
    "ProcessRecord",
    "ProcessType",
    "ProcessMode",
    # Full substrate state (Canon Spec §3.1)
    "FullSubstrateState",
    "OperationalMode",
    "ExternalInterfaceState",
    "HostedProcessState",
    "KernelControlState",
    "LedgerState",
    "create_initial_state",
    "compute_chain_digest",
    "GMOSState",
    # Continuous dynamics (Canon Spec §17)
    "ProjectedDynamicalSystem",
    "FreeDriftFunction",
    "AdmissibleSet",
    "AbsorbingBoundary",
    "DriftType",
    "DriftComponent",
    "create_projected_dynamics",
    "create_absorbing_boundary",
    # Formal theorems (Canon Spec §24)
    "theorems",
    "TheoremResult",
    "theorem_forward_invariance",
    "theorem_kernel_monopoly",
    "theorem_budget_reserve_preservation",
    "theorem_anchor_dominance",
    "theorem_memory_loop_finiteness",
    "theorem_discrete_soundness",
    "theorem_chain_closure",
    "theorem_deterministic_consensus",
    "GMOSTheorems",
    # Reject codes
    "RejectCode",
    "get_reject_description",
    "is_recoverable",
    "is_fatal",
    # GMI Receipt schemas
    "GMIReceipt",
    "GMIReceiptType",
    "InferReceipt",
    "RetrieveReceipt",
    "RepairReceipt",
    "BranchReceipt",
    "PlanReceipt",
    "ActPrepareReceipt",
    "create_receipt",
    "validate_receipt",
    # Hash chain
    "HashChainLedger",
    "ChainDigest",
    "get_global_ledger",
    "set_global_ledger",
    # Receipt
    "Receipt",
    # Verifier
    "OplaxVerifier",
]
