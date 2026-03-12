"""
Danger Index for GM-OS Self-Repair System.

Implements the coupled danger functional and trigger scores per the Self-Repair Model:

    D = w_V*Θ_V + w_T*Θ_T + w_C*Θ_C + w_B*Θ_B + w_H*Θ_H + w_I*Θ_I

With persistence filter:

    P_θ(t) = ∫_{t-Δ}^{t} 1_{D(s) > θ} ds

This module provides the "immune system" that detects when repair actions
need to be triggered.

Per Self-Repair Model Section 18: v0.1 uses (V, T, B, H) four signals.
Per Phase 2: Now includes (C) curvature and (I) identity for full danger model.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum
import time
import math


class DangerBand(Enum):
    """Reconfiguration bands per Self-Repair Model Section 8."""
    HEALTHY = 0      # D < 0.25
    DRIFT = 1       # 0.25 ≤ D < 0.45
    DAMAGE = 2      # 0.45 ≤ D < 0.65
    CRITICAL = 3     # 0.65 ≤ D < 0.85
    COLLAPSE = 4    # D ≥ 0.85


@dataclass
class DangerWeights:
    """Weights for coupled danger functional."""
    w_v: float = 1.0   # Risk/violation weight
    w_t: float = 1.0   # Tension weight
    w_c: float = 0.5   # Curvature weight (optional v0.1)
    w_b: float = 1.5   # Budget stress weight (higher - survival critical)
    w_h: float = 2.0   # Integrity weight (existential)
    w_i: float = 2.0   # Identity weight (existential)


@dataclass
class TriggerThresholds:
    """Maximum values for trigger normalization."""
    v_max: float = 100.0     # Max risk value
    t_max: float = 100.0     # Max tension value
    c_max: float = 50.0      # Max curvature value
    b_max: float = 100.0     # Max budget for normalization
    b_reserve: float = 10.0  # Reserve floor
    h_max: float = 1.0       # Integrity is already 0-1
    i_max: float = 1.0       # Identity is already 0-1
    
    # Danger thresholds
    danger_threshold: float = 0.45     # Start repair
    critical_threshold: float = 0.65   # Urgent repair
    collapse_threshold: float = 0.85    # Collapse imminent
    
    # Persistence
    persistence_window: float = 10.0   # seconds
    persistence_threshold: float = 0.6  # Fraction of window exceeding threshold


@dataclass
class DangerState:
    """Current danger state snapshot."""
    # Raw observables
    v: float = 0.0      # Risk/violation
    t: float = 0.0      # Tension
    c: float = 0.0      # Curvature (optional)
    b: float = 0.0      # Budget
    h: float = 1.0      # Integrity (1 = perfect)
    i: float = 1.0      # Identity (1 = perfect)
    
    # Computed triggers (0-1)
    theta_v: float = 0.0
    theta_t: float = 0.0
    theta_c: float = 0.0
    theta_b: float = 0.0
    theta_h: float = 0.0
    theta_i: float = 0.0
    
    # Coupled danger
    danger_index: float = 0.0
    band: DangerBand = DangerBand.HEALTHY
    
    # Persistence
    persistent_exceedance: float = 0.0
    timestamp: float = field(default_factory=time.time)


class DangerMonitor:
    """
    Computes coupled danger index and trigger scores.
    
    This is the "immune system" that detects when the organism
    needs to repair or reconfigure.
    """
    
    def __init__(
        self,
        weights: Optional[DangerWeights] = None,
        thresholds: Optional[TriggerThresholds] = None,
        include_curvature: bool = False,
        include_identity: bool = False
    ):
        self.weights = weights or DangerWeights()
        self.thresholds = thresholds or TriggerThresholds()
        self.include_curvature = include_curvature
        self.include_identity = include_identity
        
        # History for persistence filter
        self._history: List[DangerState] = []
        self._max_history = 1000  # Keep last 1000 states
    
    def compute_triggers(self, state: DangerState) -> DangerState:
        """
        Compute normalized trigger scores from raw observables.
        
        Per Self-Repair Model Section 5:
        - Risk trigger: Θ_V = V_p / V_max
        - Tension trigger: Θ_T = T_p / T_max
        - Curvature trigger: Θ_C = C_p / C_max
        - Budget stress: Θ_B = 1 - (M_B / M_B_max) where M_B = B - B_reserve
        - Integrity trigger: Θ_H = 1 - H_p
        - Identity trigger: Θ_I = 1 - I_p
        """
        # Risk trigger
        if self.thresholds.v_max > 0:
            state.theta_v = min(1.0, state.v / self.thresholds.v_max)
        
        # Tension trigger
        if self.thresholds.t_max > 0:
            state.theta_t = min(1.0, state.t / self.thresholds.t_max)
        
        # Curvature trigger (optional)
        if self.include_curvature and self.thresholds.c_max > 0:
            state.theta_c = min(1.0, state.c / self.thresholds.c_max)
        
        # Budget stress: higher when closer to reserve
        budget_margin = state.b - self.thresholds.b_reserve
        max_margin = self.thresholds.b_max - self.thresholds.b_reserve
        if max_margin > 0:
            state.theta_b = max(0.0, 1.0 - (budget_margin / max_margin))
        else:
            state.theta_b = 1.0  # At or below reserve
        
        # Integrity trigger: 1 means completely broken
        state.theta_h = max(0.0, 1.0 - state.h)
        
        # Identity trigger (optional)
        if self.include_identity:
            state.theta_i = max(0.0, 1.0 - state.i)
        
        return state
    
    def compute_danger(self, state: DangerState) -> DangerState:
        """
        Compute coupled danger index.
        
        Per Self-Repair Model Section 6:
        
            D = w_V*Θ_V + w_T*Θ_T + w_C*Θ_C + w_B*Θ_B + w_H*Θ_H + w_I*Θ_I
        """
        w = self.weights
        
        # Start with v0.1 signals: V, T, B, H
        danger = (
            w.w_v * state.theta_v +
            w.w_t * state.theta_t +
            w.w_b * state.theta_b +
            w.w_h * state.theta_h
        )
        
        # Add optional signals
        if self.include_curvature:
            danger += w.w_c * state.theta_c
        
        if self.include_identity:
            danger += w.w_i * state.theta_i
        
        # Normalize by sum of active weights
        active_weights = 4.0  # V, T, B, H
        if self.include_curvature:
            active_weights += 1.0
        if self.include_identity:
            active_weights += 1.0
        
        state.danger_index = danger / active_weights
        state.danger_index = min(1.0, state.danger_index)  # Cap at 1.0
        
        # Determine band
        state.band = self._get_band(state.danger_index)
        
        return state
    
    def _get_band(self, danger: float) -> DangerBand:
        """Map danger index to band."""
        if danger < 0.25:
            return DangerBand.HEALTHY
        elif danger < 0.45:
            return DangerBand.DRIFT
        elif danger < 0.65:
            return DangerBand.DAMAGE
        elif danger < 0.85:
            return DangerBand.CRITICAL
        else:
            return DangerBand.COLLAPSE
    
    def compute_persistence(
        self,
        current_danger: float,
        window_seconds: Optional[float] = None
    ) -> float:
        """
        Compute persistence of danger exceeding threshold.
        
        Per Self-Repair Model Section 7:
        
            P_θ(t) = ∫_{t-Δ}^{t} 1_{D(s) > θ} ds
        
        Returns fraction of window where danger exceeded threshold.
        """
        window = window_seconds or self.thresholds.persistence_window
        threshold = self.thresholds.danger_threshold
        
        now = time.time()
        cutoff = now - window
        
        # Filter to window
        relevant = [s for s in self._history if s.timestamp >= cutoff]
        
        if not relevant:
            return 0.0
        
        # Count exceedances
        exceedances = sum(1 for s in relevant if s.danger_index > threshold)
        
        return exceedances / len(relevant)
    
    def update(
        self,
        v: float = 0.0,
        t: float = 0.0,
        c: float = 0.0,
        b: float = 0.0,
        h: float = 1.0,
        i: float = 1.0
    ) -> DangerState:
        """
        Update danger state from raw observables.
        
        This is the main entry point for the immune system.
        
        Args:
            v: Risk/violation measure
            t: Tension measure
            c: Curvature/scar load (optional)
            b: Current budget
            h: Integrity score (0-1, 1 = perfect)
            i: Identity coherence (0-1, 1 = perfect)
            
        Returns:
            DangerState with computed triggers, danger index, and band
        """
        # Create state
        state = DangerState(
            v=v, t=t, c=c, b=b, h=h, i=i
        )
        
        # Compute triggers
        state = self.compute_triggers(state)
        
        # Compute danger
        state = self.compute_danger(state)
        
        # Compute persistence
        state.persistent_exceedance = self.compute_persistence(state.danger_index)
        
        # Store in history
        self._history.append(state)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        return state
    
    def should_repair(self) -> bool:
        """
        Determine if repair action should be triggered.
        
        Per Self-Repair Model Section 7:
        Repair triggers when persistent exceedance meets threshold.
        """
        if not self._history:
            return False
        
        latest = self._history[-1]
        
        # Band 2+ means damage detected
        if latest.band.value >= DangerBand.DAMAGE.value:
            # Also check persistence
            return latest.persistent_exceedance >= self.thresholds.persistence_threshold
        
        return False
    
    def should_reconfigure(self) -> bool:
        """
        Determine if reconfiguration should be triggered.
        
        Per Adaptive Reconfiguration Model Section 13.
        """
        if not self._history:
            return False
        
        latest = self._history[-1]
        
        # Critical band or persistent damage
        if latest.band == DangerBand.CRITICAL:
            return True
        
        if latest.band == DangerBand.DAMAGE:
            return latest.persistent_exceedance >= 0.8
        
        return False
    
    def should_collapse(self) -> bool:
        """
        Determine if safe-state collapse should be triggered.
        
        Per Self-Repair Model Section 8, Band 4.
        """
        if not self._history:
            return False
        
        latest = self._history[-1]
        return latest.band == DangerBand.COLLAPSE
    
    def get_recommendation(self) -> Dict[str, any]:
        """
        Get repair/reconfiguration recommendation.
        
        Returns:
            Dictionary with recommended action type and parameters
        """
        if not self._history:
            return {"action": "none", "reason": "no_data"}
        
        latest = self._history[-1]
        
        # Check collapse first (most urgent)
        if latest.band == DangerBand.COLLAPSE:
            return {
                "action": "R4_COLLAPSE",
                "band": "COLLAPSE",
                "danger": latest.danger_index,
                "reason": "Identity-threatening danger level"
            }
        
        # Critical - structural contraction
        if latest.band == DangerBand.CRITICAL:
            return {
                "action": "R3_CONTRACTION",
                "band": "CRITICAL", 
                "danger": latest.danger_index,
                "reason": "High danger requires structural reduction"
            }
        
        # Damage - targeted repair
        if latest.band == DangerBand.DAMAGE:
            return {
                "action": "R2_REPAIR",
                "band": "DAMAGE",
                "danger": latest.danger_index,
                "reason": "Moderate danger, targeted repair needed"
            }
        
        # Drift - minor correction
        if latest.band == DangerBand.DRIFT:
            return {
                "action": "R1_CORRECT",
                "band": "DRIFT",
                "danger": latest.danger_index,
                "reason": "Minor drift, local correction sufficient"
            }
        
        # Healthy
        return {
            "action": "NONE",
            "band": "HEALTHY",
            "danger": latest.danger_index,
            "reason": "System in healthy operating range"
        }


def create_danger_monitor(
    v0_1_mode: bool = True,
    budget_reserve: float = 10.0,
    budget_max: float = 100.0
) -> DangerMonitor:
    """
    Factory function to create a danger monitor.
    
    Args:
        v0_1_mode: If True, use only V, T, B, H (4 signals)
        budget_reserve: Protected reserve floor
        budget_max: Maximum budget for normalization
        
    Returns:
        Configured DangerMonitor instance
    """
    thresholds = TriggerThresholds(
        b_reserve=budget_reserve,
        b_max=budget_max
    )
    
    return DangerMonitor(
        thresholds=thresholds,
        include_curvature=not v0_1_mode,
        include_identity=not v0_1_mode
    )
