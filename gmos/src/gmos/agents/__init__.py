"""
GM-OS Agents Package

This package contains agent implementations:
- gmi: Canonical GMI agent (per GMI Canon Spec)
- experimental: Experimental agents (stubs, not yet integrated)

For new development, use gmi.agents.gmi.
"""

from gmos.agents.gmi import GMIAgent

# Re-export experimental agents for backwards compatibility
# These are stubs that will be moved to experimental/ when implemented
try:
    from gmos.agents.ns_agent import NSAgent
    from gmos.agents.physics_agent import PhysicsAgent
    from gmos.agents.planner_agent import PlannerAgent
    from gmos.agents.symbolic_agent import SymbolicAgent
    
    __all__ = [
        "GMIAgent",
        "NSAgent",
        "PhysicsAgent",
        "PlannerAgent",
        "SymbolicAgent",
    ]
except ImportError:
    __all__ = ["GMIAgent"]
