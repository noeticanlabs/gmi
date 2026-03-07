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
        
        # The Semantic Lexicon - Extended vocabulary
        # Tension values range from 0 (coherent) to 10+ (incoherent)
        self.vocab = {
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
        
        # Tension thresholds for categorization
        self.tension_zones = {
            "coherent": (0.0, 1.0),
            "logical": (1.0, 2.5),
            "creative": (2.5, 4.0),
            "speculative": (4.0, 6.0),
            "conflicting": (6.0, 8.0),
            "incoherent": (8.0, 10.0)
        }
    
    def add_word(self, word: str, tension: float, quadrant: str = "both"):
        """
        Dynamically add a word to the vocabulary.
        
        Args:
            word: The word to add
            tension: Cognitive tension value (0=coherent, 10+=incoherent)
            quadrant: Which quadrant - "first", "second", "third", "fourth", or "both"
        """
        # Map tension to 2D coordinates
        if quadrant == "first":
            coords = np.array([tension, tension])
        elif quadrant == "second":
            coords = np.array([-tension, tension])
        elif quadrant == "third":
            coords = np.array([-tension, -tension])
        elif quadrant == "fourth":
            coords = np.array([tension, -tension])
        else:  # "both" - use diagonal
            coords = np.array([tension * 0.707, tension * 0.707])
        
        self.vocab[word.lower()] = coords
    
    def get_tension_zone(self, x: np.ndarray) -> str:
        """Return the tension zone category for a coordinate."""
        tension = np.linalg.norm(x)
        
        for zone, (low, high) in self.tension_zones.items():
            if low <= tension < high:
                return zone
        return "incoherent" if tension >= 8.0 else "deep_coherence"

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
