"""
GMI Agent Package for GM-OS.

This package contains the canonical GMI agent implementation.
"""

# Re-export the main agent class
from gmos.agents.gmi.gmi_agent import (
    state,
    potential,
    constraints,
    affective_state,
    affective_budget,
    threat_modulation,
    policy_selection,
    evolution_loop,
    execution_loop,
    semantic_loop,
    hosted_agent,
    tension_law,
)

# For backwards compatibility, also create GMIAgent class wrapper
class GMIAgent:
    """GMI Agent - wrapper class for backward compatibility."""
    
    def __init__(self, budget: float = 100.0, **kwargs):
        self.budget = budget
        self.state_module = state
        self.potential_module = potential
        self.constraints_module = constraints
        
    def __getattr__(self, name):
        # Delegate to submodules
        if name in ('state', 'potential', 'constraints', 'affective_state', 
                    'affective_budget', 'threat_modulation', 'policy_selection',
                    'evolution_loop', 'execution_loop', 'semantic_loop', 
                    'hosted_agent', 'tension_law'):
            return globals()[name]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")


__all__ = [
    'GMIAgent',
    'state',
    'potential',
    'constraints',
    'affective_state',
    'affective_budget',
    'threat_modulation',
    'policy_selection',
    'evolution_loop',
    'execution_loop',
    'semantic_loop',
    'hosted_agent',
    'tension_law',
]
