"""
GM-OS Symbolic Layer.

Exports symbolic processing components:
- glyph_space: Glyph coordinate space (GlyphCoordinate, GlyphEmbedding, GlyphState)
- semantic_manifold: Semantic manifold with relation bundles
- binding: State-symbol binding
- symbolic_connector: Connector for integrating with hosted agent
"""

from gmos.symbolic import glyph_space
from gmos.symbolic import semantic_manifold
from gmos.symbolic import binding
from gmos.symbolic import symbolic_connector

__all__ = [
    "glyph_space",
    "semantic_manifold",
    "binding",
    "symbolic_connector",
]
