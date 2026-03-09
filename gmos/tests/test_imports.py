"""
GM-OS Import Smoke Tests

Basic import verification tests to ensure package integrity.
"""

import pytest


class TestGMOSImports:
    """Test that GM-OS packages can be imported."""
    
    def test_import_gmos(self):
        """Test importing main gmos package."""
        import gmos
        assert gmos is not None
    
    def test_import_kernel(self):
        """Test importing kernel module."""
        import gmos.kernel
        assert gmos.kernel is not None
    
    def test_import_agents_gmi(self):
        """Test importing GMI agent module."""
        import gmos.agents.gmi
        assert gmos.agents.gmi is not None
    
    def test_import_memory(self):
        """Test importing memory module."""
        import gmos.memory
        assert gmos.memory is not None
    
    def test_import_action(self):
        """Test importing action module."""
        import gmos.action
        assert gmos.action is not None
    
    def test_import_sensory(self):
        """Test importing sensory module."""
        import gmos.sensory
        assert gmos.sensory is not None
    
    def test_import_symbolic(self):
        """Test importing symbolic module."""
        import gmos.symbolic
        assert gmos.symbolic is not None
    
    def test_import_experimental(self):
        """Test importing experimental module."""
        import gmos.experimental
        assert gmos.experimental is not None


class TestKernelImports:
    """Test kernel module imports."""
    
    def test_import_substrate_state(self):
        """Test importing substrate state."""
        from gmos.kernel import substrate_state
        assert substrate_state is not None
    
    def test_import_scheduler(self):
        """Test importing scheduler."""
        from gmos.kernel import scheduler
        assert scheduler is not None
    
    def test_import_budget_router(self):
        """Test importing budget router."""
        from gmos.kernel import budget_router
        assert budget_router is not None
    
    def test_import_verifier(self):
        """Test importing verifier."""
        from gmos.kernel import verifier
        assert verifier is not None
    
    def test_import_hash_chain(self):
        """Test importing hash chain."""
        from gmos.kernel import hash_chain
        assert hash_chain is not None
    
    def test_import_theorems(self):
        """Test importing theorems."""
        from gmos.kernel import theorems
        assert theorems is not None
    
    def test_import_continuous_dynamics(self):
        """Test importing continuous dynamics."""
        from gmos.kernel import continuous_dynamics
        assert continuous_dynamics is not None


class TestGMIImports:
    """Test GMI agent imports."""
    
    def test_import_potential(self):
        """Test importing potential."""
        from gmos.agents.gmi import potential
        assert potential is not None
    
    def test_import_tension_law(self):
        """Test importing tension law."""
        from gmos.agents.gmi import tension_law
        assert tension_law is not None
    
    def test_import_state(self):
        """Test importing state."""
        from gmos.agents.gmi import state
        assert state is not None
    
    def test_import_affective_state(self):
        """Test importing affective state."""
        from gmos.agents.gmi import affective_state
        assert affective_state is not None
    
    def test_import_policy_selection(self):
        """Test importing policy selection."""
        from gmos.agents.gmi import policy_selection
        assert policy_selection is not None
    
    def test_import_execution_loop(self):
        """Test importing execution loop."""
        from gmos.agents.gmi import execution_loop
        assert execution_loop is not None


class TestActionImports:
    """Test action module imports."""
    
    def test_import_commitment(self):
        """Test importing commitment."""
        from gmos.action import commitment
        assert commitment is not None
    
    def test_import_external_io(self):
        """Test importing external_io."""
        from gmos.action import external_io
        assert external_io is not None
    
    def test_import_replenishment(self):
        """Test importing replenishment."""
        from gmos.action import replenishment
        assert replenishment is not None
