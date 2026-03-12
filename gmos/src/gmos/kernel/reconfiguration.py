"""
Reconfiguration Controller for GM-OS Adaptive Reconfiguration System.

Implements geometry modes and contraction decision-making per Adaptive Reconfiguration Model:

    Γ ∈ {Γ0, Γ1, Γ2, Γ3, Γ4}
    
    - Γ0: Full mode (normal operation)
    - Γ1: Efficiency mode (reduced branch/computation)
    - Γ2: Defensive mode (suspend luxury, narrow attention)
    - Γ3: Survival mode (minimal shell)
    - Γ4: Torpor/Reflex-only mode

Per Adaptive Reconfiguration Model Section 14: v0.1 minimal (FULL, SURVIVAL, TORPOR).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable, Any
from enum import Enum
import time

from gmos.kernel.danger import DangerBand, DangerMonitor


class GeometryMode(Enum):
    """
    Operating geometry modes per Adaptive Reconfiguration Model Section 4.
    
    Γ0 - Full: Normal operation with all layers
    Γ1 - Efficiency: Reduced branch/computation
    Γ2 - Defensive: Suspend luxury, narrow attention
    Γ3 - Survival: Minimal shell only
    Γ4 - Torpor: Reflex-only, wait for replenishment
    """
    FULL = "full"           # Γ0
    EFFICIENCY = "efficiency"  # Γ1
    DEFENSIVE = "defensive"    # Γ2
    SURVIVAL = "survival"      # Γ3
    TORPOR = "torpor"          # Γ4


@dataclass
class ModeConfig:
    """Configuration for a geometry mode."""
    mode: GeometryMode
    description: str
    
    # Cost modifiers
    idle_cost_mult: float = 1.0
    memory_cost_mult: float = 1.0
    inference_cost_mult: float = 1.0
    projection_cost_mult: float = 1.0
    coord_cost_mult: float = 1.0
    
    # Feature flags
    exploration_enabled: bool = True
    planning_enabled: bool = True
    rich_sensing_enabled: bool = True
    multi_process_enabled: bool = True
    
    # Transition thresholds
    enter_threshold: float = 0.0  # Danger level to enter this mode
    exit_threshold: float = 0.0  # Danger level to exit this mode


# Mode configurations
MODE_CONFIGS: Dict[GeometryMode, ModeConfig] = {
    GeometryMode.FULL: ModeConfig(
        mode=GeometryMode.FULL,
        description="Full operation - all layers enabled",
        idle_cost_mult=1.0,
        memory_cost_mult=1.0,
        inference_cost_mult=1.0,
        projection_cost_mult=1.0,
        coord_cost_mult=1.0,
        exploration_enabled=True,
        planning_enabled=True,
        rich_sensing_enabled=True,
        multi_process_enabled=True,
        enter_threshold=0.0,
        exit_threshold=0.15
    ),
    GeometryMode.EFFICIENCY: ModeConfig(
        mode=GeometryMode.EFFICIENCY,
        description="Efficiency mode - reduce branch width and recomputation",
        idle_cost_mult=0.9,
        memory_cost_mult=0.8,
        inference_cost_mult=0.7,
        projection_cost_mult=0.8,
        coord_cost_mult=0.9,
        exploration_enabled=True,
        planning_enabled=True,
        rich_sensing_enabled=True,
        multi_process_enabled=True,
        enter_threshold=0.20,
        exit_threshold=0.10
    ),
    GeometryMode.DEFENSIVE: ModeConfig(
        mode=GeometryMode.DEFENSIVE,
        description="Defensive mode - suspend luxury, narrow attention",
        idle_cost_mult=0.8,
        memory_cost_mult=0.7,
        inference_cost_mult=0.6,
        projection_cost_mult=0.7,
        coord_cost_mult=0.6,
        exploration_enabled=False,
        planning_enabled=True,
        rich_sensing_enabled=False,
        multi_process_enabled=False,
        enter_threshold=0.40,
        exit_threshold=0.25
    ),
    GeometryMode.SURVIVAL: ModeConfig(
        mode=GeometryMode.SURVIVAL,
        description="Survival mode - minimal shell, essential functions only",
        idle_cost_mult=0.6,
        memory_cost_mult=0.5,
        inference_cost_mult=0.4,
        projection_cost_mult=0.5,
        coord_cost_mult=0.3,
        exploration_enabled=False,
        planning_enabled=False,
        rich_sensing_enabled=False,
        multi_process_enabled=False,
        enter_threshold=0.65,
        exit_threshold=0.45
    ),
    GeometryMode.TORPOR: ModeConfig(
        mode=GeometryMode.TORPOR,
        description="Torpor mode - reflex only, wait for replenishment",
        idle_cost_mult=0.1,
        memory_cost_mult=0.1,
        inference_cost_mult=0.05,
        projection_cost_mult=0.1,
        coord_cost_mult=0.05,
        exploration_enabled=False,
        planning_enabled=False,
        rich_sensing_enabled=False,
        multi_process_enabled=False,
        enter_threshold=0.85,
        exit_threshold=0.30  # Higher exit - need significant improvement
    ),
}


@dataclass
class ReconfigState:
    """Current reconfiguration state."""
    current_mode: GeometryMode = GeometryMode.FULL
    target_mode: GeometryMode = GeometryMode.FULL
    
    # Transition state
    is_transitioning: bool = False
    transition_start_time: float = 0.0
    
    # History
    mode_history: List[GeometryMode] = field(default_factory=list)
    last_transition_time: float = field(default_factory=time.time)
    
    # Counters
    contraction_count: int = 0
    expansion_count: int = 0


class ReconfigurationController:
    """
    Controls geometry mode transitions based on danger level.
    
    Per Adaptive Reconfiguration Model Section 16:
    Uses hysteresis to prevent oscillatory mode switching:
    
        Γ_{n+1} = {
            Γ_{k+1}, if D > θ_k↑
            Γ_{k-1}, if D < θ_k↓
            Γ_k, otherwise
        }
    """
    
    def __init__(
        self,
        danger_monitor: Optional[DangerMonitor] = None,
        enable_hysteresis: bool = True,
        min_mode_duration: float = 5.0,  # seconds
        initial_mode: GeometryMode = GeometryMode.FULL
    ):
        self.danger_monitor = danger_monitor
        self.enable_hysteresis = enable_hysteresis
        self.min_mode_duration = min_mode_duration
        
        # Current state
        self.state = ReconfigState(current_mode=initial_mode)
    
    def evaluate(self, danger_level: float) -> GeometryMode:
        """
        Evaluate and determine target geometry mode.
        
        Args:
            danger_level: Current danger index (0-1)
            
        Returns:
            Target GeometryMode
        """
        current = self.state.current_mode
        
        # Check minimum duration for hysteresis
        now = time.time()
        time_since_transition = now - self.state.last_transition_time
        if time_since_transition < self.min_mode_duration and self.enable_hysteresis:
            return current
        
        # Determine target based on danger thresholds
        target = self._determine_target_mode(danger_level)
        
        # Apply hysteresis - only change if significantly different
        if self.enable_hysteresis and target != current:
            # Need significant danger change to switch
            config = MODE_CONFIGS[current]
            if target.value > current.value:  # Contracting
                if danger_level < config.exit_threshold:
                    return current  # Not dangerous enough to contract
            else:  # Expanding
                if danger_level > config.enter_threshold:
                    return current  # Not safe enough to expand
        
        return target
    
    def _determine_target_mode(self, danger: float) -> GeometryMode:
        """Determine target mode based on danger level."""
        if danger >= MODE_CONFIGS[GeometryMode.TORPOR].enter_threshold:
            return GeometryMode.TORPOR
        elif danger >= MODE_CONFIGS[GeometryMode.SURVIVAL].enter_threshold:
            return GeometryMode.SURVIVAL
        elif danger >= MODE_CONFIGS[GeometryMode.DEFENSIVE].enter_threshold:
            return GeometryMode.DEFENSIVE
        elif danger >= MODE_CONFIGS[GeometryMode.EFFICIENCY].enter_threshold:
            return GeometryMode.EFFICIENCY
        else:
            return GeometryMode.FULL
    
    def transition_to(self, new_mode: GeometryMode) -> bool:
        """
        Execute transition to new mode.
        
        Args:
            new_mode: Target geometry mode
            
        Returns:
            True if transition successful
        """
        if new_mode == self.state.current_mode:
            return False
        
        # Check if transition is allowed (can't skip more than one level)
        current_idx = list(GeometryMode).index(self.state.current_mode)
        target_idx = list(GeometryMode).index(new_mode)
        
        # Allow contraction by any amount, expansion by max one step
        if target_idx > current_idx and (target_idx - current_idx) > 1:
            return False  # Can't expand by more than one level
        
        old_mode = self.state.current_mode
        self.state.current_mode = new_mode
        self.state.target_mode = new_mode
        self.state.last_transition_time = time.time()
        self.state.is_transitioning = False
        
        # Update counters
        if target_idx > current_idx:
            self.state.contraction_count += 1
        else:
            self.state.expansion_count += 1
        
        # Record in history
        self.state.mode_history.append(new_mode)
        
        return True
    
    def get_mode_config(self) -> ModeConfig:
        """Get configuration for current mode."""
        return MODE_CONFIGS[self.state.current_mode]
    
    def get_cost_multipliers(self) -> Dict[str, float]:
        """Get cost multipliers for current mode."""
        config = self.get_mode_config()
        return {
            "idle": config.idle_cost_mult,
            "memory": config.memory_cost_mult,
            "inference": config.inference_cost_mult,
            "projection": config.projection_cost_mult,
            "coord": config.coord_cost_mult,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current reconfiguration status."""
        return {
            "current_mode": self.state.current_mode.value,
            "target_mode": self.state.target_mode.value,
            "is_transitioning": self.state.is_transitioning,
            "contraction_count": self.state.contraction_count,
            "expansion_count": self.state.expansion_count,
            "cost_multipliers": self.get_cost_multipliers(),
            "features": {
                "exploration": self.state.current_mode.value,
                "planning": self.get_mode_config().planning_enabled,
                "rich_sensing": self.get_mode_config().rich_sensing_enabled,
                "multi_process": self.get_mode_config().multi_process_enabled,
            }
        }


def create_reconfiguration_controller(
    danger_monitor: Optional[DangerMonitor] = None,
    v0_1_mode: bool = True
) -> ReconfigurationController:
    """
    Factory function to create a reconfiguration controller.
    
    Args:
        danger_monitor: Associated danger monitor
        v0_1_mode: If True, use simplified 3-mode (FULL, SURVIVAL, TORPOR)
        
    Returns:
        Configured ReconfigurationController
    """
    return ReconfigurationController(
        danger_monitor=danger_monitor,
        enable_hysteresis=True,
        min_mode_duration=5.0,
        initial_mode=GeometryMode.FULL
    )
