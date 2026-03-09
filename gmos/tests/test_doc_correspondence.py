"""
Doc-to-Code Correspondence Tests

Tests that verify documented concepts exist in code.
This prevents docs from quietly drifting into fiction.
"""

import pytest


class TestOperationalModes:
    """Test operational modes from docs exist in code."""
    
    def test_operational_mode_enum(self):
        """Test OperationalMode enum exists."""
        from gmos.kernel.substrate_state import OperationalMode
        
        # Should have these modes per spec
        assert hasattr(OperationalMode, 'REFLEX')
        assert hasattr(OperationalMode, 'SAFETY')
        assert hasattr(OperationalMode, 'ACTIVE')
        assert hasattr(OperationalMode, 'REFLECTIVE')
        assert hasattr(OperationalMode, 'CONSOLIDATION')


class TestTheoremSuite:
    """Test theorem suite exists."""
    
    def test_theorems_exist(self):
        """Test all 8 theorems exist."""
        from gmos.kernel import theorems
        
        assert hasattr(theorems, 'theorem_forward_invariance')
        assert hasattr(theorems, 'theorem_kernel_monopoly')
        assert hasattr(theorems, 'theorem_budget_reserve_preservation')
        assert hasattr(theorems, 'theorem_anchor_dominance')
        assert hasattr(theorems, 'theorem_memory_loop_finiteness')
        assert hasattr(theorems, 'theorem_discrete_soundness')
        assert hasattr(theorems, 'theorem_chain_closure')
        assert hasattr(theorems, 'theorem_deterministic_consensus')
    
    def test_gmos_theorems_class(self):
        """Test GMOSTheorems class exists."""
        from gmos.kernel import GMOSTheorems
        
        assert hasattr(GMOSTheorems, 'verify_all')


class TestGMIComponents:
    """Test GMI components from docs exist."""
    
    def test_gmi_potential(self):
        """Test GMIPotential exists."""
        from gmos.agents.gmi.potential import GMIPotential
        assert GMIPotential is not None
    
    def test_tension_law(self):
        """Test tension law exists."""
        from gmos.agents.gmi.tension_law import GMITensionLaw
        assert GMITensionLaw is not None
    
    def test_cognitive_state(self):
        """Test CognitiveState exists."""
        from gmos.agents.gmi.state import CognitiveState
        assert CognitiveState is not None
    
    def test_affective_state(self):
        """Test AffectiveState exists."""
        from gmos.agents.gmi.affective_state import AffectiveState
        assert AffectiveState is not None


class TestKernelComponents:
    """Test kernel components from docs exist."""
    
    def test_full_substrate_state(self):
        """Test FullSubstrateState exists."""
        from gmos.kernel import FullSubstrateState
        assert FullSubstrateState is not None
    
    def test_budget_router(self):
        """Test BudgetRouter exists."""
        from gmos.kernel import BudgetRouter
        assert BudgetRouter is not None
    
    def test_kernel_scheduler(self):
        """Test KernelScheduler exists."""
        from gmos.kernel import KernelScheduler
        assert KernelScheduler is not None
    
    def test_hash_chain_ledger(self):
        """Test HashChainLedger exists."""
        from gmos.kernel import HashChainLedger
        assert HashChainLedger is not None
    
    def test_reject_codes(self):
        """Test RejectCode enum exists."""
        from gmos.kernel import RejectCode
        assert RejectCode is not None
        assert hasattr(RejectCode, 'RESERVE_VIOLATION')
        assert hasattr(RejectCode, 'ANCHOR_CONFLICT')


class TestMemoryComponents:
    """Test memory components from docs exist."""
    
    def test_workspace(self):
        """Test Workspace exists."""
        from gmos.memory.workspace import Workspace
        assert Workspace is not None
    
    def test_consolidator(self):
        """Test Consolidator exists."""
        from gmos.memory.consolidation import Consolidator
        assert Consolidator is not None


class TestActionComponents:
    """Test action components from docs exist."""
    
    def test_commitment_manager(self):
        """Test CommitmentManager exists."""
        from gmos.action.commitment import CommitmentManager
        assert CommitmentManager is not None
    
    def test_external_interface(self):
        """Test ExternalInterface exists."""
        from gmos.action.external_io import ExternalInterface
        assert ExternalInterface is not None
    
    def test_replenishment_validator(self):
        """Test ReplenishmentValidator exists."""
        from gmos.action.replenishment import ReplenishmentValidator
        assert ReplenishmentValidator is not None
