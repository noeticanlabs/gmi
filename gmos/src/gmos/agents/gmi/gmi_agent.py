"""
GMI Agent for GM-OS.

This module provides access to the migrated GMI agent components:
- state: State, CognitiveState, Proposal classes
- potential: GMIPotential for gradient dynamics
- constraints: ConstraintSet, ConstraintGovernor for projection
- affective_state: AffectiveCognitiveState for emotional modeling
- affective_budget: AffectiveBudgetManager for budget handling
- threat_modulation: ThreatModulator for threat response
- policy_selection: PolicySelector for branch exploration
- evolution_loop: EvolutionLoop for policy evolution
- execution_loop: ExecutionLoop for action execution
- semantic_loop: SemanticLoop for semantic processing

Usage:
    from gmos.agents.gmi import gmi_agent
    
    # Access the modules directly
    state_module = gmi_agent.state
    potential_module = gmi_agent.potential
    # etc.
    
    # Or create a simple wrapper
    class MyAgent:
        def __init__(self):
            self.state = gmi_agent.state.State(...)
"""

# Re-export all migrated modules for convenience
from gmos.agents.gmi import state
from gmos.agents.gmi import potential
from gmos.agents.gmi import constraints
from gmos.agents.gmi import affective_state
from gmos.agents.gmi import affective_budget
from gmos.agents.gmi import threat_modulation
from gmos.agents.gmi import policy_selection
from gmos.agents.gmi import evolution_loop
from gmos.agents.gmi import execution_loop
from gmos.agents.gmi import semantic_loop
from gmos.agents.gmi import hosted_agent

# Expose module references
__all__ = [
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
]
