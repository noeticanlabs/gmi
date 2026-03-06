"""
Tests for ledger/oplax_verifier.py
"""
import numpy as np
import sys
sys.path.insert(0, '.')

from core.state import State, V_PL, Instruction, CompositeInstruction
from ledger.oplax_verifier import OplaxVerifier


class TestOplaxVerifier:
    """Test the OplaxVerifier class."""
    
    def test_verifier_accepts_descent(self):
        """Test verifier accepts a valid descent step."""
        verifier = OplaxVerifier(potential_fn=V_PL)
        state = State([1.0, 1.0], budget=10.0)
        
        # Small step that reduces potential
        instr = Instruction("DESCENT", lambda x: x * 0.5, sigma=0.5, kappa=0.5)
        
        accepted, next_state, receipt = verifier.check(1, state, instr)
        
        assert accepted is True
        assert receipt.decision == "ACCEPT"
    
    def test_verifier_rejects_ascent(self):
        """Test verifier rejects an ascent step that violates thermodynamic inequality."""
        verifier = OplaxVerifier(potential_fn=V_PL)
        state = State([0.5, 0.5], budget=5.0)
        
        # Large step that increases potential beyond budget
        instr = Instruction("ASCENT", lambda x: x + 10.0, sigma=5.0, kappa=5.0)
        
        accepted, next_state, receipt = verifier.check(1, state, instr)
        
        assert accepted is False
        assert receipt.decision == "REJECT"
    
    def test_composition_valid(self):
        """Test valid composition passes Oplax algebra."""
        verifier = OplaxVerifier(potential_fn=V_PL)
        
        r1 = Instruction("A", lambda x: x, sigma=1.0, kappa=1.0)
        r2 = Instruction("B", lambda x: x, sigma=1.0, kappa=1.0)
        
        # sigma >= sigma1 + sigma2, kappa <= kappa1 + kappa2
        comp = CompositeInstruction(r1, r2, sigma=2.0, kappa=2.0)
        
        valid, msg = verifier.verify_composition(comp)
        
        assert valid is True
    
    def test_composition_invalid_metabolic_undercharge(self):
        """Test invalid composition fails metabolic undercharge check."""
        verifier = OplaxVerifier(potential_fn=V_PL)
        
        r1 = Instruction("A", lambda x: x, sigma=1.0, kappa=1.0)
        r2 = Instruction("B", lambda x: x, sigma=1.0, kappa=1.0)
        
        # sigma < sigma1 + sigma2 (undercharge)
        comp = CompositeInstruction(r1, r2, sigma=1.5, kappa=2.0)
        
        valid, msg = verifier.verify_composition(comp)
        
        assert valid is False
        assert "Metabolic Undercharge" in msg
    
    def test_composition_invalid_defect_laundering(self):
        """Test invalid composition fails defect laundering check."""
        verifier = OplaxVerifier(potential_fn=V_PL)
        
        r1 = Instruction("A", lambda x: x, sigma=1.0, kappa=1.0)
        r2 = Instruction("B", lambda x: x, sigma=1.0, kappa=1.0)
        
        # kappa > kappa1 + kappa2 (laundering)
        comp = CompositeInstruction(r1, r2, sigma=2.0, kappa=3.0)
        
        valid, msg = verifier.verify_composition(comp)
        
        assert valid is False
        assert "Defect Laundering" in msg
    
    def test_budget_exhaustion_rejection(self):
        """Test verifier rejects when budget is exhausted."""
        verifier = OplaxVerifier(potential_fn=V_PL)
        state = State([1.0, 1.0], budget=0.0)
        
        instr = Instruction("STEP", lambda x: x + 0.1, sigma=1.0, kappa=1.0)
        
        accepted, next_state, receipt = verifier.check(1, state, instr)
        
        assert accepted is False
        assert receipt.decision == "REJECT"
        assert "budget" in receipt.message.lower()


class TestOplaxVerifierWithCustomPotential:
    """Test verifier with custom potential functions."""
    
    def test_custom_potential_injection(self):
        """Test that custom potential can be injected."""
        def custom_v(x):
            return float(np.sum((x - 5.0)**2))  # Minimum at x=5
        
        verifier = OplaxVerifier(potential_fn=custom_v)
        state = State([1.0, 1.0], budget=100.0)
        
        # Move toward x=5
        instr = Instruction("TO_GOAL", lambda x: x + 1.0, sigma=5.0, kappa=5.0)
        
        accepted, next_state, receipt = verifier.check(1, state, instr)
        
        # Should accept if moving toward minimum
        assert accepted is True
