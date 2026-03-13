"""
Dual-Use Morphism Operators for Sensory Substrate.

Per spec §4: The substrate has two principal morphisms:

1. ObservationOperator (O): U_world → X_sens
   - GM-OS role: World-facing observation map
   - Takes world events and projects them into sensory state

2. IngressOperator (Ξ): X_sens → U_force
   - GMI role: Organism-facing "optic nerve"
   - Maps sensory objects into bounded forcing term

3. SemanticBridge (T_sens→Noe):
   - Converts typed percept to Noetican semantic type
   - Bridge from sensory to semantic manifold

This implements the core dual-use principle:
- For GM-OS, it is a boundary-and-observation system
- For GMI, it is the organism's perceptual organ
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Callable
import numpy as np
import hashlib
import json
import time


# === Base Types ===

@dataclass
class SensoryPercept:
    """
    A sensory percept object that exists in X_sens.
    
    This is the unified percept that serves both roles:
    - As a world observation (GM-OS perspective)
    - As a forcing input (GMI perspective)
    
    Per spec §3: The state space is split as:
    X_sens = X_ext ⊕ X_int ⊕ X_sem ⊕ X_anchor
    """
    # External state (X_ext)
    raw_observation: Any = None
    topology: Optional[Dict[str, Any]] = None
    quality: float = 1.0
    source: str = ""
    
    # Internal state (X_int)
    budget: float = 1.0
    tension: float = 0.0
    curvature: float = 0.0
    shell_stability: float = 1.0
    health: float = 1.0
    memory_pressure: float = 0.0
    
    # Semantic-preparatory state (X_sem)
    novelty: float = 0.0
    salience: float = 0.0
    relevance: float = 0.0
    context_alignment: float = 0.0
    
    # Anchor state (X_anchor)
    provenance: str = ""
    authority: float = 0.0
    conflict_markers: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    # Identity
    percept_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "percept_id": self.percept_id,
            "raw_observation": str(self.raw_observation) if self.raw_observation else None,
            "topology": self.topology,
            "quality": self.quality,
            "source": self.source,
            "budget": self.budget,
            "tension": self.tension,
            "curvature": self.curvature,
            "shell_stability": self.shell_stability,
            "health": self.health,
            "memory_pressure": self.memory_pressure,
            "novelty": self.novelty,
            "salience": self.salience,
            "relevance": self.relevance,
            "context_alignment": self.context_alignment,
            "provenance": self.provenance,
            "authority": self.authority,
            "conflict_markers": self.conflict_markers,
            "timestamp": self.timestamp,
        }
    
    def compute_norm(self) -> float:
        """
        Compute L2 norm of the percept for bounded-tension checks.
        
        Per spec §13: |s|_sens ≤ S_max
        """
        components = [
            self.quality ** 2,
            self.tension ** 2,
            self.curvature ** 2,
            (1 - self.shell_stability) ** 2,
            (1 - self.health) ** 2,
            self.memory_pressure ** 2,
            self.novelty ** 2,
            self.salience ** 2,
            self.relevance ** 2,
            self.context_alignment ** 2,
            self.authority ** 2,
        ]
        return np.sqrt(sum(components))


@dataclass
class ForceTerm:
    """
    A bounded forcing term for GMI internal fields.
    
    Per spec §12: The ingress operator maps sensory objects
    into a bounded forcing term acting on GMI internal fields.
    
    This is NOT language/propositions - it is a mathematical
    forcing term for the phase field dynamics.
    """
    # Magnitude (bounded)
    magnitude: float = 0.0
    
    # Direction in field space
    direction: np.ndarray = field(default_factory=lambda: np.zeros(3))
    
    # Spatial distribution (if applicable)
    spatial_profile: Optional[np.ndarray] = None
    
    # Temporal envelope
    temporal_envelope: float = 1.0
    
    # Source percept reference
    source_percept_id: str = ""
    
    # Bounding parameters
    max_magnitude: float = 1.0
    
    def __post_init__(self):
        """Ensure bounded magnitude."""
        self.magnitude = min(abs(self.magnitude), self.max_magnitude)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "magnitude": float(self.magnitude),
            "direction": self.direction.tolist() if hasattr(self.direction, 'tolist') else list(self.direction),
            "spatial_profile": self.spatial_profile.tolist() if self.spatial_profile is not None and hasattr(self.spatial_profile, 'tolist') else None,
            "temporal_envelope": float(self.temporal_envelope),
            "source_percept_id": self.source_percept_id,
            "max_magnitude": float(self.max_magnitude),
        }
    
    def compute_l2_norm(self) -> float:
        """
        Compute L2 norm of the force term.
        
        Per spec §13: |Ξ(s)|_L² ≤ K_Ξ |s|_sens
        """
        mag_sq = self.magnitude ** 2
        dir_sq = np.sum(self.direction ** 2) if len(self.direction) > 0 else 0.0
        spatial_sq = np.sum(self.spatial_profile ** 2) if self.spatial_profile is not None else 0.0
        return np.sqrt(mag_sq + dir_sq + spatial_sq)


# === Observation Operator (O: U_world → X_sens) ===

class ObservationOperator:
    """
    Observation operator: U_world → X_sens
    
    Per spec §4.1: This is the world-facing observation map.
    It takes world events and projects them into sensory state.
    
    This is GM-OS infrastructure - the "eyes and ears" that
    observe the universe boundary.
    
    Pipeline (per spec §5):
    U_world → O → y_raw → Π_proj → x_ext ⊕ x_int → A_anchor → x_anchor → F_fuse → x_sens
    """
    
    def __init__(
        self,
        projection_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
        anchor_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        """
        Initialize the observation operator.
        
        Args:
            projection_fn: Custom projection function (world → sensory)
            anchor_fn: Custom anchoring function (takes external, internal dicts)
        """
        self.projection_fn = projection_fn or self._default_projection
        self._custom_anchor_fn = anchor_fn
    
    def __call__(self, world_event: Any) -> SensoryPercept:
        """
        Apply observation operator to a world event.
        
        Args:
            world_event: Raw event from U_world
            
        Returns:
            SensoryPercept in X_sens
        """
        # Step 1: Project to raw sensory
        raw = self._project_to_raw(world_event)
        
        # Step 2: Project to external/internal charts
        external_state, internal_state = self._project_to_charts(raw)
        
        # Step 3: Apply anchoring
        anchored = self._apply_anchor(external_state, internal_state)
        
        # Step 4: Create final percept
        percept = self._create_percept(anchored, raw)
        
        return percept
    
    def _project_to_raw(self, world_event: Any) -> Dict[str, Any]:
        """
        Project world event to raw sensory representation.
        """
        if self.projection_fn:
            return self.projection_fn(world_event)
        return self._default_projection(world_event)
    
    def _default_projection(self, world_event: Any) -> Dict[str, Any]:
        """
        Default projection from world to sensory.
        
        Extracts basic features from world event.
        """
        if isinstance(world_event, dict):
            return {
                "raw": world_event.get("data", world_event),
                "topology": world_event.get("topology", {}),
                "quality": world_event.get("quality", 1.0),
                "source": world_event.get("source", "external"),
            }
        else:
            return {
                "raw": str(world_event),
                "topology": {},
                "quality": 1.0,
                "source": "external",
            }
    
    def _project_to_charts(
        self,
        raw: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Project raw sensory to external and internal charts.
        
        Returns:
            (external_state, internal_state)
        """
        # External chart
        external = {
            "raw_observation": raw.get("raw"),
            "topology": raw.get("topology", {}),
            "quality": raw.get("quality", 1.0),
            "source": raw.get("source", "external"),
        }
        
        # Internal chart (for now, defaults - would come from GMI state in full system)
        internal = {
            "budget": 1.0,
            "tension": 0.0,
            "curvature": 0.0,
            "shell_stability": 1.0,
            "health": 1.0,
            "memory_pressure": 0.0,
        }
        
        return external, internal
    
    def _apply_anchor(
        self,
        external: Dict[str, Any],
        internal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply anchoring to add provenance and authority.
        """
        if self._custom_anchor_fn:
            return self._custom_anchor_fn(external, internal)
        
        # Default anchoring
        source = external.get("source", "external")
        
        # Authority based on source
        authority_map = {
            "external": 1.0,
            "ledger": 0.8,
            "internal": 0.5,
            "replay": 0.3,
            "simulation": 0.1,
        }
        
        authority = authority_map.get(source, 0.5)
        
        return {
            **external,
            **internal,
            "provenance": source,
            "authority": authority,
            "conflict_markers": [],
        }
    
    def _create_percept(
        self,
        anchored: Dict[str, Any],
        raw: Dict[str, Any]
    ) -> SensoryPercept:
        """Create SensoryPercept from anchored state."""
        # Generate ID
        content_str = json.dumps(anchored, sort_keys=True)
        percept_id = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        
        return SensoryPercept(
            percept_id=percept_id,
            raw_observation=anchored.get("raw_observation"),
            topology=anchored.get("topology"),
            quality=anchored.get("quality", 1.0),
            source=anchored.get("source", "external"),
            budget=anchored.get("budget", 1.0),
            tension=anchored.get("tension", 0.0),
            curvature=anchored.get("curvature", 0.0),
            shell_stability=anchored.get("shell_stability", 1.0),
            health=anchored.get("health", 1.0),
            memory_pressure=anchored.get("memory_pressure", 0.0),
            provenance=anchored.get("provenance", ""),
            authority=anchored.get("authority", 0.5),
            conflict_markers=anchored.get("conflict_markers", []),
        )


# === Ingress Operator (Ξ: X_sens → U_force) ===

class IngressOperator:
    """
    Ingress operator: X_sens → U_force
    
    Per spec §4.2: This is the "optic nerve" - it maps
    sensory objects into a bounded forcing term acting on
    GMI internal fields.
    
    This is the organism-facing role of the dual-use substrate.
    
    Per spec §12:
    ∂_t θ = κΔθ + u_endo + Ξ(s_t) + λ_C C
    
    The sensory forcing refines the u_glyph side with an
    exogenous component from the world.
    """
    
    def __init__(
        self,
        max_magnitude: float = 1.0,
        bounding_constant: float = 1.0,
        field_dimensions: int = 3,
    ):
        """
        Initialize the ingress operator.
        
        Args:
            max_magnitude: Maximum force magnitude
            bounding_constant: K_Ξ constant for |Ξ(s)|_L² ≤ K_΋ |s|_sens
            field_dimensions: Dimensionality of field space
        """
        self.max_magnitude = max_magnitude
        self.bounding_constant = bounding_constant
        self.field_dimensions = field_dimensions
    
    def __call__(self, percept: SensoryPercept) -> ForceTerm:
        """
        Apply ingress operator to convert sensory percept to forcing term.
        
        Args:
            percept: SensoryPercept in X_sens
            
        Returns:
            ForceTerm for GMI internal fields
        """
        # Compute magnitude from salience and authority
        magnitude = self._compute_magnitude(percept)
        
        # Compute direction in field space
        direction = self._compute_direction(percept)
        
        # Create force term
        force = ForceTerm(
            magnitude=magnitude,
            direction=direction,
            source_percept_id=percept.percept_id,
            max_magnitude=self.max_magnitude,
        )
        
        return force
    
    def _compute_magnitude(self, percept: SensoryPercept) -> float:
        """
        Compute force magnitude from percept.
        
        Per spec §12: The forcing is bounded by the percept properties.
        """
        # Base magnitude from salience
        base = percept.salience
        
        # Authority scaling (higher authority = stronger forcing)
        authority_scale = 0.5 + 0.5 * percept.authority
        
        # Quality adjustment
        quality_factor = percept.quality
        
        # Combine
        magnitude = base * authority_scale * quality_factor
        
        # Bound
        return min(magnitude, self.max_magnitude)
    
    def _compute_direction(self, percept: SensoryPercept) -> np.ndarray:
        """
        Compute direction in field space from percept.
        
        The direction encodes the "type" of forcing:
        - novelty → exploration direction
        - relevance → exploitation direction
        - tension → threat direction
        """
        # Feature vector
        features = np.array([
            percept.novelty,
            percept.relevance,
            percept.tension,
        ])
        
        # Normalize to unit vector (with fallback)
        norm = np.linalg.norm(features)
        if norm > 1e-6:
            direction = features / norm
        else:
            direction = np.zeros(self.field_dimensions)
            if self.field_dimensions > 0:
                direction[0] = 1.0
        
        return direction
    
    def verify_boundedness(
        self,
        percept: SensoryPercept
    ) -> Tuple[bool, float, float]:
        """
        Verify bounded-tension lemma for this percept.
        
        Per spec §13:
        If |s|_sens ≤ S_max and |Ξ(s)|_L² ≤ K_΋ |s|_sens
        
        Then |ΔV| ≤ C(...) < ∞
        
        Returns:
            (is_bounded, percept_norm, force_norm)
        """
        percept_norm = percept.compute_norm()
        force = self(percept)
        force_norm = force.compute_l2_norm()
        
        # Check boundedness condition
        bound = self.bounding_constant * percept_norm
        is_bounded = force_norm <= bound
        
        return is_bounded, percept_norm, force_norm


# === Semantic Bridge (T_sens→Noe) ===

@dataclass
class NoeticType:
    """
    A Noetican semantic type.
    
    This is the output of the semantic bridge - a typed
    percept ready for semantic commitment in Noetica.
    """
    type_tag: str  # e.g., "entity", "relation", "action"
    content: Dict[str, Any]
    confidence: float
    source_percept_id: str
    timestamp: float = field(default_factory=time.time)


class SemanticBridge:
    """
    Semantic bridge: X_sens → S_Noe
    
    Per spec §14: The sensory substrate does NOT directly
    generate language. It generates a typed percept object,
    which is passed to the Noetican semantic manifold.
    
    This is the bridge between raw perception and meaning.
    """
    
    def __init__(
        self,
        type_mapping: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the semantic bridge.
        
        Args:
            type_mapping: Custom mapping from percept features to Noetic types
        """
        if type_mapping is not None:
            self.type_mapping = type_mapping
        else:
            self.type_mapping = {
                "external": "observation",
                "internal": "interoception",
                "replay": "recollection",
                "simulation": "imagination",
            }
    
    def __call__(self, percept: SensoryPercept) -> NoeticType:
        """
        Bridge sensory percept to Noetican type.
        
        Args:
            percept: SensoryPercept from the substrate
            
        Returns:
            NoeticType for semantic commitment
        """
        # Determine type
        type_tag = self._determine_type(percept)
        
        # Extract content
        content = self._extract_content(percept)
        
        # Compute confidence
        confidence = self._compute_confidence(percept)
        
        return NoeticType(
            type_tag=type_tag,
            content=content,
            confidence=confidence,
            source_percept_id=percept.percept_id,
        )
    
    def _default_mapping(self) -> Dict[str, str]:
        """Default mapping from source to type."""
        return {
            "external": "observation",
            "internal": "interoception",
            "memory": "recollection",
            "simulation": "imagination",
        }
    
    def _determine_type(self, percept: SensoryPercept) -> str:
        """Determine the Noetic type from percept."""
        source = percept.source
        
        if self.type_mapping and source in self.type_mapping:
            return self.type_mapping[source]
        
        # Default mapping
        default_map = {
            "external": "observation",
            "internal": "interoception", 
            "replay": "recollection",
            "simulation": "imagination",
        }
        
        return default_map.get(source, "unknown")
    
    def _extract_content(self, percept: SensoryPercept) -> Dict[str, Any]:
        """Extract semantic content from percept."""
        return {
            "raw": str(percept.raw_observation) if percept.raw_observation else None,
            "topology": percept.topology,
            "quality": percept.quality,
            "novelty": percept.novelty,
            "relevance": percept.relevance,
            "authority": percept.authority,
            "provenance": percept.provenance,
        }
    
    def _compute_confidence(self, percept: SensoryPercept) -> float:
        """
        Compute confidence in the semantic interpretation.
        
        Higher authority and quality = higher confidence
        """
        return min(1.0, percept.authority * percept.quality)


# === Dual-Use Pipeline ===

class DualUseSensoryPipeline:
    """
    Complete dual-use sensory pipeline.
    
    Combines:
    1. ObservationOperator (O): U_world → X_sens
    2. IngressOperator (Ξ): X_sens → U_force
    3. SemanticBridge (T): X_sens → S_Noe
    
    Per spec §5:
    U_world → O → y_raw → Π_proj → x_ext ⊕ x_int → A_anchor → x_anchor → F_fuse → x_sens → S_sal → ẍ_sens → Ξ → u_force → T_sens→Noe → s_Noe
    """
    
    def __init__(
        self,
        observation_operator: Optional[ObservationOperator] = None,
        ingress_operator: Optional[IngressOperator] = None,
        semantic_bridge: Optional[SemanticBridge] = None,
    ):
        self.observation = observation_operator or ObservationOperator()
        self.ingress = ingress_operator or IngressOperator()
        self.semantic_bridge = semantic_bridge or SemanticBridge()
    
    def process_world_event(self, world_event: Any) -> Tuple[SensoryPercept, ForceTerm, NoeticType]:
        """
        Process a world event through the full dual-use pipeline.
        
        Args:
            world_event: Raw event from the world
            
        Returns:
            (sensory_percept, force_term, noetic_type)
        """
        # Step 1: Observe (world → sensory)
        percept = self.observation(world_event)
        
        # Step 2: Ingress (sensory → forcing)
        force = self.ingress(percept)
        
        # Step 3: Semantic bridge (sensory → noetic)
        noetic = self.semantic_bridge(percept)
        
        return percept, force, noetic
    
    def world_to_sensory(self, world_event: Any) -> SensoryPercept:
        """Apply observation operator only."""
        return self.observation(world_event)
    
    def sensory_to_force(self, percept: SensoryPercept) -> ForceTerm:
        """Apply ingress operator only."""
        return self.ingress(percept)
    
    def sensory_to_noetic(self, percept: SensoryPercept) -> NoeticType:
        """Apply semantic bridge only."""
        return self.semantic_bridge(percept)


# === Exports ===

__all__ = [
    "SensoryPercept",
    "ForceTerm",
    "ObservationOperator",
    "IngressOperator",
    "NoeticType",
    "SemanticBridge",
    "DualUseSensoryPipeline",
]
