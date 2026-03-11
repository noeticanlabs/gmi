"""
Test suite for Epistemic Shell v1-v4 integration.

Tests the 6 new tension terms:
- V_collapse (v1): Fiber/hypothesis collapse penalty
- V_overreach (v2): Horizon overreach penalty
- V_curiosity_deficit (v3): Ignoring high-EVI observations
- V_curiosity_mania (v3): Excessive exploration
- V_shock (v4): Surprise exceeding capacity
- V_gullible (v4): Trust without verification
"""

import numpy as np
import unittest
from gmos.agents.gmi.tension_law import (
    GMITensionLaw,
    GMITensionState,
    TensionWeights,
)


class TestV1CollapsePotential(unittest.TestCase):
    """Test v1: Fiber collapse penalty."""
    
    def test_no_penalty_when_fiber_inactive(self):
        """No collapse penalty when fiber tracking is inactive."""
        law = GMITensionLaw()
        state = GMITensionState()
        state.fiber_active = False
        state.fiber_hypotheses = ['h1', 'h2']
        state.fiber_beliefs = np.array([0.9, 0.1])
        
        v = law._compute_collapse_potential(
            state.fiber_active,
            state.fiber_hypotheses,
            state.fiber_beliefs,
        )
        
        self.assertEqual(v, 0.0)
    
    def test_no_penalty_single_hypothesis(self):
        """No collapse penalty with single hypothesis (nothing to collapse to)."""
        law = GMITensionLaw()
        state = GMITensionState()
        state.fiber_active = True
        state.fiber_hypotheses = ['h1']  # Single hypothesis
        state.fiber_beliefs = np.array([1.0])
        
        v = law._compute_collapse_potential(
            state.fiber_active,
            state.fiber_hypotheses,
            state.fiber_beliefs,
        )
        
        self.assertEqual(v, 0.0)
    
    def test_high_penalty_for_collapsed_beliefs(self):
        """High penalty when beliefs are collapsed to one hypothesis."""
        law = GMITensionLaw()
        state = GMITensionState()
        state.fiber_active = True
        state.fiber_hypotheses = ['h1', 'h2', 'h3']
        state.fiber_beliefs = np.array([0.95, 0.03, 0.02])  # Strongly peaked
        
        v = law._compute_collapse_potential(
            state.fiber_active,
            state.fiber_hypotheses,
            state.fiber_beliefs,
        )
        
        # Should be high penalty (close to 1.0)
        self.assertGreater(v, 0.7)
    
    def test_low_penalty_for_uniform_beliefs(self):
        """Low penalty for uniform beliefs (no premature collapse)."""
        law = GMITensionLaw()
        state = GMITensionState()
        state.fiber_active = True
        state.fiber_hypotheses = ['h1', 'h2', 'h3']
        state.fiber_beliefs = np.array([0.33, 0.33, 0.34])  # Nearly uniform
        
        v = law._compute_collapse_potential(
            state.fiber_active,
            state.fiber_hypotheses,
            state.fiber_beliefs,
        )
        
        # Should be low penalty (close to 0.0)
        self.assertLess(v, 0.3)


class TestV2OverreachPotential(unittest.TestCase):
    """Test v2: Horizon overreach penalty."""
    
    def test_no_penalty_without_beliefs(self):
        """No overreach penalty without belief distribution."""
        law = GMITensionLaw()
        state = GMITensionState()
        state.fiber_beliefs = np.array([])
        state.horizon_evidence = np.array([0.1, 0.2])
        state.horizon_confidence = 0.8
        
        v = law._compute_overreach_potential(
            state.fiber_beliefs,
            state.horizon_evidence,
            state.horizon_confidence,
        )
        
        self.assertEqual(v, 0.0)
    
    def test_no_penalty_without_evidence(self):
        """No overreach penalty without horizon evidence."""
        law = GMITensionLaw()
        state = GMITensionState()
        state.fiber_beliefs = np.array([0.5, 0.5])
        state.horizon_evidence = np.array([])
        state.horizon_confidence = 0.8
        
        v = law._compute_overreach_potential(
            state.fiber_beliefs,
            state.horizon_evidence,
            state.horizon_confidence,
        )
        
        self.assertEqual(v, 0.0)
    
    def test_penalty_for_beliefs_beyond_horizon(self):
        """Penalty when beliefs extend beyond evidence horizon."""
        law = GMITensionLaw()
        state = GMITensionState()
        # Beliefs peaked far from origin
        state.fiber_beliefs = np.array([0.1, 0.1, 0.8])  
        # Evidence near origin
        state.horizon_evidence = np.array([0.05, 0.1, 0.15])
        state.horizon_confidence = 0.9
        
        v = law._compute_overreach_potential(
            state.fiber_beliefs,
            state.horizon_evidence,
            state.horizon_confidence,
        )
        
        self.assertGreater(v, 0.0)
    
    def test_low_confidence_increases_penalty(self):
        """Lower horizon confidence increases overreach penalty."""
        law = GMITensionLaw()
        
        # High confidence
        v_high = law._compute_overreach_potential(
            fiber_beliefs=np.array([0.2, 0.8]),
            horizon_evidence=np.array([0.1, 0.2]),
            horizon_confidence=0.9,
        )
        
        # Low confidence
        v_low = law._compute_overreach_potential(
            fiber_beliefs=np.array([0.2, 0.8]),
            horizon_evidence=np.array([0.1, 0.2]),
            horizon_confidence=0.3,
        )
        
        self.assertGreater(v_low, v_high)


class TestV3CuriosityPotential(unittest.TestCase):
    """Test v3: Curiosity deficit/mania penalty."""
    
    def test_no_penalty_without_observations(self):
        """No curiosity penalty without EVI observations."""
        law = GMITensionLaw()
        
        v = law._compute_curiosity_potential(
            evi_observations=[],
            curiosity_expenditure=5.0,
        )
        
        self.assertEqual(v, 0.0)
    
    def test_deficit_penalty_for_ignored_high_evi(self):
        """Penalty for ignoring high-EVI observations."""
        law = GMITensionLaw()
        
        # Low EVI observation available (high-EVI items would be worth exploring)
        obs1 = (np.array([1.0]), 0.3)  # Below threshold
        obs2 = (np.array([2.0]), 0.2)  # Below threshold
        
        v = law._compute_curiosity_potential(
            evi_observations=[obs1, obs2],
            curiosity_expenditure=0.0,  # Not explored
        )
        
        # Should have deficit penalty (max EVI below threshold = not investigating)
        self.assertGreater(v, 0.0)
    
    def test_mania_penalty_for_excessive_spending(self):
        """Penalty for excessive curiosity expenditure."""
        law = GMITensionLaw()
        
        # Good EVI but high expenditure
        obs = (np.array([1.0]), 0.6)
        
        v = law._compute_curiosity_potential(
            evi_observations=[obs],
            curiosity_expenditure=50.0,  # Very high
        )
        
        # Should have mania penalty
        self.assertGreater(v, 0.0)
    
    def test_balanced_curiosity_low_penalty(self):
        """Low penalty when curiosity is balanced."""
        law = GMITensionLaw()
        
        # Good EVI, moderate expenditure
        obs = (np.array([1.0]), 0.7)
        
        v = law._compute_curiosity_potential(
            evi_observations=[obs],
            curiosity_expenditure=2.0,
        )
        
        # Should be low
        self.assertLess(v, 0.5)


class TestV4TrustPotential(unittest.TestCase):
    """Test v4: Shock and gullibility penalty."""
    
    def test_shock_penalty_for_surprise_exceeding_capacity(self):
        """Penalty when surprise exceeds adaptive capacity."""
        law = GMITensionLaw()
        
        v = law._compute_trust_potential(
            authority_source="test",
            authority_trust=0.5,
            authority_provenance=0.5,
            evidence_quality=0.5,
            surprise_history=[0.9],  # High surprise
            adaptive_capacity=0.5,   # Low capacity
        )
        
        # Should have shock penalty
        self.assertGreater(v, 0.0)
    
    def test_no_shock_penalty_within_capacity(self):
        """No shock penalty when surprise within capacity."""
        law = GMITensionLaw()
        
        # Test that empty surprise history has minimal penalty
        # (shock component is 0, there may be small gullibility component)
        v = law._compute_trust_potential(
            authority_source="test",
            authority_trust=0.0,  # No trust at all = no gullibility
            authority_provenance=1.0,
            evidence_quality=1.0,
            surprise_history=[],  # No surprise
            adaptive_capacity=0.5,
        )
        
        # Should be essentially zero (no shock, no gullibility)
        self.assertLess(v, 0.01)
    
    def test_gullibility_penalty_for_trust_without_evidence(self):
        """Penalty when trusting authority without evidence support."""
        law = GMITensionLaw()
        
        # High trust but low provenance and evidence quality
        v = law._compute_trust_potential(
            authority_source="unknown",
            authority_trust=0.9,           # High trust
            authority_provenance=0.2,      # Low authority
            evidence_quality=0.1,         # Poor evidence
            surprise_history=[0.2],
            adaptive_capacity=0.5,
        )
        
        # Should have gullibility penalty
        self.assertGreater(v, 0.0)
    
    def test_no_gullibility_with_well_calibrated_trust(self):
        """No gullibility when trust matches evidence."""
        law = GMITensionLaw()
        
        # W_eff = 0.9 * 0.5 * 0.9 = 0.405
        # Trust = 0.5, so trust > W_eff, but close enough (less than 0.1 difference)
        # This should give very low penalty
        v = law._compute_trust_potential(
            authority_source="trusted",
            authority_trust=0.5,
            authority_provenance=0.9,
            evidence_quality=0.9,
            surprise_history=[0.2],
            adaptive_capacity=0.5,
        )
        
        # Should have minimal gullibility (close to zero)
        self.assertLess(v, 0.2)


class TestEpistemicIntegration(unittest.TestCase):
    """Test integration of all epistemic terms."""
    
    def test_full_state_with_epistemic_terms(self):
        """Test complete GMITensionState with all epistemic fields."""
        law = GMITensionLaw()
        state = GMITensionState()
        
        # Set up complete epistemic state
        state.fiber_active = True
        state.fiber_hypotheses = ['h1', 'h2', 'h3']
        state.fiber_beliefs = np.array([0.7, 0.2, 0.1])
        
        state.horizon_evidence = np.array([0.1, 0.2, 0.3])
        state.horizon_confidence = 0.7
        
        state.evi_observations = [
            (np.array([1.0]), 0.6),
            (np.array([2.0]), 0.4),
        ]
        state.curiosity_expenditure = 3.0
        
        state.authority_source = 'expert'
        state.authority_trust = 0.6
        state.authority_provenance = 0.7
        state.evidence_quality = 0.5
        state.surprise_history = [0.4]
        state.adaptive_capacity = 0.5
        
        # Compute total V
        total_v = law.compute(state)
        
        # Should have non-zero epistemic contribution
        self.assertGreater(total_v, 0.0)
    
    def test_custom_weights_affect_epistemic_terms(self):
        """Test that custom weights change epistemic behavior."""
        # Low weights = less epistemic penalty
        low_weights = TensionWeights(
            w_collapse=0.1,
            w_overreach=0.1,
            w_curiosity_def=0.1,
            w_curiosity_man=0.1,
            w_shock=0.1,
            w_gullible=0.1,
        )
        law_low = GMITensionLaw(weights=low_weights)
        
        # High weights = more epistemic penalty
        high_weights = TensionWeights(
            w_collapse=1.0,
            w_overreach=1.0,
            w_curiosity_def=1.0,
            w_curiosity_man=1.0,
            w_shock=1.0,
            w_gullible=1.0,
        )
        law_high = GMITensionLaw(weights=high_weights)
        
        # Same state
        state = GMITensionState()
        state.fiber_active = True
        state.fiber_hypotheses = ['h1', 'h2']
        state.fiber_beliefs = np.array([0.9, 0.1])
        state.horizon_evidence = np.array([0.1])
        state.horizon_confidence = 0.5
        state.evi_observations = [(np.array([1.0]), 0.9)]
        state.curiosity_expenditure = 5.0
        state.authority_source = 'test'
        state.authority_trust = 0.8
        state.authority_provenance = 0.3
        state.evidence_quality = 0.2
        state.surprise_history = [0.8]
        state.adaptive_capacity = 0.3
        
        v_low = law_low.compute(state)
        v_high = law_high.compute(state)
        
        # High weights should give higher V
        self.assertGreater(v_high, v_low)


class TestEpistemicWeights(unittest.TestCase):
    """Test new TensionWeights fields."""
    
    def test_default_weights(self):
        """Test default epistemic weights."""
        weights = TensionWeights()
        
        self.assertEqual(weights.w_collapse, 0.5)
        self.assertEqual(weights.w_overreach, 0.5)
        self.assertEqual(weights.w_curiosity_def, 0.3)
        self.assertEqual(weights.w_curiosity_man, 0.3)
        self.assertEqual(weights.w_shock, 0.4)
        self.assertEqual(weights.w_gullible, 0.4)
    
    def test_custom_weights(self):
        """Test custom epistemic weights."""
        weights = TensionWeights(
            w_collapse=1.0,
            w_overreach=0.8,
            w_curiosity_def=0.5,
            w_curiosity_man=0.5,
            w_shock=0.9,
            w_gullible=0.9,
        )
        
        self.assertEqual(weights.w_collapse, 1.0)
        self.assertEqual(weights.w_overreach, 0.8)
        self.assertEqual(weights.w_curiosity_def, 0.5)


if __name__ == '__main__':
    unittest.main()
