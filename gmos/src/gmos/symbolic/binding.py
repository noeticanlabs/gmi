"""
Binding for GM-OS Symbolic Layer.

Connects process state and symbolic state.

This module is the bridge between:
- continuous governed process state
- symbolic/glyph semantics

Without binding, the symbolic layer is decorative.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import numpy as np

from gmos.symbolic.glyph_space import (
    GlyphSpace,
    GlyphState,
    GlyphCoordinate,
    GlyphEmbedding,
    GlyphType,
    create_glyph_space
)


@dataclass
class BindingContext:
    """
    Context for state-symbol binding.
    
    Tracks what state elements are bound to which symbols.
    """
    # State to symbol bindings
    state_to_symbol: Dict[str, str] = field(default_factory=dict)
    
    # Symbol to state bindings
    symbol_to_state: Dict[str, str] = field(default_factory=dict)
    
    # Binding confidence
    binding_confidence: Dict[str, float] = field(default_factory=dict)
    
    # Last update timestamp
    last_update: float = 0.0
    
    def bind(
        self,
        state_key: str,
        symbol_id: str,
        confidence: float = 1.0
    ):
        """Create a binding between state and symbol."""
        self.state_to_symbol[state_key] = symbol_id
        self.symbol_to_state[symbol_id] = state_key
        self.binding_confidence[symbol_id] = confidence
    
    def unbind_symbol(self, symbol_id: str):
        """Remove a symbol binding."""
        if symbol_id in self.symbol_to_state:
            state_key = self.symbol_to_state.pop(symbol_id)
            self.state_to_symbol.pop(state_key, None)
            self.binding_confidence.pop(symbol_id, None)
    
    def get_symbol(self, state_key: str) -> Optional[str]:
        """Get symbol bound to state key."""
        return self.state_to_symbol.get(state_key)
    
    def get_state(self, symbol_id: str) -> Optional[str]:
        """Get state key bound to symbol."""
        return self.symbol_to_state.get(symbol_id)


def bind_symbol_to_state(
    symbol_id: str,
    state: Dict[str, Any],
    glyph_space: GlyphSpace,
    context: Optional[BindingContext] = None,
    confidence: float = 1.0
) -> Dict[str, Any]:
    """
    Bind symbolic structure to process state.
    
    This grounds symbols into the continuous state space.
    
    Args:
        symbol_id: The symbol to bind
        state: The process state dictionary
        glyph_space: The glyph space to use
        context: Optional binding context
        confidence: Binding confidence
        
    Returns:
        Binding result with grounded state
    """
    # Get glyph from space
    glyph = glyph_space.state.get_glyph(symbol_id)
    
    if glyph is None:
        return {
            "success": False,
            "error": f"Symbol {symbol_id} not found in glyph space",
        }
    
    # Extract state values to bind
    bound_values = {}
    
    # Bind coordinate to state
    coordinate = glyph.coordinate
    bound_values["glyph_x"] = coordinate.x
    bound_values["glyph_y"] = coordinate.y
    if coordinate.z is not None:
        bound_values["glyph_z"] = coordinate.z
    
    # Bind features to state
    if glyph.features is not None:
        features = glyph.features
        # Bind first few features
        for i, f in enumerate(features[:10]):
            bound_values[f"feature_{i}"] = float(f)
    
    # Bind type
    bound_values["glyph_type"] = coordinate.glyph_type.value
    
    # Bind confidence
    bound_values["binding_confidence"] = confidence * glyph.confidence
    
    # Update context if provided
    if context:
        context.bind(symbol_id, symbol_id, confidence)
    
    return {
        "success": True,
        "symbol_id": symbol_id,
        "bound_values": bound_values,
        "confidence": bound_values["binding_confidence"],
    }


def bind_state_to_symbol(
    state: Dict[str, Any],
    glyph_space: GlyphSpace,
    context: Optional[BindingContext] = None
) -> Dict[str, Any]:
    """
    Extract symbolic representation from process state.
    
    This extracts symbols from the continuous state space.
    
    Args:
        state: The process state dictionary
        glyph_space: The glyph space to use
        context: Optional binding context
        
    Returns:
        Extracted symbols and their positions
    """
    extracted = []
    
    # Try to match state values to glyph positions
    for glyph_id, glyph in glyph_space.state.glyphs.items():
        # Simple matching: check if state values are close to glyph coordinates
        score = 0.0
        
        # Check coordinate proximity
        if "x" in state and "y" in state:
            x_diff = abs(state.get("x", 0) - glyph.coordinate.x)
            y_diff = abs(state.get("y", 0) - glyph.coordinate.y)
            
            if x_diff < 0.5 and y_diff < 0.5:
                score = 1.0 - (x_diff + y_diff) / 2
        
        if score > 0.3:
            extracted.append({
                "symbol_id": glyph_id,
                "glyph_type": glyph.coordinate.glyph_type.value,
                "match_score": score,
                "coordinate": {
                    "x": glyph.coordinate.x,
                    "y": glyph.coordinate.y,
                    "z": glyph.coordinate.z,
                },
            })
    
    # Sort by score
    extracted = sorted(extracted, key=lambda x: x["match_score"], reverse=True)
    
    return {
        "extracted_symbols": extracted,
        "primary_symbol": extracted[0] if extracted else None,
        "symbol_count": len(extracted),
    }


def create_state_symbol_bridge(
    state_dim: int = 64,
    glyph_dim: int = 3,
    embedding_dim: int = 64
) -> tuple[GlyphSpace, BindingContext]:
    """
    Create a bridge between state and symbol spaces.
    
    Args:
        state_dim: Dimension of state space
        glyph_dim: Dimension of glyph coordinates
        embedding_dim: Dimension of embeddings
        
    Returns:
        Tuple of (glyph_space, binding_context)
    """
    space = create_glyph_space(dimension=glyph_dim, embedding_dim=embedding_dim)
    context = BindingContext()
    
    return space, context


# Integration with sensory manifold
def bind_sensory_to_symbolic(
    sensory_state: Any,
    glyph_space: GlyphSpace,
    context: Optional[BindingContext] = None
) -> Dict[str, Any]:
    """
    Bind sensory state to symbolic representation.
    
    Args:
        sensory_state: SensoryState from manifold
        glyph_space: Glyph space to use
        context: Optional binding context
        
    Returns:
        Symbolic bindings for sensory state
    """
    bindings = {}
    
    # Bind external perception
    if sensory_state.external:
        ext = sensory_state.external
        bindings["external"] = {
            "confidence": ext.confidence,
            "object_count": len(ext.objects),
            "event_count": len(ext.events),
            "source_tags": ext.source_tags,
        }
    
    # Bind internal state
    if sensory_state.internal:
        internal = sensory_state.internal
        bindings["internal"] = {
            "budget": internal.budget,
            "reserve": internal.reserve,
            "pressure": internal.pressure,
            "threat": internal.threat_level,
            "mode": internal.mode,
            "health": internal.health_score,
        }
        
        # Find matching symbols for budget/pressure
        if glyph_space.state.glyphs:
            budget_glyph = None
            pressure_glyph = None
            
            for gid, glyph in glyph_space.state.glyphs.items():
                if "budget" in gid.lower():
                    budget_glyph = glyph
                if "pressure" in gid.lower():
                    pressure_glyph = glyph
            
            if budget_glyph:
                bindings["internal"]["budget_symbol"] = budget_glyph.coordinate.to_vector()
            if pressure_glyph:
                bindings["internal"]["pressure_symbol"] = pressure_glyph.coordinate.to_vector()
    
    # Bind anchors
    if sensory_state.bundle.anchors:
        bindings["anchors"] = {
            "anchor_count": len(sensory_state.bundle.anchors),
            "confidence": sensory_state.bundle.get_confidence(),
        }
    
    return bindings
