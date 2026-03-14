"""
Base Environment Interface for GMI Tasks.

Defines the standard interface all GMI environments must follow.
"""

from dataclasses import dataclass
from typing import Any, Dict, Tuple, Optional
import numpy as np


@dataclass
class EnvironmentConfig:
    """Configuration for a task environment."""
    name: str = "base_env"
    max_steps: int = 1000
    obs_dim: int = 64
    action_dim: int = 4
    reward_scale: float = 1.0
    
    # Rendering options
    render_mode: Optional[str] = None  # 'human', 'rgb_array', None


class Environment:
    """
    Base class for all GMI task environments.
    
    All environments must implement:
    - reset(): Initialize/reset environment
    - step(action): Execute action, return (obs, reward, done, info)
    - render(): Visualize current state (optional)
    
    The observation should be compatible with GMI's sensory processing:
    - Returns numpy array of shape (obs_dim,) or compatible with eye operator
    - Contains enough information to distinguish states
    """
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self._step_count = 0
        self._done = False
        self._total_reward = 0.0
    
    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observation as numpy array
        """
        raise NotImplementedError("Subclasses must implement reset()")
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one environment step.
        
        Args:
            action: Action vector (e.g., [dx, dy] or one-hot for directions)
        
        Returns:
            obs: Observation after action
            reward: Scalar reward
            done: Whether episode is finished
            info: Additional debug info
        """
        raise NotImplementedError("Subclasses must implement step()")
    
    def render(self) -> Optional[np.ndarray]:
        """
        Render the current state.
        
        Returns:
            RGB array if render_mode is 'rgb_array', None otherwise
        """
        return None
    
    @property
    def observation_space(self) -> Tuple[int, ...]:
        """Return observation space shape."""
        return (self.config.obs_dim,)
    
    @property
    def action_space(self) -> Tuple[int, ...]:
        """Return action space shape."""
        return (self.config.action_dim,)
    
    @property
    def is_done(self) -> bool:
        """Check if episode is finished."""
        return self._done
    
    @property
    def step_count(self) -> int:
        """Current step count in episode."""
        return self._step_count
    
    @property
    def total_reward(self) -> float:
        """Cumulative reward in current episode."""
        return self._total_reward
    
    def close(self):
        """Clean up environment resources."""
        pass
    
    def seed(self, seed: int):
        """Set random seed for reproducibility."""
        np.random.seed(seed)


class ActionSpace:
    """
    Discretized action space for navigation tasks.
    
    Provides common navigation actions:
    - Move: Up, Down, Left, Right
    - Interact: Pick up, Use, Open
    - Wait: No operation
    """
    
    # Action indices
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    PICKUP = 4
    USE = 5
    WAIT = 6
    
    NUM_ACTIONS = 7
    
    # Delta movements for each action
    MOVEMENTS = {
        UP: (0, -1),
        DOWN: (0, 1),
        LEFT: (-1, 0),
        RIGHT: (1, 0),
        PICKUP: (0, 0),
        USE: (0, 0),
        WAIT: (0, 0),
    }
    
    @classmethod
    def get_movement(cls, action: int) -> Tuple[int, int]:
        """Get (dx, dy) for an action."""
        return cls.MOVEMENTS.get(action, (0, 0))
    
    @classmethod
    def is_move_action(cls, action: int) -> bool:
        """Check if action is a movement."""
        return action in [cls.UP, cls.DOWN, cls.LEFT, cls.RIGHT]
    
    @classmethod
    def is_interact_action(cls, action: int) -> bool:
        """Check if action is an interaction."""
        return action in [cls.PICKUP, cls.USE]
    
    @classmethod
    def num_actions(cls) -> int:
        """Total number of actions."""
        return cls.NUM_ACTIONS
