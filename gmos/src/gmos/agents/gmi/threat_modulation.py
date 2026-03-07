"""
Threat Modulation for the GMI Universal Cognition Engine.

Module 16: Affective Mode Geometry

Handles:
- Computing χ from environment signals
- Flow band computation
- Threat-defense mode switching
"""

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np


@dataclass
class FlowBand:
    """
    Defines the optimal χ range for "flow" (thermodynamic efficiency).
    
    Theorem 16.2 (Conjecture): There exists a strict interior interval
    χ_flow = [χ_min, χ_max] where:
    - Condition number of combined operator Jacobian is minimized
    - Inter-operator switching friction is minimized
    """
    chi_min: float = 0.2
    chi_max: float = 0.4
    
    def contains(self, chi: float) -> bool:
        """Is χ in flow band?"""
        return self.chi_min <= chi <= self.chi_max
    
    def distance_to_flow(self, chi: float) -> float:
        """Distance from χ to nearest flow boundary."""
        if chi < self.chi_min:
            return self.chi_min - chi
        elif chi > self.chi_max:
            return chi - self.chi_max
        return 0.0


class ThreatModulator:
    """
    Computes and manages threat level χ.
    
    Provides:
    - χ computation from environment signals
    - Flow band detection
    - Threat-defense mode switching
    """
    
    # Default flow band
    DEFAULT_FLOW_BAND = FlowBand(0.2, 0.4)
    
    def __init__(
        self,
        flow_band: Optional[FlowBand] = None,
        smoothing: float = 0.1
    ):
        """
        Initialize threat modulator.
        
        Args:
            flow_band: Flow band definition
            smoothing: Exponential smoothing factor for χ updates
        """
        self.flow_band = flow_band or self.DEFAULT_FLOW_BAND
        self.smoothing = smoothing
        self.current_chi = 0.5
        self.chi_history = [0.5]
    
    def compute_chi(
        self,
        external_signal: float,
        prediction_error: Optional[float] = None,
        budget_ratio: Optional[float] = None
    ) -> float:
        """
        Compute χ from multiple signals.
        
        Args:
            external_signal: Environment threat signal [0, 1]
            prediction_error: Recent prediction error [0, inf]
            budget_ratio: Budget utilization ratio [0, 1]
            
        Returns:
            χ value
        """
        # Base from external signal
        chi_external = self._compute_from_external(external_signal)
        
        # Adjust from prediction error (if provided)
        if prediction_error is not None:
            chi_error = self._compute_from_error(prediction_error)
            chi_external = 0.7 * chi_external + 0.3 * chi_error
        
        # Adjust from budget (if provided)
        if budget_ratio is not None:
            chi_budget = self._compute_from_budget(budget_ratio)
            chi_external = 0.8 * chi_external + 0.2 * chi_budget
        
        # Apply smoothing
        chi_new = (
            self.smoothing * chi_external + 
            (1 - self.smoothing) * self.current_chi
        )
        
        # Clamp
        chi_new = float(np.clip(chi_new, 0.0, 1.0))
        
        # Update
        self.current_chi = chi_new
        self.chi_history.append(chi_new)
        
        return chi_new
    
    def _compute_from_external(self, signal: float) -> float:
        """Compute χ from external signal."""
        # Use tanh for smooth saturation
        return float(np.tanh(signal * 2.5))
    
    def _compute_from_error(self, error: float) -> float:
        """Compute χ from prediction error."""
        # Large error increases threat
        normalized = min(error, 1.0)  # Cap at 1
        return float(np.tanh(normalized * 3.0))
    
    def _compute_from_budget(self, ratio: float) -> float:
        """Compute χ from budget ratio."""
        # Low budget (high ratio since ratio = used/total) increases threat
        # If ratio > 0.9, we're running low
        if ratio > 0.9:
            return 0.8
        elif ratio > 0.7:
            return 0.4
        return 0.1
    
    def is_in_flow(self, chi: Optional[float] = None) -> bool:
        """Is the system in flow state?"""
        chi = chi or self.current_chi
        return self.flow_band.contains(chi)
    
    def is_defensive(self, chi: Optional[float] = None) -> bool:
        """Is the system in defensive mode?"""
        chi = chi or self.current_chi
        return chi > 0.7
    
    def is_expansive(self, chi: Optional[float] = None) -> bool:
        """Is the system in expansive (safe) mode?"""
        chi = chi or self.current_chi
        return chi < 0.3
    
    def get_mode_description(self, chi: Optional[float] = None) -> str:
        """Get human-readable mode description."""
        chi = chi or self.current_chi
        
        if chi < 0.15:
            return "deep_safety: Maximum exploration, low costs"
        elif chi < 0.35:
            return "flow: Optimal thermodynamic efficiency"
        elif chi < 0.55:
            return "neutral: Balanced generation and pruning"
        elif chi < 0.75:
            return "caution: Increased threat sensitivity"
        else:
            return "defensive: Rigid logic, minimal branching"
    
    def get_operator_recommendations(self, chi: Optional[float] = None) -> dict:
        """
        Get recommended operator usage based on χ.
        
        Returns:
            Dict with recommendations for each operator
        """
        chi = chi or self.current_chi
        
        # Imagination (O_I): broad tree search
        if chi < 0.3:
            imagination = "high"
        elif chi < 0.6:
            imagination = "moderate"
        else:
            imagination = "minimal"
        
        # Logic (O_L): constraint checking
        if chi < 0.3:
            logic = "minimal"
        elif chi < 0.6:
            logic = "moderate"
        else:
            logic = "high"
        
        # Emotion (O_E): salience weighting
        if chi < 0.4:
            emotion = "low"
        else:
            emotion = "high"
        
        return {
            'imagination': imagination,
            'logic': logic,
            'emotion': emotion,
            'branch_limit': self._compute_branch_limit(chi),
            'chi': chi
        }
    
    def _compute_branch_limit(self, chi: float) -> int:
        """Compute recommended branch limit from χ."""
        # More restrictive under threat
        if chi < 0.3:
            return 10
        elif chi < 0.5:
            return 5
        elif chi < 0.7:
            return 3
        return 1
    
    def get_statistics(self) -> dict:
        """Get threat modulation statistics."""
        if not self.chi_history:
            return {'message': 'No history'}
        
        return {
            'current_chi': self.current_chi,
            'min_chi': min(self.chi_history),
            'max_chi': max(self.chi_history),
            'avg_chi': sum(self.chi_history) / len(self.chi_history),
            'in_flow_pct': sum(1 for x in self.chi_history if self.flow_band.contains(x)) / len(self.chi_history),
            'in_defensive_pct': sum(1 for x in self.chi_history if x > 0.7) / len(self.chi_history)
        }
    
    def reset(self) -> None:
        """Reset to neutral state."""
        self.current_chi = 0.5
        self.chi_history = [0.5]


class TripartiteOperators:
    """
    The three interacting cognitive operators.
    
    1. O_E: Emotion / Salience - gradient-weighting
    2. O_I: Imagination / Branching - generative
    3. O_L: Logic / Pruning - constraint-verification
    
    Their costs are modulated by χ.
    """
    
    def __init__(self, chi: float = 0.5):
        self.chi = chi
    
    @property
    def imagination_cost(self) -> float:
        """Cost multiplier for imagination (increases with χ)."""
        return 1.0 * (1.0 + self.chi * 2.0)
    
    @property
    def logic_cost(self) -> float:
        """Cost multiplier for logic (decreases with χ)."""
        return 0.8 * (1.0 - self.chi * 0.5)
    
    @property
    def emotion_cost(self) -> float:
        """Cost multiplier for emotion (increases with χ)."""
        return 0.5 * (1.0 + self.chi * 1.5)
    
    @property
    def branch_threshold(self) -> float:
        """Minimum ROI to open a branch."""
        return 1.0 * (1.0 + self.chi)
    
    def can_open_branch(self, roi: float) -> bool:
        """Can we afford to open a branch?"""
        return roi >= self.branch_threshold
    
    def get_jacobian_condition(self) -> float:
        """
        Approximate condition number of operator coupling.
        
        Theorem 16.2: This is minimized in flow band.
        """
        # Simplified approximation
        coupling = (self.imagination_cost * self.logic_cost) / (self.emotion_cost + 0.1)
        return coupling


# Convenience functions

def create_safe_system() -> tuple[ThreatModulator, TripartiteOperators]:
    """Create system in safe mode."""
    return ThreatModulator(), TripartiteOperators(chi=0.1)


def create_flow_system() -> tuple[ThreatModulator, TripartiteOperators]:
    """Create system in flow mode."""
    modulator = ThreatModulator()
    modulator.current_chi = 0.3
    return modulator, TripartiteOperators(chi=0.3)


def create_defensive_system() -> tuple[ThreatModulator, TripartiteOperators]:
    """Create system in defensive mode."""
    modulator = ThreatModulator()
    modulator.current_chi = 0.9
    return modulator, TripartiteOperators(chi=0.9)
