"""
GMI Task Environments.

This package provides task environments for benchmarking GMI cognitive capabilities:
- Simple navigation tasks
- Maze environments (key-door, multi-goal)
- Sensory discrimination tasks

Each environment follows a standard interface:
- reset() -> state
- step(action) -> (state, reward, done, info)
- render() -> visual representation (optional)
"""

from gmos.agents.gmi.environments.base import Environment, EnvironmentConfig
from gmos.agents.gmi.environments.maze import SimpleMaze, MazeConfig
from gmos.agents.gmi.environments.key_door import KeyDoorMaze, KeyDoorConfig

__all__ = [
    'Environment',
    'EnvironmentConfig', 
    'SimpleMaze',
    'MazeConfig',
    'KeyDoorMaze',
    'KeyDoorConfig',
]
