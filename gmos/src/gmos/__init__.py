"""
GM-OS: Glyph-Manifold Operating System

Governed Manifold Operating Substrate for Reflective, Ledger-Bound Intelligence
"""

__version__ = "0.1.0"

# Core modules
from gmos.kernel import state_host, scheduler, budget_router, receipt_engine, macro_verifier, process_table
from gmos.kernel import hash_chain, receipt, verifier
from gmos.memory import relevance, memory_connector
from gmos.agents.gmi import hosted_agent
from gmos.sensory import sensory_connector
from gmos.symbolic import symbolic_connector

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
    "memory_connector",
    # Agents
    "hosted_agent",
    # Sensory
    "sensory_connector",
    # Symbolic
    "symbolic_connector",
]
