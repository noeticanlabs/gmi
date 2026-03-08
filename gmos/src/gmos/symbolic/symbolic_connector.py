"""
Symbolic Connector for GM-OS.

Integrates the symbolic layer with the hosted GMI agent:
- Binds state to symbols for memory summary
- Provides symbolic representation of memory episodes
- Tags action choices with symbolic metadata

Usage:
    from gmos.symbolic.symbolic_connector import SymbolicConnector
    
    connector = SymbolicConnector()
    
    # Bind state to create symbolic summary
    summary = connector.summarize_state(current_state)
    
    # Bind action choice
    connector.bind_action("move_left", action_metadata)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from gmos.symbolic.glyph_space import (
    GlyphSpace,
    GlyphState,
    GlyphCoordinate,
    GlyphEmbedding,
    GlyphType,
    create_glyph_space
)
from gmos.symbolic.binding import BindingContext


@dataclass
class SymbolicSummary:
    """A symbolic summary of cognitive state."""
    glyph_state: GlyphState
    bindings: Dict[str, str]  # state_key -> symbol_id
    representation: str  # Human-readable summary


@dataclass
class ActionTag:
    """Symbolic tag for an action choice."""
    action_id: str
    glyph_id: str
    reasoning: str
    confidence: float


class SymbolicConnector:
    """
    Connects symbolic layer to cognitive processing.
    
    Responsibilities:
    1. Summarize state as symbolic representation
    2. Tag actions with symbolic metadata
    3. Bind/unbind state-symbol pairs
    
    This provides one simple use case: symbolic summary of state
    which can influence memory/policy.
    """
    
    def __init__(self):
        self.glyph_space = create_glyph_space()
        self.binding_context = BindingContext()
        
        # Track summaries for memory
        self._summary_history: List[SymbolicSummary] = []
        self._action_tags: List[ActionTag] = []
    
    def summarize_state(
        self,
        state_data: Dict[str, Any],
        goal: Optional[str] = None
    ) -> SymbolicSummary:
        """
        Create a symbolic summary of the current state.
        
        This is a simple use case: convert continuous state into
        symbolic representation for memory/policy.
        
        Args:
            state_data: Current state dictionary (e.g., {"x": [1.0, 2.0], "b": 10.0})
            goal: Optional goal for context
            
        Returns:
            SymbolicSummary with glyph state and bindings
        """
        glyph_state = GlyphState()
        
        # Bind position to glyphs
        if "x" in state_data:
            x = state_data["x"]
            if isinstance(x, list) and len(x) >= 2:
                # Create glyph for position
                pos_coord = GlyphCoordinate(
                    x=float(x[0]),
                    y=float(x[1]),
                    glyph_type=GlyphType.ENTITY
                )
                pos_embedding = GlyphEmbedding(
                    coordinate=pos_coord,
                    confidence=0.9
                )
                glyph_state.add_glyph("position", pos_embedding)
                self.binding_context.bind("x", "position", confidence=0.9)
        
        # Bind budget to glyph
        if "b" in state_data:
            budget = float(state_data["b"])
            
            # Categorize budget level
            if budget > 5.0:
                budget_type = GlyphType.ENTITY
                budget_label = "abundant"
            elif budget > 2.0:
                budget_type = GlyphType.CONCEPT
                budget_label = "moderate"
            else:
                budget_type = GlyphType.CONCEPT
                budget_label = "scarce"
            
            budget_coord = GlyphCoordinate(
                x=budget,
                y=0.0,
                glyph_type=budget_type
            )
            budget_embedding = GlyphEmbedding(
                coordinate=budget_coord,
                confidence=0.95
            )
            glyph_state.add_glyph(budget_label, budget_embedding)
            self.binding_context.bind("b", budget_label, confidence=0.95)
        
        # Bind potential if present
        if "potential" in state_data:
            pot = float(state_data["potential"])
            pot_coord = GlyphCoordinate(
                x=pot,
                y=0.0,
                glyph_type=GlyphType.PREDICATE
            )
            pot_embedding = GlyphEmbedding(
                coordinate=pot_coord,
                confidence=0.85
            )
            glyph_state.add_glyph("potential", pot_embedding)
            self.binding_context.bind("potential", "potential", confidence=0.85)
        
        # Add goal as query if present
        if goal:
            goal_coord = GlyphCoordinate(
                x=0.0,
                y=0.0,
                glyph_type=GlyphType.QUERY
            )
            goal_embedding = GlyphEmbedding(
                coordinate=goal_coord,
                confidence=1.0
            )
            glyph_state.add_glyph(f"goal_{goal}", goal_embedding)
        
        # Create human-readable representation
        representation = self._create_summary_representation(
            state_data, goal, glyph_state
        )
        
        summary = SymbolicSummary(
            glyph_state=glyph_state,
            bindings=dict(self.binding_context.state_to_symbol),
            representation=representation
        )
        
        self._summary_history.append(summary)
        
        return summary
    
    def _create_summary_representation(
        self,
        state_data: Dict[str, Any],
        goal: Optional[str],
        glyph_state: GlyphState
    ) -> str:
        """Create human-readable summary."""
        parts = []
        
        # Position summary
        if "x" in state_data:
            x = state_data["x"]
            if isinstance(x, list):
                parts.append(f"pos({x[0]:.1f}, {x[1]:.1f})")
        
        # Budget summary
        if "b" in state_data:
            b = state_data["b"]
            if b > 5.0:
                parts.append("budget=abundant")
            elif b > 2.0:
                parts.append("budget=moderate")
            else:
                parts.append("budget=scarce")
        
        # Potential summary
        if "potential" in state_data:
            p = state_data["potential"]
            parts.append(f"potential={p:.2f}")
        
        # Goal
        if goal:
            parts.append(f"goal={goal}")
        
        return " | ".join(parts) if parts else "empty"
    
    def bind_action(
        self,
        action_id: str,
        action_metadata: Dict[str, Any]
    ) -> ActionTag:
        """
        Tag an action with symbolic metadata.
        
        This allows the symbolic layer to influence policy by
        providing reasoning for action choices.
        
        Args:
            action_id: The action being taken
            action_metadata: Metadata about the action
            
        Returns:
            ActionTag with glyph and reasoning
        """
        # Determine glyph based on action type
        action_type = action_metadata.get("type", "unknown")
        
        if "move" in action_id.lower():
            glyph_type = GlyphType.ACTION
            reasoning = f"Moving to improve potential"
        elif "halt" in action_id.lower():
            glyph_type = GlyphType.ACTION
            reasoning = "No lawful moves available"
        else:
            glyph_type = GlyphType.ACTION
            reasoning = f"Executing {action_type}"
        
        # Add confidence from metadata
        confidence = action_metadata.get("confidence", 0.8)
        
        # Create glyph
        coord = GlyphCoordinate(
            x=0.0,
            y=0.0,
            glyph_type=glyph_type
        )
        embedding = GlyphEmbedding(
            coordinate=coord,
            confidence=confidence
        )
        self.glyph_space.add_glyph(action_id, embedding)
        
        tag = ActionTag(
            action_id=action_id,
            glyph_id=action_id,
            reasoning=reasoning,
            confidence=confidence
        )
        
        self._action_tags.append(tag)
        
        return tag
    
    def get_last_summary(self) -> Optional[SymbolicSummary]:
        """Get the most recent symbolic summary."""
        return self._summary_history[-1] if self._summary_history else None
    
    def get_summary_for_memory(self) -> List[str]:
        """Get summaries formatted for memory storage."""
        return [s.representation for s in self._summary_history[-5:]]
    
    def get_action_tags(self) -> List[ActionTag]:
        """Get all action tags."""
        return self._action_tags
    
    def clear(self) -> None:
        """Clear history (call at episode boundary)."""
        self._summary_history.clear()
        self._action_tags.clear()


def create_symbolic_connector() -> SymbolicConnector:
    """Factory function to create a symbolic connector."""
    return SymbolicConnector()
