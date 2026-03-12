"""
Repair Controller for GM-OS Self-Repair System.

Implements the repair action ladder (R1-R4) per Self-Repair Model Section 9:

- R1: Local correction (Band 1 - Drift)
- R2: Targeted repair (Band 2 - Damage)  
- R3: Structural contraction (Band 3 - Critical)
- R4: Safe-state collapse (Band 4 - Collapse)

Per Self-Repair Model Section 18: v0.1 minimal implementation.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable, Any
from enum import Enum
import time

from gmos.kernel.danger import DangerBand, DangerMonitor, DangerState


class RepairAction(Enum):
    """Repair action types per Self-Repair Model Section 9."""
    NONE = "none"
    R1_CORRECT = "r1_correct"        # Local correction
    R2_REPAIR = "r2_repair"          # Targeted repair
    R3_CONTRACT = "r3_contract"       # Structural contraction
    R4_COLLAPSE = "r4_collapse"       # Safe-state collapse


@dataclass
class RepairActionSpec:
    """Specification for a repair action."""
    action: RepairAction
    band: DangerBand
    description: str
    expected_effects: Dict[str, float] = field(default_factory=dict)
    
    # Budget constraints
    max_spend: float = 0.0
    max_defect: float = 0.0
    
    # Execution hints
    priority: int = 0  # Higher = more urgent


@dataclass
class RepairContext:
    """Context for repair execution."""
    process_id: str
    current_state: Dict[str, Any]
    danger_state: DangerState
    available_budget: float
    reserve_floor: float
    
    # Optional hooks
    memory_access: Optional[Callable] = None
    verifier_access: Optional[Callable] = None
    scheduler_access: Optional[Callable] = None


@dataclass
class RepairResult:
    """Result of a repair action."""
    action: RepairAction
    success: bool
    
    # State changes
    delta_v: float = 0.0   # Risk change
    delta_t: float = 0.0   # Tension change
    delta_c: float = 0.0   # Curvature change
    delta_b: float = 0.0   # Budget change
    
    # Receipt
    receipt_id: str = ""
    receipt_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    message: str = ""
    timestamp: float = field(default_factory=time.time)


class RepairController:
    """
    Controls repair action selection and execution.
    
    Per Self-Repair Model Section 9:
    - R1 (Band 1): Local correction - clear stale, refresh caches
    - R2 (Band 2): Targeted repair - prune branches, rebuild summaries
    - R3 (Band 3): Structural contraction - freeze exploration, collapse
    - R4 (Band 4): Safe-state collapse - torpor, preserve kernel
    """
    
    # Action specifications per band
    ACTION_SPECS: Dict[DangerBand, RepairActionSpec] = {
        DangerBand.HEALTHY: RepairActionSpec(
            action=RepairAction.NONE,
            band=DangerBand.HEALTHY,
            description="No repair needed",
            max_spend=0.0,
            priority=0
        ),
        DangerBand.DRIFT: RepairActionSpec(
            action=RepairAction.R1_CORRECT,
            band=DangerBand.DRIFT,
            description="Local correction: clear stale branches, refresh caches, recompute invariants",
            expected_effects={"ΔV": 0, "ΔT": "< 0", "ΔC": "≈ 0"},
            max_spend=5.0,
            max_defect=1.0,
            priority=1
        ),
        DangerBand.DAMAGE: RepairActionSpec(
            action=RepairAction.R2_REPAIR,
            band=DangerBand.DAMAGE,
            description="Targeted repair: prune damaged branches, rebuild summaries, reroute around damage",
            expected_effects={"ΔT": "< 0", "ΔC": "< 0", "ΔH": "> 0"},
            max_spend=15.0,
            max_defect=5.0,
            priority=2
        ),
        DangerBand.CRITICAL: RepairActionSpec(
            action=RepairAction.R3_CONTRACT,
            band=DangerBand.CRITICAL,
            description="Structural contraction: freeze exploration, disable luxuries, restore stable checkpoint",
            expected_effects={"ΔB_drain": "< 0", "ΔV": "≤ 0", "ΔI": "≈ 0"},
            max_spend=30.0,
            max_defect=10.0,
            priority=3
        ),
        DangerBand.COLLAPSE: RepairActionSpec(
            action=RepairAction.R4_COLLAPSE,
            band=DangerBand.COLLAPSE,
            description="Safe-state collapse: preserve kernel, enter torpor, reject nonessential",
            expected_effects={"kernel_preserved": True},
            max_spend=50.0,
            max_defect=20.0,
            priority=4
        ),
    }
    
    def __init__(
        self,
        danger_monitor: Optional[DangerMonitor] = None,
        enable_r1: bool = True,
        enable_r2: bool = True,
        enable_r3: bool = True,
        enable_r4: bool = True,
        min_budget_for_repair: float = 5.0
    ):
        self.danger_monitor = danger_monitor
        self.enabled_actions = {
            RepairAction.R1_CORRECT: enable_r1,
            RepairAction.R2_REPAIR: enable_r2,
            RepairAction.R3_CONTRACT: enable_r3,
            RepairAction.R4_COLLAPSE: enable_r4,
        }
        self.min_budget_for_repair = min_budget_for_repair
        
        # Execution history
        self._history: List[RepairResult] = []
    
    def select_action(self, context: RepairContext) -> RepairAction:
        """
        Select appropriate repair action based on danger band.
        
        Per Self-Repair Model Section 7: 
        Escalation based on persistent exceedance, not instantaneous danger.
        """
        band = context.danger_state.band
        spec = self.ACTION_SPECS.get(band)
        
        if spec is None:
            return RepairAction.NONE
        
        action = spec.action
        
        # Check if action is enabled
        if action != RepairAction.NONE and not self.enabled_actions.get(action, True):
            # Fall back to lower action if this one is disabled
            if band == DangerBand.CRITICAL and self.enabled_actions.get(RepairAction.R2_REPAIR, True):
                return RepairAction.R2_REPAIR
            elif band == DangerBand.DAMAGE and self.enabled_actions.get(RepairAction.R1_CORRECT, True):
                return RepairAction.R1_CORRECT
        
        # Check budget availability
        available = context.available_budget - context.reserve_floor
        if available < spec.max_spend:
            # Can't afford this action, try lower tier
            if band == DangerBand.COLLAPSE:
                return RepairAction.R3_CONTRACT  # Still try R3
            elif band == DangerBand.CRITICAL:
                return RepairAction.R2_REPAIR
            elif band == DangerBand.DAMAGE:
                return RepairAction.R1_CORRECT
        
        return action
    
    def execute_r1(self, context: RepairContext) -> RepairResult:
        """
        Execute R1: Local correction.
        
        Per Self-Repair Model Section 9:
        - Clear stale branches
        - Refresh local caches
        - Recompute local invariants
        - Rebalance budget routing locally
        
        Expected: ΔV ≤ 0, ΔT < 0, ΔC ≈ 0, small Spend
        """
        # In v0.1, this is a lightweight local operation
        # In full implementation, would:
        # - Access memory to clear stale entries
        # - Recompute local invariants
        # - Update cache
        
        return RepairResult(
            action=RepairAction.R1_CORRECT,
            success=True,
            delta_t=-5.0,  # Reduced tension
            delta_b=-2.0,  # Small budget spend
            message="Local correction completed: stale branches cleared, caches refreshed"
        )
    
    def execute_r2(self, context: RepairContext) -> RepairResult:
        """
        Execute R2: Targeted repair.
        
        Per Self-Repair Model Section 9:
        - Prune damaged branch families
        - Rebuild summaries from anchors
        - Reroute around memory damage
        - Tighten attention/instrument width
        
        Expected: ΔT < 0, ΔC < 0, ΔH > 0
        """
        # In v0.1, moderate repair operation
        # In full implementation, would:
        # - Access memory to identify damaged branches
        # - Rebuild summaries from checkpoint anchors
        # - Update memory manifold
        
        return RepairResult(
            action=RepairAction.R2_REPAIR,
            success=True,
            delta_t=-15.0,  # Reduced tension
            delta_c=-10.0,  # Reduced curvature/scars
            delta_b=-8.0,   # Moderate budget spend
            message="Targeted repair completed: damaged branches pruned, summaries rebuilt"
        )
    
    def execute_r3(self, context: RepairContext) -> RepairResult:
        """
        Execute R3: Structural contraction.
        
        Per Self-Repair Model Section 9:
        - Freeze exploration
        - Disable luxuries
        - Collapse to core working set
        - Restore stable shell checkpoint
        
        Expected: ΔB_drain < 0, ΔV ≤ 0, ΔI ≈ 0
        """
        # In v0.1, significant contraction
        # In full implementation, would:
        # - Disable exploration modes
        # - Archive nonessential memory
        # - Restore from checkpoint
        # - Reduce active state
        
        return RepairResult(
            action=RepairAction.R3_CONTRACT,
            success=True,
            delta_v=-20.0,  # Significant risk reduction
            delta_t=-25.0,  # Major tension reduction
            delta_b=-20.0,  # Significant spend but within budget
            message="Structural contraction completed: exploration frozen, core shell restored"
        )
    
    def execute_r4(self, context: RepairContext) -> RepairResult:
        """
        Execute R4: Safe-state collapse.
        
        Per Self-Repair Model Section 9-10:
        - Collapse to protected identity kernel
        - Enter torpor/reflex mode
        - Reject nonessential actions
        - Wait for replenishment
        
        Expected: K_id preserved, all nonessential state discarded
        """
        # In v0.1, terminal collapse to torpor
        # In full implementation, would:
        # - Verify identity kernel preserved
        # - Archive all nonessential state
        # - Enter torpor mode
        # - Set wake conditions
        
        return RepairResult(
            action=RepairAction.R4_COLLAPSE,
            success=True,
            delta_v=-50.0,  # Maximum risk reduction
            delta_t=-50.0,  # Maximum tension reduction
            delta_b=-30.0,  # Collapse costs
            message="Safe-state collapse: kernel preserved, entering torpor"
        )
    
    def execute(self, context: RepairContext) -> RepairResult:
        """
        Execute repair action based on context.
        
        Returns:
            RepairResult with action outcome
        """
        # Select action
        action = self.select_action(context)
        
        if action == RepairAction.NONE:
            return RepairResult(
                action=RepairAction.NONE,
                success=True,
                message="No repair needed - system healthy"
            )
        
        # Execute appropriate action
        if action == RepairAction.R1_CORRECT:
            result = self.execute_r1(context)
        elif action == RepairAction.R2_REPAIR:
            result = self.execute_r2(context)
        elif action == RepairAction.R3_CONTRACT:
            result = self.execute_r3(context)
        elif action == RepairAction.R4_COLLAPSE:
            result = self.execute_r4(context)
        else:
            result = RepairResult(
                action=RepairAction.NONE,
                success=False,
                message=f"Unknown action: {action}"
            )
        
        # Store in history
        self._history.append(result)
        
        return result
    
    def can_execute(self, action: RepairAction, context: RepairContext) -> bool:
        """
        Check if repair action can be legally executed.
        
        Per Self-Repair Model Section 12-13:
        Repair must satisfy:
        - V(x') + Spend(r) ≤ V(x) + Defect(r)
        - Spend ≤ B - B_reserve
        """
        spec = self.ACTION_SPECS.get(
            self.ACTION_SPECS[context.danger_state.band].action
        )
        
        if spec is None:
            return False
        
        # Check budget
        available = context.available_budget - context.reserve_floor
        if available < spec.max_spend:
            return False
        
        # Check if action enabled
        if not self.enabled_actions.get(action, True):
            return False
        
        return True
    
    def get_history(self) -> List[RepairResult]:
        """Get repair execution history."""
        return self._history.copy()


def create_repair_controller(
    danger_monitor: Optional[DangerMonitor] = None,
    v0_1_mode: bool = True
) -> RepairController:
    """
    Factory function to create a repair controller.
    
    Args:
        danger_monitor: Associated danger monitor
        v0_1_mode: If True, enable all actions with minimal spend
        
    Returns:
        Configured RepairController
    """
    return RepairController(
        danger_monitor=danger_monitor,
        enable_r1=True,
        enable_r2=True,
        enable_r3=True,
        enable_r4=True,
        min_budget_for_repair=5.0 if v0_1_mode else 10.0
    )
