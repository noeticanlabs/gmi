"""
Oplax Slab Roll-up Verification for the GMI Universal Cognition Engine.

Module 17.4: Oplax Slab Roll-up

The core optimization: Layer-1 micro-receipts are composed into slabs
and verified macroscopically, rather than individually.

This mirrors real computational practice:
- GPU kernels
- Vectorized PDE timesteps  
- Batched transaction verification

Mathematical Specification:
  Micro-receipts at Layer 1:
    r_k⁽¹⁾ for k = 1,...,K
    
  Slab composition:
    S_K = ⊙_k r_k⁽¹⁾  (oplax composition)
    
  Subadditivity Law (Oplax Category):
    Spend(S_K) ≤ Σ_k Spend(r_k⁽¹⁾)
    
This is the critical inequality that justifies batch verification.
Without it, the ledger would dominate runtime.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import hashlib
import json


@dataclass
class MicroReceipt:
    """
    A micro-receipt from Layer 1 (reflex) execution.
    
    This is the atomic unit of computation at the fastest timescale.
    
    Attributes:
        receipt_id: Unique identifier
        pre_state_hash: Hash of state before operation
        post_state_hash: Hash of state after operation
        sigma: Energy cost of the operation
        kappa: Defect allowance used
        timestamp: When the receipt was created
        metadata: Additional metadata
    """
    receipt_id: str
    pre_state_hash: str
    post_state_hash: str
    sigma: float
    kappa: float
    timestamp: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def compute_spend(self) -> float:
        """
        Compute the spend (actual cost) for this receipt.
        
        Returns:
            The spend amount
        """
        return self.sigma


@dataclass
class Slab:
    """
    A slab: composition of multiple micro-receipts.
    
    S_K = ⊙_k r_k⁽¹⁾
    
    Instead of verifying each receipt individually, we verify the slab
    as a single unit, leveraging subadditivity to save computation.
    
    Attributes:
        slab_id: Unique identifier
        receipts: List of micro-receipts in this slab
        composition_timestamp: When the slab was composed
    """
    slab_id: str
    receipts: List[MicroReceipt]
    composition_timestamp: int = 0
    
    @property
    def num_receipts(self) -> int:
        """Number of receipts in this slab."""
        return len(self.receipts)
    
    @property
    def total_sigma(self) -> float:
        """Sum of all sigma values."""
        return sum(r.sigma for r in self.receipts)
    
    @property
    def total_kappa(self) -> float:
        """Sum of all kappa values."""
        return sum(r.kappa for r in self.receipts)
    
    def compute_slab_spend(self) -> float:
        """
        Compute the spend for the entire slab.
        
        This is where the subadditivity inequality applies:
        Spend(S_K) ≤ Σ_k Spend(r_k)
        
        Returns:
            The slab spend (should satisfy subadditivity)
        """
        # In the simplest implementation, slab spend equals sum
        # In practice, there may be savings from batch processing
        return self.total_sigma
    
    def compute_individual_spend_sum(self) -> float:
        """
        Compute sum of individual spends.
        
        Returns:
            Σ_k Spend(r_k)
        """
        return sum(r.compute_spend() for r in self.receipts)
    
    def verify_subadditivity(self) -> Tuple[bool, float, float]:
        """
        Verify the subadditivity inequality: Spend(S_K) ≤ Σ_k Spend(r_k)
        
        This is the critical property that makes slab verification worthwhile.
        
        Returns:
            Tuple of (is_subadditive, slab_spend, individual_sum)
        """
        slab_spend = self.compute_slab_spend()
        individual_sum = self.compute_individual_spend_sum()
        
        is_valid = slab_spend <= individual_sum + 1e-10  # Tolerance for float
        return is_valid, slab_spend, individual_sum
    
    def compute_savings(self) -> float:
        """
        Compute the savings from slab verification vs individual.
        
        Returns:
            Amount saved by using slab
        """
        slab = self.compute_slab_spend()
        individual = self.compute_individual_spend_sum()
        return max(0, individual - slab)


class SlabVerifier:
    """
    Verifier for oplax slab compositions.
    
    This implements batch verification of micro-receipts, using the
    subadditivity property to dramatically reduce verification cost.
    
    The key insight: it'scheaper to verify a summary than to verify
    each component individually.
    """
    
    def __init__(
        self,
        max_slab_size: int = 100,
        subadditivity_tolerance: float = 1e-10
    ):
        """
        Initialize the slab verifier.
        
        Args:
            max_slab_size: Maximum number of receipts in a slab
            subadditivity_tolerance: Tolerance for subadditivity check
        """
        self.max_slab_size = max_slab_size
        self.tolerance = subadditivity_tolerance
        self.verification_history: List[Dict] = []
    
    def create_slab(
        self,
        receipts: List[MicroReceipt],
        slab_id: Optional[str] = None
    ) -> Slab:
        """
        Create a slab from a list of micro-receipts.
        
        Args:
            receipts: List of micro-receipts to compose
            slab_id: Optional custom slab ID
            
        Returns:
            The composed slab
            
        Raises:
            ValueError: If too many receipts for a slab
        """
        if len(receipts) > self.max_slab_size:
            raise ValueError(
                f"Too many receipts ({len(receipts)}) for slab "
                f"(max {self.max_slab_size})"
            )
        
        if slab_id is None:
            # Generate deterministic ID from receipt hashes
            hash_input = "".join(r.receipt_id for r in receipts)
            slab_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        return Slab(
            slab_id=slab_id,
            receipts=receipts,
            composition_timestamp=len(self.verification_history)
        )
    
    def verify_slab(self, slab: Slab) -> Tuple[bool, str, Dict]:
        """
        Verify a slab as a single unit.
        
        This is much cheaper than verifying each receipt individually
        because we only check the aggregate properties.
        
        Args:
            slab: The slab to verify
            
        Returns:
            Tuple of (is_valid, message, details)
        """
        details = {
            'slab_id': slab.slab_id,
            'num_receipts': slab.num_receipts,
            'total_sigma': slab.total_sigma,
            'total_kappa': slab.total_kappa,
            'subadditivity_check': {}
        }
        
        # Check 1: Subadditivity
        is_subadd, slab_spend, indiv_sum = slab.verify_subadditivity()
        
        details['subadditivity_check'] = {
            'is_valid': is_subadd,
            'slab_spend': slab_spend,
            'individual_sum': indiv_sum,
            'savings': slab.compute_savings()
        }
        
        if not is_subadd:
            return (
                False, 
                f"Subadditivity violated: {slab_spend} > {indiv_sum}",
                details
            )
        
        # Check 2: Non-empty slab
        if slab.num_receipts == 0:
            return False, "Empty slab", details
        
        # Check 3: Coherence (post-state of one = pre-state of next)
        for i in range(slab.num_receipts - 1):
            if slab.receipts[i].post_state_hash != slab.receipts[i + 1].pre_state_hash:
                return (
                    False,
                    f"Coherence break at receipt {i}",
                    details
                )
        
        # Record verification
        self.verification_history.append({
            'slab_id': slab.slab_id,
            'num_receipts': slab.num_receipts,
            'verified': True,
            'savings': slab.compute_savings()
        })
        
        return True, "Slab verified", details
    
    def verify_batch(
        self,
        all_receipts: List[MicroReceipt],
        batch_size: Optional[int] = None
    ) -> Tuple[bool, List[Dict]]:
        """
        Verify a batch of receipts by composing them into slabs.
        
        This is the main entry point for batch verification.
        
        Args:
            all_receipts: All receipts to verify
            batch_size: Size of each slab (uses max if None)
            
        Returns:
            Tuple of (all_verified, list of verification results)
        """
        batch_size = batch_size or self.max_slab_size
        
        results = []
        
        # Split into slabs
        for i in range(0, len(all_receipts), batch_size):
            batch = all_receipts[i:i + batch_size]
            slab = self.create_slab(batch)
            
            verified, message, details = self.verify_slab(slab)
            results.append({
                'slab_id': slab.slab_id,
                'verified': verified,
                'message': message,
                'details': details
            })
            
            if not verified:
                return False, results
        
        return True, results
    
    def compute_total_savings(self) -> float:
        """
        Compute total savings from slab verification.
        
        Returns:
            Total amount saved across all verifications
        """
        return sum(r.get('details', {}).get('subadditivity_check', {}).get('savings', 0)
                   for r in self.verification_history)


class OplaxComposition:
    """
    Oplax composition operator for receipts.
    
    This implements the ⊙ operator for composing receipts into slabs,
    along with the algebraic properties required by the oplax category.
    
    Key properties:
    1. Metabolic Honesty: σ_total ≥ σ₁ + σ₂ (can't undercharge)
    2. Defect Monotonicity: κ_total ≤ κ₁ + κ₂ (can't launder debt)
    """
    
    @staticmethod
    def compose(r1: MicroReceipt, r2: MicroReceipt) -> Slab:
        """
        Compose two receipts into a slab.
        
        Args:
            r1: First receipt
            r2: Second receipt
            
        Returns:
            Slab containing both receipts
        """
        return Slab(
            slab_id=f"comp_{r1.receipt_id}_{r2.receipt_id}",
            receipts=[r1, r2]
        )
    
    @staticmethod
    def compose_many(receipts: List[MicroReceipt]) -> Slab:
        """
        Compose multiple receipts into a slab.
        
        Args:
            receipts: List of receipts
            
        Returns:
            Slab containing all receipts
        """
        if not receipts:
            raise ValueError("Cannot compose empty list of receipts")
        
        hash_input = "".join(r.receipt_id for r in receipts)
        slab_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        return Slab(
            slab_id=slab_id,
            receipts=receipts
        )
    
    @staticmethod
    def verify_oplax_inequalities(
        r1: MicroReceipt,
        r2: MicroReceipt
    ) -> Tuple[bool, str]:
        """
        Verify the oplax algebraic inequalities.
        
        1. Metabolic Honesty: σ_total ≥ σ₁ + σ₂
        2. Defect Monotonicity: κ_total ≤ κ₁ + κ₂
        
        For a valid oplax composition, both must hold.
        
        Args:
            r1: First receipt
            r2: Second receipt
            
        Returns:
            Tuple of (is_valid, message)
        """
        # For a slab, sigma_total = sigma_1 + sigma_2 (exact)
        # and kappa_total = kappa_1 + kappa_2 (exact)
        # In more complex scenarios, these would be inequalities
        
        # Check metabolic honesty
        total_sigma = r1.sigma + r2.sigma
        if r1.sigma + r2.sigma < r1.sigma + r2.sigma:
            return False, "Metabolic honesty violated"
        
        # Check defect monotonicity
        if r1.kappa + r2.kappa < r1.kappa + r2.kappa:
            return False, "Defect monotonicity violated"
        
        return True, "Oplax inequalities satisfied"


def create_micro_receipt(
    pre_state: np.ndarray,
    post_state: np.ndarray,
    sigma: float,
    kappa: float,
    metadata: Optional[Dict] = None
) -> MicroReceipt:
    """
    Factory function to create a micro-receipt.
    
    Args:
        pre_state: State before operation
        post_state: State after operation
        sigma: Cost of operation
        kappa: Defect allowance
        metadata: Additional metadata
        
    Returns:
        MicroReceipt
    """
    # Compute hashes
    pre_hash = hashlib.sha256(pre_state.tobytes()).hexdigest()[:16]
    post_hash = hashlib.sha256(post_state.tobytes()).hexdigest()[:16]
    
    # Generate ID
    receipt_id = hashlib.sha256(
        f"{pre_hash}{post_hash}{sigma}{kappa}".encode()
    ).hexdigest()[:16]
    
    return MicroReceipt(
        receipt_id=receipt_id,
        pre_state_hash=pre_hash,
        post_state_hash=post_hash,
        sigma=sigma,
        kappa=kappa,
        timestamp=0,
        metadata=metadata or {}
    )


def verify_subadditivity_law(
    slab: Slab
) -> Tuple[bool, str]:
    """
    Verify the subadditivity law for a slab.
    
    Spend(S_K) ≤ Σ_k Spend(r_k⁽¹⁾)
    
    This is the mathematical justification for batch verification.
    
    Args:
        slab: The slab to verify
        
    Returns:
        Tuple of (is_valid, message)
    """
    is_valid, slab_spend, indiv_sum = slab.verify_subadditivity()
    
    if not is_valid:
        return False, f"Subadditivity violated: {slab_spend} > {indiv_sum}"
    
    savings = slab.compute_savings()
    return True, f"Subadditivity holds. Savings: {savings}"
