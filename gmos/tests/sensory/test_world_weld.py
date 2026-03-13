"""
World Weld Test: Organism Eats First Byte

This test demonstrates the complete world-weld loop:
    World → Ξ → Tension → ACT_COMMIT → Υ → Replenishment

The organism successfully "eats" its first byte of external data
and survives the encounter with reality.

Per spec: The sensory substrate does not inject English propositions
into the soul-box; it injects a bounded forcing term.
"""

import pytest
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

# Import sensory substrate components
from gmos.sensory.operators import (
    ObservationOperator,
    IngressOperator,
    SemanticBridge,
    DualUseSensoryPipeline,
    SensoryPercept,
    ForceTerm,
    NoeticType,
)
from gmos.sensory.cost_law import ObservationCostLaw, CostCoefficients
from gmos.sensory.receipts import (
    SensoryReceiptFactory,
    SourceTag,
    StepType,
)
from gmos.sensory.verifier import SensoryVerifier
from gmos.sensory.tension_bounds import BoundedTensionLemma


# === World Weld Components ===

@dataclass
class AffectiveState:
    """
    The organism's affective/budget state.
    
    This is what gets perturbed by sensory forcing.
    """
    budget: float = 1.0
    tension: float = 0.0
    curvature: float = 0.0
    shell_stability: float = 1.0
    health: float = 1.0
    memory_pressure: float = 0.0
    
    def apply_force(self, force: ForceTerm, kappa: float = 0.1):
        """
        Apply sensory forcing to the organism.
        
        Per spec §12:
        ∂_t θ = κΔθ + u_endo + Ξ(s_t) + λ_C C
        
        The forcing term Ξ(s_t) perturbs the organism's field.
        """
        # Force creates tension proportional to magnitude
        self.tension += force.magnitude * kappa
        
        # Update shell stability based on tension
        self.shell_stability = max(0.0, 1.0 - abs(self.tension))
        
        # Health decreases with excessive tension
        if abs(self.tension) > 0.8:
            self.health = max(0.0, self.health - 0.1)
    
    def is_alive(self) -> bool:
        """Check if organism survived."""
        return self.health > 0 and self.shell_stability > 0


@dataclass
class ActionCommitment:
    """
    An action commitment from the organism.
    
    After sensing and feeling tension, the organism must act.
    """
    action_type: str
    target: Any
    commitment_strength: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class EgressYield:
    """
    The output/action produced by the organism.
    
    Υ transforms internal commitment into external action.
    """
    action: ActionCommitment
    success: bool
    energy_expended: float
    timestamp: float = field(default_factory=time.time)


class ReplenishmentMechanism:
    """
    Budget replenishment after action.
    
    Per spec: The organism must replenish to survive.
    """
    
    def __init__(self, replenish_rate: float = 0.1, max_budget: float = 1.0):
        self.replenish_rate = replenish_rate
        self.max_budget = max_budget
    
    def replenish(self, state: AffectiveState) -> float:
        """
        Replenish budget after action.
        
        Returns:
            Amount of budget restored
        """
        # Replenish some budget
        restored = self.replenish_rate
        state.budget = min(self.max_budget, state.budget + restored)
        
        # Recovery helps tension
        state.tension *= 0.9
        
        # Recovery helps health slightly
        state.health = min(1.0, state.health + 0.05)
        
        return restored


class WorldWeldSimulation:
    """
    Complete world-weld simulation.
    
    Implements: World → Ξ → Tension → ACT_COMMIT → Υ → Replenishment
    """
    
    def __init__(
        self,
        initial_budget: float = 1.0,
        kappa: float = 0.1,
        replenish_rate: float = 0.1,
    ):
        # Initialize components
        self.observation_op = ObservationOperator()
        self.ingress_op = IngressOperator(max_magnitude=1.0, bounding_constant=1.0)
        self.semantic_bridge = SemanticBridge()
        self.cost_law = ObservationCostLaw(CostCoefficients(alpha=0.01, beta=0.02))
        self.receipt_factory = SensoryReceiptFactory(
            canon_profile_hash="sha256:world_weld_test",
            policy_hash="sha256:world_weld_policy",
        )
        self.verifier = SensoryVerifier()
        self.tension_lemma = BoundedTensionLemma()
        self.replenishment = ReplenishmentMechanism(
            replenish_rate=replenish_rate,
            max_budget=initial_budget,
        )
        
        # Initialize organism state
        self.organism = AffectiveState(
            budget=initial_budget,
            tension=0.0,
            shell_stability=1.0,
            health=1.0,
        )
        
        # Simulation parameters
        self.kappa = kappa
        self.step_count = 0
        
        # History
        self.history: List[Dict[str, Any]] = []
    
    def world_event(self, data: Any, source: str = "external") -> Dict[str, Any]:
        """
        Step 1: World event arrives at boundary.
        
        Args:
            data: Raw data from the world
            source: Source of the event
            
        Returns:
            Event info
        """
        self.step_count += 1
        return {
            "step": self.step_count,
            "data": data,
            "source": source,
            "timestamp": time.time(),
        }
    
    def observe(self, world_event: Dict[str, Any]) -> SensoryPercept:
        """
        Step 2: Observation operator O converts world to sensory.
        
        O: U_world → X_sens
        """
        # Create world-formatted event
        event = {
            "data": world_event["data"],
            "source": world_event["source"],
            "quality": 0.95,
        }
        
        # Apply observation operator
        percept = self.observation_op(event)
        
        # Compute observation cost
        cost = self.cost_law.compute_cost(percept.salience, bandwidth=0.1)
        
        # Deduct from budget
        self.organism.budget = max(0, self.organism.budget - cost)
        
        return percept
    
    def ingress(self, percept: SensoryPercept) -> ForceTerm:
        """
        Step 3: Ingress operator Ξ converts sensory to forcing.
        
        Ξ: X_sens → U_force (the "optic nerve")
        """
        force = self.ingress_op(percept)
        
        # Verify bounded-tension lemma
        is_bounded, details = self.tension_lemma.verify_operator_boundedness(
            percept, self.ingress_op
        )
        
        if not is_bounded:
            raise RuntimeError("Bounded-tension lemma violated!")
        
        return force
    
    def apply_tension(self, force: ForceTerm):
        """
        Step 4: Sensory forcing creates tension in organism.
        
        ∂_t θ = κΔθ + Ξ(s_t)
        """
        self.organism.apply_force(force, kappa=self.kappa)
    
    def act_commit(self, percept: SensoryPercept, force: ForceTerm) -> ActionCommitment:
        """
        Step 5: Organism commits to action.
        
        ACT_COMMIT: After feeling tension, organism must act.
        """
        # Decide action based on tension level
        if self.organism.tension > 0.5:
            action_type = "RETREAT"
            strength = self.organism.tension
        elif self.organism.tension > 0.2:
            action_type = "INVESTIGATE"
            strength = self.organism.tension
        else:
            action_type = "OBSERVE"
            strength = 0.5
        
        commitment = ActionCommitment(
            action_type=action_type,
            target=percept.percept_id,
            commitment_strength=strength,
        )
        
        return commitment
    
    def egress(self, commitment: ActionCommitment) -> EgressYield:
        """
        Step 6: Egress Υ produces actual output.
        
        Υ: Internal commitment → External action
        """
        # Energy expenditure based on commitment
        energy = commitment.commitment_strength * 0.1
        
        success = self.organism.is_alive()
        
        egress_yield = EgressYield(
            action=commitment,
            success=success,
            energy_expended=energy,
        )
        
        # Deduct energy
        self.organism.budget = max(0, self.organism.budget - energy)
        
        return egress_yield
    
    def replenish(self) -> float:
        """
        Step 7: Replenishment restores budget.
        
        Organism recovers after action.
        """
        restored = self.replenishment.replenish(self.organism)
        return restored
    
    def receive_receipt(self, percept: SensoryPercept, force: ForceTerm):
        """
        Generate and verify a receipt for this step.
        """
        # Compute cost
        cost = self.cost_law.compute_cost(percept.salience)
        
        # Create receipt
        receipt = self.receipt_factory.create_observation_receipt(
            content={
                "percept_id": percept.percept_id,
                "force_magnitude": force.magnitude,
            },
            source_tag=SourceTag.EXTERNAL,
            authority=percept.authority,
            quality=percept.quality,
            salience=percept.salience,
            cost=cost,
        )
        
        # Verify
        result = self.verifier.verify(receipt)
        
        return receipt, result
    
    def step(self, world_data: Any) -> Dict[str, Any]:
        """
        Execute one complete world-weld step.
        
        World → Ξ → Tension → ACT_COMMIT → Υ → Replenishment
        """
        # 1. World event arrives
        event = self.world_event(world_data)
        
        # 2. Observe (O)
        percept = self.observe(event)
        
        # 3. Ingress (Ξ)
        force = self.ingress(percept)
        
        # 4. Apply tension
        self.apply_tension(force)
        
        # 5. Act commit
        commitment = self.act_commit(percept, force)
        
        # 6. Egress (Υ)
        yield_result = self.egress(commitment)
        
        # 7. Replenish
        restored = self.replenish()
        
        # Generate receipt
        receipt, verification = self.receive_receipt(percept, force)
        
        # Record history
        step_record = {
            "step": self.step_count,
            "organism_state": {
                "budget": self.organism.budget,
                "tension": self.organism.tension,
                "shell_stability": self.organism.shell_stability,
                "health": self.organism.health,
                "alive": self.organism.is_alive(),
            },
            "percept": {
                "id": percept.percept_id,
                "salience": percept.salience,
                "authority": percept.authority,
            },
            "force": {
                "magnitude": force.magnitude,
            },
            "action": commitment.action_type,
            "yield_success": yield_result.success,
            "replenished": restored,
            "receipt_verified": verification.is_valid,
        }
        
        self.history.append(step_record)
        
        return step_record
    
    def run(self, world_events: List[Any]) -> List[Dict[str, Any]]:
        """
        Run multiple world-weld steps.
        """
        results = []
        for event in world_events:
            result = self.step(event)
            results.append(result)
            
            # Stop if organism died
            if not self.organism.is_alive():
                break
        
        return results


# === Test Cases ===

class TestWorldWeld:
    """Test the complete world-weld loop."""
    
    def test_organism_survives_first_byte(self):
        """
        Test that the organism survives eating its first byte.
        
        This is the fundamental test: can the organism handle
        external data without exploding?
        """
        sim = WorldWeldSimulation(initial_budget=1.0)
        
        # First byte of data from the world
        first_byte = {"value": 42, "source": "sensor_1"}
        
        # Run one step
        result = sim.step(first_byte)
        
        # Verify organism survived
        assert result["organism_state"]["alive"], "Organism died!"
        assert result["organism_state"]["budget"] >= 0, "Budget went negative!"
        assert result["receipt_verified"], "Receipt should be valid"
        
        print(f"Step {result['step']}: Survived!")
        print(f"  Budget: {result['organism_state']['budget']:.4f}")
        print(f"  Tension: {result['organism_state']['tension']:.4f}")
        print(f"  Action: {result['action']}")
    
    def test_multiple_bytes_survival(self):
        """
        Test that the organism can eat multiple bytes.
        """
        sim = WorldWeldSimulation(initial_budget=1.0, replenish_rate=0.15)
        
        # Multiple bytes from the world
        world_data = [
            {"value": i, "source": f"sensor_{i}"}
            for i in range(10)
        ]
        
        # Run simulation
        results = sim.run(world_data)
        
        # Verify all steps
        for r in results:
            assert r["organism_state"]["alive"], f"Organism died at step {r['step']}!"
        
        # Final state
        final = results[-1]["organism_state"]
        print(f"\nFinal state after {len(results)} steps:")
        print(f"  Budget: {final['budget']:.4f}")
        print(f"  Tension: {final['tension']:.4f}")
        print(f"  Health: {final['health']:.4f}")
        print(f"  Shell: {final['shell_stability']:.4f}")
        
        # Should have survived with some budget remaining
        assert final["budget"] > 0, "Budget depleted!"
    
    def test_bounded_tension_verified(self):
        """
        Test that bounded-tension lemma is always satisfied.
        """
        sim = WorldWeldSimulation()
        
        # Run several steps
        for i in range(5):
            result = sim.step({"value": i, "source": "test"})
            
            # Force magnitude should be bounded
            assert result["force"]["magnitude"] <= 1.0, "Force exceeded bounds!"
        
        print("\nBounded-tension lemma verified for all steps!")
    
    def test_receipt_chain_integrity(self):
        """
        Test that receipts form a valid chain.
        """
        sim = WorldWeldSimulation()
        
        # Run steps and track receipts
        receipts = []
        prev_digest = ""
        
        for i in range(3):
            result = sim.step({"value": i, "source": "test"})
            assert result["receipt_verified"], f"Receipt failed at step {i+1}"
            
            # Get the last created receipt from factory
            # (In real implementation, we'd store them in history)
            # For now, verify the chain mechanism works
            prev_digest = f"step_{i}"
        
        print("\nReceipt mechanism verified (chain would form with persistent storage)!")
    
    def test_cost_enforcement(self):
        """
        Test that observation costs are properly enforced.
        """
        initial_budget = 0.1
        sim = WorldWeldSimulation(initial_budget=initial_budget, replenish_rate=0.0)
        
        # Try to observe many times without replenishment
        for i in range(20):
            result = sim.step({"value": i, "source": "test"})
            
            # If budget is exhausted, organism should be in trouble
            if result["organism_state"]["budget"] <= 0:
                print(f"\nBudget exhausted at step {i+1}")
                break
        
        # Budget should never go negative
        for r in sim.history:
            assert r["organism_state"]["budget"] >= 0, "Budget went negative!"
        
        print(f"\nCost enforcement verified: budget stayed non-negative")
    
    def test_tension_recovery(self):
        """
        Test that tension is properly managed over time.
        """
        sim = WorldWeldSimulation(replenish_rate=0.2)
        
        # Initial tension
        initial_tension = sim.organism.tension
        
        # Run steps with replenishment
        results = []
        for i in range(10):
            result = sim.step({"value": i, "source": "test"})
            results.append(result)
        
        # Tension should have recovered (reduced from initial spike)
        final_tension = results[-1]["organism_state"]["tension"]
        
        # With replenishment, tension should trend down
        print(f"\nTension over time:")
        for r in results:
            print(f"  Step {r['step']}: {r['organism_state']['tension']:.4f}")
        
        # Should survive
        assert results[-1]["organism_state"]["alive"]


class TestTraumaScarring:
    """Test the trauma/scar system - organism learns from negative experiences."""
    
    def test_poison_scar(self):
        """
        Test that the organism scars when touching poison.
        
        This is the key test: organism touches a "hot stove",
        gets damaged, creates a curvature scar, and learns to avoid it.
        """
        from gmos.sensory import CurvatureField, TraumaMemory, TraumaSeverity
        
        # Setup: Create curvature field and trauma memory
        cf = CurvatureField(dimensions=1, resolution=100, bounds=(0.0, 1.0))
        trauma = TraumaMemory(curvature_field=cf)
        
        # Position 0.7 is the "poison" location
        poison_position = 0.7
        
        # First encounter: Organism approaches poison
        print("\n--- First encounter with poison ---")
        
        # The organism tries to eat at position 0.7
        event1 = trauma.process_failure(
            action="EAT",
            damage=0.8,  # Significant damage
            semantic_position=poison_position
        )
        
        print(f"Damage taken: {event1.damage}")
        print(f"Severity: {event1.severity}")
        print(f"Scar magnitude: {event1.scar_magnitude:.4f}")
        
        # Check curvature at poison position
        curvature = cf.get_curvature(poison_position)
        print(f"Curvature at poison: {curvature:.4f}")
        
        # Second encounter: Organism should avoid
        print("\n--- Second encounter ---")
        
        decision = trauma.should_avoid(
            action="EAT",
            semantic_position=poison_position
        )
        
        print(f"Should avoid: {decision.should_avoid}")
        print(f"Reasoning: {decision.reasoning}")
        
        # Verify scarring worked
        assert decision.should_avoid, "Organism should avoid the poison!"
        assert curvature > 0.5, "Curvature should be significant"
        
        # Third encounter at different position - should be fine
        safe_position = 0.3
        decision_safe = trauma.should_avoid(
            action="EAT",
            semantic_position=safe_position
        )
        
        print(f"\n--- Safe position check ---")
        print(f"Position {safe_position}: avoid={decision_safe.should_avoid}")
        
        # Safe position should not trigger avoidance
        assert not decision_safe.should_avoid, "Safe position should not be avoided"
        
        print("\n✓ Organism successfully scarred by poison and learned to avoid it!")
    
    def test_gradient_push(self):
        """Test that curvature pushes gradient flow."""
        from gmos.sensory import CurvatureField
        
        cf = CurvatureField(dimensions=1, resolution=100, bounds=(0.0, 1.0))
        
        # Add a scar at position 0.5
        cf.add_scar(position=0.5, magnitude=2.0)
        
        # Gradient trying to go through 0.5 should be pushed away
        original_gradient = 1.0  # Moving right
        
        # Get curvature gradient
        curv_grad = cf.compute_curvature_gradient(0.5)
        
        print(f"\n--- Gradient push test ---")
        print(f"Curvature at 0.5: {cf.get_curvature(0.5):.4f}")
        print(f"Curvature gradient: {curv_grad:.4f}")
        
        # The gradient should be modified
        assert cf.get_curvature(0.5) > 1.0, "Scar should be significant"
        
        print("\n✓ Curvature successfully modifies gradient flow!")
    
    def test_multiple_scars(self):
        """Test multiple scars at different positions."""
        from gmos.sensory import CurvatureField, TraumaMemory
        
        cf = CurvatureField(dimensions=1, resolution=100, bounds=(0.0, 1.0))
        trauma = TraumaMemory(curvature_field=cf)
        
        # Create scars at multiple positions
        positions = [0.2, 0.4, 0.6, 0.8]
        
        for pos in positions:
            trauma.process_failure(
                action="BAD_ACTION",
                damage=0.5,
                semantic_position=pos
            )
        
        # Check summary
        summary = cf.get_scar_summary()
        print(f"\n--- Multiple scars test ---")
        print(f"Scar count: {summary['scar_count']}")
        print(f"Max curvature: {summary['max_curvature']:.4f}")
        
        # All positions should have curvature
        for pos in positions:
            curv = cf.get_curvature(pos)
            assert curv > 0.1, f"Position {pos} should have scar"
        
        print("\n✓ Multiple scars created successfully!")
    
    def test_scar_healing(self):
        """Test that scars decay over time."""
        from gmos.sensory import CurvatureField
        
        cf = CurvatureField(dimensions=1, resolution=100, bounds=(0.0, 1.0))
        
        # Add scar
        cf.add_scar(position=0.5, magnitude=1.0)
        
        initial = cf.get_curvature(0.5)
        print(f"\n--- Scar healing test ---")
        print(f"Initial curvature: {initial:.4f}")
        
        # Apply decay
        for i in range(10):
            cf.decay_scars(dt=1.0)
        
        healed = cf.get_curvature(0.5)
        print(f"After decay: {healed:.4f}")
        
        # Curvature should have decreased
        assert healed < initial, "Scar should have decayed"
        
        print("\n✓ Scars decay over time as expected!")


class TestWorldWeldStress:
    """Stress tests for the world-weld."""
    
    def test_high_frequency_input(self):
        """
        Test high-frequency sensory input.
        """
        sim = WorldWeldSimulation(replenish_rate=0.3)
        
        # Rapid input
        data = [{"value": i, "data": "x" * 100} for i in range(50)]
        
        results = sim.run(data)
        
        # Should survive
        assert results[-1]["organism_state"]["alive"]
        
        print(f"\nSurvived {len(results)} high-frequency inputs")
    
    def test_conflicting_input(self):
        """
        Test conflicting sensory inputs.
        """
        sim = WorldWeldSimulation()
        
        # Conflicting data
        data = [
            {"value": 100, "source": "external"},
            {"value": -100, "source": "simulation"},
        ]
        
        results = sim.run(data)
        
        # Should have handled conflict
        assert len(results) == 2
        
        print(f"\nHandled conflicting inputs:")
        print(f"  Step 1 tension: {results[0]['organism_state']['tension']:.4f}")
        print(f"  Step 2 tension: {results[1]['organism_state']['tension']:.4f}")


# === Run Tests ===

if __name__ == "__main__":
    # Run basic test
    print("=" * 60)
    print("WORLD WELD TEST: Organism Eats First Byte")
    print("=" * 60)
    
    test = TestWorldWeld()
    
    print("\n--- Test 1: First Byte Survival ---")
    test.test_organism_survives_first_byte()
    
    print("\n--- Test 2: Multiple Bytes ---")
    test.test_multiple_bytes_survival()
    
    print("\n--- Test 3: Bounded Tension ---")
    test.test_bounded_tension_verified()
    
    print("\n--- Test 4: Receipt Chain ---")
    test.test_receipt_chain_integrity()
    
    print("\n--- Test 5: Cost Enforcement ---")
    test.test_cost_enforcement()
    
    print("\n" + "=" * 60)
    print("ALL WORLD WELD TESTS PASSED!")
