"""
DEMO / RESEARCH SCRIPT
Not canonical runtime implementation - see core/embedder.py for canonical version.
This file demonstrates GMI embedding concepts.
"""

import numpy as np
import re

class GMI_Embedder:
    """
    Translates text into the continuous PhaseLoom state space.
    Words carry physical 'tension' coordinates.
    Goal state (Absolute Coherence) is [0.0, 0.0].
    """
    def __init__(self, dim=2):
        self.dim = dim
        
        # The Semantic Lexicon
        # Notice how certainty maps to low tension, and chaos maps to high tension.
        self.vocab = {
            # Low Tension (Geodesic / Logical states)
            "axiom": np.array([0.1, 0.1]),
            "proof": np.array([0.2, 0.2]),
            "logic": np.array([0.5, 0.5]),
            
            # Medium Tension (Exploratory / Imagined states)
            "hypothesis": np.array([2.0, 2.0]),
            "idea": np.array([2.5, 2.5]),
            "brainstorm": np.array([3.5, 3.5]),
            
            # High Tension (Incoherent / Costly states)
            "guess": np.array([5.0, 5.0]),
            "contradiction": np.array([6.5, 6.5]),
            "chaos": np.array([8.0, 8.0])
        }

    def embed(self, text: str) -> np.ndarray:
        """Converts a sentence into a physical coordinate vector."""
        # Fixed: Use re.sub instead of JavaScript-style replace with regex
        words = re.sub(r'[^\w\s]', '', text.lower()).split()
        
        vec = np.zeros(self.dim)
        match_count = 0
        
        for w in words:
            if w in self.vocab:
                vec += self.vocab[w]
                match_count += 1
                
        # If no recognized words, default to a high-tension "confusion" state
        if match_count == 0:
            return np.array([4.0, 4.0])
            
        # Return the semantic center of mass
        return vec / match_count

    def decode(self, x: np.ndarray) -> str:
        """Finds the closest semantic word to a given physical coordinate."""
        closest_word = "unknown"
        min_dist = float('inf')
        
        for word, vec in self.vocab.items():
            dist = np.linalg.norm(x - vec)
            if dist < min_dist:
                min_dist = dist
                closest_word = word
                
        return closest_word

# --- Quick Test ---
if __name__ == "__main__":
    embedder = GMI_Embedder()
    
    thought_1 = "Let's brainstorm a wild idea"
    coord_1 = embedder.embed(thought_1)
    
    thought_2 = "This is a rigorous logic proof"
    coord_2 = embedder.embed(thought_2)
    
    print(f"Thought 1: '{thought_1}' -> Physics: {coord_1} -> Tension V(x): {np.sum(coord_1**2):.2f}")
    print(f"Thought 2: '{thought_2}' -> Physics: {coord_2} -> Tension V(x): {np.sum(coord_2**2):.2f}")
