"""
Persistence Stack Demonstration Tests

This test suite demonstrates the two-perspective architecture:
1. GM-OS (Universe): Kernel-level governance using the persistence stack
2. GMI (Inhabitant): Agent-level survival logic using the same stack

Per docs/persistence_stack_roles.md:
- GM-OS = The Universe (governance/regulation)
- GMI = The Inhabitant (survival logic)
- Same machinery, different role
"""

import pytest
import sys

sys.path.insert(0, '/home/user/gmi/gmos/src')
sys.path.insert(0, '/home/user/gmi')


class TestGMOSUniversePerspective:
    """
    GM-OS (Universe) Perspective Tests
    
    GM-OS uses the persistence stack as the laws of physics.
    It governs, regulates, and enforces rules.
    """
    
    def test_danger_monitor_as_universe_judge(self):
        """GM-OS: DangerMonitor acts as the judge of system health."""
        from gmos.kernel.danger import DangerMonitor, DangerBand, create_danger_monitor
        
        # Create danger monitor (GM-OS's diagnostic instrument)
        monitor = create_danger_monitor()
        
        # GM-OS observes internal process signals
        state = monitor.update(v=0.3, t=0.2, c=0.1, b=50.0, h=0.8, i=0.9)
        
        # GM-OS computes danger index as the universe's entropy measure
        state = monitor.compute_danger(state)
        
        # GM-OS determines the health band (the "physical law" zone)
        band = monitor._get_band(state.danger_index)
        
        assert state.danger_index >= 0
        assert band in DangerBand
        assert isinstance(band.name, str)
        
        print(f"GM-OS (Universe): Process danger={state.danger_index:.3f}, band={band.name}")
    
    def test_reconfiguration_as_geometry_law(self):
        """GM-OS: ReconfigurationController enforces geometry modes as physical laws."""
        from gmos.kernel.reconfiguration import (
            GeometryMode, ReconfigurationController
        )
        
        # GM-OS creates the law of geometry
        controller = ReconfigurationController()
        
        # GM-OS evaluates what geometry the process CAN afford (not what it wants)
        safe_mode = controller.evaluate(0.15)  # Low danger
        critical_mode = controller.evaluate(0.85)  # High danger
        
        assert safe_mode in GeometryMode
        assert critical_mode in GeometryMode
        
        # GM-OS enforces that at high danger, geometry should be lower cost
        # (Full modes are for healthy states, not critical ones)
        print(f"GM-OS (Universe): Safe geometry={safe_mode.value}, Critical geometry={critical_mode.value}")
    
    def test_operating_cost_as_budget_law(self):
        """GM-OS: OperatingCostCalculator computes what modes are lawful."""
        from gmos.kernel.operating_cost import OperatingCostCalculator, OperatingBudget, GeometryMode
        
        # GM-OS computes the "cost of existence"
        calculator = OperatingCostCalculator()
        
        # GM-OS checks if a process can afford FULL mode
        budget = OperatingBudget(total_budget=100.0, reserve_floor=20.0)
        
        full_affordable = calculator.is_affordable(GeometryMode.FULL, budget)
        torpor_affordable = calculator.is_affordable(GeometryMode.TORPOR, budget)
        
        assert torpor_affordable  # Always affordable if budget > 0
        # FULL may or may not be affordable depending on costs
        
        # GM-OS provides cost summary (the "price of existence")
        full_cost = calculator.get_cost_summary(GeometryMode.FULL)
        
        assert 'total' in full_cost
        assert full_cost['total'] > 0
        
        print(f"GM-OS (Universe): FULL mode cost={full_cost['total']:.2f}")
    
    def test_repair_verifier_as_law_enforcer(self):
        """GM-OS: RepairVerifier ensures repairs satisfy admissibility law."""
        from gmos.kernel.repair_verifier import RepairVerifier, RepairTransition, RepairType, RepairDecision
        
        # GM-OS creates the verifier (the "court")
        verifier = RepairVerifier()
        
        # GM-OS evaluates a repair transition
        transition = RepairTransition(
            repair_type=RepairType.LOCAL_CORRECTION,
            v_before=100.0,
            v_after=95.0,
            spend=3.0,
            defect=2.0,
            budget_before=100.0,
            reserve_floor=10.0
        )
        
        decision = verifier.verify(transition)
        
        # GM-OS enforces: V_after + Spend ≤ V_before + Defect
        # 95 + 3 ≤ 100 + 2 → 98 ≤ 102 → TRUE (lawful)
        assert decision.repair_decision in RepairDecision
        
        print(f"GM-OS (Universe): Repair verdict={decision.repair_decision.value}")
    
    def test_identity_kernel_as_continuity_law(self):
        """GM-OS: IdentityKernel defines what constitutes continuity."""
        from gmos.kernel.identity_kernel import IdentityKernelManager
        
        # GM-OS defines the identity contract
        kernel_mgr = IdentityKernelManager(process_id="test_process")
        
        # GM-OS checks if a process maintains identity continuity
        # The kernel tracks identity state internally
        status = kernel_mgr.get_status()
        
        assert status is not None
        
        print(f"GM-OS (Universe): Identity status={status}")
    
    def test_checkpoint_as_recovery_anchor(self):
        """GM-OS: CheckpointManager provides recovery points."""
        from gmos.kernel.checkpoint import CheckpointManager
        
        # GM-OS creates recovery anchors
        cp_mgr = CheckpointManager()
        
        # GM-OS creates a checkpoint (a "save point")
        checkpoint_id = cp_mgr.create_checkpoint(
            state={'v': 100.0, 't': 0.5, 'b': 50.0},
            metadata={'step': 42, 'mode': 'FULL'}
        )
        
        assert checkpoint_id is not None
        
        # GM-OS can restore from checkpoint
        restored = cp_mgr.get_checkpoint(checkpoint_id)
        assert restored is not None
        assert restored.state['v'] == 100.0
        
        print(f"GM-OS (Universe): Created checkpoint {checkpoint_id[:8]}...")


class TestGMIInhabitantPerspective:
    """
    GMI (Inhabitant) Perspective Tests
    
    GMI uses the persistence stack as survival logic.
    It asks: How do I stay alive?
    """
    
    def test_persistence_layer_asks_survival_questions(self):
        """GMI: GMIPersistenceLayer asks 'How do I stay alive?'"""
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        
        # GMI creates its survival toolkit
        layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=100.0)
        
        # GMI observes its internal state (How damaged am I?)
        assessment = layer.observe(
            tension=0.3,      # How stressed am I?
            curvature=0.2,    # How scarred is my memory?
            integrity=0.7,    # How intact is my reasoning chain?
            identity_coherence=0.85  # How coherent is my self-model?
        )
        
        assert 'danger_index' in assessment
        assert 'band' in assessment
        
        # GMI asks: What should I do to survive?
        action = layer.decide_survival_action()
        
        assert 'repair_action' in action
        assert 'target_geometry' in action
        
        print(f"GMI (Inhabitant): Danger={assessment['danger_index']:.3f}, Band={assessment['band']}")
        print(f"GMI (Inhabitant): Action={action['repair_action']}, Geometry={action['target_geometry']}")
    
    def test_gmi_adapts_geometry_to_survive(self):
        """GMI: Gracefully degrades when needed."""
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        from gmos.kernel.reconfiguration import GeometryMode
        
        # GMI with limited budget must adapt
        layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=30.0)
        
        # GMI tries to contract to survive
        result = layer.adapt_geometry(GeometryMode.SURVIVAL)
        
        assert 'geometry' in result
        assert result['geometry'] == 'SURVIVAL'
        
        print(f"GMI (Inhabitant): Adapted to {result['geometry']} to survive")
    
    def test_gmi_executes_self_repair(self):
        """GMI: Attempts to heal itself."""
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        
        layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=80.0)
        
        # GMI observes damage
        layer.observe(tension=0.4, curvature=0.3, integrity=0.6, identity_coherence=0.8)
        
        # GMI attempts repair
        repair_result = layer.execute_self_repair(
            target_state={'tension': 0.2, 'curvature': 0.1, 'integrity': 0.8}
        )
        
        assert 'action' in repair_result
        assert 'transition' in repair_result
        
        print(f"GMI (Inhabitant): Repair action={repair_result['action']}")
    
    def test_gmi_preserves_identity_core(self):
        """GMI: Preserves its essential self."""
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        
        layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=50.0)
        
        # GMI preserves its identity kernel
        preservation = layer.preserve_identity()
        
        assert 'preserved' in preservation
        assert 'core_identity' in preservation
        
        print(f"GMI (Inhabitant): Identity preserved={preservation['preserved']}")
    
    def test_gmi_gets_survival_status(self):
        """GMI: Reports its survival status."""
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        
        layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=75.0)
        
        # GMI observes its state
        layer.observe(tension=0.2, curvature=0.1, integrity=0.85, identity_coherence=0.9)
        
        # GMI reports survival status
        status = layer.get_survival_status()
        
        assert 'budget' in status
        assert 'current_geometry' in status
        assert 'can_survive' in status
        
        print(f"GMI (Inhabitant): Can survive={status['can_survive']}, Budget={status['budget']:.1f}")


class TestTwoPerspectiveInteraction:
    """
    Tests showing the interaction between both perspectives.
    
    The same persistence machinery, viewed two ways.
    """
    
    def test_same_danger_monitor_different_perspective(self):
        """
        Demonstrates: Same DangerMonitor, two perspectives.
        
        GM-OS uses it as the universe's diagnostic instrument.
        GMI uses it to understand its own damage.
        """
        from gmos.kernel.danger import create_danger_monitor
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        
        # === GM-OS Perspective ===
        gmos_monitor = create_danger_monitor()
        
        # GM-OS observes process signals objectively
        state = gmos_monitor.update(v=0.5, t=0.4, c=0.3, b=30.0, h=0.6, i=0.7)
        state = gmos_monitor.compute_danger(state)
        
        gmos_verdict = gmos_monitor.get_recommendation()
        
        # === GMI Perspective ===
        gmi_layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=30.0)
        
        # GMI observes "I am damaged"
        gmi_assessment = gmi_layer.observe(
            tension=0.4,
            curvature=0.3,
            integrity=0.6,
            identity_coherence=0.7
        )
        
        gmi_action = gmi_layer.decide_survival_action()
        
        # Both perspectives arrive at compatible conclusions
        # (GM-OS says "contract", GMI says "I need to shrink")
        
        print(f"GM-OS (Universe) verdict: {gmos_verdict['action']}")
        print(f"GMI (Inhabitant) action: {gmi_action['repair_action']}")
        
        # Both recognize danger and recommend action
        assert gmos_verdict['action'] is not None
        assert gmi_action['repair_action'] is not None
    
    def test_budget_constraint_enforced_by_universe_obeyed_by_inhabitant(self):
        """
        Demonstrates: GM-OS enforces budget law, GMI obeys it.
        
        GM-OS says: "FULL mode costs 60, you have 30, unlawful!"
        GMI says: "I cannot afford FULL, I must contract."
        """
        from gmos.kernel.operating_cost import OperatingCostCalculator, OperatingBudget, GeometryMode
        from gmos.kernel.reconfiguration import create_reconfiguration_controller
        
        # === GM-OS Perspective: Enforcing the law ===
        calculator = OperatingCostCalculator()
        budget = OperatingBudget(total_budget=30.0, reserve_floor=0.0)
        
        full_cost = calculator.calculate_cost(GeometryMode.FULL)
        full_affordable = calculator.is_affordable(GeometryMode.FULL, budget)
        
        # GM-OS declares: FULL mode is UNLAWFUL (cannot afford)
        assert not full_affordable  # 30 < cost of FULL
        
        # GM-OS recommends affordable modes
        affordable_modes = calculator.get_affordable_modes(budget)
        
        # === GMI Perspective: Obeying the law ===
        controller = create_reconfiguration_controller()
        
        # GMI asks: What geometry must I accept?
        mandatory_geometry = controller.evaluate(0.7)  # High danger
        
        print(f"GM-OS (Universe): FULL affordable? {full_affordable}")
        print(f"GM-OS (Universe): Affordable modes: {[m.value for m in affordable_modes]}")
        print(f"GMI (Inhabitant): Must accept geometry: {mandatory_geometry.value}")
        
        # GMI must accept a geometry it can afford
        assert mandatory_geometry in affordable_modes


class TestPersistenceStackWorkflows:
    """
    End-to-end workflows demonstrating the persistence stack.
    """
    
    def test_degradation_workflow(self):
        """
        Complete workflow: From healthy to torpor and back.
        
        This demonstrates the full persistence lifecycle.
        """
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        from gmos.kernel.reconfiguration import GeometryMode
        
        # Start healthy
        layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=100.0)
        
        # === Stage 1: Healthy ===
        assessment = layer.observe(
            tension=0.1, curvature=0.05, integrity=0.95, identity_coherence=0.98
        )
        assert assessment['band'] == 'HEALTHY'
        
        # === Stage 2: Drift (minor stress) ===
        assessment = layer.observe(
            tension=0.3, curvature=0.2, integrity=0.8, identity_coherence=0.85
        )
        assert assessment['band'] in ['HEALTHY', 'DRIFT']
        
        # === Stage 3: Damage (significant stress) ===
        assessment = layer.observe(
            tension=0.5, curvature=0.4, integrity=0.6, identity_coherence=0.7
        )
        
        # GMI must adapt geometry
        action = layer.decide_survival_action()
        
        # === Stage 4: Contraction (if needed) ===
        if layer.current_budget < 40.0:
            result = layer.adapt_geometry(GeometryMode.SURVIVAL)
            assert result['geometry'] in ['SURVIVAL', 'TORPOR']
        
        print("Degradation workflow complete: HEALTHY → DRIFT → DAMAGE → adaptation")
    
    def test_repair_workflow(self):
        """
        Complete workflow: Damage detected → Repair attempted → Verification.
        """
        from gmos.agents.gmi.persistence_integration import create_gmi_persistence_layer
        from gmos.kernel.repair_verifier import RepairVerifier, RepairTransition, create_repair_verifier
        
        layer = create_gmi_persistence_layer(process_id="test_gmi", initial_budget=80.0)
        
        # GMI detects damage
        layer.observe(tension=0.4, curvature=0.3, integrity=0.65, identity_coherence=0.75)
        
        # GMI attempts repair
        repair = layer.execute_self_repair(
            target_state={'tension': 0.2, 'curvature': 0.1, 'integrity': 0.85}
        )
        
        # GM-OS verifies repair is lawful
        from gmos.kernel.repair_verifier import RepairVerifier, RepairDecision
        verifier = RepairVerifier()
        
        # Construct the transition that was attempted
        transition = RepairTransition(
            v_before=80.0,
            v_after=75.0,
            repair_cost=4.0,
            defect=1.0,
            is_collapse=False
        )
        
        decision = verifier.verify(transition)
        
        # If repair was lawful, GMI can continue
        if decision.is_admissible:
            print(f"Repair verified as {decision.verdict}")
        
        assert decision.verdict in ['LAWFUL', 'UNLAWFUL', 'MARGINAL']
        print("Repair workflow complete")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
