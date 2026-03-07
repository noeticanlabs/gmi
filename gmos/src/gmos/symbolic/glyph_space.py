"""
Glyph Space for GM-OS Symbolic Layer.

Defines symbolic glyph coordinate container.

TODO: Implement:
- GlyphCoordinate type
- GlyphState container
- Glyph embeddings
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GlyphCoordinate:
    """Symbolic glyph coordinate."""
    x: float
    y: float
    z: Optional[float] = None
    glyph_type: str = "unknown"


@dataclass
class GlyphState:
    """Container for glyph coordinates."""
    coordinates: List[GlyphCoordinate] = None
    # TODO: Add more fields
