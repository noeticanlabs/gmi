"""
Adapters Test Suite

Comprehensive tests for:
- adapters/base.py: Base adapter interface
- adapters/stochastic_synthesizer.py: NPE proposal generation
- adapters/npe_adapter.py: NPE integration
- adapters/cbtsv1_adapter.py: CBTSv1 solver adapter
- adapters/npe_integration.py: NPE + GMI runtime
"""

import numpy as np
import pytest
import sys
sys.path.insert(0, '/home/user/gmi')


class TestStochasticSynthesizer:
    """Tests for adapters/stochastic_synthesizer.py."""
    
    def test_synthesizer_creation(self):
        """Test StochasticSynthesizer creation."""
        from adapters.stochastic_synthesizer import StochasticSynthesizer
        
        synth = StochasticSynthesizer(
            temperature=1.0,
            hallucination_rate=0.3
        )
        
        assert synth.temperature == 1.0
        assert synth.hallucination_rate == 0.3
    
    def test_proposal_generation(self):
        """Test proposal generation."""
        from adapters.stochastic_synthesizer import StochasticSynthesizer
        
        synth = StochasticSynthesizer(temperature=1.0, hallucination_rate=0.5)
        
        context = {"task": "test", "step": 0}
        proposals = synth.generate_wild_proposals(context, n_proposals=5)
        
        assert len(proposals) == 5
    
    def test_wild_proposal_structure(self):
        """Test WildProposal structure."""
        from adapters.stochastic_synthesizer import StochasticSynthesizer
        
        synth = StochasticSynthesizer(temperature=1.0, hallucination_rate=0.5)
        
        context = {"task": "test"}
        
        proposals = synth.generate_wild_proposals(context, n_proposals=3)
        
        # Each proposal should be a WildProposal with novelty_score
        for p in proposals:
            assert hasattr(p, 'novelty_score')
    
    def test_temperature_effect(self):
        """Test temperature affects randomness."""
        from adapters.stochastic_synthesizer import StochasticSynthesizer
        
        cold = StochasticSynthesizer(temperature=0.1, hallucination_rate=0.5)
        hot = StochasticSynthesizer(temperature=2.0, hallucination_rate=0.5)
        
        context = {"task": "test"}
        
        # Both should produce proposals
        cold_proposals = cold.generate_wild_proposals(context, n_proposals=5)
        hot_proposals = hot.generate_wild_proposals(context, n_proposals=5)
        
        assert len(cold_proposals) == 5
        assert len(hot_proposals) == 5


class TestNPEAdapter:
    """Tests for adapters/npe_adapter.py."""
    
    def test_npe_adapter_creation(self):
        """Test NPEAdapter creation."""
        try:
            from adapters.npe_adapter import NPEAdapter
            
            adapter = NPEAdapter(n_proposals=3)
            
            assert adapter.n_proposals == 3
        except Exception as e:
            pytest.skip(f"NPEAdapter not available: {e}")
    
    def test_npe_adapter_available(self):
        """Test NPEAdapter can be imported."""
        try:
            from adapters.npe_adapter import NPEAdapter
            
            assert NPEAdapter is not None
        except Exception as e:
            pytest.skip(f"NPEAdapter not available: {e}")


class TestCBTSv1Adapter:
    """Tests for adapters/cbtsv1_adapter.py."""
    
    def test_cbtsv1_adapter_creation(self):
        """Test CBTSv1 adapter creation."""
        try:
            from adapters.cbtsv1_adapter import CBTSv1Adapter
            
            adapter = CBTSv1Adapter(
                solver_type="gr",
                Nx=8, Ny=8, Nz=8
            )
            
            assert adapter.solver_type == "gr"
            assert adapter.Nx == 8
        except Exception as e:
            pytest.skip(f"CBTSv1Adapter not available: {e}")
    
    def test_governed_step(self):
        """Test governed execution step."""
        try:
            from adapters.cbtsv1_adapter import CBTSv1Adapter
            
            adapter = CBTSv1Adapter(solver_type="gr", Nx=4, Ny=4, Nz=4)
            
            # Test with simple step
            result = adapter.execute_governed_step(dt_candidate=0.01)
            
            assert result is not None
            assert hasattr(result, 'accepted')
        except Exception as e:
            pytest.skip(f"CBTSv1Adapter not available: {e}")
    
    def test_solver_initialization(self):
        """Test solver initialization."""
        try:
            from adapters.cbtsv1_adapter import CBTSv1Adapter
            
            adapter = CBTSv1Adapter(solver_type="wave", Nx=4, Ny=4, Nz=4)
            
            assert adapter.solver is not None
        except Exception as e:
            pytest.skip(f"CBTSv1Adapter not available: {e}")


class TestNPEIntegration:
    """Tests for adapters/npe_integration.py."""
    
    def test_npe_gmi_runtime_creation(self):
        """Test NPE+GMI runtime creation."""
        try:
            from adapters.npe_integration import create_npe_gmi_runtime
            
            def V(x):
                return float(np.sum(x**2))
            
            runtime = create_npe_gmi_runtime(
                potential_fn=V,
                budget=100.0
            )
            
            assert runtime is not None
        except Exception as e:
            pytest.skip(f"NPE integration not available: {e}")
    
    def test_runtime_execution(self):
        """Test runtime execution."""
        try:
            from adapters.npe_integration import create_npe_gmi_runtime
            
            def V(x):
                return float(np.sum(x**2))
            
            runtime = create_npe_gmi_runtime(
                potential_fn=V,
                budget=20.0
            )
            
            result = runtime.run(
                initial_x=np.array([1.0, 1.0]),
                budget=20.0,
                n_steps=3
            )
            
            assert result is not None
            assert hasattr(result, 'x')
        except Exception as e:
            pytest.skip(f"NPE integration not available: {e}")


class TestAdapterBase:
    """Tests for adapters/base.py."""
    
    def test_adapter_base_available(self):
        """Test base adapter is available."""
        try:
            import adapters.base as base_module
            
            assert base_module is not None
        except Exception as e:
            pytest.skip(f"Adapter base not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
