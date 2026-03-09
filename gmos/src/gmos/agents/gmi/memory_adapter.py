"""
Memory Adapter for GM-OS GMI Agent.

Canonical wrapper providing MemoryManifold interface for the GMI agent loops.

This adapter wraps gmos.memory components to provide the interface expected
by the evolution_loop and other GMI components that use:
- write_scar(x, penalty)
- write_reward(x, strength)
- read_curvature(x)
- step()
"""

import numpy as np
from typing import Optional, List, Tuple


class MemoryManifold:
    """
    The geometric memory of the GMI engine.
    
    Uses INVERSE SCARRING - rewards successful paths instead of just punishing failures.
    This aligns with biological learning (reinforcement) rather than pure punishment.
    
    - Scars: Curvature bumps at FAILED positions (makes them harder to revisit)
    - Rewards: Curvature dips at SUCCESSFUL positions (makes them cheaper to revisit)
    - Decay: Rewards fade over time to prevent getting stuck at previous hotspots
    
    This is a canonical implementation that wraps gmos.memory components.
    """
    
    def __init__(
        self, 
        lambda_c: float = 5.0, 
        lambda_r: float = 2.0, 
        reward_decay: float = 0.95
    ):
        """
        Initialize the MemoryManifold.
        
        Args:
            lambda_c: How severely a scar warps the space (penalty coefficient)
            lambda_r: How strongly rewards lower potential
            reward_decay: Decay factor per step
        """
        self.scars: List[Tuple[np.ndarray, float]] = []
        self.rewards: List[Tuple[np.ndarray, float, int]] = []
        self.lambda_c = lambda_c
        self.lambda_r = lambda_r
        self.reward_decay = reward_decay
        self.current_step = 0
        
        # Optional: Connect to canonical gmos memory components
        self._workspace_memory: Optional[object] = None
        self._archive_memory: Optional[object] = None
    
    def step(self) -> None:
        """
        Advance time step - rewards will decay.
        Call this after each cognitive cycle.
        """
        self.current_step += 1
    
    def write_scar(self, x: np.ndarray, penalty: float = 1.0) -> None:
        """
        Places a curvature BUMP at a rejected/failed coordinate.
        
        This makes failed positions more expensive to revisit, implementing
        a geometric memory of what doesn't work.
        
        Args:
            x: Coordinate array to scar
            penalty: Height of the curvature bump (default 1.0)
        """
        self.scars.append((np.array(x), penalty * self.lambda_c))
    
    def write_reward(self, x: np.ndarray, strength: float = 1.0) -> None:
        """
        Places a curvature DIP at a successful coordinate.
        
        This makes successful positions CHEAPER to revisit - inverse scarring!
        Includes timestamp for decay.
        
        Args:
            x: Coordinate array to reward
            strength: Strength of the reward (default 1.0)
        """
        self.rewards.append((np.array(x), strength * self.lambda_r, self.current_step))
    
    def read_curvature(self, x: np.ndarray) -> float:
        """
        Evaluates total curvature at a given position.
        
        - Scars create hills (high potential) - harder to revisit failed positions
        - Rewards create valleys (low potential) - cheaper to revisit successful positions
        - Rewards decay over time (fading memory)
        
        Args:
            x: Coordinate array to evaluate
            
        Returns:
            Curvature value at position x (positive = harder, negative = easier)
        """
        c_val = 0.0
        
        # Add scar contributions (positive = harder)
        for scar_x, height in self.scars:
            dist_sq = np.sum((x - scar_x) ** 2)
            c_val += height * np.exp(-dist_sq / 2.0)
        
        # Add reward contributions (negative = easier), with decay
        for reward_x, strength, step_created in self.rewards:
            # Calculate decay based on time since reward was created
            age = self.current_step - step_created
            decay_factor = self.reward_decay ** age
            effective_strength = strength * decay_factor
            
            dist_sq = np.sum((x - reward_x) ** 2)
            c_val -= effective_strength * np.exp(-dist_sq / 2.0)
        
        return c_val
    
    def get_scar_count(self) -> int:
        """Return the number of scars in memory."""
        return len(self.scars)
    
    def get_reward_count(self) -> int:
        """Return the number of rewards in memory."""
        return len(self.rewards)
    
    def clear(self) -> None:
        """Clear all scars and rewards."""
        self.scars.clear()
        self.rewards.clear()
        self.current_step = 0
    
    def __repr__(self) -> str:
        return (
            f"MemoryManifold(scars={len(self.scars)}, "
            f"rewards={len(self.rewards)}, step={self.current_step})"
        )


def create_memory_manifold(
    lambda_c: float = 5.0,
    lambda_r: float = 2.0,
    reward_decay: float = 0.95
) -> MemoryManifold:
    """
    Factory function to create a MemoryManifold.
    
    Args:
        lambda_c: Scar penalty coefficient
        lambda_r: Reward strength coefficient  
        reward_decay: Reward decay per step
        
    Returns:
        MemoryManifold instance
    """
    return MemoryManifold(
        lambda_c=lambda_c,
        lambda_r=lambda_r,
        reward_decay=reward_decay
    )


# Default instance
_default_memory: Optional[MemoryManifold] = None


def get_default_memory() -> MemoryManifold:
    """Get or create the default MemoryManifold instance."""
    global _default_memory
    if _default_memory is None:
        _default_memory = MemoryManifold()
    return _default_memory
