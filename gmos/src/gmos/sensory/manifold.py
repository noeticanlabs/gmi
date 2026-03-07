"""
Sensory Manifold for GM-OS.

Defines sensory manifold container type, holds fused external/internal/
semantic percept bundles.

TODO: Implement charts and bundles for:
- External manifold (physical perception)
- Semantic manifold (conceptual/symbolic)
- Internal manifold (interoception)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class SensoryState:
    """Container for fused sensory state."""
    external: Optional[Dict[str, Any]] = None
    semantic: Optional[Dict[str, Any]] = None
    internal: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0


# TODO: Implement manifold charts
# TODO: Implement bundle fusion
# TODO: Implement coordinate transforms
