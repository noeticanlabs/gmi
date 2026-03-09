"""
Experimental Agents and Components

This module contains experimental agent implementations that are not yet
part of the canonical GM-OS specification. These are stubs or partial
implementations for future research directions.

Currently included:
- agents/: Experimental agent implementations

For canonical GMI agent, use gmos.agents.gmi.
"""

# Re-export stub agents for backwards compatibility
# These are in experimental/agents/ but available here for import compatibility
try:
    from gmos.agents.ns_agent import NSAgent
    from gmos.agents.physics_agent import PhysicsAgent
    from gmos.agents.planner_agent import PlannerAgent
    from gmos.agents.symbolic_agent import SymbolicAgent
    
    __all__ = [
        "NSAgent",
        "PhysicsAgent", 
        "PlannerAgent",
        "SymbolicAgent",
    ]
except ImportError:
    __all__ = []
