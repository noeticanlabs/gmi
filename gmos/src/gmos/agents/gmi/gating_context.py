"""
Gating Context Structures for Phase 4

Defines the context structures that gating decisions
are based on.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class TaskType(Enum):
    """Task types for gating decisions."""
    DIAGNOSIS = "diagnosis"
    TRIAGE = "triage"
    EVIDENCE_GATHERING = "evidence_gathering"
    UNKNOWN = "unknown"


class EvidenceType(Enum):
    """Types of evidence that can be requested."""
    SYMPTOM = "symptom"
    CONTEXT = "context"
    HISTORY = "history"
    SENSOR = "sensor"


class FailureType(Enum):
    """Types of failures for repair decisions."""
    BUDGET_EXCEEDED = "budget_exceeded"
    CONSTRAINT_VIOLATION = "constraint_violation"
    LOW_CONFIDENCE = "low_confidence"
    TIMEOUT = "timeout"
    VERIFICATION_FAILED = "verification_failed"
    UNKNOWN = "unknown"


@dataclass
class PerceptContext:
    """Context from the perception layer."""
    confidence: float = 0.5  # 0-1, how confident is perception
    ambiguity: float = 0.5   # 0-1, how ambiguous is the situation
    quality: float = 1.0     # 0-1, signal quality


@dataclass
class MemoryContext:
    """Context from memory retrieval."""
    relevance: float = 0.5   # 0-1, how relevant are retrieved memories
    confidence: float = 0.5  # 0-1, confidence in retrieved memories
    count: int = 0           # Number of memories retrieved
    noise_risk: float = 0.5  # 0-1, risk of memory contamination


@dataclass
class BudgetContext:
    """Context from budget state."""
    ratio: float = 1.0       # Current budget / total budget
    reserve_proximity: float = 0.0  # 0-1, how close to reserve floor
    spent: float = 0.0       # Amount spent
    remaining: float = 100.0  # Amount remaining


@dataclass
class RiskContext:
    """Context about potential risks."""
    severity: float = 0.5    # 0-1, estimated harm if wrong
    reversibility: float = 0.5  # 0-1, how reversible is a wrong decision
    downstream_impact: float = 0.5  # 0-1, impact on future episodes


@dataclass
class VerifierContext:
    """Context from the verifier."""
    score: float = 0.5       # 0-1, verifier confidence
    passed: bool = True       # Whether verification passed
    issues: List[str] = field(default_factory=list)  # Issues found


@dataclass
class HistoryContext:
    """Context from episode history."""
    recent_failures: int = 0     # Consecutive failures
    total_episodes: int = 0      # Total episodes run
    recent_accuracy: float = 0.5  # Recent accuracy
    task_switched: bool = False   # Whether task switched recently


@dataclass
class GatingContext:
    """
    Complete context for gating decisions.
    
    This is assembled from all subsystem outputs
    and used by the gating policy to decide
    which features to enable.
    """
    # Task information
    task_type: TaskType = TaskType.UNKNOWN
    task_name: str = ""
    
    # Percept context
    percept: PerceptContext = field(default_factory=PerceptContext)
    
    # Memory context
    memory: MemoryContext = field(default_factory=MemoryContext)
    
    # Budget context
    budget: BudgetContext = field(default_factory=BudgetContext)
    
    # Risk context
    risk: RiskContext = field(default_factory=RiskContext)
    
    # Verifier context
    verifier: VerifierContext = field(default_factory=VerifierContext)
    
    # History context
    history: HistoryContext = field(default_factory=HistoryContext)
    
    # Episode information
    episode_id: str = ""
    step: int = 0
    
    # Available evidence types (for evidence request)
    available_evidence_types: List[EvidenceType] = field(default_factory=list)
    
    # Current confidence estimate (for calibration)
    estimated_confidence: float = 0.5
    
    # Raw features (for more complex gating)
    raw_features: Dict[str, Any] = field(default_factory=dict)
    
    def get_combined_confidence(self) -> float:
        """
        Get a combined confidence score from all sources.
        
        This is a simple average - more sophisticated
        combination could be learned.
        """
        scores = [
            self.percept.confidence,
            self.memory.confidence,
            self.verifier.score,
            self.estimated_confidence,
        ]
        return sum(scores) / len(scores)
    
    def should_use_memory(self) -> bool:
        """Quick check if memory might be useful."""
        return (
            self.memory.relevance > 0.3 and 
            self.memory.noise_risk < 0.6
        )
    
    def is_budget_critical(self) -> bool:
        """Check if budget is critical."""
        return (
            self.budget.ratio < 0.2 or 
            self.budget.reserve_proximity > 0.8
        )
    
    def is_high_risk(self) -> bool:
        """Check if this is a high-risk situation."""
        return (
            self.risk.severity > 0.7 or
            self.risk.downstream_impact > 0.7
        )


@dataclass
class MemoryGatingDecision:
    """Decision for memory gating."""
    use_memory: bool = False
    top_k: int = 0
    reasoning: str = ""
    confidence: float = 0.0


@dataclass
class SafeHoldGatingDecision:
    """Decision for SafeHold gating."""
    enable_safehold: bool = False
    threshold_override: Optional[float] = None
    reasoning: str = ""
    confidence: float = 0.0


@dataclass
class EvidenceGatingDecision:
    """Decision for evidence request gating."""
    request_evidence: bool = False
    evidence_type: Optional[EvidenceType] = None
    reasoning: str = ""
    expected_value: float = 0.0


@dataclass
class RepairGatingDecision:
    """Decision for repair gating."""
    enable_repair: bool = False
    max_attempts: int = 1
    reasoning: str = ""
    

@dataclass
class AdaptationGatingDecision:
    """Decision for adaptation gating."""
    apply_adaptation: bool = False
    learning_rate: float = 0.1
    reasoning: str = ""


@dataclass
class GatingDecision:
    """
    Complete gating decision combining all feature gates.
    """
    episode_id: str = ""
    task_type: TaskType = TaskType.UNKNOWN
    
    # Individual feature decisions
    memory: MemoryGatingDecision = field(default_factory=MemoryGatingDecision)
    safehold: SafeHoldGatingDecision = field(default_factory=SafeHoldGatingDecision)
    evidence: EvidenceGatingDecision = field(default_factory=EvidenceGatingDecision)
    repair: RepairGatingDecision = field(default_factory=RepairGatingDecision)
    adaptation: AdaptationGatingDecision = field(default_factory=AdaptationGatingDecision)
    
    # Combined decision
    combined_confidence: float = 0.5
    
    # Metadata
    timestamp: float = 0.0
    
    def get_enabled_features(self) -> List[str]:
        """Get list of enabled features."""
        enabled = []
        if self.memory.use_memory:
            enabled.append("memory")
        if self.safehold.enable_safehold:
            enabled.append("safehold")
        if self.evidence.request_evidence:
            enabled.append("evidence_request")
        if self.repair.enable_repair:
            enabled.append("repair")
        if self.adaptation.apply_adaptation:
            enabled.append("adaptation")
        return enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "episode_id": self.episode_id,
            "task_type": self.task_type.value,
            "enabled_features": self.get_enabled_features(),
            "memory": {
                "use_memory": self.memory.use_memory,
                "top_k": self.memory.top_k,
                "reasoning": self.memory.reasoning,
            },
            "safehold": {
                "enable": self.safehold.enable_safehold,
                "reasoning": self.safehold.reasoning,
            },
            "evidence": {
                "request": self.evidence.request_evidence,
                "type": self.evidence.evidence_type.value if self.evidence.evidence_type else None,
                "reasoning": self.evidence.reasoning,
            },
            "repair": {
                "enable": self.repair.enable_repair,
                "reasoning": self.repair.reasoning,
            },
            "adaptation": {
                "apply": self.adaptation.apply_adaptation,
                "reasoning": self.adaptation.reasoning,
            },
            "combined_confidence": self.combined_confidence,
            "timestamp": self.timestamp,
        }
