"""
Glyph Embedder for GM-OS Symbolic Layer.

Canonical replacement for legacy GMI_Embedder from core.embedder.

This module provides text-to-vector embedding using the glyph space,
supporting the GMI agent loops with semantic exploration capabilities.
"""

import numpy as np
import re
from typing import Dict, Optional
from gmos.symbolic.glyph_space import GlyphCoordinate, GlyphType


class GlyphEmbedder:
    """
    Translates text into the continuous GMI state space using glyph coordinates.
    
    Words carry cognitive 'tension' coordinates - low values near origin
    represent coherent states, high values represent incoherent states.
    
    This is the canonical replacement for the legacy GMI_Embedder.
    """
    
    def __init__(self, dim: int = 2):
        """
        Initialize the embedder.
        
        Args:
            dim: Dimension of embedding vectors (default 2)
        """
        self.dim = dim
        
        # The Semantic Lexicon - vocabulary with tension coordinates
        # Maps words to cognitive tension values (0=coherent, 10+=incoherent)
        self._vocab: Dict[str, np.ndarray] = {
            # Very Low Tension (0-0.5): Fundamental truths
            "truth": np.array([0.0, 0.0]),
            "axiom": np.array([0.1, 0.1]),
            "proof": np.array([0.2, 0.2]),
            "theorem": np.array([0.2, 0.2]),
            "fact": np.array([0.3, 0.3]),
            
            # Low Tension (0.5-1.0): Logical reasoning
            "logic": np.array([0.5, 0.5]),
            "reason": np.array([0.6, 0.6]),
            "deduction": np.array([0.7, 0.7]),
            "analysis": np.array([0.8, 0.8]),
            
            # Medium-Low Tension (1.0-2.0): Structured thinking
            "model": np.array([1.0, 1.0]),
            "theory": np.array([1.2, 1.2]),
            "hypothesis": np.array([2.0, 2.0]),
            
            # Medium Tension (2.0-4.0): Creative exploration
            "idea": np.array([2.5, 2.5]),
            "concept": np.array([2.8, 2.8]),
            "brainstorm": np.array([3.5, 3.5]),
            "creative": np.array([3.2, 3.2]),
            "imagine": np.array([3.8, 3.8]),
            
            # Medium-High Tension (4.0-6.0): Uncertain speculation
            "speculate": np.array([4.0, 4.0]),
            "guess": np.array([5.0, 5.0]),
            "theory_craft": np.array([4.5, 4.5]),
            
            # High Tension (6.0-8.0): Cognitive dissonance
            "paradox": np.array([6.0, 6.0]),
            "contradiction": np.array([6.5, 6.5]),
            "confusion": np.array([7.0, 7.0]),
            
            # Very High Tension (8.0+): Complete incoherence
            "chaos": np.array([8.0, 8.0]),
            "nonsense": np.array([8.5, 8.5]),
            "absurd": np.array([9.0, 9.0]),
        }
        
        # Extend vocabulary based on dimension
        if dim > 2:
            self._extend_vocab_to_dim(dim)
        
        # Tension thresholds for categorization
        self.tension_zones = {
            "coherent": (0.0, 1.0),
            "logical": (1.0, 2.5),
            "creative": (2.5, 4.0),
            "speculative": (4.0, 6.0),
            "conflicting": (6.0, 8.0),
            "incoherent": (8.0, 10.0)
        }
    
    def _extend_vocab_to_dim(self, dim: int) -> None:
        """Extend vocabulary entries to match target dimension."""
        for word, vec in list(self._vocab.items()):
            if len(vec) < dim:
                # Pad with zeros to match dimension
                self._vocab[word] = np.pad(vec, (0, dim - len(vec)), mode='constant')
    
    @property
    def vocab(self) -> Dict[str, np.ndarray]:
        """Return the vocabulary dictionary."""
        return self._vocab
    
    def add_word(self, word: str, tension: float, quadrant: str = "both") -> None:
        """
        Dynamically add a word to the vocabulary.
        
        Args:
            word: The word to add
            tension: Cognitive tension value (0=coherent, 10+=incoherent)
            quadrant: Which quadrant - "first", "second", "third", "fourth", or "both"
        """
        # Map tension to coordinates based on quadrant
        if quadrant == "first":
            coords = np.array([tension] * self.dim)
        elif quadrant == "second":
            coords = np.array([-tension if i % 2 == 0 else tension for i in range(self.dim)])
        elif quadrant == "third":
            coords = np.array([-tension] * self.dim)
        elif quadrant == "fourth":
            coords = np.array([tension if i % 2 == 0 else -tension for i in range(self.dim)])
        else:  # "both" - use diagonal
            diag_val = tension * 0.707
            coords = np.array([diag_val] * self.dim)
        
        self._vocab[word.lower()] = coords
    
    def get_tension_zone(self, x: np.ndarray) -> str:
        """
        Return the tension zone category for a coordinate.
        
        Args:
            x: Coordinate vector
            
        Returns:
            Zone name string
        """
        tension = np.linalg.norm(x)
        
        for zone, (low, high) in self.tension_zones.items():
            if low <= tension < high:
                return zone
        return "incoherent" if tension >= 8.0 else "deep_coherence"
    
    def embed(self, text: str) -> np.ndarray:
        """
        Converts a text string into a coordinate vector.
        
        Args:
            text: Input text string
            
        Returns:
            Coordinate vector in the cognitive tension space
        """
        # Tokenize: lowercase and remove punctuation
        words = re.sub(r'[^\w\s]', '', text.lower()).split()
        
        vec = np.zeros(self.dim)
        match_count = 0
        
        for w in words:
            if w in self._vocab:
                vec += self._vocab[w]
                match_count += 1
        
        # If no recognized words, default to medium-tension "confusion" state
        if match_count == 0:
            default = np.array([4.0, 4.0])
            if self.dim > 2:
                default = np.pad(default, (0, self.dim - 2), mode='constant')
            return default
        
        # Return the semantic center of mass
        return vec / match_count
    
    def decode(self, x: np.ndarray) -> str:
        """
        Finds the closest semantic word to a given coordinate.
        
        Args:
            x: Coordinate vector
            
        Returns:
            Closest vocabulary word
        """
        closest_word = "unknown"
        min_dist = float('inf')
        
        for word, vec in self._vocab.items():
            # Handle dimension mismatch
            vec_padded = vec
            if len(vec) < self.dim:
                vec_padded = np.pad(vec, (0, self.dim - len(vec)), mode='constant')
            
            dist = np.linalg.norm(x - vec_padded)
            if dist < min_dist:
                min_dist = dist
                closest_word = word
                
        return closest_word
    
    def to_glyph_coordinate(self, x: np.ndarray, glyph_type: GlyphType = GlyphType.CONCEPT) -> GlyphCoordinate:
        """
        Convert embedding vector to GlyphCoordinate.
        
        Args:
            x: Embedding vector
            glyph_type: Type of glyph to create
            
        Returns:
            GlyphCoordinate object
        """
        if len(x) >= 3:
            return GlyphCoordinate(x=x[0], y=x[1], z=x[2], glyph_type=glyph_type)
        return GlyphCoordinate(x=x[0], y=x[1] if len(x) > 1 else 0.0, glyph_type=glyph_type)
    
    def from_glyph_coordinate(self, coord: GlyphCoordinate) -> np.ndarray:
        """
        Convert GlyphCoordinate to embedding vector.
        
        Args:
            coord: GlyphCoordinate object
            
        Returns:
            Embedding vector
        """
        return np.array(coord.to_vector())


# Factory function for compatibility with legacy code
def create_embedder(dim: int = 2) -> GlyphEmbedder:
    """
    Create a GlyphEmbedder instance.
    
    Args:
        dim: Embedding dimension
        
    Returns:
        GlyphEmbedder instance
    """
    return GlyphEmbedder(dim=dim)


# Default embedder instance for convenience
_default_embedder: Optional[GlyphEmbedder] = None


def get_default_embedder() -> GlyphEmbedder:
    """Get or create the default embedder instance."""
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = GlyphEmbedder()
    return _default_embedder


# Quick test
if __name__ == "__main__":
    embedder = GlyphEmbedder()
    
    thought_1 = "Let's brainstorm a wild idea"
    coord_1 = embedder.embed(thought_1)
    
    thought_2 = "This is a rigorous logic proof"
    coord_2 = embedder.embed(thought_2)
    
    print(f"Thought 1: '{thought_1}' -> {coord_1} -> Tension V(x): {np.sum(coord_1**2):.2f}")
    print(f"Thought 2: '{thought_2}' -> {coord_2} -> Tension V(x): {np.sum(coord_2**2):.2f}")
    
    # Test glyph coordinate conversion
    glyph = embedder.to_glyph_coordinate(coord_1)
    print(f"Converted to GlyphCoordinate: {glyph}")
