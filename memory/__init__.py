"""
Memory Module for the GMI Universal Cognition Engine.

This module implements the complete reflective memory system:

Memory Layers:
- C (Passive Structural Memory): Curvature from core/memory.py
- E (Episodic Archive): Explicit readable memory
- W (Reconstructive Workspace): Volatile phantom states
- Ω (Ledger Anchor): Memory operations tied to ledger

Memory Operators:
- O_W (Write): Encode state into episode
- O_R (Read): Retrieve episodes
- O_P (Replay): Reconstruct phantom states
- O_C (Compare): Compare current with memory
- O_K (Prune): Consolidate archive

Key Classes:
- GMIPotential: Canonical energy law
- EpisodicArchive: Episode storage
- Workspace: Phantom state management
- MemoryOperators: Read/write/replay/compare/prune
- MemoryBudgetLaw: Operation pricing
- RealityAnchor: Externally grounded memory

The memory system obeys the anti-raccoon law:
- No free recall
- No free imagination  
- No self-issued reward
- All operations priced in budget
"""

from memory.episode import (
    Episode,
    EpisodeSummary,
    EpisodeRef,
    create_episode,
    generate_episode_id
)

from memory.archive import (
    EpisodicArchive,
    get_global_archive,
    set_global_archive
)

from memory.workspace import (
    PhantomState,
    ComparisonResult,
    BranchSeed,
    WorkspaceState,
    Workspace
)

from memory.budget_costs import (
    MemoryBudgetLaw,
    get_budget_law,
    set_budget_law
)

from memory.reality_anchors import (
    RealityAnchor,
    RealityAnchorManager,
    get_anchor_manager,
    set_anchor_manager
)

from memory.memory_receipts import (
    MemoryReceipt,
    MemoryReceiptLedger,
    get_memory_ledger,
    set_memory_ledger
)

from memory.query_engine import (
    MemoryQuery,
    QueryEngine
)

from memory.replay_engine import ReplayEngine

from memory.comparator import (
    StateComparison,
    Comparator
)

from memory.consolidation import (
    ConsolidationReport,
    SlabReceipt,
    Consolidator,
    get_consolidator
)

from memory.operators import (
    MemoryOperationResult,
    WriteOperator,
    ReadOperator,
    ReplayOperator,
    CompareOperator,
    PruneOperator,
    MemoryOperatorFactory
)


__all__ = [
    # Episode
    'Episode',
    'EpisodeSummary', 
    'EpisodeRef',
    'create_episode',
    'generate_episode_id',
    
    # Archive
    'EpisodicArchive',
    'get_global_archive',
    'set_global_archive',
    
    # Workspace
    'PhantomState',
    'ComparisonResult',
    'BranchSeed',
    'WorkspaceState',
    'Workspace',
    
    # Budget
    'MemoryBudgetLaw',
    'get_budget_law',
    'set_budget_law',
    
    # Reality Anchors
    'RealityAnchor',
    'RealityAnchorManager',
    'get_anchor_manager',
    'set_anchor_manager',
    
    # Memory Receipts
    'MemoryReceipt',
    'MemoryReceiptLedger',
    'get_memory_ledger',
    'set_memory_ledger',
    
    # Query
    'MemoryQuery',
    'QueryEngine',
    
    # Replay
    'ReplayEngine',
    
    # Comparator
    'StateComparison',
    'Comparator',
    
    # Consolidation
    'ConsolidationReport',
    'SlabReceipt',
    'Consolidator',
    'get_consolidator',
    
    # Operators
    'MemoryOperationResult',
    'WriteOperator',
    'ReadOperator',
    'ReplayOperator',
    'CompareOperator',
    'PruneOperator',
    'MemoryOperatorFactory',
]
