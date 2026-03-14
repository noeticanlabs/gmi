"""
Simple Greedy Planner for GMI.

A planning module that selects actions based on goal-directed heuristics.
This is the "gradient descent" level of planning - not full lookahead,
but better than pure reactive behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from gmos.agents.gmi.planning.goal_representation import (
    GoalState,
    GoalType,
    SubGoal,
    GoalDecomposition,
)


@dataclass
class PlannerConfig:
    """Configuration for the planner."""
    # Planning horizon
    horizon: int = 5  # How many steps to look ahead
    
    # Action selection
    num_candidates: int = 4  # Number of candidate actions to evaluate
    
    # Exploration
    exploration_weight: float = 0.1  # For epsilon-greedy
    
    # Goal handling
    max_subgoal_steps: int = 50
    
    # Learning
    learn_from_experience: bool = True
    replay_buffer_size: int = 1000


class GreedyPlanner:
    """
    Goal-directed planner using greedy action selection.
    
    Given a goal, this planner:
    1. Evaluates candidate actions by simulating their effect
    2. Selects the action that best reduces distance to goal
    3. Updates goal progress based on outcome
    
    This is "gradient descent in action space" - not optimal,
    but effective for simple tasks.
    """
    
    # Action candidates for 2D navigation
    ACTION_DELTAS = [
        (0, -1),   # Up
        (0, 1),    # Down
        (-1, 0),   # Left
        (1, 0),    # Right
        (0, 0),    # Wait
    ]
    
    def __init__(self, config: PlannerConfig):
        self.config = config
        self.current_goal: Optional[GoalState] = None
        self.current_subgoal: Optional[SubGoal] = None
        self.goal_memory: List[Dict[str, Any]] = []
        
        # State tracking for hierarchical tasks
        self._has_key = False
        self._door_open = False
        self._inventory = set()
        
        # Statistics
        self.stats = {
            "goals_achieved": 0,
            "goals_failed": 0,
            "total_steps": 0,
            "subgoals_completed": 0,
        }
    
    def set_goal(self, goal: GoalState):
        """Set the current goal."""
        self.current_goal = goal
        
        # Initialize sub-goal tracking
        if goal.goal_type == GoalType.SEQUENCE:
            # Get first sub-goal
            self.current_subgoal = SubGoal(
                goal_state=goal.sub_goals[0] if goal.sub_goals else goal,
                max_steps=self.config.max_subgoal_steps
            )
        else:
            self.current_subgoal = SubGoal(
                goal_state=goal,
                max_steps=self.config.max_subgoal_steps
            )
    
    def reset(self):
        """Reset planner state."""
        self.current_goal = None
        self.current_subgoal = None
    
    def select_action(
        self,
        state: Dict[str, Any],
        observation: np.ndarray,
    ) -> Tuple[int, np.ndarray]:
        """
        Select an action given current state and observation.
        
        Args:
            state: Environment state dict (position, inventory, etc.)
            observation: Sensory observation
        
        Returns:
            (action_index, action_vector)
        """
        # Update internal state tracking
        self._update_state_tracking(state)
        
        if self.current_goal is None:
            # No goal - default action
            return 4, np.array([0, 0])  # Wait
        
        # Check if current sub-goal is achieved
        if self.current_subgoal and self.current_subgoal.goal_state.is_achieved(state):
            # Move to next sub-goal
            self.stats["subgoals_completed"] += 1
            self._advance_subgoal(state)
        
        if self.current_subgoal is None:
            # Goal complete!
            self.stats["goals_achieved"] += 1
            return 4, np.array([0, 0])  # Wait
        
        # Evaluate candidate actions
        candidates = self._evaluate_candidates(state)
        
        # Select best action (with exploration)
        if np.random.random() < self.config.exploration_weight:
            # Random action
            action_idx = np.random.randint(len(candidates))
        else:
            # Greedy selection
            action_idx = max(range(len(candidates)), key=lambda i: candidates[i]["score"])
        
        self.current_subgoal.steps_taken += 1
        
        # Check for timeout
        if self.current_subgoal.is_timeout():
            self.stats["goals_failed"] += 1
            self._advance_subgoal(state)
        
        dx, dy = self.ACTION_DELTAS[action_idx]
        return action_idx, np.array([dx, dy])
    
    def _update_state_tracking(self, state: Dict[str, Any]):
        """Update internal state tracking from environment state."""
        # Track inventory
        if "inventory" in state:
            self._inventory = state["inventory"]
        
        # Track key status
        self._has_key = state.get("has_key", "key" in self._inventory)
        
        # Track door status
        self._door_open = state.get("door_open", False)
    
    def _evaluate_candidates(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all candidate actions."""
        candidates = []
        
        current_pos = state.get("position", (0, 0))
        
        for action_idx, (dx, dy) in enumerate(self.ACTION_DELTAS):
            # Simulate next position
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            # Simulate state for evaluation
            sim_state = state.copy()
            sim_state["position"] = next_pos
            sim_state["has_key"] = self._has_key
            sim_state["door_open"] = self._door_open
            sim_state["inventory"] = self._inventory
            
            # Evaluate based on goal
            if self.current_subgoal:
                distance = self.current_subgoal.goal_state.distance_to_goal(sim_state)
                
                # Score: lower distance = better
                score = -distance
                
                # Bonus for goal achievement
                if self.current_subgoal.goal_state.is_achieved(sim_state):
                    score += 10.0
                
                # KEY-DOOR CONSTRAINT: Don't target door without key
                if self.current_subgoal.goal_state.goal_type == GoalType.REACH:
                    target = self.current_subgoal.goal_state.target
                    if target and hasattr(target, '__iter__') and len(target) == 2:
                        # Check if targeting door
                        door_pos = self.current_subgoal.goal_state.constraints.get("requires", [])
                        if "key" in door_pos and not self._has_key:
                            # Heavy penalty for trying to enter door without key
                            if next_pos == target:
                                score -= 5.0
                
                # Penalty for obstacles (if we can detect them)
                if state.get("collision"):
                    score -= 0.5
            else:
                score = 0.0
            
            candidates.append({
                "action_idx": action_idx,
                "delta": (dx, dy),
                "next_pos": next_pos,
                "score": score,
            })
        
        return candidates
    
    def _advance_subgoal(self, state: Dict[str, Any]):
        """Move to the next sub-goal in sequence."""
        if self.current_goal is None:
            self.current_subgoal = None
            return
        
        if self.current_goal.goal_type == GoalType.SEQUENCE:
            # Find current position in sequence
            current_idx = 0
            for i, sg in enumerate(self.current_goal.sub_goals):
                if sg.is_achieved(state):
                    current_idx = i + 1
                else:
                    break
            
            # Check if more sub-goals
            if current_idx < len(self.current_goal.sub_goals):
                self.current_subgoal = SubGoal(
                    goal_state=self.current_goal.sub_goals[current_idx],
                    max_steps=self.config.max_subgoal_steps
                )
            else:
                # All complete
                self.current_subgoal = None
        else:
            # Single goal - check if achieved
            if self.current_goal.is_achieved(state):
                self.current_subgoal = None
    
    def record_outcome(self, achieved: bool, final_state: Dict[str, Any]):
        """Record goal outcome for learning."""
        if self.current_goal:
            self.goal_memory.append({
                "goal": self.current_goal,
                "achieved": achieved,
                "final_state": final_state.copy(),
            })
            
            if len(self.goal_memory) > self.config.replay_buffer_size:
                self.goal_memory.pop(0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get planner statistics."""
        return self.stats.copy()


class HierarchicalPlanner:
    """
    Hierarchical planner that combines:
    1. Goal decomposition (high-level)
    2. Greedy planning (mid-level)
    3. Reactive control (low-level)
    """
    
    def __init__(self, config: PlannerConfig):
        self.config = config
        self.planner = GreedyPlanner(config)
        self.decomposition = GoalDecomposition()
        
        # Current task
        self.task_type: Optional[str] = None
    
    def setup_key_door_task(self):
        """Set up a key-door task."""
        self.task_type = "key_door"
        goal = self.decomposition.decompose_key_door_task()
        self.planner.set_goal(goal)
    
    def setup_navigation_task(self, target: Tuple[int, int]):
        """Set up a simple navigation task."""
        self.task_type = "navigation"
        goal = GoalState(
            goal_type=GoalType.REACH,
            target=target,
            priority=1.0
        )
        self.planner.set_goal(goal)
    
    def step(
        self,
        state: Dict[str, Any],
        observation: np.ndarray,
    ) -> Tuple[int, np.ndarray]:
        """Plan and select action."""
        return self.planner.select_action(state, observation)
    
    def reset(self):
        """Reset planner."""
        self.planner.reset()
        self.task_type = None
    
    @property
    def is_task_complete(self) -> bool:
        """Check if current task is complete."""
        return self.planner.current_subgoal is None


def create_planner(
    horizon: int = 5,
    exploration_weight: float = 0.1,
) -> GreedyPlanner:
    """Factory function to create a planner."""
    config = PlannerConfig(
        horizon=horizon,
        exploration_weight=exploration_weight,
    )
    return GreedyPlanner(config)


def create_hierarchical_planner(
    horizon: int = 5,
    exploration_weight: float = 0.1,
) -> HierarchicalPlanner:
    """Factory function to create a hierarchical planner."""
    config = PlannerConfig(
        horizon=horizon,
        exploration_weight=exploration_weight,
    )
    return HierarchicalPlanner(config)
