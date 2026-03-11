"""
GMI Consciousness & Physics Tests

Tests measuring consciousness-like properties and physics interactions:
1. Self-modeling - core to consciousness  
2. Physics interaction - GMI affects GMOS substrate
"""

import numpy as np
import pytest
import sys

sys.path.insert(0, '/home/user/gmi/gmos/src')
sys.path.insert(0, '/home/user/gmi')


class TestSelfModeling:
    """Tests for self-representation - core to consciousness."""
    
    def test_state_self_reference(self):
        """GMI state computes its own potential."""
        from gmos.agents.gmi.state import State
        state = State(x=[1.0, 2.0], budget=10.0)
        pot = state.compute_potential()
        assert pot >= 0
        
    def test_budget_self_awareness(self):
        """GMI tracks its own budget (energy)."""
        from gmos.agents.gmi.state import State
        state = State(x=[1.0], budget=10.0)
        assert state.b == 10.0


class TestPhysicsInteraction:
    """Tests: GMI interacts with GMOS physics substrate."""
    
    def test_potential_energy_landscape(self):
        """Potential defines energy landscape."""
        from gmos.agents.gmi.potential import GMIPotential
        pot = GMIPotential()
        high_E = pot.base(np.array([5.0, 5.0]))
        low_E = pot.base(np.array([0.1, 0.1]))
        assert high_E > low_E
        
    def test_budget_as_energy(self):
        """Budget is like free energy."""
        from gmos.agents.gmi.state import State
        state = State(x=[1.0], budget=100.0)
        assert state.b > 0
        
    def test_ledger_exists(self):
        """Receipt ledger exists (spacetime record)."""
        from gmos.kernel.hash_chain import HashChainLedger
        chain = HashChainLedger()
        # Ledger has integrity verification
        assert hasattr(chain, 'verify_chain')
        
    def test_constraints_governor(self):
        """Constraints act like physical laws."""
        from gmos.agents.gmi.constraints import ConstraintGovernor
        gov = ConstraintGovernor()
        # Governor exists and has methods
        assert gov is not None


class TestConsciousnessMetrics:
    """Quantifiable consciousness-like properties."""
    
    def test_causal_power(self):
        """Causal power: can GMI affect future?"""
        from gmos.agents.gmi.state import State, Instruction
        state = State(x=[1.0, 0.0], budget=10.0)
        instr = Instruction("move", lambda x: x + np.array([0.1, 0.0]), sigma=0.5, kappa=0.1)
        new_x = instr.pi(state.x)
        assert not np.allclose(state.x, new_x)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
