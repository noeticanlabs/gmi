"""
GM-OS Agents Package

This package contains agent implementations:
- gmi: Canonical GMI agent (per GMI Canon Spec)
- experimental: Experimental agents (stubs, not yet integrated)

⚠️  WARNING: Stub agents (NSAgent, PhysicsAgent, PlannerAgent, SymbolicAgent)
    have been moved to gmos.experimental.agents. They are NOT canonical
    and should NOT be used in production.

For canonical production use, import from gmos.agents.gmi only.
"""

from gmos.agents.gmi import GMIAgent

# Import canonical GMI agent only - stubs moved to experimental
__all__ = ["GMIAgent"]

# DEPRECATED: The following stub agents have been moved to gmos.experimental.agents
# They remain here only for backwards compatibility but are deprecated.
# Import from gmos.experimental.agents instead:
#
#   from gmos.experimental.agents import NSAgent, PhysicsAgent, PlannerAgent, SymbolicAgent
#
# Or import individually:
#
#   from gmos.experimental.agents.ns_agent import NSAgent
#   from gmos.experimental.agents.physics_agent import PhysicsAgent
#   from gmos.experimental.agents.planner_agent import PlannerAgent
#   from gmos.experimental.agents.symbolic_agent import SymbolicAgent
import warnings

def __getattr__(name):
    if name in ("NSAgent", "PhysicsAgent", "PlannerAgent", "SymbolicAgent"):
        warnings.warn(
            f"{name} has been moved to gmos.experimental.agents. "
            f"It is NOT canonical and should NOT be used in production. "
            f"Import from gmos.experimental.agents instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Lazy import from experimental
        if name == "NSAgent":
            from gmos.experimental.agents.ns_agent import NSAgent
            return NSAgent
        elif name == "PhysicsAgent":
            from gmos.experimental.agents.physics_agent import PhysicsAgent
            return PhysicsAgent
        elif name == "PlannerAgent":
            from gmos.experimental.agents.planner_agent import PlannerAgent
            return PlannerAgent
        elif name == "SymbolicAgent":
            from gmos.experimental.agents.symbolic_agent import SymbolicAgent
            return SymbolicAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
