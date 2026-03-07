import numpy as np

class MemoryManifold:
    """
    The geometric memory of the GMI engine.
    Uses INVERSE SCARRING - rewards successful paths instead of just punishing failures.
    This aligns with biological learning (reinforcement) rather than pure punishment.
    
    - Scars: Curvature bumps at FAILED positions (makes them harder to revisit)
    - Rewards: Curvature dips at SUCCESSFUL positions (makes them cheaper to revisit)
    - Decay: Rewards fade over time to prevent getting stuck at previous hotspots
    """
    def __init__(self, lambda_c=5.0, lambda_r=2.0, reward_decay=0.95):
        self.scars = []        # List of tuples: (coordinate_array, penalty_height)
        self.rewards = []      # List of tuples: (coordinate_array, reward_strength, step_created)
        self.lambda_c = lambda_c  # How severely a scar warps the space (penalty)
        self.lambda_r = lambda_r  # How strongly rewards lower potential
        self.reward_decay = reward_decay  # Decay factor per step
        self.current_step = 0  # Track steps for decay

    def step(self):
        """Advance time step - rewards will decay"""
        self.current_step += 1

    def write_scar(self, x: np.ndarray, penalty=1.0):
        """Places a curvature BUMP at a rejected/failed coordinate."""
        self.scars.append((np.array(x), penalty))

    def write_reward(self, x: np.ndarray, strength=1.0):
        """
        Places a curvature DIP at a successful coordinate.
        This makes successful positions CHEAPER to revisit - inverse scarring!
        Includes timestamp for decay.
        """
        self.rewards.append((np.array(x), strength, self.current_step))

    def read_curvature(self, x: np.ndarray) -> float:
        """
        Evaluates total curvature: scars (positive) + rewards (negative).
        
        - Scars create hills (high potential) - harder to revisit failed positions
        - Rewards create valleys (low potential) - cheaper to revisit successful positions
        - Rewards decay over time (fading memory)
        """
        c_val = 0.0
        
        # Add scar contributions (positive = harder)
        for scar_x, height in self.scars:
            dist_sq = np.sum((x - scar_x)**2)
            c_val += height * np.exp(-dist_sq / 2.0)
        
        # Add reward contributions (negative = easier), with decay
        for reward_x, strength, step_created in self.rewards:
            # Calculate decay based on time since reward was created
            age = self.current_step - step_created
            decay_factor = self.reward_decay ** age
            effective_strength = strength * decay_factor
            
            dist_sq = np.sum((x - reward_x)**2)
            c_val -= effective_strength * np.exp(-dist_sq / 2.0)  # Negative!
            
        return self.lambda_c * c_val
    
    def clear(self):
        """Clear all scars and rewards (for testing)"""
        self.scars = []
        self.rewards = []
        self.current_step = 0
