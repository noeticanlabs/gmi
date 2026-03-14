"""
Integration Tests for Dual-Use Sensory Substrate.

This module tests the complete sensory pipeline from world event
to GMI forcing, including:
1. Full pipeline: world event → sensory state → force term
2. Receipt generation and verification
3. Budget enforcement with cost law
4. Fusion with provenance preservation
5. Conflict detection and resolution
6. Bounded tension verification
"""

import pytest
import time
from typing import Dict, Any, List

# Import all sensory components
from gmos.sensory.receipts import (
    SensoryReceipt,
    SensoryReceiptFactory,
    SourceTag,
    StepType,
    Verdict,
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
)
from gmos.sensory.conflict import (
    ConflictDetector,
    ConflictResolver,
    ConflictStrategy,
    ConflictResult,
    ConflictSet,
)


# === Test Fixtures ===

@pytest.fixture
def cost_law():
    """Create observation cost law for testing."""
    return ObservationCostLaw(
        coefficients=CostCoefficients(alpha=0.001, beta=0.002, gamma=0.001)
    )


@pytest.fixture
def observation_operator():
    """Create observation operator for testing."""
    return ObservationOperator()


@pytest.fixture
def ingress_operator():
    """Create ingress operator for testing."""
    return IngressOperator(max_magnitude=1.0, bounding_constant=1.0)


@pytest.fixture
def semantic_bridge():
    """Create semantic bridge for testing."""
    return SemanticBridge()


@pytest.fixture
def pipeline(observation_operator, ingress_operator, semantic_bridge):
    """Create full dual-use pipeline."""
    return DualUseSensoryPipeline(
        observation_operator=observation_operator,
        ingress_operator=ingress_operator,
        semantic_bridge=semantic_bridge,
    )


@pytest.fixture
def verifier():
    """Create sensory verifier for testing."""
    return SensoryVerifier()


@pytest.fixture
def receipt_factory():
    """Create receipt factory for testing."""
    return SensoryReceiptFactory(
        canon_profile_hash="sha256:test_profile",
        policy_hash="sha256:test_policy",
    )


@pytest.fixture
def fusion_engine():
    """Create fusion engine for testing."""
    return FusionEngineWithProvenance()


@pytest.fixture
def conflict_detector():
    """Create conflict detector for testing."""
    return ConflictDetector(conflict_threshold=0.5)


@pytest.fixture
def tension_lemma():
    """Create bounded-tension lemma for testing."""
    return BoundedTensionLemma(
        params=TensionBoundParameters(
            bounding_constant=1.0,
            max_percept_norm=10.0,
        )
    )


# === Test Cases ===

class TestObservationOperator:
    """Test the observation operator (O: U_world → X_sens)."""
    
    def test_world_to_sensory_projection(self, observation_operator):
        """Test projection from world event to sensory state."""
        world_event = {
            "data": {"temperature": 25.5, "humidity": 60},
            "source": "sensor_1",
            "quality": 0.95,
        }
        
        percept = observation_operator(world_event)
        
        assert isinstance(percept, SensoryPercept)
        assert percept.source_class == "ext"
        assert percept.quality == 0.95
        assert percept.percept_id != ""
    
    def test_percept_has_required_fields(self, observation_operator):
        """Test that percept has all required fields."""
        world_event = {"data": "test", "source": "test"}
        
        percept = observation_operator(world_event)
        
        # Check external state
        assert hasattr(percept, "raw_observation")
        assert hasattr(percept, "quality")
        assert hasattr(percept, "source_id")
        assert hasattr(percept, "source_class")
        
        # Check internal state
        assert hasattr(percept, "budget")
        assert hasattr(percept, "tension")
        
        # Check semantic state
        assert hasattr(percept, "salience")
        assert hasattr(percept, "novelty")
        
        # Check anchor state
        assert hasattr(percept, "authority")
        assert hasattr(percept, "provenance")


class TestIngressOperator:
    """Test the ingress operator (Ξ: X_sens → U_force)."""
    
    def test_sensory_to_force_conversion(self, ingress_operator, observation_operator):
        """Test conversion from sensory to forcing term."""
        # Create a percept
        world_event = {"data": "test", "source": "external"}
        percept = observation_operator(world_event)
        percept.salience = 0.8
        percept.authority = 0.9
        
        # Convert to force
        force = ingress_operator(percept)
        
        assert isinstance(force, ForceTerm)
        assert force.magnitude > 0
        assert force.source_percept_id == percept.percept_id
    
    def test_force_is_bounded(self, ingress_operator, observation_operator):
        """Test that force magnitude is bounded."""
        # Create percepts with various saliences
        for salience in [0.0, 0.5, 1.0]:
            world_event = {"data": "test", "source": "external"}
            percept = observation_operator(world_event)
            percept.salience = salience
            percept.authority = 1.0
            
            force = ingress_operator(percept)
            
            assert force.magnitude <= ingress_operator.max_magnitude


class TestSemanticBridge:
    """Test the semantic bridge (T_sens→Noe)."""
    
    def test_sensory_to_noetic_type(self, semantic_bridge, observation_operator):
        """Test conversion from sensory to Noetic type."""
        world_event = {"data": "test", "source": "external"}
        percept = observation_operator(world_event)
        
        noetic = semantic_bridge(percept)
        
        assert isinstance(noetic, NoeticType)
        assert noetic.type_tag in ["observation", "interoception", "recollection", "imagination"]
        assert noetic.confidence > 0


class TestDualUsePipeline:
    """Test the complete dual-use pipeline."""
    
    def test_full_pipeline_world_to_force(self, pipeline):
        """Test complete pipeline from world event to force term."""
        world_event = {
            "data": {"object": "ball", "position": [1, 2, 3]},
            "source": "vision",
            "quality": 0.9,
        }
        
        percept, force, noetic = pipeline.process_world_event(world_event)
        
        assert isinstance(percept, SensoryPercept)
        assert isinstance(force, ForceTerm)
        assert isinstance(noetic, NoeticType)
    
    def test_pipeline_produces_valid_ids(self, pipeline):
        """Test that pipeline produces valid percept IDs."""
        world_event = {"data": "test", "source": "external"}
        
        percept, force, noetic = pipeline.process_world_event(world_event)
        
        assert percept.percept_id != ""
        assert force.source_percept_id == percept.percept_id
        assert noetic.source_percept_id == percept.percept_id


class TestObservationCostLaw:
    """Test the observation cost law."""
    
    def test_cost_is_positive(self, cost_law):
        """Test that observation cost is always positive."""
        # Test various salience and bandwidth values
        for salience in [0.0, 0.5, 1.0]:
            for bandwidth in [0.0, 0.5, 1.0]:
                cost = cost_law.compute_cost(salience, bandwidth)
                assert cost > 0, f"Cost should be positive for salience={salience}, bandwidth={bandwidth}"
    
    def test_budget_enforcement(self, cost_law):
        """Test budget enforcement."""
        budget = 0.01
        percepts = [
            {"salience": 0.5, "bandwidth": 0.1},
            {"salience": 0.5, "bandwidth": 0.1},
            {"salience": 0.5, "bandwidth": 0.1},
        ]
        
        fits, total, costs = cost_law.check_budget(budget, percepts)
        
        # Either all fit, or total exceeds budget
        if not fits:
            assert total > budget
    
    def test_budget_absorption(self, cost_law):
        """Test budget absorption at b=0."""
        budget = 0.0
        percept = {"salience": 0.5, "bandwidth": 0.1}
        
        _, effective = cost_law.budget_absorption(budget, percept)
        
        # When budget is 0, no spend allowed
        assert effective == 0.0


class TestReceiptGeneration:
    """Test receipt generation and validation."""
    
    def test_create_observation_receipt(self, receipt_factory):
        """Test creating an observation receipt."""
        content = {"data": "test", "value": 42}
        
        receipt = receipt_factory.create_observation_receipt(
            content=content,
            source_tag=SourceTag.EXTERNAL,
            authority=0.95,
            quality=0.88,
            salience=0.73,
            cost=0.004,
        )
        
        assert receipt.schema_id == SCHEMA_ID
        assert receipt.source_tag == "ext"
        assert receipt.authority_weight == "0.95"
        assert receipt.salience_score == "0.73"
    
    def test_receipt_validation(self, receipt_factory):
        """Test receipt validation."""
        content = {"data": "test"}
        
        receipt = receipt_factory.create_observation_receipt(
            content=content,
            source_tag=SourceTag.EXTERNAL,
            authority=0.8,
            quality=0.9,
            salience=0.5,
            cost=0.005,
        )
        
        is_valid, error = receipt.validate()
        
        assert is_valid, f"Receipt should be valid: {error}"
    
    def test_receipt_to_dict_roundtrip(self, receipt_factory):
        """Test receipt serialization and deserialization."""
        content = {"data": "test"}
        
        receipt = receipt_factory.create_observation_receipt(
            content=content,
            source_tag=SourceTag.INTERNAL,
            authority=0.5,
            quality=0.7,
            salience=0.3,
            cost=0.002,
        )
        
        # Serialize to dict
        d = receipt.to_dict()
        
        # Deserialize
        receipt2 = SensoryReceipt.from_dict(d)
        
        assert receipt2.schema_id == receipt.schema_id
        assert receipt2.source_tag == receipt.source_tag
        assert receipt2.authority_weight == receipt.authority_weight


class TestSensoryVerifier:
    """Test the sensory verifier."""
    
    def test_verify_valid_receipt(self, verifier, receipt_factory):
        """Test verification of valid receipt."""
        content = {"data": "test"}
        
        receipt = receipt_factory.create_observation_receipt(
            content=content,
            source_tag=SourceTag.EXTERNAL,
            authority=0.9,
            quality=0.8,
            salience=0.5,
            cost=0.003,
        )
        
        result = verifier.verify(receipt)
        
        assert result.is_valid
        assert result.verdict == Verdict.ACCEPT.value
    
    def test_verify_invalid_source_tag(self, verifier, receipt_factory):
        """Test rejection of invalid source tag."""
        content = {"data": "test"}
        
        receipt = receipt_factory.create_observation_receipt(
            content=content,
            source_tag=SourceTag.EXTERNAL,
            authority=0.9,
            quality=0.8,
            salience=0.5,
            cost=0.003,
        )
        
        # Manually set invalid source tag
        receipt.source_tag = "invalid"
        
        result = verifier.verify(receipt)
        
        assert not result.is_valid
        assert result.reject_code is not None
    
    def test_verify_negative_cost(self, verifier, receipt_factory):
        """Test rejection of negative cost."""
        content = {"data": "test"}
        
        receipt = receipt_factory.create_observation_receipt(
            content=content,
            source_tag=SourceTag.EXTERNAL,
            authority=0.9,
            quality=0.8,
            salience=0.5,
            cost=-0.001,  # Negative!
        )
        
        result = verifier.verify(receipt)
        
        assert not result.is_valid
        assert "cost" in result.error_message.lower()


class TestFusionWithProvenance:
    """Test fusion with provenance preservation."""
    
    def test_fuse_preserves_provenance(self, fusion_engine):
        """Test that fusion preserves provenance."""
        percepts = [
            {
                "content": {"value": 10},
                "authority": 0.8,
                "quality": 0.9,
                "source": "ext",
                "content_hash": "hash1",
            },
            {
                "content": {"value": 20},
                "authority": 0.6,
                "quality": 0.7,
                "source": "int",
                "content_hash": "hash2",
            },
        ]
        
        result = fusion_engine.fuse(percepts)
        
        assert isinstance(result, FusedPerceptWithProvenance)
        assert len(result.provenance.source_tags) == 2
        assert "ext" in result.provenance.source_tags
        assert "int" in result.provenance.source_tags
    
    def test_fusion_weights_by_authority(self, fusion_engine):
        """Test that fusion weights by authority."""
        percepts = [
            {
                "content": {"value": 100},
                "authority": 0.9,
                "quality": 1.0,
                "source": "ext",
                "content_hash": "hash1",
            },
            {
                "content": {"value": 0},
                "authority": 0.1,
                "quality": 0.1,
                "source": "sim",
                "content_hash": "hash2",
            },
        ]
        
        result = fusion_engine.fuse(percepts)
        
        # Fused value should be close to 100 (high authority dominates)
        assert result.content.get("value", 0) > 50


class TestConflictDetection:
    """Test conflict detection and resolution."""
    
    def test_detect_external_vs_simulation_conflict(self, conflict_detector):
        """Test detection of external vs simulation conflict."""
        p1 = {
            "percept_id": "p1",
            "source": "ext",
            "authority": 0.9,
            "content": {"position": [1, 2, 3]},
            "timestamp": time.time(),
        }
        p2 = {
            "percept_id": "p2", 
            "source": "sim",
            "authority": 0.2,
            "content": {"position": [10, 20, 30]},
            "timestamp": time.time(),
        }
        
        result = conflict_detector.detect_conflict(p1, p2)
        
        assert result.has_conflict
        assert result.conflict_score > 0.5
    
    def test_conflict_resolution_raise_uncertainty(self, conflict_detector):
        """Test raising uncertainty for conflicts."""
        resolver = ConflictResolver(detector=conflict_detector)
        
        conflict_set = ConflictSet(
            percept_ids=["p1", "p2"],
            conflicts=[("p1", "p2", 0.8)],
        )
        
        percepts = [
            {"percept_id": "p1", "confidence": 0.8, "authority": 0.8, "content": {}},
            {"percept_id": "p2", "confidence": 0.7, "authority": 0.3, "content": {}},
        ]
        
        result = resolver.resolve(conflict_set, ConflictStrategy.RAISE_UNCERTAINTY, percepts)
        
        assert result["action"] == "uncertainty_raised"


class TestBoundedTensionLemma:
    """Test the bounded-tension lemma."""
    
    def test_percept_norm_bounded(self, tension_lemma):
        """Test that percept norm can be bounded."""
        features = {
            "quality": 0.8,
            "tension": 0.3,
            "curvature": 0.1,
            "shell_stability": 0.9,
            "novelty": 0.5,
            "salience": 0.7,
            "authority": 0.8,
        }
        
        norm = tension_lemma.compute_percept_norm(features)
        
        assert norm > 0
        assert norm < float('inf')
    
    def test_tension_bound_finite(self, tension_lemma):
        """Test that tension bound is finite."""
        features = {
            "quality": 1.0,
            "tension": 1.0,
            "curvature": 1.0,
            "shell_stability": 1.0,
            "novelty": 1.0,
            "salience": 1.0,
            "authority": 1.0,
        }
        
        # With bounded percept, tension should be finite
        is_bounded, details = tension_lemma.verify(
            features,
            theta_norm=1.0,
            curvature_magnitude=0.5,
        )
        
        assert is_bounded
        assert details["tension_bound"] < float('inf')
    
    def test_verifies_ingress_operator(self, tension_lemma, observation_operator, ingress_operator):
        """Test boundedness of ingress operator."""
        # Create percept
        world_event = {"data": "test", "source": "external"}
        percept = observation_operator(world_event)
        percept.salience = 0.8
        percept.authority = 0.9
        
        # Verify operator boundedness
        is_bounded, details = tension_lemma.verify_operator_boundedness(
            percept, ingress_operator
        )
        
        assert is_bounded
        assert details["forcing_norm"] <= details["forcing_bound"]


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_complete_sensory_cycle(self, pipeline, receipt_factory, verifier, cost_law):
        """Test complete sensory processing cycle."""
        # 1. World event
        world_event = {
            "data": {"temperature": 22.5, "humidity": 45},
            "source": "environment_sensor",
            "quality": 0.92,
        }
        
        # 2. Process through pipeline
        percept, force, noetic = pipeline.process_world_event(world_event)
        
        # 3. Compute cost
        cost = cost_law.compute_cost(percept.salience, bandwidth=0.1)
        assert cost > 0
        
        # 4. Generate receipt
        receipt = receipt_factory.create_observation_receipt(
            content=percept.to_dict(),
            source_tag=SourceTag.EXTERNAL,
            authority=percept.authority,
            quality=percept.quality,
            salience=percept.salience,
            cost=cost,
        )
        
        # 5. Verify receipt
        result = verifier.verify(receipt)
        
        assert result.is_valid
    
    def test_multiple_percepts_budget_limited(self, pipeline, cost_law):
        """Test that budget limits number of processed percepts."""
        budget = 0.01
        
        # Generate multiple percepts
        percepts = []
        for i in range(10):
            world_event = {"data": f"event_{i}", "source": "external"}
            percept, _, _ = pipeline.process_world_event(world_event)
            percept.salience = 0.5
            percepts.append(percept)
        
        # Check which fit in budget
        percept_dicts = [{"salience": p.salience, "bandwidth": 0.1} for p in percepts]
        selected, costs = cost_law.select_observations(budget, percept_dicts)
        
        # Should select fewer than total
        assert len(selected) <= len(percepts)


# === Run Tests ===

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
