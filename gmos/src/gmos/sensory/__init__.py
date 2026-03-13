"""
GM-OS Sensory Layer.

Exports sensory processing components:
- manifold: Sensory manifold state (ExternalChart, InternalChart, SensoryState)
- projection: Projection functions for world/internal state
- salience: Salience computation (novelty, relevance, surprise)
- sensory_connector: Connector for integrating with hosted agent
- anchors: Anchor authority functional and conflict resolution (per spec §5.3)
- receipts: Sensory receipt schema (receipt_sensory_micro.v1)
- cost_law: Observation cost law with budget enforcement
- operators: Dual-use morphism operators (O, Ξ, T)
- tension_bounds: Bounded-tension lemma
- verifier: Sensory verifier (RV_sens)
- fusion: Fusion with provenance preservation
- conflict: Conflict detection and resolution
"""

from gmos.sensory import manifold
from gmos.sensory import projection
from gmos.sensory import salience
from gmos.sensory import sensory_connector
from gmos.sensory import anchors
from gmos.sensory import receipts
from gmos.sensory import cost_law
from gmos.sensory import operators
from gmos.sensory import tension_bounds
from gmos.sensory import verifier
from gmos.sensory import fusion
from gmos.sensory import conflict
from gmos.sensory import curvature
from gmos.sensory import trauma

# Export commonly used classes
from gmos.sensory.sensory_connector import SensoryConnector, SensoryState, ProcessedPercept
from gmos.sensory.salience import SalienceScore
from gmos.sensory.manifold import SensoryState as ManifoldSensoryState

# Export dual-use substrate classes
from gmos.sensory.receipts import (
    SensoryReceipt,
    SensoryReceiptFactory,
    SourceTag,
    StepType,
    Verdict,
    RejectCode,
    SCHEMA_ID,
)
from gmos.sensory.cost_law import ObservationCostLaw, CostCoefficients
from gmos.sensory.operators import (
    ObservationOperator,
    IngressOperator,
    SemanticBridge,
    DualUseSensoryPipeline,
    SensoryPercept,
    ForceTerm,
    NoeticType,
)
from gmos.sensory.tension_bounds import BoundedTensionLemma, TensionBoundParameters
from gmos.sensory.verifier import SensoryVerifier, VerificationResult
from gmos.sensory.fusion import (
    FusionEngineWithProvenance,
    fuse_with_provenance,
    FusedPerceptWithProvenance,
    ProvenanceTrace,
)
from gmos.sensory.conflict import (
    ConflictDetector,
    ConflictResolver,
    ConflictStrategy,
    ConflictResult,
    ConflictSet,
)
from gmos.sensory.curvature import (
    CurvatureField,
    CurvatureField2D,
    CurvatureParameters,
)
from gmos.sensory.trauma import (
    TraumaMemory,
    AdaptiveTraumaMemory,
    TraumaSeverity,
    TraumaEvent,
    AvoidanceDecision,
)

__all__ = [
    # Modules
    "manifold",
    "projection", 
    "salience",
    "sensory_connector",
    "anchors",
    "receipts",
    "cost_law",
    "operators",
    "tension_bounds",
    "verifier",
    "fusion",
    "conflict",
    # Exported classes
    "SensoryConnector",
    "SensoryState", 
    "ProcessedPercept",
    "SalienceScore",
    "ManifoldSensoryState",
    # Dual-use substrate
    "SensoryReceipt",
    "SensoryReceiptFactory",
    "SourceTag",
    "StepType",
    "Verdict",
    "RejectCode",
    "SCHEMA_ID",
    "ObservationCostLaw",
    "CostCoefficients",
    "ObservationOperator",
    "IngressOperator",
    "SemanticBridge",
    "DualUseSensoryPipeline",
    "SensoryPercept",
    "ForceTerm",
    "NoeticType",
    "BoundedTensionLemma",
    "TensionBoundParameters",
    "SensoryVerifier",
    "VerificationResult",
    "FusionEngineWithProvenance",
    "fuse_with_provenance",
    "FusedPerceptWithProvenance",
    "ProvenanceTrace",
    "ConflictDetector",
    "ConflictResolver",
    "ConflictStrategy",
    "ConflictResult",
    "ConflictSet",
    # Curvature and trauma
    "CurvatureField",
    "CurvatureField2D",
    "CurvatureParameters",
    "TraumaMemory",
    "AdaptiveTraumaMemory",
    "TraumaSeverity",
    "TraumaEvent",
    "AvoidanceDecision",
]
