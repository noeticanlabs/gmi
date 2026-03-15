"""
Feature Gating Policy for Phase 4

The core of Phase 4: selective intelligence about when to use
substrate features (memory, SafeHold, repair, evidence request, adaptation).

This policy takes context from all subsystems and decides which
features should be enabled for the current episode.
"""

import os
import sys
import time
from typing import List, Optional, Dict, Any

# Add current directory to path for imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    from gating_config import (
        GatingConfig,
        MemoryGatingConfig,
        SafeHoldGatingConfig,
        EvidenceGatingConfig,
        RepairGatingConfig,
        AdaptationGatingConfig,
        create_default_gating_config,
        create_task_specific_config,
    )
    from gating_context import (
        GatingContext,
        GatingDecision,
        MemoryGatingDecision,
        SafeHoldGatingDecision,
        EvidenceGatingDecision,
        RepairGatingDecision,
        AdaptationGatingDecision,
        TaskType,
        EvidenceType,
        FailureType,
    )
except ImportError:
    # Fallback for when run from different directory
    from gmos.agents.gmi.gating_config import (
        GatingConfig,
        MemoryGatingConfig,
        SafeHoldGatingConfig,
        EvidenceGatingConfig,
        RepairGatingConfig,
        AdaptationGatingConfig,
        create_default_gating_config,
        create_task_specific_config,
    )
    from gmos.agents.gmi.gating_context import (
        GatingContext,
        GatingDecision,
        MemoryGatingDecision,
        SafeHoldGatingDecision,
        EvidenceGatingDecision,
        RepairGatingDecision,
        AdaptationGatingDecision,
        TaskType,
        EvidenceType,
        FailureType,
    )


class GatingPolicy:
    """
    Feature gating policy for selective substrate intelligence.
    
    This is the main entry point for making gating decisions.
    It combines all the individual feature gating logic.
    """
    
    def __init__(
        self,
        config: Optional[GatingConfig] = None,
        task_name: str = "",
    ):
        """
        Initialize the gating policy.
        
        Args:
            config: Gating configuration. If None, uses defaults.
            task_name: Name of the current task for task-specific tuning.
        """
        self.config = config or create_default_gating_config()
        self.task_name = task_name
        
        # Apply task-specific config if provided
        if task_name:
            self.config = create_task_specific_config(task_name)
        
        # Decision history for analysis
        self.decision_history: List[GatingDecision] = []
        
        # Statistics
        self.stats = {
            "memory_enabled_count": 0,
            "memory_disabled_count": 0,
            "safehold_enabled_count": 0,
            "evidence_requested_count": 0,
            "repair_enabled_count": 0,
            "adaptation_applied_count": 0,
        }
    
    def compute_gating(
        self,
        context: GatingContext,
    ) -> GatingDecision:
        """
        Compute gating decision based on current context.
        
        This is the main method - it takes context from all
        subsystems and produces a complete gating decision.
        
        Args:
            context: Current episode context
            
        Returns:
            GatingDecision with all feature enable/disable flags
        """
        # Check if gating is enabled
        if not self.config.enable_gating:
            return self._create_always_on_decision(context)
        
        # Compute individual feature decisions
        memory_decision = self._compute_memory_gating(context)
        safehold_decision = self._compute_safehold_gating(context)
        evidence_decision = self._compute_evidence_gating(context)
        repair_decision = self._compute_repair_gating(context)
        adaptation_decision = self._compute_adaptation_gating(context)
        
        # Combine into complete decision
        decision = GatingDecision(
            episode_id=context.episode_id,
            task_type=context.task_type,
            memory=memory_decision,
            safehold=safehold_decision,
            evidence=evidence_decision,
            repair=repair_decision,
            adaptation=adaptation_decision,
            combined_confidence=context.get_combined_confidence(),
            timestamp=time.time(),
        )
        
        # Update statistics
        self._update_stats(decision)
        
        # Store in history
        self.decision_history.append(decision)
        
        return decision
    
    def _create_always_on_decision(
        self,
        context: GatingContext,
    ) -> GatingDecision:
        """Create decision with all features enabled (no gating)."""
        return GatingDecision(
            episode_id=context.episode_id,
            task_type=context.task_type,
            memory=MemoryGatingDecision(
                use_memory=True,
                top_k=self.config.memory.default_top_k,
                reasoning="Always-on mode",
            ),
            safehold=SafeHoldGatingDecision(
                enable_safehold=True,
                reasoning="Always-on mode",
            ),
            evidence=EvidenceGatingDecision(
                request_evidence=True,
                reasoning="Always-on mode",
            ),
            repair=RepairGatingDecision(
                enable_repair=True,
                reasoning="Always-on mode",
            ),
            adaptation=AdaptationGatingDecision(
                apply_adaptation=True,
                reasoning="Always-on mode",
            ),
            combined_confidence=context.get_combined_confidence(),
            timestamp=time.time(),
        )
    
    def _compute_memory_gating(
        self,
        context: GatingContext,
    ) -> MemoryGatingDecision:
        """
        Decide whether to use memory and how many memories to retrieve.
        
        Phase 3 insight: Memory helps Task B (+53%) but not Task A (0%).
        """
        config = self.config.memory
        
        # Get task-specific benefit rate
        task_benefit = config.task_benefit_map.get(self.task_name, None)
        
        # Check if we have evidence that memory helps this task
        if task_benefit is not None and task_benefit < 0:
            # Memory has hurt this task - disable
            return MemoryGatingDecision(
                use_memory=False,
                top_k=0,
                reasoning=f"Memory harmful on {self.task_name} (benefit: {task_benefit})",
                confidence=task_benefit,
            )
        
        # Check relevance threshold
        if context.memory.relevance < config.relevance_threshold:
            return MemoryGatingDecision(
                use_memory=False,
                top_k=0,
                reasoning=f"Memory relevance {context.memory.relevance:.2f} below threshold {config.relevance_threshold}",
                confidence=context.memory.relevance,
            )
        
        # Check confidence threshold
        if context.memory.confidence < config.confidence_threshold:
            return MemoryGatingDecision(
                use_memory=False,
                top_k=0,
                reasoning=f"Memory confidence {context.memory.confidence:.2f} below threshold {config.confidence_threshold}",
                confidence=context.memory.confidence,
            )
        
        # Check noise risk
        if context.memory.noise_risk > config.noise_risk_threshold:
            # High risk of contamination - use fewer memories
            top_k = max(1, config.default_top_k // 2)
            return MemoryGatingDecision(
                use_memory=True,
                top_k=top_k,
                reasoning=f"Noise risk high ({context.memory.noise_risk:.2f}), limiting to {top_k} memories",
                confidence=1 - context.memory.noise_risk,
            )
        
        # Default: use memory with configured top-k
        # Scale top-k based on relevance
        if context.memory.relevance > 0.8:
            top_k = config.max_top_k
        elif context.memory.relevance > 0.6:
            top_k = config.default_top_k
        else:
            top_k = max(2, config.default_top_k // 2)
        
        return MemoryGatingDecision(
            use_memory=True,
            top_k=min(top_k, config.max_top_k),
            reasoning=f"Memory relevant ({context.memory.relevance:.2f}), using {top_k} memories",
            confidence=context.memory.relevance,
        )
    
    def _compute_safehold_gating(
        self,
        context: GatingContext,
    ) -> SafeHoldGatingDecision:
        """
        Decide whether to enable SafeHold pathway.
        
        Phase 3 insight: SafeHold was overactive (67% rate) and hurt accuracy.
        Need calibrated thresholds.
        """
        config = self.config.safehold
        
        # Get current confidence
        confidence = context.get_combined_confidence()
        
        # Check budget criticality
        if context.is_budget_critical():
            return SafeHoldGatingDecision(
                enable_safehold=True,
                threshold_override=config.low_confidence_threshold,
                reasoning=f"Budget critical ({context.budget.ratio:.2f}), enabling SafeHold",
                confidence=confidence,
            )
        
        # Check high risk situation
        if context.is_high_risk():
            # Elevate threshold in high-risk situations
            adjusted_threshold = min(
                config.high_confidence_threshold,
                confidence + 0.1
            )
            if confidence < adjusted_threshold:
                return SafeHoldGatingDecision(
                    enable_safehold=True,
                    threshold_override=adjusted_threshold,
                    reasoning=f"High risk ({context.risk.severity:.2f}), elevated threshold",
                    confidence=confidence,
                )
        
        # Check consecutive failures
        if context.history.recent_failures >= config.max_consecutive_holds:
            return SafeHoldGatingDecision(
                enable_safehold=True,
                threshold_override=config.low_confidence_threshold,
                reasoning=f"Too many consecutive failures ({context.history.recent_failures})",
                confidence=confidence,
            )
        
        # Use calibrated or fixed threshold
        if confidence >= config.high_confidence_threshold:
            # High confidence - no SafeHold needed
            return SafeHoldGatingDecision(
                enable_safehold=False,
                reasoning=f"High confidence ({confidence:.2f})",
                confidence=confidence,
            )
        elif confidence >= config.medium_confidence_threshold:
            # Medium confidence - maybe, but not urgent
            return SafeHoldGatingDecision(
                enable_safehold=False,
                reasoning=f"Medium confidence ({confidence:.2f}), proceeding with caution",
                confidence=confidence,
            )
        else:
            # Low confidence - enable SafeHold
            return SafeHoldGatingDecision(
                enable_safehold=True,
                threshold_override=config.low_confidence_threshold,
                reasoning=f"Low confidence ({confidence:.2f}), enabling SafeHold",
                confidence=confidence,
            )
    
    def _compute_evidence_gating(
        self,
        context: GatingContext,
    ) -> EvidenceGatingDecision:
        """
        Decide whether to request additional evidence.
        
        This is a key Phase 4 feature - instead of just
        proceeding or abstaining, the system can ask for more info.
        """
        config = self.config.evidence
        
        # Check if evidence request is enabled
        if not config.enabled:
            return EvidenceGatingDecision(
                request_evidence=False,
                reasoning="Evidence request disabled in config",
            )
        
        # Check max requests per episode
        # (Track this in context for now, simplified)
        
        # Get current confidence
        confidence = context.get_combined_confidence()
        
        # Evidence request makes sense in medium confidence range
        if confidence < config.min_confidence:
            # Too uncertain - should probably abstain, not request evidence
            return EvidenceGatingDecision(
                request_evidence=False,
                reasoning=f"Confidence too low ({confidence:.2f}) for evidence request",
                expected_value=0.0,
            )
        
        if confidence > config.max_confidence:
            # Confidence high enough - proceed
            return EvidenceGatingDecision(
                request_evidence=False,
                reasoning=f"Confidence high enough ({confidence:.2f})",
                expected_value=0.0,
            )
        
        # In medium range - consider evidence request
        # Check if there's evidence available
        if not context.available_evidence_types:
            return EvidenceGatingDecision(
                request_evidence=False,
                reasoning="No evidence types available to request",
                expected_value=0.0,
            )
        
        # Check expected value
        expected_value = self._estimate_evidence_value(context)
        
        if expected_value < config.evidence_value_threshold:
            return EvidenceGatingDecision(
                request_evidence=False,
                reasoning=f"Expected evidence value ({expected_value:.2f}) below threshold",
                expected_value=expected_value,
            )
        
        # Select best evidence type
        best_evidence = self._select_best_evidence_type(context)
        
        return EvidenceGatingDecision(
            request_evidence=True,
            evidence_type=best_evidence,
            reasoning=f"Medium confidence ({confidence:.2f}), requesting {best_evidence.value}",
            expected_value=expected_value,
        )
    
    def _estimate_evidence_value(self, context: GatingContext) -> float:
        """
        Estimate the expected value of requesting more evidence.
        
        This is a simple heuristic - could be learned.
        """
        # Higher value if:
        # - Ambiguity is high (evidence would help disambiguate)
        # - Risk is high (evidence would reduce risk)
        # - Current memories are not too confident
        
        ambiguity_factor = context.percept.ambiguity
        risk_factor = context.risk.severity
        memory_factor = 1.0 - context.memory.confidence
        
        # Weighted combination
        value = (
            ambiguity_factor * 0.4 +
            risk_factor * 0.4 +
            memory_factor * 0.2
        )
        
        return min(1.0, value)
    
    def _select_best_evidence_type(
        self,
        context: GatingContext,
    ) -> EvidenceType:
        """Select the best type of evidence to request."""
        # Simple heuristic: prefer evidence that addresses ambiguity
        if context.percept.ambiguity > 0.6:
            # High ambiguity - prefer symptom evidence
            return EvidenceType.SYMPTOM
        elif context.risk.severity > 0.6:
            # High risk - prefer context
            return EvidenceType.CONTEXT
        else:
            # Default to symptom
            return EvidenceType.SYMPTOM
    
    def _compute_repair_gating(
        self,
        context: GatingContext,
    ) -> RepairGatingDecision:
        """
        Decide whether to enable repair pathway.
        
        Repair is attempted after verification failure.
        """
        config = self.config.repair
        
        if not config.enabled:
            return RepairGatingDecision(
                enable_repair=False,
                reasoning="Repair disabled in config",
            )
        
        # Check budget
        if context.budget.ratio < config.budget_threshold:
            return RepairGatingDecision(
                enable_repair=False,
                max_attempts=0,
                reasoning=f"Budget too low ({context.budget.ratio:.2f}) for repair",
            )
        
        # Check if we have verification issues
        if context.verifier.passed:
            # No failure, no repair needed
            return RepairGatingDecision(
                enable_repair=False,
                reasoning="Verification passed, no repair needed",
            )
        
        # Verification failed - consider repair
        # Check if failure type is repairable
        failure_type = self._identify_failure_type(context)
        
        if failure_type.value not in [f.value for f in config.repairable_failure_types]:
            return RepairGatingDecision(
                enable_repair=False,
                reasoning=f"Failure type ({failure_type.value}) not repairable",
            )
        
        return RepairGatingDecision(
            enable_repair=True,
            max_attempts=config.max_attempts,
            reasoning=f"Repairable failure ({failure_type.value}), enabling repair",
        )
    
    def _identify_failure_type(
        self,
        context: GatingContext,
    ) -> Any:
        """Identify the type of failure from verifier context."""
        # Check verifier issues for clues
        issues = context.verifier.issues
        
        if any("budget" in i.lower() for i in issues):
            return FailureType.BUDGET_EXCEEDED
        elif any("constraint" in i.lower() for i in issues):
            return FailureType.CONSTRAINT_VIOLATION
        elif any("confidence" in i.lower() for i in issues):
            return FailureType.LOW_CONFIDENCE
        elif context.verifier.score < 0.3:
            return FailureType.LOW_CONFIDENCE
        else:
            return FailureType.VERIFICATION_FAILED
    
    def _compute_adaptation_gating(
        self,
        context: GatingContext,
    ) -> AdaptationGatingDecision:
        """
        Decide whether to apply adaptation updates.
        
        Adaptation learns from episode outcomes.
        """
        config = self.config.adaptation
        
        if not config.enabled:
            return AdaptationGatingDecision(
                apply_adaptation=False,
                reasoning="Adaptation disabled in config",
            )
        
        # Check minimum episodes
        if context.history.total_episodes < config.min_episodes:
            return AdaptationGatingDecision(
                apply_adaptation=False,
                reasoning=f"Only {context.history.total_episodes} episodes, need {config.min_episodes}",
            )
        
        # Check recent accuracy
        if context.history.recent_accuracy > (1.0 - config.failure_threshold):
            # Doing well - don't change
            return AdaptationGatingDecision(
                apply_adaptation=False,
                reasoning=f"Recent accuracy good ({context.history.recent_accuracy:.2f})",
            )
        
        # Low accuracy - consider adaptation
        return AdaptationGatingDecision(
            apply_adaptation=True,
            learning_rate=config.learning_rate,
            reasoning=f"Recent accuracy ({context.history.recent_accuracy:.2f}) below threshold, applying adaptation",
        )
    
    def _update_stats(self, decision: GatingDecision):
        """Update statistics with a decision."""
        if decision.memory.use_memory:
            self.stats["memory_enabled_count"] += 1
        else:
            self.stats["memory_disabled_count"] += 1
        
        if decision.safehold.enable_safehold:
            self.stats["safehold_enabled_count"] += 1
        
        if decision.evidence.request_evidence:
            self.stats["evidence_requested_count"] += 1
        
        if decision.repair.enable_repair:
            self.stats["repair_enabled_count"] += 1
        
        if decision.adaptation.apply_adaptation:
            self.stats["adaptation_applied_count"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gating statistics."""
        total = sum(self.stats.values())
        return {
            **self.stats,
            "total_decisions": len(self.decision_history),
            "memory_enabled_rate": self.stats["memory_enabled_count"] / max(1, total),
            "safehold_enabled_rate": self.stats["safehold_enabled_count"] / max(1, total),
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "memory_enabled_count": 0,
            "memory_disabled_count": 0,
            "safehold_enabled_count": 0,
            "evidence_requested_count": 0,
            "repair_enabled_count": 0,
            "adaptation_applied_count": 0,
        }
        self.decision_history = []


def create_gating_policy(
    task_name: str = "",
    enable_gating: bool = True,
) -> GatingPolicy:
    """
    Factory function to create a gating policy.
    
    Args:
        task_name: Name of task for task-specific tuning
        enable_gating: Whether to enable gating (False = always-on)
        
    Returns:
        Configured GatingPolicy
    """
    config = create_task_specific_config(task_name) if task_name else create_default_gating_config()
    config.enable_gating = enable_gating
    return GatingPolicy(config=config, task_name=task_name)
