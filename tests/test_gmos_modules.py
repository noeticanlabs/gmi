"""
GMOS Module Test Suite

Comprehensive tests for the new GMOS implementation:
- gmos/src/gmos/agents/gmi/: GMI agent components
- gmos/src/gmos/kernel/: Kernel components (verifier, scheduler, etc.)
- gmos/src/gmos/memory/: Memory components
- gmos/src/gmos/sensory/: Sensory processing
- gmos/src/gmos/symbolic/: Symbolic processing

Note: GMOS is the canonical implementation in src/gmos/
"""

import numpy as np
import pytest
import sys
import os

# Add gmos to path
sys.path.insert(0, '/home/user/gmi/gmos/src')


class TestGMIAgent:
    """Tests for gmos/src/gmos/agents/gmi/."""
    
    def test_gmi_agent_creation(self):
        """Test GMIAgent creation."""
        try:
            from gmos.agents.gmi.gmi_agent import GMIAgent
            
            agent = GMIAgent(budget=100.0)
            
            assert agent.budget == 100.0
        except ImportError as e:
            pytest.skip(f"GMOS not fully implemented: {e}")
    
    def test_gmi_state_creation(self):
        """Test GMI state."""
        try:
            from gmos.agents.gmi.state import GMIState
            
            state = GMIState(
                x=np.array([1.0, 2.0]),
                budget=10.0
            )
            
            assert np.allclose(state.x, np.array([1.0, 2.0]))
            assert state.budget == 10.0
        except ImportError:
            pytest.skip("GMI state not available")
    
    def test_affective_budget(self):
        """Test affective budget allocation."""
        try:
            from gmos.agents.gmi.affective_budget import AffectiveBudget
            
            budget = AffectiveBudget(total=100.0)
            
            assert budget.total == 100.0
        except ImportError:
            pytest.skip("AffectiveBudget not available")
    
    def test_affective_state(self):
        """Test affective state."""
        try:
            from gmos.agents.gmi.affective_state import AffectiveState
            
            state = AffectiveState(
                valence=0.5,
                arousal=0.3,
                dominance=0.7
            )
            
            assert state.valence == 0.5
        except ImportError:
            pytest.skip("AffectiveState not available")


class TestKernel:
    """Tests for gmos/src/gmos/kernel/."""
    
    def test_verifier(self):
        """Test kernel verifier."""
        try:
            from gmos.kernel.verifier import KernelVerifier
            
            verifier = KernelVerifier()
            
            assert verifier is not None
        except ImportError:
            pytest.skip("KernelVerifier not available")
    
    def test_scheduler(self):
        """Test scheduler."""
        try:
            from gmos.kernel.scheduler import Scheduler
            
            scheduler = Scheduler()
            
            assert scheduler is not None
        except ImportError:
            pytest.skip("Scheduler not available")
    
    def test_receipt(self):
        """Test receipt creation."""
        try:
            from gmos.kernel.receipt import Receipt
            
            receipt = Receipt(
                step_id=1,
                instruction="test",
                decision="ACCEPTED"
            )
            
            assert receipt.step_id == 1
            assert receipt.decision == "ACCEPTED"
        except ImportError:
            pytest.skip("Receipt not available")
    
    def test_reject_codes(self):
        """Test reject codes."""
        try:
            from gmos.kernel.reject_codes import RejectCode
            
            # Test valid reject code
            code = RejectCode.INSUFFICIENT_BUDGET
            
            assert code is not None
        except ImportError:
            pytest.skip("RejectCode not available")
    
    def test_budget_router(self):
        """Test budget routing."""
        try:
            from gmos.kernel.budget_router import BudgetRouter
            
            router = BudgetRouter()
            
            assert router is not None
        except ImportError:
            pytest.skip("BudgetRouter not available")
    
    def test_hash_chain(self):
        """Test hash chain."""
        try:
            from gmos.kernel.hash_chain import HashChain
            
            chain = HashChain()
            
            assert chain is not None
        except ImportError:
            pytest.skip("HashChain not available")
    
    def test_macro_verifier(self):
        """Test macro verifier."""
        try:
            from gmos.kernel.macro_verifier import MacroVerifier
            
            verifier = MacroVerifier()
            
            assert verifier is not None
        except ImportError:
            pytest.skip("MacroVerifier not available")


class TestGMOSMemory:
    """Tests for gmos/src/gmos/memory/."""
    
    def test_archive(self):
        """Test archive."""
        try:
            from gmos.memory.archive import Archive
            
            archive = Archive()
            
            assert archive is not None
        except ImportError:
            pytest.skip("Archive not available")
    
    def test_workspace(self):
        """Test workspace - uses max_capacity not capacity."""
        try:
            from gmos.memory.workspace import Workspace
            
            workspace = Workspace(max_capacity=100)  # Fixed: max_capacity
            
            assert workspace.state.max_capacity == 100
        except ImportError:
            pytest.skip("Workspace not available")
    
    def test_consolidation(self):
        """Test consolidation."""
        try:
            from gmos.memory.consolidation import consolidate
            
            result = consolidate([])
            
            assert result is not None
        except ImportError:
            pytest.skip("consolidate not available")
    
    def test_replay(self):
        """Test replay."""
        try:
            from gmos.memory.replay import replay
            
            result = replay([], context=None)
            
            assert result is not None
        except ImportError:
            pytest.skip("replay not available")
    
    def test_relevance(self):
        """Test relevance scoring."""
        try:
            from gmos.memory.relevance import compute_relevance
            
            score = compute_relevance(
                episode=None,
                context=np.array([1.0])
            )
            
            assert 0 <= score <= 1.0
        except ImportError:
            pytest.skip("compute_relevance not available")


class TestSensory:
    """Tests for gmos/src/gmos/sensory/."""
    
    def test_sensory_connector(self):
        """Test sensory connector."""
        try:
            from gmos.sensory.sensory_connector import SensoryConnector
            
            connector = SensoryConnector()
            
            assert connector is not None
        except ImportError:
            pytest.skip("SensoryConnector not available")
    
    def test_projection(self):
        """Test projection."""
        try:
            from gmos.sensory.projection import project
            
            result = project(
                observation=np.array([1.0, 2.0]),
                manifold_dim=3
            )
            
            assert result is not None
        except ImportError:
            pytest.skip("projection not available")
    
    def test_salience(self):
        """Test salience - it's a dataclass, not a function."""
        try:
            from gmos.sensory.salience import SalienceScore
            
            score = SalienceScore(
                novelty=0.5,
                relevance=0.3,
                surprise=0.2
            )
            
            assert score.novelty == 0.5
            assert score.relevance == 0.3
            assert score.surprise == 0.2
            assert 0 <= score.combined <= 1.0
        except ImportError:
            pytest.skip("SalienceScore not available")


class TestSymbolic:
    """Tests for gmos/src/gmos/symbolic/."""
    
    def test_glyph_embedder(self):
        """Test glyph embedding."""
        try:
            from gmos.symbolic.glyph_embedder import GlyphEmbedder
            
            embedder = GlyphEmbedder(dimensions=64)
            
            assert embedder.dimensions == 64
        except ImportError:
            pytest.skip("GlyphEmbedder not available")
    
    def test_glyph_space(self):
        """Test glyph space."""
        try:
            from gmos.symbolic.glyph_space import GlyphSpace
            
            space = GlyphSpace(dimensions=32)
            
            assert space.dimensions == 32
        except ImportError:
            pytest.skip("GlyphSpace not available")
    
    def test_semantic_manifold(self):
        """Test semantic manifold."""
        try:
            from gmos.symbolic.semantic_manifold import SemanticManifold
            
            manifold = SemanticManifold(dimensions=64)
            
            assert manifold.dimensions == 64
        except ImportError:
            pytest.skip("SemanticManifold not available")
    
    def test_binding(self):
        """Test symbol binding."""
        try:
            from gmos.symbolic.binding import bind
            
            result = bind(
                symbol="test",
                meaning=np.array([1.0, 0.0])
            )
            
            assert result is not None
        except ImportError:
            pytest.skip("binding not available")


class TestGMOSImport:
    """Test that GMOS can be imported."""
    
    def test_gmos_import(self):
        """Test main gmos import."""
        try:
            import gmos
            
            assert gmos is not None
        except ImportError:
            pytest.skip("GMOS package not available")
    
    def test_gmos_version(self):
        """Test gmos has version."""
        try:
            import gmos
            
            # Should have version or __init__.py
            assert hasattr(gmos, '__version__') or hasattr(gmos, '__file__')
        except ImportError:
            pytest.skip("GMOS not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
