"""
Trauma Memory System.

Per spec: When an action fails or harms the organism, that event
must physically deform the geometric landscape of the PhaseLoom,
creating a "hill" that repels the gradient flow from making
that same choice again.

This module handles:
1. Processing failed actions and negative feedback
2. Creating curvature scars at semantic coordinates
3. Deciding whether to avoid previously harmful actions
4. Logging traumatic events for future reference
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import time

from gmos.sensory.curvature import CurvatureField, CurvatureParameters


class TraumaSeverity(Enum):
    """Severity levels for traumatic events."""
    MINOR = 0.1    # Minor discomfort, quick recovery
    MODERATE = 0.5 # Noticeable harm, longer recovery
    SEVERE = 1.0   # Major damage, lasting scar
    CRITICAL = 2.0 # Near-death, permanent scar


@dataclass
class TraumaEvent:
    """
    A single traumatic event in the organism's history.
    """
    timestamp: float
    action: str
    semantic_position: float
    damage: float
    severity: TraumaSeverity
    scar_magnitude: float
    scar_spread: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "semantic_position": self.semantic_position,
            "damage": self.damage,
            "severity": self.severity.value,
            "scar_magnitude": self.scar_magnitude,
            "scar_spread": self.scar_spread,
        }


@dataclass
class AvoidanceDecision:
    """
    Decision about whether to avoid an action.
    """
    action: str
    position: float
    should_avoid: bool
    curvature_at_position: float
    avoidance_threshold: float
    reasoning: str


class TraumaMemory:
    """
    Manages traumatic memories that create lasting scars.
    
    When the organism experiences negative outcomes, this system:
    1. Processes the failure event
    2. Creates a curvature scar at the semantic coordinate
    3. Logs the trauma for future reference
    4. Provides avoidance recommendations for future decisions
    """
    
    def __init__(
        self,
        curvature_field: Optional[CurvatureField] = None,
        default_scar_spread: float = 0.1,
        severity_multiplier: float = 1.0,
    ):
        """
        Initialize the trauma memory system.
        
        Args:
            curvature_field: The curvature field to manage
            default_scar_spread: Default σ for Gaussian scars
            severity_multiplier: Multiplier for scar magnitude
        """
        self.curvature = curvature_field or CurvatureField(
            dimensions=1,
            resolution=100,
            bounds=(0.0, 1.0),
        )
        self.default_scar_spread = default_scar_spread
        self.severity_multiplier = severity_multiplier
        
        # Trauma log
        self.trauma_log: List[TraumaEvent] = []
        
        # Statistics
        self.total_damage_taken = 0.0
        self.total_scars_created = 0
    
    def process_failure(
        self,
        action: str,
        damage: float,
        semantic_position: float,
        scar_spread: Optional[float] = None
    ) -> TraumaEvent:
        """
        Process a failed action and create a scar.
        
        Args:
            action: The action that failed
            damage: The amount of damage taken
            semantic_position: The semantic coordinate of the failure
            scar_spread: Optional override for scar spread
            
        Returns:
            The created TraumaEvent
        """
        # Determine severity
        severity = self._determine_severity(damage)
        
        # Calculate scar magnitude (proportional to damage)
        scar_magnitude = damage * self.severity_multiplier
        
        # Add the scar to the curvature field
        self.curvature.add_scar(
            position=semantic_position,
            magnitude=scar_magnitude,
            spread=scar_spread or self.default_scar_spread
        )
        
        # Create trauma event
        event = TraumaEvent(
            timestamp=time.time(),
            action=action,
            semantic_position=semantic_position,
            damage=damage,
            severity=severity,
            scar_magnitude=scar_magnitude,
            scar_spread=scar_spread or self.default_scar_spread,
        )
        
        # Log the trauma
        self.trauma_log.append(event)
        
        # Update statistics
        self.total_damage_taken += damage
        self.total_scars_created += 1
        
        return event
    
    def _determine_severity(self, damage: float) -> TraumaSeverity:
        """Determine trauma severity from damage amount."""
        if damage < 0.1:
            return TraumaSeverity.MINOR
        elif damage < 0.3:
            return TraumaSeverity.MODERATE
        elif damage < 0.6:
            return TraumaSeverity.SEVERE
        else:
            return TraumaSeverity.CRITICAL
    
    def should_avoid(
        self,
        action: str,
        semantic_position: float,
        override_threshold: Optional[float] = None
    ) -> AvoidanceDecision:
        """
        Check if an action should be avoided based on scarring.
        
        Args:
            action: The action being considered
            semantic_position: The semantic coordinate
            override_threshold: Optional threshold override
            
        Returns:
            AvoidanceDecision with reasoning
        """
        # Get curvature at position
        curvature = self.curvature.get_curvature(semantic_position)
        
        # Determine threshold
        threshold = override_threshold or self.curvature.params.avoidance_threshold
        
        # Make decision
        should_avoid = curvature > threshold
        
        # Generate reasoning
        if should_avoid:
            reasoning = f"Curvature {curvature:.3f} exceeds threshold {threshold:.3f}"
        else:
            reasoning = f"Curvature {curvature:.3f} below threshold {threshold:.3f}"
        
        return AvoidanceDecision(
            action=action,
            position=semantic_position,
            should_avoid=should_avoid,
            curvature_at_position=curvature,
            avoidance_threshold=threshold,
            reasoning=reasoning,
        )
    
    def get_gradient_push(
        self,
        current_position: float,
        gradient_direction: float
    ) -> float:
        """
        Get the modified gradient after hitting curvature.
        
        When gradient flow encounters a curvature hill, it gets
        pushed away from the high-curvature region.
        
        Args:
            current_position: Current position in semantic space
            gradient_direction: Original gradient direction
            
        Returns:
            Modified gradient (pushed away from scar)
        """
        curvature = self.curvature.get_curvature(current_position)
        
        if curvature < self.curvature.params.avoidance_threshold:
            # No significant curvature, return original gradient
            return gradient_direction
        
        # Get curvature gradient (direction of steepest ascent)
        curv_grad = self.curvature.compute_curvature_gradient(current_position)
        
        # Push gradient away from curvature hill
        # If gradient points toward high curvature, reverse and reduce
        push_strength = min(1.0, curvature)
        
        modified = gradient_direction - push_strength * curv_grad * 0.1
        
        return modified
    
    def process_negative_feedback(
        self,
        action: str,
        feedback_value: float,
        semantic_position: float
    ) -> Optional[TraumaEvent]:
        """
        Process negative feedback from the environment.
        
        Args:
            action: The action that produced negative feedback
            feedback_value: Negative value (damage, penalty)
            semantic_position: Semantic coordinate of the action
            
        Returns:
            TraumaEvent if damage occurred, None otherwise
        """
        # Only process negative feedback
        if feedback_value >= 0:
            return None
        
        # Convert negative feedback to positive damage
        damage = abs(feedback_value)
        
        # Create scar
        return self.process_failure(
            action=action,
            damage=damage,
            semantic_position=semantic_position,
        )
    
    def heal_scars(self, dt: float = 1.0):
        """
        Apply scar decay/healing over time.
        
        Args:
            dt: Time step
        """
        self.curvature.decay_scars(dt)
    
    def get_trauma_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all trauma events.
        
        Returns:
            Dictionary with trauma statistics
        """
        return {
            "total_events": len(self.trauma_log),
            "total_damage": self.total_damage_taken,
            "total_scars": self.total_scars_created,
            "curvature_summary": self.curvature.get_scar_summary(),
            "recent_events": [
                e.to_dict() for e in self.trauma_log[-5:]
            ] if self.trauma_log else [],
        }
    
    def get_most_damaging_action(self) -> Optional[str]:
        """
        Get the action that caused the most damage.
        
        Returns:
            Action name or None
        """
        if not self.trauma_log:
            return None
        
        damage_by_action: Dict[str, float] = {}
        for event in self.trauma_log:
            damage_by_action[event.action] = damage_by_action.get(event.action, 0) + event.damage
        
        if not damage_by_action:
            return None
        
        return max(damage_by_action.items(), key=lambda x: x[1])[0]
    
    def clear_old_scars(self, before_timestamp: float):
        """
        Clear scars from before a certain time.
        
        Note: This doesn't actually remove curvature, but could
        be used to filter trauma_log. Real scar removal would
        require recalculating the curvature field.
        
        Args:
            before_timestamp: Clear events before this time
        """
        # Filter log (actual curvature would need field reset)
        self.trauma_log = [
            e for e in self.trauma_log
            if e.timestamp >= before_timestamp
        ]


class AdaptiveTraumaMemory(TraumaMemory):
    """
    Trauma memory that adapts its parameters based on experience.
    
    Learns optimal scar spread and severity scaling from
    the organism's survival history.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.survival_count = 0
        self.near_death_count = 0
    
    def record_survival(self):
        """Record that the organism survived another step."""
        self.survival_count += 1
    
    def record_near_death(self):
        """Record a near-death experience."""
        self.near_death_count += 1
        
        # Near-death experiences create stronger scars
        self.severity_multiplier *= 1.2
    
    def adapt_parameters(self):
        """
        Adapt trauma parameters based on survival history.
        
        If organism keeps dying despite scars, increase scar intensity.
        """
        if self.survival_count > 0:
            death_rate = self.near_death_count / self.survival_count
            
            if death_rate > 0.3:
                # Dying too often - increase scar strength
                self.severity_multiplier = min(5.0, self.severity_multiplier * 1.1)
                self.curvature.params.avoidance_threshold *= 0.9
            elif death_rate < 0.05:
                # Safe enough - reduce scar strength
                self.severity_multiplier = max(0.5, self.severity_multiplier * 0.95)


# === Exports ===

__all__ = [
    "TraumaSeverity",
    "TraumaEvent",
    "AvoidanceDecision",
    "TraumaMemory",
    "AdaptiveTraumaMemory",
]
