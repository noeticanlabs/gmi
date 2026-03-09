"""
Replenishment for GM-OS Action Layer.

Defines interface for externally verified budget replenishment.
Integrates with BudgetRouter for verified budget increases.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
import uuid
import time


@dataclass
class ReplenishmentReceipt:
    """Verified replenishment record."""
    receipt_id: str = field(default_factory=lambda: f"repl_{uuid.uuid4().hex[:12]}")
    amount: float = 0.0
    source: str = "external"
    verified: bool = False
    verification_method: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReplenishmentValidator:
    """
    Validates external budget replenishment.
    
    Provides mechanisms for verifying external validation sources
    before adding budget to the system.
    """
    
    def __init__(self, budget_router=None):
        """
        Initialize replenishment validator.
        
        Args:
            budget_router: Optional BudgetRouter for direct budget updates
        """
        self.budget_router = budget_router
        self.validators: Dict[str, Callable] = {}
        self.receipts: List[ReplenishmentReceipt] = []
    
    def register_validator(
        self,
        source: str,
        validator: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Register a validator for a replenishment source.
        
        Args:
            source: Name of the source
            validator: Function that validates replenishment data
        """
        self.validators[source] = validator
    
    def validate(
        self,
        source: str,
        external_validation: Dict[str, Any]
    ) -> bool:
        """
        Validate external replenishment data.
        
        Args:
            source: Source of the validation
            external_validation: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if source not in self.validators:
            # No validator registered - accept by default (or reject)
            return False
        
        try:
            validator = self.validators[source]
            return validator(external_validation)
        except Exception:
            return False
    
    def compute_replenishment(
        self,
        external_validation: Dict[str, Any],
        source: str = "external",
    ) -> ReplenishmentReceipt:
        """
        Compute externally verified replenishment amount.
        
        Args:
            external_validation: Validation data from external source
            source: Source of the validation
            
        Returns:
            ReplenishmentReceipt with verified amount
        """
        # Default computation - extract amount from validation
        amount = external_validation.get('amount', 0.0)
        
        # Validate if validator exists
        verified = False
        if source in self.validators:
            verified = self.validate(source, external_validation)
        else:
            # For now, accept if amount is positive
            verified = amount > 0
        
        receipt = ReplenishmentReceipt(
            amount=amount,
            source=source,
            verified=verified,
            verification_method=source if verified else "none",
            metadata=external_validation,
        )
        
        self.receipts.append(receipt)
        
        # Apply to budget router if verified
        if verified and self.budget_router and 'process_id' in external_validation:
            process_id = external_validation.get('process_id')
            layer = external_validation.get('layer', 0)
            # Budget router would need a replenish method
            # For now, this is handled externally
        
        return receipt
    
    def get_verified_receipts(
        self,
        since: Optional[float] = None,
    ) -> List[ReplenishmentReceipt]:
        """Get verified replenishment receipts."""
        receipts = [r for r in self.receipts if r.verified]
        
        if since:
            receipts = [r for r in receipts if r.timestamp >= since]
        
        return receipts


# Backwards compatibility function
def compute_verified_replenishment(
    external_validation: Dict[str, Any]
) -> ReplenishmentReceipt:
    """Compute externally verified replenishment amount."""
    validator = ReplenishmentValidator()
    return validator.compute_replenishment(external_validation)


# Common validator implementations

def validate_sensor_based(
    validation: Dict[str, Any]
) -> bool:
    """
    Validate based on sensor input.
    
    Expected format: {'type': 'sensor', 'sensor_data': {...}}
    """
    if validation.get('type') != 'sensor':
        return False
    
    sensor_data = validation.get('sensor_data', {})
    # Check for required fields
    return 'reading' in sensor_data


def validate_reward_based(
    validation: Dict[str, Any]
) -> bool:
    """
    Validate based on reward signal.
    
    Expected format: {'type': 'reward', 'reward': float}
    """
    if validation.get('type') != 'reward':
        return False
    
    reward = validation.get('reward', 0.0)
    # Accept positive rewards
    return reward > 0


def validate_anchor_based(
    validation: Dict[str, Any]
) -> bool:
    """
    Validate based on anchor/authority signal.
    
    Expected format: {'type': 'anchor', 'authority': float, 'percept': {...}}
    """
    if validation.get('type') != 'anchor':
        return False
    
    authority = validation.get('authority', 0.0)
    # Accept high-authority signals
    return authority > 0.8
