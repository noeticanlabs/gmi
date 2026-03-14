"""
Key-Door Maze Environment for GMI.

Tests hierarchical planning: must acquire key before reaching door.
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
import numpy as np

from gmos.agents.gmi.environments.base import Environment, EnvironmentConfig, ActionSpace


@dataclass
class KeyDoorConfig(EnvironmentConfig):
    """Configuration for key-door maze environment."""
    name: str = "key_door_maze"
    width: int = 10
    height: int = 10
    start_pos: Tuple[int, int] = (1, 1)
    goal_pos: Tuple[int, int] = (8, 8)
    key_pos: Tuple[int, int] = (1, 8)
    door_pos: Tuple[int, int] = (5, 5)
    max_steps: int = 500
    
    # Rewards
    goal_reward: float = 20.0
    key_reward: float = 5.0
    door_open_reward: float = 2.0
    step_cost: float = -0.01
    collision_cost: float = -0.05
    wrong_order_penalty: float = -1.0
    
    # Observation
    obs_type: str = "spectral"


class KeyDoorMaze(Environment):
    """
    Key-door maze environment for testing hierarchical planning.
    
    Task: Reach goal by:
    1. First, pick up key (anywhere in maze)
    2. Then, go to door to unlock it
    3. Finally, reach goal
    
    The agent must learn the correct ordering - can't just
    go straight to the goal.
    """
    
    # Cell types
    EMPTY = 0
    WALL = 1
    GOAL = 2
    KEY = 3
    DOOR = 4
    START = 5
    
    def __init__(self, config: KeyDoorConfig):
        super().__init__(config)
        self.config = config
        
        # State
        self.grid = None
        self.agent_pos = None
        self.has_key = False
        self.door_open = False
        
        self._build_maze()
    
    def _build_maze(self):
        """Build the key-door maze - simple open layout."""
        w, h = self.config.width, self.config.height
        
        # Initialize grid
        self.grid = np.zeros((h, w), dtype=np.int8)
        
        # Walls around border only
        self.grid[0, :] = self.WALL
        self.grid[-1, :] = self.WALL
        self.grid[:, 0] = self.WALL
        self.grid[:, -1] = self.WALL
        
        # Place items (they'll be on empty cells)
        # Config uses (x, y) format, grid uses [y, x] indexing
        gx, gy = self.config.goal_pos
        kx, ky = self.config.key_pos
        dx, dy = self.config.door_pos
        
        self.grid[gy, gx] = self.GOAL
        self.grid[ky, kx] = self.KEY
        self.grid[dy, dx] = self.DOOR
    
    def reset(self) -> np.ndarray:
        """Reset to initial state."""
        self.agent_pos = list(self.config.start_pos)
        self.has_key = False
        self.door_open = False
        self._step_count = 0
        self._done = False
        self._total_reward = 0.0
        
        return self._get_observation()
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """Execute one step."""
        if self._done:
            raise RuntimeError("Episode done. Call reset().")
        
        # Parse action
        if len(action) == 1 or action.ndim == 0:
            action_idx = int(action.flat[0])
        else:
            dx, dy = action[0], action[1]
            if abs(dx) > abs(dy):
                action_idx = ActionSpace.RIGHT if dx > 0 else ActionSpace.LEFT
            else:
                action_idx = ActionSpace.DOWN if dy > 0 else ActionSpace.UP
        
        dx, dy = ActionSpace.get_movement(action_idx)
        
        # Try to move
        new_x = self.agent_pos[0] + dx
        new_y = self.agent_pos[1] + dy
        
        reward = self.config.step_cost
        info = {"action": action_idx, "has_key": self.has_key, "door_open": self.door_open}
        
        # Check what's at the new position
        if self._is_valid(new_x, new_y):
            cell = self.grid[new_y, new_x]
            
            # Handle door interaction - opens when adjacent with key
            if cell == self.DOOR:
                if self.has_key:
                    # Can open and pass through
                    if not self.door_open:
                        self.door_open = True
                        reward += self.config.door_open_reward
                        info["door_opened"] = True
                    self.agent_pos = [new_x, new_y]
                else:
                    # Can't pass without key
                    reward += self.config.collision_cost
                    info["blocked_at_door"] = True
            else:
                # Normal movement
                self.agent_pos = [new_x, new_y]
                
                # Check for key pickup
                if cell == self.KEY and not self.has_key:
                    self.has_key = True
                    reward += self.config.key_reward
                    info["key_picked_up"] = True
                    # Remove key from grid (mark as empty)
                    self.grid[new_y, new_x] = self.EMPTY
                
                # Check for goal
                if cell == self.GOAL:
                    if self.door_open:
                        reward += self.config.goal_reward
                        self._done = True
                        info["goal_reached"] = True
                    else:
                        # Can't reach goal without going through door
                        reward += self.config.wrong_order_penalty
                        info["goal_blocked"] = True
        else:
            reward += self.config.collision_cost
            info["collision"] = True
        
        # Check step limit
        self._step_count += 1
        if self._step_count >= self.config.max_steps:
            self._done = True
            info["max_steps"] = True
        
        self._total_reward += reward
        
        return self._get_observation(), reward, self._done, info
    
    def _is_valid(self, x: int, y: int) -> bool:
        """Check if position is valid."""
        if x < 0 or y < 0:
            return False
        if y >= self.grid.shape[0] or x >= self.grid.shape[1]:
            return False
        
        cell = self.grid[y, x]
        
        # Wall is always invalid
        if cell == self.WALL:
            return False
        
        # Door is valid if agent has key (will open when stepped on)
        if cell == self.DOOR:
            return self.has_key or self.door_open
        
        return True
    
    def _get_observation(self) -> np.ndarray:
        """Get spectral observation."""
        if self.config.obs_type == "spectral":
            return self._get_spectral_observation()
        else:
            return self._get_full_observation()
    
    def _get_spectral_observation(self) -> np.ndarray:
        """
        Spectral observation encoding:
        - Distance to key (if not collected)
        - Distance to door (if key collected)
        - Distance to goal (if door open)
        """
        ax, ay = self.agent_pos
        
        spectral = np.zeros(88, dtype=np.float32)
        
        # Encode distances to key, door, goal
        targets = []
        
        if not self.has_key:
            targets.append(self.config.key_pos)
        elif not self.door_open:
            targets.append(self.config.door_pos)
        else:
            targets.append(self.config.goal_pos)
        
        # Add secondary targets for context
        if not self.has_key:
            targets.append(self.config.door_pos)
            targets.append(self.config.goal_pos)
        
        for i, (tx, ty) in enumerate(targets):
            dist = np.sqrt((ax - tx)**2 + (ay - ty)**2)
            
            # Map distance to frequency band
            freq_band = int(np.clip(dist * 3, 0, 87))
            
            # Add spectral energy at appropriate band
            spectral[freq_band] += 2.0 if i == 0 else 1.0
            
            # Spread slightly for robustness
            if freq_band > 0:
                spectral[freq_band - 1] += 0.5 if i == 0 else 0.25
            if freq_band < 87:
                spectral[freq_band + 1] += 0.5 if i == 0 else 0.25
        
        # Encode state as additional features
        # 0-10: has_key, door_open, distance_to_key, distance_to_door, distance_to_goal
        state_features = np.zeros(10, dtype=np.float32)
        if not self.has_key:
            state_features[0] = 0
            state_features[2] = np.sqrt((ax - self.config.key_pos[0])**2 + 
                                        (ay - self.config.key_pos[1])**2) / 20.0
        else:
            state_features[0] = 1
        
        if self.door_open:
            state_features[1] = 1
        
        state_features[3] = np.sqrt((ax - self.config.door_pos[0])**2 + 
                                    (ay - self.config.door_pos[1])**2) / 20.0
        state_features[4] = np.sqrt((ax - self.config.goal_pos[0])**2 + 
                                    (ay - self.config.goal_pos[1])**2) / 20.0
        
        return np.concatenate([spectral, state_features])
    
    def _get_full_observation(self) -> np.ndarray:
        """Full grid observation."""
        h, w = self.grid.shape
        
        grid_norm = (self.grid == self.WALL).astype(float) * -1
        grid_norm = np.where(self.grid == self.GOAL, 1.0, grid_norm)
        
        # Key (if not picked up)
        if not self.has_key:
            ky, kx = self.config.key_pos
            grid_norm[ky, kx] = 0.5  # Key visible
        
        # Door (changes if open)
        dy, dx = self.config.door_pos
        if self.door_open:
            grid_norm[dy, dx] = 0.3  # Open door
        else:
            grid_norm[dy, dx] = -0.5  # Closed door
        
        # Agent
        agent_layer = np.zeros((h, w), dtype=np.float32)
        agent_layer[self.agent_pos[1], self.agent_pos[0]] = 1.0
        
        obs = np.stack([grid_norm, agent_layer], axis=-1)
        return obs.flatten()
    
    def render(self) -> Optional[np.ndarray]:
        """Render maze as RGB."""
        h, w = self.grid.shape
        scale = 20
        
        img = np.zeros((h * scale, w * scale, 3), dtype=np.uint8)
        
        colors = {
            self.EMPTY: (255, 255, 255),
            self.WALL: (50, 50, 50),
            self.GOAL: (0, 255, 0),
            self.KEY: (255, 215, 0),     # Gold
            self.DOOR: (139, 69, 19),     # Brown (closed), will show as green if open
            self.START: (0, 0, 255),
        }
        
        for y in range(h):
            for x in range(w):
                cell = self.grid[y, x]
                if cell == self.EMPTY:
                    if (x, y) == self.config.start_pos:
                        img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors[self.START]
                    else:
                        img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors[self.EMPTY]
                elif cell == self.KEY and not self.has_key:
                    img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors[self.KEY]
                elif cell == self.DOOR:
                    if self.door_open:
                        img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = (100, 255, 100)  # Light green
                    else:
                        img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors[self.DOOR]
                else:
                    img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors.get(cell, colors[self.EMPTY])
        
        # Agent
        ax, ay = self.agent_pos
        img[ay*scale:(ay+1)*scale, ax*scale:(ax+1)*scale] = (255, 0, 0)
        
        return img
    
    @property
    def agent_position(self) -> Tuple[int, int]:
        """Get current agent position."""
        return tuple(self.agent_pos)
    
    @property
    def state(self) -> Dict[str, Any]:
        """Get full state."""
        return {
            "grid": self.grid.copy(),
            "agent_pos": tuple(self.agent_pos),
            "has_key": self.has_key,
            "door_open": self.door_open,
            "key_pos": self.config.key_pos,
            "door_pos": self.config.door_pos,
            "goal_pos": self.config.goal_pos,
            "step_count": self._step_count,
        }


def create_key_door_maze(
    width: int = 10,
    height: int = 10,
    obs_type: str = "spectral",
) -> KeyDoorMaze:
    """Factory function."""
    config = KeyDoorConfig(
        width=width,
        height=height,
        obs_type=obs_type,
    )
    return KeyDoorMaze(config)
