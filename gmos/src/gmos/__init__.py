"""
GM-OS: Glyph-Manifold Operating System

Governed Manifold Operating Substrate for Reflective, Ledger-Bound Intelligence
"""

__version__ = "0.1.0"

# Core modules
from gmos.kernel import state_host, scheduler, budget_router, receipt_engine, macro_verifier, process_table
from gmos.kernel import hash_chain, receipt, verifier
from gmos.memory import relevance

__all__ = [
    # Version
    "__version__",
    # Kernel
    "state_host",
    "scheduler", 
    "budget_router",
    "receipt_engine",
    "macro_verifier",
    "process_table",
    "hash_chain",
    "receipt",
    "verifier",
    # Memory
    "relevance",
]
