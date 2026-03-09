"""
GM-OS Sensory Layer.

Exports sensory processing components:
- manifold: Sensory manifold state (ExternalChart, InternalChart, SensoryState)
- projection: Projection functions for world/internal state
- salience: Salience computation (novelty, relevance, surprise)
- sensory_connector: Connector for integrating with hosted agent
- anchors: Anchor authority functional and conflict resolution (per spec §5.3)
"""

from gmos.sensory import manifold
from gmos.sensory import projection
from gmos.sensory import salience
from gmos.sensory import sensory_connector
from gmos.sensory import anchors

__all__ = [
    "manifold",
    "projection", 
    "salience",
    "sensory_connector",
    "anchors",
]
