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

# Export commonly used classes
from gmos.sensory.sensory_connector import SensoryConnector, SensoryState, ProcessedPercept
from gmos.sensory.salience import SalienceScore
from gmos.sensory.manifold import SensoryState as ManifoldSensoryState

__all__ = [
    "manifold",
    "projection", 
    "salience",
    "sensory_connector",
    "anchors",
    # Exported classes
    "SensoryConnector",
    "SensoryState", 
    "ProcessedPercept",
    "SalienceScore",
    "ManifoldSensoryState",
]
