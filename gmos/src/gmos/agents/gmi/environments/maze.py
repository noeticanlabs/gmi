"""
Simple Maze Environment for GMI.

A basic grid-world maze environment for testing navigation and planning.
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Optional, List
import numpy as np

from gmos.agents.gmi.environments.base import Environment, EnvironmentConfig, ActionSpace


@dataclass
class MazeConfig(EnvironmentConfig):
    """Configuration for maze environment."""
    name: str = "simple_maze"
    width: int = 10
    height: int = 10
    start_pos: Tuple[int, int] = (1, 1)
    goal_pos: Tuple[int, int] = (8, 8)
    obstacle_prob: float = 0.2
    max_steps: int = 200
    
    # Observation options
    obs_type: str = "full"  # "full", "local", "spectral"
    local_radius: int = 3
    
    # Reward shaping
    goal_reward: float = 10.0
    step_cost: float = -0.01
    collision_cost: float = -0.1


class SimpleMaze(Environment):
    """
    Simple grid-world maze for testing GMI navigation and planning.
    
    The maze provides:
    - A grid with obstacles
    - A start position and goal position
    - Sparse reward (goal only) + shaping
    - Configurable observation types
    """
    
    # Cell types
    EMPTY = 0
    WALL = 1
    GOAL = 2
    START = 3
    
    def __init__(self, config: MazeConfig):
        super().__init__(config)
        self.config = config
        
        # Grid state
        self.grid = None
        self.agent_pos = None
        self.goal_pos = config.goal_pos
        
        # Build the maze
        self._build_maze()
    
    def _build_maze(self):
        """Generate the maze grid."""
        w, h = self.config.width, self.config.height
        
        # Initialize with empty cells
        self.grid = np.zeros((h, w), dtype=np.int8)
        
        # Add walls around border
        self.grid[0, :] = self.WALL
        self.grid[-1, :] = self.WALL
        self.grid[:, 0] = self.WALL
        self.grid[:, -1] = self.WALL
        
        # Add random obstacles (excluding start and goal)
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if (x, y) != self.config.start_pos and (x, y) != self.goal_pos:
                    if np.random.random() < self.config.obstacle_prob:
                        self.grid[y, x] = self.WALL
        
        # Place goal
        gy, gx = self.goal_pos
        self.grid[gy, gx] = self.GOAL
    
    def reset(self) -> np.ndarray:
        """Reset environment to initial state."""
        self.agent_pos = list(self.config.start_pos)
        self._step_count = 0
        self._done = False
        self._total_reward = 0.0
        
        return self._get_observation()
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one step in the maze.
        
        Args:
            action: Action vector. Can be:
                - Discrete: action[0] = action index
                - Continuous: [dx, dy] normalized
            
        Returns:
            obs: Observation
            reward: Scalar reward
            done: Episode finished
            info: Debug info
        """
        if self._done:
            raise RuntimeError("Episode already done. Call reset().")
        
        # Parse action
        if len(action) == 1 or action.ndim == 0:
            action_idx = int(action.flat[0])
        else:
            # Continuous action: [dx, dy] -> discretize
            dx, dy = action[0], action[1]
            if abs(dx) > abs(dy):
                action_idx = ActionSpace.RIGHT if dx > 0 else ActionSpace.LEFT
            else:
                action_idx = ActionSpace.DOWN if dy > 0 else ActionSpace.UP
        
        # Get movement
        dx, dy = ActionSpace.get_movement(action_idx)
        
        # Compute new position
        new_x = self.agent_pos[0] + dx
        new_y = self.agent_pos[1] + dy
        
        # Check collision
        reward = self.config.step_cost
        info = {"action": action_idx, "collision": False}
        
        if self._is_valid(new_x, new_y):
            self.agent_pos = [new_x, new_y]
        else:
            reward += self.config.collision_cost
            info["collision"] = True
        
        # Check goal
        if tuple(self.agent_pos) == self.goal_pos:
            reward += self.config.goal_reward
            self._done = True
            info["goal_reached"] = True
        
        # Check max steps
        self._step_count += 1
        if self._step_count >= self.config.max_steps:
            self._done = True
            info["max_steps"] = True
        
        self._total_reward += reward
        
        obs = self._get_observation()
        return obs, reward, self._done, info
    
    def _is_valid(self, x: int, y: int) -> bool:
        """Check if position is valid (in bounds, not a wall)."""
        if x < 0 or y < 0:
            return False
        if y >= self.grid.shape[0] or x >= self.grid.shape[1]:
            return False
        return self.grid[y, x] != self.WALL
    
    def _get_observation(self) -> np.ndarray:
        """Get observation based on config."""
        if self.config.obs_type == "full":
            return self._get_full_observation()
        elif self.config.obs_type == "local":
            return self._get_local_observation()
        elif self.config.obs_type == "spectral":
            return self._get_spectral_observation()
        else:
            return self._get_full_observation()
    
    def _get_full_observation(self) -> np.ndarray:
        """Full grid observation flattened."""
        # Include agent position, goal position, and grid
        h, w = self.grid.shape
        
        # Normalize grid: -1 for walls, 0 for empty, 1 for goal
        grid_norm = (self.grid == self.WALL).astype(float) * -1
        grid_norm = np.where(self.grid == self.GOAL, 1.0, grid_norm)
        
        # Agent position (one-hot or coordinates)
        agent_layer = np.zeros((h, w), dtype=np.float32)
        agent_layer[self.agent_pos[1], self.agent_pos[0]] = 1.0
        
        # Stack and flatten
        obs = np.stack([grid_norm, agent_layer], axis=-1)
        return obs.flatten()
    
    def _get_local_observation(self) -> np.ndarray:
        """Local observation around agent."""
        r = self.config.local_radius
        h, w = self.grid.shape
        ax, ay = self.agent_pos
        
        # Extract local region with padding
        local = np.zeros((2*r+1, 2*r+1, 2), dtype=np.float32)
        
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx, ny = ax + dx, ay + dy
                if 0 <= nx < w and 0 <= ny < h:
                    local[dy+r, dx+r, 0] = -1 if self.grid[ny, nx] == self.WALL else 0
                    local[dy+r, dx+r, 0] = 1 if self.grid[ny, nx] == self.GOAL else local[dy+r, dx+r, 0]
                    local[dy+r, dx+r, 1] = 1 if (dx == 0 and dy == 0) else 0
        
        return local.flatten()
    
    def _get_spectral_observation(self) -> np.ndarray:
        """
        Spectral observation for GMI's resonant field.
        
        Creates a spectral signature based on:
        - Distance to goal (frequency based on distance)
        - Local obstacles (filter certain frequencies)
        """
        ax, ay = self.agent_pos
        gx, gy = self.goal_pos
        
        # Distance to goal
        dist = np.sqrt((ax - gx)**2 + (ay - gy)**2)
        
        # Create spectral signature across 88 octaves
        spectral = np.zeros(88, dtype=np.float32)
        
        for n in range(88):
            # Frequency response based on distance
            freq = 0.1 * 2**(n / 10)
            response = np.exp(-((dist - freq)**2) / 10)
            spectral[n] = response
        
        # Modulate by local obstacles
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                nx, ny = ax + dx, ay + dy
                if 0 <= nx < self.grid.shape[1] and 0 <= ny < self.grid.shape[0]:
                    if self.grid[ny, nx] == self.WALL:
                        # Block some frequencies
                        block_freq = np.sqrt(dx**2 + dy**2)
                        for n in range(88):
                            freq = 0.1 * 2**(n / 10)
                            if abs(freq - block_freq) < 2:
                                spectral[n] *= 0.5
        
        return spectral
    
    def render(self) -> Optional[np.ndarray]:
        """Render the maze as RGB."""
        h, w = self.grid.shape
        scale = 20
        
        img = np.zeros((h * scale, w * scale, 3), dtype=np.uint8)
        
        # Colors
        colors = {
            self.EMPTY: (255, 255, 255),  # White
            self.WALL: (50, 50, 50),       # Dark gray
            self.GOAL: (0, 255, 0),        # Green
            self.START: (0, 0, 255),       # Blue
        }
        
        for y in range(h):
            for x in range(w):
                cell = self.grid[y, x]
                if cell == self.EMPTY:
                    # Check if start
                    if (x, y) == self.config.start_pos:
                        img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors[self.START]
                    else:
                        img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors[self.EMPTY]
                else:
                    img[y*scale:(y+1)*scale, x*scale:(x+1)*scale] = colors.get(cell, colors[self.EMPTY])
        
        # Draw agent
        ax, ay = self.agent_pos
        img[ay*scale:(ay+1)*scale, ax*scale:(ax+1)*scale] = (255, 0, 0)  # Red
        
        return img
    
    @property
    def agent_position(self) -> Tuple[int, int]:
        """Get current agent position."""
        return tuple(self.agent_pos)
    
    @property
    def state(self) -> Dict[str, Any]:
        """Get full environment state."""
        return {
            "grid": self.grid.copy(),
            "agent_pos": tuple(self.agent_pos),
            "goal_pos": self.goal_pos,
            "step_count": self._step_count,
            "done": self._done,
        }


def create_maze(
    width: int = 10,
    height: int = 10,
    start: Tuple[int, int] = (1, 1),
    goal: Tuple[int, int] = (8, 8),
    obstacle_prob: float = 0.2,
    obs_type: str = "spectral",
) -> SimpleMaze:
    """Factory function to create a maze."""
    config = MazeConfig(
        width=width,
        height=height,
        start_pos=start,
        goal_pos=goal,
        obstacle_prob=obstacle_prob,
        obs_type=obs_type,
    )
    return SimpleMaze(config)
