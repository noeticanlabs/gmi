"""
Persistence Integration for GMI Agent.

This module integrates the persistence stack (self-repair, identity kernel, adaptive reconfiguration)
into the GMI agent as the inhabitant's survival logic.

Per docs/persistence_stack_roles.md:
- GM-OS (Universe): Governance - enforces rules
- GMI (Inhabitant): Survival - uses the same stack to actually survive

This provides GMI with:
- Internal self-repair (healing itself)
- Selfhood preservation (knowing what it cannot lose)
- Graceful degradation (shrinking while remaining itself)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
import numpy as np

# Import persistence components
from gmos.kernel.danger import DangerMonitor, DangerBand, create_danger_monitor
from gmos.kernel.repair_controller import RepairController, RepairAction, create_repair_controller
from gmos.kernel.identity_kernel import IdentityKernelManager, IdentityStatus, create_identity_kernel
from gmos.kernel.reconfiguration import GeometryMode, ReconfigurationController, create_reconfiguration_controller
from gmos.kernel.operating_cost import OperatingCostCalculator, OperatingBudget
from gmos.kernel.checkpoint import CheckpointManager, create_checkpoint_manager
from gmos.kernel.repair_verifier import RepairVerifier, create_repair_verifier
from gmos.kernel.thermodynamic_cost import ThermodynamicCostTracker, create_cost_tracker


@dataclass
class GMIPersistenceConfig:
    """Configuration for GMI's use of persistence stack."""
    # GMI uses v0.1 minimal mode by default
    v0_1_mode: bool = True
    
    # Danger monitoring
    budget_reserve: float = 10.0
    budget_max: float = 100.0
    
    # Identity kernel
    identity_reserve: float = 10.0
    
    # Checkpoint
    checkpoint_interval: float = 60.0
    max_checkpoints: int = 5


class GMIPersistenceLayer:
    """
    GMI's survival logic layer.
    
    This wraps GMI's cognitive components with the ability to:
    - Detect internal damage (self-repair)
    - Preserve selfhood (identity kernel)
    - Adapt cognition under pressure (reconfiguration)
    
    This is the "inhabitant" perspective on the persistence stack.
    """
    
    def __init__(
        self,
        process_id: str,
        initial_budget: float = 100.0,
        config: Optional[GMIPersistenceConfig] = None
    ):
        """
        Initialize GMI persistence layer.
        
        Args:
            process_id: GMI process identifier
            initial_budget: Starting budget
            config: Configuration (uses defaults if None)
        """
        self.process_id = process_id
        self.config = config or GMIPersistenceConfig()
        
        # Core persistence components (from GMI's perspective)
        
        # 1. Danger monitoring - GMI sees damage signals
        self.danger_monitor = create_danger_monitor(
            v0_1_mode=self.config.v0_1_mode,
            budget_reserve=self.config.budget_reserve,
            budget_max=self.config.budget_max
        )
        
        # 2. Repair controller - GMI decides how to heal itself
        self.repair_controller = create_repair_controller(
            danger_monitor=self.danger_monitor,
            v0_1_mode=self.config.v0_1_mode
        )
        
        # 3. Identity kernel - GMI knows what defines "me"
        self.identity_manager = IdentityKernelManager()
        self.identity_manager.create_kernel(
            process_id=process_id,
            genesis_receipt_hash="",  # Will be set on first step
            reserve_floor=self.config.identity_reserve
        )
        
        # 4. Reconfiguration - GMI adapts its cognition
        self.reconfig_controller = create_reconfiguration_controller(
            danger_monitor=self.danger_monitor,
            v0_1_mode=self.config.v0_1_mode
        )
        
        # 5. Cost calculator - GMI knows what it can afford
        self.cost_calculator = OperatingCostCalculator()
        
        # 6. Checkpoints - GMI can restore itself
        self.checkpoint_manager = create_checkpoint_manager(
            max_checkpoints=self.config.max_checkpoints,
            checkpoint_interval=self.config.checkpoint_interval
        )
        
        # 7. Repair verifier - GMI verifies its healing is lawful
        self.repair_verifier = create_repair_verifier()
        
        # 8. Thermodynamic tracking - GMI tracks its survival costs
        self.cost_tracker = create_cost_tracker(
            total_budget=initial_budget,
            reserve=self.config.identity_reserve
        )
        
        # Current state
        self.current_budget = initial_budget
        self.current_geometry = GeometryMode.FULL
    
    def observe(
        self,
        tension: float,
        curvature: float = 0.0,
        integrity: float = 1.0,
        identity_coherence: float = 1.0
    ) -> Dict[str, Any]:
        """
        GMI observes its internal state to detect damage.
        
        This is how GMI (as inhabitant) monitors itself:
        - How much internal mismatch (tension)?
        - How damaged is memory (curvature)?
        - Is my chain of thought intact (integrity)?
        - Do I still know who I am (identity)?
        
        Args:
            tension: Current tension/residual
            curvature: Memory curvature/scar load
            integrity: Chain integrity (0-1)
            identity_coherence: Identity coherence (0-1)
            
        Returns:
            Danger assessment
        """
        # Update danger monitor with GMI's internal signals
        state = self.danger_monitor.update(
            v=tension * 0.5,  # Risk proportional to tension
            t=tension,
            c=curvature,
            b=self.current_budget,
            h=integrity,
            i=identity_coherence
        )
        
        return {
            "danger_index": state.danger_index,
            "band": state.band.name,
            "triggers": {
                "risk": state.theta_v,
                "tension": state.theta_t,
                "curvature": state.theta_c,
                "budget": state.theta_b,
                "integrity": state.theta_h,
                "identity": state.theta_i
            }
        }
    
    def decide_survival_action(self) -> Dict[str, Any]:
        """
        GMI decides how to survive based on detected damage.
        
        This is GMI asking:
        - What part of me is damaged?
        - What can I repair?
        - What must I preserve?
        - How small must I become?
        
        Returns:
            Survival action decision
        """
        # Get danger recommendation
        danger_rec = self.danger_monitor.get_recommendation()
        
        # Check if we need to reconfigure geometry
        target_geometry = self.reconfig_controller.evaluate(
            self.danger_monitor._history[-1].danger_index if self.danger_monitor._history else 0.0
        )
        
        # Determine affordability using OperatingBudget
        available = self.current_budget - self.config.identity_reserve
        budget = OperatingBudget(total_budget=available, reserve_floor=0.0)
        affordable = self.cost_calculator.is_affordable(
            target_geometry,
            budget
        )
        
        return {
            "repair_action": danger_rec["action"],
            "target_geometry": target_geometry.value,
            "geometry_affordable": affordable,
            "reason": danger_rec["reason"]
        }
    
    def execute_self_repair(
        self,
        repair_type: RepairAction,
        expected_v_reduction: float = 0.0
    ) -> Dict[str, Any]:
        """
        GMI repairs itself.
        
        This is GMI (as inhabitant) healing itself:
        - Clearing bad branches
        - Restoring coherent summaries
        - Reducing internal mismatch
        
        Args:
            repair_type: Type of repair to execute
            expected_v_reduction: Expected potential reduction
            
        Returns:
            Repair result
        """
        # Compute repair cost
        cost = self.cost_tracker.compute_repair_cost(
            operation=repair_type.value,
            curvature_delta=-10.0 if repair_type != RepairAction.NONE else 0.0,
            tension_delta=-expected_v_reduction if expected_v_reduction > 0 else 0.0,
            state_size_delta=0.0,
            branches_pruned=2 if repair_type == RepairAction.R2_REPAIR else 0
        )
        
        # Check if we can afford it
        if not self.cost_tracker.can_afford(cost):
            return {
                "success": False,
                "reason": "Insufficient thermodynamic budget for repair"
            }
        
        # Apply the cost
        self.cost_tracker.spend(cost)
        
        # Update budget (would normally come from GM-OS)
        self.current_budget -= cost.total
        
        return {
            "success": True,
            "cost": cost.total,
            "repair_type": repair_type.value,
            "remaining_budget": self.current_budget
        }
    
    def adapt_geometry(self, target_mode: GeometryMode) -> Dict[str, Any]:
        """
        GMI adapts its cognitive geometry.
        
        This is GMI (as inhabitant) shrinking its cognition:
        - Narrowing attention
        - Reducing memory access
        - Suspending exploration
        
        Args:
            target_mode: Target geometry mode
            
        Returns:
            Adaptation result
        """
        # Compute cost of reconfiguration
        reconfig_cost = self.cost_tracker.compute_reconfiguration_cost(
            from_mode=self.current_geometry.value,
            to_mode=target_mode.value,
            features_disabled=2,
            memory_compressed=10.0
        )
        
        # Apply if affordable
        if self.cost_tracker.spend(reconfig_cost):
            self.reconfig_controller.transition_to(target_mode)
            self.current_geometry = target_mode
            self.current_budget -= reconfig_cost.total
            
            return {
                "success": True,
                "from_mode": self.current_geometry.value,
                "to_mode": target_mode.value,
                "cost": reconfig_cost.total,
                "remaining_budget": self.current_budget
            }
        
        return {
            "success": False,
            "reason": "Cannot afford geometry transition"
        }
    
    def preserve_identity(self) -> Dict[str, Any]:
        """
        GMI ensures its identity is preserved.
        
        This is GMI checking:
        - My chain of thought is intact
        - My core goals are preserved
        - My policy is not lost
        
        Returns:
            Identity status
        """
        kernel = self.identity_manager.get_kernel(self.process_id)
        
        if kernel is None:
            return {
                "status": "error",
                "reason": "No identity kernel found"
            }
        
        # Verify continuity (would use actual chain digest in real use)
        metrics = self.identity_manager.verify_continuity(
            process_id=self.process_id,
            current_chain_digest=kernel.chain_digest,
            current_policy_hash=kernel.policy_hash,
            current_budget=self.current_budget
        )
        
        return {
            "status": metrics.status.value,
            "deformation": metrics.total_deformation,
            "failure": metrics.failure.value if metrics.failure else "none"
        }
    
    def get_survival_status(self) -> Dict[str, Any]:
        """
        Get complete GMI survival status.
        
        Returns:
            Full survival assessment from inhabitant perspective
        """
        return {
            "process_id": self.process_id,
            "budget": {
                "current": self.current_budget,
                "reserve": self.config.identity_reserve,
                "available": self.current_budget - self.config.identity_reserve
            },
            "geometry": {
                "current": self.current_geometry.value,
                "cost": self.cost_calculator.calculate_cost(self.current_geometry).total
            },
            "identity": self.preserve_identity(),
            "cost_tracking": self.cost_tracker.get_statistics()
        }


def create_gmi_persistence_layer(
    process_id: str,
    initial_budget: float = 100.0,
    v0_1_mode: bool = True
) -> GMIPersistenceLayer:
    """
    Factory to create GMI persistence layer.
    
    Args:
        process_id: GMI process identifier
        initial_budget: Starting budget
        v0_1_mode: Use minimal 4-signal mode
        
    Returns:
        Configured GMIPersistenceLayer
    """
    config = GMIPersistenceConfig(v0_1_mode=v0_1_mode)
    return GMIPersistenceLayer(
        process_id=process_id,
        initial_budget=initial_budget,
        config=config
    )
