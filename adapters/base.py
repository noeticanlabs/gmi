"""
Base Adapter for the GMI Universal Cognition Engine.

All domain adapters must implement this interface to plug into the universal cognition engine.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import numpy as np


@dataclass
class DomainEncoding:
    """
    Result of encoding domain input into universal schema.
    
    Contains:
    - rho: embedding coordinates
    - theta: phase/direction
    - domain_metrics: domain-specific residuals
    - authority: amplification factor
    """
    rho: np.ndarray
    theta: np.ndarray
    domain_metrics: Dict[str, float]
    authority: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DomainAdapter(ABC):
    """
    Base class for domain adapters.
    
    All adapters must map their domain to the universal CognitiveState schema.
    This allows Navier-Stokes, planning, language, theorem search, and GR
    all become special cases of the same engine.
    """
    
    def __init__(self, name: str, domain_name: str):
        """
        Initialize adapter.
        
        Args:
            name: Adapter name
            domain_name: Name of the domain
        """
        self.name = name
        self.domain_name = domain_name
        self.authority = 1.0
    
    @abstractmethod
    def encode(self, domain_input: Any) -> DomainEncoding:
        """
        Encode domain-specific input to universal schema.
        
        Args:
            domain_input: Input from domain
            
        Returns:
            DomainEncoding with universal schema components
        """
        pass
    
    @abstractmethod
    def decode(self, cognitive_state: 'CognitiveState') -> Any:
        """
        Decode universal state back to domain representation.
        
        Args:
            cognitive_state: Universal cognitive state
            
        Returns:
            Domain-specific representation
        """
        pass
    
    @abstractmethod
    def contribute_to_potential(self, domain_encoding: DomainEncoding) -> float:
        """
        Compute domain-specific potential term.
        
        Called by GMIPotential.domain_term() to include domain residuals.
        
        Args:
            domain_encoding: Encoded domain state
            
        Returns:
            Domain contribution to potential (higher = more incoherent)
        """
        pass
    
    @abstractmethod
    def generate_proposal(
        self, 
        cognitive_state: 'CognitiveState',
        instruction_type: str
    ) -> np.ndarray:
        """
        Generate a proposal in universal space.
        
        Args:
            cognitive_state: Current universal state
            instruction_type: Type of instruction ("EXPLORE", "INFER", etc.)
            
        Returns:
            Proposed delta in universal space
        """
        pass
    
    def validate_input(self, domain_input: Any) -> bool:
        """
        Validate domain input.
        
        Args:
            domain_input: Input to validate
            
        Returns:
            True if valid
        """
        return True
    
    def get_domain_metrics(self, domain_input: Any) -> Dict[str, float]:
        """
        Extract domain-specific metrics from input.
        
        Args:
            domain_input: Domain input
            
        Returns:
            Dict of metric_name -> value
        """
        return {}


class CognitiveState:
    """
    Universal cognitive state (placeholder - actual definition in core/state.py).
    """
    pass


class AdapterRegistry:
    """
    Registry for domain adapters.
    
    Allows dynamic registration and lookup of adapters by domain.
    """
    
    def __init__(self):
        self._adapters: Dict[str, DomainAdapter] = {}
    
    def register(self, adapter: DomainAdapter) -> None:
        """Register an adapter."""
        self._adapters[adapter.domain_name] = adapter
    
    def get(self, domain_name: str) -> Optional[DomainAdapter]:
        """Get adapter by domain name."""
        return self._adapters.get(domain_name)
    
    def list_domains(self) -> List[str]:
        """List all registered domains."""
        return list(self._adapters.keys())
    
    def unregister(self, domain_name: str) -> bool:
        """Unregister an adapter."""
        if domain_name in self._adapters:
            del self._adapters[domain_name]
            return True
        return False


# Global registry
_global_registry: Optional[AdapterRegistry] = None


def get_adapter_registry() -> AdapterRegistry:
    """Get or create global adapter registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AdapterRegistry()
    return _global_registry


def register_adapter(adapter: DomainAdapter) -> None:
    """Register an adapter in the global registry."""
    get_adapter_registry().register(adapter)
