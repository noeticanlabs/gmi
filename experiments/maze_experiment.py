"""
GMI Maze Navigation Experiments

This experiment tests GMI's ability to navigate through:
1. Simple Maze: Find path from start to goal
2. Key-Door Maze: Collect key first to unlock door, then reach goal

The maze is represented as a 2D grid with:
- 0 = open space (low tension)
- 1 = wall (high tension / barrier)
- 2 = goal (minimum tension)
- 3 = start
- 4 = key (in key-door variant)
- 5 = door (passable only with key)

The GMI system treats this as a thermodynamic problem:
- Movement cost = sigma
- Wall collision = high potential barrier
- Goal = minimum potential
"""

import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set
import random

# GMI imports
from core.state import State, Instruction
from core.memory import MemoryManifold
from ledger.oplax_verifier import OplaxVerifier


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


# Simple maze (8x8)
SIMPLE_MAZE = [
    [3, 0, 1, 0, 0, 0, 0, 0],
    [1, 0, 1, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 2, 1, 0],
    [0, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0],
    [1, 1, 1, 1, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
]

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


@dataclass
class MazeConfig:
    """Configuration for maze navigation"""
    grid: List[List[int]]
    start_pos: Tuple[int, int]
    goal_pos: Tuple[int, int]
    has_key: bool = False
    has_door: bool = False
    key_pos: Optional[Tuple[int, int]] = None
    door_pos: Optional[Tuple[int, int]] = None
    inventory: Set[str] = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = set()


class MazePotential:
    """
    Potential function for maze navigation.
    Higher V = more obstacles / harder to traverse.
    """
    
    def __init__(self, config: MazeConfig, memory: MemoryManifold = None, 
                 wall_penalty: float = 50.0, memory_weight: float = 1.0):
        self.config = config
        self.memory = memory
        self.wall_penalty = wall_penalty
        self.memory_weight = memory_weight
        self.height = len(config.grid)
        self.width = len(config.grid[0])
    
    def __call__(self, x: np.ndarray) -> float:
        """Compute potential at position x (continuous coordinates)"""
        # Convert to grid coordinates
        grid_x = int(round(x[0]))
        grid_y = int(round(x[1]))
        
        # Clamp to grid bounds
        grid_x = max(0, min(self.width - 1, grid_x))
        grid_y = max(0, min(self.height - 1, grid_y))
        
        cell = self.config.grid[grid_y][grid_x]
        
        # Base potential based on cell type
        if cell == CellType.WALL.value:
            base_v = self.wall_penalty
        elif cell == CellType.GOAL.value:
            base_v = 0.0
        elif cell == CellType.DOOR.value:
            if "key" in self.config.inventory:
                base_v = 0.5  # Easy to pass with key
            else:
                base_v = self.wall_penalty  # Blocked without key
        else:
            # Distance to goal
            dx = grid_x - self.config.goal_pos[0]
            dy = grid_y - self.config.goal_pos[1]
            base_v = dx**2 + dy**2
        
        # Add memory curvature if available
        memory_v = 0.0
        if self.memory is not None:
            memory_v = self.memory.read_curvature(x) * self.memory_weight
        
        return float(base_v + memory_v)


def get_valid_moves(pos: Tuple[int, int], config: MazeConfig) -> List[Tuple[int, int]]:
    """Get valid neighboring positions from current position"""
    x, y = pos
    moves = []
    
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx, ny = x + dx, y + dy
        
        # Check bounds
        if 0 <= nx < len(config.grid[0]) and 0 <= ny < len(config.grid):
            cell = config.grid[ny][nx]
            
            # Check if passable
            if cell != CellType.WALL.value:
                # Door requires key
                if cell == CellType.DOOR.value and "key" not in config.inventory:
                    continue
                moves.append((nx, ny))
    
    return moves


# =============================================================================
# GMI MAZE NAVIGATOR
# =============================================================================

@dataclass
class MazeResult:
    """Result from maze navigation"""
    success: bool
    steps: int
    final_pos: Tuple[int, int]
    path: List[Tuple[int, int]]
    budget_spent: float
    key_collected: bool = False
    door_passed: bool = False


def run_maze_navigation(
    maze: List[List[int]],
    start_pos: Tuple[int, int],
    goal_pos: Tuple[int, int],
    initial_budget: float = 100.0,
    max_steps: int = 100,
    has_key: bool = False,
    key_pos: Optional[Tuple[int, int]] = None,
    has_door: bool = False,
    door_pos: Optional[Tuple[int, int]] = None,
    use_memory: bool = False,
    memory_lambda: float = 0.5,
    shared_memory: MemoryManifold = None,  # NEW: Pass existing memory across runs
    seed: int = None
) -> MazeResult:
    """
    Navigate through maze using GMI thermodynamics.
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    # Setup config
    config = MazeConfig(
        grid=maze,
        start_pos=start_pos,
        goal_pos=goal_pos,
        has_key=has_key,
        has_door=has_door,
        key_pos=key_pos,
        door_pos=door_pos
    )
    
    # Setup memory - use shared_memory if provided, otherwise create new
    if shared_memory is not None:
        memory = shared_memory
    elif use_memory:
        memory = MemoryManifold(lambda_c=memory_lambda)
    else:
        memory = None
    
    # Setup potential function
    potential_fn = MazePotential(config, memory)
    verifier = OplaxVerifier(potential_fn=potential_fn)
    
    # Start state
    state = State(list(start_pos), initial_budget)
    
    path = [start_pos]
    steps = 0
    budget_spent = 0.0
    key_collected = False
    door_passed = False
    
    while steps < max_steps:
        current_pos = (int(state.x[0]), int(state.x[1]))
        
        # Check if at goal
        if current_pos == goal_pos:
            return MazeResult(
                success=True,
                steps=steps,
                final_pos=current_pos,
                path=path,
                budget_spent=budget_spent,
                key_collected=key_collected,
                door_passed=door_passed
            )
        
        # Get valid moves
        valid_moves = get_valid_moves(current_pos, config)
        
        if not valid_moves:
            # Stuck
            break
        
        # Generate EXPLORE and INFER proposals
        explore_move = random.choice(valid_moves)
        
        # EXPLORE: Random valid move
        explore_instr = Instruction(
            "EXPLORE",
            lambda x, m=explore_move: np.array([float(m[0]), float(m[1])]),
            sigma=3.0,
            kappa=8.0
        )
        
        # INFER: Smart heuristic - prioritize key if needed, else goal
        if has_key and key_pos and "key" not in config.inventory:
            # Need to get key first
            target = key_pos
        else:
            target = goal_pos
            
        best_move = min(valid_moves, 
                       key=lambda m: (m[0] - target[0])**2 + (m[1] - target[1])**2)
        infer_instr = Instruction(
            "INFER",
            lambda x, m=best_move: np.array([float(m[0]), float(m[1])]),
            sigma=0.5,
            kappa=0.5
        )
        
        # Try EXPLORE first
        accepted, next_state, receipt = verifier.check(steps, state, explore_instr)
        
        if accepted:
            new_pos = (int(next_state.x[0]), int(next_state.x[1]))
            
            # Check for key collection
            if has_key and key_pos and new_pos == key_pos:
                config.inventory.add("key")
                key_collected = True
            
            # Check for door passage
            if has_door and door_pos and new_pos == door_pos:
                door_passed = True
            
            path.append(new_pos)
            state = next_state
            budget_spent += explore_instr.sigma
        else:
            # Try INFER fallback
            accepted, next_state, receipt = verifier.check(steps, state, infer_instr)
            
            if accepted:
                new_pos = (int(next_state.x[0]), int(next_state.x[1]))
                
                if has_key and key_pos and new_pos == key_pos:
                    config.inventory.add("key")
                    key_collected = True
                
                if has_door and door_pos and new_pos == door_pos:
                    door_passed = True
                
                path.append(new_pos)
                state = next_state
                budget_spent += infer_instr.sigma
            else:
                # Record failed position in memory
                if use_memory and memory:
                    failed_move = explore_move
                    memory.write_scar(np.array([float(failed_move[0]), float(failed_move[1])]), 
                                     penalty=1.0)
                break
        
        steps += 1
    
    # Failed to reach goal
    return MazeResult(
        success=False,
        steps=steps,
        final_pos=(int(state.x[0]), int(state.x[1])),
        path=path,
        budget_spent=budget_spent,
        key_collected=key_collected,
        door_passed=door_passed
    )


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def run_maze_experiments():
    """Run both maze experiments"""
    
    print("=" * 60)
    print("GMI MAZE NAVIGATION EXPERIMENTS")
    print("=" * 60)
    
    # Find positions in simple maze - start at top-left, goal near center
    start = (0, 0)
    goal = (2, 2)  # Adjust to be reachable
    
    # Test 1: Simple Maze (using smaller, simpler maze)
    simple_maze = [
        [3, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 1, 1, 2],
    ]
    
    print("\n" + "=" * 60)
    print("TEST 1: SIMPLE MAZE NAVIGATION")
    print("=" * 60)
    print("Maze:")
    for row in simple_maze:
        print("  ", row)
    print(f"Start: {start}, Goal: {goal}")
    
    # Test configuration: 1 run for no-memory baseline, 10 runs for memory
    print("\n--- Simple Maze: No Memory (1 run) ---")
    r_simple_no_mem = run_maze_navigation(
        maze=simple_maze,
        start_pos=start,
        goal_pos=goal,
        initial_budget=100.0,
        max_steps=100,
        use_memory=False,
        seed=0
    )
    print(f"  Result: {'SUCCESS' if r_simple_no_mem.success else 'FAILED'} (steps={r_simple_no_mem.steps}, budget_spent={r_simple_no_mem.budget_spent:.1f})")
    
    print("\n--- Simple Maze: With Memory (10 runs, shared memory) ---")
    # Create ONE memory instance that persists across all 10 runs - learns from failures
    shared_memory_simple = MemoryManifold(lambda_c=0.5)
    results_with_memory = []
    for seed in range(10):
        r = run_maze_navigation(
            maze=simple_maze,
            start_pos=start,
            goal_pos=goal,
            initial_budget=100.0,
            max_steps=100,
            use_memory=True,
            memory_lambda=0.5,
            shared_memory=shared_memory_simple,  # Share memory across runs
            seed=seed
        )
        results_with_memory.append(r)
        print(f"  Seed {seed}: {'SUCCESS' if r.success else 'FAILED'} (steps={r.steps}, memory_scars={len(shared_memory_simple.scars)})")
    
    success_mem = sum(1 for r in results_with_memory if r.success)
    print(f"\nResults (With Memory): {success_mem}/10 ({success_mem*10:.0f}%)")
    
    # Test 2: Key-Door Maze
    print("\n" + "=" * 60)
    print("TEST 2: KEY-DOOR MAZE")
    print("=" * 60)
    
    # Fix: Make sure path exists to key and through door
    key_door_maze = [
        [3, 0, 0, 0, 4],  # Row 0: start at (0,0), key at (4,0)
        [0, 1, 1, 0, 1],  
        [0, 0, 0, 0, 0],  
        [1, 1, 1, 5, 1],  # Door at (3,3)
        [0, 0, 0, 0, 2],  # Goal at (4,4)
    ]
    
    start_kd = (0, 0)
    goal_kd = (4, 4)
    key_pos_kd = (4, 0)
    door_pos_kd = (3, 3)
    
    print("Maze:")
    for row in key_door_maze:
        print("  ", row)
    print(f"Start: {start_kd}, Goal: {goal_kd}")
    print(f"Key: {key_pos_kd}, Door: {door_pos_kd}")
    
    # Test configuration: 1 run for no-memory baseline, 10 runs for memory
    print("\n--- Key-Door Maze: No Memory (1 run) ---")
    r_kd_no_mem = run_maze_navigation(
        maze=key_door_maze,
        start_pos=start_kd,
        goal_pos=goal_kd,
        initial_budget=200.0,
        max_steps=150,
        has_key=True,
        key_pos=key_pos_kd,
        has_door=True,
        door_pos=door_pos_kd,
        use_memory=False,
        seed=0
    )
    print(f"  Result: {'SUCCESS' if r_kd_no_mem.success else 'FAILED'} "
          f"(steps={r_kd_no_mem.steps}, key={r_kd_no_mem.key_collected}, door={r_kd_no_mem.door_passed})")
    
    print("\n--- Key-Door Maze: With Memory (10 runs, shared memory) ---")
    # Create ONE memory instance that persists across all 10 runs - learns from failures
    shared_memory_kd = MemoryManifold(lambda_c=0.5)
    results_kd = []
    for seed in range(10):
        r = run_maze_navigation(
            maze=key_door_maze,
            start_pos=start_kd,
            goal_pos=goal_kd,
            initial_budget=200.0,
            max_steps=150,
            has_key=True,
            key_pos=key_pos_kd,
            has_door=True,
            door_pos=door_pos_kd,
            use_memory=True,
            memory_lambda=0.5,
            shared_memory=shared_memory_kd,  # Share memory across runs
            seed=seed
        )
        results_kd.append(r)
        print(f"  Seed {seed}: {'SUCCESS' if r.success else 'FAILED'} "
              f"(steps={r.steps}, key={r.key_collected}, door={r.door_passed}, scars={len(shared_memory_kd.scars)})")
    
    success_kd = sum(1 for r in results_kd if r.success)
    print(f"\nKey-Door Results: {success_kd}/10 successful")
    
    # Summary
    print("\n" + "=" * 60)
    print("MAZE EXPERIMENT SUMMARY")
    print("=" * 60)
    simple_no_mem_result = 'SUCCESS' if r_simple_no_mem.success else 'FAILED'
    print(f"Simple Maze - No Memory: {simple_no_mem_result} (1 run)")
    print(f"Simple Maze - With Memory: {success_mem}/10 ({success_mem*10}%)")
    print(f"Key-Door Maze - No Memory: {'SUCCESS' if r_kd_no_mem.success else 'FAILED'} (1 run)")
    print(f"Key-Door Maze - With Memory: {success_kd}/10 ({success_kd*10}%)")
    
    return {
        "simple_no_memory": 1 if r_simple_no_mem.success else 0,
        "simple_with_memory": success_mem,
        "key_door_no_memory": 1 if r_kd_no_mem.success else 0,
        "key_door_with_memory": success_kd
    }


if __name__ == "__main__":
    run_maze_experiments()
