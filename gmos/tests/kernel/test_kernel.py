"""
Tests for GM-OS Kernel Modules.

Tests for:
- StateHost
- KernelScheduler
- BudgetRouter
- ProcessTable
- MacroVerifier
"""

import pytest
from gmos.kernel import state_host, scheduler, budget_router, process_table, macro_verifier


class TestStateHost:
    """Tests for StateHost."""
    
    def test_register_process(self):
        """Test process registration."""
        sh = state_host.StateHost()
        s = sh.register_process("test", {"value": 42})
        assert s.process_id == "test"
        assert s.state_data["value"] == 42
    
    def test_get_state(self):
        """Test getting state."""
        sh = state_host.StateHost()
        sh.register_process("test", {"value": 42})
        s = sh.get_state("test")
        assert s is not None
        assert s.process_id == "test"
    
    def test_set_state(self):
        """Test setting new state."""
        sh = state_host.StateHost()
        sh.register_process("test", {"value": 42})
        s = sh.set_state("test", {"value": 100})
        assert s.state_data["value"] == 100
        assert s.step_index == 1
    
    def test_mark_halt(self):
        """Test marking process as halted."""
        sh = state_host.StateHost()
        sh.register_process("test", {"value": 42})
        result = sh.mark_halt("test")
        assert result is True
        s = sh.get_state("test")
        assert s.flag == state_host.ProcessStateFlag.HALTED
    
    def test_mark_torpor(self):
        """Test marking process as in torpor."""
        sh = state_host.StateHost()
        sh.register_process("test", {"value": 42})
        result = sh.mark_torpor("test")
        assert result is True
        s = sh.get_state("test")
        assert s.flag == state_host.ProcessStateFlag.TORPOR


class TestKernelScheduler:
    """Tests for KernelScheduler."""
    
    def test_register_process(self):
        """Test registering a process."""
        ks = scheduler.KernelScheduler()
        ks.register_process("test", scheduler.ScheduleMode.ACTIVE)
        assert "test" in ks._processes
    
    def test_tick(self):
        """Test scheduling tick."""
        ks = scheduler.KernelScheduler()
        ks.register_process("test", scheduler.ScheduleMode.ACTIVE)
        next_pid = ks.tick()
        assert next_pid == "test"
    
    def test_set_mode(self):
        """Test setting scheduler mode."""
        ks = scheduler.KernelScheduler()
        ks.set_mode(scheduler.ScheduleMode.SURVIVAL_CRITICAL)
        assert ks._current_mode == scheduler.ScheduleMode.SURVIVAL_CRITICAL


class TestBudgetRouter:
    """Tests for BudgetRouter."""
    
    def test_register_budget(self):
        """Test budget registration."""
        br = budget_router.BudgetRouter()
        b = br.register_process_budget("test", 1, 100.0, 10.0)
        assert b.process_id == "test"
        assert b.amount == 100.0
        assert b.reserve == 10.0
    
    def test_can_spend_valid(self):
        """Test valid spend check."""
        br = budget_router.BudgetRouter()
        br.register_process_budget("test", 1, 100.0, 20.0)
        assert br.can_spend("test", 1, 80.0) is True
    
    def test_can_spend_below_reserve(self):
        """Test spend below reserve is rejected."""
        br = budget_router.BudgetRouter()
        br.register_process_budget("test", 1, 100.0, 20.0)
        assert br.can_spend("test", 1, 90.0) is False
    
    def test_apply_spend(self):
        """Test applying a spend."""
        br = budget_router.BudgetRouter()
        br.register_process_budget("test", 1, 100.0, 20.0)
        result = br.apply_spend("test", 1, 50.0)
        assert result is True
        assert br.get_budget("test", 1) == 50.0
    
    def test_reserve_protected(self):
        """Test that reserve is always protected."""
        br = budget_router.BudgetRouter()
        br.register_process_budget("test", 1, 100.0, 30.0)
        # Try to spend 80 (would leave only 20, below reserve of 30)
        result = br.apply_spend("test", 1, 80.0)
        assert result is False
        # Budget should remain unchanged
        assert br.get_budget("test", 1) == 100.0


class TestProcessTable:
    """Tests for ProcessTable."""
    
    def test_register(self):
        """Test process registration."""
        pt = process_table.ProcessTable()
        rec = pt.register("gmi1", process_table.ProcessType.GMI, priority=5)
        assert rec.process_id == "gmi1"
        assert rec.process_type == process_table.ProcessType.GMI
    
    def test_get(self):
        """Test getting process record."""
        pt = process_table.ProcessTable()
        pt.register("gmi1", process_table.ProcessType.GMI)
        rec = pt.get("gmi1")
        assert rec is not None
        assert rec.process_id == "gmi1"
    
    def test_set_mode(self):
        """Test setting process mode."""
        pt = process_table.ProcessTable()
        pt.register("gmi1", process_table.ProcessType.GMI)
        pt.set_mode("gmi1", process_table.ProcessMode.HALTED)
        rec = pt.get("gmi1")
        assert rec.mode == process_table.ProcessMode.HALTED
    
    def test_list_active(self):
        """Test listing active processes."""
        pt = process_table.ProcessTable()
        pt.register("gmi1", process_table.ProcessType.GMI)
        pt.register("gmi2", process_table.ProcessType.GMI)
        active = pt.list_active()
        assert len(active) == 2


class TestMacroVerifier:
    """Tests for MacroVerifier."""
    
    def test_build_slab(self):
        """Test building a slab."""
        mv = macro_verifier.MacroVerifier()
        receipts = [
            {"step": 0, "spend": 1.0, "defect": 0.1},
            {"step": 1, "spend": 1.5, "defect": 0.2},
        ]
        slab = mv.build_slab("slab1", "test", 0, 1, receipts)
        assert slab.slab_id == "slab1"
        assert slab.total_spend == 2.5
        assert abs(slab.total_defect - 0.3) < 1e-6
    
    def test_verify_oplax_bound_valid(self):
        """Test oplax bound verification (valid)."""
        mv = macro_verifier.MacroVerifier()
        receipts = [
            {"spend": 1.0, "defect": 0.1},
            {"spend": 1.5, "defect": 0.2},
        ]
        slab = mv.build_slab("slab1", "test", 0, 1, receipts)
        assert mv.verify_oplax_bound(slab) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
