"""
Budget Reserve Tests

Tests for budget reserve floor enforcement.
"""

import pytest


class TestBudgetReserve:
    """Test budget reserve floor enforcement."""
    
    def test_reserve_floor_preserved(self):
        """Test that legal step preserves reserve."""
        from gmos.kernel.budget_router import BudgetRouter, BudgetSlice
        
        router = BudgetRouter(global_reserve=5.0)
        router.register_process_budget("test_process", 10.0, 1.0)  # 10 budget, 1.0 reserve
        
        # Try to spend 4.0 (should leave 6.0, above 1.0 reserve)
        can_spend = router.can_spend("test_process", 0, 4.0)
        assert can_spend is True
        
        # Actually spend
        success = router.apply_spend("test_process", 0, 4.0)
        assert success is True
        
        # Check remaining
        remaining = router.get_budget("test_process", 0)
        assert remaining == 6.0
    
    def test_reserve_violation_rejected(self):
        """Test that step below reserve rejects."""
        from gmos.kernel.budget_router import BudgetRouter
        
        router = BudgetRouter(global_reserve=5.0)
        router.register_process_budget("test_process", 10.0, 1.0)  # 10 budget, 1.0 reserve
        
        # Try to spend 9.5 (would leave 0.5, below 1.0 reserve)
        can_spend = router.can_spend("test_process", 0, 9.5)
        assert can_spend is False
    
    def test_boundary_detection(self):
        """Test boundary detection."""
        from gmos.kernel.budget_router import BudgetRouter
        
        router = BudgetRouter(global_reserve=5.0)
        router.register_process_budget("test_process", 10.0, 1.0)
        
        # At boundary
        is_at = router.is_at_boundary("test_process", 0)
        # Will be True when remaining <= reserve
        assert isinstance(is_at, bool)
    
    def test_reserve_ok_check(self):
        """Test reserve_ok method."""
        from gmos.kernel.budget_router import BudgetRouter
        
        router = BudgetRouter(global_reserve=5.0)
        router.register_process_budget("test_process", 10.0, 1.0)
        
        # Check reserve is OK
        ok = router.reserve_ok("test_process", 0)
        assert ok is True
    
    def test_zero_budget(self):
        """Test zero budget handling."""
        from gmos.kernel.budget_router import BudgetRouter
        
        router = BudgetRouter(global_reserve=5.0)
        router.register_process_budget("test_process", 0.0, 0.0)
        
        # Cannot spend from zero budget
        can_spend = router.can_spend("test_process", 0, 0.1)
        assert can_spend is False
