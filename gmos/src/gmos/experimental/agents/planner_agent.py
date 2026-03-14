"""
Planner Agent - Experimental Stub

⚠️ EXPERIMENTAL: This is NOT a canonical agent.
⚠️ This is a stub for future planning-based GMI hosted process.
⚠️ Do NOT use in production. API is unstable.

Status: Speculative - Not implemented
"""

from typing import Dict, Any, Optional


class PlannerAgent:
    """
    Planner agent stub.
    
    ⚠️ WARNING: This is a placeholder implementation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._implemented = False
    
    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one planning step.
        
        ⚠️ Not implemented - returns stub response.
        """
        return {"action": "plan", "status": "not_implemented"}
    
    def propose_plan(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a plan to achieve goal.
        
        ⚠️ Not implemented - returns stub response.
        """
        return {"plan": [], "status": "not_implemented"}
    
    def __repr__(self) -> str:
        return "PlannerAgent(EXPERIMENTAL_STUB)"
