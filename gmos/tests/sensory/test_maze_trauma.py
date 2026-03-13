"""
Enhanced Maze Test with Trauma Memory

This test compares the upgraded GMI (with trauma/curvature memory)
against the basic GMI in a key-door maze.

The key-door maze requires:
1. Finding the key first
2. Then going through the door
3. Finally reaching the goal

The trauma system should help the organism:
- Remember walls it bumped into
- Learn to avoid dead ends
- Remember which paths led to damage vs reward
"""

import numpy as np
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

from gmos.sensory import (
    CurvatureField,
    TraumaMemory,
    TraumaSeverity,
    ObservationCostLaw,
    CostCoefficients,
)


# =============================================================================
# MAZE DEFINITIONS
# =============================================================================

class CellType(Enum):
    EMPTY = 0
    WALL = 1
    GOAL = 2
    START = 3
    KEY = 4
    DOOR = 5
    POISON = 6  # NEW: Harmful cells


# Key-door maze (requires key before door)
KEY_DOOR_MAZE = [
    [3, 0, 1, 0, 0, 0, 1, 4],
    [1, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 1, 5, 1, 1, 1, 0],
    [0, 1, 2, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
]


# Maze with poison (damages organism)
POISON_MAZE = [
    [3, 0, 1, 6, 0, 0, 1, 4],
    [1, 0, 1, 6, 1, 0, 1, 0],
    [0, 0, 0, 6, 1, 0, 0, 0],
    [0, 1, 1, 5, 1, 1, 1, 0],
    [0, 1, 2, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 6, 6, 6, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
]


# =============================================================================
# ENHANCED GMI WITH TRAUMA
# =============================================================================

@dataclass
class EnhancedGMIState:
    """Enhanced GMI state with trauma memory."""
    position: Tuple[int, int]
    budget: float
    health: float = 1.0
    has_key: bool = False
    inventory: List[str] = field(default_factory=list)
    tension: float = 0.0


class EnhancedMazeGMI:
    """
    Enhanced GMI that uses trauma memory to learn from failures.
    
    When it hits a wall or poison, it creates a curvature scar
    that repels future attempts to go that direction.
    """
    
    def __init__(
        self,
        maze: List[List[int]],
        start_pos: Tuple[int, int],
        goal_pos: Tuple[int, int],
        initial_budget: float = 100.0,
        has_key_door: bool = False,
        has_poison: bool = False,
        trauma_memory: Optional[TraumaMemory] = None,
    ):
        self.maze = maze
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.height = len(maze)
        self.width = len(maze[0]) if maze else 0
        self.has_key_door = has_key_door
        self.has_poison = has_poison
        
        # Find key position if it exists
        self.key_pos = None
        if has_key_door:
            for y, row in enumerate(maze):
                for x, cell in enumerate(row):
                    if cell == CellType.KEY.value:
                        self.key_pos = (x, y)
                        break
        
        # State
        self.state = EnhancedGMIState(
            position=start_pos,
            budget=initial_budget,
            health=1.0,
        )
        
        # Trauma memory for learning
        if trauma_memory is not None:
            self.trauma = trauma_memory
        else:
            curvature = CurvatureField(
                dimensions=2,
                resolution=50,
                bounds=(0.0, float(max(self.width, self.height))),
            )
            self.trauma = TraumaMemory(
                curvature_field=curvature,
                default_scar_spread=0.5,
            )
        
        # Movement cost
        self.move_cost = 1.0
        self.wall_damage = 0.3
        self.poison_damage = 0.5
        self.goal_reward = 10.0
        
        # History
        self.path: List[Tuple[int, int]] = [start_pos]
        self.budget_spent = 0.0
        self.walls_hit = 0
        self.poison_hits = 0
    
    def _pos_to_semantic(self, pos: Tuple[int, int]) -> float:
        """Convert position to semantic coordinate for curvature."""
        x, y = pos
        # Use Manhattan distance from origin as semantic coordinate
        return float(x + y)
    
    def _get_cell(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get cell type at position."""
        x, y = pos
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.maze[y][x]
        return None
    
    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """Get valid moves from current position."""
        x, y = self.state.position
        moves = []
        
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            cell = self._get_cell((nx, ny))
            
            if cell is None:
                continue
            
            # Wall - can't move
            if cell == CellType.WALL.value:
                continue
            
            # Door - need key
            if cell == CellType.DOOR.value and not self.state.has_key:
                continue
            
            moves.append((nx, ny))
        
        return moves
    
    def _check_avoidance(self, pos: Tuple[int, int]) -> bool:
        """Check if trauma memory says to avoid this position."""
        semantic = self._pos_to_semantic(pos)
        decision = self.trauma.should_avoid(
            action="MOVE",
            semantic_position=semantic,
        )
        return decision.should_avoid
    
    def step(self) -> Dict[str, Any]:
        """
        Take one step in the maze.
        
        Returns info about what happened.
        """
        x, y = self.state.position
        info = {
            "action": "none",
            "success": False,
            "new_pos": (x, y),
            "damage": 0.0,
            "reward": 0.0,
            "event": "none",
        }
        
        # Check if at goal
        if (x, y) == self.goal_pos:
            info["event"] = "goal"
            info["reward"] = self.goal_reward
            self.state.budget += self.goal_reward
            return info
        
        # Get valid moves
        valid_moves = self.get_valid_moves()
        
        if not valid_moves:
            info["event"] = "trapped"
            return info
        
        # Filter out moves that trauma says to avoid
        moves_to_consider = []
        for move in valid_moves:
            if not self._check_avoidance(move):
                moves_to_consider.append(move)
        
        # If all moves are avoided, we have to try anyway
        if not moves_to_consider:
            moves_to_consider = valid_moves
        
        # Choose move: prefer moves toward key or goal (heuristic)
        best_move = None
        best_score = -float('inf')
        
        for move in moves_to_consider:
            score = 0.0
            mx, my = move
            
            # Check what's at this move
            cell = self._get_cell(move)
            
            # High score for goal
            if cell == CellType.GOAL.value:
                score += 100.0
            
            # Medium score for key
            elif cell == CellType.KEY.value:
                score += 50.0
            
            # Small bonus for moving closer to goal (if we have key)
            elif self.state.has_key and self.goal_pos:
                gx, gy = self.goal_pos
                score += 10.0 - (abs(mx - gx) + abs(my - gy))  # Closer = higher
            
            # Small bonus for moving closer to key (if we don't have it)
            elif not self.state.has_key and self.key_pos:
                kx, ky = self.key_pos
                score += 5.0 - (abs(mx - kx) + abs(my - ky)) * 0.5
            
            # Random noise to avoid getting stuck
            score += random.random() * 2.0
            
            if score > best_score:
                best_score = score
                best_move = move
        
        next_pos = best_move if best_move else random.choice(moves_to_consider)
        
        # Check what we moved into
        cell = self._get_cell(next_pos)
        
        # Calculate cost
        cost = self.move_cost
        self.state.budget -= cost
        self.budget_spent += cost
        
        # Check for special cells
        if cell == CellType.KEY.value:
            self.state.has_key = True
            self.state.inventory.append("key")
            info["reward"] = 2.0
            self.state.budget += 2.0
            info["event"] = "got_key"
        
        elif cell == CellType.POISON.value:
            self.state.health -= self.poison_damage
            info["damage"] = self.poison_damage
            info["event"] = "poison"
            
            # Create trauma scar!
            semantic = self._pos_to_semantic(next_pos)
            self.trauma.process_failure(
                action="MOVE",
                damage=self.poison_damage,
                semantic_position=semantic,
            )
            self.poison_hits += 1
        
        elif cell == CellType.WALL.value:
            # This shouldn't happen with valid_moves filter, but just in case
            self.walls_hit += 1
        
        # Update position
        self.state.position = next_pos
        self.path.append(next_pos)
        info["new_pos"] = next_pos
        info["success"] = True
        
        return info
    
    def run(self, max_steps: int = 100) -> Dict[str, Any]:
        """Run the maze until goal or max steps."""
        for step in range(max_steps):
            info = self.step()
            
            if info["event"] == "goal":
                return {
                    "success": True,
                    "steps": step + 1,
                    "path": self.path.copy(),
                    "budget_spent": self.budget_spent,
                    "walls_hit": self.walls_hit,
                    "poison_hits": self.poison_hits,
                    "final_health": self.state.health,
                    "got_key": self.state.has_key,
                }
            
            if info["event"] == "trapped":
                return {
                    "success": False,
                    "steps": step + 1,
                    "path": self.path.copy(),
                    "budget_spent": self.budget_spent,
                    "walls_hit": self.walls_hit,
                    "poison_hits": self.poison_hits,
                    "final_health": self.state.health,
                    "got_key": self.state.has_key,
                    "reason": "trapped",
                }
            
            # Check if dead
            if self.state.health <= 0:
                return {
                    "success": False,
                    "steps": step + 1,
                    "path": self.path.copy(),
                    "budget_spent": self.budget_spent,
                    "walls_hit": self.walls_hit,
                    "poison_hits": self.poison_hits,
                    "final_health": 0.0,
                    "got_key": self.state.has_key,
                    "reason": "died",
                }
        
        return {
            "success": False,
            "steps": max_steps,
            "path": self.path.copy(),
            "budget_spent": self.budget_spent,
            "walls_hit": self.walls_hit,
            "poison_hits": self.poison_hits,
            "final_health": self.state.health,
            "got_key": self.state.has_key,
            "reason": "max_steps",
        }


# =============================================================================
# COMPARISON TEST
# =============================================================================

def run_comparison():
    """Compare GMI with and without trauma memory."""
    
    print("=" * 70)
    print("KEY-DOOR MAZE TEST: Basic GMI vs Trauma-Enhanced GMI")
    print("=" * 70)
    
    # Find positions
    start_pos = None
    goal_pos = None
    key_pos = None
    
    for y, row in enumerate(KEY_DOOR_MAZE):
        for x, cell in enumerate(row):
            if cell == CellType.START.value:
                start_pos = (x, y)
            elif cell == CellType.GOAL.value:
                goal_pos = (x, y)
            elif cell == CellType.KEY.value:
                key_pos = (x, y)
    
    print(f"\nMaze setup:")
    print(f"  Start: {start_pos}")
    print(f"  Goal: {goal_pos}")
    print(f"  Key: {key_pos}")
    
    # Test 1: Basic GMI (no trauma) - multiple runs
    print("\n" + "-" * 70)
    print("BASIC GMI (No Trauma Memory)")
    print("-" * 70)
    
    basic_results = []
    for run in range(5):
        random.seed(run * 100)
        np.random.seed(run * 100)
        
        gmi = EnhancedMazeGMI(
            maze=KEY_DOOR_MAZE,
            start_pos=start_pos,
            goal_pos=goal_pos,
            has_key_door=True,
        )
        
        result = gmi.run(max_steps=500)
        basic_results.append(result)
        
        status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
        print(f"  Run {run + 1}: {status} in {result['steps']} steps, "
              f"key={result['got_key']}, health={result['final_health']:.2f}")
    
    basic_success_rate = sum(1 for r in basic_results if r["success"]) / len(basic_results)
    basic_avg_steps = sum(r["steps"] for r in basic_results) / len(basic_results)
    
    print(f"\n  Basic GMI Success Rate: {basic_success_rate * 100:.0f}%")
    print(f"  Basic GMI Avg Steps: {basic_avg_steps:.1f}")
    
    # Test 2: Enhanced GMI (with trauma) - multiple runs
    print("\n" + "-" * 70)
    print("TRAUMA-ENHANCED GMI (Learns from failures)")
    print("-" * 70)
    
    # Create shared trauma memory for learning across runs
    curvature = CurvatureField(
        dimensions=2,
        resolution=50,
        bounds=(0.0, 10.0),
    )
    trauma = TraumaMemory(
        curvature_field=curvature,
        default_scar_spread=0.5,
    )
    
    enhanced_results = []
    for run in range(5):
        random.seed(run * 100)
        np.random.seed(run * 100)
        
        # Use fresh trauma for each run to see individual learning
        run_curvature = CurvatureField(
            dimensions=2,
            resolution=50,
            bounds=(0.0, 10.0),
        )
        run_trauma = TraumaMemory(
            curvature_field=run_curvature,
            default_scar_spread=0.5,
        )
        
        gmi = EnhancedMazeGMI(
            maze=KEY_DOOR_MAZE,
            start_pos=start_pos,
            goal_pos=goal_pos,
            has_key_door=True,
            trauma_memory=run_trauma,
        )
        
        result = gmi.run(max_steps=500)
        enhanced_results.append(result)
        
        status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
        print(f"  Run {run + 1}: {status} in {result['steps']} steps, "
              f"key={result['got_key']}, health={result['final_health']:.2f}")
    
    enhanced_success_rate = sum(1 for r in enhanced_results if r["success"]) / len(enhanced_results)
    enhanced_avg_steps = sum(r["steps"] for r in enhanced_results) / len(enhanced_results)
    
    print(f"\n  Enhanced GMI Success Rate: {enhanced_success_rate * 100:.0f}%")
    print(f"  Enhanced GMI Avg Steps: {enhanced_avg_steps:.1f}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Basic GMI:     {basic_success_rate * 100:.0f}% success, {basic_avg_steps:.1f} avg steps")
    print(f"  Enhanced GMI: {enhanced_success_rate * 100:.0f}% success, {enhanced_avg_steps:.1f} avg steps")
    
    if enhanced_success_rate > basic_success_rate:
        print(f"\n  → Trauma memory IMPROVED success rate by {(enhanced_success_rate - basic_success_rate) * 100:.0f}%!")
    elif enhanced_avg_steps < basic_avg_steps:
        print(f"\n  → Trauma memory REDUCED steps by {basic_avg_steps - enhanced_avg_steps:.1f} on average!")
    else:
        print(f"\n  → Results similar - maze may be too simple to show benefit")


def run_poison_maze():
    """Test with poison cells that create scars."""
    
    print("\n\n" + "=" * 70)
    print("POISON MAZE TEST: Learning to Avoid Harm")
    print("=" * 70)
    
    # Find positions
    start_pos = None
    goal_pos = None
    
    for y, row in enumerate(POISON_MAZE):
        for x, cell in enumerate(row):
            if cell == CellType.START.value:
                start_pos = (x, y)
            elif cell == CellType.GOAL.value:
                goal_pos = (x, y)
    
    print(f"\nMaze setup:")
    print(f"  Start: {start_pos}")
    print(f"  Goal: {goal_pos}")
    
    # Run with trauma
    print("\n" + "-" * 70)
    print("TRAUMA-ENHANCED GMI in Poison Maze")
    print("-" * 70)
    
    results = []
    for run in range(3):
        random.seed(run * 100)
        np.random.seed(run * 100)
        
        run_curvature = CurvatureField(
            dimensions=2,
            resolution=50,
            bounds=(0.0, 10.0),
        )
        run_trauma = TraumaMemory(
            curvature_field=run_curvature,
            default_scar_spread=0.8,
        )
        
        gmi = EnhancedMazeGMI(
            maze=POISON_MAZE,
            start_pos=start_pos,
            goal_pos=goal_pos,
            has_key_door=True,
            has_poison=True,
            trauma_memory=run_trauma,
        )
        
        result = gmi.run(max_steps=500)
        results.append(result)
        
        status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
        print(f"  Run {run + 1}: {status}")
        print(f"    Steps: {result['steps']}, Poison hits: {result['poison_hits']}, "
              f"Health: {result['final_health']:.2f}")
        
        # Show trauma summary
        if run_trauma.trauma_log:
            print(f"    Trauma events: {len(run_trauma.trauma_log)}")
    
    # Test learning across runs
    print("\n" + "-" * 70)
    print("LEARNING ACROSS MULTIPLE EPISODES")
    print("-" * 70)
    
    # Shared trauma - learns from previous failures
    shared_curvature = CurvatureField(
        dimensions=2,
        resolution=50,
        bounds=(0.0, 10.0),
    )
    shared_trauma = TraumaMemory(
        curvature_field=shared_curvature,
        default_scar_spread=0.8,
    )
    
    episode_results = []
    for episode in range(5):
        random.seed(episode * 100)
        np.random.seed(episode * 100)
        
        gmi = EnhancedMazeGMI(
            maze=POISON_MAZE,
            start_pos=start_pos,
            goal_pos=goal_pos,
            has_key_door=True,
            has_poison=True,
            trauma_memory=shared_trauma,
        )
        
        result = gmi.run(max_steps=500)
        episode_results.append(result)
        
        status = "✓" if result["success"] else "✗"
        print(f"  Episode {episode + 1}: {status} "
              f"poison={result['poison_hits']}, "
              f"health={result['final_health']:.2f}")
    
    # Show final trauma state
    summary = shared_trauma.get_trauma_summary()
    print(f"\n  Final trauma state:")
    print(f"    Total damage taken: {summary['total_damage']:.2f}")
    print(f"    Total scars: {summary['total_scars']}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    run_comparison()
    run_poison_maze()
    
    print("\n" + "=" * 70)
    print("ALL MAZE TESTS COMPLETE!")
