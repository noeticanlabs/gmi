"""
Unified Persistence System for GM-OS.

Integrates all self-repair components into a single cohesive system:
- DangerMonitor (immune system)
- RepairController (repair actions)
- IdentityKernelManager (identity spine)
- ReconfigurationController (adaptive geometry)
- OperatingCostCalculator (cost management)
- CheckpointManager (recovery)
- RepairVerifier (admissibility)

This provides the complete self-healing architecture per the Self-Repair Model,
Identity Kernel Model, and Adaptive Reconfiguration Model.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any, Callable
from enum import Enum
import time

# Import all components
from gmos.kernel.danger import DangerMonitor, DangerBand, DangerState, create_danger_monitor
from gmos.kernel.repair_controller import RepairController, RepairAction, RepairContext, create_repair_controller
from gmos.kernel.identity_kernel import IdentityKernelManager, IdentityKernel, IdentityStatus, create_identity_kernel
from gmos.kernel.reconfiguration import GeometryMode, ReconfigurationController, create_reconfiguration_controller
from gmos.kernel.operating_cost import OperatingCostCalculator, OperatingBudget
from gmos.kernel.checkpoint import CheckpointManager, Checkpoint, create_checkpoint_manager
from gmos.kernel.repair_verifier import RepairVerifier, RepairTransition, RepairType, RepairDecision, create_repair_verifier
from gmos.kernel.integrity_scorer import IntegrityScorer


class SystemState(Enum):
    """Overall system state."""
    HEALTHY = "healthy"
    DRIFTING = "drifting"
    DAMAGED = "damaged"
    CRITICAL = "critical"
    REPAIRING = "repairing"
    RECONFIGURING = "reconfiguring"
    TORPOR = "torpor"


@dataclass
class UnifiedPersistenceState:
    """Current state of the unified persistence system."""
    # Danger state
    danger_index: float = 0.0
    danger_band: DangerBand = DangerBand.HEALTHY
    
    # Geometry
    geometry_mode: GeometryMode = GeometryMode.FULL
    
    # Identity
    identity_status: IdentityStatus = IdentityStatus.INTACT
    
    # Budget
    current_budget: float = 100.0
    reserve_floor: float = 10.0
    available_budget: float = 90.0
    
    # System state
    system_state: SystemState = SystemState.HEALTHY
    
    # Timestamps
    last_danger_update: float = 0.0
    last_repair: float = 0.0
    last_reconfiguration: float = 0.0


class UnifiedPersistenceSystem:
    """
    Complete self-healing system integrating all components.
    
    This is the "organism" that:
    - Detects damage (DangerMonitor)
    - Decides repair actions (RepairController)
    - Preserves identity (IdentityKernelManager)
    - Adapts geometry (ReconfigurationController)
    - Manages costs (OperatingCostCalculator)
    - Creates checkpoints (CheckpointManager)
    - Verifies legality (RepairVerifier)
    """
    
    def __init__(
        self,
        process_id: str,
        initial_budget: float = 100.0,
        reserve_floor: float = 10.0,
        v0_1_mode: bool = False
    ):
        """
        Initialize unified persistence system.
        
        Args:
            process_id: Process to manage
            initial_budget: Starting budget
            reserve_floor: Protected reserve
            v0_1_mode: Use minimal 4-signal mode
        """
        self.process_id = process_id
        self.state = UnifiedPersistenceState(
            current_budget=initial_budget,
            reserve_floor=reserve_floor,
            available_budget=initial_budget - reserve_floor
        )
        
        # Create all components
        self.danger_monitor = create_danger_monitor(
            v0_1_mode=v0_1_mode,
            budget_reserve=reserve_floor,
            budget_max=initial_budget
        )
        
        self.repair_controller = create_repair_controller(
            danger_monitor=self.danger_monitor,
            v0_1_mode=v0_1_mode
        )
        
        self.identity_manager = IdentityKernelManager()
        self.identity_manager.create_kernel(
            process_id=process_id,
            genesis_receipt_hash="",
            reserve_floor=reserve_floor
        )
        
        self.reconfig_controller = create_reconfiguration_controller(
            danger_monitor=self.danger_monitor,
            v0_1_mode=v0_1_mode
        )
        
        self.cost_calculator = OperatingCostCalculator()
        
        self.checkpoint_manager = create_checkpoint_manager(
            max_checkpoints=10,
            checkpoint_interval=60.0
        )
        
        self.repair_verifier = create_repair_verifier(
            enable_kernel_check=True,
            enable_identity_check=True
        )
        
        self.integrity_scorer = IntegrityScorer()
        
        # Callbacks
        self._on_state_change: Optional[Callable] = None
        self._on_repair: Optional[Callable] = None
        self._on_reconfigure: Optional[Callable] = None
    
    def update(
        self,
        v: float = 0.0,
        t: float = 0.0,
        c: float = 0.0,
        b: Optional[float] = None,
        h: float = 1.0,
        i: float = 1.0
    ) -> UnifiedPersistenceState:
        """
        Update system state from observables.
        
        Args:
            v: Risk/violation
            t: Tension
            c: Curvature
            b: Budget (uses current if None)
            h: Integrity (0-1)
            i: Identity coherence (0-1)
            
        Returns:
            Updated UnifiedPersistenceState
        """
        # Update budget if provided
        if b is not None:
            self.state.current_budget = b
            self.state.available_budget = max(0, b - self.state.reserve_floor)
        
        # Update danger monitor
        danger_state = self.danger_monitor.update(
            v=v, t=t, c=c, b=self.state.current_budget, h=h, i=i
        )
        
        self.state.danger_index = danger_state.danger_index
        self.state.danger_band = danger_state.band
        self.state.last_danger_update = time.time()
        
        # Update system state based on danger
        self._update_system_state()
        
        return self.state
    
    def _update_system_state(self) -> None:
        """Update overall system state from components."""
        band = self.state.danger_band
        
        if band == DangerBand.HEALTHY:
            self.state.system_state = SystemState.HEALTHY
        elif band == DangerBand.DRIFT:
            self.state.system_state = SystemState.DRIFTING
        elif band == DangerBand.DAMAGE:
            self.state.system_state = SystemState.DAMAGED
        elif band == DangerBand.CRITICAL:
            self.state.system_state = SystemState.CRITICAL
        elif band == DangerBand.COLLAPSE:
            self.state.system_state = SystemState.TORPOR
    
    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate system and get recommendations.
        
        Returns:
            Dictionary with evaluation and recommendations
        """
        # Get danger recommendation
        danger_rec = self.danger_monitor.get_recommendation()
        
        # Evaluate reconfiguration need
        target_mode = self.reconfig_controller.evaluate(self.state.danger_index)
        
        # Check affordability
        budget = OperatingBudget(
            total_budget=self.state.current_budget,
            reserve_floor=self.state.reserve_floor
        )
        affordable_modes = self.cost_calculator.get_affordable_modes(budget)
        
        # Get identity status
        identity_status = self.identity_manager.get_status(self.process_id)
        
        return {
            "system_state": self.state.system_state.value,
            "danger": {
                "index": self.state.danger_index,
                "band": self.state.danger_band.value,
                "recommendation": danger_rec
            },
            "geometry": {
                "current": self.state.geometry_mode.value,
                "target": target_mode.value,
                "affordable_modes": [m.value for m in affordable_modes]
            },
            "identity": {
                "status": identity_status.value if identity_status else "unknown"
            },
            "budget": {
                "current": self.state.current_budget,
                "available": self.state.available_budget,
                "reserve": self.state.reserve_floor
            }
        }
    
    def execute_repair(self) -> Dict[str, Any]:
        """
        Execute repair if needed.
        
        Returns:
            Repair result
        """
        # Check if repair needed
        if not self.danger_monitor.should_repair():
            return {"action": "none", "reason": "no_repair_needed"}
        
        # Get danger state
        if not self.danger_monitor._history:
            return {"action": "none", "reason": "no_danger_data"}
        
        danger_state = self.danger_monitor._history[-1]
        
        # Create repair context
        context = RepairContext(
            process_id=self.process_id,
            current_state={},
            danger_state=danger_state,
            available_budget=self.state.current_budget,
            reserve_floor=self.state.reserve_floor
        )
        
        # Execute repair
        result = self.repair_controller.execute(context)
        
        self.state.last_repair = time.time()
        self.state.system_state = SystemState.REPAIRING
        
        return {
            "action": result.action.value,
            "success": result.success,
            "message": result.message,
            "delta_b": result.delta_b
        }
    
    def execute_reconfiguration(self) -> Dict[str, Any]:
        """
        Execute reconfiguration if needed.
        
        Returns:
            Reconfiguration result
        """
        # Evaluate target mode
        target_mode = self.reconfig_controller.evaluate(self.state.danger_index)
        
        # Check if transition needed
        if target_mode == self.state.geometry_mode:
            return {"action": "none", "reason": "no_reconfiguration_needed"}
        
        # Check affordability
        budget = OperatingBudget(
            total_budget=self.state.current_budget,
            reserve_floor=self.state.reserve_floor
        )
        
        if not self.cost_calculator.is_affordable(target_mode, budget):
            # Can't afford target, find lowest affordable
            min_affordable = self.cost_calculator.get_minimum_affordable_mode(budget)
            if min_affordable:
                target_mode = min_affordable
        
        # Execute transition
        success = self.reconfig_controller.transition_to(target_mode)
        
        if success:
            self.state.geometry_mode = target_mode
            self.state.last_reconfiguration = time.time()
            self.state.system_state = SystemState.RECONFIGURING
        
        return {
            "action": "transition" if success else "failed",
            "from": self.reconfig_controller.state.current_mode.value if not success else self.state.geometry_mode.value,
            "to": target_mode.value,
            "cost_multipliers": self.reconfig_controller.get_cost_multipliers()
        }
    
    def create_checkpoint(self) -> Optional[Checkpoint]:
        """Create checkpoint if needed."""
        # Get kernel for checkpoint
        kernel = self.identity_manager.get_kernel(self.process_id)
        if kernel is None:
            return None
        
        return self.checkpoint_manager.create_checkpoint(
            process_id=self.process_id,
            state_hash=kernel.chain_digest,
            state_data={"budget": self.state.current_budget},
            identity_kernel_hash=kernel.compute_hash(),
            chain_digest=kernel.chain_digest,
            policy_hash=kernel.policy_hash
        )
    
    def verify_repair_legality(
        self,
        v_before: float,
        v_after: float,
        spend: float,
        defect: float
    ) -> bool:
        """
        Verify a proposed repair is legally admissible.
        
        Args:
            v_before: Potential before
            v_after: Potential after
            spend: Repair cost
            defect: Defect from repair
            
        Returns:
            True if repair is lawful
        """
        transition = RepairTransition(
            repair_type=RepairType.TARGETED_REPAIR,
            v_before=v_before,
            v_after=v_after,
            spend=spend,
            defect=defect,
            budget_before=self.state.current_budget,
            reserve_floor=self.state.reserve_floor,
            kernel_preserved=True,
            identity_deformation=0.0
        )
        
        result = self.repair_verifier.verify(transition)
        return result.is_lawful
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        return {
            "process_id": self.process_id,
            "system_state": self.state.system_state.value,
            "danger": {
                "index": self.state.danger_index,
                "band": self.state.danger_band.name
            },
            "geometry": {
                "mode": self.state.geometry_mode.value
            },
            "budget": {
                "current": self.state.current_budget,
                "available": self.state.available_budget,
                "reserve": self.state.reserve_floor
            },
            "identity": {
                "status": self.identity_manager.get_status(self.process_id).value 
                         if self.identity_manager.get_status(self.process_id) else "unknown"
            }
        }
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable] = None,
        on_repair: Optional[Callable] = None,
        on_reconfigure: Optional[Callable] = None
    ) -> None:
        """Set system callbacks."""
        self._on_state_change = on_state_change
        self._on_repair = on_repair
        self._on_reconfigure = on_reconfigure


def create_unified_persistence_system(
    process_id: str,
    initial_budget: float = 100.0,
    reserve_floor: float = 10.0,
    v0_1_mode: bool = False
) -> UnifiedPersistenceSystem:
    """
    Factory function to create unified persistence system.
    
    Args:
        process_id: Process to manage
        initial_budget: Starting budget
        reserve_floor: Protected reserve
        v0_1_mode: Use minimal mode
        
    Returns:
        Configured UnifiedPersistenceSystem
    """
    return UnifiedPersistenceSystem(
        process_id=process_id,
        initial_budget=initial_budget,
        reserve_floor=reserve_floor,
        v0_1_mode=v0_1_mode
    )
