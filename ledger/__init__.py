"""
Ledger Module for the GMI Universal Cognition Engine.

Provides:
- Receipt: Immutable proof artifacts with hash chain fields
- OplaxVerifier: Thermodynamic constraint verifier
- HashChainLedger: Cryptographic execution chain
- LedgerReplay: Deterministic replay for offline audit
"""

from ledger.receipt import (
    Receipt,
    create_receipt_from_verifier
)

from ledger.oplax_verifier import OplaxVerifier

from ledger.hash_chain import (
    HashChainLedger,
    ChainDigest,
    SlabSummary,
    DecisionCode,
    get_global_ledger,
    set_global_ledger
)

from ledger.replay import (
    LedgerReplay,
    ReplayResult,
    replay_from_files,
    verify_ledger_chain
)


__all__ = [
    # Receipt
    'Receipt',
    'create_receipt_from_verifier',
    
    # Verifier
    'OplaxVerifier',
    
    # Hash Chain
    'HashChainLedger',
    'ChainDigest',
    'SlabSummary',
    'DecisionCode',
    'get_global_ledger',
    'set_global_ledger',
    
    # Replay
    'LedgerReplay',
    'ReplayResult',
    'replay_from_files',
    'verify_ledger_chain',
]
