"""
Protected Identity Kernel for GM-OS.

Implements the minimal identity kernel per Identity Kernel Model Section 14:

    K^id_v0.1 = (process_id, genesis_receipt_hash, chain_digest, policy_hash, B_reserve, checkpoint_id)

This is the minimal anchor set that allows a hosted process to:
- Survive sleep, repair, contraction, or torpor
- Restore lawfully without ceasing to be itself
- Prove identity continuity to the verifier

Per Identity Kernel Model Section 11: The process may think with its mind, but not with its spine.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from enum import Enum
import hashlib
import time


class IdentityStatus(Enum):
    """Identity continuity status."""
    INTACT = "intact"              # Kernel fully preserved
    DEFORMED = "deformed"          # Kernel within admissible deformation
    FRACTURED = "fractured"        # Provenance broken
    AMNESIAC = "amnesiac"          # Policy lost
    HOLLOW = "hollow"              # Semantic core degraded
    FRAUDULENT = "fraudulent"      # Reserve violated
    DEAD = "dead"                  # Identity lost


class IdentityFailure(Enum):
    """Classes of identity failure per Identity Kernel Model Section 9."""
    NONE = "none"
    SOFT_CONTRACTION = "soft_contraction"    # Working state lost, kernel preserved
    PROVENANCE_FRACTURE = "provenance_fracture"  # Omega broken
    POLICY_AMNESIA = "policy_amnesia"        # Pi lost
    SEMANTIC_HOLLOWING = "semantic_hollowing"  # Sigma degraded
    METABOLIC_FRAUD = "metabolic_fraud"      # Lambda violated
    IDENTITY_DEATH = "identity_death"        # ID or shell lost


@dataclass
class IdentityKernel:
    """
    Protected Identity Kernel for a hosted process.
    
    Per Identity Kernel Model Section 14 (v0.1):
    
        K^id_v0.1 = (process_id, genesis_receipt_hash, chain_digest, policy_hash, B_reserve, checkpoint_id)
    
    This is the minimal set required for lawful identity continuity.
    """
    # Core identity
    process_id: str = ""
    genesis_receipt_hash: str = ""
    
    # Provenance anchor
    chain_digest: str = ""
    
    # Policy anchor
    policy_hash: str = ""
    
    # Reserve anchor
    reserve_floor: float = 10.0
    last_budget: float = 0.0
    
    # Checkpoint anchor
    latest_checkpoint_id: str = ""
    latest_checkpoint_hash: str = ""
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    last_verified_at: float = field(default_factory=time.time)
    
    def compute_hash(self) -> str:
        """
        Compute canonical hash of the kernel for verification.
        
        This allows the verifier to check identity continuity
        without exposing internal state.
        """
        data = f"{self.process_id}:{self.genesis_receipt_hash}:{self.chain_digest}:{self.policy_hash}:{self.reserve_floor}:{self.latest_checkpoint_id}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize kernel to dictionary."""
        return {
            "process_id": self.process_id,
            "genesis_receipt_hash": self.genesis_receipt_hash,
            "chain_digest": self.chain_digest,
            "policy_hash": self.policy_hash,
            "reserve_floor": self.reserve_floor,
            "last_budget": self.last_budget,
            "latest_checkpoint_id": self.latest_checkpoint_id,
            "latest_checkpoint_hash": self.latest_checkpoint_hash,
            "kernel_hash": self.compute_hash(),
            "created_at": self.created_at,
            "last_verified_at": self.last_verified_at
        }


@dataclass
class IdentityMetrics:
    """Metrics for identity continuity assessment."""
    # Deformation distances
    id_distance: float = 0.0       # 0 if exact match, inf if lost
    omega_distance: float = 0.0     # Chain distance
    pi_distance: float = 0.0       # Policy mismatch
    sigma_distance: float = 0.0     # Semantic loss
    lambda_distance: float = 0.0    # Reserve distortion
    
    # Composite
    total_deformation: float = 0.0
    
    # Status
    status: IdentityStatus = IdentityStatus.INTACT
    failure: IdentityFailure = IdentityFailure.NONE
    
    # Timestamp
    computed_at: float = field(default_factory=time.time)


class IdentityKernelManager:
    """
    Manages identity kernels for hosted processes.
    
    Per Identity Kernel Model Section 5: Identity Continuity Law
    - Canonical identity preservation (ID)
    - Provenance continuity (Omega)  
    - Policy continuity (Pi)
    - Kernel deformation bounds
    """
    
    def __init__(self):
        self._kernels: Dict[str, IdentityKernel] = {}
        self._metrics: Dict[str, IdentityMetrics] = {}
    
    def create_kernel(
        self,
        process_id: str,
        genesis_receipt_hash: str,
        policy_hash: str = "",
        reserve_floor: float = 10.0
    ) -> IdentityKernel:
        """
        Create a new identity kernel for a process.
        
        This is called at process genesis.
        """
        kernel = IdentityKernel(
            process_id=process_id,
            genesis_receipt_hash=genesis_receipt_hash,
            chain_digest=genesis_receipt_hash,  # Start with genesis
            policy_hash=policy_hash,
            reserve_floor=reserve_floor,
            last_budget=0.0
        )
        
        self._kernels[process_id] = kernel
        self._metrics[process_id] = IdentityMetrics()
        
        return kernel
    
    def get_kernel(self, process_id: str) -> Optional[IdentityKernel]:
        """Get kernel for a process."""
        return self._kernels.get(process_id)
    
    def update_chain_digest(self, process_id: str, digest: str) -> bool:
        """
        Update chain digest (provenance anchor).
        
        Per Identity Kernel Model Section 4.2:
        Omega must track chain continuity.
        """
        kernel = self._kernels.get(process_id)
        if kernel is None:
            return False
        
        kernel.chain_digest = digest
        kernel.last_verified_at = time.time()
        return True
    
    def update_checkpoint(
        self,
        process_id: str,
        checkpoint_id: str,
        checkpoint_hash: str
    ) -> bool:
        """
        Update checkpoint anchor.
        
        Per Identity Kernel Model Section 4.4:
        Sigma includes latest stable shell.
        """
        kernel = self._kernels.get(process_id)
        if kernel is None:
            return False
        
        kernel.latest_checkpoint_id = checkpoint_id
        kernel.latest_checkpoint_hash = checkpoint_hash
        return True
    
    def update_budget(self, process_id: str, budget: float) -> bool:
        """
        Update budget tracking.
        
        Per Identity Kernel Model Section 4.5:
        Lambda tracks reserve continuity.
        """
        kernel = self._kernels.get(process_id)
        if kernel is None:
            return False
        
        kernel.last_budget = budget
        return True
    
    def verify_continuity(
        self,
        process_id: str,
        current_chain_digest: str,
        current_policy_hash: str,
        current_budget: float
    ) -> IdentityMetrics:
        """
        Verify identity continuity.
        
        Per Identity Kernel Model Section 5:
        Identity is preserved if kernel deformation ≤ epsilon.
        
        Returns:
            IdentityMetrics with deformation assessment
        """
        kernel = self._kernels.get(process_id)
        if kernel is None:
            return IdentityMetrics(
                status=IdentityStatus.DEAD,
                failure=IdentityFailure.IDENTITY_DEATH
            )
        
        metrics = IdentityMetrics()
        
        # Check ID preservation
        if kernel.process_id != process_id:
            metrics.id_distance = float('inf')
            metrics.status = IdentityStatus.DEAD
            metrics.failure = IdentityFailure.IDENTITY_DEATH
            return metrics
        
        # Check provenance (Omega)
        if current_chain_digest != kernel.chain_digest:
            # Chain changed - check it's a lawful extension
            metrics.omega_distance = 1.0  # Simple model: 1 = changed
        else:
            metrics.omega_distance = 0.0
        
        # Check policy (Pi)
        if current_policy_hash != kernel.policy_hash:
            metrics.pi_distance = 1.0
        else:
            metrics.pi_distance = 0.0
        
        # Check reserve (Lambda)
        if current_budget < kernel.reserve_floor:
            metrics.lambda_distance = 1.0
            metrics.status = IdentityStatus.FRAUDULENT
            metrics.failure = IdentityFailure.METABOLIC_FRAUD
        else:
            metrics.lambda_distance = 0.0
        
        # Compute total deformation
        metrics.total_deformation = (
            metrics.id_distance +
            metrics.omega_distance +
            metrics.pi_distance +
            metrics.lambda_distance
        )
        
        # Determine status
        if metrics.total_deformation == 0:
            metrics.status = IdentityStatus.INTACT
        elif metrics.total_deformation < 0.5:
            metrics.status = IdentityStatus.DEFORMED
        elif metrics.lambda_distance > 0:
            metrics.status = IdentityStatus.FRAUDULENT
        else:
            metrics.status = IdentityStatus.FRACTURED
            metrics.failure = IdentityFailure.PROVENANCE_FRACTURE
        
        # Store metrics
        self._metrics[process_id] = metrics
        
        return metrics
    
    def can_restore(
        self,
        process_id: str,
        target_budget: float
    ) -> bool:
        """
        Check if process can be restored.
        
        Per Identity Kernel Model Section 8:
        Restoration is possible if kernel preserved and budget ≥ reserve.
        """
        kernel = self._kernels.get(process_id)
        if kernel is None:
            return False
        
        # Must have budget to restore
        if target_budget < kernel.reserve_floor:
            return False
        
        # Check recent metrics
        metrics = self._metrics.get(process_id)
        if metrics and metrics.status == IdentityStatus.DEAD:
            return False
        
        return True
    
    def get_status(self, process_id: str) -> Optional[IdentityStatus]:
        """Get current identity status."""
        metrics = self._metrics.get(process_id)
        return metrics.status if metrics else None


def create_identity_kernel(
    process_id: str,
    initial_budget: float = 100.0,
    reserve_floor: float = 10.0
) -> IdentityKernel:
    """
    Factory function to create a new identity kernel.
    
    Args:
        process_id: Unique process identifier
        initial_budget: Starting budget
        reserve_floor: Protected reserve
        
    Returns:
        Initialized IdentityKernel
    """
    # Generate genesis hash
    genesis_data = f"{process_id}:{time.time()}:{initial_budget}"
    genesis_hash = hashlib.sha256(genesis_data.encode()).hexdigest()
    
    return IdentityKernel(
        process_id=process_id,
        genesis_receipt_hash=genesis_hash,
        chain_digest=genesis_hash,
        reserve_floor=reserve_floor,
        last_budget=initial_budget
    )
