"""
Conflict Detection and Resolution for Sensory Substrate.

Per spec §11: If two anchored percepts conflict, the substrate must
not silently collapse them.

Conflict Resolution Rules:
- If Conf(s_i, s_j) > τ_conf:
  - Option 1: Raise uncertainty
  - Option 2: Defer semantic commitment
  - Option 3: Request new observation
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import numpy as np


class ConflictStrategy(Enum):
    """Strategies for resolving conflicts."""
    RAISE_UNCERTAINTY = "raise_uncertainty"
    DEFER_COMMITMENT = "defer_commitment"
    REQUEST_OBSERVATION = "request_observation"
    RESOLVE_WEIGHTED = "resolve_weighted"


@dataclass
class ConflictResult:
    """
    Result of conflict detection between two percepts.
    """
    has_conflict: bool
    conflict_score: float
    conflicting_fields: List[str]
    recommended_strategy: ConflictStrategy


@dataclass
class ConflictSet:
    """
    A set of percepts with conflicts between them.
    
    Per spec §11: A conflict set is retained whenever
    Conf(s_i, s_j) > τ_conf.
    """
    percept_ids: List[str]
    conflicts: List[Tuple[str, str, float]]  # (id1, id2, score)
    uncertainty_raised: bool = False
    resolution_strategy: Optional[ConflictStrategy] = None
    resolution_result: Optional[Dict[str, Any]] = None


class ConflictDetector:
    """
    Detects conflicts between anchored percepts.
    
    Per spec §11: Conflict detection ensures the substrate
    does not silently collapse conflicting observations.
    """
    
    def __init__(
        self,
        conflict_threshold: float = 0.5,
        authority_weight: float = 0.5,
    ):
        """
        Initialize conflict detector.
        
        Args:
            conflict_threshold: τ_conf - threshold for conflict detection
            authority_weight: Weight of authority in conflict calculation
        """
        self.conflict_threshold = conflict_threshold
        self.authority_weight = authority_weight
    
    def detect_conflict(
        self,
        percept1: Dict[str, Any],
        percept2: Dict[str, Any]
    ) -> ConflictResult:
        """
        Detect conflict between two percepts.
        
        Args:
            percept1: First percept dictionary
            percept2: Second percept dictionary
            
        Returns:
            ConflictResult with conflict details
        """
        # Check source tags for direct contradiction
        source1 = percept1.get("source", "")
        source2 = percept2.get("source", "")
        
        # External vs simulation is a strong conflict
        if source1 == "ext" and source2 == "sim":
            return ConflictResult(
                has_conflict=True,
                conflict_score=1.0,
                conflicting_fields=["source"],
                recommended_strategy=ConflictStrategy.RAISE_UNCERTAINTY,
            )
        
        # Compute content conflict
        content_conflict = self._compute_content_conflict(percept1, percept2)
        
        # Compute authority conflict
        authority_conflict = self._compute_authority_conflict(percept1, percept2)
        
        # Compute temporal conflict
        temporal_conflict = self._compute_temporal_conflict(percept1, percept2)
        
        # Combine conflicts
        combined_score = (
            content_conflict * (1 - self.authority_weight) +
            authority_conflict * self.authority_weight +
            temporal_conflict * 0.2
        )
        
        # Determine conflicting fields
        conflicting_fields = []
        if content_conflict > self.conflict_threshold:
            conflicting_fields.append("content")
        if authority_conflict > self.conflict_threshold:
            conflicting_fields.append("authority")
        if temporal_conflict > self.conflict_threshold:
            conflicting_fields.append("temporal")
        
        has_conflict = combined_score > self.conflict_threshold
        
        # Recommend strategy
        if has_conflict:
            strategy = self._recommend_strategy(
                combined_score,
                authority_conflict,
                source1,
                source2
            )
        else:
            strategy = ConflictStrategy.RAISE_UNCERTAINTY
        
        return ConflictResult(
            has_conflict=has_conflict,
            conflict_score=combined_score,
            conflicting_fields=conflicting_fields,
            recommended_strategy=strategy,
        )
    
    def _compute_content_conflict(
        self,
        p1: Dict[str, Any],
        p2: Dict[str, Any]
    ) -> float:
        """Compute conflict in content between percepts."""
        # Get content
        c1 = p1.get("content", {})
        c2 = p2.get("content", {})
        
        if not c1 or not c2:
            return 0.0
        
        # Find conflicting keys
        all_keys = set(c1.keys()) | set(c2.keys())
        if not all_keys:
            return 0.0
        
        conflicts = 0
        for key in all_keys:
            if key in c1 and key in c2:
                v1, v2 = c1[key], c2[key]
                if self._values_conflict(v1, v2):
                    conflicts += 1
        
        return conflicts / len(all_keys)
    
    def _values_conflict(self, v1: Any, v2: Any) -> bool:
        """Check if two values conflict."""
        # Numeric conflict
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            # Large relative difference is a conflict
            if v1 == 0 and v2 == 0:
                return False
            if v1 == 0 or v2 == 0:
                return True
            ratio = min(v1, v2) / max(v1, v2) if max(v1, v2) > 0 else 0
            return ratio < 0.5  # More than 2x difference
        
        # String/Boolean conflict
        if v1 != v2:
            return True
        
        return False
    
    def _compute_authority_conflict(
        self,
        p1: Dict[str, Any],
        p2: Dict[str, Any]
    ) -> float:
        """Compute conflict in authority between percepts."""
        a1 = p1.get("authority", 0.5)
        a2 = p2.get("authority", 0.5)
        
        # High authority difference is a conflict
        authority_diff = abs(a1 - a2)
        
        # If one is high authority and other is low, that's a conflict
        if (a1 > 0.7 and a2 < 0.3) or (a2 > 0.7 and a1 < 0.3):
            return 1.0
        
        return authority_diff
    
    def _compute_temporal_conflict(
        self,
        p1: Dict[str, Any],
        p2: Dict[str, Any]
    ) -> float:
        """Compute temporal conflict between percepts."""
        t1 = p1.get("timestamp", 0)
        t2 = p2.get("timestamp", 0)
        
        if t1 == 0 or t2 == 0:
            return 0.0
        
        # Time difference in seconds
        dt = abs(t1 - t2)
        
        # More than 1 hour apart is a potential conflict
        if dt > 3600:
            return min(1.0, dt / 86400)  # Cap at 1 day
        
        return 0.0
    
    def _recommend_strategy(
        self,
        conflict_score: float,
        authority_conflict: float,
        source1: str,
        source2: str
    ) -> ConflictStrategy:
        """Recommend a resolution strategy based on conflict details."""
        # High conflict with different authorities
        if authority_conflict > 0.5:
            return ConflictStrategy.RAISE_UNCERTAINTY
        
        # External vs simulation - always raise uncertainty
        if source1 == "ext" and source2 == "sim":
            return ConflictStrategy.RAISE_UNCERTAINTY
        
        # Medium conflict - defer commitment
        if conflict_score > 0.3:
            return ConflictStrategy.DEFER_COMMITMENT
        
        # Low conflict - resolve with weighting
        return ConflictStrategy.RESOLVE_WEIGHTED
    
    def detect_batch_conflicts(
        self,
        percepts: List[Dict[str, Any]]
    ) -> List[ConflictSet]:
        """
        Detect all conflicts in a batch of percepts.
        
        Args:
            percepts: List of percept dictionaries
            
        Returns:
            List of ConflictSet objects
        """
        if len(percepts) < 2:
            return []
        
        conflict_sets = []
        
        # Check all pairs
        for i in range(len(percepts)):
            for j in range(i + 1, len(percepts)):
                result = self.detect_conflict(percepts[i], percepts[j])
                
                if result.has_conflict:
                    id1 = percepts[i].get("percept_id", f"percept_{i}")
                    id2 = percepts[j].get("percept_id", f"percept_{j}")
                    
                    conflict_sets.append(ConflictSet(
                        percept_ids=[id1, id2],
                        conflicts=[(id1, id2, result.conflict_score)],
                    ))
        
        return conflict_sets


class ConflictResolver:
    """
    Resolves conflicts between percepts.
    
    Per spec §11: Conflict resolution can:
    - Raise uncertainty
    - Defer semantic commitment
    - Request new observation
    """
    
    def __init__(
        self,
        detector: Optional[ConflictDetector] = None,
    ):
        self.detector = detector or ConflictDetector()
    
    def resolve(
        self,
        conflict_set: ConflictSet,
        strategy: ConflictStrategy,
        percepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve a conflict set using the specified strategy.
        
        Args:
            conflict_set: The conflict to resolve
            strategy: Resolution strategy to use
            percepts: Available percepts
            
        Returns:
            Resolution result with metadata
        """
        if strategy == ConflictStrategy.RAISE_UNCERTAINTY:
            return self._resolve_raise_uncertainty(conflict_set, percepts)
        elif strategy == ConflictStrategy.DEFER_COMMITMENT:
            return self._resolve_defer_commitment(conflict_set, percepts)
        elif strategy == ConflictStrategy.REQUEST_OBSERVATION:
            return self._resolve_request_observation(conflict_set, percepts)
        else:  # RESOLVE_WEIGHTED
            return self._resolve_weighted(conflict_set, percepts)
    
    def _resolve_raise_uncertainty(
        self,
        conflict_set: ConflictSet,
        percepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Raise uncertainty when conflicts cannot be resolved."""
        # Increase uncertainty in all conflicting percepts
        uncertainty_factor = 1.5
        
        result_percepts = []
        for p in percepts:
            if p.get("percept_id") in conflict_set.percept_ids:
                new_conf = p.get("confidence", 0.5) / uncertainty_factor
                new_auth = p.get("authority", 0.5) / uncertainty_factor
                result_percepts.append({
                    **p,
                    "confidence": new_conf,
                    "authority": new_auth,
                    "conflict_flag": True,
                })
            else:
                result_percepts.append(p)
        
        return {
            "strategy": ConflictStrategy.RAISE_UNCERTAINTY.value,
            "result_percepts": result_percepts,
            "action": "uncertainty_raised",
            "conflict_ids": conflict_set.percept_ids,
        }
    
    def _resolve_defer_commitment(
        self,
        conflict_set: ConflictSet,
        percepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Defer semantic commitment on conflicting percepts."""
        result_percepts = []
        for p in percepts:
            if p.get("percept_id") in conflict_set.percept_ids:
                result_percepts.append({
                    **p,
                    "commitment_deferred": True,
                    "semantic_type": "unknown",
                })
            else:
                result_percepts.append(p)
        
        return {
            "strategy": ConflictStrategy.DEFER_COMMITMENT.value,
            "result_percepts": result_percepts,
            "action": "commitment_deferred",
            "conflict_ids": conflict_set.percept_ids,
        }
    
    def _resolve_request_observation(
        self,
        conflict_set: ConflictSet,
        percepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Request new observation to resolve conflict."""
        # Mark conflicting percepts as needing more data
        result_percepts = []
        for p in percepts:
            if p.get("percept_id") in conflict_set.percept_ids:
                result_percepts.append({
                    **p,
                    "needs_observation": True,
                    "observation_priority": "high",
                })
            else:
                result_percepts.append(p)
        
        return {
            "strategy": ConflictStrategy.REQUEST_OBSERVATION.value,
            "result_percepts": result_percepts,
            "action": "observation_requested",
            "conflict_ids": conflict_set.percept_ids,
            "reason": "conflict_requires_additional_data",
        }
    
    def _resolve_weighted(
        self,
        conflict_set: ConflictSet,
        percepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resolve conflict using weighted combination."""
        # Get weights from authorities
        weights = {}
        for p in percepts:
            pid = p.get("percept_id", "")
            if pid in conflict_set.percept_ids:
                weights[pid] = p.get("authority", 0.5)
        
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        # Create weighted average content
        content_sum = {}
        for p in percepts:
            pid = p.get("percept_id", "")
            if pid in weights:
                w = weights[pid]
                content = p.get("content", {})
                for k, v in content.items():
                    if k in content_sum:
                        content_sum[k] = content_sum[k] + w * v
                    else:
                        content_sum[k] = w * v
        
        return {
            "strategy": ConflictStrategy.RESOLVE_WEIGHTED.value,
            "merged_content": content_sum,
            "weights_used": weights,
            "action": "merged",
            "conflict_ids": conflict_set.percept_ids,
        }
    
    def resolve_auto(
        self,
        conflict_set: ConflictSet,
        percepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Automatically resolve a conflict using the recommended strategy.
        
        Args:
            conflict_set: The conflict to resolve
            percepts: Available percepts
            
        Returns:
            Resolution result
        """
        # Get conflict details
        if not conflict_set.conflicts:
            return {"action": "no_conflict"}
        
        _, _, score = conflict_set.conflicts[0]
        
        # Get percepts involved
        p1 = None
        p2 = None
        for p in percepts:
            if p.get("percept_id") == conflict_set.percept_ids[0]:
                p1 = p
            if p.get("percept_id") == conflict_set.percept_ids[1]:
                p2 = p
        
        if not p1 or not p2:
            return {"action": "percepts_not_found"}
        
        # Use detector to recommend strategy
        result = self.detector.detect_conflict(p1, p2)
        strategy = result.recommended_strategy
        
        # Resolve
        return self.resolve(conflict_set, strategy, percepts)


# === Exports ===

__all__ = [
    "ConflictStrategy",
    "ConflictResult",
    "ConflictSet",
    "ConflictDetector",
    "ConflictResolver",
]
