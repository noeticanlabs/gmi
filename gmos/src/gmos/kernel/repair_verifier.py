"""
Repair Verifier for GM-OS Self-Repair System.

Implements repair admissibility verification per Self-Repair Model Section 13:

Given repair transition: x → x'

Repair is lawful iff:
    V(x') + Spend(r) ≤ V(x) + Defect(r)

And:
    Spend(r) ≤ B - B_reserve

This ensures healing is budgeted and soundness is preserved.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Any
from enum import Enum
import time


class RepairType(Enum):
    """Types of repair operations."""
    LOCAL_CORRECTION = "r1"      # Band 1
    TARGETED_REPAIR = "r2"      # Band 2
    STRUCTURAL_CONTRACTION = "r3"  # Band 3
    SAFE_STATE_COLLAPSE = "r4"   # Band 4


class RepairDecision(Enum):
    """Repair verification decision."""
    APPROVED = "approved"
    REJECTED_INSUFFICIENT_BUDGET = "rejected_insufficient_budget"
    REJECTED_SOUNDNESS_VIOLATION = "rejected_soundness_violation"
    REJECTED_KERNEL_NOT_PRESERVED = "rejected_kernel_not_preserved"
    REJECTED_IDENTITY_FRACTURE = "rejected_identity_fracture"


@dataclass
class RepairTransition:
    """A repair transition to verify."""
    repair_type: RepairType
    
    # State values
    v_before: float
    v_after: float
    
    # Cost components
    spend: float
    defect: float
    
    # Budget context
    budget_before: float
    reserve_floor: float
    
    # Identity context
    kernel_preserved: bool = True
    identity_deformation: float = 0.0
    
    # Metadata
    repair_action: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class VerificationResult:
    """Result of repair verification."""
    decision: RepairDecision
    is_lawful: bool
    
    # Details
    soundness_check: bool = False
    budget_check: bool = False
    kernel_check: bool = False
    identity_check: bool = False
    
    # Margins
    soundness_margin: float = 0.0
    budget_margin: float = 0.0
    
    # Message
    message: str = ""


class RepairVerifier:
    """
    Verifies repair transitions are lawful.
    
    Per Self-Repair Model Section 13 (Repair Admissibility Lemma):
    
    If:
        1. V(x') ≤ V(x), T(x') ≤ T(x), C(x') ≤ C(x)
        2. Spend(r) ≤ B - B_reserve
        3. V(x') + Spend(r) ≤ V(x) + Defect(r)
    
    Then repair is lawful.
    """
    
    def __init__(
        self,
        enable_kernel_check: bool = True,
        enable_identity_check: bool = True,
        max_identity_deformation: float = 0.1,
        safety_margin: float = 0.0
    ):
        """
        Args:
            enable_kernel_check: Verify kernel preserved
            enable_identity_check: Verify identity continuity
            max_allowed_deformation: Maximum allowed identity deformation
            safety_margin: Additional budget safety buffer
        """
        self.enable_kernel_check = enable_kernel_check
        self.enable_identity_check = enable_identity_check
        self.max_identity_deformation = max_identity_deformation
        self.safety_margin = safety_margin
        
        # Statistics
        self.total_verifications = 0
        self.approved_count = 0
        self.rejected_count = 0
    
    def verify(self, transition: RepairTransition) -> VerificationResult:
        """
        Verify a repair transition is lawful.
        
        Args:
            transition: Repair transition to verify
            
        Returns:
            VerificationResult with decision
        """
        self.total_verifications += 1
        
        # Check 1: Budget availability
        available = transition.budget_before - transition.reserve_floor - self.safety_margin
        budget_check = transition.spend <= available
        budget_margin = available - transition.spend
        
        if not budget_check:
            self.rejected_count += 1
            return VerificationResult(
                decision=RepairDecision.REJECTED_INSUFFICIENT_BUDGET,
                is_lawful=False,
                budget_check=False,
                budget_margin=budget_margin,
                message=f"Repair spend {transition.spend} exceeds available budget {available}"
            )
        
        # Check 2: Soundness law (Coh)
        # V(x') + Spend ≤ V(x) + Defect
        left_side = transition.v_after + transition.spend
        right_side = transition.v_before + transition.defect
        soundness_check = left_side <= right_side
        soundness_margin = right_side - left_side
        
        if not soundness_check:
            self.rejected_count += 1
            return VerificationResult(
                decision=RepairDecision.REJECTED_SOUNDNESS_VIOLATION,
                is_lawful=False,
                soundness_check=False,
                budget_check=True,
                soundness_margin=soundness_margin,
                message=f"Soundness violated: {left_side} > {right_side}"
            )
        
        # Check 3: Kernel preservation (if enabled)
        kernel_check = True
        if self.enable_kernel_check:
            kernel_check = transition.kernel_preserved
        
        if not kernel_check:
            self.rejected_count += 1
            return VerificationResult(
                decision=RepairDecision.REJECTED_KERNEL_NOT_PRESERVED,
                is_lawful=False,
                soundness_check=True,
                budget_check=True,
                kernel_check=False,
                message="Kernel preservation check failed"
            )
        
        # Check 4: Identity continuity (if enabled)
        identity_check = True
        if self.enable_identity_check:
            identity_check = transition.identity_deformation <= self.max_identity_deformation
        
        if not identity_check:
            self.rejected_count += 1
            return VerificationResult(
                decision=RepairDecision.REJECTED_IDENTITY_FRACTURE,
                is_lawful=False,
                soundness_check=True,
                budget_check=True,
                kernel_check=True,
                identity_check=False,
                message=f"Identity deformation {transition.identity_deformation} exceeds max {self.max_identity_deformation}"
            )
        
        # All checks passed
        self.approved_count += 1
        return VerificationResult(
            decision=RepairDecision.APPROVED,
            is_lawful=True,
            soundness_check=True,
            budget_check=True,
            kernel_check=kernel_check,
            identity_check=identity_check,
            soundness_margin=soundness_margin,
            budget_margin=budget_margin,
            message="Repair approved"
        )
    
    def quick_verify(
        self,
        v_before: float,
        v_after: float,
        spend: float,
        defect: float,
        budget: float,
        reserve: float
    ) -> Tuple[bool, str]:
        """
        Quick verification without full transition object.
        
        Args:
            v_before: Potential before
            v_after: Potential after
            spend: Repair cost
            defect: Defect from repair
            budget: Current budget
            reserve: Reserve floor
            
        Returns:
            (is_lawful, message)
        """
        # Budget check
        available = budget - reserve - self.safety_margin
        if spend > available:
            return False, f"Insufficient budget: {spend} > {available}"
        
        # Soundness check
        if v_after + spend > v_before + defect:
            return False, f"Soundness violated: {v_after + spend} > {v_before + defect}"
        
        return True, "Repair lawful"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get verification statistics."""
        return {
            "total_verifications": self.total_verifications,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "approval_rate": self.approved_count / max(1, self.total_verifications)
        }
    
    def reset_statistics(self) -> None:
        """Reset verification statistics."""
        self.total_verifications = 0
        self.approved_count = 0
        self.rejected_count = 0


def create_repair_verifier(
    enable_kernel_check: bool = True,
    enable_identity_check: bool = True
) -> RepairVerifier:
    """
    Factory function to create a repair verifier.
    
    Args:
        enable_kernel_check: Verify kernel preserved
        enable_identity_check: Verify identity continuity
        
    Returns:
        Configured RepairVerifier
    """
    return RepairVerifier(
        enable_kernel_check=enable_kernel_check,
        enable_identity_check=enable_identity_check
    )
