"""
Core Modules Test Suite

Comprehensive tests for:
- core/state.py: State, Instruction, Proposal
- core/potential.py: GMIPotential, potential functions
"""

import numpy as np
import pytest
import sys
sys.path.insert(0, '/home/user/gmi')

from core.state import State, Instruction, Proposal, V_PL
from core.potential import GMIPotential, create_potential


class TestState:
    """Tests for core/state.py State class."""
    
    def test_state_creation(self):
        """Test State object creation."""
        x = [1.0, 2.0, 3.0]  # list, not numpy array
        b = 10.0
        state = State(x, b)
        
        assert np.allclose(state.x, x)
        assert state.b == b
    
    def test_state_budget_attribute(self):
        """Test budget is stored in b attribute."""
        state = State([1.0], 10.0)
        
        assert hasattr(state, 'b')
        assert state.b == 10.0
    
    def test_state_is_admissible(self):
        """Test admissibility check."""
        state = State([1.0], 10.0)
        
        assert state.is_admissible() is True
        
        state_zero = State([1.0], 0.0)
        assert state_zero.is_admissible() is False
    
    def test_state_hash(self):
        """Test state hashing."""
        state = State([1.0, 2.0], 10.0)
        
        h = state.hash()
        assert isinstance(h, str)
        assert len(h) > 0
    
    def test_instruction_creation(self):
        """Test Instruction creation."""
        def transform(x):
            return x * 0.5
        
        instr = Instruction(
            op_code="test_op",  # op_code, not name
            pi_func=transform,   # pi_func, not transform
            sigma=0.5,
            kappa=0.3
        )
        
        assert instr.op_code == "test_op"
        assert instr.sigma == 0.5
        assert instr.kappa == 0.3
    
    def test_instruction_repr(self):
        """Test Instruction repr."""
        instr = Instruction("halve", lambda x: x, sigma=0.1, kappa=0.1)
        
        repr_str = repr(instr)
        assert "halve" in repr_str


class TestProposal:
    """Tests for Proposal class."""
    
    def test_proposal_creation(self):
        """Test Proposal object creation."""
        instr = Instruction("test", lambda x: x, sigma=0.1, kappa=0.1)
        x_prime = np.array([1.0, 2.0])
        
        proposal = Proposal(instruction=instr, x_prime=x_prime)
        
        assert proposal.instruction is instr
        assert np.allclose(proposal.x_prime, x_prime)


class TestPotential:
    """Tests for core/potential.py."""
    
    def test_gmi_potential_creation(self):
        """Test GMIPotential creation."""
        potential = GMIPotential()
        
        assert potential is not None
    
    def test_potential_lyapunov(self):
        """Test Lyapunov property: V(x) >= 0."""
        potential = create_potential()
        x = np.array([1.0, 2.0, 3.0])
        
        V = potential.base(x)
        
        assert V >= 0
    
    def test_v_pl_function(self):
        """Test piecewise linear potential function."""
        x = np.array([1.0, 2.0])
        
        V = V_PL(x)  # Only takes x, no theta
        
        assert V >= 0
        # For larger x, V should be larger
        x_large = np.array([5.0, 5.0])
        V_large = V_PL(x_large)
        assert V_large > V
    
    def test_create_potential(self):
        """Test potential factory function."""
        potential = create_potential("gmi")
        
        assert isinstance(potential, GMIPotential)
    
    def test_potential_total(self):
        """Test total potential computation."""
        potential = create_potential()
        x = np.array([1.0, 2.0])
        b = 10.0
        
        V = potential.total(x, b)
        
        assert V >= 0
    
    def test_potential_is_admissible(self):
        """Test admissibility check."""
        potential = create_potential()
        
        assert potential.is_admissible(10.0) is True
        assert potential.is_admissible(0.0) is False
        assert potential.is_admissible(-1.0) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
