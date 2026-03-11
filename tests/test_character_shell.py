"""
Test suite for Character Shell v1.

Tests the character shell χ as a threshold modulation field:
- Character state creation and profiles
- Threshold modulation map M_χ
- Character dynamics (drift under experience)
- Character non-override constraint
"""

import numpy as np
import unittest
from gmos.agents.gmi.character_shell import (
    CharacterState,
    EpistemicThresholds,
    ModulatedThresholds,
    compute_modulated_thresholds,
    update_character,
    is_action_allowed,
    interpolate_character,
    character_summary,
)


class TestCharacterStateCreation(unittest.TestCase):
    """Test character state creation and profiles."""
    
    def test_default_character(self):
        """Test default character values."""
        chi = CharacterState()
        
        self.assertEqual(chi.chi_courage, 0.5)
        self.assertEqual(chi.chi_discipline, 0.5)
        self.assertEqual(chi.chi_patience, 0.5)
        self.assertEqual(chi.chi_curiosity, 0.5)
        self.assertEqual(chi.chi_restraint, 0.5)
        self.assertEqual(chi.chi_persistence, 0.5)
        self.assertEqual(chi.chi_laziness, 0.3)  # Default is lower
        self.assertEqual(chi.chi_humility, 0.5)
    
    def test_clamping(self):
        """Test that character values are clamped to [0, 1]."""
        chi = CharacterState(
            chi_courage=1.5,
            chi_discipline=-0.5,
        )
        
        self.assertEqual(chi.chi_courage, 1.0)
        self.assertEqual(chi.chi_discipline, 0.0)
    
    def test_scientist_profile(self):
        """Test scientist profile creation."""
        chi = CharacterState.create_scientist()
        
        # Scientist: careful, thorough, humble
        self.assertLess(chi.chi_courage, 0.5)
        self.assertGreater(chi.chi_discipline, 0.5)
        self.assertGreater(chi.chi_humility, 0.5)
        self.assertGreater(chi.chi_patience, 0.5)
    
    def test_warrior_profile(self):
        """Test warrior profile creation."""
        chi = CharacterState.create_warrior()
        
        # Warrior: bold, fast, decisive
        self.assertGreater(chi.chi_courage, 0.5)
        self.assertLess(chi.chi_patience, 0.5)
        self.assertLess(chi.chi_humility, 0.5)
    
    def test_explorer_profile(self):
        """Test explorer profile creation."""
        chi = CharacterState.create_explorer()
        
        # Explorer: curious, bold
        self.assertGreater(chi.chi_curiosity, 0.7)
        self.assertGreater(chi.chi_courage, 0.5)
    
    def test_diplomat_profile(self):
        """Test diplomat profile creation."""
        chi = CharacterState.create_diplomat()
        
        # Diplomat: balanced, cautious, verification-focused
        self.assertGreater(chi.chi_restraint, 0.5)
        self.assertGreater(chi.chi_humility, 0.5)


class TestThresholdModulation(unittest.TestCase):
    """Test threshold modulation map M_χ."""
    
    def test_modulation_map_exists(self):
        """Test that modulation map produces ModulatedThresholds."""
        chi = CharacterState()
        base = EpistemicThresholds()
        
        modulated = compute_modulated_thresholds(base, chi)
        
        self.assertIsInstance(modulated, ModulatedThresholds)
    
    def test_humility_increases_collapse_weight(self):
        """Higher humility should increase collapse penalty weight."""
        base = EpistemicThresholds(lambda_collapse=0.5)
        
        # Low humility
        chi_low = CharacterState(chi_humility=0.0)
        mod_low = compute_modulated_thresholds(base, chi_low)
        
        # High humility
        chi_high = CharacterState(chi_humility=1.0)
        mod_high = compute_modulated_thresholds(base, chi_high)
        
        # Higher humility = higher collapse weight
        self.assertGreater(mod_high.lambda_collapse, mod_low.lambda_collapse)
    
    def test_courage_increases_fragility_tolerance(self):
        """Higher courage should increase fragility tolerance."""
        base = EpistemicThresholds(tau_frag=0.5)
        
        # Low courage
        chi_low = CharacterState(chi_courage=0.0, chi_restraint=0.5)
        mod_low = compute_modulated_thresholds(base, chi_low)
        
        # High courage
        chi_high = CharacterState(chi_courage=1.0, chi_restraint=0.5)
        mod_high = compute_modulated_thresholds(base, chi_high)
        
        # Higher courage = higher fragility threshold
        self.assertGreater(mod_high.tau_frag, mod_low.tau_frag)
    
    def test_laziness_increases_refresh_threshold(self):
        """Higher laziness should increase representative refresh threshold."""
        base = EpistemicThresholds(tau_refresh=0.5)
        
        # Low laziness
        chi_low = CharacterState(chi_laziness=0.0, chi_discipline=0.5)
        mod_low = compute_modulated_thresholds(base, chi_low)
        
        # High laziness
        chi_high = CharacterState(chi_laziness=1.0, chi_discipline=0.5)
        mod_high = compute_modulated_thresholds(base, chi_high)
        
        # Higher laziness = higher refresh threshold (stick with current rep longer)
        self.assertGreater(mod_high.tau_refresh, mod_low.tau_refresh)
    
    def test_curiosity_decreases_epi_threshold(self):
        """Higher curiosity should decrease EVI threshold (ask more)."""
        base = EpistemicThresholds(tau_epistemic=0.5)
        
        # Low curiosity
        chi_low = CharacterState(chi_curiosity=0.0, chi_laziness=0.5)
        mod_low = compute_modulated_thresholds(base, chi_low)
        
        # High curiosity
        chi_high = CharacterState(chi_curiosity=1.0, chi_laziness=0.5)
        mod_high = compute_modulated_thresholds(base, chi_high)
        
        # Higher curiosity = lower EVI threshold = more queries
        self.assertLess(mod_high.tau_epistemic, mod_low.tau_epistemic)
    
    def test_restraint_increases_corr_threshold(self):
        """Higher restraint should increase corroboration threshold."""
        base = EpistemicThresholds(tau_corr=0.5)
        
        # Low restraint
        chi_low = CharacterState(chi_restraint=0.0, chi_humility=0.5, chi_courage=0.5)
        mod_low = compute_modulated_thresholds(base, chi_low)
        
        # High restraint
        chi_high = CharacterState(chi_restraint=1.0, chi_humility=0.5, chi_courage=0.5)
        mod_high = compute_modulated_thresholds(base, chi_high)
        
        # Higher restraint = higher corroboration threshold = need more evidence
        self.assertGreater(mod_high.tau_corr, mod_low.tau_corr)
    
    def test_courage_patience_soften_shock(self):
        """Higher courage/patience should decrease shock weight."""
        base = EpistemicThresholds(lambda_shock=0.5)
        
        # Low courage and patience
        chi_low = CharacterState(chi_courage=0.0, chi_patience=0.0, chi_laziness=0.5)
        mod_low = compute_modulated_thresholds(base, chi_low)
        
        # High courage and patience
        chi_high = CharacterState(chi_courage=1.0, chi_patience=1.0, chi_laziness=0.5)
        mod_high = compute_modulated_thresholds(base, chi_high)
        
        # Higher courage/patience = lower shock weight = less affected by falsification
        self.assertLess(mod_high.lambda_shock, mod_low.lambda_shock)


class TestCharacterDynamics(unittest.TestCase):
    """Test character drift under experience."""
    
    def test_courage_increases_on_success(self):
        """Successful action under pressure should increase courage."""
        chi = CharacterState(chi_courage=0.5)
        
        new_chi = update_character(
            current=chi,
            action_taken=True,
            action_successful=True,
            action_value=0.5,
            pressure_input=0.5,
            shock_received=False,
        )
        
        self.assertGreater(new_chi.chi_courage, chi.chi_courage)
    
    def test_courage_decreases_on_failure(self):
        """Failed action should decrease courage."""
        chi = CharacterState(chi_courage=0.5)
        
        new_chi = update_character(
            current=chi,
            action_taken=True,
            action_successful=False,
            action_value=0.5,
            pressure_input=0.3,
            shock_received=False,
        )
        
        self.assertLess(new_chi.chi_courage, chi.chi_courage)
    
    def test_humility_increases_on_shock(self):
        """Model falsification shock should increase humility."""
        chi = CharacterState(chi_humility=0.5)
        
        new_chi = update_character(
            current=chi,
            action_taken=True,
            action_successful=False,
            action_value=-0.5,
            pressure_input=0.3,
            shock_received=True,
        )
        
        self.assertGreater(new_chi.chi_humility, chi.chi_humility)
    
    def test_laziness_increases_on_refusal(self):
        """Lazy refusal should increase laziness."""
        chi = CharacterState(chi_laziness=0.3)
        
        new_chi = update_character(
            current=chi,
            action_taken=False,  # Refused action
            action_successful=False,
            action_value=0.5,    # But action had positive value
            pressure_input=0.0,
            shock_received=False,
        )
        
        self.assertGreater(new_chi.chi_laziness, chi.chi_laziness)
    
    def test_adaptation_rate_clamped(self):
        """Character should respect adaptation rate."""
        chi = CharacterState(chi_courage=0.5, adaptation_rate=0.01)
        
        # Multiple updates
        for _ in range(100):
            chi = update_character(
                current=chi,
                action_taken=True,
                action_successful=True,
                action_value=0.5,
                pressure_input=0.8,
                shock_received=False,
            )
        
        # Should not exceed bounds despite many updates
        self.assertLessEqual(chi.chi_courage, 1.0)
        self.assertGreaterEqual(chi.chi_courage, 0.0)


class TestCharacterProfiles(unittest.TestCase):
    """Test different character profiles have distinct behaviors."""
    
    def test_scientist_vs_warrior_fragility(self):
        """Scientist should have higher fragility tolerance than warrior."""
        scientist = CharacterState.create_scientist()
        warrior = CharacterState.create_warrior()
        
        base = EpistemicThresholds(tau_frag=0.5)
        
        mod_scientist = compute_modulated_thresholds(base, scientist)
        mod_warrior = compute_modulated_thresholds(base, warrior)
        
        # Warrior is more tolerant of fragility (acts faster under uncertainty)
        self.assertGreater(mod_warrior.tau_frag, mod_scientist.tau_frag)
    
    def test_scientist_vs_warrior_collapse(self):
        """Scientist should resist collapse more than warrior."""
        scientist = CharacterState.create_scientist()
        warrior = CharacterState.create_warrior()
        
        base = EpistemicThresholds(lambda_collapse=0.5)
        
        mod_scientist = compute_modulated_thresholds(base, scientist)
        mod_warrior = compute_modulated_thresholds(base, warrior)
        
        # Scientist has higher collapse resistance
        self.assertGreater(mod_scientist.lambda_collapse, mod_warrior.lambda_collapse)
    
    def test_explorer_vs_diplomat_curiosity(self):
        """Explorer should have lower EVI threshold (more curious) than diplomat."""
        explorer = CharacterState.create_explorer()
        diplomat = CharacterState.create_diplomat()
        
        base = EpistemicThresholds(tau_epistemic=0.5)
        
        mod_explorer = compute_modulated_thresholds(base, explorer)
        mod_diplomat = compute_modulated_thresholds(base, diplomat)
        
        # Explorer asks more questions
        self.assertLess(mod_explorer.tau_epistemic, mod_diplomat.tau_epistemic)


class TestCharacterNonOverride(unittest.TestCase):
    """Test character non-override constraint."""
    
    def test_illegal_action_rejected(self):
        """Illegal actions must be rejected regardless of character."""
        allowed, reason = is_action_allowed(False, "budget exhausted")
        
        self.assertFalse(allowed)
        self.assertIn("lawful constraints", reason)
    
    def test_legal_action_allowed(self):
        """Legal actions can be allowed through character modulation."""
        allowed, reason = is_action_allowed(True)
        
        self.assertTrue(allowed)


class TestCharacterUtilities(unittest.TestCase):
    """Test utility functions."""
    
    def test_interpolation(self):
        """Test character interpolation."""
        c1 = CharacterState(chi_courage=0.0, chi_humility=0.0)
        c2 = CharacterState(chi_courage=1.0, chi_humility=1.0)
        
        mid = interpolate_character(c1, c2, 0.5)
        
        self.assertAlmostEqual(mid.chi_courage, 0.5)
        self.assertAlmostEqual(mid.chi_humility, 0.5)
    
    def test_summary(self):
        """Test character summary."""
        chi = CharacterState(chi_courage=0.7, chi_discipline=0.3)
        
        summary = character_summary(chi)
        
        self.assertEqual(summary['courage'], 0.7)
        self.assertEqual(summary['discipline'], 0.3)
    
    def test_serialization(self):
        """Test character serialization/deserialization."""
        chi = CharacterState(
            chi_courage=0.7,
            chi_discipline=0.3,
            chi_humility=0.9,
        )
        
        data = chi.to_dict()
        restored = CharacterState.from_dict(data)
        
        self.assertEqual(restored.chi_courage, chi.chi_courage)
        self.assertEqual(restored.chi_discipline, chi.chi_discipline)
        self.assertEqual(restored.chi_humility, chi.chi_humility)


class TestIntegrationWithEpistemic(unittest.TestCase):
    """Test that character properly modulates epistemic shell."""
    
    def test_full_modulation_cycle(self):
        """Test complete modulation cycle with all parameters."""
        # Create base epistemic thresholds
        base = EpistemicThresholds(
            lambda_collapse=0.5,
            tau_frag=0.5,
            tau_refresh=0.5,
            lambda_overreach=0.5,
            tau_epistemic=0.5,
            beta_delay=0.3,
            lambda_mania=0.3,
            tau_corr=0.6,
            lambda_shock=0.4,
        )
        
        # Apply scientist character
        scientist = CharacterState.create_scientist()
        mod = compute_modulated_thresholds(base, scientist)
        
        # Scientist should:
        # - Higher collapse resistance (higher lambda_collapse)
        self.assertGreater(mod.lambda_collapse, base.lambda_collapse)
        
        # - LOWER refresh threshold (discipline = refresh sooner when misfit rises)
        self.assertLess(mod.tau_refresh, base.tau_refresh)
        
        # - Higher corroboration demand
        self.assertGreater(mod.tau_corr, base.tau_corr)
        
        # - Lower shock sensitivity
        self.assertLess(mod.lambda_shock, base.lambda_shock)


if __name__ == '__main__':
    unittest.main()
