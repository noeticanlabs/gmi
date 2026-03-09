"""
GMI Abilities Test Suite - Inside GMOS

Tests the GMI (Governed Metabolic Intelligence) capabilities
when accessed through the GMOS framework.

Key GMI Abilities Tested:
1. Module imports and basic functionality
2. GMIPotential for thermodynamic verification
3. Affective state management
4. Semantic processing
5. Policy selection
"""

import numpy as np
import pytest
import sys
import os
import tempfile

sys.path.insert(0, '/home/user/gmi/gmos/src')
sys.path.insert(0, '/home/user/gmi')


class TestGMIEngineImports:
    """Test GMI engine imports work."""
    
    def test_execution_loop_import(self):
        """Test execution_loop can be imported."""
        from gmos.agents.gmi import execution_loop
        
        assert execution_loop is not None
        assert hasattr(execution_loop, 'run_gmi_engine')
    
    def test_evolution_loop_import(self):
        """Test evolution_loop can be imported."""
        from gmos.agents.gmi import evolution_loop
        
        assert evolution_loop is not None


class TestGMIPotential:
    """Test GMIPotential inside GMOS."""
    
    def test_potential_creation(self):
        """Test potential creation."""
        from gmos.agents.gmi import potential
        
        pot = potential.create_potential()
        
        assert pot is not None
    
    def test_lyapunov_property(self):
        """Test Lyapunov property: V(x) >= 0."""
        from gmos.agents.gmi import potential
        
        pot = potential.create_potential()
        x = np.array([1.0, 2.0, 3.0])
        
        V = pot.base(x)
        
        assert V >= 0, "Potential should be non-negative"
    
    def test_potential_total(self):
        """Test total potential with budget."""
        from gmos.agents.gmi import potential
        
        pot = potential.create_potential()
        x = np.array([1.0, 2.0])
        b = 10.0
        
        V = pot.total(x, b)
        
        assert V >= 0


class TestGMIConstraints:
    """Test GMI constraints inside GMOS."""
    
    def test_constraint_governor(self):
        """Test constraint governor."""
        from gmos.agents.gmi import constraints
        
        governor = constraints.ConstraintGovernor()
        
        assert governor is not None
    
    def test_constraint_set(self):
        """Test constraint set."""
        from gmos.agents.gmi import constraints
        
        cset = constraints.ConstraintSet()
        
        assert cset is not None


class TestGMIAffective:
    """Test GMI affective components in GMOS."""
    
    def test_affective_state(self):
        """Test affective state."""
        from gmos.agents.gmi import affective_state
        
        state = affective_state.AffectiveCognitiveState(
            rho=np.array([1.0, 0.5]),
            theta=np.array([0.0])
        )
        
        assert state is not None
        assert state.rho is not None
    
    def test_affective_budget(self):
        """Test affective budget manager."""
        from gmos.agents.gmi import affective_budget
        
        manager = affective_budget.AffectiveBudgetCalculator()
        
        assert manager is not None


class TestGMISemanticLoop:
    """Test GMI semantic loop in GMOS."""
    
    def test_semantic_loop_import(self):
        """Test semantic loop can be imported."""
        from gmos.agents.gmi import semantic_loop
        
        assert semantic_loop is not None


class TestGMIPolicySelection:
    """Test GMI policy selection in GMOS."""
    
    def test_policy_selector(self):
        """Test policy selector."""
        from gmos.agents.gmi import policy_selection
        
        selector = policy_selection.SelectionOperator()
        
        assert selector is not None


class TestGMITensionLaw:
    """Test GMI tension law in GMOS."""
    
    def test_tension_import(self):
        """Test tension law can be imported."""
        from gmos.agents.gmi import tension_law
        
        assert tension_law is not None


class TestGMIAgentIntegration:
    """Integration tests for GMI in GMOS."""
    
    def test_state_module(self):
        """Test state module works."""
        from gmos.agents.gmi import state
        
        # GMOS State uses 'budget' positional arg and stores as 'b'
        s = state.State(x=[1.0, 2.0], budget=10.0)
        
        assert np.allclose(s.x, [1.0, 2.0])
        assert s.b == 10.0
    
    def test_instruction(self):
        """Test instruction creation."""
        from gmos.agents.gmi import state
        
        instr = state.Instruction(
            op_code="TEST",
            pi_func=lambda x: x,
            sigma=0.1,
            kappa=0.1
        )
        
        assert instr.op_code == "TEST"
    
    def test_proposal(self):
        """Test proposal creation."""
        from gmos.agents.gmi import state
        
        instr = state.Instruction("TEST", lambda x: x, 0.1, 0.1)
        proposal = state.Proposal(instruction=instr, x_prime=np.array([1.0]))
        
        assert proposal.instruction is instr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
