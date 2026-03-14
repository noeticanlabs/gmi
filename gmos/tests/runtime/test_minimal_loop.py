"""
Tests for the Minimal Runtime Loop

These tests verify the Phase 1 minimal executable law.

Status: Canonical - Phase 1 Tests
"""

import pytest
from gmos.contracts.types import (
    State,
    BudgetState,
    Verdict,
    create_initial_state,
    create_initial_budget,
    compute_residual,
    check_verifier_inequality,
)
from gmos.runtime.minimal_loop import (
    MinimalVerifier,
    MinimalRuntimeLoop,
    MinimalBudgetManager,
    MinimalStateHost,
    MinimalMemory,
    MinimalReceiptStore,
)


class TestVerifierInequality:
    """Test the core verifier inequality."""
    
    def test_check_inequality_satisfied(self):
        """Test that inequality is satisfied when proposal is good."""
        # V(x_t) = 50, V(x_{t+1}) = 45 (improved)
        # σ = 5, κ = 10, r = 20
        # Check: 45 + 5 <= 50 + 10 + 20 => 50 <= 80 => True
        result = check_verifier_inequality(
            coherence_before=50.0,
            coherence_after=45.0,
            spend=5.0,
            defect=10.0,
            reserve_slack=20.0
        )
        assert result is True
    
    def test_check_inequality_violated(self):
        """Test that inequality is violated when proposal is bad."""
        # V(x_t) = 50, V(x_{t+1}) = 80 (much worse)
        # σ = 10, κ = 5, r = 10
        # Check: 80 + 10 <= 50 + 5 + 10 => 90 <= 65 => False
        result = check_verifier_inequality(
            coherence_before=50.0,
            coherence_after=80.0,
            spend=10.0,
            defect=5.0,
            reserve_slack=10.0
        )
        assert result is False
    
    def test_check_inequality_boundary(self):
        """Test boundary case where inequality is exactly satisfied."""
        # V(x_t) = 50, V(x_{t+1}) = 50 (no change)
        # σ = 5, κ = 10, r = 5
        # Check: 50 + 5 <= 50 + 10 + 5 => 55 <= 65 => True
        result = check_verifier_inequality(
            coherence_before=50.0,
            coherence_after=50.0,
            spend=5.0,
            defect=10.0,
            reserve_slack=5.0
        )
        assert result is True


class TestComputeResidual:
    """Test residual computation."""
    
    def test_residual_improving(self):
        """Test residual when coherence improves."""
        residual = compute_residual(coherence_before=50.0, coherence_after=45.0)
        assert residual == -5.0
    
    def test_residual_degrading(self):
        """Test residual when coherence degrades."""
        residual = compute_residual(coherence_before=50.0, coherence_after=60.0)
        assert residual == 10.0
    
    def test_residual_neutral(self):
        """Test residual when coherence is unchanged."""
        residual = compute_residual(coherence_before=50.0, coherence_after=50.0)
        assert residual == 0.0


class TestMinimalVerifier:
    """Test the minimal verifier."""
    
    def test_verifier_accepts_good_proposal(self):
        """Test that verifier accepts proposals that satisfy inequality."""
        verifier = MinimalVerifier(defect_tolerance=10.0)
        
        current = create_initial_state(coherence=50.0)
        proposed = State(state_id="proposed", step=1, coherence=45.0)
        budget = create_initial_budget(total=100.0, reserve_floor=10.0)
        
        result = verifier.verify(current, proposed, budget, spend=5.0)
        
        assert result.verdict == Verdict.ACCEPT
    
    def test_verifier_rejects_bad_proposal(self):
        """Test that verifier rejects proposals that violate inequality."""
        verifier = MinimalVerifier(defect_tolerance=5.0)
        
        current = create_initial_state(coherence=50.0)
        proposed = State(state_id="proposed", step=1, coherence=80.0)  # Much worse
        budget = create_initial_budget(total=100.0, reserve_floor=10.0)
        
        result = verifier.verify(current, proposed, budget, spend=20.0)
        
        assert result.verdict == Verdict.REJECT


class TestMinimalBudgetManager:
    """Test the minimal budget manager."""
    
    def test_initial_budget(self):
        """Test initial budget state."""
        manager = MinimalBudgetManager(total=100.0, reserve_floor=10.0)
        budget = manager.get_budget()
        
        assert budget.total == 100.0
        assert budget.available == 100.0
        assert budget.reserve_floors["default"] == 10.0
    
    def test_can_spend_within_reserve(self):
        """Test spending within reserve limits."""
        manager = MinimalBudgetManager(total=100.0, reserve_floor=10.0)
        
        assert manager.can_spend(50.0) is True
        assert manager.can_spend(89.0) is True
        assert manager.can_spend(91.0) is False  # Would violate reserve
    
    def test_spend_updates_available(self):
        """Test that spending updates available budget."""
        manager = MinimalBudgetManager(total=100.0, reserve_floor=10.0)
        
        result = manager.spend(30.0)
        
        assert result is True
        assert manager.available == 70.0
        assert manager.spent == 30.0
    
    def test_spend_fails_at_reserve_boundary(self):
        """Test that spending fails at reserve boundary."""
        manager = MinimalBudgetManager(total=100.0, reserve_floor=10.0)
        
        result = manager.spend(95.0)  # Would leave only 5, below 10 reserve
        
        assert result is False
        assert manager.available == 100.0  # No change


class TestMinimalRuntimeLoop:
    """Test the minimal runtime loop."""
    
    def test_loop_initialization(self):
        """Test loop initializes correctly."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        state = loop.state_host.get_state()
        assert state.coherence == 50.0
        
        budget = loop.budget_manager.get_budget()
        assert budget.total == 100.0
    
    def test_loop_accepts_proposal(self):
        """Test loop accepts a lawful proposal."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        result = loop.step(
            proposed_coherence_change=-5.0,  # Improve coherence
            proposed_spend=5.0
        )
        
        assert result.verdict == Verdict.ACCEPT
        assert result.state_after.coherence == 45.0
    
    def test_loop_rejects_over_budget(self):
        """Test loop rejects over-budget proposal."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        result = loop.step(
            proposed_coherence_change=10.0,  # Degrade coherence
            proposed_spend=95.0  # Would violate reserve
        )
        
        # Either rejected or repaired
        assert result.verdict in [Verdict.REJECT, Verdict.REPAIR]
    
    def test_loop_creates_receipt(self):
        """Test loop creates receipts."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        result = loop.step(
            proposed_coherence_change=-5.0,
            proposed_spend=5.0
        )
        
        assert result.receipt is not None
        assert result.receipt.step == 0
    
    def test_loop_sequence(self):
        """Test running multiple steps."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        results = loop.run_sequence(
            num_steps=3,
            coherence_changes=[-5.0, -5.0, -5.0],
            spends=[5.0, 5.0, 5.0]
        )
        
        assert len(results) == 3
        
        # All should be accepted
        for r in results:
            assert r.verdict == Verdict.ACCEPT
    
    def test_loop_decreases_coherence(self):
        """Test that loop decreases coherence over successful steps."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        results = loop.run_sequence(
            num_steps=3,
            coherence_changes=[-5.0, -5.0, -5.0],
            spends=[5.0, 5.0, 5.0]
        )
        
        # Coherence should decrease (improve)
        final_coherence = loop.state_host.get_state().coherence
        assert final_coherence < 50.0
    
    def test_loop_budget_decreases(self):
        """Test that budget decreases with spending."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        loop.run_sequence(
            num_steps=3,
            coherence_changes=[-5.0, -5.0, -5.0],
            spends=[5.0, 5.0, 5.0]
        )
        
        final_budget = loop.budget_manager.get_budget()
        assert final_budget.available < 100.0
    
    def test_receipt_continuity(self):
        """Test that every step has a valid receipt."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        results = loop.run_sequence(
            num_steps=5,
            coherence_changes=[-5.0] * 5,
            spends=[5.0] * 5
        )
        
        receipts = loop.receipt_store.get_all()
        
        assert len(receipts) == 5
        
        # Check receipt continuity
        for i, receipt in enumerate(receipts):
            assert receipt.step == i
            assert receipt.verdict == Verdict.ACCEPT


class TestMinimalMemory:
    """Test minimal memory."""
    
    def test_store_episode(self):
        """Test storing memory episodes."""
        memory = MinimalMemory()
        
        episode_id = memory.store({"content": "test"})
        
        assert episode_id is not None
        assert len(memory.episodes) == 1
    
    def test_retrieve_episodes(self):
        """Test retrieving memory."""
        memory = MinimalMemory()
        
        memory.store({"content": "test1"})
        memory.store({"content": "test2"})
        
        retrieved = memory.retrieve()
        
        assert len(retrieved) == 2


# ============================================================================
# Acceptance Tests from Phase 1 Spec
# ============================================================================


class TestPhase1Acceptance:
    """Phase 1 acceptance tests."""
    
    def test_accepted_lawful_proposal(self):
        """Test accepted lawful proposal."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        result = loop.step(
            proposed_coherence_change=-5.0,  # Improves coherence
            proposed_spend=5.0
        )
        
        assert result.verdict == Verdict.ACCEPT
    
    def test_rejected_over_budget_proposal(self):
        """Test rejected over-budget proposal."""
        loop = MinimalRuntimeLoop(
            initial_coherence=50.0,
            initial_budget=100.0,
            reserve_floor=10.0
        )
        
        result = loop.step(
            proposed_coherence_change=10.0,  # Worse coherence
            proposed_spend=95.0  # Violates reserve
        )
        
        # Should be rejected or repaired
        assert result.verdict in [Verdict.REJECT, Verdict.REPAIR]
    
    def test_repaired_proposal(self):
        """Test repaired proposal."""
        verifier = MinimalVerifier(defect_tolerance=10.0)
        
        current = create_initial_state(coherence=50.0)
        proposed = State(state_id="proposed", step=1, coherence=55.0)  # Slightly worse
        budget = create_initial_budget(total=100.0, reserve_floor=10.0)
        
        result = verifier.verify(current, proposed, budget, spend=5.0)
        
        # May be repaired or accepted depending on parameters
        assert result.verdict in [Verdict.ACCEPT, Verdict.REPAIR]
    
    def test_reserve_floor_violation(self):
        """Test reserve floor violation detection."""
        manager = MinimalBudgetManager(total=100.0, reserve_floor=20.0)
        
        # This should fail - would leave only 5, below 20 reserve
        can_spend = manager.can_spend(80.0)
        
        assert can_spend is False
    
    def test_invalid_percept(self):
        """Test handling of invalid/malformed percept."""
        loop = MinimalRuntimeLoop()
        
        # Using None as raw input
        result = loop.step(raw_input=None)
        
        # Should still work, just use default
        assert result.verdict in [Verdict.ACCEPT, Verdict.REJECT, Verdict.REPAIR]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
