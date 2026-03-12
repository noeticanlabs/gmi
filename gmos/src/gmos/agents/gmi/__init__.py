"""
GMI Agent Package for GM-OS.

This package contains the canonical GMI agent implementation.
"""

# Re-export the main agent class
from gmos.agents.gmi.gmi_agent import (
    state,
    potential,
    constraints,
    affective_state,
    affective_budget,
    threat_modulation,
    policy_selection,
    evolution_loop,
    execution_loop,
    semantic_loop,
    hosted_agent,
    tension_law,
)

# For backwards compatibility, also create GMIAgent class wrapper
class GMIAgent:
    """
    GMI Agent - wrapper class for backward compatibility.
    
    Minimal GMIAgent implementation for GM-OS kernel boot sequence:
    1. Wake up (register with ProcessTable)
    2. Receive budget (via BudgetRouter)  
    3. Propose action (NOOP or REFLECT)
    4. Go to sleep (enter Torpor when budget depleted)
    """
    
    def __init__(self, budget: float = 100.0, process_id: str = "P_GMI", **kwargs):
        self.budget = budget
        self.process_id = process_id
        self.state_module = state
        self.potential_module = potential
        self.constraints_module = constraints
        # Kernel integration
        self._process_table = None
        self._budget_router = None
        self._scheduler = None
        self._status = "created"
        
    def register_with_kernel(self, process_table, budget_router, scheduler):
        """
        Register this agent with the GM-OS kernel.
        
        Args:
            process_table: ProcessTable instance
            budget_router: BudgetRouter instance
            scheduler: KernelScheduler instance
        """
        from gmos.kernel import ProcessType, ProcessMode, ReserveTier, ScheduleMode
        
        # Register in ProcessTable
        process_table.register(
            self.process_id,
            ProcessType.GMI,
            priority=5
        )
        
        # Allocate budget
        budget_router.register_process_budget(
            process_id=self.process_id,
            layer=1,
            amount=self.budget,
            reserve=0.1,  # Reserve floor
            tier=ReserveTier.ESSENTIAL
        )
        
        # Register in scheduler
        scheduler.register_process(
            self.process_id,
            ScheduleMode.ACTIVE
        )
        
        # Store references
        self._process_table = process_table
        self._budget_router = budget_router
        self._scheduler = scheduler
        self._status = "registered"
        
    def tick(self):
        """
        Execute one agent tick: wake → propose → sleep.
        
        Returns:
            dict: Result of the tick with keys:
                - action: 'NOOP' | 'REFLECT' | 'TORPOR'
                - budget_before: float
                - budget_after: float
                - status: str
        """
        if self._status == "torpor":
            return {"action": "TORPOR", "status": "already_in_torpor"}
        
        if self._status not in ("registered", "active"):
            return {"action": None, "status": self._status}
        
        # Get current budget
        budget_before = self._budget_router.get_budget(self.process_id, 1)
        
        if budget_before is None or budget_before <= 0.1:  # At reserve
            # Enter torpor
            self._scheduler.mark_torpor(self.process_id)
            self._status = "torpor"
            return {
                "action": "TORPOR",
                "budget_before": budget_before,
                "budget_after": budget_before,
                "status": "entered_torpor"
            }
        
        # Propose NOOP or REFLECT (for minimal implementation, always NOOP)
        action = "NOOP"
        
        # Apply tick cost
        tick_cost = 0.01  # Minimal tick cost
        if self._budget_router.can_spend(self.process_id, 1, tick_cost):
            self._budget_router.apply_spend(self.process_id, 1, tick_cost)
            budget_after = self._budget_router.get_budget(self.process_id, 1)
        else:
            budget_after = budget_before
            action = "TORPOR"
            self._scheduler.mark_torpor(self.process_id)
            self._status = "torpor"
        
        return {
            "action": action,
            "budget_before": budget_before,
            "budget_after": budget_after,
            "status": "executed"
        }
        
    def is_alive(self) -> bool:
        """Check if agent is alive (not in torpor)."""
        return self._status != "torpor"
        
    def __getattr__(self, name):
        # Delegate to submodules
        if name in ('state', 'potential', 'constraints', 'affective_state', 
                    'affective_budget', 'threat_modulation', 'policy_selection',
                    'evolution_loop', 'execution_loop', 'semantic_loop', 
                    'hosted_agent', 'tension_law'):
            return globals()[name]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")


__all__ = [
    'GMIAgent',
    'state',
    'potential',
    'constraints',
    'affective_state',
    'affective_budget',
    'threat_modulation',
    'policy_selection',
    'evolution_loop',
    'execution_loop',
    'semantic_loop',
    'hosted_agent',
    'tension_law',
]
