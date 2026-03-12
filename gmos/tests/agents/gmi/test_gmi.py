"""
GMI Agent Smoke Tests

Basic tests to verify GMI components can be imported and used.
"""

import pytest


class TestGMIPotential:
    """Tests for GMIPotential."""
    
    def test_import_potential(self):
        """Test importing GMIPotential."""
        from gmos.agents.gmi.potential import GMIPotential, create_potential
        assert GMIPotential is not None
        assert create_potential is not None
    
    def test_potential_creation(self):
        """Test creating a potential function."""
        from gmos.agents.gmi.potential import GMIPotential
        import numpy as np
        
        potential = GMIPotential()
        
        # Test on a valid state
        x = np.array([0.5, 0.5])
        v = potential.base(x)
        assert isinstance(v, float)
        assert v >= 0
    
    def test_is_admissible(self):
        """Test admissibility check."""
        from gmos.agents.gmi.potential import GMIPotential
        
        potential = GMIPotential()
        assert potential.is_admissible(10.0) is True
        assert potential.is_admissible(0.0) is False  # b=0 means no motion possible


class TestCognitiveState:
    """Tests for CognitiveState."""
    
    def test_import_state(self):
        """Test importing CognitiveState."""
        from gmos.agents.gmi.state import CognitiveState, State
        assert CognitiveState is not None
        assert State is not None
    
    def test_state_creation(self):
        """Test creating a cognitive state."""
        from gmos.agents.gmi.state import CognitiveState
        import numpy as np
        
        state = CognitiveState(rho=np.array([0.5, 0.5]), theta=np.array([0.0, 0.0]), budget=10.0)
        assert state.budget == 10.0
        assert len(state.rho) == 2
    
    def test_to_vector(self):
        """Test converting state to vector."""
        from gmos.agents.gmi.state import CognitiveState
        import numpy as np
        
        state = CognitiveState(rho=np.array([0.5, 0.5]), theta=np.array([0.0, 0.0]), budget=10.0)
        vec = state.to_vector()
        assert isinstance(vec, np.ndarray)
        assert len(vec) == 5  # rho + theta + budget


class TestTensionLaw:
    """Tests for GMI Tension Law."""
    
    def test_import_tension_law(self):
        """Test importing tension law."""
        from gmos.agents.gmi.tension_law import GMITensionLaw
        assert GMITensionLaw is not None
    
    def test_tension_law_creation(self):
        """Test creating tension law."""
        from gmos.agents.gmi.tension_law import GMITensionLaw, GMITensionState
        import numpy as np
        
        law = GMITensionLaw()
        
        # Test on proper state object
        state = GMITensionState(latent_state=np.array([0.5, 0.5]))
        v = law.compute(state)
        assert isinstance(v, float)


class TestAffectiveState:
    """Tests for AffectiveState."""
    
    def test_import_affective(self):
        """Test importing affective state."""
        from gmos.agents.gmi.affective_state import AffectiveState
        assert AffectiveState is not None


class TestPolicySelection:
    """Tests for PolicySelection."""
    
    def test_import_policy(self):
        """Test importing policy selection."""
        from gmos.agents.gmi.policy_selection import PolicySelection
        assert PolicySelection is not None
