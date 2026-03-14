"""
Goal Representation and Decomposition for GMI Planning.

This module provides:
- GoalState: Representation of task goals
- SubGoal: Individual subgoals in a decomposed plan
- GoalDecomposition: Logic for breaking down complex goals
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from enum import Enum


class GoalType(Enum):
    """Types of goals the GMI can pursue."""
    REACH = "reach"              # Reach a position
    ACQUIRE = "acquire"          # Acquire an object
    AVOID = "avoid"              # Avoid something
    EXPLORE = "explore"          # Explore unknown area
    MAINTAIN = "maintain"        # Maintain a state
    SEQUENCE = "sequence"        # Sequence of goals


@dataclass
class GoalState:
    """
    Represents a goal state for the GMI.
    
    The goal can be:
    - A target position (reach)
    - An object to acquire
    - A state to avoid
    - A sequence of subgoals
    """
    goal_type: GoalType
    target: Any = None           # Position, object ID, etc.
    priority: float = 1.0        # Goal priority (0-1)
    deadline: Optional[int] = None  # Max steps to achieve
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # For SEQUENCE type
    sub_goals: List['GoalState'] = field(default_factory=list)
    
    def is_achieved(self, current_state: Dict[str, Any]) -> bool:
        """
        Check if goal is achieved given current state.
        
        Args:
            current_state: Dict with 'position', 'inventory', 'visited', etc.
        
        Returns:
            True if goal is achieved
        """
        if self.goal_type == GoalType.REACH:
            if self.target is None:
                return False
            pos = current_state.get("position", (0, 0))
            
            # Check constraints (e.g., need key before reaching door)
            requires = self.constraints.get("requires", [])
            if "key" in requires:
                has_key = current_state.get("has_key", "key" in current_state.get("inventory", set()))
                if not has_key:
                    return False  # Can't reach door without key
            if "door_open" in requires:
                door_open = current_state.get("door_open", False)
                if not door_open:
                    return False
            
            return pos == self.target
        
        elif self.goal_type == GoalType.ACQUIRE:
            inventory = current_state.get("inventory", set())
            return self.target in inventory
        
        elif self.goal_type == GoalType.AVOID:
            pos = current_state.get("position", (0, 0))
            avoid_targets = current_state.get("avoid", set())
            return pos not in avoid_targets
        
        elif self.goal_type == GoalType.EXPLORE:
            visited = current_state.get("visited", set())
            target_area = self.constraints.get("area", set())
            return len(target_area & visited) >= self.constraints.get("min_coverage", 0.8)
        
        elif self.goal_type == GoalType.SEQUENCE:
            return all(sg.is_achieved(current_state) for sg in self.sub_goals)
        
        return False
    
    def distance_to_goal(self, current_state: Dict[str, Any]) -> float:
        """
        Estimate distance to goal achievement.
        
        Returns:
            Float distance estimate (0 = achieved)
        """
        if self.is_achieved(current_state):
            return 0.0
        
        if self.goal_type == GoalType.REACH:
            if self.target is None:
                return float('inf')
            pos = current_state.get("position", (0, 0))
            
            # Check if constraints prevent achievement
            requires = self.constraints.get("requires", [])
            if "key" in requires:
                has_key = current_state.get("has_key", "key" in current_state.get("inventory", set()))
                if not has_key:
                    # Can't reach yet - distance is infinite (or very large)
                    return 1000.0 + np.sqrt((pos[0] - self.target[0])**2 + (pos[1] - self.target[1])**2)
            if "door_open" in requires:
                door_open = current_state.get("door_open", False)
                if not door_open:
                    return 1000.0 + np.sqrt((pos[0] - self.target[0])**2 + (pos[1] - self.target[1])**2)
            
            dx = pos[0] - self.target[0]
            dy = pos[1] - self.target[1]
            return np.sqrt(dx**2 + dy**2)
        
        elif self.goal_type == GoalType.ACQUIRE:
            inventory = current_state.get("inventory", set())
            if self.target in inventory:
                return 0.0
            # Distance to object
            obj_pos = self.constraints.get("position", (0, 0))
            pos = current_state.get("position", (0, 0))
            dx = pos[0] - obj_pos[0]
            dy = pos[1] - obj_pos[1]
            return np.sqrt(dx**2 + dy**2)
        
        elif self.goal_type == GoalType.SEQUENCE:
            # Distance to first unachieved sub-goal
            for sg in self.sub_goals:
                if not sg.is_achieved(current_state):
                    return sg.distance_to_goal(current_state)
            return 0.0
        
        return 1.0  # Unknown distance
    
    def get_next_subgoal(self, current_state: Dict[str, Any]) -> Optional['GoalState']:
        """
        Get the next actionable sub-goal.
        
        For SEQUENCE goals, returns first unachieved sub-goal.
        For atomic goals, returns self if not achieved.
        """
        if self.goal_type == GoalType.SEQUENCE:
            for sg in self.sub_goals:
                if not sg.is_achieved(current_state):
                    return sg.get_next_subgoal(current_state)
            return None
        
        if self.is_achieved(current_state):
            return None
        
        return self


@dataclass
class SubGoal:
    """
    A single actionable sub-goal with associated policy.
    
    This is what gets fed to the GMI's action selection:
    - Clear target state
    - Heuristic for selecting actions
    - Success criteria
    """
    goal_state: GoalState
    heuristic_fn: str = "gradient"  # How to select actions
    max_steps: int = 50
    reward_if_achieved: float = 1.0
    penalty_if_failed: float = -0.1
    
    # For tracking progress
    steps_taken: int = 0
    attempts: int = 0
    
    def reset(self):
        """Reset tracking counters."""
        self.steps_taken = 0
        self.attempts += 1
    
    def is_timeout(self) -> bool:
        """Check if we've exceeded max steps."""
        return self.steps_taken >= self.max_steps


class GoalDecomposition:
    """
    Decomposes complex goals into sequences of sub-goals.
    
    This is the "strong planning" component that transforms
    high-level objectives into actionable sub-goals.
    """
    
    @staticmethod
    def decompose_key_door_task() -> GoalState:
        """
        Decompose key-door task into sub-goals.
        
        Goal: Reach goal
        Sub-goals:
        1. Acquire key
        2. Reach door
        3. Open door
        4. Reach goal
        """
        # Sub-goal 1: Get the key
        acquire_key = GoalState(
            goal_type=GoalType.ACQUIRE,
            target="key",
            priority=1.0,
            constraints={"position": (1, 8)}  # Key position
        )
        
        # Sub-goal 2: Go to door (with key)
        reach_door = GoalState(
            goal_type=GoalType.REACH,
            target=(5, 5),  # Door position
            priority=0.9,
            constraints={"requires": ["key"]}
        )
        
        # Sub-goal 3: Open door (implicit in reaching door with key)
        # This is handled by the environment
        
        # Sub-goal 4: Reach goal (after door is open)
        reach_goal = GoalState(
            goal_type=GoalType.REACH,
            target=(8, 8),  # Goal position
            priority=0.8,
            constraints={"requires": ["door_open"]}
        )
        
        # Combine into sequence
        return GoalState(
            goal_type=GoalType.SEQUENCE,
            sub_goals=[acquire_key, reach_door, reach_goal],
            priority=1.0
        )
    
    @staticmethod
    def decompose_explore_task(
        grid_size: Tuple[int, int],
        start: Tuple[int, int]
    ) -> GoalState:
        """
        Decompose exploration task.
        
        Goal: Explore grid
        Sub-goals: Visit all reachable cells
        """
        # For now, simple version: explore in expanding spirals
        return GoalState(
            goal_type=GoalType.EXPLORE,
            target=None,
            priority=1.0,
            constraints={
                "area": set(),  # Will be filled in
                "min_coverage": 0.9
            }
        )
    
    @staticmethod
    def decompose_avoid_task(
        hazards: List[Tuple[int, int]],
        target: Tuple[int, int]
    ) -> GoalState:
        """
        Decompose avoidance task.
        
        Goal: Reach target while avoiding hazards
        """
        return GoalState(
            goal_type=GoalType.SEQUENCE,
            sub_goals=[
                GoalState(
                    goal_type=GoalType.AVOID,
                    target=None,
                    constraints={"hazards": set(hazards)}
                ),
                GoalState(
                    goal_type=GoalType.REACH,
                    target=target
                )
            ],
            priority=1.0
        )
    
    @staticmethod
    def get_current_goal(goal_state: GoalState, current_state: Dict[str, Any]) -> Optional[SubGoal]:
        """
        Convert a goal state to an actionable sub-goal.
        
        Args:
            goal_state: The overall goal
            current_state: Current agent state
        
        Returns:
            SubGoal ready for action selection
        """
        next_goal = goal_state.get_next_subgoal(current_state)
        
        if next_goal is None:
            return None
        
        return SubGoal(
            goal_state=next_goal,
            max_steps=goal_state.deadline or 50
        )


class GoalMemory:
    """
    Memory of past goals and their outcomes.
    
    Used for learning which decompositions work.
    """
    
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.history: List[Dict[str, Any]] = []
    
    def record(
        self,
        goal: GoalState,
        achieved: bool,
        steps: int,
        final_state: Dict[str, Any]
    ):
        """Record a goal attempt."""
        record = {
            "goal_type": goal.goal_type,
            "achieved": achieved,
            "steps": steps,
            "final_state": final_state.copy(),
        }
        
        self.history.append(record)
        
        if len(self.history) > self.capacity:
            self.history.pop(0)
    
    def success_rate(self, goal_type: GoalType) -> float:
        """Get success rate for a goal type."""
        matching = [r for r in self.history if r["goal_type"] == goal_type]
        if not matching:
            return 0.0
        
        achieved = sum(1 for r in matching if r["achieved"])
        return achieved / len(matching)
    
    def average_steps(self, goal_type: GoalType) -> float:
        """Get average steps for a goal type."""
        matching = [r for r in self.history if r["goal_type"] == goal_type and r["achieved"]]
        if not matching:
            return float('inf')
        
        return sum(r["steps"] for r in matching) / len(matching)
