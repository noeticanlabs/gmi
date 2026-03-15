"""
Cross-Episode Adaptation System for Phase 3

Implements lightweight adaptation mechanisms that improve performance
based on prior episode data without full retraining.

Allowed mechanisms:
- Memory utility reweighting
- Retrieval score updates  
- Policy threshold calibration
- Failure pattern tagging
- Proposal ranking adjustments
- Confidence calibration

NOT included:
- Gradient-based learning
- Model retraining
- Core logic mutation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict


class FailureType(Enum):
    """Types of failures that can be learned from."""
    VERIFICATION_REJECTED = "verification_rejected"
    BUDGET_EXHAUSTED = "budget_exhausted"
    MEMORY_USELESS = "memory_useless"
    MEMORY_HARMFUL = "memory_harmful"
    PROPOSAL_INVALID = "proposal_invalid"
    CONFIDENCE_MISaligned = "confidence_miscalibrated"
    SAFE_HOLD_APPROPRIATE = "safe_hold_appropriate"
    SAFE_HOLD_MISSED = "safe_hold_missed"
    REPAIR_FAILED = "repair_failed"
    UNKNOWN = "unknown"


@dataclass
class RetrievalOutcome:
    """Outcome of a memory retrieval."""
    episode_id: str
    was_used: bool
    helped: bool          # Retrieval improved decision
    hurt: bool           # Retrieval hurt decision
    action_taken: str
    outcome_success: bool


@dataclass
class AdaptationOutcome:
    """Result of an episode for adaptation purposes."""
    episode_id: str
    task_type: str        # "diagnosis" or "triage"
    success: bool
    memory_used: bool
    memory_helped: bool   # Did memory improve outcome?
    failures: List[FailureType]
    confidence: float
    actual_correct: bool
    
    # For memory adaptation
    retrievals: List[RetrievalOutcome] = field(default_factory=list)
    
    # For proposal adaptation
    proposals_considered: int = 0
    proposals_accepted: int = 0
    proposals_rejected: int = 0


@dataclass
class FailurePattern:
    """Pattern of failures that can be used for adaptation."""
    pattern_id: str
    failure_type: FailureType
    occurrence_count: int = 1
    last_seen: float = 0.0
    symptoms: Dict[str, Any] = field(default_factory=dict)
    
    # What to do when this pattern is detected
    recommended_action: Optional[str] = None
    confidence_adjustment: float = 0.0


@dataclass
class AdaptationConfig:
    """Configuration for adaptation behavior."""
    # Memory reweighting
    enable_memory_reweight: bool = True
    memory_help_bonus: float = 1.1      # Multiply weight when memory helps
    memory_harm_penalty: float = 0.9    # Multiply weight when memory hurts
    reweight_window: int = 10           # Episodes to consider for reweighting
    
    # Retrieval score adaptation
    enable_retrieval_adaptation: bool = True
    score_update_rate: float = 0.1      # How fast to update scores
    
    # Threshold calibration
    enable_threshold_calibration: bool = True
    confidence_adjustment_rate: float = 0.05
    
    # Failure pattern
    enable_failure_patterns: bool = True
    min_pattern_occurrences: int = 3
    
    # Rollback
    enable_rollback: bool = True
    max_consecutive_failures: int = 5


class AdaptationTracker:
    """
    Tracks adaptation state across episodes.
    
    Provides mechanisms to:
    - Record episode outcomes
    - Identify failure patterns
    - Adjust memory weights
    - Calibrate confidence
    """
    
    def __init__(self, config: Optional[AdaptationConfig] = None):
        self.config = config or AdaptationConfig()
        
        # Episode history
        self.outcomes: List[AdaptationOutcome] = []
        
        # Memory utility by retrieval type
        self.memory_utility: Dict[str, float] = defaultdict(lambda: 1.0)
        
        # Failure patterns
        self.failure_patterns: Dict[str, FailurePattern] = {}
        
        # Confidence calibration
        self.confidence_errors: List[float] = []
        
        # Proposal statistics
        self.proposal_stats: Dict[str, int] = defaultdict(int)
        
        # Adaptation state
        self._enabled = True
        self._consecutive_failures = 0
        self._last_adaptation_epoch = 0
    
    def record_outcome(self, outcome: AdaptationOutcome) -> None:
        """Record an episode outcome for adaptation."""
        if not self._enabled:
            return
        
        self.outcomes.append(outcome)
        
        # Track consecutive failures
        if outcome.success:
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1
        
        # Check for rollback condition
        if (self.config.enable_rollback and 
            self._consecutive_failures >= self.config.max_consecutive_failures):
            self._rollback()
        
        # Update memory utility
        if self.config.enable_memory_reweight and outcome.memory_used:
            self._update_memory_utility(outcome)
        
        # Update failure patterns
        if self.config.enable_failure_patterns:
            self._update_failure_patterns(outcome)
        
        # Update confidence calibration
        if outcome.memory_used:
            error = abs(outcome.confidence - (1.0 if outcome.actual_correct else 0.0))
            self.confidence_errors.append(error)
            if len(self.confidence_errors) > 100:
                self.confidence_errors.pop(0)
    
    def get_memory_weight(self, retrieval_type: str) -> float:
        """Get the current weight for a retrieval type."""
        return self.memory_utility.get(retrieval_type, 1.0)
    
    def get_confidence_adjustment(self) -> float:
        """Get confidence calibration adjustment."""
        if not self.confidence_errors:
            return 0.0
        
        mean_error = sum(self.confidence_errors) / len(self.confidence_errors) if self.confidence_errors else 0.0
        
        # Positive = overconfident, negative = underconfident
        return -mean_error * self.config.confidence_adjustment_rate
    
    def get_recommended_action(
        self,
        symptoms: Dict[str, Any],
        failures: List[FailureType]
    ) -> Optional[str]:
        """Get recommended action based on failure patterns."""
        if not self.config.enable_failure_patterns:
            return None
        
        # Find matching patterns
        matches = []
        for pattern in self.failure_patterns.values():
            if pattern.failure_type in failures:
                if pattern.occurrence_count >= self.config.min_pattern_occurrences:
                    matches.append(pattern)
        
        if not matches:
            return None
        
        # Return most common recommendation
        recommendations = [p.recommended_action for p in matches if p.recommended_action]
        if recommendations:
            return max(set(recommendations), key=recommendations.count)
        
        return None
    
    def get_adaptation_summary(self) -> Dict[str, Any]:
        """Get summary of adaptation state."""
        recent_outcomes = self.outcomes[-20:] if self.outcomes else []
        
        return {
            "total_episodes": len(self.outcomes),
            "success_rate": sum(1 for o in recent_outcomes if o.success) / len(recent_outcomes) if recent_outcomes else 0,
            "memory_help_rate": sum(1 for o in recent_outcomes if o.memory_helped) / len(recent_outcomes) if recent_outcomes else 0,
            "consecutive_failures": self._consecutive_failures,
            "memory_weights": dict(self.memory_utility),
            "failure_patterns_count": len(self.failure_patterns),
            "confidence_adjustment": self.get_confidence_adjustment()
        }
    
    def enable(self) -> None:
        """Enable adaptation."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable adaptation."""
        self._enabled = False
    
    def reset(self) -> None:
        """Reset adaptation state."""
        self.outcomes.clear()
        self.memory_utility.clear()
        self.failure_patterns.clear()
        self.confidence_errors.clear()
        self.proposal_stats.clear()
        self._consecutive_failures = 0
    
    def _update_memory_utility(self, outcome: AdaptationOutcome) -> None:
        """Update memory utility weights based on outcome."""
        
        for retrieval in outcome.retrievals:
            if not retrieval.was_used:
                continue
            
            retrieval_type = retrieval.episode_id
            
            if retrieval.helped:
                # Memory helped - increase weight
                current = self.memory_utility[retrieval_type]
                self.memory_utility[retrieval_type] = min(
                    current * self.config.memory_help_bonus,
                    2.0  # Cap at 2x
                )
            elif retrieval.hurt:
                # Memory hurt - decrease weight
                current = self.memory_utility[retrieval_type]
                self.memory_utility[retrieval_type] = max(
                    current * self.config.memory_harm_penalty,
                    0.5  # Floor at 0.5x
                )
    
    def _update_failure_patterns(self, outcome: AdaptationOutcome) -> None:
        """Update failure pattern database."""
        
        import time
        now = time.time()
        
        for failure in outcome.failures:
            pattern_id = f"{outcome.task_type}_{failure.value}"
            
            if pattern_id in self.failure_patterns:
                pattern = self.failure_patterns[pattern_id]
                pattern.occurrence_count += 1
                pattern.last_seen = now
            else:
                pattern = FailurePattern(
                    pattern_id=pattern_id,
                    failure_type=failure,
                    last_seen=now,
                    symptoms=outcome.failures[0].__dict__ if outcome.failures else {}
                )
                self.failure_patterns[pattern_id] = pattern
            
            # Update recommendations based on success/failure
            if failure == FailureType.SAFE_HOLD_MISSED and not outcome.success:
                pattern.recommended_action = "safe_hold"
            elif failure == FailureType.VERIFICATION_REJECTED:
                pattern.recommended_action = "repair"
            elif failure == FailureType.MEMORY_HARMFUL:
                pattern.recommended_action = "ignore_memory"
    
    def _rollback(self) -> None:
        """Rollback recent adaptations if too many failures."""
        # Reset to previous stable state
        if len(self.outcomes) > self.config.reweight_window:
            # Keep only outcomes before the failure streak
            rollback_point = len(self.outcomes) - self.config.reweight_window
            self.outcomes = self.outcomes[:rollback_point]
            
            # Reset memory weights to defaults
            self.memory_utility.clear()
            
            # Reset confidence calibration
            self.confidence_errors.clear()
            
            print(f"ADAPTATION: Rolled back after {self._consecutive_failures} consecutive failures")


def create_adaptation_tracker(
    enable_memory_reweight: bool = True,
    enable_failure_patterns: bool = True,
    enable_rollback: bool = True
) -> AdaptationTracker:
    """Factory function to create an adaptation tracker."""
    
    config = AdaptationConfig(
        enable_memory_reweight=enable_memory_reweight,
        enable_failure_patterns=enable_failure_patterns,
        enable_rollback=enable_rollback
    )
    
    return AdaptationTracker(config)
