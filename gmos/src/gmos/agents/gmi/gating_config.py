"""
Gating Configuration Classes for Phase 4

Defines configuration for selective feature activation:
- Memory gating
- SafeHold gating
- Evidence request gating
- Repair gating
- Adaptation gating
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MemoryGatingConfig:
    """
    Configuration for memory gating decisions.
    
    Controls when to use memory retrieval and how many
    memories to retrieve.
    """
    # Threshold for using memory at all
    relevance_threshold: float = 0.5
    
    # Minimum confidence in retrieved memories
    confidence_threshold: float = 0.4
    
    # Task-specific memory benefit rates (from Phase 3)
    # Task -> benefit rate (None = unknown)
    task_benefit_map: Dict[str, float] = field(default_factory=lambda: {
        "diagnosis": 0.0,    # Task A: no benefit
        "triage": 0.53,       # Task B: +53% benefit
        "evidence_gathering": None,  # Task C: TBD
    })
    
    # Maximum memories to retrieve
    max_top_k: int = 10
    
    # Default top-k when memory is used
    default_top_k: int = 5
    
    # Risk threshold for memory contamination
    noise_risk_threshold: float = 0.6


@dataclass
class SafeHoldGatingConfig:
    """
    Configuration for SafeHold (abstention) gating.
    
    Controls when to enable the SafeHold pathway
    based on confidence, budget, and risk.
    """
    # Confidence thresholds
    high_confidence_threshold: float = 0.8
    medium_confidence_threshold: float = 0.5
    low_confidence_threshold: float = 0.3
    
    # Budget threshold (enable SafeHold when budget is low)
    budget_threshold: float = 0.2
    
    # Risk severity threshold
    risk_threshold: float = 0.7
    
    # Maximum consecutive SafeHolds before forcing action
    max_consecutive_holds: int = 3
    
    # Whether to use calibrated thresholds (vs fixed)
    use_calibrated_thresholds: bool = True
    
    # Calibrated thresholds (set after calibration runs)
    calibrated_thresholds: Optional[Dict[str, float]] = None


@dataclass
class EvidenceGatingConfig:
    """
    Configuration for evidence request gating.
    
    Controls when to request additional evidence
    instead of proceeding or abstaining.
    """
    # Confidence range where evidence request makes sense
    min_confidence: float = 0.3
    max_confidence: float = 0.7
    
    # Expected value threshold for evidence
    evidence_value_threshold: float = 0.5
    
    # Whether evidence request is enabled at all
    enabled: bool = True
    
    # Maximum evidence requests per episode
    max_requests_per_episode: int = 1
    
    # Evidence type preferences
    preferred_evidence_types: List[str] = field(default_factory=lambda: [
        "symptom",
        "context", 
        "history",
        "sensor"
    ])


@dataclass
class RepairGatingConfig:
    """
    Configuration for repair pathway gating.
    
    Controls when to attempt repair after
    proposal verification failure.
    """
    # Maximum repair attempts per episode
    max_attempts: int = 2
    
    # Failure types that are repairable
    repairable_failure_types: List[str] = field(default_factory=lambda: [
        "budget_exceeded",
        "constraint_violation",
        "low_confidence",
    ])
    
    # Budget threshold for repair
    budget_threshold: float = 0.3
    
    # Whether repair is enabled
    enabled: bool = True
    
    # Maximum consecutive repair failures before disabling
    max_consecutive_failures: int = 2


@dataclass
class AdaptationGatingConfig:
    """
    Configuration for adaptation gating.
    
    Controls when to update adaptation weights
    based on episode outcomes.
    """
    # Minimum episodes before applying adaptation
    min_episodes: int = 5
    
    # Failure rate threshold for triggering adaptation
    failure_threshold: float = 0.3
    
    # Learning rate for weight updates
    learning_rate: float = 0.1
    
    # Whether adaptation is enabled
    enabled: bool = True
    
    # Maximum weight change per episode
    max_weight_change: float = 0.2


@dataclass
class GatingConfig:
    """
    Master gating configuration combining all feature gates.
    """
    memory: MemoryGatingConfig = field(default_factory=MemoryGatingConfig)
    safehold: SafeHoldGatingConfig = field(default_factory=SafeHoldGatingConfig)
    evidence: EvidenceGatingConfig = field(default_factory=EvidenceGatingConfig)
    repair: RepairGatingConfig = field(default_factory=RepairGatingConfig)
    adaptation: AdaptationGatingConfig = field(default_factory=AdaptationGatingConfig)
    
    # Master switch - if False, all features use always-on behavior
    enable_gating: bool = True
    
    # Whether to log gating decisions
    log_decisions: bool = True


def create_default_gating_config() -> GatingConfig:
    """Create default gating configuration."""
    return GatingConfig()


def create_task_specific_config(task_name: str) -> GatingConfig:
    """
    Create task-specific gating configuration.
    
    Different tasks may need different gating strategies
    based on what we know about their memory/feature benefit.
    """
    config = GatingConfig()
    
    # Task-specific SafeHold thresholds
    if task_name == "diagnosis":
        # Task A: Memory doesn't help, so disable memory gating
        config.memory.relevance_threshold = 0.8  # Only use memory if very relevant
        config.memory.default_top_k = 2  # Conservative memory use
        
    elif task_name == "triage":
        # Task B: Memory helps significantly
        config.memory.relevance_threshold = 0.4  # More aggressive memory use
        config.memory.default_top_k = 7  # More memories
        
    elif task_name == "evidence_gathering":
        # Task C: New task - start with balanced config
        config.memory.relevance_threshold = 0.5
        config.evidence.enabled = True  # Enable evidence requests
        
    return config
