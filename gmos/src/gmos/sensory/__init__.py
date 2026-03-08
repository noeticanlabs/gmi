"""
GM-OS Sensory Layer.

Exports sensory processing components:
- manifold: Sensory manifold state (ExternalChart, InternalChart, SensoryState)
- projection: Projection functions for world/internal state
- salience: Salience computation (novelty, relevance, surprise)
- sensory_connector: Connector for integrating with hosted agent
"""

from gmos.sensory import manifold
from gmos.sensory import projection
from gmos.sensory import salience
from gmos.sensory import sensory_connector

__all__ = [
    "manifold",
    "projection", 
    "salience",
    "sensory_connector",
]
