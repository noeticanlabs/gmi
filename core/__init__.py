"""
Core Module for the GMI Universal Cognition Engine.

Provides:
- State, CognitiveState: State representations
- GMIPotential: Canonical energy law
- Instruction, CompositeInstruction: Transition operators
"""

from core.state import (
    State,
    CognitiveState,
    Proposal,
    Instruction,
    CompositeInstruction,
    V_PL,
    create_potential
)

from core.potential import (
    GMIPotential,
    create_potential as create_gmi_potential
)

# Re-export for convenience
__all__ = [
    'State',
    'CognitiveState',
    'Proposal',
    'Instruction', 
    'CompositeInstruction',
    'V_PL',
    'GMIPotential',
    'create_potential',
    'create_gmi_potential',
]
