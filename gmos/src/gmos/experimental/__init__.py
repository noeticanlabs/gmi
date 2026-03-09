"""
Experimental Agents

This module contains experimental agent implementations that are not yet
part of the canonical GM-OS specification. These are stubs or partial
implementations for future research directions.

Currently included:
- NSAgent: Navier-Stokes GMI agent (stub)
- PhysicsAgent: Physics-based agent (stub)
- PlannerAgent: Planning agent (stub)
- SymbolicAgent: Symbolic reasoning agent (stub)

These agents are not yet integrated with the canonical GMI architecture.
"""

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
