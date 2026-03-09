"""
GM-OS: Glyph-Manifold Operating System

Governed Manifold Operating Substrate for Reflective, Ledger-Bound Intelligence
"""

__version__ = "0.1.0"

# Use lazy imports to avoid circular import issues
def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    
    # Kernel modules
    if name == "state_host":
        from gmos.kernel import state_host
        return state_host
    elif name == "scheduler":
        from gmos.kernel import scheduler
        return scheduler
    elif name == "budget_router":
        from gmos.kernel import budget_router
        return budget_router
    elif name == "receipt_engine":
        from gmos.kernel import receipt_engine
        return receipt_engine
    elif name == "macro_verifier":
        from gmos.kernel import macro_verifier
        return macro_verifier
    elif name == "process_table":
        from gmos.kernel import process_table
        return process_table
    elif name == "hash_chain":
        from gmos.kernel import hash_chain
        return hash_chain
    elif name == "receipt":
        from gmos.kernel import receipt
        return receipt
    elif name == "verifier":
        from gmos.kernel import verifier
        return verifier
    
    # Memory modules
    elif name == "relevance":
        from gmos.memory import relevance
        return relevance
    elif name == "memory_connector":
        from gmos.memory import memory_connector
        return memory_connector
    
    # Agent modules
    elif name == "hosted_agent":
        from gmos.agents.gmi import hosted_agent
        return hosted_agent
    
    # Sensory modules
    elif name == "sensory_connector":
        from gmos.sensory import sensory_connector
        return sensory_connector
    
    # Symbolic modules
    elif name == "symbolic_connector":
        from gmos.symbolic import symbolic_connector
        return symbolic_connector
    
    raise AttributeError(f"module 'gmos' has no attribute '{name}'")


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
