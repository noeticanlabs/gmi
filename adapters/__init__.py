# NPE Adapter Package
# 
# This package provides bridges between NPE proposals and GMI verification.
#
# Main components:
# - npe_adapter: NPE → GMI adapter with feedback loop
# - stochastic_synthesizer: Wild imagination synthesizer (bypasses registry)

from .npe_adapter import (
    NPEAdapter,
    GMIToNPEFeedback,
    CombinedRuntime,
    NPEProposal,
    CoherenceMetrics
)

from .stochastic_synthesizer import (
    StochasticSynthesizer,
    OperatorHallucinator,
    WildProposal,
    GMIGatekeeper
)

__all__ = [
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
