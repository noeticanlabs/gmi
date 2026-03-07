# Adapter Package for the GMI Universal Cognition Engine

# This package provides bridges between domain-specific proposals and GMI verification.

# Base adapter interface
from .base import (
    DomainAdapter,
    DomainEncoding,
    AdapterRegistry,
    get_adapter_registry,
    register_adapter
)

# NPE Adapter
from .npe_adapter import (
    NPEAdapter,
    GMIToNPEFeedback,
    CombinedRuntime,
    NPEProposal,
    CoherenceMetrics
)

# Stochastic Synthesizer
from .stochastic_synthesizer import (
    StochasticSynthesizer,
    OperatorHallucinator,
    WildProposal,
    GMIGatekeeper
)


__all__ = [
    # Base adapter
    'DomainAdapter',
    'DomainEncoding',
    'AdapterRegistry',
    'get_adapter_registry',
    'register_adapter',
    
    # NPE Adapter
    'NPEAdapter',
    'GMIToNPEFeedback', 
    'CombinedRuntime',
    'NPEProposal',
    'CoherenceMetrics',
    
    # Stochastic Synthesizer
    'StochasticSynthesizer',
    'OperatorHallucinator', 
    'WildProposal',
    'GMIGatekeeper',
]
