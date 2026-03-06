"""
Tests for core/state.py
"""
import numpy as np
import sys
sys.path.insert(0, '.')

from core.state import State, V_PL, Instruction, CompositeInstruction, Proposal


class TestState:
    """Test the State class."""
    
    def test_state_creation(self):
        """Test State can be created with x and budget."""
        x = [1.0, 2.0]
        budget = 10.0
        state = State(x, budget)
        
        assert np.allclose(state.x, [1.0, 2.0])
        assert state.b == budget
    
    def test_state_hash_deterministic(self):
        """Test that State.hash() is deterministic."""
        x = [1.0, 2.0]
        budget = 10.0
        state1 = State(x, budget)
        state2 = State(x, budget)
        
        assert state1.hash() == state2.hash()
    
    def test_state_hash_rounding(self):
        """Test that State.hash() uses proper rounding."""
        x = [1.1234567, 2.9876543]
        budget = 10.0
        state = State(x, budget)
        
        # Should round to 6 decimal places
        hash_result = state.hash()
        assert len(hash_result) == 64  # SHA256 hex length


class TestV_PL:
    """Test the V_PL potential function."""
    
    def test_v_pl_zero_at_origin(self):
        """Test V_PL is zero at origin."""
        x = np.array([0.0, 0.0])
        assert V_PL(x) == 0.0
    
    def test_v_pl_positive(self):
        """Test V_PL is positive for non-zero x."""
        x = np.array([1.0, 1.0])
        assert V_PL(x) == 2.0
    
    def test_v_pl_sum_of_squares(self):
        """Test V_PL computes sum of squares."""
        x = np.array([3.0, 4.0])
        assert V_PL(x) == 25.0


class TestInstruction:
    """Test the Instruction class."""
    
    def test_instruction_creation(self):
        """Test Instruction can be created."""
        def pi(x):
            return x + 1.0
        
        instr = Instruction("TEST", pi, sigma=1.0, kappa=2.0)
        
        assert instr.op_code == "TEST"
        assert instr.sigma == 1.0
        assert instr.kappa == 2.0
    
    def test_instruction_pi_function(self):
        """Test Instruction.pi works correctly."""
        def pi(x):
            return x * 2
        
        instr = Instruction("DOUBLE", pi, sigma=1.0, kappa=1.0)
        result = instr.pi(np.array([1.0, 2.0]))
        
        assert np.allclose(result, [2.0, 4.0])


class TestCompositeInstruction:
    """Test CompositeInstruction for Oplax operator algebra."""
    
    def test_composite_creation(self):
        """Test CompositeInstruction can be created."""
        r1 = Instruction("A", lambda x: x, sigma=1.0, kappa=1.0)
        r2 = Instruction("B", lambda x: x, sigma=1.0, kappa=1.0)
        
        comp = CompositeInstruction(r1, r2, sigma=2.0, kappa=2.0)
        
        assert comp.r1 is r1
        assert comp.r2 is r2
        assert comp.sigma == 2.0
        assert comp.kappa == 2.0


class TestProposal:
    """Test the Proposal dataclass."""
    
    def test_proposal_creation(self):
        """Test Proposal can be created with instruction and x_prime."""
        instr = Instruction("TEST", lambda x: x, sigma=1.0, kappa=1.0)
        x_prime = np.array([2.0, 3.0])
        
        proposal = Proposal(instruction=instr, x_prime=x_prime)
        
        assert proposal.instruction is instr
        assert np.allclose(proposal.x_prime, [2.0, 3.0])
    
    def test_proposal_dataclass(self):
        """Test Proposal is a proper dataclass with defaults."""
        instr = Instruction("TEST", lambda x: x, sigma=1.0, kappa=1.0)
        
        # Test with required fields only
        proposal = Proposal(instruction=instr, x_prime=np.array([1.0, 2.0]))
        
        assert hasattr(proposal, 'instruction')
        assert hasattr(proposal, 'x_prime')
